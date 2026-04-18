import re

CHARS_PER_TOKEN = 3.5
TARGET_TOKENS = 400
MAX_TOKENS = 500
MIN_TOKENS = 300


def chunk_text(text: str, overlap_sentences: int = 1) -> list[str]:
    if not text.strip():
        return []

    paragraphs = _split_markdown_paragraphs(text)
    chunks: list[str] = []

    for paragraph in paragraphs:
        sentences = _split_into_sentences([paragraph])
        i = 0
        while i < len(sentences):
            chunk_sentences = []
            char_count = 0
            while i < len(sentences):
                sentence = sentences[i]
                if char_count + len(sentence) > MAX_TOKENS * CHARS_PER_TOKEN and chunk_sentences:
                    break
                chunk_sentences.append(sentence)
                char_count += len(sentence)
                i += 1

            if chunk_sentences:
                chunks.append(" ".join(chunk_sentences))

            if i < len(sentences):
                i = max(i - overlap_sentences, i - len(chunk_sentences) + 1)

    return chunks


def _split_markdown_paragraphs(text: str) -> list[str]:
    return [part for part in re.split(r"\n(?=#{1,3}\s)", text) if part.strip()]


def _split_into_sentences(paragraphs: list[str]) -> list[str]:
    sentences: list[str] = []
    for paragraph in paragraphs:
        parts = re.split(r"(?<=[.!?])\s+", paragraph.strip())
        sentences.extend([s.strip() for s in parts if s.strip()])
    return sentences
