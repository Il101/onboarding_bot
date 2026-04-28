from __future__ import annotations

SOP_SECTION_ORDER = ["Goal", "Steps", "Exceptions", "Verification"]


def render_sop(*, topic: str, goal: str, steps: list[str], exceptions: list[str], verification: list[str]) -> str:
    steps_md = "\n".join(f"{i + 1}. {step}" for i, step in enumerate(steps)) or "1. No sufficient steps provided"
    exceptions_md = "\n".join(f"- {item}" for item in exceptions) or "- No explicit exceptions"
    verification_md = "\n".join(f"- {item}" for item in verification) or "- Manual verification required"

    return (
        f"# SOP: {topic}\n\n"
        f"## Goal\n{goal}\n\n"
        f"## Steps\n{steps_md}\n\n"
        f"## Exceptions\n{exceptions_md}\n\n"
        f"## Verification\n{verification_md}\n"
    )
