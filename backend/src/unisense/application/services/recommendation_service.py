"""Tercih önerme servisi — puan/sıralama bazlı yapılandırılmış öneri."""
from __future__ import annotations

import json
import math
from functools import lru_cache
from pathlib import Path

from unisense.application.interfaces.vector_store import VectorStore
from unisense.core.config import get_settings
from unisense.core.logging import get_logger
from unisense.domain.models import Recommendation, RecommendationList, StudentProfile

logger = get_logger(__name__)


def placement_probability(
    user_rank: int | None,
    base_rank: int | None,
    q1_rank: int | None = None,
) -> float | None:
    """Yerleşme olasılığını sigmoid ile yumuşat.

    - user_rank == base_rank → 0.50 (medyan = yarı yarıya)
    - user_rank << base_rank → 0.90+ (rahat yerleşir)
    - user_rank >> base_rank → 0.10- (zor yerleşir)

    q1_rank verildiğinde (eski yıl en üst %25 sırası) eğri daha duyarlı.
    Yoksa base_rank'ın %15'i kadar varsayılan spread kullanılır.
    """
    if not user_rank or not base_rank or user_rank <= 0 or base_rank <= 0:
        return None
    if q1_rank and 0 < q1_rank < base_rank:
        spread = (base_rank - q1_rank) * 1.5
    else:
        spread = max(base_rank * 0.15, 50)
    # Küçük user_rank → büyük z → yüksek olasılık
    z = (base_rank - user_rank) / spread
    # Aşırı uçları sınırla (overflow korunması)
    z = max(min(z, 10.0), -10.0)
    prob = 1.0 / (1.0 + math.exp(-z))
    return round(prob, 3)


@lru_cache(maxsize=1)
def _load_data() -> tuple[list[dict], list[dict], dict[str, dict]]:
    """rankings + departments + universities lookup yükle."""
    settings = get_settings()
    proc = Path(settings.project_root) / "data" / "processed"

    rankings = json.load(open(proc / "rankings.json", encoding="utf-8"))

    # BELLEK: departments.json 54MB — komple parse etmek ~400MB tepe yapar
    # ve 512MB'lık instance'ı OOM'a sürükler. Docker build slim kopya üretir
    # (cli/slim_data.py); varsa onu yükle. Yoksa (lokal dev) full'ü yükleyip
    # ağır alanları at.
    slim = proc / "departments_slim.json"
    if slim.exists():
        departments = json.load(open(slim, encoding="utf-8"))
    else:
        departments = json.load(open(proc / "departments.json", encoding="utf-8"))
        for d in departments:
            d.pop("osym_conditions", None)
            d.pop("accreditation_full", None)

    universities = json.load(open(proc / "universities.json", encoding="utf-8"))
    uni_lookup = {u["code"]: u for u in universities}
    return rankings, departments, uni_lookup


def _tr_lower(s: str) -> str:
    return s.replace("İ", "i").replace("I", "ı").lower()


# Şehir adıyla başlayan üniversiteler ("İSTANBUL ÜNİVERSİTESİ" gibi) sadece
# "istanbul üniversitesi" tam öbeği geçerse eşleşir — yoksa her "istanbul"
# geçen sorgu o üniversiteye bağlanırdı.
_CITY_AMBIGUOUS = {
    "istanbul", "ankara", "izmir", "bursa", "adana", "antalya", "konya",
    "eskişehir", "samsun", "trabzon", "erzurum", "van", "gaziantep",
    "kayseri", "mersin", "malatya", "sivas", "denizli", "sakarya",
}


@lru_cache(maxsize=1)
def _uni_name_index() -> list[tuple[str, str, bool]]:
    """(arama_anahtarı, uni_code, şehir_adı_mı) listesi — uzun anahtar önce.

    Anahtarlar fold'lanır (aksansız): "cerrahpasa" da "cerrahpaşa" da eşleşir.
    """
    from unisense.core.text import fold_tr

    _, _, uni_lookup = _load_data()
    import re as _re

    # 1. tur: tam anahtarlar (tire → boşluk: "istanbul universitesi-cerrahpasa"
    # → "istanbul cerrahpasa")
    keys_by_code: dict[str, str] = {}
    for code, uni in uni_lookup.items():
        name = fold_tr(uni.get("name", "")).replace("-", " ")
        # "(ANKARA)", "(KKTC-GAZİMAĞUSA)" gibi şehir eklerini at
        name = _re.sub(r"\(.*?\)", " ", name)
        for word in ("universitesi", "universite", "university"):
            name = name.replace(word, " ")
        key = " ".join(name.split()).strip()
        if len(key) >= 3:
            keys_by_code[code] = key

    # 2. tur: çok kelimeli adların AYIRT EDİCİ kelimeleri de anahtar olsun
    # ("istanbul cerrahpasa" → "cerrahpasa"). Sadece TÜM üniversiteler içinde
    # benzersiz + yeterince uzun kelimeler — "teknik", "anadolu" gibi
    # çakışanlar/kısalar eklenmez (yanlış eşleşme riski).
    word_freq: dict[str, int] = {}
    for key in keys_by_code.values():
        for w in set(key.split()):
            word_freq[w] = word_freq.get(w, 0) + 1

    index: list[tuple[str, str, bool]] = []
    for code, key in keys_by_code.items():
        needs_phrase = key in _CITY_AMBIGUOUS or len(key) <= 4
        index.append((key, code, needs_phrase))
        for w in key.split():
            if len(w) >= 6 and word_freq[w] == 1 and w not in _CITY_AMBIGUOUS and w != key:
                index.append((w, code, False))
    index.sort(key=lambda x: -len(x[0]))
    return index


def detect_universities(query: str) -> list[str]:
    """Sorguda geçen üniversiteleri tespit et → uni code listesi.

    "hacettepe tıp kaç puan" → [Hacettepe kodu]. Şehir adlı üniversiteler
    ("İstanbul Üniversitesi") için "X üniversitesi" öbeği aranır.
    Sorgu ve anahtarlar fold'lu karşılaştırılır (ASCII yazım toleransı).
    """
    from unisense.core.text import fold_tr

    q = fold_tr(query)
    found: list[str] = []
    for key, code, ambiguous in _uni_name_index():
        if code in found:
            continue  # aynı üni hem tam adla hem kelimeyle eşleşebilir
        if ambiguous:
            if f"{key} universitesi" in q or f"{key} uni " in q:
                found.append(code)
        elif key in q:
            found.append(code)
    return found


class RecommendationService:
    """Sıralama bazlı tercih önerme servisi."""

    def __init__(self, store: VectorStore) -> None:
        self._store = store

    def lookup_programs(self, codes: list[str]) -> list[dict]:
        """Verilen department_code listesi için isim/üni/sıra/taban/kontenjan bilgilerini döner.

        Eski tercih listelerinde eksik kalan rank/score bilgilerini doldurmak için kullanılır.
        """
        if not codes:
            return []
        rankings, departments, uni_lookup = _load_data()
        dept_lookup = {d["code"]: d for d in departments}
        rank_lookup = {r["department_code"]: r for r in rankings}

        out: list[dict] = []
        for code in codes:
            code_str = str(code)
            dept = dept_lookup.get(code_str)
            if not dept:
                out.append({"department_code": code_str, "found": False})
                continue
            uni = uni_lookup.get(dept.get("university_code", ""), {})
            r = rank_lookup.get(code_str, {})
            out.append({
                "department_code": code_str,
                "found": True,
                "department_name": dept.get("name", ""),
                "department_group_name": dept.get("group_name", "") or dept.get("name", ""),
                "university_code": dept.get("university_code", ""),
                "university_name": uni.get("name", ""),
                "city": dept.get("city", ""),
                "score_type": dept.get("score_type", ""),
                "education_language": dept.get("education_language", ""),
                "scholarship": dept.get("scholarship", ""),
                "last_year_base_rank": r.get("base_rank"),
                "last_year_base_score": r.get("base_score"),
                "quota": r.get("quota"),
            })
        return out

    def list_programs(
        self,
        *,
        cities: list[str] | None = None,
        uni_codes: list[str] | None = None,
        dept_keywords: list[str] | None = None,
        limit: int = 30,
    ) -> dict:
        """Şehir/üniversite/bölüm filtresine uyan programları listeler.

        "İstanbul'daki tıp fakülteleri kaç puan, kaç kişi alıyor?" gibi
        SIRA/PUAN VERİLMEDEN sorulan envanter sorularını yapısal veriden
        cevaplamak için — RAG'in top_k limiti bu tür soruları eksik bırakır.
        """
        rankings, departments, uni_lookup = _load_data()
        rank_lookup = {r["department_code"]: r for r in rankings}

        from unisense.core.text import fold_tr

        # Şehirler geo.REGIONS'tan Türkçe büyük harfle gelir ("İSTANBUL")
        want_cities = {c.upper() for c in (cities or [])}
        # fold'lu kıyas: ASCII yazımlı anahtar ("pastacilik") da isabet eder
        kw_lower = [fold_tr(k) for k in (dept_keywords or [])]

        results: list[dict] = []
        total_quota = 0
        for d in departments:
            if kw_lower and not any(kw in fold_tr(d.get("name", "")) for kw in kw_lower):
                continue
            if want_cities and d.get("city", "").upper() not in want_cities:
                continue
            if uni_codes and d.get("university_code", "") not in uni_codes:
                continue
            r = rank_lookup.get(d["code"], {})
            uni = uni_lookup.get(d.get("university_code", ""), {})
            quota = r.get("quota")
            if isinstance(quota, int):
                total_quota += quota
            results.append({
                "department_code": d["code"],
                "department_name": d.get("name", ""),
                "university_name": uni.get("name", ""),
                "university_type": uni.get("type", ""),
                "city": d.get("city", ""),
                "score_type": d.get("score_type", ""),
                "base_rank": r.get("base_rank"),
                "base_score": r.get("base_score"),
                "quota": quota,
                "scholarship": d.get("scholarship", ""),
            })

        # En iyi (küçük) sıradan kötüye; sırası olmayanlar sona
        results.sort(key=lambda x: (x["base_rank"] is None, x["base_rank"] or 0))
        return {
            "programs": results[:limit],
            "total": len(results),
            "total_quota": total_quota,
        }

    def recommend(self, profile: StudentProfile) -> RecommendationList:
        if profile.rank is None and profile.score is None:
            return RecommendationList(
                profile=profile,
                notes="Lütfen sıralama veya puan girin.",
            )

        rankings, departments, uni_lookup = _load_data()
        dept_lookup = {d["code"]: d for d in departments}
        st = profile.score_type.value if hasattr(profile.score_type, "value") else str(profile.score_type)

        # Filter rankings: aynı puan türü + base_rank var
        candidates = [
            r for r in rankings
            if r.get("score_type") == st
            and r.get("base_rank") is not None
            and r.get("base_score") is not None
        ]

        if not candidates:
            return RecommendationList(
                profile=profile,
                notes=f"{st} puan türünde sıralama verisi bulunamadı.",
            )

        # Kullanıcının sıralaması yoksa, puanından tahmin et
        user_rank = profile.rank
        if user_rank is None and profile.score is not None:
            # Yakın puanlı programdan tahmin et
            sorted_by_score = sorted(candidates, key=lambda r: abs(r["base_score"] - profile.score))
            if sorted_by_score:
                user_rank = sorted_by_score[0]["base_rank"]

        if user_rank is None:
            return RecommendationList(
                profile=profile,
                notes="Sıralama hesaplanamadı.",
            )

        # 3 kategori
        # safe:   user_rank * 1.5 < program_rank (rahat yerleşir)
        # target: user_rank * 0.7 < program_rank <= user_rank * 1.5  (uygun)
        # reach:  user_rank * 0.5 < program_rank <= user_rank * 0.7  (zorlama)
        safe = []
        target = []
        reach = []

        for r in candidates:
            prog_rank = r["base_rank"]
            dept = dept_lookup.get(r["department_code"])
            if not dept:
                continue
            uni = uni_lookup.get(dept.get("university_code", ""))
            if not uni:
                continue

            # Filter: tercih edilemez (min_basari_sirasi_kosul kullanıcının üstünde)
            min_kosul = r.get("min_basari_sirasi_kosul")
            if min_kosul:
                try:
                    if user_rank > int(min_kosul):
                        continue  # şartı sağlamıyor
                except (ValueError, TypeError):
                    pass

            # Şehir filtresi
            if profile.preferred_cities and dept.get("city", "").upper() not in [c.upper() for c in profile.preferred_cities]:
                continue
            # Üni türü filtresi (case-insensitive)
            if profile.preferred_uni_types:
                uni_type = (uni.get("type") or "").upper()
                wanted = [t.upper() for t in profile.preferred_uni_types]
                # KKTC için de eşleştir
                if uni_type not in wanted and not (
                    "KKTC" in wanted and "KKTC" in (uni.get("city", "") or "").upper()
                ):
                    continue

            # Coğrafi filtreler (AskService'ten gelen geo_flags)
            geo_flags = getattr(profile, "_geo_flags", []) or []
            if geo_flags:
                # uni veya dept enriched alanlarını oku
                is_coastal = uni.get("is_coastal") or dept.get("is_coastal", False)
                is_metropolis = uni.get("is_metropolis") or dept.get("is_metropolis", False)
                is_central = uni.get("is_central_district") or dept.get("is_central_district", False)
                seas = uni.get("seas") or dept.get("seas") or []

                if "coastal" in geo_flags and not is_coastal:
                    continue
                if "inland" in geo_flags and is_coastal:
                    continue
                if "central" in geo_flags and not is_central:
                    continue
                if "metropolis" in geo_flags and not is_metropolis:
                    continue
                # Spesifik deniz filtresi
                sea_map = {
                    "sea_karadeniz": "Karadeniz",
                    "sea_marmara": "Marmara",
                    "sea_ege": "Ege",
                    "sea_akdeniz": "Akdeniz",
                }
                requested_seas = [sea_map[f] for f in geo_flags if f in sea_map]
                if requested_seas and not any(s in seas for s in requested_seas):
                    continue
            # Bölüm filtresi
            if profile.preferred_departments:
                dept_match = False
                for prefer in profile.preferred_departments:
                    if prefer.lower() in dept.get("name", "").lower() or prefer.lower() in dept.get("group_name", "").lower():
                        dept_match = True
                        break
                if not dept_match:
                    continue

            # Kategoriye göre uyum
            ratio = prog_rank / user_rank if user_rank > 0 else float('inf')

            prob = placement_probability(
                user_rank=user_rank,
                base_rank=prog_rank,
                q1_rank=r.get("rank_q1"),
            )
            rec = Recommendation(
                department_code=r["department_code"],
                university_code=dept["university_code"],
                department_name=dept["name"],
                university_name=uni["name"],
                city=dept.get("city", ""),
                score_type=profile.score_type,
                fit_score=min(100.0, max(0.0, 100 - abs(ratio - 1.0) * 50)),
                safety_level="",
                placement_probability=prob,
                last_year_base_rank=prog_rank,
                last_year_base_score=r["base_score"],
                quota=r.get("quota"),
                scholarship=dept.get("scholarship", ""),
                education_language=dept.get("education_language", ""),
                duration_years=dept.get("duration_years"),
                osym_conditions=(dept.get("osym_conditions") or {}).get("summary", [])[:4],
                trend=r.get("history", []),
            )

            if ratio >= 1.5:
                rec.safety_level = "safe"
                rec.reason = f"Senin sıralaman ({user_rank:,}) bu programın taban sıralamasından ({prog_rank:,}) iyi — rahat yerleşirsin"
                safe.append(rec)
            elif ratio >= 0.85:
                rec.safety_level = "target"
                rec.reason = f"Bu programın taban sıralaması ({prog_rank:,}) senin seviyene uygun"
                target.append(rec)
            elif ratio >= 0.5:
                rec.safety_level = "reach"
                rec.reason = f"Bu program biraz hedef üstü ({prog_rank:,}) — denenebilir"
                reach.append(rec)

        # Her kategoride en iyi 30'unu al (taban sırasına göre)
        safe.sort(key=lambda x: x.last_year_base_rank or 999_999)
        target.sort(key=lambda x: x.last_year_base_rank or 999_999)
        reach.sort(key=lambda x: x.last_year_base_rank or 999_999)

        return RecommendationList(
            profile=profile,
            safe=safe[:30],
            target=target[:30],
            reach=reach[:30],
            notes=(
                f"Senin sıralaman: {user_rank:,} ({st}) | "
                f"Toplam aday: {len(candidates):,} program"
            ),
        )
