import pytest


def test_fallback_phrase_matches_locked_decision():
    from src.ai.langgraph.nodes.answer import compose_grounded_answer
    from src.bot.presenters import render_bot_message

    result = compose_grounded_answer(
        {
            "decision": "fallback",
            "rag_payload": {
                "confidence": 0.12,
                "fallback_used": True,
                "answer": "unused",
                "sources": [
                    {
                        "source_id": "seed:knowledge",
                        "excerpt": "Ближайший найденный фрагмент по запросу",
                        "timestamp": "2026-04-19T10:00:00",
                    }
                ],
            },
        }
    )
    rendered = render_bot_message(result)
    assert rendered.startswith("Я не знаю — обратитесь к коллеге")
    assert "Источники" in rendered


@pytest.mark.asyncio
async def test_graph_masks_internal_errors_with_safe_envelope(monkeypatch):
    from src.ai.langgraph.graph import build_graph
    from src.bot.presenters import render_bot_message

    async def _boom(*args, **kwargs):
        raise RuntimeError("secret stack details")

    monkeypatch.setattr("src.ai.langgraph.graph.retrieve_phase2_payload", _boom)

    graph = build_graph()
    result = await graph.ainvoke(
        {"role": "employee", "query": "Как оформить доступ?", "user_id": "7", "chat_id": "11"},
        config={"configurable": {"thread_id": "tg:11:7"}},
    )
    rendered = render_bot_message(result["result"])
    assert result["decision"] == "error"
    assert "secret" not in rendered.lower()
    assert "traceback" not in rendered.lower()
    assert "Источники" in rendered


@pytest.mark.asyncio
async def test_low_confidence_path_avoids_answer_synthesis(monkeypatch):
    from src.ai.langgraph.graph import build_graph

    async def _low_conf_retrieve(*args, **kwargs):
        return {
            "rag_payload": {
                "answer": "Недостаточно данных",
                "confidence": 0.1,
                "fallback_used": False,
                "sources": [
                    {
                        "source_id": "doc:low",
                        "excerpt": "Низкая уверенность",
                        "timestamp": "2026-04-10T10:00:00",
                    }
                ],
            }
        }

    def _forbidden_answer(*args, **kwargs):
        raise AssertionError("answer synthesis must not run on low confidence fallback path")

    monkeypatch.setattr("src.ai.langgraph.graph.retrieve_phase2_payload", _low_conf_retrieve)
    monkeypatch.setattr("src.ai.langgraph.graph.compose_grounded_answer", _forbidden_answer)
    graph = build_graph()
    result = await graph.ainvoke(
        {"role": "employee", "query": "Сложный вопрос", "user_id": "42", "chat_id": "99"},
        config={"configurable": {"thread_id": "tg:99:42"}},
    )

    assert result["decision"] == "fallback"
    assert result["result"].answer.startswith("Я не знаю — обратитесь к коллеге")


@pytest.mark.asyncio
async def test_offtopic_query_routes_to_offtopic_policy(monkeypatch):
    from src.ai.langgraph.graph import build_graph

    async def _fake_retrieve(*args, **kwargs):
        return {
            "rag_payload": {
                "answer": "unused",
                "confidence": 0.95,
                "fallback_used": False,
                "sources": [
                    {
                        "source_id": "doc:policy",
                        "excerpt": "Бот отвечает только на рабочие темы",
                        "timestamp": "2026-04-10T10:00:00",
                    }
                ],
            }
        }

    monkeypatch.setattr("src.ai.langgraph.graph.retrieve_phase2_payload", _fake_retrieve)
    graph = build_graph()
    result = await graph.ainvoke(
        {"role": "employee", "query": "Какая погода завтра?", "user_id": "5", "chat_id": "9"},
        config={"configurable": {"thread_id": "tg:9:5"}},
    )
    assert result["decision"] == "offtopic"
    assert "только по рабочим вопросам" in result["result"].answer.lower()
    assert "Источники" in result["result"].answer
