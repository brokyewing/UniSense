"""DGS endpoint keşif scripti."""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, "src")

from yokatlas_py.http_client import HttpClient
from yokatlas_py.config import Settings

h = HttpClient(settings=Settings())

print("=== DGS puanTuru varyasyonları ===")
for pt in ["DGS", "DGS_SAY", "DGS_SOZ", "DGS_EA", "DIKEY_GECIS", "ON_LISANS"]:
    body = {"filters": {"puanTuru": pt}, "page": 0, "size": 3}
    try:
        r = h.post_json("/api/tercih-kilavuz/search", json_body=body)
        total = r.get("totalElements", 0)
        first = r.get("content", [{}])[0] if r.get("content") else {}
        sinav = first.get("sinav", "?").strip()
        bt = first.get("birimTuruAdi", "?")
        print(f"  puanTuru={pt:15} | total={total} | sinav={sinav} | birimTuru={bt}")
    except Exception as e:
        print(f"  puanTuru={pt:15} | ERROR {str(e)[:80]}")

print("\n=== Sınav türü filtrelemesi ===")
for sinav in ["DGS", "ALES"]:
    body = {"filters": {"sinav": sinav}, "page": 0, "size": 3}
    try:
        r = h.post_json("/api/tercih-kilavuz/search", json_body=body)
        total = r.get("totalElements", 0)
        first = r.get("content", [{}])[0] if r.get("content") else {}
        print(f"  sinav={sinav:10} | total={total} | first.sinav={first.get('sinav', '?')}")
    except Exception as e:
        print(f"  sinav={sinav:10} | ERROR {str(e)[:80]}")

# Belki tabloTuru filter'i var (TABLO 3 = ön lisans, TABLO 4 = lisans)
print("\n=== tabloTuru filtrelemesi ===")
for t in ["TABLO 3", "TABLO 4", "TABLO 5", "DGS"]:
    body = {"filters": {"tabloTuru": t}, "page": 0, "size": 3}
    try:
        r = h.post_json("/api/tercih-kilavuz/search", json_body=body)
        total = r.get("totalElements", 0)
        first = r.get("content", [{}])[0] if r.get("content") else {}
        print(f"  tabloTuru={t:10} | total={total} | first.tabloTuru={first.get('tabloTuru', '?')}")
    except Exception as e:
        print(f"  tabloTuru={t:10} | ERROR {str(e)[:80]}")


# Farklı endpoint'ler
print("\n=== Farklı endpoint'ler ===")
for path in [
    "/api/dgs-tercih-kilavuzu/search",
    "/api/dgs-kilavuz/search",
    "/api/dgs/search",
    "/api/dikey-gecis/search",
    "/api/tercih-kilavuzu-dgs/search",
]:
    body = {"filters": {}, "page": 0, "size": 2}
    try:
        r = h.post_json(path, json_body=body)
        total = r.get("totalElements", 0)
        first = r.get("content", [{}])[0] if r.get("content") else {}
        if total > 0:
            print(f"  ✓ {path}: total={total} | sinav={first.get('sinav', '?')}")
        else:
            print(f"    {path}: total=0 (boş)")
    except Exception as e:
        msg = str(e)[:60]
        print(f"  ✗ {path}: {msg}")

h.close()
