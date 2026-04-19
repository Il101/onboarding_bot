import pytest
import httpx


@pytest.mark.asyncio
async def test_retrieve_calls_knowledge_query_with_bounded_top_k():
    import httpx

    from src.ai.langgraph.nodes.retrieve_phase2 import retrieve_phase2_payload
    from src.core.config import settings

    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["json"] = request.content.decode("utf-8")
        return httpx.Response(
            200,
            json={
                "answer": "seed answer",
                "confidence": 0.4,
                "sources": [
                    {
                        "source_id": "seed:knowledge",
                        "excerpt": "Ближайший найденный фрагмент по запросу",
                        "timestamp": "2026-04-01T00:00:00",
                    }
                ],
                "fallback_used": False,
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(base_url="http://test", transport=transport) as client:
        result = await retrieve_phase2_payload(
            {"query": "как оформить заявку"},
            top_k=settings.rag_hybrid_top_k + 100,
            client=client,
        )

    assert captured["path"] == "/api/knowledge/query"
    assert f'"top_k":{settings.rag_hybrid_top_k}' in captured["json"].replace(" ", "")
    assert set(result["rag_payload"].keys()) == {"answer", "confidence", "sources", "fallback_used"}


def test_summarize_trims_old_turns_and_updates_summary():
    from src.ai.langgraph.nodes.summarize import summarize_history_if_needed

    state = {
        "summary": "",
        "messages": [
            {"role": "user", "content": "Нужно настроить доступ к CRM"},
            {"role": "assistant", "content": "Откройте портал доступов"},
            {"role": "user", "content": "Где искать форму?"},
            {"role": "assistant", "content": "В разделе ИТ сервисы"},
            {"role": "user", "content": "А срок рассмотрения?"},
        ],
    }
    updated = summarize_history_if_needed(state, max_messages=3, max_tokens=20)
    assert updated["summary"]
    assert len(updated["messages"]) <= 3
    assert updated["messages"][-1]["content"] == "А срок рассмотрения?"


def test_thread_id_isolation_same_pair_shared_other_pair_isolated():
    from src.ai.langgraph.state import build_thread_id

    a1 = build_thread_id(chat_id=100, user_id=200)
    a2 = build_thread_id(chat_id=100, user_id=200)
    b = build_thread_id(chat_id=100, user_id=201)

    assert a1 == a2
    assert a1 != b


def test_summarize_never_removes_latest_user_message():
    from src.ai.langgraph.nodes.summarize import summarize_history_if_needed

    state = {
        "summary": "Ранее обсуждали доступы.",
        "messages": [
            {"role": "user", "content": "Старый вопрос 1"},
            {"role": "assistant", "content": "Старый ответ 1"},
            {"role": "user", "content": "Старый вопрос 2"},
            {"role": "assistant", "content": "Старый ответ 2"},
            {"role": "user", "content": "А что с доступом сегодня?"},
        ],
    }
    updated = summarize_history_if_needed(state, max_messages=2, max_tokens=10)
    assert any(
        msg["role"] == "user" and msg["content"] == "А что с доступом сегодня?"
        for msg in updated["messages"]
    )


@pytest.mark.asyncio
async def test_graph_allows_single_clarify_then_forces_final_branch(monkeypatch):
    from src.ai.langgraph.graph import build_graph

    async def _fake_retrieve(*args, **kwargs):
        return {
            "rag_payload": {
                "answer": "Оформление доступа CRM",
                "confidence": 0.9,
                "fallback_used": False,
                "sources": [{"source_id": "doc:crm", "excerpt": "Инструкция CRM", "timestamp": "2026-04-10T10:00:00"}],
            }
        }

    monkeypatch.setattr("src.ai.langgraph.graph.retrieve_phase2_payload", _fake_retrieve)
    graph = build_graph()
    config = {"configurable": {"thread_id": "tg:111:222"}}

    first = await graph.ainvoke(
        {"role": "employee", "query": "Что делать с отчетом?", "user_id": "222", "chat_id": "111"},
        config=config,
    )
    second = await graph.ainvoke(
        {"role": "employee", "query": "Что делать с отчетом?", "user_id": "222", "chat_id": "111"},
        config=config,
    )

    assert first["decision"] == "clarify"
    assert second["decision"] in {"answer", "conflict"}


@pytest.mark.asyncio
async def test_graph_conflict_prefers_newest_source(monkeypatch):
    from src.ai.langgraph.graph import build_graph

    async def _fake_retrieve(*args, **kwargs):
        return {
            "rag_payload": {
                "answer": "Найдены противоречия",
                "confidence": 0.9,
                "fallback_used": False,
                "sources": [
                    {
                        "source_id": "doc:old",
                        "excerpt": "Старое правило",
                        "timestamp": "2026-03-01T00:00:00",
                    },
                    {
                        "source_id": "doc:new",
                        "excerpt": "Новое правило",
                        "timestamp": "2026-04-10T00:00:00",
                    },
                ],
            }
        }

    monkeypatch.setattr("src.ai.langgraph.graph.retrieve_phase2_payload", _fake_retrieve)
    graph = build_graph()
    result = await graph.ainvoke(
        {"role": "employee", "query": "Какой регламент верный?", "user_id": "222", "chat_id": "111"},
        config={"configurable": {"thread_id": "tg:111:222"}},
    )
    sources = result["result"].sources
    assert result["decision"] == "conflict"
    assert len(sources) >= 2
    assert sources[0].source_id == "doc:new"


@pytest.mark.asyncio
async def test_retrieve_retries_with_ceiling_on_transient_failures():
    from src.ai.langgraph.nodes.retrieve_phase2 import retrieve_phase2_payload

    attempts = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        if attempts["n"] < 3:
            return httpx.Response(502, json={"detail": "upstream"})
        return httpx.Response(
            200,
            json={
                "answer": "ok",
                "confidence": 0.8,
                "sources": [{"source_id": "doc:x", "excerpt": "x", "timestamp": "2026-04-01T00:00:00"}],
                "fallback_used": False,
            },
        )

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(base_url="http://test", transport=transport) as client:
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("src.ai.langgraph.nodes.retrieve_phase2.settings.bot_retrieve_max_attempts", 3)
            mp.setattr("src.ai.langgraph.nodes.retrieve_phase2.settings.bot_retrieve_retry_backoff_seconds", 0.0)
            result = await retrieve_phase2_payload({"query": "q"}, client=client)

    assert attempts["n"] == 3
    assert result["rag_payload"]["answer"] == "ok"


@pytest.mark.asyncio
async def test_retrieve_stops_after_retry_ceiling():
    from src.ai.langgraph.nodes.retrieve_phase2 import retrieve_phase2_payload

    attempts = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        attempts["n"] += 1
        return httpx.Response(503, json={"detail": "down"})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(base_url="http://test", transport=transport) as client:
        with pytest.MonkeyPatch.context() as mp:
            mp.setattr("src.ai.langgraph.nodes.retrieve_phase2.settings.bot_retrieve_max_attempts", 2)
            mp.setattr("src.ai.langgraph.nodes.retrieve_phase2.settings.bot_retrieve_retry_backoff_seconds", 0.0)
            with pytest.raises(httpx.HTTPStatusError):
                await retrieve_phase2_payload({"query": "q"}, client=client)

    assert attempts["n"] == 2
