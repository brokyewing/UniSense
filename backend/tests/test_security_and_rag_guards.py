"""Güvenlik, RAG PII/boş-bağlam koruması ve servis/şema regresyon testleri."""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from types import SimpleNamespace

import pytest
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from unisense.api.v1.routes import _norm_sinav
from unisense.api.v1.schemas import TusOneriRequest, UserExamContext
from unisense.application.services import ask_service as ask_mod
from unisense.application.services import employment_service as emp_mod
from unisense.application.services import recommendation_service as rec_mod
from unisense.application.services import scholarship_service as sch_mod
from unisense.core.config import get_settings
from unisense.domain.enums import ScoreType
from unisense.domain.models import Query, StudentProfile


@pytest.fixture(autouse=True)
def _reset_caches():
    get_settings.cache_clear()
    ask_mod._response_cache.clear()
    yield
    get_settings.cache_clear()
    ask_mod._response_cache.clear()


def test_lifespan_fails_closed_in_production_without_auth(monkeypatch):
    from unisense import main as main_mod

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECURITY_REQUIRE_AUTH", "false")
    monkeypatch.delenv("UNISENSE_ALLOW_INSECURE_PROD", raising=False)
    get_settings.cache_clear()

    async def _enter():
        async with asynccontextmanager(main_mod.lifespan)(FastAPI()):
            pass

    with pytest.raises(RuntimeError, match="SECURITY_REQUIRE_AUTH=true"):
        asyncio.run(_enter())


def test_lifespan_allows_explicit_insecure_prod_override(monkeypatch):
    from unisense import main as main_mod

    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SECURITY_REQUIRE_AUTH", "false")
    monkeypatch.setenv("UNISENSE_ALLOW_INSECURE_PROD", "1")
    monkeypatch.setattr(
        main_mod,
        "get_vector_store",
        lambda: SimpleNamespace(count=lambda: 1, warmup=lambda: None),
    )
    get_settings.cache_clear()

    async def _enter():
        async with asynccontextmanager(main_mod.lifespan)(FastAPI()):
            return True

    assert asyncio.run(_enter()) is True


def test_scrub_pii_masks_email_tckn_and_phone():
    raw = "Adım Ali, TCKN 12345678901, tel +90 532 123 45 67 veya 05551112233, mail ali@example.com."
    cleaned = ask_mod._scrub_pii(raw)
    assert "12345678901" not in cleaned
    assert "532" not in cleaned
    assert "05551112233" not in cleaned
    assert "ali@example.com" not in cleaned


def test_ask_service_empty_context_skips_llm():
    class FakeRetrieval:
        def retrieve(self, query):
            return []

        def build_context(self, docs, max_chars=4000):
            return ""

    class FakeLLM:
        def __init__(self):
            self.calls = 0

        def generate(self, query, context=None, history=None):
            self.calls += 1
            return "Uydurma cevap"

    class FakeRec:
        pass

    llm = FakeLLM()
    svc = ask_mod.AskService(retrieval=FakeRetrieval(), llm=llm, recommendation=FakeRec())
    ans = svc.execute(Query(text="Tamamen bilinmeyen uydurma bölüm hakkında bilgi ver"))
    assert llm.calls == 0
    assert ans.text == ask_mod._EMPTY_CONTEXT_ANSWER


def test_recommendation_service_rejects_non_positive_rank(monkeypatch):
    fake_store = SimpleNamespace(search=lambda *a, **kw: [])
    svc = rec_mod.RecommendationService(store=fake_store)
    monkeypatch.setattr(
        rec_mod,
        "_load_data",
        lambda: (
            [{"department_code": "1", "score_type": "SAY", "base_rank": 1000, "base_score": 500.0}],
            [{"code": "1", "university_code": "10", "department_name": "Bilgisayar", "university_name": "Test"}],
            {},
        ),
    )
    res = svc.recommend(StudentProfile(score_type=ScoreType.SAY, rank=0))
    assert res.safe == [] and res.target == [] and res.reach == []
    assert "≥ 1" in res.notes


def test_employment_and_scholarship_tr_lower_and_list_copy(monkeypatch):
    monkeypatch.setattr(
        emp_mod,
        "_load_data",
        lambda: {
            "year": 2026,
            "items": [{"year": 2026, "department_name": "BİLGİSAYAR MÜHENDİSLİĞİ", "program_code": "101"}],
        },
    )
    emp = emp_mod.EmploymentService()
    filtered = emp.list(department="bilgisayar")
    assert filtered["total"] == 1
    unfiltered = emp.list()
    unfiltered["items"].append({"fake": True})
    assert emp.list()["total"] == 1

    monkeypatch.setattr(
        sch_mod,
        "_load_data",
        lambda: {
            "year": 2026,
            "items": [
                {
                    "year": 2026,
                    "university_name": "İSTANBUL TEST ÜNİ",
                    "department_name": "IŞIK FİZİĞİ",
                    "university_type": "VAKIF",
                    "program_code": "202",
                }
            ],
        },
    )
    sch = sch_mod.ScholarshipService()
    assert sch.list(university="istanbul")["total"] == 1
    assert sch.list(department="ışık")["total"] == 1
    assert sch.list(type_filter="vakıf")["total"] == 1
    sch_all = sch.list()
    sch_all["items"].clear()
    assert sch.list()["total"] == 1


def test_schema_and_route_input_guards():
    ok = UserExamContext(tercih_sehirler=[" İstanbul ", "Ankara"])
    assert ok.tercih_sehirler == ["İstanbul", "Ankara"]

    with pytest.raises(ValidationError):
        UserExamContext(tercih_sehirler=["x" * 51])

    with pytest.raises(ValidationError):
        UserExamContext(tercih_sehirler=["   "])

    assert TusOneriRequest(puan=65.0, sinav="dus").sinav == "DUS"
    with pytest.raises(ValidationError):
        TusOneriRequest(puan=65.0, sinav="YKS")

    assert _norm_sinav("tus") == "TUS"
    assert _norm_sinav("DUS") == "DUS"
    with pytest.raises(HTTPException) as exc_info:
        _norm_sinav("LGS")
    assert exc_info.value.status_code == 400
