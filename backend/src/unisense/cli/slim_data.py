"""departments.json'dan runtime için inceltilmiş kopya üretir.

54MB'lık dosyanın ~%75'i sadece chunk üretiminde kullanılan osym_conditions
metinleri. Runtime bu dosyayı komple parse ederse bellek tepesi ~400MB'ı
bulur ve 512MB'lık free instance OOM olur. Docker build'de bu script
çalıştırılıp fat dosya imajdan silinir; runtime slim'i yükler (~13MB).

Kullanım: python -m unisense.cli.slim_data
"""
from __future__ import annotations

import json
from pathlib import Path

# Runtime'da hiçbir servisin kullanmadığı ağır alanlar
HEAVY_FIELDS = ("osym_conditions", "accreditation_full")


def main() -> None:
    proc = Path(__file__).resolve().parents[3] / "data" / "processed"
    src = proc / "departments.json"
    dst = proc / "departments_slim.json"

    departments = json.load(open(src, encoding="utf-8"))
    for d in departments:
        for f in HEAVY_FIELDS:
            d.pop(f, None)

    with open(dst, "w", encoding="utf-8") as f:
        json.dump(departments, f, ensure_ascii=False, separators=(",", ":"))

    print(f"slim yazildi: {dst} ({dst.stat().st_size / 1e6:.1f} MB "
          f"<- {src.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
