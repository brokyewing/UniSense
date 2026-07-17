"""API v1 — routes."""
# NOT: `from __future__ import annotations` BİLEREK YOK. slowapi'nin
# @limiter.limit dekoratörü fonksiyonu sarmalar; string annotation'lar
# sarmalayıcının __globals__'ında çözülemez ve FastAPI body parametrelerini
# query param sanır (tüm istekler 422 döner).
import re

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi import Query as ApiQuery  # domain.models.Query ile ad çakışmasın

from unisense.api.v1.dependencies import (
    ask_service_dep,
    compare_service_dep,
    compass_service_dep,
    dgs_service_dep,
    guide_service_dep,
    kpss_service_dep,
    lgs_service_dep,
    tus_service_dep,
    news_service_dep,
    recommendation_service_dep,
)
from unisense.api.v1.schemas import (
    AskRequest,
    AskResponse,
    SiralamaResponse,
    CompareRequest,
    CompareResponse,
    CompassAxesRequest,
    CompassInterestsRequest,
    CompassInterestsTaxonomyResponse,
    CompassResponse,
    CompassSelectionRequest,
    CompassTaxonomyResponse,
    CompassTextRequest,
    DgsGecisRequest,
    DgsGecisResponse,
    DgsProgramRequest,
    DgsProgramResponse,
    ExamCalendarResponse,
    GuideDetailResponse,
    GuideListResponse,
    DocResponse,
    HealthResponse,
    LgsIlcelerResponse,
    LgsIllerResponse,
    LgsOneriRequest,
    LgsOneriResponse,
    TusMetaResponse,
    TusOneriRequest,
    TusOneriResponse,
    KpssKadroRequest,
    KpssKadroResponse,
    ModelInfo,
    ModelsResponse,
    ProgramLookupRequest,
    ProgramLookupResponse,
    RecommendResponse,
    StudentProfileRequest,
)
from unisense.application.services import (
    AskService,
    CompareService,
    CompassService,
    RecommendationService,
)
from unisense.api.middleware.rate_limit import (
    ASK_DAILY_GLOBAL_LIMIT,
    ASK_DAILY_LIMIT,
    ASK_LIMIT,
    DEFAULT_LIMIT,
    _global_key,
    limiter,
)
from unisense.core.di import get_vector_store
from unisense.core.logging import get_logger
from unisense.domain.models import Query, StudentProfile
from unisense.security.audit_log import audit
from unisense.security.auth import require_api_key
from unisense.security.firebase_auth import require_user
from unisense.security.input_sanitizer import sanitize_history_text, sanitize_query

router = APIRouter(prefix="/api/v1", tags=["v1"])
logger = get_logger(__name__)

# LLM cevabındaki ÖSYM program kodları (9 hane) — doğrulama için
_OSYM_CODE_RE = re.compile(r"\b(\d{9})\b")


@router.get("/health", response_model=HealthResponse)
def health(response: Response) -> HealthResponse:
    """Sağlık kontrolü.

    Index boşsa 'degraded' ama 200: eskiden 503 dönüyordu ve HF kesintisinde
    (index inemeyince) Render health-check'i instance'ı öldürüp crash-loop
    yaratıyordu. RAG-dışı her şey (takvim/robotlar/öneri/hesap) chroma'sız
    çalıştığı için instance TRAFİKTE KALMALI; yalnız /ask degraded olur ve
    arka plan görevi (lifespan) index'i HF dönünce kendiliğinden indirir.
    """
    try:
        count = get_vector_store().count()
    except Exception:  # noqa: BLE001
        count = None
    status = "ok" if count else "degraded"
    return HealthResponse(status=status, version="0.1.0", chunks_count=count)


@router.get("/models", response_model=ModelsResponse)
def list_models() -> ModelsResponse:
    """Mevcut LLM modellerini listele — şu an sadece Gemini."""
    from unisense.core.di import get_llm_provider
    llm = get_llm_provider()
    available = bool(getattr(llm, "is_available", lambda: True)())
    models = [{
        "id": "gemini",
        "name": "Gemini",
        "available": available,
        "description": "Google Gemini Flash Lite — bulut, hızlı, geniş bilgi",
    }]
    return ModelsResponse(models=[ModelInfo(**m) for m in models])


@router.post(
    "/ask",
    response_model=AskResponse,
    dependencies=[Depends(require_api_key), Depends(require_user)],
)
# Üç katman: (1) hesap/IP başına dakika (ani patlama), (2) hesap/IP başına gün
# (tek hesabın aşırı kullanımı), (3) site geneli gün (çok-hesap LLM kota tüketme
# saldırısına sert backstop — açık Firebase kaydıyla Gemini günlük kotasını
# bitirmeyi engeller). Limit aşılınca slowapi 429 döndürür.
@limiter.limit(ASK_LIMIT)
@limiter.limit(ASK_DAILY_LIMIT)
@limiter.limit(ASK_DAILY_GLOBAL_LIMIT, key_func=_global_key)
def ask(
    request: Request,
    body: AskRequest,
) -> AskResponse:
    """Üniversite/bölüm sorgu — RAG ile."""
    # Degraded mod (index boş — ör. HF kesintisinde boot): 500 yerine anlaşılır
    # mesaj. GUARD, servis kurulumundan ÖNCE: AskService inşası embedding
    # modelini ister ve model dosyası yokken HF'e gidip ASILIR — bu yüzden
    # Depends() yerine guard sonrası elle çözülür.
    try:
        index_hazir = bool(get_vector_store().count())
    except Exception:  # noqa: BLE001
        index_hazir = False
    if not index_hazir:
        raise HTTPException(
            status_code=503,
            detail="Bilgi bankası şu an yükleniyor (geçici kesinti) — birkaç dakika "
                   "sonra tekrar dene. Tercih robotları ve hesaplama araçları çalışıyor.",
        )
    svc: AskService = ask_service_dep()

    safe_query = sanitize_query(body.query)

    audit(
        "ask_query",
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        query=safe_query,
        extra={"uid": getattr(request.state, "uid", None)},
    )

    # History'i domain'e geçir (max son 8 mesaj — daha fazlası token şişirir).
    # History de LLM'e gittiği için sanitize edilir; şüpheli turlar düşürülür.
    from unisense.domain.models import ChatTurn as DomainTurn
    history = []
    for t in (body.history or []):
        safe_text = sanitize_history_text(t.text)
        if safe_text:
            history.append(DomainTurn(role=t.role, text=safe_text))
    history = history[-8:]

    domain_query = Query(
        text=safe_query,
        top_k=body.top_k,
        history=history,
        model_preference=body.model_preference,
    )
    answer = svc.execute(
        domain_query,
        user_context=body.user_context.model_dump(exclude_none=True) if body.user_context else None,
    )

    # Program chunk'larındaki dept/uni isimlerini ve sıra/taban bilgilerini lookup ile doldur
    # — frontend'in "+ Pusulaya Ekle" / "+ Tercihe Ekle" butonları için gerekli.
    # LLM cevabındaki 9 haneli kodlar da doğrulanır: veritabanında olmayan kodlar
    # (halüsinasyon ya da RAG kaynağına sızmış injection) cevaptan temizlenir.
    from unisense.core.di import get_recommendation_service
    rec_svc = get_recommendation_service()
    doc_codes = [d.department_code for d in answer.docs if d.department_code]
    text_codes = _OSYM_CODE_RE.findall(answer.text or "")
    program_codes = list(dict.fromkeys(doc_codes + text_codes))
    lookup_map: dict[str, dict] = {}
    lookup_ok = False
    if program_codes:
        try:
            lookups = rec_svc.lookup_programs(program_codes)
            lookup_map = {p["department_code"]: p for p in lookups if p.get("found")}
            lookup_ok = True
        except Exception as e:  # noqa: BLE001
            logger.warning("ask_lookup_failed", error=str(e)[:200])

    answer_text = answer.text
    if lookup_ok:
        invalid_codes = [c for c in set(text_codes) if c not in lookup_map]
        for c in invalid_codes:
            answer_text = re.sub(rf"\[{c}\]\s*|\b{c}\b", "", answer_text)
        if invalid_codes:
            logger.warning("ask_invalid_codes_stripped", codes=invalid_codes[:10])

    docs_resp = []
    for d in answer.docs:
        info = lookup_map.get(d.department_code, {}) if d.department_code else {}
        docs_resp.append(DocResponse(
            content=d.content,
            source=d.source,
            source_url=d.source_url,
            university_code=d.university_code,
            department_code=d.department_code,
            year=d.year,
            score_type=d.score_type,
            distance=d.distance,
            department_name=info.get("department_name", ""),
            department_group_name=info.get("department_group_name", "") or info.get("department_name", ""),
            university_name=info.get("university_name", ""),
            city=info.get("city", "") or d.city,
            last_year_base_rank=info.get("last_year_base_rank"),
            last_year_base_score=info.get("last_year_base_score"),
            quota=info.get("quota"),
        ))

    return AskResponse(
        query=answer.query,
        text=answer_text,
        docs=docs_resp,
        total_latency_ms=answer.total_latency_ms,
    )


@router.post(
    "/recommend",
    response_model=RecommendResponse,
    dependencies=[Depends(require_api_key), Depends(require_user)],
)
@limiter.limit(DEFAULT_LIMIT)
def recommend(
    request: Request,
    body: StudentProfileRequest,
    svc: RecommendationService = Depends(recommendation_service_dep),
) -> RecommendResponse:
    """Öğrenci profiline göre tercih önerme."""
    profile = StudentProfile(**body.model_dump())
    result = svc.recommend(profile)

    def _to_item(r):
        return {
            "department_code": r.department_code,
            "university_code": r.university_code,
            "department_name": r.department_name,
            "university_name": r.university_name,
            "city": r.city,
            "fit_score": r.fit_score,
            "safety_level": r.safety_level,
            "reason": r.reason,
            "placement_probability": r.placement_probability,
            "last_year_base_rank": r.last_year_base_rank,
            "last_year_base_score": r.last_year_base_score,
            "scholarship": r.scholarship,
            "education_language": r.education_language,
            "duration_years": r.duration_years,
            "osym_conditions": r.osym_conditions,
            "trend": r.trend,
        }

    return RecommendResponse(
        safe=[_to_item(r) for r in result.safe],
        target=[_to_item(r) for r in result.target],
        reach=[_to_item(r) for r in result.reach],
        notes=result.notes,
    )


# === İlgi Pusulası ===

@router.get("/compass/taxonomy", response_model=CompassTaxonomyResponse)
def compass_taxonomy(
    svc: CompassService = Depends(compass_service_dep),
) -> CompassTaxonomyResponse:
    """Tüm bölümlerin kategoriye göre gruplu listesi (Mod A için)."""
    data = svc.get_taxonomy()
    return CompassTaxonomyResponse(**data)


@router.post("/compass/by-selection", response_model=CompassResponse)
@limiter.limit(DEFAULT_LIMIT)
def compass_by_selection(
    request: Request,
    body: CompassSelectionRequest,
    svc: CompassService = Depends(compass_service_dep),
) -> CompassResponse:
    """Mod A: seçilen bölümlere yakın diğer bölüm önerileri."""
    matches = svc.by_selection(body.selected, top_k=body.top_k)
    return CompassResponse(
        matches=matches,
        mode="selection",
        notes=f"{len(body.selected)} seçimden {len(matches)} öneri",
    )


@router.post("/compass/by-text", response_model=CompassResponse)
@limiter.limit(ASK_LIMIT)
def compass_by_text(
    request: Request,
    body: CompassTextRequest,
    svc: CompassService = Depends(compass_service_dep),
) -> CompassResponse:
    """Mod B: serbest metinden bölüm önerisi."""
    # Her istek embedding hesabı tetikler — /ask ile aynı sıkı limit
    matches = svc.by_text(body.text, top_k=body.top_k)
    return CompassResponse(matches=matches, mode="text")


@router.post("/compass/by-axes", response_model=CompassResponse)
@limiter.limit(DEFAULT_LIMIT)
def compass_by_axes(
    request: Request,
    body: CompassAxesRequest,
    svc: CompassService = Depends(compass_service_dep),
) -> CompassResponse:
    """Mod C: 5 sorulu kişilik testi → bölüm eşleştirme."""
    axes = [body.math, body.human, body.creative, body.research, body.field]
    matches = svc.by_axes(axes, top_k=body.top_k)
    return CompassResponse(matches=matches, mode="axes")


@router.get("/compass/interests", response_model=CompassInterestsTaxonomyResponse)
def compass_interests(
    svc: CompassService = Depends(compass_service_dep),
) -> CompassInterestsTaxonomyResponse:
    """Kategori başına ilgi etiketleri (pill'ler) — bölüm adı içermez."""
    return CompassInterestsTaxonomyResponse(**svc.get_interests_taxonomy())


@router.post("/compass/by-interests", response_model=CompassResponse)
@limiter.limit(DEFAULT_LIMIT)
def compass_by_interests(
    request: Request,
    body: CompassInterestsRequest,
    svc: CompassService = Depends(compass_service_dep),
) -> CompassResponse:
    """Seçilen ilgi etiketlerinden bölüm önerisi (yeni Mod A — bölüm adı yok)."""
    matches = svc.by_interests(body.interests, top_k=body.top_k)
    return CompassResponse(
        matches=matches,
        mode="interests",
        notes=f"{len(body.interests)} ilgi → {len(matches)} bölüm",
    )


@router.post("/programs/lookup", response_model=ProgramLookupResponse)
@limiter.limit(DEFAULT_LIMIT)
def programs_lookup(
    request: Request,
    body: ProgramLookupRequest,
    svc: RecommendationService = Depends(recommendation_service_dep),
) -> ProgramLookupResponse:
    """Tercih listesindeki kodlar için sıra/taban/kontenjan bilgisini batch döner."""
    programs = svc.lookup_programs(body.codes)
    return ProgramLookupResponse(programs=programs)


@router.get("/hesap/siralama", response_model=SiralamaResponse)
@limiter.limit(DEFAULT_LIMIT)
def hesap_siralama(
    request: Request,
    puan: float = ApiQuery(..., ge=0, le=600),
    tur: str = ApiQuery("SAY", max_length=6),
) -> SiralamaResponse:
    """Yerleştirme puanından TAHMİNÎ başarı sırası (program tabanlarından interpolasyon).

    Hesap makinesi puanının yanında sıra göstermek için. Gerçek ÖSYM puan-sıralama
    tablosu değil — yaklaşık; uçlarda (çok yüksek/düşük puan) daha zayıf.
    """
    from unisense.application.services.recommendation_service import tahmini_sira

    r = tahmini_sira(puan, tur.upper())
    if r is None:
        raise HTTPException(status_code=404, detail="Bu puan türü için sıralama verisi yok")
    return SiralamaResponse(**r)


@router.post("/kpss/kadrolar", response_model=KpssKadroResponse)
@limiter.limit(DEFAULT_LIMIT)
def kpss_kadrolar(
    request: Request,
    body: KpssKadroRequest,
    svc=Depends(kpss_service_dep),
) -> KpssKadroResponse:
    """Aktif KPSS tercih dönemi kadroları — bölüm/puan/il filtresiyle.

    'Bilgisayar mühendisi hangi kadrolara başvurabilir?' → nitelik kodu
    eşleşmesi + geçmiş dönem taban puanı karşılaştırması.
    """
    result = svc.kadro_ara(
        bolum=body.bolum,
        puan=body.puan,
        duzey=body.duzey,
        il=body.il,
        iller=body.iller,
        limit=body.limit,
    )
    return KpssKadroResponse(**result)


@router.post("/dgs/gecis", response_model=DgsGecisResponse)
@limiter.limit(DEFAULT_LIMIT)
def dgs_gecis(
    request: Request,
    body: DgsGecisRequest,
    svc=Depends(dgs_service_dep),
) -> DgsGecisResponse:
    """Önlisans bölümü → geçilebilecek lisans bölümleri (ÖSYM DGS Tablo-2)."""
    return DgsGecisResponse(**svc.gecis_ara(body.onlisans))


@router.post("/dgs/programlar", response_model=DgsProgramResponse)
@limiter.limit(DEFAULT_LIMIT)
def dgs_programlar(
    request: Request,
    body: DgsProgramRequest,
    svc=Depends(dgs_service_dep),
) -> DgsProgramResponse:
    """DGS puanıyla geçilebilecek lisans programları (ÖSYM yıllık min/max)."""
    result = svc.program_ara(
        puan_turu=body.puan_turu,
        puan=body.puan,
        bolum=body.bolum,
        il=body.il,
        uni_turu=body.uni_turu,
        oneri=body.oneri,
        limit=body.limit,
    )
    return DgsProgramResponse(**result)


# === Bölüm Rehberi (gezilebilir /bolum) ===

@router.get("/bolumler", response_model=GuideListResponse)
@limiter.limit(DEFAULT_LIMIT)
def bolum_katalog(
    request: Request,
    svc=Depends(guide_service_dep),
) -> GuideListResponse:
    """Bölüm rehberi kataloğu — tanıtımı olan tüm bölümler (SEO + gezinme)."""
    items = svc.list_guides()
    return GuideListResponse(total=len(items), items=items)


@router.get("/bolum/{slug}", response_model=GuideDetailResponse)
@limiter.limit(DEFAULT_LIMIT)
def bolum_detay(
    request: Request,
    slug: str,
    svc=Depends(guide_service_dep),
) -> GuideDetailResponse:
    """Tek bölüm: tanıtım içeriği + o bölümü veren tüm üniversitelerin canlı tabanı."""
    detail = svc.get_guide(slug)
    if detail is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Bölüm rehberi bulunamadı")
    return GuideDetailResponse(**detail)


@router.get("/takvim", response_model=ExamCalendarResponse)
@limiter.limit(DEFAULT_LIMIT)
def sinav_takvimi(
    request: Request,
    svc=Depends(news_service_dep),
) -> ExamCalendarResponse:
    """Yaklaşan sınav etkinlikleri (kalan gün hesaplı) — haber akışı/takvim."""
    return ExamCalendarResponse(**svc.takvim())


@router.get("/lgs/iller", response_model=LgsIllerResponse)
@limiter.limit(DEFAULT_LIMIT)
def lgs_iller(
    request: Request,
    svc=Depends(lgs_service_dep),
) -> LgsIllerResponse:
    """LGS lise verisinde bulunan iller (öneri filtresi dropdown'ı için)."""
    return LgsIllerResponse(iller=svc.iller())


@router.get("/lgs/ilceler", response_model=LgsIlcelerResponse)
@limiter.limit(DEFAULT_LIMIT)
def lgs_ilceler(
    request: Request,
    il: str,
    svc=Depends(lgs_service_dep),
) -> LgsIlcelerResponse:
    """Seçilen ildeki ilçeler (öneri filtresi dropdown'ı için)."""
    return LgsIlcelerResponse(ilceler=svc.ilceler(il))


@router.post("/lgs/oneri", response_model=LgsOneriResponse)
@limiter.limit(DEFAULT_LIMIT)
def lgs_oneri(
    request: Request,
    payload: LgsOneriRequest,
    svc=Depends(lgs_service_dep),
) -> LgsOneriResponse:
    """Yüzdelik dilim (+ il/ilçe/tür) → güvenli/tutar/riskli lise önerileri (tersine).

    TAHMİNÎDİR: geçen yılın taban yüzdeliklerine dayanır (veri yılı yanıttaki
    `yil` alanındadır).
    """
    result = svc.oneri(
        yuzdelik=payload.yuzdelik,
        il=payload.il,
        iller=payload.iller,
        ilce=payload.ilce,
        turler=payload.turler,
        pansiyon=payload.pansiyon,
    )
    return LgsOneriResponse(**result)


def _norm_sinav(s: str | None) -> str:
    return "DUS" if (s or "").strip().upper() == "DUS" else "TUS"


@router.get("/tus/meta", response_model=TusMetaResponse)
@limiter.limit(DEFAULT_LIMIT)
def tus_meta(
    request: Request,
    sinav: str = "TUS",
    svc=Depends(tus_service_dep),
) -> TusMetaResponse:
    """TUS/DUS meta: dönem + dal listesi (öneri filtresi dropdown'ı için)."""
    return TusMetaResponse(**svc.meta(_norm_sinav(sinav)))


@router.post("/tus/oneri", response_model=TusOneriResponse)
@limiter.limit(DEFAULT_LIMIT)
def tus_oneri(
    request: Request,
    payload: TusOneriRequest,
    svc=Depends(tus_service_dep),
) -> TusOneriResponse:
    """K/T puanı (+ dal/kurum/tür) → yerleşebileceğin uzmanlık programları.

    TAHMÎNİDİR: geçen dönem ÖSYM en küçük yerleşme puanlarına dayanır.
    """
    result = svc.oneri(
        puan=payload.puan,
        sinav=_norm_sinav(payload.sinav),
        dal=payload.dal,
        kontenjan_turu=payload.kontenjan_turu,
        kurum=payload.kurum,
    )
    return TusOneriResponse(**result)


@router.post("/programs/compare", response_model=CompareResponse)
@limiter.limit(DEFAULT_LIMIT)
def programs_compare(
    request: Request,
    body: CompareRequest,
    svc: CompareService = Depends(compare_service_dep),
) -> CompareResponse:
    """2-5 ÖSYM kodunu yan yana karşılaştır (trend, taban, sıra, kontenjan, kadro)."""
    result = svc.compare(body.codes)
    return CompareResponse(**result)
