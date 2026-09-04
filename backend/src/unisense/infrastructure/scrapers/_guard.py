"""Scraper çıktısı yazarken veri kaybına karşı bekçi.

Neden var: kpss_scraper 2026-07-27'de kaynağa erişemedi, boş liste üretti ve
sonucu KOŞULSUZ dosyaya yazdı. 1.027.352 byte'lık kpss_placements.json `[]`
oldu, script exit 0 döndüğü için workflow "success" deyip commit'ledi ve
prod'da KPSS geçmiş taban özelliği 6 hafta boyunca boş kaldı (commit e9ece83).

Kural: bir scrape boş döndüyse ya da mevcut veriyi ciddi biçimde küçültüyorsa
bu bir kaynak arızasıdır, veri güncellemesi değil. Dosyaya DOKUNMA ve sıfırdan
farklı kod ile çık — sessiz başarı yerine kırmızı workflow.
"""
from __future__ import annotations

import json
from pathlib import Path

# Mevcut kayıt sayısının bu oranından azına düşen sonuç şüpheli sayılır.
SHRINK_LIMIT = 0.5


class ScrapeGuardError(RuntimeError):
    """Sonuç şüpheli — çağıran sıfırdan farklı kodla çıkmalı."""


def _existing_count(path: Path) -> int:
    if not path.exists():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return 0
    return len(data) if isinstance(data, (list, dict)) else 0


def write_json_guarded(path: Path, records, *, label: str, force: bool = False) -> None:
    """records'u path'e yaz — ama boşsa/ciddi küçülüyorsa yazma, hata fırlat.

    force=True bekçiyi atlar (kaynak gerçekten küçüldüyse elle kullanılır).
    """
    new = len(records)
    old = _existing_count(path)

    if not force:
        if new == 0:
            raise ScrapeGuardError(
                f"{label}: hiç kayıt üretilemedi, mevcut {old} kayıt KORUNUYOR "
                f"(dosyaya dokunulmadı). Kaynak erişilemiyor olabilir."
            )
        if old and new < old * SHRINK_LIMIT:
            raise ScrapeGuardError(
                f"{label}: sonuç {new} kayıt, mevcut {old} kaydın "
                f"%{SHRINK_LIMIT * 100:.0f}'inden az — şüpheli, dosyaya dokunulmadı. "
                f"Gerçekten küçüldüyse --force ile çalıştır."
            )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"✅ {new} kayıt → {path}" + (f"  (önceki: {old})" if old else ""))
