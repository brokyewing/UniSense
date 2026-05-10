"""API v1 — routes."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from unisense.api.v1.dependencies import (
    ask_service_dep,
    compass_service_dep,
    recommendation_service_dep,
)
from unisense.api.v1.schemas import (
    AskRequest,
    AskResponse,
    CompassAxesRequest,
    CompassInterestsRequest,
    CompassInterestsTaxonomyResponse,
    CompassResponse,
    CompassSelectionRequest,
    CompassTaxonomyResponse,
    CompassTextRequest,
    DocResponse,
    HealthResponse,
    ModelInfo,
    ModelsResponse,
    ProgramLookupRequest,
    ProgramLookupResponse,
    RecommendResponse,
    StudentProfileRequest,
)
from unisense.application.services import AskService, CompassService, RecommendationService
from unisense.core.di import get_vector_store
from unisense.core.logging import get_logger
from unisense.domain.models import Query, StudentProfile
from unisense.security.audit_log import audit
from unisense.security.auth import require_api_key
from unisense.security.input_sanitizer import sanitize_query

router = APIRouter(prefix="/api/v1", tags=["v1"])
logger = get_logger(__name__)


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    try:
        count = get_vector_store().count()
    except Exception:  # noqa: BLE001
        count = None
    return HealthResponse(status="ok", version="0.1.0", chunks_count=count)


@router.get("/models", response_model=ModelsResponse)
def list_models() -> ModelsResponse:
    """Mevcut LLM modellerini listele (Gemini + UniSenseLocal)."""
    from unisense.core.di import get_llm_provider
    llm = get_llm_provider()
    if hasattr(llm, "get_available_models"):
        models = llm.get_available_models()
    else:
        models = [{"id": "gemini", "name": "Gemini", "available": True, "description": ""}]
    return ModelsResponse(models=[ModelInfo(**m) for m in models])


@router.post(
    "/ask",
    response_model=AskResponse,
    dependencies=[Depends(require_api_key)],
)
def ask(
    request: Request,
    body: AskRequest,
    svc: AskService = Depends(ask_service_dep),
) -> AskResponse:
    """Üniversite/bölüm sorgu — RAG ile."""
    safe_query = sanitize_query(body.query)

    audit(
        "ask_query",
        ip=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
        query=safe_query,
    )

    # History'i domain'e geçir (max son 8 mesaj — daha fazlası token şişirir)
    from unisense.domain.models import ChatTurn as DomainTurn
    history = [DomainTurn(role=t.role, text=t.text) for t in (body.history or [])][-8:]

    domain_query = Query(
        text=safe_query,
        top_k=body.top_k,
        history=history,
        model_preference=body.model_preference,
    )
    answer = svc.execute(domain_query)

    # Program chunk'larındaki dept/uni isimlerini ve sıra/taban bilgilerini lookup ile doldur
    # — frontend'in "+ Pusulaya Ekle" / "+ Tercihe Ekle" butonları için gerekli
    from unisense.core.di import get_recommendation_service
    rec_svc = get_recommendation_service()
    program_codes = [d.department_code for d in answer.docs if d.department_code]
    lookup_map: dict[str, dict] = {}
    if program_codes:
        try:
            lookups = rec_svc.lookup_programs(program_codes)
            lookup_map = {p["department_code"]: p for p in lookups if p.get("found")}
        except Exception as e:  # noqa: BLE001
            logger.warning("ask_lookup_failed", error=str(e)[:200])

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
        text=answer.text,
        docs=docs_resp,
        total_latency_ms=answer.total_latency_ms,
    )


@router.post(
    "/recommend",
    response_model=RecommendResponse,
    dependencies=[Depends(require_api_key)],
)
def recommend(
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
            "last_year_base_rank": r.last_year_base_rank,
            "last_year_base_score": r.last_year_base_score,
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
def compass_by_selection(
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
def compass_by_text(
    body: CompassTextRequest,
    svc: CompassService = Depends(compass_service_dep),
) -> CompassResponse:
    """Mod B: serbest metinden bölüm önerisi."""
    matches = svc.by_text(body.text, top_k=body.top_k)
    return CompassResponse(matches=matches, mode="text")


@router.post("/compass/by-axes", response_model=CompassResponse)
def compass_by_axes(
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
def compass_by_interests(
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
def programs_lookup(
    body: ProgramLookupRequest,
    svc: RecommendationService = Depends(recommendation_service_dep),
) -> ProgramLookupResponse:
    """Tercih listesindeki kodlar için sıra/taban/kontenjan bilgisini batch döner."""
    programs = svc.lookup_programs(body.codes)
    return ProgramLookupResponse(programs=programs)
