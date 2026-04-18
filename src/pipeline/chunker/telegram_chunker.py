from src.pipeline.chunker.text_chunker import chunk_text
from src.pipeline.filters.grouping import group_messages_chronologically


def chunk_telegram_messages(messages: list, window_minutes: int = 30) -> list[dict]:
    groups = group_messages_chronologically(messages, window_minutes)
    chunks: list[dict] = []

    for group in groups:
        group_text = "\n".join(f"[{m.author}]: {m.text}" for m in group if m.text)
        metadata = {
            "source_type": "telegram",
            "date_range": f"{group[0].date} - {group[-1].date}",
            "authors": list({m.author for m in group}),
            "chat": group[0].author,
        }

        text_chunks = chunk_text(group_text)
        for idx, chunk in enumerate(text_chunks):
            chunks.append({"text": chunk, "metadata": {**metadata, "chunk_index": idx}})

    return chunks
