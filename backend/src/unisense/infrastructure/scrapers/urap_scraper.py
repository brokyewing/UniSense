"""URAP Türkiye sıralaması — PDF parse.

URAP 2025-2026 basın bildirisi PDF'inden 190 üniversite sıralamasını çıkarır.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

if sys.platform == "win32":
    import io as _io
    sys.stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

import fitz  # PyMuPDF


# Üni adı pattern: "İSTANBUL TEKNİK ÜNİVERSİTESİ", "KOÇ ÜNİVERSİTESİ"
# vb. — sonunda ÜNİVERSİTESİ var
UNI_RE = re.compile(
    r"^([A-ZÇĞİÖŞÜ\.\-\s\(\)]+ÜNİVERSİTESİ)\s*$",
    re.MULTILINE,
)

# Sıra ve puan: "1\n1152,95" veya "1 1152,95"
RANK_RE = re.compile(r"^\s*(\d{1,3})\s*$", re.MULTILINE)
SCORE_RE = re.compile(r"^\s*(\d{2,4}[,.]\d+)\s*$", re.MULTILINE)


def parse_urap_pdf(pdf_path: Path) -> list[dict]:
    doc = fitz.open(pdf_path)

    # Tüm metni topla
    full_text = ""
    for page in doc:
        full_text += page.get_text("text") + "\n"

    doc.close()

    # Satır satır işle: "ÜNİ ADI\nSIRA\nPUAN" pattern'i
    lines = [l.strip() for l in full_text.split("\n") if l.strip()]

    rankings: list[dict] = []
    seen: set[tuple[str, int]] = set()

    i = 0
    while i < len(lines) - 2:
        line = lines[i]
        # Üniversite satırı?
        if "ÜNİVERSİTESİ" in line and len(line) > 10 and len(line) < 80:
            # Sonraki 1-3 satırda sıra + puan ara
            for j in range(i + 1, min(i + 4, len(lines))):
                next_line = lines[j]
                # Sıra (1-300 arası)
                m_rank = re.fullmatch(r"\d{1,3}", next_line)
                if m_rank:
                    rank = int(next_line)
                    if 1 <= rank <= 300:
                        # Puan sonraki satırda mı?
                        for k in range(j + 1, min(j + 3, len(lines))):
                            score_line = lines[k]
                            m_score = re.fullmatch(r"\d{2,4}[,.]\d+", score_line)
                            if m_score:
                                score = float(score_line.replace(",", "."))
                                key = (line, rank)
                                if key not in seen and 100 <= score <= 5000:
                                    seen.add(key)
                                    rankings.append({
                                        "rank": rank,
                                        "name": line,
                                        "score": score,
                                    })
                                break
                        break
        i += 1

    return rankings


def main() -> None:
    project_root = Path(__file__).resolve().parents[4]
    pdf_path = project_root / "data" / "raw" / "urap_2025_2026.pdf"
    out_dir = project_root / "data" / "raw" / "urap"
    out_dir.mkdir(parents=True, exist_ok=True)

    if not pdf_path.exists():
        print(f"❌ PDF bulunamadı: {pdf_path}")
        return

    print(f"📄 PDF parse: {pdf_path.name}")
    rankings = parse_urap_pdf(pdf_path)

    # Sırayla sırala (rank ascending)
    rankings.sort(key=lambda r: r["rank"])

    out_file = out_dir / "urap_2025_2026.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(rankings, f, ensure_ascii=False, indent=2)

    print(f"✅ {len(rankings)} üniversite sıralaması")
    print(f"📁 {out_file}\n")
    print("İlk 10:")
    for r in rankings[:10]:
        print(f"  {r['rank']:>3}. {r['name']:<55} {r['score']}")


if __name__ == "__main__":
    main()
