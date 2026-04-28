import re

NOISE_PATTERNS = [
    re.compile(r"^\s*$"),
    re.compile(r"^[.\-]+$", re.IGNORECASE),
    re.compile(r"^[+\-]$", re.IGNORECASE),
]

NOISE_EXACT = {"ok", "oki", "ok!", "ok.", "thanks", "thx", "yes", "hello", "+"}


def is_noise(message_text: str, is_service: bool, is_bot: bool, author: str) -> bool:
    if is_service:
        return True
    if is_bot:
        return True

    stripped = message_text.strip().lower()
    if stripped in NOISE_EXACT:
        return True
    for pattern in NOISE_PATTERNS:
        if pattern.match(stripped):
            return True
    return False


def filter_messages(messages):
    return [m for m in messages if not is_noise(m.text, m.is_service, m.is_bot, m.author)]
