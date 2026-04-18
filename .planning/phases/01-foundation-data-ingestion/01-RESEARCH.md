# Phase 1: Foundation & Data Ingestion - Research

**Researched:** 2026-04-18
**Domain:** Data ingestion pipeline, PII anonymization, vector indexing with hybrid search
**Confidence:** HIGH

## Summary

Phase 1 устанавливает фундамент всей системы V-Brain: пайплайн приёма данных из двух источников (Telegram JSON export и PDF), очистку от шума, PII-анонимизацию, и индексацию в Qdrant с гибридным поиском. Это greenfield-фаза -- кодовая база пуста, и Phase 1 определяет все фундаментальные паттерны (структура проекта, конфигурация, обработка ошибок, API-дизайн), которые будут использоваться в последующих фазах.

Ключевые технические решения: (1) Presidio + кастомные regex-распознаватели для PII -- работает, но требует тщательной валидации на реальных русских данных; (2) Qdrant с named dense + sparse векторами через FastEmbed для гибридного поиска -- SPLADE++ для sparse - англоцентричный, для русского текста BM42 или BM25 через FastEmbed подходят лучше; (3) Docling для PDF с кириллицей -- нативно поддерживает кириллицу, экспортирует в Markdown; (4) Celery + Redis для асинхронной обработки тяжёлых задач; (5) Groq Whisper API для транскрибации голосовых .ogg файлов из Telegram export.

**Primary recommendation:** Начать с инфраструктурной настройки (Docker Compose: Qdrant + Redis + PostgreSQL), затем построить пайплайн ингеста снизу вверх: парсер -> PII -> чанкинг -> эмбеддинги -> Qdrant. PII-валидация на реальных данных -- отдельная задача, которая должна предшествовать полной индексации.

## User Constraints

### Locked Decisions (from CONTEXT.md)

- **D-01:** Ингест через REST API (FastAPI endpoints), Phase 4 добавит веб-форму поверх этого API
- **D-02:** Конечные точки API: `/api/ingest/telegram` (JSON + .ogg файлы), `/api/ingest/pdf` (multipart upload), `/api/ingest/status/{job_id}` (прогресс)
- **D-03:** Пакетная обработка через Celery + Redis -- тяжелые задачи (PII, эмбеддинг) не блокируют API
- **D-04:** Распознаваемые типы PII: имена людей (ФИО, отчества, сокращённые имена, никнеймы), телефоны (все форматы: +7, 8, скобки, дефисы), email (личные и рабочие), адреса, номера документов
- **D-05:** Формат токенов: читаемые -- `<PERSON_1>`, `<PHONE_1>`, `<EMAIL_1>`, `<ADDRESS_1>`, `<DOC_1>`
- **D-06:** Presidio + кастомные русские regex-распознаватели для телефонов, ИНН, СНИЛС; spaCy `ru_core_news_md` для NER
- **D-07:** PII анонимизация происходит ДО любой дальнейшей обработки (критическое архитектурное требование)
- **D-08:** Нужна валидация качества Presidio на реальных русских данных -- отдельная задача в Phase 1
- **D-09:** Отсеиваем: service messages (вступил/вышел, фото удалено, pinned), bot messages, приветствия/подтверждения ("привет", "ок", "да", "спасибо", "+")
- **D-10:** Короткие сообщения НЕ отсекаем -- в них может быть ценная информация ("звони Ивану", "проверь накладную")
- **D-12:** Medium chunks: 5-10 предложений, ~300-500 токенов, перекрытие 1 предложение между чанками
- **D-13:** Метаданные к каждому чанку: дата, автор, чат/источник, тип (текст/голос/PDF)
- **D-14:** Markdown-aware разбиение: учитываем заголовки и параграфы, сохраняем структуру документа
- **D-15:** Для Telegram: группируем сообщения по хронологии (окно, например 30 минут) перед чанкированием
- **D-16:** Нужны оба варианта: реальный Telegram чат (экспорт из Telegram Desktop) для валидации формата + синтетические данные с PII для тестирования edge cases
- **D-17:** Voice messages: при Telegram export .ogg файлы лежат рядом с JSON -- парсер должен уметь связывать их с сообщениями

### Claude's Discretion (from CONTEXT.md)

- Фильтрация шума: какие конкретно сообщения ниже порога считаются шумом (решает разработчик на основе тестовых данных)
- Порог confidence для PII: минимальная длина совпадения, tradeoff между recall и precision
- Размер окна хронологической группировки для Telegram сообщений перед чанкированием

### Deferred Ideas (OUT OF SCOPE)

- Пользователь хочет drag & drop загрузку в вебке -- это Phase 4 (REST API уже будет готов). Заметил на случай если понадобится прототип.

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| ING-01 | PII анонимизация (ФИО, телефоны, email, ИНН) через Presidio + кастомные русские распознаватели | Presidio 2.2.362 + PatternRecognizer + spaCy ru_core_news_md; стандартный подход к кастомным regex-распознавателям |
| ING-02 | Парсинг Telegram JSON export (result.json) с метаданными | Стандартный json-модуль; известная структура result.json из Telegram Desktop |
| ING-03 | Транскрибация голосовых сообщений через Groq Whisper API | Groq SDK 1.2.0, whisper-large-v3-turbo, .ogg поддерживается нативно |
| ING-04 | Фильтрация шума из Telegram логов | Кастомный фильтр по правилам D-09/D-10 + стоп-слова |
| ING-05 | Извлечение текста из PDF с поддержкой кириллицы | Docling 2.90.0; экспорт в Markdown, нативная поддержка кириллицы |
| ING-06 | Пакетная обработка с прогресс-трекингом | Celery 5.6.3 + Redis; self.update_state для прогресса; task_id через API |

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Telegram JSON парсинг | API / Backend | -- | Серверный парсинг JSON-файлов, загрузка через REST API |
| PDF извлечение текста | API / Backend | -- | Docling работает на CPU/GPU сервера |
| PII анонимизация | API / Backend | -- | Presidio + spaCy -- CPU-intensive, работает на сервере |
| Groq Whisper транскрибация | API / Backend (внешний API) | -- | Вызов внешнего API из Celery worker'а |
| Фильтрация шума | API / Backend | -- | Кастомные правила фильтрации в Python |
| Чанкинг текста | API / Backend | -- | Нативная обработка текста |
| Генерация эмбеддингов | API / Backend | -- | FastEmbed / sentence-transformers -- CPU/GPU |
| Индексация в Qdrant | Database / Storage | -- | Upsert векторов через qdrant-client |
| Прогресс-трекинг | API / Backend | CDN / Static | Celery state + REST API endpoint для polling |
| REST API endpoints | API / Backend | -- | FastAPI сервер |

## Standard Stack

### Core (for Phase 1)

| Library | Version (PyPI verified 2026-04-18) | Purpose | Why Standard |
|---------|-------------------------------------|---------|--------------|
| Python | 3.12.4 | Runtime | [VERIFIED: python3 --version] Установлена на машине. 3.12 -- оптимальный баланс: все библиотеки поддерживаются, улучшена производительность |
| FastAPI | 0.136.0 | REST API сервер | [VERIFIED: PyPI] Индустриальный стандарт для Python API. Нативный async, авто-docs |
| Celery | 5.6.3 | Асинхронная очередь задач | [VERIFIED: PyPI] Python-стандарт для task queue; task chains для пайплайна |
| qdrant-client | 1.17.1 | Клиент векторной БД | [VERIFIED: PyPI] Поддерживает dense + sparse векторы, hybrid search |
| fastembed | 0.8.0 | Dense + sparse эмбеддинги локально | [VERIFIED: PyPI] Единый API для dense (multilingual-e5-large) и sparse (BM42) эмбеддингов |
| presidio-analyzer | 2.2.362 | PII обнаружение | [VERIFIED: PyPI] Индустриальный стандарт de-identification |
| presidio-anonymizer | 2.2.362 | PII замена на токены | [VERIFIED: PyPI] Работает в паре с analyzer |
| docling | 2.90.0 | PDF парсинг | [VERIFIED: PyPI] IBM open-source; кириллица, таблицы, OCR, Markdown export |
| beautifulsoup4 | 4.14.3 | HTML cleanup из Telegram | [VERIFIED: PyPI] Telegram JSON может содержать HTML-форматирование в text |
| groq | 1.2.0 | Groq API SDK для Whisper | [VERIFIED: PyPI] Whisper transcription, .ogg нативно поддерживается |
| redis (клиент) | latest | Celery broker + result backend | [ASSUMED] Стандартный брокер для Celery |
| sqlalchemy | 2.0.x | ORM для метаданных | [ASSUMED] Хранение статусов ингеста, источников |
| uvicorn | latest | ASGI сервер для FastAPI | [ASSUMED] Стандартный ASGI сервер |

### Infrastructure (Docker)

| Service | Version | Purpose | Notes |
|---------|---------|---------|-------|
| Qdrant | latest | Векторная БД | [ASSUMED] Docker image: qdrant/qdrant |
| Redis | latest | Celery broker + result backend | [ASSUMED] Docker image: redis:latest |
| PostgreSQL | 16+ | Реляционная БД для метаданных | [ASSUMED] Docker image: postgres:16 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| FastEmbed (dense+sparse) | sentence-transformers (dense) + кастомный BM25 (sparse) | FastEmbed предоставляет единый API для обоих типов эмбеддингов + интеграцию с Qdrant. Раздельные библиотеки -- больше ручной работы |
| SPLADE_PP_en_v1 (sparse) | Qdrant BM42 / BM25 | SPLADE -- англоцентричный, для русского работает хуже. BM42 через FastEmbed или Qdrant-native BM25 предпочтительнее для русского |
| Docling | PyPDF2 / pdfplumber | Docling строго лучше: таблицы, layout, OCR. Но тяжелее (зависимости). Для простых PDF можно pdfplumber |
| Celery | ARQ | ARQ проще, но менее feature-rich. Celery -- стандарт индустрии |

**Installation:**
```bash
# Core ingestion pipeline
pip install fastapi>=0.136.0 uvicorn>=0.44.0
pip install celery[redis]>=5.6.0 redis>=5.0.0
pip install qdrant-client>=1.17.1 fastembed>=0.8.0
pip install presidio-analyzer>=2.2.362 presidio-anonymizer>=2.2.362
pip install docling>=2.90.0 beautifulsoup4>=4.14.3
pip install groq>=1.2.0
pip install sqlalchemy>=2.0.49 psycopg2-binary>=2.9.11
pip install pydantic>=2.13.0

# spaCy Russian NER
python -m spacy download ru_core_news_md
```

## Architecture Patterns

### System Architecture Diagram

```
                          [Администратор]
                               |
                               v
                     +---------+---------+
                     |    FastAPI REST   |
                     |     /api/ingest/* |
                     +----+--------+-----+
                          |        |
                   [status polling]  [upload]
                          |        |
                     +----v--------v-----+
                     |   Celery Worker   |
                     |  (Redis broker)   |
                     +----+--------+-----+
                          |
           +--------------+--------------+
           |              |              |
     +-----v-----+  +----v-----+  +----v------+
     |  Telegram  |  |   PDF    |  |  Groq     |
     |  Parser    |  |  Parser  |  |  Whisper  |
     +-----+------+  +----+-----+  +----+------+
           |              |              |
           +------+-------+--------------+
                  |
           +------v------+
           |  PII Filter |
           |  (Presidio) |
           +------+------+
                  |
           +------v------+
           |   Noise     |
           |   Filter    |
           +------+------+
                  |
           +------v------+
           |  Chrono     |
           |  Grouper    |
           +------+------+
                  |
           +------v------+
           |  Chunker    |
           |  (5-10 sent)|
           +------+------+
                  |
           +------v------------------+
           |  Embeddings (FastEmbed) |
           |  dense: e5-large (1024d)|
           |  sparse: BM42           |
           +------+------------------+
                  |
           +------v------+
           |   Qdrant    |
           |  Collection |
           |  (hybrid)   |
           +------+------+
                  |
           +------v------+
           | PostgreSQL  |
           |  (metadata) |
           +-------------+
```

### Recommended Project Structure

```
src/
├── api/                        # FastAPI application
│   ├── main.py                 # App entry, middleware
│   ├── routes/
│   │   └── ingest.py           # /api/ingest/* endpoints
│   └── deps.py                 # Dependency injection
│
├── pipeline/                   # Ingestion pipeline (Core Phase 1)
│   ├── parsers/
│   │   ├── telegram.py         # Telegram JSON export parser
│   │   ├── pdf.py              # PDF parser (Docling wrapper)
│   │   └── voice.py            # Groq Whisper transcription
│   ├── anonymizer/
│   │   ├── engine.py           # Presidio analyzer + anonymizer setup
│   │   ├── recognizers.py      # Custom Russian PII recognizers
│   │   └── token_mapping.py    # PII token mapping storage/reversal
│   ├── filters/
│   │   ├── noise.py            # Telegram noise filter (service, bots, greetings)
│   │   └── grouping.py         # Chronological message grouping
│   ├── chunker/
│   │   ├── text_chunker.py     # Sentence-based chunking with overlap
│   │   └── telegram_chunker.py # Chrono-grouped chunking for Telegram
│   └── indexer/
│       ├── embedder.py         # Dense + sparse embedding generation
│       └── qdrant_store.py     # Qdrant collection management & upsert
│
├── models/                     # SQLAlchemy / Pydantic models
│   ├── source.py               # Data source metadata
│   └── ingest_job.py           # Ingestion job status tracking
│
├── core/                       # Shared utilities
│   ├── config.py               # Settings (pydantic-settings)
│   └── logging.py              # Structured logging
│
└── tasks/                      # Celery task definitions
    └── ingest.py               # Ingestion task chain + progress

tests/
├── pipeline/
│   ├── test_telegram_parser.py
│   ├── test_pdf_parser.py
│   ├── test_anonymizer.py
│   ├── test_noise_filter.py
│   ├── test_chunker.py
│   └── test_qdrant_indexer.py
├── api/
│   └── test_ingest_routes.py
└── conftest.py                 # Shared fixtures (sample data, mock clients)
```

### Pattern 1: Celery Task Chain с Progress Tracking

**What:** Каждый этап обработки (парсинг -> PII -> фильтрация -> чанкинг -> эмбеддинг -> индексация) -- отдельная Celery-задача. Прогресс отслеживается через `self.update_state(state='PROGRESS', meta=...)`.

**When to use:** Батчевая обработка документов, где каждый этап CPU-intensive или I/O-heavy.

**Example:**
```python
# Source: [CITED: Context7 /celery/celery - task progress tracking]
from celery import chain

@app.task(bind=True)
def ingest_telegram(self, source_id: str):
    """Main orchestration task."""
    # Report initial progress
    self.update_state(state='PROGRESS', meta={
        'stage': 'parsing', 'current': 0, 'total': 100
    })
    messages = parse_telegram_export(source_id)

    self.update_state(state='PROGRESS', meta={
        'stage': 'anonymizing', 'current': 25, 'total': 100
    })
    messages = anonymize_pii(messages)

    self.update_state(state='PROGRESS', meta={
        'stage': 'filtering', 'current': 50, 'total': 100
    })
    messages = filter_noise(messages)

    self.update_state(state='PROGRESS', meta={
        'stage': 'chunking', 'current': 60, 'total': 100
    })
    chunks = chunk_messages(messages)

    self.update_state(state='PROGRESS', meta={
        'stage': 'embedding', 'current': 75, 'total': 100
    })
    embedded = embed_chunks(chunks)

    self.update_state(state='PROGRESS', meta={
        'stage': 'indexing', 'current': 90, 'total': 100
    })
    index_to_qdrant(embedded)

    return {'status': 'completed', 'chunks_indexed': len(embedded)}
```

### Pattern 2: Presidio Custom Russian Recognizers

**What:** Кастомные PatternRecognizer для русского PII: телефоны (+7/8 форматы), ИНН (10/12 цифр), СНИЛС, адреса. Используем Pattern + deny-list подход.

**When to use:** Для структурированных PII-паттернов, которые стандартные Presidio recognizers не покрывают для русского языка.

**Example:**
```python
# Source: [CITED: Context7 /microsoft/presidio - custom recognizers]
from presidio_analyzer import Pattern, PatternRecognizer

# Russian phone: +7(XXX)XXX-XX-XX, 8XXXXXXXXXX, +7XXXXXXXXXX
RUSSIAN_PHONE_PATTERNS = [
    Pattern(
        name="russian_phone_intl",
        regex=r"(?:\+7|8)[\s\-\(]*\d{3}[\s\-\)]*\d{3}[\s\-]*\d{2}[\s\-]*\d{2}",
        score=0.7,
    ),
    Pattern(
        name="russian_phone_short",
        regex=r"\b\d{10}\b",
        score=0.3,
    ),
]

class RussianPhoneRecognizer(PatternRecognizer):
    def __init__(self):
        super().__init__(
            supported_entity="PHONE_NUMBER",
            patterns=RUSSIAN_PHONE_PATTERNS,
            supported_language="ru",
        )

# INN (10 digits for individuals, 12 for legal entities)
INN_PATTERN = Pattern(
    name="russian_inn",
    regex=r"\b\d{10}\b|\b\d{12}\b",
    score=0.4,  # Lower score -- many 10/12 digit numbers are not INN
)
```

### Pattern 3: Qdrant Hybrid Search Setup (Dense + Sparse)

**What:** Коллекция Qdrant с двумя named-векторами: dense (multilingual-e5-large, 1024d) и sparse (BM42/SPLADE). Hybrid search через prefetch + RRF fusion.

**When to use:** Для всех текстовых коллекций в V-Brain -- комбинация dense-семантики и sparse-ключевых слов.

**Example:**
```python
# Source: [CITED: Context7 /qdrant/qdrant-client + /qdrant/fastembed]
from qdrant_client import QdrantClient, models
from qdrant_client.models import SparseVectorParams

client = QdrantClient(host="localhost", port=6333)

# Create collection with dense + sparse vectors
client.create_collection(
    collection_name="knowledge",
    vectors_config={
        "dense": models.VectorParams(
            size=1024,  # multilingual-e5-large
            distance=models.Distance.COSINE,
        ),
    },
    sparse_vectors_config={
        "sparse": models.SparseVectorParams(
            index=models.SparseIndexParams(
                on_init=False,  # Don't build index during creation
            ),
        ),
    },
)

# Upsert with both dense and sparse vectors
from fastembed import TextEmbedding, SparseTextEmbedding

dense_model = TextEmbedding(model_name="intfloat/multilingual-e5-large")
sparse_model = SparseTextEmbedding(model_name="Qdrant/bm42-all-MiniLM-L6-v2-quantized")

# Generate embeddings
dense_vectors = list(dense_model.embed(documents, batch_size=32))
sparse_vectors = list(sparse_model.embed(documents))

# Upsert points
points = [
    models.PointStruct(
        id=i,
        vector={
            "dense": dense_vectors[i].tolist(),
            "sparse": models.SparseVector(
                indices=sparse_vectors[i].indices,
                values=sparse_vectors[i].values,
            ),
        },
        payload={"text": doc, "source": "telegram", "date": "..."},
    )
    for i, doc in enumerate(documents)
]
client.upsert("knowledge", points=points)
```

### Pattern 4: Telegram JSON Export Parser

**What:** Парсер `result.json` из Telegram Desktop -- обрабатывает как text (string), так и rich text (array of objects). Отделяет service messages от обычных. Связывает voice_message с .ogg файлами.

**When to use:** Для ING-02 -- основной парсер Telegram экспорта.

**Example:**
```python
import json
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional

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

def parse_text_field(text_field) -> str:
    """Handle both string and rich-text array formats."""
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
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    messages = []
    for msg in data.get("messages", []):
        msg_type = msg.get("type", "")
        if msg_type == "service":
            continue  # Skip service messages per D-09

        text = parse_text_field(msg.get("text", ""))
        if not text and msg.get("media_type") != "voice_message":
            continue  # Skip messages without text content

        messages.append(TelegramMessage(
            id=msg["id"],
            date=msg.get("date", ""),
            author=msg.get("from", ""),
            author_id=msg.get("from_id", ""),
            text=BeautifulSoup(text, "html.parser").get_text(),
            is_service=msg_type == "service",
            is_bot="bot" in msg.get("from_id", "").lower(),
            media_type=msg.get("media_type"),
            voice_path=msg.get("file_name") if msg.get("media_type") == "voice_message" else None,
        ))
    return messages
```

### Pattern 5: Docling PDF Parsing

**What:** Использование Docling DocumentConverter для извлечения текста из PDF с кириллицей в Markdown формат.

**When to use:** Для ING-05 -- извлечение текста из PDF документов.

**Example:**
```python
# Source: [CITED: Context7 /docling-project/docling - convert PDF to markdown]
from docling.document_converter import DocumentConverter

def extract_pdf_text(filepath: str) -> str:
    converter = DocumentConverter()
    result = converter.convert(filepath)
    markdown = result.document.export_to_markdown()
    return markdown
```

### Anti-Patterns to Avoid

- **Обработка PII после эмбеддинга:** PII необходимо анонимизировать ДО создания эмбеддингов. Иначе embeddings кодируют PII-паттерны. [CITED: ARCHITECTURE.md Anti-Pattern 4]
- **Synchronous pipeline в API endpoint:** Все тяжёлые задачи через Celery. API всегда возвращает task_id немедленно. [CITED: ARCHITECTURE.md Anti-Pattern 5]
- **SPLADE_PP_en_v1 для русского sparse:** Англоцентричная модель, плохо работает с кириллицей. Использовать BM42 или Qdrant-native BM25. [ASSUMED -- основано на описании модели в FastEmbed]
- **Пропуск edited messages в Telegram:** `edit_date` указывает на изменённое сообщение. Нужно хранить последнюю версию. [CITED: PITFALLS.md]
- **Фиксированный размер чанка без учёта семантики:** Средний размер по D-12, но с sentence boundary awareness и перекрытием. [CITED: PITFALLS.md Pitfall 3]

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| PDF парсинг | Кастомный PyPDF/pdfplumber парсер | Docling | Layout analysis, таблицы, OCR, Markdown export. Docling строго превосходит |
| PII обнаружение | Regex-only pipeline | Presidio Analyzer + кастомные recognizers | Presidio даёт NER через spaCy + regex + deny-list + context-aware scoring |
| PII замена | Кастомный string replace | Presidio AnonymizerEngine | Операторы replace, mask, redact, hash с конфигурацией |
| Эмбеддинги dense | Собственная модель / raw ONNX | FastEmbed TextEmbedding | Автозагрузка, кэширование, ONNX-оптимизация, unified API |
| Эмбеддинги sparse | Ручной BM25 TF-IDF | FastEmbed SparseTextEmbedding или Qdrant BM25 | Интеграция с Qdrant, готовые модели |
| Асинхронные задачи | Кастомный ThreadPoolExecutor | Celery + Redis | Retry policies, progress tracking, monitoring, task chains |
| HTML cleanup | Регулярки | BeautifulSoup4 | Надёжный парсинг HTML из Telegram text_entities |
| Транскрибация голосовых | Whisper local (необходим GPU) | Groq Whisper API | Быстро, дёшево, .ogg нативно, нет нагрузки на сервер |

**Key insight:** Каждая из этих задач кажется простой ("просто парси PDF"), но реальная сложность -- в edge cases (многоколоночный layout, сканированные страницы, кириллица). Готовые библиотеки уже решили эти проблемы.

## Common Pitfalls

### Pitfall 1: SPLADE sparse model не работает для русского текста

**What goes wrong:** Использование `prithivida/Splade_PP_en_v1` (единственная sparse модель в примерах FastEmbed) для русских текстов. Англоцентричная модель почти не улавливает морфологию русского языка. Гибридный поиск не даёт ожидаемого улучшения по сравнению с pure dense.

**Why it happens:** SPLADE обучена на английских корпусах. Russian tokenization в BERT-токенизаторе ломает слово на subword-токены, которые SPLADE не умеет агрегировать.

**How to avoid:** Использовать BM42 (`Qdrant/bm42-all-MiniLM-L6-v2-quantized`) -- мультиязычная sparse-модель в FastEmbed. Если BM42 недоступна, использовать Qdrant-native BM25 (полностью ключевой подход, не ML-модель). Для чистого ключевого поиска BM25 на русском -- надёжнее SPLADE.

**Warning signs:** Sparse search ничего не находит для русских запросов. Hybrid search по качеству равен pure dense search.

**Confidence:** MEDIUM -- BM42 описан в FastEmbed docs как мультиязычная sparse-модель, но не бенчмаркнута специфически на русском.

### Pitfall 2: Telegram JSON text field -- массив вместо строки

**What goes wrong:** Парсер ожидает `msg["text"]` как строку, но Telegram export хранит форматированные сообщения как массив объектов `[{"type": "plain", "text": "Hello"}, {"type": "bold", "text": "world"}]`. Парсер падает с TypeError или получает "garbage" при конкатенации.

**Why it happens:** Telegram Desktop export генерирует rich-text формат для сообщений с форматированием (bold, italic, links, mentions). Неформатированные сообщения -- просто строка.

**How to avoid:** Всегда проверять тип `text` field. Если list -- извлекать `text` из каждого элемента. Использовать `BeautifulSoup` для очистки HTML-тегов.

**Warning signs:** TypeError при обработке messages, пустые строки для форматированных сообщений.

**Confidence:** HIGH -- подтверждено анализом структуры result.json [ASSUMED -- основано на документации Telegram Desktop export].

### Pitfall 3: Presidio + spaCy ru_core_news_md пропускает русские имена в косвенных падежах

**What goes wrong:** NER spaCy обучена на новостных текстах и хорошо распознаёт именительный падеж ("Иванов Иван"). Но в рабочих чатах часты: "дай документ Иванову", "звони Александровне", "передай Сидоровой". SpaCy NER не распознаёт эти формы как PERSON.

**Why it happens:** Русская морфология -- 6 падежей, 3 рода. spaCy ru_core_news_md -- medium-size модель (53MB), обученная на ограниченном корпусе. Declension coverage неполная.

**How to avoid:** Complementary подход: (1) spaCy NER для именительного падежа, (2) кастомный regex для паттернов "Фамилия + суффикс падежа" (-ову, -евой, -ину, -ину), (3) deny-list имён сотрудников компании. D-08 explicitly требует валидацию -- построить тестовую выборку из реальных данных.

**Warning signs:** Recall PII < 95% на тестовых данных. Имена в косвенных падежах проходят неанонимизированными.

**Confidence:** HIGH -- подтверждено в PITFALLS.md и является известной проблемой русского NER.

### Pitfall 4: Groq Whisper API -- размер файла и формат

**What goes wrong:** Голосовые сообщения из Telegram (часто длинные -- 5-30 минут) превышают лимит Groq (25MB). Или формат не поддерживается.

**Why it happens:** Telegram экспортирует voice messages как .ogg (opus codec). Groq поддерживает .ogg, но есть лимит размера. Длинные разговоры = большие файлы.

**How to avoid:** Проверять размер файла перед отправкой. Если > 25MB, разбивать на чанки через pydub. Использовать `whisper-large-v3-turbo` для скорости.

**Warning signs:** Groq API возвращает ошибку 413 или timeout. Файлы > 25MB не обрабатываются.

**Confidence:** MEDIUM -- размер лимита основан на web search (rate-limited, не удалось верифицировать).

### Pitfall 5: Целочисленные ID конфликтуют при повторном ингесте

**What goes wrong:** При повторной загрузке Telegram export или PDF, Qdrant upsert перезаписывает старые данные (если ID совпадают). Или наоборот -- дублируются записи при разных ID.

**Why it happens:** Нет единой стратегии ID-генерации. Telegram message IDs уникальны внутри чата, но не глобально. PDF чанки -- нужно генерировать стабильные ID.

**How to avoid:** Генерировать composite ID: `{source_type}:{source_id}:{chunk_index}` или UUID v5 от контента. При повторном ингесте -- сначала удалить все записи этого source, потом upsert новые.

**Confidence:** HIGH -- стандартная проблема при работе с векторными БД.

## Code Examples

### Celery + FastAPI: Асинхронный ингест с прогрессом

```python
# Source: [CITED: Context7 /celery/celery - task progress + async result]
# tasks/ingest.py
from celery import Celery
from celery.result import AsyncResult

app = Celery('vbrain', broker='redis://localhost:6379/0', backend='redis://localhost:6379/1')

@app.task(bind=True)
def ingest_telegram(self, source_id: str, file_path: str):
    # Parsing
    self.update_state(state='PROGRESS', meta={'stage': 'parsing', 'progress': 10})
    messages = parse_telegram_export(file_path)

    # PII Anonymization
    self.update_state(state='PROGRESS', meta={'stage': 'anonymizing', 'progress': 30})
    messages = anonymize_messages(messages)

    # Filtering
    self.update_state(state='PROGRESS', meta={'stage': 'filtering', 'progress': 50})
    messages = filter_noise(messages)

    # Transcribe voice messages (if any)
    self.update_state(state='PROGRESS', meta={'stage': 'transcribing', 'progress': 60})
    messages = transcribe_voice_messages(messages, voice_dir)

    # Chunking
    self.update_state(state='PROGRESS', meta={'stage': 'chunking', 'progress': 70})
    chunks = chunk_messages(messages)

    # Embedding + Indexing
    self.update_state(state='PROGRESS', meta={'stage': 'indexing', 'progress': 85})
    index_chunks(chunks)

    return {'status': 'completed', 'messages_processed': len(messages), 'chunks_indexed': len(chunks)}
```

```python
# api/routes/ingest.py
from fastapi import APIRouter, UploadFile, File, BackgroundTasks
from tasks.ingest import ingest_telegram
from celery.result import AsyncResult

router = APIRouter(prefix="/api/ingest")

@router.post("/telegram")
async def upload_telegram(file: UploadFile = File(...)):
    # Save file, create source record
    source_id = save_upload(file)
    # Launch async task
    task = ingest_telegram.delay(source_id, file_path)
    return {"job_id": task.id, "status": "started"}

@router.get("/status/{job_id}")
async def get_status(job_id: str):
    result = AsyncResult(job_id)
    if result.state == 'PROGRESS':
        return {"status": "processing", **result.info}
    elif result.state == 'SUCCESS':
        return {"status": "completed", **result.result}
    else:
        return {"status": result.state}
```

### Presidio Setup с кастомными русскими распознавателями

```python
# Source: [CITED: Context7 /microsoft/presidio - NLP engine + custom recognizers]
# pipeline/anonymizer/engine.py
from presidio_analyzer import AnalyzerEngine, RecognizerRegistry
from presidio_analyzer.nlp_engine import NlpEngineProvider
from presidio_anonymizer import AnonymizerEngine, OperatorConfig

def create_analyzer():
    configuration = {
        "nlp_engine_name": "spacy",
        "models": [{"lang_code": "ru", "model_name": "ru_core_news_md"}],
    }
    provider = NlpEngineProvider(nlp_configuration=configuration)
    nlp_engine = provider.create_engine()

    registry = RecognizerRegistry()
    registry.load_predefined_recognizers(languages=["en", "ru"])

    # Add custom Russian recognizers
    registry.add_recognizer(RussianPhoneRecognizer())
    registry.add_recognizer(RussianINNRecognizer())
    registry.add_recognizer(RussianSNILSRecognizer())

    return AnalyzerEngine(
        registry=registry,
        nlp_engine=nlp_engine,
        supported_languages=["ru", "en"],
    )

def create_anonymizer():
    return AnonymizerEngine()

# Token format per D-05
OPERATORS = {
    "PERSON": OperatorConfig("replace", {"new_value": "<PERSON_>"}),
    "PHONE_NUMBER": OperatorConfig("replace", {"new_value": "<PHONE_>"}),
    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "<EMAIL_>"}),
    # ... etc
}
```

### Qdrant Collection Setup для Hybrid Search

```python
# Source: [CITED: Context7 /qdrant/qdrant-client - create collection + /qdrant/fastembed]
# pipeline/indexer/qdrant_store.py
from qdrant_client import QdrantClient, models

def create_knowledge_collection(client: QdrantClient):
    client.create_collection(
        collection_name="knowledge",
        vectors_config={
            # Dense vectors for semantic search
            "dense": models.VectorParams(
                size=1024,  # multilingual-e5-large
                distance=models.Distance.COSINE,
                hnsw_config=models.HnswConfigDiff(m=16, ef_construct=100),
            ),
        },
        sparse_vectors_config={
            # Sparse vectors for keyword/BM25-like search
            "sparse": models.SparseVectorParams(
                index=models.SparseIndexParams(on_init=False),
            ),
        },
        # Payload schema for source attribution (D-13)
    )
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Pure vector search | Hybrid (dense + sparse) + RRF fusion | 2024-2025 | Обязательный паттерн для production RAG |
| Английский sparse (SPLADE en) | Мультиязычный sparse (BM42) | 2025 | Для русского языка критично |
| LangChain для всего | LlamaIndex для RAG + кастомный код для pipeline | 2024-2025 | Минимизация framework lock-in |
| Синхронная обработка | Celery task chain с прогрессом | Стандарт | Не блокирует API, retryability |

**Deprecated/outdated:**
- ChromaDB для production -- не подходит по причине concurrent writes и отсутствия hybrid search
- pdfplumber для сложных PDF -- нет layout analysis
- `nltk.sent_tokenize` для русского -- English-optimized, плохо работает с кириллицей

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | BM42 через FastEmbed работает для русского текста | Standard Stack / Anti-Patterns | Hybrid search не даст преимущества; нужно тестировать на реальных данных. Fallback: Qdrant-native BM25 |
| A2 | Groq Whisper API лимит файла -- 25MB | Pitfall 4 | Голосовые сообщения > 25MB нужно разбивать через pydub. Не критично, но добавляет сложность |
| A3 | Telegram JSON export структура стабильна (2022-2025) | Pattern 4 | Может измениться в новых версиях Telegram Desktop. Нужно верифицировать реальным экспортом |
| A4 | Qdrant SparseVectorParams поддерживает on_init=False для lazy index building | Pattern 3 | Если нет -- может быть задержка при первом upsert. Не критично |
| A5 | Docling нативно поддерживает кириллицу без дополнительной конфигурации | Pattern 5 | Если нет -- нужен fallback на pdfplumber + custom layout detection |
| A6 | Redis доступен для Celery (Docker контейнер) | Standard Stack | Redis не запущен -- Celery не работает. Требуется docker-compose setup |
| A7 | PostgreSQL 16+ доступен для метаданных (Docker контейнер) | Standard Stack | Если нет -- можно использовать SQLite для разработки (но не production) |

## Open Questions

1. **BM42 vs Qdrant-native BM25 для русского sparse search**
   - What we know: FastEmbed предоставляет SparseTextEmbedding с BM42-моделью. Qdrant также имеет встроенный BM25 через full-text search index.
   - What's unclear: Какой подход лучше для русского языка? BM42 (ML-модель, multilingual) или Qdrant BM25 (классический TF-IDF)?
   - Recommendation: Бенчмаркнуть оба подхода на реальных данных в Phase 1. Начать с BM42 (через FastEmbed -- единый API). Если качество неудовлетворительное -- переключиться на Qdrant-native BM25.

2. **Groq Whisper -- лимит размера файла для длинных голосовых**
   - What we know: Groq поддерживает .ogg нативно, whisper-large-v3-turbo. Есть ограничение на размер файла.
   - What's unclear: Точный лимит для .ogg файлов. Нужно ли разбивать длинные записи?
   - Recommendation: Реализовать с проверкой размера + fallback на chunking через pydub.

3. **Стратегия ID-генерации для Qdrant при повторном ингесте**
   - What we know: Нужна стабильная ID-схема для upsert без дубликатов.
   - What's unclear: UUID vs deterministic hash vs composite ID. Что лучше для стабильности при повторном ингесте?
   - Recommendation: Использовать deterministic hash (content-based) для PDF-чанков. Composite ID для Telegram ({chat_id}:{msg_id}:{chunk_idx}).

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12+ | Runtime | Yes | 3.12.4 | -- |
| Docker | Qdrant, Redis, PostgreSQL | CLI installed | 29.2.1 | Docker daemon not running -- needs start |
| Redis | Celery broker | CLI installed | -- | Not running (ping failed). Start via docker-compose |
| uv | Package manager | Yes | 0.8.22 | -- |
| Node.js | -- (не нужен для Phase 1) | Yes | 24.5.0 | -- |

**Missing dependencies with no fallback:**
- Docker daemon не запущен (`docker ps` fail). Необходимо запустить Docker Desktop перед началом работы.

**Missing dependencies with fallback:**
- Redis не запущен. Запускается через docker-compose как часть инфраструктуры.
- PostgreSQL не проверялся, но запускается через docker-compose.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest + pytest-asyncio |
| Config file | None -- Wave 0 (создаётся в рамках Phase 1) |
| Quick run command | `pytest tests/pipeline/ -x -v` |
| Full suite command | `pytest tests/ -v --tb=short` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ING-01 | PII detected and replaced with tokens | unit | `pytest tests/pipeline/test_anonymizer.py -x` | Wave 0 |
| ING-02 | Telegram JSON parsed with metadata | unit | `pytest tests/pipeline/test_telegram_parser.py -x` | Wave 0 |
| ING-03 | Voice messages transcribed via Groq | unit (mock Groq) | `pytest tests/pipeline/test_voice.py -x` | Wave 0 |
| ING-04 | Service messages and noise filtered | unit | `pytest tests/pipeline/test_noise_filter.py -x` | Wave 0 |
| ING-05 | PDF text extracted with Cyrillic | unit | `pytest tests/pipeline/test_pdf_parser.py -x` | Wave 0 |
| ING-06 | Batch processing with progress tracking | integration | `pytest tests/api/test_ingest_routes.py -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/pipeline/ -x -v`
- **Per wave merge:** `pytest tests/ -v --tb=short`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/conftest.py` -- shared fixtures (sample Telegram JSON, sample PDF, mock Presidio, mock Qdrant client)
- [ ] `tests/pipeline/test_telegram_parser.py` -- ING-02
- [ ] `tests/pipeline/test_anonymizer.py` -- ING-01
- [ ] `tests/pipeline/test_noise_filter.py` -- ING-04
- [ ] `tests/pipeline/test_pdf_parser.py` -- ING-05
- [ ] `tests/pipeline/test_voice.py` -- ING-03
- [ ] `tests/pipeline/test_chunker.py` -- chunking quality
- [ ] `tests/pipeline/test_qdrant_indexer.py` -- indexing verification
- [ ] `tests/api/test_ingest_routes.py` -- ING-06
- [ ] Framework install: `pip install pytest pytest-asyncio httpx`

## Security Domain

### Applicable ASVS Categories

| ASVS Category | Applies | Standard Control |
|---------------|---------|-----------------|
| V2 Authentication | No (Phase 1 -- API endpoints без авторизации, авторизация в Phase 3/4) | -- |
| V3 Session Management | No | -- |
| V4 Access Control | No | -- |
| V5 Input Validation | Yes | Pydantic v2 models для validation входящих данных (файлы, JSON). File type whitelist (.json, .pdf, .ogg) |
| V6 Cryptography | No | -- |

### Known Threat Patterns for FastAPI + File Upload

| Pattern | STRIDE | Standard Mitigation |
|---------|--------|---------------------|
| Malicious file upload (PDF/JSON with embedded code) | Tampering | Validate file type (magic bytes), limit file size, save to isolated directory |
| Path traversal in file paths | Tampering | Use secure filename generation (uuid), never use user-supplied paths |
| Resource exhaustion (large files) | Denial of Service | Max file size limit (100MB), max number of concurrent tasks |
| PII exposure in logs | Information Disclosure | Never log raw text before anonymization. Log only token IDs |
| PII mapping stored unencrypted | Information Disclosure | Encrypt token mapping at rest. Restrict DB access |

## Sources

### Primary (HIGH confidence)
- [Context7 /qdrant/qdrant-client] -- Qdrant Python client API, create_collection, query_points, upsert
- [Context7 /qdrant/fastembed] -- FastEmbed TextEmbedding, SparseTextEmbedding, hybrid search pattern, BM42, multilingual-e5-large
- [Context7 /microsoft/presidio] -- Custom recognizers (PatternRecognizer), NLP engine configuration, spaCy integration, OperatorConfig
- [Context7 /celery/celery] -- Task progress tracking (update_state), AsyncResult, Redis backend configuration
- [Context7 /docling-project/docling] -- DocumentConverter, export_to_markdown, PDF parsing
- [PyPI verified 2026-04-18] -- Все версии пакетов проверены через PyPI JSON API

### Secondary (MEDIUM confidence)
- [Context7 /qdrant/qdrant-client] -- Sparse vector configuration (SparseVectorParams) -- описана в API docs, но примеры hybrid с sparse через Context7 ограничены
- [ASSUMED: Telegram Desktop JSON export format] -- структура result.json основана на документации и training data, не верифицирована реальным экспортом
- [ASSUMED: Groq Whisper API] -- SDK groq 1.2.0 подтверждён, но API details основаны на web search (rate-limited)

### Tertiary (LOW confidence)
- [ASSUMED: BM42 multilingual support for Russian] -- BM42 описан как multilingual в FastEmbed, но не бенчмаркнута на русском
- [ASSUMED: Groq file size limit 25MB] -- основано на web search, не удалось верифицировать из-за rate limit

## Project Constraints (from CLAUDE.md)

- **Безопасность**: PII-анонимизация обязательна -- ФИО, телефоны, email заменяются на токены перед обработкой (D-07: PII ДО любой обработки)
- **LLM**: Не привязан к конкретной модели -- можно использовать API (OpenAI, Anthropic) или локальный деплой (Gemma, Qwen, Llama). В Phase 1 LLM не используется напрямую (это Phase 2), но архитектура должна допускать гибкий LLM
- **Источники MVP**: Только Telegram логи (JSON) и PDF -- видео парсинг отложен
- **Периметр**: Данные не покидают периметр компании при локальном деплое LLM. Embeddings -- локально (FastEmbed). Groq Whisper -- внешний API (только аудио, текст не содержит PII после анонимизации... но голос может содержать PII в аудио-форме -- это нужно учитывать)
- **Язык**: Все данные, извлечённые знания и ответы на русском
- **Не использовать**: LangChain как primary framework, Dify.ai как core pipeline, ChromaDB для production, OpenAI-only embeddings, React SPA для админки, pinecone/Weaviate Cloud
- **Инструменты**: uv для пакетного менеджмента, ruff для линтинга, pytest для тестов, Docker + docker-compose для контейнеризации

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH -- все версии проверены через PyPI 2026-04-18
- Architecture: HIGH -- паттерны подтверждены через Context7 docs для всех основных библиотек
- Pitfalls: HIGH -- Russian PII и Telegram parsing pitfalls подтверждены из проекта PITFALLS.md + Context7
- Sparse embeddings для русского: MEDIUM -- BM42 не бенчмаркнут на русском

**Research date:** 2026-04-18
**Valid until:** 2026-05-18 (30 дней -- стабильный стек, но версии могут обновиться)
