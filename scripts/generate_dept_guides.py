"""604 bölüm grubu için meslek/bölüm tanıtımları üretir (Gemini, tek seferlik).

"Endüstri mühendisi ne iş yapar?" tarzı sorulara kaynaklı cevap verebilmek
için her bölüm grubuna yapılandırılmış bir tanıtım metni üretir. Halüsinasyon
önlemleri:
  - Spesifik maaş rakamı, istihdam yüzdesi, istatistik YASAK (prompt'ta)
  - Nitel bilgi: görevler, sektörler, dersler, kimlere uygun
  - Chunk kaynağı şeffaf: "Bölüm Rehberi (yapay zeka destekli özet)"

Resume destekli: kısmi çıktı dosyasına yazar, tekrar çalıştırılırsa kaldığı
yerden devam eder. Key rotasyonu + 429 backoff var.

Kullanım: cd backend && python ../scripts/generate_dept_guides.py
Çıktı:    backend/data/processed/dept_guides.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1] / "backend"
sys.path.insert(0, str(BACKEND / "src"))
OUT = BACKEND / "data" / "processed" / "dept_guides.json"

# Kota havuzları model bazında ayrı — biri dolunca diğerine geç
MODELS = ["gemini-2.5-flash-lite", "gemini-2.5-flash"]
# Free tier: ~10-15 RPM/key — key başına 6sn aralık bırak
MIN_INTERVAL_PER_KEY_S = 6.0

PROMPT = """Türkiye'de üniversite tercihi yapan lise öğrencileri için "{name}" bölümünün tanıtımını yaz.

Bölüm kategorisi: {category}
Bu bölümün Türkiye'de {count} programı var.

Şu başlıklarla, madde işaretli, toplam 150-220 kelime:
🎓 Bölüm nedir: 1-2 cümle, sade dille
📚 Tipik dersler: 4-6 ders adı
💼 Mezunlar ne iş yapar: somut görev/pozisyon örnekleri
🏢 Çalışılan sektörler: 3-5 sektör
🧭 Kimler için uygun: ilgi/beceri profili

KESIN KURALLAR:
- Maaş RAKAMI verme (aralık bile verme) — istersen "deneyim ve sektöre göre değişir" de
- İstihdam oranı, işsizlik yüzdesi gibi İSTATİSTİK verme
- Üniversite adı verme (bu genel bölüm tanıtımı)
- Uydurma sertifika/yasal koşul yazma; emin olmadığını yazma
- Türkçe, samimi ama bilgilendirici ton"""


def main() -> None:
    import google.generativeai as genai

    from unisense.application.services.compass_service import CompassService  # noqa: F401 (path check)
    from unisense.application.services.compass_taxonomy import get_taxonomy
    from unisense.core.config import get_settings

    settings = get_settings()
    keys = settings.gemini_keys_list
    if not keys:
        sys.exit("GEMINI_API_KEYS gerekli (backend/.env)")

    taxonomy = get_taxonomy()
    cat_labels = {k: v["label"] for k, v in taxonomy["categories"].items()}
    groups = taxonomy["departments"]
    print(f"Toplam {len(groups)} bölüm grubu | {len(keys)} key | modeller: {MODELS}")
    dead: set[tuple[int, str]] = set()  # (key_idx, model) → kotası bitenler

    guides: dict[str, dict] = {}
    if OUT.exists():
        guides = {g["name"]: g for g in json.load(open(OUT, encoding="utf-8"))}
        print(f"↻ Resume: {len(guides)} tanıtım zaten var")

    todo = [g for g in groups if g["name"] not in guides]
    last_call: dict[int, float] = {}
    done, fail = 0, 0

    for i, g in enumerate(todo):
        prompt = PROMPT.format(
            name=g["name"],
            category=cat_labels.get(g["category"], g["category"]),
            count=g["program_count"],
        )
        text = None
        combos = [(ki, m) for m in MODELS for ki in range(len(keys))
                  if (ki, m) not in dead]
        if not combos:
            print("   ⛔ Tüm key×model kotaları doldu — resume ile sonra devam edilebilir")
            break
        for ki, model_name in combos:
            # RPM pacing (key bazlı)
            wait = MIN_INTERVAL_PER_KEY_S - (time.time() - last_call.get(ki, 0))
            if wait > 0:
                time.sleep(wait)
            last_call[ki] = time.time()
            try:
                genai.configure(api_key=keys[ki])
                model = genai.GenerativeModel(model_name)
                resp = model.generate_content(prompt)
                text = (resp.text or "").strip()
                if len(text) > 200:
                    break
                text = None
            except Exception as e:  # noqa: BLE001
                msg = str(e)
                if "429" in msg[:60] or "quota" in msg[:200].lower():
                    if "PerDay" in msg:
                        # Günlük kota gerçekten bitti — bu kombo bugünlük ölü
                        print(f"   ⏳ günlük kota: key{ki}×{model_name} devre dışı")
                        dead.add((ki, model_name))
                    else:
                        # Dakikalık patlama — bekle, kombo YAŞIYOR
                        time.sleep(20)
                else:
                    print(f"   ⚠️ {g['name']}: {msg[:100]}")
        if text:
            guides[g["name"]] = {
                "name": g["name"],
                "category": g["category"],
                "program_count": g["program_count"],
                "content": text,
            }
            done += 1
        else:
            fail += 1

        if (i + 1) % 10 == 0 or i == len(todo) - 1:
            json.dump(list(guides.values()), open(OUT, "w", encoding="utf-8"),
                      ensure_ascii=False, indent=1)
            print(f"   {len(guides)}/{len(groups)} tamam (bu tur: +{done}, hata: {fail})",
                  flush=True)

    json.dump(list(guides.values()), open(OUT, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print(f"✅ {len(guides)} tanıtım → {OUT}")


if __name__ == "__main__":
    main()
