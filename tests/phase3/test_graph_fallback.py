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
