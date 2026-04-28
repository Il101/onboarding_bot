from __future__ import annotations

from unittest.mock import MagicMock, patch


def test_publishable_runtime_flow_reaches_index_writer_and_grouped_sop_path():
    from src.tasks.knowledge import extract_knowledge_task

    extraction_outputs = [
        [
            {
                "fact": "Open CRM and check the client card",
                "topic": "CRM",
                "confidence": 0.9,
                "source_refs": [
                    {
                        "source_id": "src-crm",
                        "excerpt": "Open CRM",
                        "timestamp": "2026-04-12T11:00:00",
                    }
                ],
            }
        ]
    ]
    sop_delay = MagicMock()
    index_writer = MagicMock(return_value=1)

    with (
        patch.object(extract_knowledge_task, "update_state", return_value=None),
        patch("src.tasks.knowledge.generate_sop_task.delay", sop_delay),
    ):
        result = extract_knowledge_task.run(
            source_id="src-crm",
            chunks=[{"text": "crm", "metadata": {"source_id": "src-crm"}}],
            extraction_outputs=extraction_outputs,
            index_writer=index_writer,
        )

    index_writer.assert_called_once()
    sop_delay.assert_called_once()
    _, kwargs = sop_delay.call_args
    assert kwargs["source_id"] == "src-crm"
    assert list(kwargs["grouped_units"].keys()) == ["CRM"]
    assert result["publishable_count"] == 1
    assert result["indexed_count"] == 1


def test_low_confidence_units_stay_review_only_not_indexed_or_sop_dispatched():
    from src.tasks.knowledge import extract_knowledge_task

    extraction_outputs = [
        [
            {
                "fact": "Unverified rule from chat",
                "topic": "Operations",
                "confidence": 0.2,
                "source_refs": [
                    {
                        "source_id": "src-ops",
                        "excerpt": "unverified rule",
                        "timestamp": "2026-04-12T12:00:00",
                    }
                ],
            }
        ]
    ]
    sop_delay = MagicMock()
    index_writer = MagicMock(return_value=0)

    with (
        patch.object(extract_knowledge_task, "update_state", return_value=None),
        patch("src.tasks.knowledge.generate_sop_task.delay", sop_delay),
    ):
        result = extract_knowledge_task.run(
            source_id="src-ops",
            chunks=[{"text": "ops", "metadata": {"source_id": "src-ops"}}],
            extraction_outputs=extraction_outputs,
            index_writer=index_writer,
        )

    index_writer.assert_called_once_with([])
    sop_delay.assert_not_called()
    assert result["publishable_count"] == 0
    assert result["review_needed_count"] == 1
