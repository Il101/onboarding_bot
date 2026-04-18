import json
from dataclasses import dataclass
from typing import Optional

from bs4 import BeautifulSoup


@dataclass
class TelegramMessage:
    id: int
    date: str
    author: str
    author_id: str
    text: str
    is_service: bool
    is_bot: bool
    media_type: Optional[str]
    voice_path: Optional[str]
    edit_date: Optional[str] = None


def parse_text_field(text_field) -> str:
    if isinstance(text_field, str):
        return text_field
    if isinstance(text_field, list):
        parts = []
        for item in text_field:
            if isinstance(item, str):
                parts.append(item)
            elif isinstance(item, dict):
                parts.append(item.get("text", ""))
        return "".join(parts)
    return ""


def parse_telegram_export(filepath: str) -> list[TelegramMessage]:
    with open(filepath, "r", encoding="utf-8") as file:
        data = json.load(file)

    messages: list[TelegramMessage] = []
    for msg in data.get("messages", []):
        msg_type = msg.get("type", "")
        if msg_type == "service":
            continue

        text = parse_text_field(msg.get("text", ""))
        if not text and msg.get("media_type") != "voice_message":
            continue

        messages.append(
            TelegramMessage(
                id=msg["id"],
                date=msg.get("date", ""),
                author=msg.get("from", ""),
                author_id=msg.get("from_id", ""),
                text=BeautifulSoup(text, "html.parser").get_text(),
                is_service=msg_type == "service",
                is_bot="bot" in msg.get("from_id", "").lower(),
                media_type=msg.get("media_type"),
                voice_path=msg.get("file_name") if msg.get("media_type") == "voice_message" else None,
                edit_date=msg.get("edit_date"),
            )
        )
    return messages
