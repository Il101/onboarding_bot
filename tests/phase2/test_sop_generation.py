from unittest.mock import patch


def _grouped_units():
    from src.ai.extraction.schemas import KnowledgeUnit

    return {
        "Payments": [
            KnowledgeUnit.model_validate(
                {
                    "fact": "Check payment status in CRM",
                    "topic": "Payments",
                    "confidence": 0.9,
                    "source_refs": [
                        {
                            "source_id": "telegram:ops",
                            "excerpt": "Check payment status in CRM",
                            "timestamp": "2026-04-12T11:00:00",
                        }
                    ],
                }
            ),
            KnowledgeUnit.model_validate(
                {
                    "fact": "If status is pending >24h, escalate to finance",
                    "topic": "Payments",
                    "confidence": 0.82,
                    "source_refs": [{"source_id": "pdf:guide", "excerpt": "escalate", "page": 4}],
                }
            ),
        ]
    }


def test_sop_markdown_has_fixed_ordered_sections():
    from src.ai.sop.generator import generate_sop_for_topic

    result = generate_sop_for_topic("Payments", _grouped_units()["Payments"])
    markdown = result["markdown"]
    assert "## Goal" in markdown
    assert "## Steps" in markdown
    assert "## Exceptions" in markdown
    assert "## Verification" in markdown
    assert (
        markdown.index("## Goal")
        < markdown.index("## Steps")
        < markdown.index("## Exceptions")
        < markdown.index("## Verification")
    )


def test_generator_does_not_emit_freeform_without_required_sections():
    from src.ai.sop.generator import generate_sop_for_topic

    result = generate_sop_for_topic("Payments", _grouped_units()["Payments"])
    markdown = result["markdown"]
    for header in ["## Goal", "## Steps", "## Exceptions", "## Verification"]:
        assert header in markdown


def test_sop_includes_attribution_source_excerpt_and_locator():
    from src.ai.sop.generator import generate_sop_for_topic

    result = generate_sop_for_topic("Payments", _grouped_units()["Payments"])
    sources = result["sources"]
    assert len(sources) == 2
    assert all(source.source_id for source in sources)
    assert all(source.excerpt for source in sources)
    assert all((source.timestamp is not None) or (source.page is not None) for source in sources)


def test_insufficient_input_returns_non_generation_result():
    from src.ai.sop.generator import generate_sop_for_topic

    result = generate_sop_for_topic("Payments", [])
    assert result["generated"] is False
    assert result["markdown"] is None


def test_generate_sop_task_returns_markdown_artifact_and_sources():
    from src.tasks.knowledge import generate_sop_task

    with patch.object(generate_sop_task, "update_state", return_value=None):
        result = generate_sop_task.run(source_id="src1", grouped_units=_grouped_units())

    assert result["status"] == "completed"
    assert result["topics"][0]["generated"] is True
    assert result["topics"][0]["markdown"]
    assert result["topics"][0]["sources"]
