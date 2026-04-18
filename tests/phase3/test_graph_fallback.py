import pytest
from pydantic import ValidationError


def test_fallback_phrase_matches_locked_decision():
    from src.ai.langgraph.state import BotAnswer, SourceRef

    answer = BotAnswer(
        answer="Я не знаю — обратитесь к коллеге",
        confidence=0.12,
        fallback_used=True,
        sources=[
            SourceRef(
                source_id="seed:knowledge",
                excerpt="Ближайший найденный фрагмент по запросу",
                timestamp="2026-04-19T10:00:00",
            )
        ],
    )
    assert answer.answer == "Я не знаю — обратитесь к коллеге"
    assert answer.fallback_used is True


def test_fallback_answer_requires_source_for_traceability():
    from src.ai.langgraph.state import BotAnswer

    with pytest.raises(ValidationError):
        BotAnswer(
            answer="Я не знаю — обратитесь к коллеге",
            confidence=0.12,
            fallback_used=True,
            sources=[],
        )


def test_decision_routes_low_confidence_to_locked_fallback():
    from src.ai.langgraph.nodes.decide import decide_next_action

    route = decide_next_action(
        {
            "role": "employee",
            "query": "Как заполнить форму?",
            "rag_payload": {"confidence": 0.12, "fallback_used": False, "sources": []},
            "clarify_turns_used": 0,
        }
    )
    assert route == "fallback"


def test_ambiguous_query_triggers_single_clarification_then_final_answer():
    from src.ai.langgraph.nodes.decide import decide_next_action

    first = decide_next_action(
        {
            "role": "employee",
            "query": "Что делать с отчетом?",
            "rag_payload": {"confidence": 0.82, "fallback_used": False, "sources": []},
            "clarify_turns_used": 0,
        }
    )
    second = decide_next_action(
        {
            "role": "employee",
            "query": "Что делать с отчетом?",
            "rag_payload": {"confidence": 0.82, "fallback_used": False, "sources": []},
            "clarify_turns_used": 1,
        }
    )
    assert first == "clarify"
    assert second == "answer"


def test_offtopic_query_gets_refusal_branch():
    from src.ai.langgraph.nodes.decide import decide_next_action

    route = decide_next_action(
        {
            "role": "employee",
            "query": "Расскажи анекдот",
            "rag_payload": {"confidence": 0.9, "fallback_used": False, "sources": []},
            "clarify_turns_used": 0,
        }
    )
    assert route == "offtopic"


def test_conflict_route_selected_when_sources_conflict():
    from src.ai.langgraph.nodes.decide import decide_next_action

    route = decide_next_action(
        {
            "role": "employee",
            "query": "Какой регламент применять?",
            "rag_payload": {
                "confidence": 0.9,
                "fallback_used": False,
                "sources": [
                    {"source_id": "doc:new", "excerpt": "Делайте через портал X", "timestamp": "2026-04-20T10:00:00"},
                    {"source_id": "doc:old", "excerpt": "Делайте через почту", "timestamp": "2026-01-01T10:00:00"},
                ],
            },
            "clarify_turns_used": 0,
        }
    )
    assert route == "conflict"


@pytest.mark.asyncio
async def test_graph_denied_role_short_circuits_before_retrieve(monkeypatch):
    from src.ai.langgraph.graph import build_graph

    calls = {"retrieve": 0}

    async def _fake_retrieve(*args, **kwargs):
        calls["retrieve"] += 1
        return {"rag_payload": {"answer": "x", "confidence": 0.9, "sources": [], "fallback_used": False}}

    monkeypatch.setattr("src.ai.langgraph.graph.retrieve_phase2_payload", _fake_retrieve)
    graph = build_graph()
    result = await graph.ainvoke(
        {"role": "guest", "query": "Как оформить доступ?", "user_id": "7", "chat_id": "11"},
        config={"configurable": {"thread_id": "tg:11:7"}},
    )
    assert calls["retrieve"] == 0
    assert result["decision"] == "deny"
    assert result["result"].fallback_used is True


@pytest.mark.asyncio
async def test_graph_low_confidence_skips_answer_synthesis(monkeypatch):
    from src.ai.langgraph.graph import build_graph

    calls = {"answer": 0}

    async def _fake_retrieve(*args, **kwargs):
        return {
            "rag_payload": {
                "answer": "seed",
                "confidence": 0.1,
                "sources": [{"source_id": "seed:knowledge", "excerpt": "x", "timestamp": "2026-04-01T00:00:00"}],
                "fallback_used": False,
            }
        }

    def _fake_answer(*args, **kwargs):
        calls["answer"] += 1
        raise AssertionError("answer synthesis must not be called for low-confidence fallback")

    monkeypatch.setattr("src.ai.langgraph.graph.retrieve_phase2_payload", _fake_retrieve)
    monkeypatch.setattr("src.ai.langgraph.graph.compose_grounded_answer", _fake_answer)

    graph = build_graph()
    result = await graph.ainvoke(
        {"role": "employee", "query": "Как оформить доступ?", "user_id": "7", "chat_id": "11"},
        config={"configurable": {"thread_id": "tg:11:7"}},
    )
    assert calls["answer"] == 0
    assert result["decision"] == "fallback"
    assert result["result"].answer.startswith("Я не знаю — обратитесь к коллеге")


@pytest.mark.asyncio
async def test_graph_masks_internal_errors_with_safe_envelope(monkeypatch):
    from src.ai.langgraph.graph import build_graph

    async def _boom(*args, **kwargs):
        raise RuntimeError("secret stack details")

    monkeypatch.setattr("src.ai.langgraph.graph.retrieve_phase2_payload", _boom)

    graph = build_graph()
    result = await graph.ainvoke(
        {"role": "employee", "query": "Как оформить доступ?", "user_id": "7", "chat_id": "11"},
        config={"configurable": {"thread_id": "tg:11:7"}},
    )
    assert result["decision"] == "error"
    assert "secret" not in result["result"].answer.lower()
    assert "traceback" not in result["result"].answer.lower()
    assert "Источники" in result["result"].answer
