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
