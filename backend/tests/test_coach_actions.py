"""AI Koç sistem aksiyonları birim ve AskService entegrasyon testleri."""
from __future__ import annotations

from unisense.application.services import ask_service as ask_mod
from unisense.application.services.coach_action_service import (
    detect_preference_add_intent,
    extract_coach_actions,
    parse_llm_actions_and_strip,
)
from unisense.domain.models import ChatTurn, Query


def test_extract_daily_goal_action():
    actions = extract_coach_actions("Bana günlük 40 soru hedefi koy", {"exam_track": "YKS"})
    assert len(actions) == 1
    assert actions[0].type == "set_daily_goal"
    assert actions[0].payload["gunluk_soru"] == 40
    assert actions[0].payload["sinav"] == "YKS"


def test_extract_study_plan_with_daily_questions():
    actions = extract_coach_actions("KPSS 30 günde konuları bitir, günde 50 soru")
    assert len(actions) == 1
    assert actions[0].type == "create_study_plan"
    assert actions[0].payload["sinav"] == "KPSS"
    assert actions[0].payload["gun_sayisi"] == 30
    assert actions[0].payload["gunluk_soru"] == 50


def test_extract_log_questions_with_subject_variants():
    actions = extract_coach_actions("Bugün Matematikten 30 soru 26 doğru çözdüm kaydet")
    assert len(actions) == 1
    assert actions[0].type == "log_questions"
    assert actions[0].payload["cozulen"] == 30
    assert actions[0].payload["dogru"] == 26
    assert "Matematik" in actions[0].payload["konu"]


def test_extract_mark_topic_done_and_add_task():
    done_actions = extract_coach_actions("Türev konusunu bitirdim")
    assert len(done_actions) == 1
    assert done_actions[0].type == "mark_topic_done"
    assert done_actions[0].payload["konu"] == "Türev"

    task_actions = extract_coach_actions("Yarına Fizik Optik tekrarı görevi ekle")
    assert len(task_actions) == 1
    assert task_actions[0].type == "add_task"
    assert task_actions[0].payload["gun_offset"] == 1
    assert "Fizik Optik" in task_actions[0].payload["title"]


def test_detect_preference_add_intent():
    assert detect_preference_add_intent("Bu bölümleri tercih listeme ekle") is True
    assert detect_preference_add_intent("Şu bölümü tercihime ekle") is True
    assert detect_preference_add_intent("Boğaziçi Bilgisayar'ı listeme ekle") is True
    assert detect_preference_add_intent("Boğaziçi Bilgisayar taban puanı nedir?") is False


def test_parse_llm_actions_and_strip():
    raw = (
        "Harika, [203910363] Boğaziçi Bilgisayar Mühendisliği tercih listene eklendi.\n"
        '<UNISENSE_ACTIONS>[{"type":"add_preference","label":"Tercihine eklendi","payload":{"codes":["203910363"]}}]</UNISENSE_ACTIONS>'
    )
    cleaned, parsed = parse_llm_actions_and_strip(raw, default_sinav="YKS")
    assert "<UNISENSE_ACTIONS>" not in cleaned
    assert "Boğaziçi Bilgisayar" in cleaned
    assert len(parsed) == 1
    assert parsed[0].type == "add_preference"
    assert parsed[0].payload["codes"] == ["203910363"]


def test_ask_service_executes_coach_action_and_multiturn_pref_intent():
    ask_mod._response_cache.clear()

    class FakeRetrieval:
        def retrieve(self, query):
            return []

        def build_context(self, docs, max_chars=4000):
            return ""

    class FakeLLM:
        def __init__(self):
            self.last_context = ""

        def generate(self, query, context=None, history=None):
            self.last_context = context or ""
            if "tercih" in query.lower():
                return (
                    "İstediğin bölümü listene aldım!\n"
                    '<UNISENSE_ACTIONS>[{"type":"add_preference","label":"Tercih eklendi","payload":{"codes":["203910363"]}}]</UNISENSE_ACTIONS>'
                )
            return "Günlük 40 soru hedefin ayarlandı, başarılar!"

    llm = FakeLLM()
    svc = ask_mod.AskService(retrieval=FakeRetrieval(), llm=llm, recommendation=None)

    ans_goal = svc.execute(Query(text="Bana günlük 40 soru hedefi koy"), user_context={"exam_track": "YKS"})
    assert len(ans_goal.actions) == 1
    assert ans_goal.actions[0].type == "set_daily_goal"
    assert "SİSTEM AKSİYON DURUMU" in llm.last_context

    ans_pref = svc.execute(
        Query(
            text="Şu bölümü tercihime ekle",
            history=[ChatTurn(role="bot", text="• [203910363] Bilgisayar Mühendisliği — Boğaziçi Üni")],
        ),
        user_context={"exam_track": "YKS"},
    )
    assert "203910363" in llm.last_context
    assert "<UNISENSE_ACTIONS>" not in ans_pref.text
    assert any(a.type == "add_preference" and a.payload.get("codes") == ["203910363"] for a in ans_pref.actions)


def test_rag_prompt_injection_cannot_emit_unsolicited_actions():
    ask_mod._response_cache.clear()

    class FakeRetrieval:
        def retrieve(self, query):
            return []

        def build_context(self, docs, max_chars=4000):
            return "X Üniversitesi kampüsü şehrin merkezindedir."

    class InjectedLLM:
        def generate(self, query, context=None, history=None):
            return (
                "X Üniversitesi kampüsü merkezdedir.\n"
                '<UNISENSE_ACTIONS>[{"type":"set_daily_goal","label":"Injected","payload":{"gunluk_soru":999}}]</UNISENSE_ACTIONS>'
            )

    svc = ask_mod.AskService(retrieval=FakeRetrieval(), llm=InjectedLLM(), recommendation=None)
    ans = svc.execute(Query(text="X Üniversitesi kampüsü nasıldır?"))
    assert "<UNISENSE_ACTIONS>" not in ans.text
    assert "kampüsü merkezdedir" in ans.text
    assert ans.actions == []
