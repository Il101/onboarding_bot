from unittest.mock import patch


def _grouped_units():
    from src.ai.extraction.schemas import KnowledgeUnit

    return {
        "Оплаты": [
            KnowledgeUnit.model_validate(
                {
                    "fact": "Проверить статус оплаты в CRM",
                    "topic": "Оплаты",
                    "confidence": 0.9,
                    "source_refs": [
                        {
                            "source_id": "telegram:ops",
                            "excerpt": "Проверь статус оплаты в CRM",
                            "timestamp": "2026-04-12T11:00:00",
                        }
                    ],
                }
            ),
            KnowledgeUnit.model_validate(
                {
                    "fact": "Если статус pending > 24ч, эскалировать в финансы",
                    "topic": "Оплаты",
                    "confidence": 0.82,
                    "source_refs": [{"source_id": "pdf:guide", "excerpt": "эскалировать", "page": 4}],
                }
            ),
        ]
    }


def test_sop_markdown_has_fixed_ordered_sections():
    from src.ai.sop.generator import generate_sop_for_topic

    result = generate_sop_for_topic("Оплаты", _grouped_units()["Оплаты"])
    markdown = result["markdown"]
    assert "## Цель" in markdown
    assert "## Шаги" in markdown
    assert "## Исключения" in markdown
    assert "## Проверка результата" in markdown
    assert markdown.index("## Цель") < markdown.index("## Шаги") < markdown.index("## Исключения") < markdown.index("## Проверка результата")


def test_generator_does_not_emit_freeform_without_required_sections():
    from src.ai.sop.generator import generate_sop_for_topic

    result = generate_sop_for_topic("Оплаты", _grouped_units()["Оплаты"])
    markdown = result["markdown"]
    for header in ["## Цель", "## Шаги", "## Исключения", "## Проверка результата"]:
        assert header in markdown


def test_sop_includes_attribution_source_excerpt_and_locator():
    from src.ai.sop.generator import generate_sop_for_topic

    result = generate_sop_for_topic("Оплаты", _grouped_units()["Оплаты"])
    sources = result["sources"]
    assert len(sources) == 2
    assert all(source.source_id for source in sources)
    assert all(source.excerpt for source in sources)
    assert all((source.timestamp is not None) or (source.page is not None) for source in sources)


def test_insufficient_input_returns_non_generation_result():
    from src.ai.sop.generator import generate_sop_for_topic

    result = generate_sop_for_topic("Оплаты", [])
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
