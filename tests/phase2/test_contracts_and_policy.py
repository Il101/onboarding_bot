import pytest
from pydantic import ValidationError


def test_knowledge_unit_contract():
    from src.ai.extraction.schemas import KnowledgeUnit

    valid_payload = {
        "fact": "Before running the report, select the current branch.",
        "topic": "Reporting",
        "confidence": 0.82,
        "source_refs": [
            {
                "source_id": "telegram:ops",
                "excerpt": "Select branch first, otherwise the report is empty",
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
            "excerpt": "Without locator",
        }
    ]
    with pytest.raises(ValidationError):
        KnowledgeUnit.model_validate(no_locator)


def test_rag_answer_contract():
    from src.ai.rag.contracts import RagAnswer

    valid = {
        "answer": "Check order status in CRM and open the client card.",
        "confidence": 0.77,
        "fallback_used": False,
        "sources": [
            {
                "source_id": "pdf:onboarding-guide",
                "excerpt": "Step 1: open CRM. Step 2: find client by number.",
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


def test_publish_policy_threshold():
    from src.ai.extraction.publish_policy import should_publish_knowledge
    from src.ai.extraction.schemas import KnowledgeUnit

    blocked_unit = KnowledgeUnit.model_validate(
        {
            "fact": "If order is not found, escalate to shift lead.",
            "topic": "Escalation",
            "confidence": 0.2,
            "source_refs": [
                {
                    "source_id": "telegram:ops",
                    "excerpt": "If order is not found, contact shift lead.",
                    "timestamp": "2026-04-11T12:00:00",
                }
            ],
        }
    )
    decision = should_publish_knowledge(blocked_unit)
    assert decision.publish is False
    assert decision.reason


def test_phase2_threshold_settings(monkeypatch):
    from src.core.config import Settings

    settings = Settings()
    assert settings.knowledge_confidence_threshold == 0.7
    assert settings.rag_relevance_threshold == 0.35
    assert settings.rag_similarity_top_k == 8
    assert settings.rag_sparse_top_k == 12
    assert settings.rag_hybrid_top_k == 6
    assert settings.rag_rerank_top_k == 5

    monkeypatch.setenv("KNOWLEDGE_CONFIDENCE_THRESHOLD", "0.81")
    monkeypatch.setenv("RAG_RELEVANCE_THRESHOLD", "0.41")
    overridden = Settings()
    assert overridden.knowledge_confidence_threshold == 0.81
    assert overridden.rag_relevance_threshold == 0.41
