#!/bin/sh
# Commit öncesi kalite kapısı — ruff + hızlı test.
#
# NEDEN VAR: 2026-09-05'te CI 4 saat boyunca 18 commit kırmızı kaldı ve kimse
# fark etmedi. Lint düzeltmeleri iki kez commit'lendi, iki kez de başka bir
# ajanın çalışma kopyası üzerine yazınca geri gitti. Kırmızı CI'a alışmak
# gerçek hataları görünmez yapıyor (Careerjet tarih hatası ve açık-ilan
# budaması tam bu yüzden günlerce fark edilmedi).
#
# KURULUM (her araç kendi tarafında bir kez yapar):
#   git config core.hooksPath scripts/githooks
#   mkdir -p scripts/githooks && cp scripts/pre-commit.sh scripts/githooks/pre-commit
#   chmod +x scripts/githooks/pre-commit
#
# ATLAMAK (yalnız gerçekten gerekliyse):  git commit --no-verify

set -e

# Yalnız backend Python dosyaları stage'lenmişse çalış
DEGISEN=$(git diff --cached --name-only --diff-filter=ACM | grep -E '^backend/.*\.py$' || true)
[ -z "$DEGISEN" ] && exit 0

cd backend || exit 0

if ! command -v ruff >/dev/null 2>&1 && ! python -m ruff --version >/dev/null 2>&1; then
    echo "pre-commit: ruff bulunamadi, atlanıyor (pip install -e '.[dev]')"
    exit 0
fi

RUFF="ruff"
command -v ruff >/dev/null 2>&1 || RUFF="python -m ruff"

echo "pre-commit: ruff check..."
if ! $RUFF check src tests; then
    echo ""
    echo "  ✗ Lint hatasi var. Duzeltmek icin:  cd backend && ruff check src tests --fix"
    echo "    Zorunlu hallerde:  git commit --no-verify"
    exit 1
fi

echo "pre-commit: pytest..."
if ! python -m pytest tests -q --no-header -x; then
    echo ""
    echo "  ✗ Test kirik. Kirmizi CI'a alismak gercek hatalari gizliyor."
    echo "    Zorunlu hallerde:  git commit --no-verify"
    exit 1
fi

echo "pre-commit: temiz."
