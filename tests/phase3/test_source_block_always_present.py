from src.ai.langgraph.state import BotAnswer, SourceRef
from src.bot.presenters import render_bot_message, render_sources_block


def _answer(text: str) -> BotAnswer:
    return BotAnswer(
        answer=text,
        confidence=0.9,
        fallback_used=False,
        sources=[SourceRef(source_id="doc:base", excerpt="Base source", timestamp="2026-04-01T00:00:00")],
    )


def test_answer_branch_renders_separate_sources_block():
    rendered = render_bot_message(
        _answer("1. Open CRM\n2. Find the client\n3. Check the profile"),
    )
    assert rendered.startswith("1. Open CRM")
    assert "\n\nSources:\n" in rendered
    assert "- doc:base: Base source" in rendered


def test_fallback_branch_renders_exact_phrase_and_sources_block():
    rendered = render_bot_message(_answer("I don't know - please ask a colleague."))
    assert rendered.startswith("I don't know - please ask a colleague.")
    assert "\n\nSources:\n" in rendered


def test_deny_offtopic_clarify_each_include_sources_block():
    deny = render_bot_message(_answer("Access restricted: this bot is available only to company employees."))
    offtopic = render_bot_message(_answer("I can only help with work-related questions."))
    clarify = render_bot_message(_answer("Please clarify which process you need help with."))
    assert "Sources" in deny
    assert "Sources" in offtopic
    assert "Sources" in clarify


def test_render_sources_truncates_and_preserves_score_then_freshness_order():
    long_excerpt = "Very long excerpt " * 20
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
                "excerpt": "New medium source",
                "score": 0.5,
                "timestamp": "2026-05-01T10:00:00",
            },
            {
                "source_id": "doc:mid-old",
                "excerpt": "Old medium source",
                "score": 0.5,
                "timestamp": "2026-01-01T10:00:00",
            },
        ],
        excerpt_max_len=80,
    )
    lines = rendered.splitlines()
    assert lines[0] == "Sources:"
    assert lines[1].startswith("- doc:high:")
    assert lines[2].startswith("- doc:mid-new:")
    assert lines[3].startswith("- doc:mid-old:")
    assert "…" in lines[1]
