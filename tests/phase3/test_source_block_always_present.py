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
