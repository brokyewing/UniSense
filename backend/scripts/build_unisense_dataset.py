"""UniSense Q/A dataset hazırlayıcısı (Qwen3-4B fine-tuning için) — KAPSAMLI v2.

Format: Alpaca-style (instruction/output) — AFET projesi ile aynı pipeline.
Çıktı: data/training/unisense_dataset.jsonl

İçerik (~30-50K örnek):
  - 227 üniversite × 5-7 soru = ~1500
  - 21.602 program × 2 soru (taban + detay) = ~43.000
  - 21.602 program × 1 trend Q/A (yıllık değişim) = ~21.000
  - 21.602 program × 1 akademik kadro Q/A (kadrolu olanlar) = ~10.000
  - Akreditasyonlu programlar = ~3000
  - Burs durumu (vakıf programları) = ~5000
  - Eğitim dili (yabancı dilli programlar) = ~2000
  - Sıra/puan/filtre kombinasyonları = ~1000
  - Coğrafi (deniz/merkez/şehir) = ~200
  - Pusula ilgi → bölüm = ~30
  - Hesap mantığı + genel = ~20

Kullanım:
    python scripts/build_unisense_dataset.py
    python scripts/build_unisense_dataset.py --max 50000
    python scripts/build_unisense_dataset.py --light  # sadece ~5K (hızlı test için)
"""
from __future__ import annotations

import argparse
import json
import sys
import random
from collections import Counter
from pathlib import Path

if sys.platform == "win32":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

HERE = Path(__file__).resolve()
PROJECT_ROOT = HERE.parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from unisense.domain.geo import (
    is_coastal_city, is_metropolis, get_seas, cities_by_sea,
)


PROCESSED = PROJECT_ROOT / "data" / "processed"
OUTPUT_DIR = PROJECT_ROOT / "data" / "training"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT = OUTPUT_DIR / "unisense_dataset.jsonl"


# ============================================================
# DATA LOADERS
# ============================================================

DEPS = json.load(open(PROCESSED / "departments.json", encoding="utf-8"))
UNIS = json.load(open(PROCESSED / "universities.json", encoding="utf-8"))
RANKINGS = json.load(open(PROCESSED / "rankings.json", encoding="utf-8"))
FACULTIES = json.load(open(PROCESSED / "faculties.json", encoding="utf-8"))

UNI_LOOKUP = {u["code"]: u for u in UNIS}
DEPT_LOOKUP = {d["code"]: d for d in DEPS}
RANK_LOOKUP = {r["department_code"]: r for r in RANKINGS}
FACULTY_LOOKUP = {f["code"]: f for f in FACULTIES}

print(f"📥 {len(UNIS)} üni, {len(DEPS)} bölüm, {len(FACULTIES)} fakülte, {len(RANKINGS)} sıra")


# ============================================================
# HELPERS
# ============================================================

def fmt_rank(r):
    if r is None:
        return "?"
    return f"{int(r):,}".replace(",", ".")


def fmt_score(s):
    if s is None:
        return "?"
    return f"{float(s):.2f}"


def make(instruction: str, output: str, src: str = "synthesis") -> dict:
    return {
        "instruction": instruction.strip(),
        "output": output.strip(),
        "_src": src,
    }


# ============================================================
# Q/A GENERATORS
# ============================================================

def gen_university_qa() -> list[dict]:
    """Her üni için 5-7 farklı soru."""
    out = []
    for u in UNIS:
        if not u.get("name"):
            continue
        name = u["name"]
        city = u.get("city", "?")
        utype = u.get("type", "?")
        seas = u.get("seas", []) or []
        is_coast = u.get("is_coastal", False)
        is_metro = u.get("is_metropolis", False)
        district = u.get("district", "")
        dept_count = u.get("department_count", "?")

        # 1) Genel
        a = f"📍 {name}\n• Şehir: {city} ({utype})"
        if dept_count != "?": a += f"\n• {dept_count} program sunmaktadır"
        if seas: a += f"\n• Deniz kıyısı: {', '.join(seas)} ({u.get('coast_km', '?')} km)"
        elif not is_coast: a += "\n• İç kesim ili (sahili yok)"
        if is_metro: a += "\n• Büyükşehir konumunda"
        out.append(make(f"{name} hakkında bilgi ver", a + "\nⓘ YÖK Atlas/ÖSYM kaynaklı.", "uni_general"))

        # 2) Lokasyon
        loc = f"{name}, {city}"
        if district: loc += f" — {district} ilçesinde"
        if u.get("is_central_district"): loc += " (şehir merkezi)"
        if is_coast: loc += f". Sahil ili — {', '.join(seas)} kıyısında"
        out.append(make(f"{name} hangi şehirde, merkezi mi?", loc, "uni_location"))

        # 3) Tür
        if utype:
            a3 = f"{name}, **{utype}** üniversitesidir."
            if utype == "VAKIF":
                a3 += " Vakıf üniversitelerinde ücretler değişir, burs imkânları kontrol edilmelidir."
            elif utype == "DEVLET":
                a3 += " Devlet üniversitelerinde öğrenim ücretsizdir."
            out.append(make(f"{name} devlet mi vakıf mı?", a3, "uni_type"))

        # 4) Bölüm sayısı
        if dept_count and dept_count != "?":
            out.append(make(
                f"{name}'nde kaç bölüm var?",
                f"{name}'nde **{dept_count} program** bulunmaktadır.",
                "uni_dept_count"
            ))

        # 5) Akreditasyon
        if u.get("accreditation"):
            out.append(make(
                f"{name} akredite mi?",
                f"{name} {u['accreditation']} tarafından akredite edilmiştir.",
                "uni_accreditation"
            ))
    return out


def gen_program_full_qa() -> list[dict]:
    """TÜM 21.602 program için 1-2 detaylı Q/A."""
    out = []
    for d in DEPS:
        if not d.get("group_name"):
            continue
        uni = UNI_LOOKUP.get(d.get("university_code", ""))
        if not uni:
            continue
        rank = RANK_LOOKUP.get(d["code"], {})

        # 1) Taban + sıra (program-level)
        q = f"{uni['name']} {d['name']} taban puanı ve sıralaması nedir?"
        a_lines = [
            f"📚 {d['name']}",
            f"🏛 {uni['name']}",
            f"📍 {d.get('city', '?')}",
        ]
        if rank.get("base_rank"): a_lines.append(f"• 2025 başarı sırası: {fmt_rank(rank['base_rank'])}")
        if rank.get("base_score"): a_lines.append(f"• 2025 taban puanı: {fmt_score(rank['base_score'])}")
        if rank.get("quota"): a_lines.append(f"• Kontenjan: {rank['quota']}")
        if d.get("scholarship"): a_lines.append(f"• Burs: {d['scholarship']}")
        if d.get("education_language"): a_lines.append(f"• Eğitim dili: {d['education_language']}")
        if d.get("education_level"): a_lines.append(f"• Düzey: {d['education_level']}")
        if d.get("duration_years"): a_lines.append(f"• Süre: {d['duration_years']} yıl")
        if d.get("accreditation"): a_lines.append(f"• Akreditasyon: {d['accreditation']}")
        a_lines.append(f"• ÖSYM tercih kodu: [{d['code']}]")
        out.append(make(q, "\n".join(a_lines), "prog_full"))

        # 2) Sadece kod sorgusu (tercih hatırlaması için)
        out.append(make(
            f"[{d['code']}] hangi bölüm?",
            f"[{d['code']}] = {d['name']} — {uni['name']} ({d.get('city', '?')})",
            "prog_code_lookup"
        ))
    return out


def gen_program_trend_qa() -> list[dict]:
    """Trend Q/A — son 3 yıl (history alanından)."""
    out = []
    for r in RANKINGS:
        history = r.get("history") or []
        if len(history) < 1:
            continue
        d = DEPT_LOOKUP.get(r["department_code"])
        if not d:
            continue
        uni = UNI_LOOKUP.get(d.get("university_code", ""))
        if not uni:
            continue

        a_lines = [f"{uni['name']} — {d['name']} son yıllar trend:"]
        a_lines.append(
            f"• 2025: sıra {fmt_rank(r.get('base_rank'))} · "
            f"taban {fmt_score(r.get('base_score'))}"
            + (f" · kontenjan {r['quota']}" if r.get('quota') else '')
        )
        for h in history:
            a_lines.append(
                f"• {h['year']}: sıra {fmt_rank(h.get('base_rank'))} · "
                f"taban {fmt_score(h.get('base_score'))}"
                + (f" · {h['yerlesen']} yerleşen" if h.get('yerlesen') else '')
            )
        # Momentum
        if history and history[0].get("base_rank") and r.get("base_rank"):
            diff = history[0]["base_rank"] - r["base_rank"]
            if abs(diff) > 500:
                trend = "📈 yükselişte" if diff > 0 else "📉 düşüşte"
                a_lines.append(f"\n→ {trend} (sıralama {abs(diff):,} {'iyileşti' if diff > 0 else 'kötüleşti'})")
            else:
                a_lines.append(f"\n→ 📊 stabil")
        out.append(make(
            f"{uni['name']} {d['group_name']} son yıllar trendi nedir?",
            "\n".join(a_lines),
            "prog_trend"
        ))
    return out


def gen_program_academic_qa() -> list[dict]:
    """Akademik kadro Q/A — sadece kadrolu programlar (toplam > 0)."""
    out = []
    for d in DEPS:
        staff = d.get("academic_staff", {})
        total = staff.get("total", 0)
        if total < 5:  # 5'ten az hocası varsa atla
            continue
        uni = UNI_LOOKUP.get(d.get("university_code", ""))
        if not uni:
            continue

        a = f"{uni['name']} — {d['name']} akademik kadrosu:\n"
        if staff.get("professor"): a += f"• Profesör: {staff['professor']}\n"
        if staff.get("associate_professor"): a += f"• Doçent: {staff['associate_professor']}\n"
        if staff.get("assistant_professor"): a += f"• Dr. Öğretim Üyesi: {staff['assistant_professor']}\n"
        if staff.get("research_assistant"): a += f"• Araştırma Görevlisi: {staff['research_assistant']}\n"
        if staff.get("lecturer"): a += f"• Öğretim Görevlisi: {staff['lecturer']}\n"
        a += f"• Toplam: {total} akademisyen\n"
        a += f"\n🔗 Detay: https://akademik.yok.gov.tr/AkademikArama/?aramaTerim={uni['name'].replace(' ', '+')}"
        out.append(make(
            f"{uni['name']} {d['group_name']} hocaları kaç?",
            a,
            "prog_academic"
        ))
    return out


def gen_accreditation_qa() -> list[dict]:
    """Akreditasyonu olan programları topla."""
    out = []
    by_acc = {}
    for d in DEPS:
        acc = d.get("accreditation", "").strip()
        if not acc:
            continue
        by_acc.setdefault(acc, []).append(d)

    for acc, depts in by_acc.items():
        if len(depts) < 2:
            continue
        # Sample max 30 programs
        sample = random.sample(depts, min(30, len(depts)))
        a_lines = [f"{acc} akreditasyonlu programlardan örnekler ({len(depts)} adet):"]
        for d in sample[:20]:
            uni = UNI_LOOKUP.get(d.get("university_code", ""), {})
            a_lines.append(f"• {d['name']} — {uni.get('name', '?')[:40]}")
        out.append(make(
            f"{acc} akreditasyonu olan bölümler hangileri?",
            "\n".join(a_lines),
            "accreditation"
        ))
    return out


def gen_scholarship_qa() -> list[dict]:
    """Burslu programlar (vakıf üni, %50, %75, tam burs)."""
    out = []
    by_burs = {}
    for d in DEPS:
        burs = d.get("scholarship", "").strip()
        if not burs or burs == "Ücretli":
            continue
        by_burs.setdefault(burs, []).append(d)

    for burs, depts in by_burs.items():
        if len(depts) < 5:
            continue
        # Üni tipine göre filter (vakıf burslu çok kıymetli)
        sample = random.sample(depts, min(50, len(depts)))
        a_lines = [f"{burs} programlar (örnek, {len(depts)} adet):"]
        for d in sample[:15]:
            uni = UNI_LOOKUP.get(d.get("university_code", ""), {})
            rank = RANK_LOOKUP.get(d["code"], {})
            a_lines.append(
                f"• {d['name'][:40]} — {uni.get('name', '?')[:30]}"
                + (f" (sıra {fmt_rank(rank.get('base_rank'))})" if rank.get('base_rank') else '')
            )
        out.append(make(
            f"{burs} programlar hangileri?",
            "\n".join(a_lines),
            "scholarship"
        ))
    return out


def gen_language_qa() -> list[dict]:
    """Eğitim diline göre programlar."""
    out = []
    by_lang = {}
    for d in DEPS:
        lang = d.get("education_language", "").strip()
        if not lang or lang == "Türkçe":
            continue  # Türkçe default, sıkıcı
        by_lang.setdefault(lang, []).append(d)

    for lang, depts in by_lang.items():
        if len(depts) < 5:
            continue
        sample = random.sample(depts, min(30, len(depts)))
        a_lines = [f"{lang} eğitim veren programlardan örnekler ({len(depts)} adet):"]
        for d in sample[:15]:
            uni = UNI_LOOKUP.get(d.get("university_code", ""), {})
            a_lines.append(f"• {d['name'][:40]} — {uni.get('name', '?')[:30]}")
        out.append(make(
            f"{lang} eğitim veren bölümler hangileri?",
            "\n".join(a_lines),
            "language"
        ))
    return out


def gen_onlisans_qa() -> list[dict]:
    """Önlisans-spesifik Q/A — TYT puanlı, MYO bölümleri."""
    out = []
    onlisans = [d for d in DEPS if d.get("education_level") == "Ön Lisans"]

    # Genel önlisans bilgi
    out.append(make(
        "Önlisans nedir?",
        "Önlisans (2 yıllık) programlar:\n"
        "• Meslek Yüksekokulu (MYO) bünyesinde\n"
        "• Süre: 2 yıl\n"
        "• Puan türü: TYT\n"
        "• Mezunlar 'önlisans diploması' alır\n"
        f"• UniSense'te {len(onlisans)} önlisans programı var\n"
        "• DGS ile lisansa geçiş mümkün",
        "onlisans_general"
    ))

    # Şehir bazlı önlisans
    cities_with_onlisans = {}
    for d in onlisans:
        city = d.get("city", "")
        if city:
            cities_with_onlisans.setdefault(city, []).append(d)
    for city, depts in list(cities_with_onlisans.items())[:30]:
        if len(depts) < 5:
            continue
        sample = random.sample(depts, min(15, len(depts)))
        a_lines = [f"{city.title()}'da önlisans programları (örnek, {len(depts)} toplam):"]
        for d in sample[:10]:
            uni = UNI_LOOKUP.get(d.get("university_code", ""), {})
            a_lines.append(f"• {d['name'][:40]} — {uni.get('name', '?')[:30]}")
        out.append(make(
            f"{city.title()}'daki önlisans programları",
            "\n".join(a_lines),
            "onlisans_city"
        ))
    return out


def gen_faculty_qa() -> list[dict]:
    """Fakülte/MYO bazlı Q/A."""
    out = []
    by_kind = {}
    for f in FACULTIES:
        by_kind.setdefault(f.get("kind", "Fakülte"), []).append(f)

    for kind, facs in by_kind.items():
        # Örnek üniversiteler
        unis_with_kind = {}
        for f in facs:
            uc = f.get("university_code")
            if uc:
                unis_with_kind.setdefault(uc, []).append(f)
        sample_unis = random.sample(list(unis_with_kind.keys()), min(15, len(unis_with_kind)))
        a_lines = [f"{kind} olan üniversitelerden örnekler ({len(unis_with_kind)} üni):"]
        for uc in sample_unis:
            uni = UNI_LOOKUP.get(uc, {})
            a_lines.append(f"• {uni.get('name', '?')}")
        out.append(make(
            f"Hangi üniversitelerde {kind} var?",
            "\n".join(a_lines),
            "faculty_kind"
        ))
    return out


def gen_rank_filter_qa(n_samples: int = 1500) -> list[dict]:
    """Sıra/puan/filtre kombinasyonları — daha kapsamlı."""
    out = []
    score_types = ["SAY", "EA", "SÖZ", "DİL", "TYT"]
    rank_buckets = [3000, 10000, 25000, 50000, 80000, 120000, 200000, 300000, 500000]
    uni_types = [None, "Devlet", "Vakıf"]

    for _ in range(n_samples):
        st = random.choice(score_types)
        rank = random.choice(rank_buckets)
        utype = random.choice(uni_types)

        candidates = [
            r for r in RANKINGS
            if r.get("score_type") == st and r.get("base_rank") and r["base_rank"] >= rank * 0.5
        ]
        if utype:
            candidates = [
                r for r in candidates
                if (UNI_LOOKUP.get(DEPT_LOOKUP.get(r["department_code"], {}).get("university_code", ""), {}).get("type", "") or "").upper() == utype.upper()
            ]
        if not candidates:
            continue
        candidates.sort(key=lambda r: abs((r["base_rank"] or 0) - rank))
        top = candidates[:6]

        q_parts = [f"{rank:,}".replace(",", ".") + " sıra"]
        if st != "SAY": q_parts.append(st)
        if utype: q_parts.append(utype)
        q_parts.append("üniversitelerine yerleşebilir miyim?")
        q = " ".join(q_parts)

        a_lines = [f"{rank:,}".replace(",", ".") + f" sıra ({st}) ile yazabileceğin programlar:"]
        for r in top:
            d = DEPT_LOOKUP.get(r["department_code"], {})
            uni = UNI_LOOKUP.get(d.get("university_code", ""), {})
            a_lines.append(
                f"• [{r['department_code']}] {d.get('name', '?')[:40]} — "
                f"{uni.get('name', '?')[:30]} (sıra {fmt_rank(r['base_rank'])}, taban {fmt_score(r['base_score'])})"
            )
        a_lines.append("ⓘ Tercih sayfasından detaylı bak.")
        out.append(make(q, "\n".join(a_lines), "rank_filter"))
    return out


def gen_geo_qa() -> list[dict]:
    """Coğrafi sorular — daha kapsamlı."""
    out = []
    for sea in ["Karadeniz", "Marmara", "Ege", "Akdeniz"]:
        cities = cities_by_sea(sea)
        unis_in_sea = [u for u in UNIS if u.get("city", "").upper() in [c.upper() for c in cities]]
        for filt_label, filt_unis in [
            ("", unis_in_sea),
            ("devlet ", [u for u in unis_in_sea if (u.get("type") or "").upper() == "DEVLET"]),
            ("vakıf ", [u for u in unis_in_sea if (u.get("type") or "").upper() == "VAKIF"]),
        ]:
            if not filt_unis:
                continue
            a_lines = [f"{sea} kıyısındaki {filt_label}üniversiteler ({len(filt_unis)}):"]
            for u in filt_unis[:15]:
                a_lines.append(f"• {u['name']} — {u['city']}")
            if len(filt_unis) > 15:
                a_lines.append(f"... ve {len(filt_unis) - 15} tane daha")
            out.append(make(
                f"{sea} kıyısındaki {filt_label}üniversiteler",
                "\n".join(a_lines),
                "geo_sea"
            ))

    # Şehir bazlı (ilk 30 büyük şehir)
    city_counts = Counter(u.get("city", "") for u in UNIS if u.get("city"))
    for city, _ in city_counts.most_common(30):
        unis = [u for u in UNIS if u.get("city") == city]
        a_lines = [f"{city.title()}'da {len(unis)} üniversite var:"]
        for u in unis[:15]:
            a_lines.append(f"• {u['name']} ({u.get('type', '?')})")
        out.append(make(f"{city.title()}'daki üniversiteler", "\n".join(a_lines), "geo_city"))
    return out


def gen_compass_qa() -> list[dict]:
    """İlgi → bölüm önerisi."""
    interest_to_depts = {
        "yazılım, algoritma, yapay zeka": ["Bilgisayar Mühendisliği", "Yazılım Mühendisliği", "Yapay Zeka Mühendisliği", "Veri Mühendisliği"],
        "hasta bakımı, klinik, şefkat": ["Hemşirelik", "Tıp", "Ebelik", "Fizyoterapi", "Sağlık Yönetimi"],
        "matematik, soyutlama, ispat": ["Matematik", "İstatistik", "Matematik Mühendisliği"],
        "yaratıcı, görsel, tasarım": ["Grafik Tasarım", "Endüstriyel Tasarım", "Mimarlık", "İç Mimarlık"],
        "hukuk, adalet, müzakere": ["Hukuk", "Sosyal Hizmet"],
        "para, finans, analiz": ["İktisat", "İşletme", "Bankacılık ve Finans", "Maliye"],
        "çocuk, eğitim, gelişim": ["Sınıf Öğretmenliği", "Okul Öncesi Öğretmenliği", "Çocuk Gelişimi"],
        "doğa, hayvan, saha": ["Veteriner Fakültesi", "Ziraat Mühendisliği", "Orman Mühendisliği"],
        "ses, performans, müzik": ["Müzik Öğretmenliği", "Müzikoloji", "Sahne Sanatları"],
        "uçak, havacılık, uzay": ["Pilotaj", "Uçak Mühendisliği", "Havacılık Yönetimi"],
        "kimya, deney, laboratuvar": ["Kimya Mühendisliği", "Kimya", "Biyokimya"],
        "elektrik, elektronik, devre": ["Elektrik-Elektronik Mühendisliği", "Elektronik ve Haberleşme Mühendisliği"],
        "makine, imalat, otomotiv": ["Makine Mühendisliği", "Otomotiv Mühendisliği", "Mekatronik Mühendisliği"],
        "inşaat, yapı, mimari": ["İnşaat Mühendisliği", "Mimarlık", "Şehir ve Bölge Planlaması"],
        "diş, ağız sağlığı": ["Diş Hekimliği"],
        "ilaç, eczane": ["Eczacılık"],
    }
    out = []
    for interests, depts in interest_to_depts.items():
        for q_template in [
            f"İlgi alanım: {interests}. Hangi bölümleri seçebilirim?",
            f"{interests} sevenlere ne önerirsin?",
            f"{interests} ile ilgili bölümler nelerdir?",
        ]:
            a = f"Bu ilgilere uygun bölümler:\n" + "\n".join(f"• {d}" for d in depts)
            out.append(make(q_template, a, "compass"))
    return out


def gen_calc_general_qa() -> list[dict]:
    """YKS hesap mantığı + genel sorular."""
    return [
        make("TYT puanı nasıl hesaplanır?",
             "TYT puan hesabı (yaklaşık, ÖSYM 2025):\n"
             "• Türkçe net × 3.3\n"
             "• Sosyal net × 3.4\n"
             "• Matematik net × 3.3\n"
             "• Fen net × 3.4\n"
             "• Tabana 100 eklenir → max ~500 puan\n"
             "• Yerleştirme = TYT_puan + (OBP × 0.12)\n"
             "ⓘ Yaklaşık formül; gerçek puan ÖSYM normuyla ±5-10 sapabilir.", "calc"),
        make("OBP nasıl hesaplanır?",
             "OBP (Ortaöğretim Başarı Puanı):\n"
             "• Diploma notu (100'lük) × 5 = OBP\n"
             "• Örn: 85 → 425 OBP\n"
             "• Yerleştirmeye OBP × 0.12 eklenir (yani 425 × 0.12 = 51 puan)", "calc"),
        make("AYT-SAY puanı nasıl hesaplanır?",
             "AYT-SAY (Sayısal lisans için):\n"
             "• Mat × 3.0, Fizik × 2.85, Kimya × 3.07, Biyoloji × 3.07\n"
             "• Tabana 100 eklenir\n"
             "• Yerleştirme = TYT × 0.4 + AYT × 0.6 + OBP × 0.12\n"
             "• Max ~560 puan", "calc"),
        make("DGS nedir?",
             "DGS (Dikey Geçiş Sınavı):\n"
             "• Önlisans (2 yıllık) mezunlarının lisansa (4 yıllık) geçişi için\n"
             "• Sayısal + Sözel net × 3.0 + 100 = ham puan\n"
             "• Yerleştirme = ham + (önlisans GPA × 25 × 0.5)\n"
             "• Lisans tamamlama amaçlıdır.", "calc"),
        make("YKS ne zaman?",
             "YKS 2025 Haziran ayında. Tam tarih için ÖSYM takvimi:\n"
             "🔗 https://www.osym.gov.tr/", "general"),
        make("Tercih başvurusu nasıl yapılır?",
             "Tercih başvurusu:\n"
             "1. https://aday.osym.gov.tr/ giriş\n"
             "2. Tercih ücreti ödeme\n"
             "3. Maks 24 program seçimi\n"
             "4. Sıralama önemli (1. tercih en istenen)\n"
             "5. Onaylama\n"
             "ⓘ UniSense ile tercih listeni hazırlayabilirsin.", "general"),
        make("Ek puan ne demek?",
             "Ek puan: Mesleki lise + alan içi tercih bonusu.\n"
             "• Aynı alanda devam eden MEB öğrencilerine puan eklenir\n"
             "• Yaklaşık 0.06 × OBP", "general"),
        make("Yatay geçiş şartları nedir?",
             "Yatay geçiş genel şartları:\n"
             "• Aynı seviye (lisans → lisans)\n"
             "• GANO 2.0+\n"
             "• İlk dönem hariç tüm dönemlerde başvurulabilir\n"
             "• Hedef üni koşullarını incele", "general"),
        make("MÜDEK nedir?",
             "MÜDEK = Mühendislik Eğitim Programları Değerlendirme ve Akreditasyon Derneği.\n"
             "• Mühendislik bölümleri için akreditasyon sağlar\n"
             "• Akredite mezunlar uluslararası tanınır (Washington Accord)\n"
             "• 2 yıllık geçerlilik süresi vardır", "general"),
        make("FEDEK nedir?",
             "FEDEK = Fen, Edebiyat, Fen-Edebiyat, Dil ve Tarih-Coğrafya Fakülteleri Öğretim Programları Değerlendirme ve Akreditasyon Derneği.\n"
             "• Fen ve edebiyat fakülteleri için akreditasyon", "general"),
        make("TEPDAD nedir?",
             "TEPDAD = Tıp Eğitimi Programlarını Değerlendirme ve Akreditasyon Derneği.\n"
             "• Tıp fakülteleri için akreditasyon\n"
             "• Mezunlar TEPDAD onaylı diploma alır", "general"),
    ]


# ============================================================
# MAIN
# ============================================================

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=str(OUTPUT))
    p.add_argument("--max", type=int, default=None, help="Max örnek sayısı")
    p.add_argument("--light", action="store_true", help="Sadece ~5K örnek (hızlı test)")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    random.seed(args.seed)

    print("\n🔧 Q/A üretiliyor (KAPSAMLI)...")
    all_data = []

    all_data += gen_university_qa()
    print(f"  Üni Q/A:              +{len(all_data):>6}  | toplam {len(all_data):>6}")

    if not args.light:
        # Heavy duty — tüm 21k program
        prog_qa = gen_program_full_qa()
        all_data += prog_qa
        print(f"  Tüm program Q/A:      +{len(prog_qa):>6}  | toplam {len(all_data):>6}")

        trend_qa = gen_program_trend_qa()
        all_data += trend_qa
        print(f"  Trend Q/A:            +{len(trend_qa):>6}  | toplam {len(all_data):>6}")

        academic_qa = gen_program_academic_qa()
        all_data += academic_qa
        print(f"  Akademik kadro:       +{len(academic_qa):>6}  | toplam {len(all_data):>6}")

        accred_qa = gen_accreditation_qa()
        all_data += accred_qa
        print(f"  Akreditasyon:         +{len(accred_qa):>6}  | toplam {len(all_data):>6}")

        burs_qa = gen_scholarship_qa()
        all_data += burs_qa
        print(f"  Burs/ücret:           +{len(burs_qa):>6}  | toplam {len(all_data):>6}")

        lang_qa = gen_language_qa()
        all_data += lang_qa
        print(f"  Eğitim dili:          +{len(lang_qa):>6}  | toplam {len(all_data):>6}")

        onlisans_qa = gen_onlisans_qa()
        all_data += onlisans_qa
        print(f"  Önlisans-spesifik:    +{len(onlisans_qa):>6}  | toplam {len(all_data):>6}")

        faculty_qa = gen_faculty_qa()
        all_data += faculty_qa
        print(f"  Fakülte/MYO:          +{len(faculty_qa):>6}  | toplam {len(all_data):>6}")
    else:
        # Light — sadece ilk 1500 program
        prog_sample = random.sample(DEPS, min(1500, len(DEPS)))
        prog_dict = {d["code"]: d for d in prog_sample}
        from copy import copy
        DEPS_BACKUP = copy(DEPS)
        DEPS.clear(); DEPS.extend(prog_sample)
        prog_qa = gen_program_full_qa()
        all_data += prog_qa
        DEPS.clear(); DEPS.extend(DEPS_BACKUP)
        print(f"  Program Q/A (1500):   +{len(prog_qa):>6}  | toplam {len(all_data):>6}")

    rank_qa = gen_rank_filter_qa(n_samples=200 if args.light else 1500)
    all_data += rank_qa
    print(f"  Sıra+filtre:          +{len(rank_qa):>6}  | toplam {len(all_data):>6}")

    geo_qa = gen_geo_qa()
    all_data += geo_qa
    print(f"  Coğrafi:              +{len(geo_qa):>6}  | toplam {len(all_data):>6}")

    compass_qa = gen_compass_qa()
    all_data += compass_qa
    print(f"  Pusula/ilgi:          +{len(compass_qa):>6}  | toplam {len(all_data):>6}")

    cgr = gen_calc_general_qa()
    all_data += cgr
    print(f"  Hesap+genel:          +{len(cgr):>6}  | toplam {len(all_data):>6}")

    # Dedupe
    seen_instr = set()
    deduped = []
    for ex in all_data:
        key = ex["instruction"]
        if key in seen_instr:
            continue
        seen_instr.add(key)
        deduped.append(ex)

    if args.max:
        deduped = deduped[:args.max]

    random.shuffle(deduped)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for ex in deduped:
            rec = {"instruction": ex["instruction"], "output": ex["output"]}
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    src_counts = Counter(ex["_src"] for ex in deduped)
    avg_instr = sum(len(ex["instruction"]) for ex in deduped) // max(len(deduped), 1)
    avg_out = sum(len(ex["output"]) for ex in deduped) // max(len(deduped), 1)
    total_chars = sum(len(ex["instruction"]) + len(ex["output"]) for ex in deduped)
    est_tokens = total_chars // 3  # kabaca

    print(f"\n{'='*60}")
    print(f"✓ {out_path}")
    print(f"  Toplam unique: {len(deduped):,}  (dedupe öncesi {len(all_data):,})")
    print(f"  Boyut: {out_path.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"  Ortalama instr: {avg_instr} char | output: {avg_out} char")
    print(f"  Tahmini token: ~{est_tokens:,} (eğitim için ~{est_tokens // 1000:,}K context)")
    print(f"\nKaynak dağılımı:")
    for s, c in src_counts.most_common():
        print(f"  {c:>6,}  {s}")

    print("\n--- Örnek 3 ---")
    for ex in random.sample(deduped, min(3, len(deduped))):
        print(f"Q: {ex['instruction'][:120]}")
        print(f"A: {ex['output'][:200]}...\n")

    print(f"📤 Kaggle:  cd {out_path.parent} && kaggle datasets create -p . --dir-mode zip")


if __name__ == "__main__":
    main()
