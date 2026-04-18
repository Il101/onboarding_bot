from src.ai.langgraph.state import BotAnswer, SourceRef
from src.bot.presenters import render_bot_message, render_sources_block


def _answer(text: str) -> BotAnswer:
    return BotAnswer(
        answer=text,
        confidence=0.9,
        fallback_used=False,
        sources=[SourceRef(source_id="doc:base", excerpt="Базовый источник", timestamp="2026-04-01T00:00:00")],
    )


def test_answer_branch_renders_separate_sources_block():
    rendered = render_bot_message(
        _answer("1. Откройте CRM\n2. Найдите клиента\n3. Проверьте карточку"),
    )
    assert rendered.startswith("1. Откройте CRM")
    assert "\n\nИсточники:\n" in rendered
    assert "- doc:base: Базовый источник" in rendered


def test_fallback_branch_renders_exact_phrase_and_sources_block():
    rendered = render_bot_message(_answer("Я не знаю — обратитесь к коллеге"))
    assert rendered.startswith("Я не знаю — обратитесь к коллеге")
    assert "\n\nИсточники:\n" in rendered


def test_deny_offtopic_clarify_each_include_sources_block():
    deny = render_bot_message(_answer("Доступ ограничен: бот доступен только сотрудникам компании."))
    offtopic = render_bot_message(_answer("Я помогаю только по рабочим вопросам."))
    clarify = render_bot_message(_answer("Уточните, пожалуйста, по какому процессу нужен ответ?"))
    assert "Источники" in deny
    assert "Источники" in offtopic
    assert "Источники" in clarify


def test_render_sources_truncates_and_preserves_score_then_freshness_order():
    long_excerpt = "Очень длинный фрагмент " * 20
    rendered = render_sources_block(
        [
            {
                "source_id": "doc:high",
                "excerpt": long_excerpt,
                "score": 0.99,
                "timestamp": "2026-04-01T10:00:00",
            },
            {
                "source_id": "doc:mid-new",
                "excerpt": "Новый средний источник",
                "score": 0.5,
                "timestamp": "2026-05-01T10:00:00",
            },
            {
                "source_id": "doc:mid-old",
                "excerpt": "Старый средний источник",
                "score": 0.5,
                "timestamp": "2026-01-01T10:00:00",
            },
        ],
        excerpt_max_len=80,
    )
    lines = rendered.splitlines()
    assert lines[0] == "Источники:"
    assert lines[1].startswith("- doc:high:")
    assert lines[2].startswith("- doc:mid-new:")
    assert lines[3].startswith("- doc:mid-old:")
    assert "…" in lines[1]
