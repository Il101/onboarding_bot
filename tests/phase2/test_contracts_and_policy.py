import pytest
from pydantic import ValidationError


def test_knowledge_unit_contract():
    from src.ai.extraction.schemas import KnowledgeUnit

    valid_payload = {
        "fact": "Перед запуском отчета нужно выбрать текущий филиал.",
        "topic": "Отчетность",
        "confidence": 0.82,
        "source_refs": [
            {
                "source_id": "telegram:ops",
                "excerpt": "Сначала выберите филиал, иначе отчет пустой",
                "timestamp": "2026-04-10T10:00:00",
            }
        ],
    }

    unit = KnowledgeUnit.model_validate(valid_payload)
    assert unit.fact == valid_payload["fact"]

    for missing_key in ["fact", "topic", "source_refs", "confidence"]:
        bad = dict(valid_payload)
        bad.pop(missing_key)
        with pytest.raises(ValidationError):
            KnowledgeUnit.model_validate(bad)

    too_low = dict(valid_payload)
    too_low["confidence"] = -0.1
    with pytest.raises(ValidationError):
        KnowledgeUnit.model_validate(too_low)

    too_high = dict(valid_payload)
    too_high["confidence"] = 1.5
    with pytest.raises(ValidationError):
        KnowledgeUnit.model_validate(too_high)

    no_locator = dict(valid_payload)
    no_locator["source_refs"] = [
        {
            "source_id": "telegram:ops",
            "excerpt": "Без локатора",
        }
    ]
    with pytest.raises(ValidationError):
        KnowledgeUnit.model_validate(no_locator)


def test_rag_answer_contract():
    from src.ai.rag.contracts import RagAnswer

    valid = {
        "answer": "Нужно проверить статус заказа в CRM и открыть карточку клиента.",
        "confidence": 0.77,
        "fallback_used": False,
        "sources": [
            {
                "source_id": "pdf:onboarding-guide",
                "excerpt": "Шаг 1: открыть CRM. Шаг 2: найти клиента по номеру.",
                "score": 0.77,
                "page": 3,
            }
        ],
    }

    answer = RagAnswer.model_validate(valid)
    assert answer.sources[0].source_id == "pdf:onboarding-guide"

    missing_excerpt = dict(valid)
    missing_excerpt["sources"] = [{"source_id": "x", "score": 0.4}]
    with pytest.raises(ValidationError):
        RagAnswer.model_validate(missing_excerpt)
