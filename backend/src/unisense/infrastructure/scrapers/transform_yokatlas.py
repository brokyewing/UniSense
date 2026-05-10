"""YÖK Atlas raw JSON → UniSense Domain modelleri.

Çıktı:
  data/processed/universities.json   # 227 University
  data/processed/departments.json    # ~12.000 Department (program bazlı)
  data/processed/rankings.json       # ~12.000 Ranking (2025)
  data/processed/faculties.json      # fakülte/yüksekokul listesi
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

if sys.platform == "win32":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from unisense.domain.geo import il_to_bolge


SCORE_TYPE_MAP = {
    "SAY": "SAY",
    "EA": "EA",
    "SÖZ": "SÖZ",
    "DİL": "DİL",
    "TYT": "TYT",
}

EDU_LEVEL_MAP = {
    "LISANS": "Lisans",
    "ONLISANS": "Ön Lisans",
    "ÜNLISANS": "Ön Lisans",  # encoding bug
}

LANG_MAP = {
    "Türkçe": "Türkçe",
    "İngilizce": "İngilizce",
    "Almanca": "Almanca",
    "Fransızca": "Fransızca",
    "Arapça": "Arapça",
}


def _short_uni_name(full: str) -> str:
    """'İSTANBUL TEKNİK ÜNİVERSİTESİ' → 'İTÜ' best-effort kısaltma."""
    s = full.replace("(KKTC)", "").replace("(İSTANBUL)", "").replace("ÜNİVERSİTESİ", "").strip()
    # Çok bilinen kısaltmalar
    KNOWN = {
        "İSTANBUL TEKNİK": "İTÜ",
        "BOĞAZİÇİ": "Boğaziçi",
        "ORTA DOĞU TEKNİK": "ODTÜ",
        "HACETTEPE": "Hacettepe",
        "ANKARA": "AÜ",
        "İSTANBUL": "İÜ",
        "EGE": "Ege",
        "DOKUZ EYLÜL": "DEÜ",
        "GAZİ": "Gazi",
        "MARMARA": "Marmara",
        "YILDIZ TEKNİK": "YTÜ",
    }
    for k, v in KNOWN.items():
        if k in s:
            return v
    # Kelimelerin baş harfi
    words = s.split()
    if len(words) >= 2:
        return "".join(w[0] for w in words[:3] if w)
    return s[:6]


def transform(raw_dir: Path, out_dir: Path) -> None:
    print("=" * 60)
    print("🔄 YÖK Atlas Raw → UniSense Modelleri")
    print("=" * 60)

    # 1. Üniversiteler
    raw_unis = json.load(open(raw_dir / "universities.json", encoding="utf-8"))
    print(f"📥 {len(raw_unis)} raw üniversite")

    # 2. Programlar (RAW) — lisans + önlisans + dgs (varsa hepsi)
    raw_programs: list[dict] = []
    sources_loaded = []
    for fname, label in [
        ("programs_2025.json", "Lisans"),
        ("programs_onlisans_2025.json", "Önlisans"),
        ("programs_dgs_2025.json", "DGS"),
    ]:
        fpath = raw_dir / fname
        if fpath.exists():
            data = json.load(open(fpath, encoding="utf-8"))
            raw_programs.extend(data)
            sources_loaded.append(f"{label}: {len(data)}")
            print(f"📥 {fname}: {len(data)} program")
        else:
            print(f"⏭ {fname}: yok (atlandı)")

    if not raw_programs:
        print("❌ Hiç RAW program bulunamadı! Önce yokatlas_scraper.py çalıştır.")
        return

    print(f"📊 Toplam: {len(raw_programs)} program ({', '.join(sources_loaded)})")

    # 3. Üniversite cluster — programlardan otomatik şehir/türü çıkar
    uni_meta: dict[int, dict] = {}
    for p in raw_programs:
        uid = p.get("universiteId")
        if not uid:
            continue
        if uid not in uni_meta:
            uni_meta[uid] = {
                "code": str(uid),
                "name": p.get("universiteAdi", ""),
                "type": p.get("universiteTuru", "DEVLET"),
                "city": p.get("uniIlAdi", ""),
                "city_code": p.get("uniIlKodu"),
                "district": p.get("uniIlceAdi", ""),
                "region": il_to_bolge(p.get("uniIlAdi")),
                "accreditation": p.get("uniAkreditasyon", ""),
                "faculty_codes": set(),
                "department_count": 0,
            }
        if p.get("fymkId"):
            uni_meta[uid]["faculty_codes"].add(str(p["fymkId"]))
        uni_meta[uid]["department_count"] += 1

    # raw_unis'i kullanarak isim kontrolü ve eksikleri ekle
    raw_uni_lookup = {u["universiteId"]: u for u in raw_unis}
    for uid, raw_u in raw_uni_lookup.items():
        if uid not in uni_meta:
            uni_meta[uid] = {
                "code": str(uid),
                "name": raw_u.get("universiteAdi", ""),
                "type": "DEVLET",
                "city": "",
                "city_code": None,
                "district": "",
                "region": "Bilinmiyor",
                "accreditation": "",
                "faculty_codes": set(),
                "department_count": 0,
            }

    universities = []
    for uid, meta in uni_meta.items():
        universities.append({
            **meta,
            "faculty_codes": sorted(meta["faculty_codes"]),
            "short_name": _short_uni_name(meta["name"]),
        })

    # 4. Fakülteler
    faculty_meta: dict[int, dict] = {}
    for p in raw_programs:
        fid = p.get("fymkId")
        if not fid or fid in faculty_meta:
            continue
        faculty_meta[fid] = {
            "code": str(fid),
            "name": p.get("fymkAdi", ""),
            "kind": "Fakülte",  # YÖK'te her şey "Fakülte/Yüksekokul" olabilir, default
            "university_code": str(p.get("universiteId")),
            "city": p.get("fymkIlAdi", ""),
            "district": p.get("fymkIlceAdi", ""),
            "accreditation": p.get("fymkKilAciklama", ""),
        }
        # Fakülte türü tespit
        n = faculty_meta[fid]["name"].lower()
        if "meslek yüksek" in n or "myo" in n:
            faculty_meta[fid]["kind"] = "Meslek Yüksekokulu"
        elif "yüksekokul" in n:
            faculty_meta[fid]["kind"] = "Yüksekokul"
        elif "konservatuvar" in n:
            faculty_meta[fid]["kind"] = "Konservatuvar"

    faculties = list(faculty_meta.values())

    # 5. Departments + Rankings
    departments = []
    rankings = []
    for p in raw_programs:
        # Department
        departments.append({
            "code": str(p.get("kilavuzKodu") or p.get("birimId")),
            "kilavuz_kodu": p.get("kilavuzKodu"),
            "name": p.get("birimAdi", ""),
            "group_name": p.get("birimGrupAdi", ""),
            "group_code": str(p.get("birimGrupId", "")),
            "faculty_code": str(p.get("fymkId", "")),
            "faculty_name": p.get("fymkAdi", ""),
            "university_code": str(p.get("universiteId", "")),
            "score_type": SCORE_TYPE_MAP.get(p.get("puanTuru", ""), p.get("puanTuru", "")),
            "education_level": EDU_LEVEL_MAP.get(p.get("birimTuruAdi", ""), p.get("birimTuruAdi", "")),
            "education_language": p.get("ogrenimDiliAdi", "Türkçe"),
            "education_type": p.get("ogrenimTuruAdi", ""),  # Örgün/İkinci/Açık
            "duration_years": p.get("ogrenimSuresi") or 4,
            "city": p.get("ilAdi", ""),
            "district": p.get("ilceAdi", ""),
            "region": il_to_bolge(p.get("ilAdi")),
            "scholarship": p.get("bursOraniAdi", ""),
            "scholarship_pct": _parse_scholarship_pct(p.get("bursOraniAdi", "")),
            "fee_try": p.get("ucret"),
            "accreditation": p.get("akreditasyon", ""),
            "accreditation_full": p.get("akreditasyonAck", ""),
            "min_basari_sirasi_kosul": p.get("minBasariSirasi"),  # tercih edebilmek için min başarı
            # Akademik kadro (YÖK Atlas verisi)
            "academic_staff": {
                "professor": p.get("prof", 0) or 0,
                "associate_professor": p.get("doc", 0) or 0,    # Doçent
                "assistant_professor": p.get("dou", 0) or 0,    # Dr. Öğretim Üyesi
                "research_assistant": p.get("arGor", 0) or 0,   # Araştırma Görevlisi
                "lecturer": p.get("ogrGor", 0) or 0,            # Öğretim Görevlisi
                "total": (p.get("prof", 0) or 0) + (p.get("doc", 0) or 0) +
                         (p.get("dou", 0) or 0) + (p.get("arGor", 0) or 0) +
                         (p.get("ogrGor", 0) or 0),
            },
            # ÖSYM Tercih Kılavuzu Kosul kodları
            "osym_conditions": _parse_osym_conditions(p.get("kosul", ""), p.get("kosulList", [])),
        })

        # Ranking (2025) — içinde 2024 ve 2023 trend verileri de var
        # YÖK Atlas API field'ları:
        #   minPuan, basariSirasi      = bu yıl (2025)
        #   minPuan1, basariSirasi1, gk1 = 1 yıl önce (2024) — "history[0]"
        #   minPuan2, basariSirasi2, gk2 = 2 yıl önce (2023) — "history[1]"
        current_year = p.get("yil", 2025)
        history = []
        if p.get("basariSirasi1") is not None or p.get("minPuan1") is not None:
            history.append({
                "year": current_year - 1,
                "base_rank": p.get("basariSirasi1"),
                "base_score": _to_float(p.get("minPuan1")),
                "yerlesen": p.get("gk1"),
            })
        if p.get("basariSirasi2") is not None or p.get("minPuan2") is not None:
            history.append({
                "year": current_year - 2,
                "base_rank": p.get("basariSirasi2"),
                "base_score": _to_float(p.get("minPuan2")),
                "yerlesen": p.get("gk2"),
            })

        rankings.append({
            "year": current_year,
            "department_code": str(p.get("kilavuzKodu") or p.get("birimId")),
            "university_code": str(p.get("universiteId", "")),
            "kilavuz_kodu": p.get("kilavuzKodu"),
            "score_type": SCORE_TYPE_MAP.get(p.get("puanTuru", ""), p.get("puanTuru", "")),
            "base_score": p.get("minPuan"),
            "base_rank": p.get("basariSirasi"),
            "yerlesen": p.get("gkY"),
            # Geçmiş yıllar (2024, 2023) — trend için
            "history": history,
            "quota": p.get("kontenjan"),
            "quota_dep": p.get("kontenjanDep"),
            "min_basari_sirasi_kosul": p.get("minBasariSirasi"),
            "source": "YÖK Atlas",
            # Eski uyumluluk için (legacy)
            "rank_q1": p.get("basariSirasi1"),
            "score_q1": _to_float(p.get("minPuan1")),
        })

    # YAZ
    out_dir.mkdir(parents=True, exist_ok=True)

    with open(out_dir / "universities.json", "w", encoding="utf-8") as f:
        json.dump(universities, f, ensure_ascii=False, indent=2)
    with open(out_dir / "faculties.json", "w", encoding="utf-8") as f:
        json.dump(faculties, f, ensure_ascii=False, indent=2)
    with open(out_dir / "departments.json", "w", encoding="utf-8") as f:
        json.dump(departments, f, ensure_ascii=False, indent=2)
    with open(out_dir / "rankings.json", "w", encoding="utf-8") as f:
        json.dump(rankings, f, ensure_ascii=False, indent=2)

    # Stats
    print()
    print("📊 STATS")
    print(f"  Üniversite: {len(universities)}")
    print(f"  Fakülte:    {len(faculties)}")
    print(f"  Bölüm:      {len(departments)}")
    print(f"  Ranking:    {len(rankings)}")

    # Bölge dağılımı
    from collections import Counter
    region_count = Counter(u["region"] for u in universities)
    print("\n🗺️ Üniversiteler bölgeye göre:")
    for r, n in region_count.most_common():
        print(f"  {n:3d} | {r}")

    type_count = Counter(u["type"] for u in universities)
    print("\n🏛️ Üniversiteler türe göre:")
    for t, n in type_count.most_common():
        print(f"  {n:3d} | {t}")

    score_count = Counter(d["score_type"] for d in departments)
    print("\n📚 Bölüm puan türü dağılımı:")
    for s, n in score_count.most_common():
        print(f"  {n:5d} | {s}")

    print("\n✅ Çıktılar:", out_dir)


def _parse_osym_conditions(kosul_str: str, kosul_list: list) -> dict:
    """ÖSYM tercih kosul kodlarını insan-okunur dict'e çevir.

    Örnek:
      kosul = "21,22,23,24"
      kosulList = [{"21": "Burslu eğitim..."}, {"23": "İngilizce..."}]
      → {
          "codes": [21,22,23,24],
          "summary": ["Burslu", "İngilizce", "1 yıl hazırlık"],
          "language_required": True,
          "scholarship_required": True,
          "min_rank_required": None,
          "details": [{"code": 21, "text": "..."}, ...],
        }
    """
    if not kosul_str or not kosul_list:
        return {"codes": [], "summary": [], "details": []}

    codes = []
    for c in kosul_str.split(","):
        try:
            codes.append(int(c.strip()))
        except ValueError:
            continue

    details = []
    summary = []
    for entry in kosul_list:
        if not isinstance(entry, dict):
            continue
        for code_str, text in entry.items():
            try:
                code = int(code_str)
            except ValueError:
                continue
            details.append({"code": code, "text": text[:500]})
            # Özet kısa sürüm
            short = _summarize_kosul(code, text)
            if short:
                summary.append(short)

    # Özel kontroller
    out = {
        "codes": codes,
        "summary": summary,
        "details": details,
    }
    # Min başarı sırası şartı
    for d in details:
        if "başarı sırası" in d["text"].lower() and "altında" in d["text"].lower():
            import re
            m = re.search(r"(\d{1,3}[.,]?\d{3})", d["text"])
            if m:
                out["min_rank_required"] = int(m.group(1).replace(".", "").replace(",", ""))
                break
    return out


_KOSUL_SUMMARIES = {
    18: "Milli sporcu özel kontenjan",
    21: "Burslu (öğrenim ücreti yok)",
    22: "2 yıl içinde hazırlık tamamlanmazsa Türkçe programa geçirilir",
    23: "Öğretim dili İngilizce",
    24: "1 yıl zorunlu yabancı dil hazırlığı",
    25: "Öğretim dili %30 İngilizce",
    26: "Öğretim dili Almanca",
    27: "Öğretim dili Fransızca",
    28: "Öğretim dili Arapça",
    29: "İsteğe bağlı yabancı dil hazırlık (1 yıl)",
    35: "Öğrenim Çince",
    50: "%50 indirimli (yarı ücretli)",
    64: "Vakıf/KKTC öğrenim ücretine tabi",
    75: "%75 indirimli",
    78: "Yetenek sınavı zorunlu",
    79: "Polis Akademisi sınavı/sağlık şartları",
    87: "Mavi yaka sertifikası gerekli",
    155: "Tıp programları min başarı sırası şartı (50.000)",
    156: "Hukuk programları min başarı sırası şartı (125.000)",
    157: "Mühendislik programları min başarı sırası şartı (240.000)",
    158: "Mimarlık/öğretmenlik min başarı sırası şartı (300.000)",
}


def _summarize_kosul(code: int, full_text: str) -> str | None:
    """Kosul kodunu kısa özetine çevir."""
    if code in _KOSUL_SUMMARIES:
        return _KOSUL_SUMMARIES[code]
    # Bilinmeyen kosul → ilk cümle
    first_sentence = full_text.split(".", 1)[0].strip()
    if 10 < len(first_sentence) < 80:
        return first_sentence
    return None


def _parse_scholarship_pct(text: str) -> int | None:
    if not text:
        return None
    t = text.lower()
    if "burslu" in t and "indirim" not in t:
        return 100
    if "%50" in t or "yüzde 50" in t:
        return 50
    if "%25" in t or "yüzde 25" in t:
        return 25
    if "%75" in t or "yüzde 75" in t:
        return 75
    if "ücretli" in t:
        return 0
    return None


def _to_float(x):
    if x is None or x == "" or x == "0":
        return None
    try:
        return float(x)
    except (ValueError, TypeError):
        return None


if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[4]
    raw_dir = project_root / "data" / "raw" / "yokatlas"
    out_dir = project_root / "data" / "processed"
    transform(raw_dir, out_dir)
