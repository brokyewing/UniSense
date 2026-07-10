"""Chunker — programlar + Wikipedia tanımlarını ChromaDB için chunks'a çevirir.

Strateji:
  1. **Program chunks** (12.265 adet) — her program tek chunk
     "İTÜ Bilgisayar Müh (İngilizce) | SAY | Taban: 521.4 | Sıra: 5500 | Kontenjan: 60"
  2. **Wikipedia üni chunks** (~200 üni × ~5-10 bölüm = ~1500 chunk)
     Üniversite tarihçesi, kampüs, fakülte listesi
  3. **Üni özet chunks** — her üni için bir kapak chunk
     "İTÜ İstanbul'da Devlet üni, 1773 kuruluş, Marmara bölgesinde, 30 fakülte..."

Çıktı:
  data/processed/chunks.json
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from collections import defaultdict

if sys.platform == "win32":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def fmt_score(p: dict) -> str:
    """Programdan tek satır özet üret."""
    parts = []
    parts.append(f"📚 {p['name']}")
    parts.append(f"🏛 {_uni_name_lookup.get(p['university_code'], p['university_code'])}")
    if p.get("faculty_name"):
        parts.append(f"🏫 {p['faculty_name']}")
    if p.get("city"):
        parts.append(f"📍 {p['city']}")

    parts.append(f"Puan türü: {p.get('score_type', '?')}")
    parts.append(f"Eğitim seviyesi: {p.get('education_level', '?')}")
    parts.append(f"Eğitim dili: {p.get('education_language', '?')}")
    parts.append(f"Süre: {p.get('duration_years', '?')} yıl")

    if p.get("scholarship"):
        parts.append(f"Burs: {p['scholarship']}")
    if p.get("fee_try"):
        parts.append(f"Yıllık ücret: {p['fee_try']:,} TL")
    if p.get("accreditation"):
        parts.append(f"Akreditasyon: {p['accreditation']}")
    if p.get("min_basari_sirasi_kosul"):
        parts.append(f"Min başarı sırası şartı: {p['min_basari_sirasi_kosul']}")

    return " | ".join(parts)


def fmt_academic_staff(p: dict) -> str:
    """Akademik kadro bilgisi."""
    s = p.get("academic_staff") or {}
    if not s or s.get("total", 0) == 0:
        return ""
    bits = []
    if s.get("professor"):
        bits.append(f"{s['professor']} profesör")
    if s.get("associate_professor"):
        bits.append(f"{s['associate_professor']} doçent")
    if s.get("assistant_professor"):
        bits.append(f"{s['assistant_professor']} dr. öğretim üyesi")
    if s.get("research_assistant"):
        bits.append(f"{s['research_assistant']} araştırma görevlisi")
    if s.get("lecturer"):
        bits.append(f"{s['lecturer']} öğretim görevlisi")
    if not bits:
        return ""
    return f"👨‍🏫 Akademik kadro: {', '.join(bits)} (toplam {s.get('total', 0)} kişi)"


def fmt_osym_conditions(p: dict) -> str:
    """ÖSYM tercih koşulları (dil, burs, hazırlık, min başarı)."""
    cond = p.get("osym_conditions") or {}
    summary = cond.get("summary", [])
    codes = cond.get("codes", [])
    if not summary:
        return ""
    bits = []
    if codes:
        bits.append(f"📋 ÖSYM kodları: {', '.join(str(c) for c in codes)}")
    bits.append("Tercih koşulları:")
    for s in summary[:6]:
        bits.append(f"  • {s}")
    return "\n".join(bits)


def fmt_ranking(r: dict, p: dict) -> str:
    """Sıralama bilgisi metin şeklinde."""
    out = []
    out.append(f"📊 {r['year']} yerleştirme verisi:")
    if r.get("base_score") is not None:
        out.append(f"  • Taban puan: {r['base_score']:.2f}")
    if r.get("base_rank") is not None:
        out.append(f"  • Başarı sırası: {r['base_rank']:,}")
    if r.get("quota") is not None:
        out.append(f"  • Kontenjan: {r['quota']}")
    if r.get("score_q1") is not None:
        out.append(f"  • Q1 (üst %25) puan: {r['score_q1']:.2f}")
    if r.get("score_q3") is not None:
        out.append(f"  • Q3 (alt %25) puan: {r['score_q3']:.2f}")
    return "\n".join(out)


def build_program_chunks(departments: list[dict], rankings: list[dict]) -> list[dict]:
    """Her program için tek chunk."""
    rank_lookup = {r["department_code"]: r for r in rankings}
    chunks = []
    seen_ids: set[str] = set()
    for idx, d in enumerate(departments):
        r = rank_lookup.get(d["code"])
        # Tam tanım metni
        info = fmt_score(d)
        rank_text = fmt_ranking(r, d) if r else "📊 Sıralama verisi yok."
        staff_text = fmt_academic_staff(d)
        osym_text = fmt_osym_conditions(d)

        parts = [info, rank_text]
        if staff_text:
            parts.append(staff_text)
        if osym_text:
            parts.append(osym_text)
        content = "\n\n".join(parts)

        # ID'yi eşsiz yap (bazı program kodları farklı puan türü için tekrar edebilir)
        base_id = f"prog_{d['code']}"
        chunk_id = base_id
        suffix = 1
        while chunk_id in seen_ids:
            chunk_id = f"{base_id}_{suffix}"
            suffix += 1
        seen_ids.add(chunk_id)

        chunks.append({
            "chunk_id": chunk_id,
            "content": content,
            "chunk_type": "program",
            "university_code": d["university_code"],
            "department_code": d["code"],
            "department_group": d.get("group_name", ""),
            "score_type": d.get("score_type", ""),
            "year": r.get("year") if r else 2025,
            "city": d.get("city", ""),
            "region": d.get("region", ""),
            "education_level": d.get("education_level", ""),
            "education_language": d.get("education_language", ""),
            "scholarship": d.get("scholarship", ""),
            "heading": d["name"],
            "source": "YÖK Atlas 2025",
            "source_url": f"https://yokatlas.yok.gov.tr/lisans.php?y={d.get('kilavuz_kodu', '')}",
            "language": "tr",
        })
    return chunks


def build_university_summary_chunks(universities: list[dict],
                                     departments: list[dict]) -> list[dict]:
    """Her üniversite için bir kapak chunk."""
    # Üni başına bölüm sayısı
    dept_count = defaultdict(int)
    fac_codes = defaultdict(set)
    cities = defaultdict(set)
    score_types = defaultdict(set)
    for d in departments:
        dept_count[d["university_code"]] += 1
        fac_codes[d["university_code"]].add(d.get("faculty_code", ""))
        cities[d["university_code"]].add(d.get("city", ""))
        score_types[d["university_code"]].add(d.get("score_type", ""))

    chunks = []
    for u in universities:
        c = u["code"]
        bits = []
        bits.append(f"🏛 {u['name']}")
        if u.get("short_name"):
            bits.append(f"Kısa ad: {u['short_name']}")
        bits.append(f"Türü: {u['type']}")
        if u.get("founded_year"):
            bits.append(f"Kuruluş: {u['founded_year']}")
        if u.get("city"):
            bits.append(f"Şehir: {u['city']}")
        if u.get("region") and u["region"] != "Bilinmiyor":
            bits.append(f"Bölge: {u['region']}")
        if u.get("accreditation"):
            bits.append(f"Akreditasyon: {u['accreditation']}")
        bits.append(f"Bölüm sayısı: {dept_count[c]}")
        bits.append(f"Fakülte/birim sayısı: {len(fac_codes[c]) - (1 if '' in fac_codes[c] else 0)}")
        if score_types[c]:
            bits.append(f"Mevcut puan türleri: {', '.join(sorted(score_types[c] - {''}))}")
        if u.get("website"):
            bits.append(f"Web: {u['website']}")
        if u.get("phone"):
            bits.append(f"Tel: {u['phone']}")
        if u.get("email"):
            bits.append(f"E-posta: {u['email']}")
        if u.get("rector"):
            # Rektör metni uzun olabilir; ilk 80 karakteri al
            rector_short = u["rector"][:80] + ("..." if len(u["rector"]) > 80 else "")
            bits.append(f"Rektör: {rector_short}")
        if u.get("address"):
            bits.append(f"Adres: {u['address']}")

        content = " | ".join(bits)
        chunks.append({
            "chunk_id": f"uni_{c}",
            "content": content,
            "chunk_type": "university",
            "university_code": c,
            "department_code": "",
            "city": u.get("city", ""),
            "region": u.get("region", ""),
            "heading": u["name"],
            "source": "YÖK Atlas 2025 + Wikipedia",
            "source_url": u.get("website", ""),
            "language": "tr",
            # Metadata için sayısal/string ek alanlar (chunk_meta'da kullanılabilir)
            "founded_year": u.get("founded_year") or 0,
            "logo_url": u.get("logo_url", ""),
        })
    return chunks


def build_wikipedia_chunks(wiki_data: list[dict]) -> list[dict]:
    """Wikipedia üniversite makalelerini bölüm bazlı chunks."""
    chunks = []
    for w in wiki_data:
        if not w.get("wikipedia_title") or not w.get("sections"):
            continue
        uni_name = w["name"]
        url = w.get("wikipedia_url", "")
        for i, sec in enumerate(w["sections"]):
            heading = sec.get("heading", "")
            content_text = sec.get("content", "")
            if not content_text or len(content_text) < 100:
                continue
            # Çok uzun bölümleri 1500 char'a böl
            if len(content_text) > 1500:
                # 1200 char penceresi + 200 overlap
                chunks_text = []
                step = 1000
                for start in range(0, len(content_text), step):
                    end = min(start + 1200, len(content_text))
                    chunks_text.append(content_text[start:end])
                    if end == len(content_text):
                        break
            else:
                chunks_text = [content_text]

            for j, ct in enumerate(chunks_text):
                chunks.append({
                    "chunk_id": f"wiki_{w['code']}_{i:03d}_{j:02d}",
                    "content": f"📖 {uni_name} — {heading}\n\n{ct}",
                    "chunk_type": "university_wiki",
                    "university_code": w["code"],
                    "department_code": "",
                    "heading": f"{uni_name} - {heading}",
                    "source": "Wikipedia TR",
                    "source_url": url,
                    "language": "tr",
                })
    return chunks


# Üniversite kodu → ad lookup (program chunk'larında okunabilir ad için)
_uni_name_lookup: dict[str, str] = {}


def build_dept_guide_chunks(guides: list[dict]) -> list[dict]:
    """Bölüm/meslek tanıtım chunk'ları (dept_guides.json'dan).

    "X bölümü ne iş yapar?" sorularına kaynaklı cevap sağlar. Kaynak alanı
    şeffaf: yapay zeka destekli özet olduğu belirtilir.
    """
    chunks = []
    for g in guides:
        name = g.get("name", "")
        content = (g.get("content") or "").strip()
        if not name or len(content) < 100:
            continue
        chunks.append({
            "chunk_id": f"guide_{name.replace(' ', '_')[:60]}",
            "content": f"📖 {name} — Bölüm Rehberi\n\n{content}",
            "chunk_type": "dept_guide",
            "university_code": "",
            "department_code": "",
            "department_group": name,
            "score_type": "",
            "year": 2026,
            "city": "",
            "heading": f"{name} nedir, mezunları ne iş yapar?",
            "source": "Bölüm Rehberi (yapay zeka destekli özet)",
            "source_url": "",
            "language": "tr",
        })
    return chunks


def main() -> None:
    # backend/src/unisense/cli/build_chunks.py
    # parents[0]=cli, [1]=unisense, [2]=src, [3]=backend
    project_root = Path(__file__).resolve().parents[3]
    proc = project_root / "data" / "processed"
    raw_wiki = project_root / "data" / "raw" / "wikipedia"

    print("=" * 60)
    print("🔨 UniSense Chunker")
    print("=" * 60)

    # Yükle
    universities = json.load(open(proc / "universities.json", encoding="utf-8"))
    departments = json.load(open(proc / "departments.json", encoding="utf-8"))
    rankings = json.load(open(proc / "rankings.json", encoding="utf-8"))
    print(f"📥 {len(universities)} uni, {len(departments)} bölüm, {len(rankings)} sıralama")

    # Lookup
    global _uni_name_lookup
    _uni_name_lookup = {u["code"]: u["name"] for u in universities}

    # Wikipedia (varsa)
    wiki_data = []
    wiki_file = raw_wiki / "universities.json"
    if wiki_file.exists():
        wiki_data = json.load(open(wiki_file, encoding="utf-8"))
        print(f"📥 {len(wiki_data)} Wikipedia üniversite")

    # Build
    print("\n🔨 Chunks oluşturuluyor...")
    program_chunks = build_program_chunks(departments, rankings)
    print(f"   Program chunks: {len(program_chunks)}")

    uni_summary_chunks = build_university_summary_chunks(universities, departments)
    print(f"   Üni özet chunks: {len(uni_summary_chunks)}")

    wiki_chunks = build_wikipedia_chunks(wiki_data) if wiki_data else []
    print(f"   Wikipedia chunks: {len(wiki_chunks)}")

    # Bölüm rehberleri — iki katman:
    #   1. İŞKUR/MEB resmi meslek metinleri (iskur_guides.json) — ÖNCELİKLİ
    #   2. Gemini özeti (dept_guides.json) — İŞKUR'da karşılığı olmayanlar
    iskur_file = proc / "iskur_guides.json"
    guide_file = proc / "dept_guides.json"
    iskur_chunks, guide_chunks = [], []
    iskur_names: set[str] = set()
    if iskur_file.exists():
        iskur = json.load(open(iskur_file, encoding="utf-8"))
        iskur_names = {g["name"] for g in iskur}
        for g in iskur:
            g["content"] = (f"Meslek: {g.get('meslek', g['name'])}\n\n"
                            f"{g['content']}")
        iskur_chunks = build_dept_guide_chunks(iskur)
        for c in iskur_chunks:
            c["chunk_id"] = "iskur_" + c["chunk_id"]
            c["source"] = "İŞKUR Meslek Bilgi Kitapçığı (MEB kariyer portalı)"
        print(f"   İŞKUR meslek chunks: {len(iskur_chunks)}")
    if guide_file.exists():
        guides = [g for g in json.load(open(guide_file, encoding="utf-8"))
                  if g["name"] not in iskur_names]
        guide_chunks = build_dept_guide_chunks(guides)
        print(f"   Bölüm rehberi (AI) chunks: {len(guide_chunks)}")

    all_chunks = (program_chunks + uni_summary_chunks + wiki_chunks
                  + iskur_chunks + guide_chunks)

    # chunk_index renumber
    for i, c in enumerate(all_chunks):
        c["chunk_index"] = i

    # Yaz
    out_file = proc / "chunks.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, ensure_ascii=False, indent=2)

    print(f"\n✅ Toplam chunk: {len(all_chunks)}")
    print(f"📁 {out_file}")
    print(f"📊 Boyut: {out_file.stat().st_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
