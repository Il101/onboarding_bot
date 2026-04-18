def _render_with_sources(answer_text: str, sources: list[dict]) -> str:
    sources_lines = "\n".join(f"- {item['source_id']}: {item['excerpt']}" for item in sources)
    return f"{answer_text}\n\nИсточники:\n{sources_lines}"


def test_sources_block_present_for_regular_answer():
    rendered = _render_with_sources(
        "1. Откройте CRM\n2. Найдите клиента\n3. Проверьте карточку",
        [{"source_id": "pdf:onboarding", "excerpt": "Шаги по работе с CRM"}],
    )
    assert "Источники" in rendered
    assert "- pdf:onboarding:" in rendered


def test_sources_block_present_for_fallback_answer():
    rendered = _render_with_sources(
        "Я не знаю — обратитесь к коллеге",
        [{"source_id": "seed:knowledge", "excerpt": "Ближайший найденный фрагмент по запросу"}],
    )
    assert "Источники" in rendered
    assert "- seed:knowledge:" in rendered


def test_sources_block_present_for_access_denied_answer():
    from src.bot.auth import build_access_denied_answer

    denied = build_access_denied_answer(reason="role_not_allowed")
    rendered = _render_with_sources(
        denied.answer,
        [item.model_dump() for item in denied.sources],
    )
    assert "Источники" in rendered
    assert denied.fallback_used is True


def test_answer_node_formats_russian_steps_with_sources():
    from src.ai.langgraph.nodes.answer import compose_grounded_answer

    result = compose_grounded_answer(
        {
            "query": "Как оформить доступ в CRM?",
            "decision": "answer",
            "rag_payload": {
                "confidence": 0.86,
                "fallback_used": False,
                "answer": "Оформление доступа CRM",
                "sources": [
                    {"source_id": "doc:crm", "excerpt": "Шаги оформления доступа", "timestamp": "2026-04-10T10:00:00"}
                ],
            },
        }
    )
    lines = [line for line in result.answer.splitlines() if line.strip()]
    numbered = [line for line in lines if line.startswith(("1.", "2.", "3.", "4.", "5.", "6."))]
    assert 3 <= len(numbered) <= 6
    assert "Источники" in result.answer
    assert result.sources


def test_fallback_branch_uses_exact_locked_phrase_with_sources():
    from src.ai.langgraph.nodes.answer import compose_grounded_answer

    result = compose_grounded_answer(
        {
            "decision": "fallback",
            "rag_payload": {
                "confidence": 0.2,
                "fallback_used": True,
                "answer": "unused",
                "sources": [
                    {
                        "source_id": "seed:knowledge",
                        "excerpt": "Ближайший найденный фрагмент по запросу",
                        "timestamp": "2026-04-01T00:00:00",
                    }
                ],
            },
        }
    )
    assert result.answer.startswith("Я не знаю — обратитесь к коллеге")
    assert "Источники" in result.answer
    assert result.fallback_used is True


def test_conflict_branch_marks_conflict_and_prefers_fresh_source():
    from src.ai.langgraph.nodes.answer import compose_grounded_answer

    result = compose_grounded_answer(
        {
            "decision": "conflict",
            "rag_payload": {
                "confidence": 0.74,
                "fallback_used": False,
                "answer": "Нужно выбрать актуальную инструкцию",
                "sources": [
                    {"source_id": "doc:old", "excerpt": "Делайте по старой схеме", "timestamp": "2026-01-01T10:00:00"},
                    {"source_id": "doc:new", "excerpt": "Делайте по новой схеме", "timestamp": "2026-04-20T10:00:00"},
                ],
            },
        }
    )
    assert "конфликт" in result.answer.lower()
    assert result.sources[0].source_id == "doc:new"
    assert "Источники" in result.answer


def test_offtopic_branch_returns_concise_refusal_with_sources():
    from src.ai.langgraph.nodes.answer import compose_grounded_answer

    result = compose_grounded_answer(
        {
            "decision": "offtopic",
            "rag_payload": {"confidence": 1.0, "fallback_used": True, "answer": "", "sources": []},
        }
    )
    assert "рабоч" in result.answer.lower()
    assert "Источники" in result.answer
    assert result.sources
