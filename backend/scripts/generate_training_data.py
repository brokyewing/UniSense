"""UniSense Fine-Tuning veri üretici.

Çeşitli sorgu kalıplarından (Q, A) çiftleri üretir, JSONL olarak kaydeder.
Cevaplar:
  - structured veriden direkt sentezlenir (Gemini gerekmez)
  - veya isteğe bağlı: backend'in /ask endpoint'i kullanılarak Gemini cevabı

Çıktı formatı: ShareGPT (Unsloth/Axolotl uyumlu)
[
  {
    "messages": [
      {"role": "system", "content": "Sen UniSense..."},
      {"role": "user", "content": "300.000 sırayla devlet üniversiteleri"},
      {"role": "assistant", "content": "• [101410163] Bilgisayar Müh. — Karabük..."}
    ]
  },
  ...
]

Çalıştır:
    python scripts/generate_training_data.py
    python scripts/generate_training_data.py --use-llm  # Gemini ile cevaplari de üret
    python scripts/generate_training_data.py --max 1000
"""
from __future__ import annotations

import argparse
import json
import sys
import random
from pathlib import Path

HERE = Path(__file__).resolve()
PROJECT_ROOT = HERE.parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from unisense.domain.geo import (
    is_coastal_city, is_metropolis, is_central_district, get_seas, cities_by_sea
)


SYSTEM_PROMPT = """Sen UniSense — Türkiye 2025 YKS tercih asistanısın.
Verilen yapısal verilere dayanarak Türkçe, kısa, madde işaretli cevaplar ver.

KURALLAR:
- Sayılar (sıra, puan, kontenjan) verilmişse mutlaka belirt
- Bölüm/üniversite adları tam yazılır
- Veri yoksa "Bu bilgi YÖK Atlas'tan kontrol edilmeli" de
- Maksimum 8 madde
- Akademik nötr ton"""


PROCESSED = PROJECT_ROOT / "data" / "processed"
DEPS = json.load(open(PROCESSED / "departments.json", encoding="utf-8"))
UNIS = json.load(open(PROCESSED / "universities.json", encoding="utf-8"))
RANKINGS = json.load(open(PROCESSED / "rankings.json", encoding="utf-8"))

UNI_LOOKUP = {u["code"]: u for u in UNIS}
DEPT_LOOKUP = {d["code"]: d for d in DEPS}
RANK_LOOKUP = {r["department_code"]: r for r in RANKINGS}


def fmt_rank(r):
    return f"{int(r):,}".replace(",", ".") if r else "?"


def fmt_score(s):
    return f"{float(s):.2f}" if s else "?"


def fmt_program(d, rank=None):
    """Program tek satırlık özet."""
    code = d.get("code", "?")
    name = d.get("name", "?")
    uni = UNI_LOOKUP.get(d.get("university_code", ""), {})
    uni_name = uni.get("name", "?")
    city = d.get("city", "?")
    r = rank or RANK_LOOKUP.get(code) or {}
    rank_v = r.get("base_rank")
    score_v = r.get("base_score")
    quota = r.get("quota")
    parts = [f"[{code}] {name}", uni_name, city]
    extras = []
    if rank_v: extras.append(f"sıra {fmt_rank(rank_v)}")
    if score_v: extras.append(f"taban {fmt_score(score_v)}")
    if quota: extras.append(f"kontenjan {quota}")
    if extras:
        parts.append("(" + " · ".join(extras) + ")")
    return " — ".join(parts[:2]) + (f" — {parts[2]}" if len(parts) > 2 else "") + (f" {parts[3]}" if len(parts) > 3 else "")


def make_pair(question: str, answer: str) -> dict:
    """ShareGPT formatında bir örnek üret."""
    return {
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": question},
            {"role": "assistant", "content": answer},
        ]
    }


# === Q/A üreticileri ===

def gen_university_summaries(n_per_uni=3):
    """Her üni için 'X üniversitesi hakkında' tip Q/A."""
    out = []
    for u in UNIS:
        if not u.get("name"): continue
        name = u["name"]
        city = u.get("city", "?")
        utype = u.get("type", "?")
        seas = u.get("seas") or []
        is_coast = u.get("is_coastal", False)
        is_metro = u.get("is_metropolis", False)
        dept_count = u.get("department_count", "?")

        # Q1: Genel bilgi
        q1 = random.choice([
            f"{name} hakkında bilgi ver",
            f"{name} nasıl bir okul",
            f"{name} hakkında ne söyleyebilirsin",
        ])
        a1_lines = [
            f"📍 {name}",
            f"• Şehir: {city} ({utype})",
        ]
        if dept_count != "?":
            a1_lines.append(f"• {dept_count} program sunmaktadır")
        if seas:
            a1_lines.append(f"• Deniz kıyısı: {', '.join(seas)} ({u.get('coast_km', '?')} km)")
        elif not is_coast:
            a1_lines.append(f"• İç kesim ili (sahili yok)")
        if is_metro:
            a1_lines.append(f"• Büyükşehir konumunda")
        a1 = "\n".join(a1_lines)
        out.append(make_pair(q1, a1))

        # Q2: Şehir/lokasyon
        q2 = random.choice([
            f"{name} hangi şehirde",
            f"{name} nerede",
        ])
        district = u.get("district", "")
        loc = f"{name}, {city}"
        if district: loc += f" ({district} ilçesi)"
        if is_coast: loc += f" — sahil ili, {', '.join(seas)} kıyısı"
        out.append(make_pair(q2, loc))

        # Q3: Devlet/Vakıf
        if utype:
            q3 = f"{name} devlet mi vakıf mı"
            a3 = f"{name}, **{utype}** üniversitesidir."
            out.append(make_pair(q3, a3))

    return out


def gen_department_at_uni(n_samples=500):
    """'X üniversitesinde Y bölümü' tip Q/A."""
    random.shuffle(DEPS)
    out = []
    seen = set()
    for d in DEPS[:n_samples * 2]:
        if not d.get("group_name"): continue
        uni = UNI_LOOKUP.get(d.get("university_code", ""))
        if not uni: continue
        key = (uni["code"], d["group_name"])
        if key in seen: continue
        seen.add(key)

        q = random.choice([
            f"{uni['name']} {d['group_name']} taban puanı",
            f"{uni['name']}'nde {d['group_name']} bölümü hakkında bilgi",
            f"{d['group_name']} {uni['name']}",
        ])
        rank = RANK_LOOKUP.get(d["code"], {})
        a_lines = [f"📚 {d['name']}", f"🏛 {uni['name']}", f"📍 {d.get('city', '?')}"]
        if rank.get("base_rank"):
            a_lines.append(f"• Geçen yıl başarı sırası: {fmt_rank(rank['base_rank'])}")
        if rank.get("base_score"):
            a_lines.append(f"• Taban puan: {fmt_score(rank['base_score'])}")
        if rank.get("quota"):
            a_lines.append(f"• Kontenjan: {rank['quota']}")
        if d.get("scholarship"):
            a_lines.append(f"• Burs durumu: {d['scholarship']}")
        if d.get("education_language"):
            a_lines.append(f"• Eğitim dili: {d['education_language']}")
        if d.get("accreditation"):
            a_lines.append(f"• Akreditasyon: {d['accreditation']}")
        a_lines.append(f"• ÖSYM kodu: {d['code']}")
        out.append(make_pair(q, "\n".join(a_lines)))
        if len(out) >= n_samples: break
    return out


def gen_rank_filter_questions(n_samples=400):
    """'X sıra ile devlet üniversiteleri', '50k sıra mühendislik' vb."""
    out = []
    score_types = ["SAY", "EA", "SÖZ", "TYT"]
    rank_buckets = [10000, 30000, 50000, 100000, 150000, 250000, 400000]
    uni_types = [None, "Devlet", "Vakıf"]
    geo_filters = [None, "deniz", "merkez", "büyükşehir", "Karadeniz", "Akdeniz"]

    for _ in range(n_samples):
        st = random.choice(score_types)
        rank = random.choice(rank_buckets)
        utype = random.choice(uni_types)
        geo = random.choice(geo_filters)

        # Filter rankings
        candidates = [
            r for r in RANKINGS
            if r.get("score_type") == st and r.get("base_rank") and r["base_rank"] >= rank * 0.5
        ]
        if not candidates: continue

        # Apply uni type filter
        if utype:
            candidates = [
                r for r in candidates
                if (UNI_LOOKUP.get(DEPT_LOOKUP.get(r["department_code"], {}).get("university_code", ""), {}).get("type", "") or "").upper() == utype.upper()
            ]

        # Apply geo filter
        if geo == "deniz":
            candidates = [r for r in candidates if DEPT_LOOKUP.get(r["department_code"], {}).get("is_coastal")]
        elif geo == "merkez":
            candidates = [r for r in candidates if DEPT_LOOKUP.get(r["department_code"], {}).get("is_central_district")]
        elif geo == "büyükşehir":
            candidates = [r for r in candidates if DEPT_LOOKUP.get(r["department_code"], {}).get("is_metropolis")]
        elif geo in ("Karadeniz", "Akdeniz", "Marmara", "Ege"):
            candidates = [r for r in candidates if geo in (DEPT_LOOKUP.get(r["department_code"], {}).get("seas") or [])]

        if not candidates: continue

        # Sort by closeness to rank
        candidates.sort(key=lambda r: abs((r["base_rank"] or 0) - rank))
        top = candidates[:6]

        # Build question
        q_parts = [f"{rank:,}".replace(",", ".") + " sıra"]
        if st != "SAY": q_parts.append(st)
        if utype: q_parts.append(utype)
        if geo: q_parts.append(geo)
        q_parts.append("üniversitelerine yerleşebilir miyim")
        q = " ".join(q_parts)

        # Build answer
        a_lines = [f"{rank:,}".replace(",", ".") + f" sıralama ile ({st}) önerilen programlar:"]
        for r in top:
            d = DEPT_LOOKUP.get(r["department_code"], {})
            uni = UNI_LOOKUP.get(d.get("university_code", ""), {})
            a_lines.append(
                f"• [{r['department_code']}] {d.get('name', '?')[:40]} — "
                f"{uni.get('name', '?')[:30]} (sıra {fmt_rank(r['base_rank'])}, taban {fmt_score(r['base_score'])})"
            )
        out.append(make_pair(q, "\n".join(a_lines)))
    return out


def gen_geo_questions(n_samples=200):
    """Coğrafi sorular: deniz, merkez, sahil."""
    out = []
    sea_names = ["Karadeniz", "Marmara", "Ege", "Akdeniz"]

    for sea in sea_names:
        cities = cities_by_sea(sea)
        unis_in_sea = [u for u in UNIS if u.get("city", "").upper() in [c.upper() for c in cities]]
        q = f"{sea} kıyısındaki üniversiteler hangileri"
        a_lines = [f"{sea} kıyısındaki üniversiteler ({len(unis_in_sea)}):"]
        for u in unis_in_sea[:10]:
            a_lines.append(f"• {u['name']} — {u['city']} ({u.get('type', '?')})")
        out.append(make_pair(q, "\n".join(a_lines)))

        # Devlet versiyonu
        devlet = [u for u in unis_in_sea if (u.get("type", "") or "").upper() == "DEVLET"]
        q2 = f"{sea} kıyısındaki devlet üniversiteleri"
        a2_lines = [f"{sea} kıyısındaki devlet üniversiteleri ({len(devlet)}):"]
        for u in devlet[:10]:
            a2_lines.append(f"• {u['name']} — {u['city']}")
        out.append(make_pair(q2, "\n".join(a2_lines)))

    # Şehir bazlı
    sample_cities = ["İSTANBUL", "ANKARA", "İZMİR", "ANTALYA", "ESKİŞEHİR", "KONYA", "TRABZON"]
    for city in sample_cities:
        unis = [u for u in UNIS if u.get("city", "").upper() == city]
        q = f"{city.title()}'daki üniversiteler"
        a_lines = [f"{city.title()}'daki üniversiteler ({len(unis)}):"]
        for u in unis[:10]:
            a_lines.append(f"• {u['name']} ({u.get('type', '?')})")
        out.append(make_pair(q, "\n".join(a_lines)))

    return out


def gen_compass_interest_questions(n_samples=100):
    """İlgi → bölüm önerisi tip sorular."""
    out = []
    interest_to_depts = {
        "yazılım, algoritma, yapay zeka": ["Bilgisayar Mühendisliği", "Yazılım Mühendisliği", "Yapay Zeka Mühendisliği"],
        "hasta bakımı, klinik, şefkat": ["Hemşirelik", "Tıp", "Ebelik", "Fizyoterapi"],
        "matematik, soyutlama, ispat": ["Matematik", "İstatistik", "Matematik Mühendisliği"],
        "yaratıcı, görsel, tasarım": ["Grafik Tasarım", "Endüstriyel Tasarım", "Mimarlık", "İç Mimarlık"],
        "hukuk, adalet, müzakere": ["Hukuk"],
        "para, finans, analiz": ["İktisat", "İşletme", "Bankacılık ve Finans"],
        "çocuk, eğitim, gelişim": ["Sınıf Öğretmenliği", "Okul Öncesi Öğretmenliği", "Çocuk Gelişimi"],
        "doğa, hayvan, saha": ["Veteriner Fakültesi", "Ziraat", "Orman Mühendisliği"],
    }
    for interests, depts in interest_to_depts.items():
        q = f"İlgi alanım: {interests}. Hangi bölümleri seçebilirim?"
        a = f"İlgilerine göre uygun bölümler:\n" + "\n".join(f"• {d}" for d in depts)
        out.append(make_pair(q, a))
    return out


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--out", default=str(PROJECT_ROOT / "data" / "training" / "qwen_finetune.jsonl"))
    p.add_argument("--max", type=int, default=None, help="Max örnek sayısı")
    p.add_argument("--seed", type=int, default=42)
    args = p.parse_args()

    random.seed(args.seed)

    print("Veri üretiliyor...")
    all_data = []
    all_data += gen_university_summaries(n_per_uni=3); print(f"  Üni özetleri: {len(all_data)}")
    all_data += gen_department_at_uni(n_samples=1500);  print(f"  Bölüm/üni: {len(all_data)}")
    all_data += gen_rank_filter_questions(n_samples=600); print(f"  Sıra+filtre: {len(all_data)}")
    all_data += gen_geo_questions(n_samples=50); print(f"  Coğrafi: {len(all_data)}")
    all_data += gen_compass_interest_questions(); print(f"  İlgi: {len(all_data)}")

    random.shuffle(all_data)
    if args.max:
        all_data = all_data[:args.max]

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for ex in all_data:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"\n✓ {len(all_data)} örnek yazıldı: {out_path}")
    print(f"  Boyut: {out_path.stat().st_size / 1024 / 1024:.1f} MB")
    print(f"\nTrain için:")
    print(f"  - Unsloth: https://github.com/unslothai/unsloth")
    print(f"  - Axolotl: https://github.com/OpenAccess-AI-Collective/axolotl")
    print(f"  - HF TRL: SFTTrainer + Qwen3-4B-Instruct + LoRA r=16")


if __name__ == "__main__":
    main()
