from unittest.mock import patch


def _chunks():
    return [
        {
            "id": "telegram:src1:0",
            "text": "Before running the report, select branch",
            "metadata": {"source_id": "src1", "timestamp": "2026-04-12T11:00:00"},
        },
        {
            "id": "pdf:src2:0",
            "text": "On payment error, escalate to finance manager",
            "metadata": {"source_id": "src2", "page": 2},
        },
    ]


def test_extract_returns_schema_valid_units():
    from src.ai.extraction.extractor import extract_knowledge_units

    raw = [
        [
            {
                "fact": "Select branch before running the report",
                "topic": "Reporting",
                "confidence": 0.9,
                "source_refs": [
                    {
                        "source_id": "src1",
                        "excerpt": "need to select branch",
                        "timestamp": "2026-04-12T11:00:00",
                    }
                ],
            }
        ],
        [
            {
                "fact": "On payment error, escalate to manager",
                "topic": "Escalation",
                "confidence": 0.85,
                "source_refs": [{"source_id": "src2", "excerpt": "escalate", "page": 2}],
            }
        ],
    ]

    result = extract_knowledge_units(_chunks(), extraction_outputs=raw)
    assert len(result["all_units"]) == 2
    assert all(hasattr(unit, "fact") for unit in result["all_units"])


def test_single_fact_invariant_one_unit_per_atomic_fact():
    from src.ai.extraction.extractor import extract_knowledge_units

    raw = [
        [
            {
                "fact": "Open CRM",
                "topic": "CRM",
                "confidence": 0.91,
                "source_refs": [{"source_id": "src1", "excerpt": "Open CRM", "timestamp": "2026-04-12T11:00:00"}],
            }
        ]
    ]

    result = extract_knowledge_units(_chunks()[:1], extraction_outputs=raw)
    assert len(result["all_units"]) == 1
    assert result["all_units"][0].fact == "Open CRM"


def test_low_confidence_units_go_to_review_queue():
    from src.ai.extraction.extractor import extract_knowledge_units

    raw = [
        [
            {
                "fact": "Unverified rule",
                "topic": "Operations",
                "confidence": 0.2,
                "source_refs": [{"source_id": "src1", "excerpt": "...", "timestamp": "2026-04-12T11:00:00"}],
            }
        ]
    ]

    result = extract_knowledge_units(_chunks()[:1], extraction_outputs=raw)
    assert len(result["publishable"]) == 0
    assert len(result["review_needed"]) == 1


def test_grouping_clusters_publishable_by_topic():
    from src.ai.extraction.extractor import extract_knowledge_units, group_units_by_topic

    raw = [
        [
            {
                "fact": "Step 1",
                "topic": "Payments",
                "confidence": 0.9,
                "source_refs": [{"source_id": "src1", "excerpt": "Step 1", "timestamp": "2026-04-12T11:00:00"}],
            },
            {
                "fact": "Step 2",
                "topic": "Payments",
                "confidence": 0.8,
                "source_refs": [{"source_id": "src1", "excerpt": "Step 2", "timestamp": "2026-04-12T11:01:00"}],
            },
        ]
    ]

    result = extract_knowledge_units(_chunks()[:1], extraction_outputs=raw)
    grouped = group_units_by_topic(result["publishable"])
    assert list(grouped.keys()) == ["Payments"]
    assert len(grouped["Payments"]) == 2


def test_extract_task_reports_progress_stages():
    from src.tasks.knowledge import extract_knowledge_task

    stages = []

    def _capture(*, state, meta):
        if state == "PROGRESS":
            stages.append(meta["stage"])

    raw = [
        [
            {
                "fact": "Select branch",
                "topic": "Reporting",
                "confidence": 0.9,
                "source_refs": [
                    {"source_id": "src1", "excerpt": "select branch", "timestamp": "2026-04-12T11:00:00"}
                ],
            }
        ]
    ]

    with (
        patch.object(extract_knowledge_task, "update_state", side_effect=_capture),
        patch("src.tasks.knowledge.generate_sop_task.delay", return_value=None),
    ):
        extract_knowledge_task.run(
            source_id="src1",
            chunks=_chunks()[:1],
            extraction_outputs=raw,
            index_writer=lambda units: len(units),
        )

    assert stages == ["extracting", "validating", "gating", "grouping", "completed"]
