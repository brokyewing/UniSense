"""Paket A/B/C testleri: öğrenci hafızası, LGS/TUS/Takvim/Kariyer/Özet router'ları ve tercih çözümleme."""
from __future__ import annotations

from unisense.api.v1.schemas import PreferenceResolveRequest, UserExamContext
from unisense.application.services import ask_service as ask_mod
from unisense.application.services.intent_router import (
    build_guide_ozet_context,
    build_kariyer_context,
    build_lgs_context,
    build_profile_context,
    build_takvim_context,
    build_tus_dus_context,
)
from unisense.domain.models import Query


def test_user_exam_context_and_profile_memory_block():
    uc = UserExamContext(
        exam_track="YKS",
        yks_sira=24000,
        ilgi_alanlari=["Yazılım", "Yapay Zeka"],
        son_denemeler=["TYT-3: 82.5 net (410 p) · 2026-11-26"],
        bekleyen_gorevler=["Türev Tekrar (2026-11-27)"],
        son_notlar=["[Matematik] İntegral formüllerini tekrar et"],
        tercih_ozeti=["[203910363] Bilgisayar Mühendisliği — Boğaziçi Üni"],
        calisma_eksik_konular=["Fizik: Optik"],
        toplam_calisma_dk=420,
        seri_gun=6,
    )
    txt = build_profile_context(uc.model_dump(exclude_none=True))
    assert "İlgi Pusulası" in txt and "Yapay Zeka" in txt
    assert "Son deneme sonuçları" in txt and "82.5 net" in txt
    assert "Bekleyen plan görevleri" in txt
    assert "Aktif çalışma notları" in txt
    assert "Mevcut tercih listesi" in txt
    assert "420 dk toplam çalışma" in txt
    assert "6 gün kesintisiz seri" in txt


def test_lgs_tus_takvim_kariyer_guide_routers():
    lgs_ctx = build_lgs_context("Ankara'da %3 yüzdelikle hangi fen veya anadolu liseleri gelir?")
    assert "LGS LİSE TERCİH VERİSİ" in lgs_ctx

    tus_ctx = build_tus_dus_context("TUS 65 puanla hangi uzmanlıklar gelir?")
    assert "TUS UZMANLIK VERİSİ" in tus_ctx

    takvim_ctx = build_takvim_context("2026 KPSS ve YKS sınav tarihleri ne zaman?")
    assert "RESMİ SINAV TAKVİMİ" in takvim_ctx

    kariyer_ctx = build_kariyer_context("Bilgisayar mühendisi için güncel kamu ve iş ilanları neler?")
    assert "GÜNCEL KARİYER" in kariyer_ctx

    ozet_ctx = build_guide_ozet_context("Türev ve limit formül özeti neler?")
    assert isinstance(ozet_ctx, str)


def test_ask_service_routes_personal_coaching_and_takvim_without_rag():
    ask_mod._response_cache.clear()

    class CountingRetrieval:
        def __init__(self):
            self.calls = 0

        def retrieve(self, query):
            self.calls += 1
            return []

        def build_context(self, docs, max_chars=4000):
            return ""

    class CapturingLLM:
        def __init__(self):
            self.last_context = ""
            self.last_mode = ""

        def generate(self, query, context=None, history=None, mode="rag"):
            self.last_context = context or ""
            self.last_mode = mode
            return "• Son deneme trendin yükselişte!"

    ret = CountingRetrieval()
    llm = CapturingLLM()
    svc = ask_mod.AskService(retrieval=ret, llm=llm, recommendation=None)

    ans_coach = svc.execute(
        Query(text="Son denemelerim nasıl gidiyor?"),
        user_context={"exam_track": "KPSS", "son_denemeler": ["Pozitif Bilgi: 86.25 net"]},
    )
    assert ret.calls == 0
    assert llm.last_mode == "coach"
    assert "Pozitif Bilgi: 86.25 net" in llm.last_context
    assert "yükselişte" in ans_coach.text

    ask_mod._response_cache.clear()
    svc.execute(Query(text="YKS başvuruları ve sınavı ne zaman?"))
    assert "RESMİ SINAV TAKVİMİ" in llm.last_context


def test_preference_resolve_endpoint_handles_all_exams():
    from starlette.requests import Request

    from unisense.api.v1.routes import preferences_resolve
    from unisense.core.di import get_recommendation_service

    scope = {"type": "http", "method": "POST", "path": "/api/v1/preferences/resolve", "headers": []}
    req = Request(scope)
    rec = get_recommendation_service()

    res_lgs = preferences_resolve(req, PreferenceResolveRequest(sinav="LGS", query="lisesi"), rec_svc=rec)
    assert res_lgs.sinav == "LGS"
    assert isinstance(res_lgs.items, list)
