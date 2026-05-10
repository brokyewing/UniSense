"""UniSense Tester — backend'e bir sorgu seti gönderir, markdown rapor üretir.

Kullanım:
    python scripts/test_queries.py
    python scripts/test_queries.py --base http://localhost:8002 --top-k 8
    python scripts/test_queries.py --category siralama_intent
    python scripts/test_queries.py --query "İskenderun Teknik Üni"
    python scripts/test_queries.py --only-failed   # sadece başarısızları yeniden çalıştır

Çıktı:
    backend/scripts/reports/test_report_<timestamp>.md
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from datetime import datetime
from pathlib import Path

import urllib.request
import urllib.error

# Renk
class C:
    RST = "\033[0m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    CYAN = "\033[36m"
    GREY = "\033[90m"
    BOLD = "\033[1m"


SCRIPT_DIR = Path(__file__).parent
QUERIES_FILE = SCRIPT_DIR / "test_queries.json"
REPORTS_DIR = SCRIPT_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def post_ask(base_url: str, query: str, top_k: int = 8, timeout: int = 60) -> dict:
    """POST /api/v1/ask — return parsed JSON or {error: ...}."""
    url = f"{base_url.rstrip('/')}/api/v1/ask"
    payload = json.dumps({"query": query, "top_k": top_k}).encode("utf-8")
    req = urllib.request.Request(
        url, data=payload, method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode("utf-8"))
            data["_status"] = r.status
            return data
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}", "_status": e.code}
    except urllib.error.URLError as e:
        return {"error": f"URLError: {e.reason}", "_status": 0}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {str(e)[:200]}", "_status": -1}


def classify_response(resp: dict) -> tuple[str, str]:
    """(emoji_status, kısa açıklama) — bir cevabı sınıflandır."""
    if "error" in resp:
        return "❌", f"hata: {resp['error']}"
    text = (resp.get("text") or "").strip()
    if not text:
        return "❌", "boş cevap"
    if text.startswith("⚠️"):
        return "❌", "LLM error/quota"
    low = text.lower()
    # Yetersiz cevap işaretleri
    bad_phrases = [
        "kaynaklarımda yok", "kaynaklarımda bulunmamak", "bilgi bulunmamak",
        "kaynaklarımda bilgi", "üzgünüm", "bulamadım", "yok", "i don't have",
    ]
    if any(p in low for p in bad_phrases):
        # Ama "kaynaklarımda" sadece ek not olarak da geçebilir; sayı içeriyorsa muhtemelen iyi
        has_numbers = any(c.isdigit() for c in text[:300])
        if not has_numbers:
            return "⚠️", "yetersiz/uydurulmamış cevap"
    if len(text) < 60:
        return "⚠️", f"çok kısa ({len(text)} char)"
    return "✅", f"{len(text)} char"


def short(s: str, n: int = 220) -> str:
    s = (s or "").strip().replace("\n", " ")
    return s[:n] + ("…" if len(s) > n else "")


def run(args):
    queries_data = json.loads(QUERIES_FILE.read_text(encoding="utf-8"))

    # Filtre uygula
    if args.query:
        all_queries = [{"category": "manual", "query": args.query}]
    else:
        all_queries = []
        for cat in queries_data["categories"]:
            if args.category and cat["id"] != args.category:
                continue
            for q in cat["queries"]:
                all_queries.append({
                    "category": cat["id"],
                    "category_label": cat["label"],
                    "query": q,
                })

    if not all_queries:
        print(f"{C.RED}Sorgu bulunamadı (filtre uyumsuz?){C.RST}")
        return 1

    total = len(all_queries)
    print(f"{C.BOLD}{C.CYAN}UniSense Tester{C.RST}")
    print(f"  Backend: {C.GREY}{args.base}{C.RST}")
    print(f"  Sorgu sayısı: {C.BOLD}{total}{C.RST}\n")

    results = []
    t0 = time.time()
    fail_count = warn_count = ok_count = 0

    for i, item in enumerate(all_queries, 1):
        q = item["query"]
        cat = item.get("category_label") or item.get("category", "")
        print(f"{C.GREY}[{i:>2}/{total}]{C.RST} ", end="", flush=True)

        start = time.time()
        resp = post_ask(args.base, q, top_k=args.top_k, timeout=args.timeout)
        elapsed_ms = int((time.time() - start) * 1000)
        emoji, summary = classify_response(resp)

        if emoji == "❌":
            fail_count += 1
            color = C.RED
        elif emoji == "⚠️":
            warn_count += 1
            color = C.YELLOW
        else:
            ok_count += 1
            color = C.GREEN

        print(
            f"{emoji} {color}{q[:55]:<55}{C.RST}  "
            f"{C.GREY}{elapsed_ms:>5}ms · {summary}{C.RST}"
        )

        results.append({
            "category": cat,
            "category_id": item.get("category", ""),
            "query": q,
            "elapsed_ms": elapsed_ms,
            "status": emoji,
            "summary": summary,
            "response": resp,
        })

    total_elapsed = time.time() - t0
    print(
        f"\n{C.BOLD}Özet:{C.RST} "
        f"{C.GREEN}✅ {ok_count}{C.RST}  "
        f"{C.YELLOW}⚠️  {warn_count}{C.RST}  "
        f"{C.RED}❌ {fail_count}{C.RST}  "
        f"({total_elapsed:.1f}s, ortalama {total_elapsed/total:.1f}s/sorgu)"
    )

    # Raporu yaz
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORTS_DIR / f"test_report_{ts}.md"
    write_report(report_path, results, args, ok_count, warn_count, fail_count, total_elapsed)
    print(f"\n📄 Rapor: {C.CYAN}{report_path}{C.RST}")

    # JSON dökümü (--only-failed için lazım)
    json_path = REPORTS_DIR / f"test_results_{ts}.json"
    json_path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")

    # Failed listesi var mı söyle
    if fail_count + warn_count > 0:
        print(f"\n{C.YELLOW}⚠️  {fail_count + warn_count} sorgu yetersiz/hatalı — raporu incele.{C.RST}")
        print(f"   Sorunlu olanları kullanıcıya sunup düzeltme planı yapabilirsin.")
    return 0


def write_report(path: Path, results: list[dict], args, ok, warn, fail, elapsed) -> None:
    lines = []
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    lines.append(f"# UniSense Test Raporu")
    lines.append(f"")
    lines.append(f"**Tarih:** {ts}  ")
    lines.append(f"**Backend:** `{args.base}`  ")
    lines.append(f"**Top-K:** {args.top_k}  ")
    lines.append(f"")
    lines.append(f"## Özet")
    lines.append(f"")
    lines.append(f"| | Sayı |")
    lines.append(f"|---|---:|")
    lines.append(f"| ✅ Başarılı | {ok} |")
    lines.append(f"| ⚠️ Yetersiz/kısa | {warn} |")
    lines.append(f"| ❌ Hata/boş | {fail} |")
    lines.append(f"| **Toplam** | **{len(results)}** |")
    lines.append(f"| Toplam süre | {elapsed:.1f}s |")
    lines.append(f"")

    # Kategoriye göre grupla
    by_cat: dict[str, list[dict]] = {}
    for r in results:
        by_cat.setdefault(r["category"], []).append(r)

    # Önce SORUNLULAR ayrı bir bölüm olarak çıksın
    problems = [r for r in results if r["status"] in ("❌", "⚠️")]
    if problems:
        lines.append(f"## 🔥 Düzeltilmesi Gerekenler ({len(problems)})")
        lines.append(f"")
        lines.append(f"| # | Sorgu | Durum | Sebep |")
        lines.append(f"|---|---|:-:|---|")
        for i, r in enumerate(problems, 1):
            q = r["query"].replace("|", "\\|")
            lines.append(f"| {i} | `{q}` | {r['status']} | {r['summary']} |")
        lines.append(f"")
        lines.append(f"---")
        lines.append(f"")

    # Detaylı sonuçlar
    for cat_label, items in by_cat.items():
        lines.append(f"## {cat_label} ({len(items)})")
        lines.append(f"")
        for r in items:
            lines.append(f"### {r['status']} `{r['query']}`")
            lines.append(f"")
            lines.append(f"- **Süre:** {r['elapsed_ms']} ms")
            lines.append(f"- **Durum:** {r['summary']}")
            resp = r["response"]
            docs = resp.get("docs") or []
            lines.append(f"- **Kaynaklar:** {len(docs)}")
            text = resp.get("text") or resp.get("error") or "(yanıt yok)"
            lines.append(f"")
            lines.append(f"**Cevap:**")
            lines.append(f"")
            lines.append(f"> " + text.strip().replace("\n", "\n> "))
            lines.append(f"")
            if docs:
                lines.append(f"<details><summary>Top kaynaklar ({min(len(docs),5)})</summary>")
                lines.append(f"")
                for d in docs[:5]:
                    src = d.get("source", "?")
                    snippet = short((d.get("content") or ""), 180)
                    lines.append(f"- **{src}**: {snippet}")
                lines.append(f"")
                lines.append(f"</details>")
                lines.append(f"")
            lines.append(f"---")
            lines.append(f"")

    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description="UniSense API tester")
    p.add_argument("--base", default="http://localhost:8002")
    p.add_argument("--top-k", type=int, default=8)
    p.add_argument("--timeout", type=int, default=60)
    p.add_argument("--category", help="Sadece bu kategori")
    p.add_argument("--query", help="Tek bir sorgu çalıştır")
    args = p.parse_args()

    if not QUERIES_FILE.exists():
        print(f"{C.RED}Sorgu seti bulunamadı: {QUERIES_FILE}{C.RST}")
        sys.exit(1)

    sys.exit(run(args))


if __name__ == "__main__":
    main()
