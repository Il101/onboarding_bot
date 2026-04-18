from __future__ import annotations

SOP_SECTION_ORDER = ["Цель", "Шаги", "Исключения", "Проверка результата"]


def render_sop(*, topic: str, goal: str, steps: list[str], exceptions: list[str], verification: list[str]) -> str:
    steps_md = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(steps)) or "1. Нет достаточных шагов"
    exceptions_md = "\n".join(f"- {item}" for item in exceptions) or "- Нет явных исключений"
    verification_md = "\n".join(f"- {item}" for item in verification) or "- Требуется ручная проверка"

    return (
        f"# SOP: {topic}\n\n"
        f"## Цель\n{goal}\n\n"
        f"## Шаги\n{steps_md}\n\n"
        f"## Исключения\n{exceptions_md}\n\n"
        f"## Проверка результата\n{verification_md}\n"
    )
