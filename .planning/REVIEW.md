# V-Brain: Code Review Report

**Reviewed:** 2026-04-19  
**Depth:** deep (cross-file, full stack)  
**Files Reviewed:** 67 Python source files + 30 test files  
**Status:** issues_found

---

## Summary

Ревью охватило весь код в `src/` и `tests/`. Архитектура проекта хорошо структурирована: чёткое разделение на pipeline, api, bot, ai слои; Pydantic v2 везде; async/await корректно применён в Telegram-боте и FastAPI. Тем не менее, обнаружены серьёзные проблемы, часть из которых блокирует деплой.

**Ключевые риски:**

1. **CRITICAL:** Admin-пароль хранится и сравнивается как plain SHA-256 без соли — уязвим к rainbow-table атакам.
2. **CRITICAL:** `knowledge/query` endpoint не защищён аутентификацией — любой может запрашивать из базы знаний компании.
3. **CRITICAL:** Внутри граф-ноды `retrieve_phase2_payload` жёстко прописан `http://localhost:8000` — бот и API должны запускаться на одной машине, это архитектурное ограничение без failsafe.
4. **CRITICAL:** Celery-задачи создают по два экземпляра `Celery("vbrain")` (в `tasks/ingest.py` и `tasks/knowledge.py`) — потенциальные конфликты с брокером и дублирование.
5. **HIGH:** Несохранение изменений `IngestJob.status` в БД при успехе/неудаче celery-задачи — таблица `ingest_jobs` создаётся, но никогда не обновляется из задачи.
6. **HIGH:** `admin_password` в `Settings` ожидает SHA-256 hex строку в `.env`, но это нигде не документировано и не валидируется — пустое значение по умолчанию (`""`) приведёт к 500 при первом же логине.
7. **HIGH:** `format_attribution` создаёт `AttributionItem` с пустым `source_id=""` без проверки — это нарушает контракт `Field(min_length=1)` и вызовет `ValidationError` в рантайме.
8. **HIGH:** `knowledge_writer.py:32` — `unit.source_refs[0]` без проверки длины списка, IndexError если `source_refs` пуст.
9. **HIGH:** Мутация глобального объекта `settings` в обработчиках запросов (`admin.py:460`, `admin.py:481`) — не thread-safe, изменения не персистентны между рестартами.
10. **MEDIUM:** `qdrant_store.py:upsert_chunks` использует строковый `id` (типа `"telegram:uuid:0"`), но Qdrant ожидает `int` или `UUID` — может падать в рантайме с qdrant-client 1.17+.

---

## Critical Issues

### CR-01: Admin-пароль — SHA-256 без соли

**File:** `src/api/routes/admin.py:32-38`  
**Issue:** Функция `_hash_password` использует голый SHA-256 без соли. SHA-256 детерминирован — один и тот же пароль даёт одинаковый хэш. При компрометации `.env` (или утечке базы сессий) атакующий может использовать rainbow tables или GPU-брутфорс. Библиотека `hashlib` сама по себе не подходит для хранения паролей.

```python
# ТЕКУЩИЙ КОД (уязвимый):
def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()
```

**Fix:** Использовать `bcrypt` или `passlib` с bcrypt-бэкендом.

```python
from passlib.context import CryptContext

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def _hash_password(password: str) -> str:
    return _pwd_context.hash(password)

def _verify_password(plain: str, hashed: str) -> bool:
    return _pwd_context.verify(plain, hashed)
```

При этом `admin_password` в `.env` нужно хранить уже как bcrypt-хэш (`$2b$...`), а не SHA-256 hex.

---

### CR-02: `/api/knowledge/query` не защищён аутентификацией

**File:** `src/api/routes/knowledge.py:18-48`  
**Issue:** Эндпоинт `POST /api/knowledge/query` открыт публично — никакой аутентификации нет. `AdminAuthMiddleware` защищает только `/api/admin/*`. Любой, у кого есть доступ к сети, может извлекать корпоративные знания через этот API без авторизации. Особенно критично, учитывая что система хранит внутренние инструкции и деанонимизированные бизнес-процессы.

**Fix:** Добавить dependency-инъекцию для проверки аутентификации на этот роутер, либо хотя бы ограничить доступ к `/api/knowledge/*` только из `localhost` или с токен-аутентификацией.

```python
# Вариант 1 — API-ключ через заголовок:
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header(...)):
    if x_api_key != settings.internal_api_key:
        raise HTTPException(status_code=401)

@router.post("/query", dependencies=[Depends(verify_api_key)])
async def query_knowledge(payload: KnowledgeQueryRequest):
    ...
```

---

### CR-03: Hardcoded `localhost:8000` в retrieve-ноде

**File:** `src/ai/langgraph/nodes/retrieve_phase2.py:23-26`  
**Issue:** URL сервиса жёстко прописан как `http://localhost:8000`. Это означает:
1. Бот и API **обязаны** запускаться на одной машине — нет возможности деплоить их раздельно.
2. При недоступности локального сервиса (`ConnectionRefusedError`) ошибка перехватывается выше и пользователь получает тихий fallback, не зная о системной проблеме.
3. В Docker-окружении `localhost` внутри контейнера не видит соседние сервисы.

```python
# ТЕКУЩИЙ КОД:
local_client = client or httpx.AsyncClient(
    base_url="http://localhost:8000",
    timeout=httpx.Timeout(15.0),
)
```

**Fix:** Вынести URL в конфиг.

```python
# src/core/config.py:
knowledge_api_base_url: str = "http://localhost:8000"

# retrieve_phase2.py:
local_client = client or httpx.AsyncClient(
    base_url=settings.knowledge_api_base_url,
    timeout=httpx.Timeout(15.0),
)
```

---

### CR-04: Два независимых экземпляра `Celery("vbrain")`

**File:** `src/tasks/ingest.py:19`, `src/tasks/knowledge.py:12`  
**Issue:** Оба модуля создают `celery_app = Celery("vbrain", broker=..., backend=...)` независимо. Задачи регистрируются на разных app-объектах. При запуске воркера через `celery -A src.tasks.ingest worker` задача `extract_knowledge_task` может не найтись (зарегистрирована в другом app). Также при изменении конфига Redis необходимо менять в двух местах.

**Fix:** Создать единый Celery-экземпляр в отдельном модуле.

```python
# src/tasks/celery_app.py:
from celery import Celery
from src.core.config import settings

celery_app = Celery("vbrain", broker=settings.redis_url, backend=settings.redis_url)

# В ingest.py и knowledge.py:
from src.tasks.celery_app import celery_app

@celery_app.task(...)
def ingest_telegram(...): ...
```

---

## High Issues

### HR-01: `IngestJob.status` никогда не обновляется задачей

**File:** `src/tasks/ingest.py`, `src/api/routes/admin.py:158-167`  
**Issue:** При создании задачи в БД создаётся `IngestJob` со статусом `PENDING`. Celery-задача никогда не обновляет эту запись в БД — ни при прогрессе, ни при успехе, ни при ошибке. Статус в `ingest_jobs` вечно остаётся `PENDING`. Страница sources в admin-панели не имеет корректных данных о ходе задачи.

**Fix:** Добавить DB-сессию в celery-задачу и обновлять `IngestJob` при смене состояния, либо использовать webhook/callback от Celery после завершения.

---

### HR-02: `format_attribution` создаёт AttributionItem с пустым `source_id`

**File:** `src/ai/rag/attribution.py:13`  
**Issue:** `metadata.get("source_id", "")` может вернуть пустую строку. `AttributionItem.source_id` имеет ограничение `Field(min_length=1)` — при пустом `source_id` конструктор кидает `ValidationError`. Это приведёт к исключению в `synthesize_answer` → непредсказуемый ответ пользователю.

```python
# УЯЗВИМАЯ СТРОКА:
source_id=metadata.get("source_id", ""),  # может быть ""
```

**Fix:**

```python
source_id=metadata.get("source_id") or "unknown",
excerpt=node.get("text", "")[:240] or "Фрагмент не извлечён",
```

---

### HR-03: `index_knowledge_units` — IndexError при пустом `source_refs`

**File:** `src/pipeline/indexer/knowledge_writer.py:32`  
**Issue:** Строка `ref = unit.source_refs[0]` выполняется без предварительной проверки длины списка. Несмотря на то что схема `KnowledgeUnit` требует `min_length=1` для `source_refs`, данные могут прийти из внешних источников в обход валидации (например, если Celery-задача передаёт уже-сериализованные объекты). IndexError здесь прервёт всю задачу `extract_knowledge_task`.

**Fix:**

```python
if not unit.source_refs:
    continue  # или использовать placeholder
ref = unit.source_refs[0]
```

---

### HR-04: Мутация глобального `settings` в обработчиках запросов

**File:** `src/api/routes/admin.py:460`, `src/api/routes/admin.py:481`  
**Issue:** При добавлении/удалении пользователей через admin-панель код напрямую мутирует `settings.telegram_user_roles`:

```python
settings.telegram_user_roles[user_id] = role   # строка 460
settings.telegram_user_roles.pop(user_id, None) # строка 481
```

Проблемы:
1. **Not thread-safe** — при параллельных запросах (несколько воркеров uvicorn) dict может быть в несогласованном состоянии.
2. **Не персистентно** — после рестарта API изменения теряются (пользователь добавлен в БД, но `settings` перечитывается из `.env`).
3. Бот и API в разных процессах не разделяют `settings` — бот никогда не увидит эти изменения.

**Fix:** Бот должен читать роли пользователей только из БД, а не из `settings`. `telegram_user_roles` в конфиге следует убрать или сделать read-only начальной загрузкой.

---

### HR-05: Отсутствие CSRF-защиты для POST-эндпоинтов admin-панели

**File:** `src/api/routes/admin.py:61-84`, `src/api/routes/admin.py:315-338`  
**Issue:** Форматы POST-запросов (`/api/admin/login`, `/api/admin/knowledge/approve`, `/api/admin/knowledge/reject`, `/api/admin/users`) не имеют CSRF-токенов. Cookie `admin_session` используется с `SameSite=lax`, что частично защищает, но не полностью — `SameSite=lax` не защищает от атак при навигации через GET+redirect с кросс-доменных сайтов в некоторых браузерах. Для production нужен явный CSRF-токен.

**Fix:** Добавить CSRF-middleware или использовать `itsdangerous` для генерации CSRF-токенов в формах.

---

### HR-06: Отсутствие ограничения rate-limit на `/api/admin/login`

**File:** `src/api/routes/admin.py:61-84`  
**Issue:** Эндпоинт `/api/admin/login` не имеет никаких ограничений на количество попыток. Возможна неограниченная брутфорс-атака на пароль администратора.

**Fix:** Добавить `slowapi` или аналог, либо блокировку после N неудачных попыток.

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/login")
@limiter.limit("5/minute")
async def login_submit(request: Request, ...):
    ...
```

---

### HR-07: Qdrant point ID — строка вместо int/UUID

**File:** `src/tasks/ingest.py:76`, `src/tasks/ingest.py:115`, `src/pipeline/indexer/knowledge_writer.py:33`  
**Issue:** Qdrant point ID задаётся как строка: `"telegram:source_id:0"`, `"pdf:source_id:1"`, `"knowledge:ref_id:0"`. Qdrant-client с версии 1.x принимает только `int` или `UUID` в качестве `id`. Строковые ID приведут к `ValidationError` от qdrant-client в рантайме.

```python
chunk["id"] = f"telegram:{source_id}:{i}"  # ← строка, но qdrant ожидает int/UUID
```

**Fix:** Использовать UUID.

```python
import uuid
chunk["id"] = str(uuid.uuid5(uuid.NAMESPACE_DNS, f"telegram:{source_id}:{i}"))
# или детерминированный int:
chunk["id"] = abs(hash(f"telegram:{source_id}:{i}")) % (2**63)
```

---

## Medium Issues

### MD-01: `voice.py` — temp-файлы не удаляются при исключении в `_transcribe_single_file`

**File:** `src/pipeline/parsers/voice.py:67-72`  
**Issue:** Временные файлы удаляются в блоке `finally`, но только для успешно созданных путей. Если `_transcribe_single_file` упадёт с исключением для одного chunk, остальные temp-файлы, созданные в предыдущих итерациях, не будут удалены — цикл прерывается.

```python
for temp_path in temp_paths:
    try:
        texts.append(_transcribe_single_file(client, temp_path))
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)  # удаляет текущий, но при исключении цикл может прерваться
```

Фактически код написан правильно (`finally` в каждой итерации), однако если `os.remove` упадёт, следующие итерации не выполнятся. Безопаснее использовать `contextlib.ExitStack` или `tempfile.TemporaryDirectory`.

---

### MD-02: `grouping.py` — некорректная обработка сообщений без `date`

**File:** `src/pipeline/filters/grouping.py:10`, `src/pipeline/filters/grouping.py:27`  
**Issue:** `_parse_date` вызывает `datetime.fromisoformat(date_str.replace("Z", "+00:00"))`. Если `date_str` пустая строка или `None` (поле `date` в Telegram-экспорте может отсутствовать), функция бросит `ValueError`, что прервёт весь `ingest_telegram`. Парсер `telegram.py:65` устанавливает `date=msg.get("date", "")` — пустая строка вполне возможна для системных сообщений, хотя они фильтруются по `type=="service"`, но не во всех случаях.

**Fix:**

```python
def _parse_date(date_str: str) -> datetime:
    if not date_str:
        return datetime.min.replace(tzinfo=timezone.utc)
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        return datetime.min.replace(tzinfo=timezone.utc)
```

---

### MD-03: `_admin_sessions` — in-memory словарь без защиты от утечки памяти

**File:** `src/api/routes/admin.py:29`, `src/api/routes/admin.py:40-53`  
**Issue:** `_admin_sessions: dict[str, dict] = {}` — истёкшие сессии удаляются только при следующем запросе от того же пользователя. Если атакующий создаёт множество сессий (многократный login без logout), dict будет расти неограниченно. Также при нескольких воркерах uvicorn каждый воркер имеет свой `_admin_sessions` — сессия, созданная на воркере 1, не будет видна воркеру 2, что приводит к случайным logout-ам.

**Fix:** Хранить сессии в Redis (уже используется как брокер).

---

### MD-04: `knowledge_page` — SQL LIKE-инъекция через параметр `topic`

**File:** `src/api/routes/admin.py:282`  
**Issue:** `query = query.filter(KnowledgeItem.topic.contains(topic))` — метод `.contains()` у SQLAlchemy экранирует спецсимволы SQL, но **не** экранирует символы `%` и `_` для LIKE-паттерна. Если `topic` содержит `%`, запрос вернёт все записи. Это не SQL-инъекция в полном смысле (данные не утекут), но может привести к неожиданному поведению и повышенной нагрузке на БД.

**Fix:** Использовать `ilike` с экранированием или `==` для точного совпадения:

```python
if topic:
    query = query.filter(KnowledgeItem.topic == topic)
# или с LIKE и явным escape:
    query = query.filter(KnowledgeItem.topic.ilike(f"%{topic.replace('%', r'\%').replace('_', r'\_')}%", escape="\\"))
```

---

### MD-05: `telegram.py` — путь к voice-файлу из данных пользователя без санитизации

**File:** `src/pipeline/parsers/telegram.py:71`  
**Issue:** `voice_path=msg.get("file_name")` — путь к файлу берётся напрямую из JSON-экспорта Telegram, который является пользовательскими данными. Далее в `voice.py:83` строится `full_path = os.path.join(voice_dir, message.voice_path)`. Если `file_name` содержит `../` (path traversal), произойдёт выход за пределы `voice_dir`.

**Fix:**

```python
# В voice.py:
from pathlib import Path

voice_dir_path = Path(voice_dir).resolve()
full_path = (voice_dir_path / Path(message.voice_path).name).resolve()
if not str(full_path).startswith(str(voice_dir_path)):
    logger.warning("Path traversal attempt: %s", message.voice_path)
    continue
```

---

### MD-06: `synthesizer.py` — ответ пользователю содержит сырой текст чанка, а не LLM-ответ

**File:** `src/ai/rag/synthesizer.py:26`  
**Issue:** `grounded_text = reranked[0].get("text", "")` — в качестве ответа пользователю возвращается дословный текст первого ретривед-чанка. Это не генерированный LLM-ответ, а сырой кусок текста из базы. Функционально это может быть намеренным (MVP grounding-only подход), но:
1. Пользователь видит сырой контент из документов компании — возможно, с PII-токенами типа `<PERSON_1>`.
2. Это нарушает принципы RAG (Retrieve-Augment-**Generate**) — нет шага генерации.
3. `compose_grounded_answer` в `answer.py` только форматирует ответ из `rag_payload["answer"]` — которое равно тексту первого чанка.

**Fix:** Добавить LLM-синтез на основе retrieved chunks — это ключевая функциональность системы.

---

### MD-07: Дублирующийся класс `SourceRef` в двух модулях

**File:** `src/ai/extraction/schemas.py:6-16` и `src/ai/langgraph/state.py:12-24`  
**Issue:** `SourceRef` определён дважды с практически идентичными полями. Это нарушает DRY, создаёт риск рассинхронизации контрактов и требует двойного поддержания. Оба класса имеют `model_validator` с одинаковой логикой.

**Fix:** Оставить одно определение в `src/ai/extraction/schemas.py` и импортировать его везде.

---

### MD-08: `deps.py` — синхронный движок SQLAlchemy, но FastAPI асинхронный

**File:** `src/api/deps.py:4-10`  
**Issue:** Используется синхронный `create_engine` и `Session` (psycopg2-based), тогда как FastAPI нативно async. Хотя FastAPI умеет работать с синхронными зависимостями, блокирующие вызовы БД в async-эндпоинтах (`async def admin_index`) будут блокировать event loop, снижая throughput под нагрузкой.

**Fix:** Перейти на `AsyncSession` с `asyncpg`.

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

engine = create_async_engine(settings.database_url.replace("psycopg2", "asyncpg"))
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
```

---

### MD-09: `ingest_telegram` — утечка файла при падении после записи, до commit

**File:** `src/api/routes/admin.py:205-215`, `src/api/routes/ingest.py:50-68`  
**Issue:** Файл записывается на диск (`json_path.write_bytes(json_content)`) до `db.commit()`. Если commit упадёт (исключение БД), файл на диске останется, но запись в `sources` не будет создана. Файл станет orphaned — займёт место, но никогда не будет обработан или удалён.

**Fix:** Обернуть запись файла и commit в транзакцию с cleanup при ошибке.

```python
try:
    json_path.write_bytes(json_content)
    db.add(source)
    db.commit()
except Exception:
    json_path.unlink(missing_ok=True)
    raise
```

---

### MD-10: `datetime.utcnow()` — deprecated в Python 3.12

**File:** `src/models/knowledge_item.py:27-28`, `src/models/source.py:33-34`, `src/models/feedback_event.py:19`, `src/models/ingest_job.py:20-21`, `src/models/telegram_user.py:20-21`  
**Issue:** `datetime.utcnow()` помечен как deprecated с Python 3.12 и будет удалён в будущих версиях. Возвращает naive datetime (без tzinfo), что создаёт риск ошибок при сравнении с timezone-aware datetimes.

**Fix:**

```python
from datetime import datetime, timezone

created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
```

---

## Low Issues

### LW-01: `voice.py` — groq API ключ пустой строкой по умолчанию

**File:** `src/core/config.py:20`, `src/pipeline/parsers/voice.py:78`  
**Issue:** `groq_api_key: str = ""` — при пустом ключе Groq SDK создаётся без ключа, но падает только при первом вызове API с `AuthenticationError`. Ошибка произойдёт в середине ingestion-задачи, после того как данные уже частично обработаны.

**Fix:** Добавить валидацию при запуске задачи:

```python
if not settings.groq_api_key:
    logger.warning("groq_api_key not configured, voice transcription skipped")
    return messages
```

---

### LW-02: `is_bot` — определение через `from_id` содержит слово "bot"

**File:** `src/pipeline/parsers/telegram.py:69`  
**Issue:** `is_bot="bot" in msg.get("from_id", "").lower()` — эвристика на основе строки `from_id`. Обычный пользователь с именем вида `user_botmaster` получит `is_bot=True`. Telegram API имеет явное поле `is_bot` в объекте User.

**Fix:** Добавить дополнительную проверку типа сообщения или использовать явное поле из Telegram export.

---

### LW-03: `_is_offtopic` — слишком узкий и хрупкий список маркеров

**File:** `src/ai/langgraph/nodes/decide.py:11-13`  
**Issue:** Список `{"анекдот", "погода", "фильм", "рецепт", "музык", "гороскоп"}` крайне мал и легко обходится — фраза "какой прогноз по погоде на стройке" не попадёт в offtopic, хотя является нерабочим вопросом. При этом ложные срабатывания могут заблокировать легитимные запросы (например, "погода влияет на наш производственный график?").

---

### LW-04: `RussianINNRecognizer` — паттерн `\b\d{10}\b|\b\d{12}\b` конфликтует с телефоном

**File:** `src/pipeline/anonymizer/recognizers.py:27-34`  
**Issue:** Паттерн для ИНН `\b\d{10}\b` совпадает с 10-значным телефонным номером (без `+7`/`8`). Телефон `9031234567` будет помечен как ИНН и PHONE_NUMBER одновременно. Функция deduplication в `engine.py` должна это обработать, но только если score ИНН (0.4) ниже телефона (0.3 для short, 0.7 для intl) — приоритет отдаётся ИНН (`RUSSIAN_INN: 100`), что неверно.

---

### LW-05: `chunk_text` — потенциальный бесконечный цикл

**File:** `src/pipeline/chunker/text_chunker.py:33-34`  
**Issue:** Строка `i = max(i - overlap_sentences, i - len(chunk_sentences) + 1)`. Если `overlap_sentences == 0` и `len(chunk_sentences) == 1`, то `i = max(i - 0, i - 1 + 1) = max(i, i) = i` — переменная `i` не продвинется вперёд при следующей итерации внешнего цикла `while i < len(sentences)`. Это бесконечный цикл.

**Fix:**

```python
if i < len(sentences) and overlap_sentences > 0:
    i = max(i - overlap_sentences, i - len(chunk_sentences) + 1)
# Если overlap=0, i уже корректно установлен вышestным циклом
```

---

### LW-06: Тест `test_failure_state_on_exception` — фиктивный assertion

**File:** `tests/api/test_ingest_routes.py:125-135`  
**Issue:**

```python
try:
    ingest_telegram.run(...)
except RuntimeError:
    assert True  # ← тест всегда проходит, даже если исключение не RuntimeError
```

`assert True` ничего не проверяет. Если задача поглотит исключение внутри и не пробросит, тест всё равно пройдёт.

**Fix:** Использовать `pytest.raises`.

```python
with pytest.raises(RuntimeError, match="boom"):
    ingest_telegram.run(source_id="s1", json_path="/tmp/a.json", voice_dir="/tmp")
```

---

### LW-07: Отсутствие тестов для LLM/synthesis пути

**File:** `tests/` (отсутствуют тесты для `src/ai/rag/synthesizer.py`, `src/ai/langgraph/nodes/answer.py`)  
**Issue:** Критический путь генерации ответа пользователю (`synthesize_answer` → `compose_grounded_answer`) не покрыт тестами. Есть тесты для retrieval, attribution contract, fallback, но не для собственно формирования финального ответа.

---

### LW-08: `admin.py` — `except Exception: pass` без логирования в строках 333, 358

**File:** `src/api/routes/admin.py:332-338`, `src/api/routes/admin.py:357-363`  
**Issue:**

```python
except Exception:
    db.rollback()
    return HTMLResponse(content='...Ошибка при публикации...', status_code=500)
```

Исключение подавляется без логирования. Невозможно диагностировать причину ошибки в production.

**Fix:** Добавить `logger.exception(...)` перед `return`.

---

## Вердикт

**Проект НЕ готов к деплою в production.**

### Блокирующие проблемы (необходимо исправить перед деплоем):

| # | Issue | Файл |
|---|-------|------|
| CR-01 | SHA-256 без соли для admin-пароля | `admin.py:32` |
| CR-02 | Открытый `/api/knowledge/query` | `knowledge.py:18` |
| CR-03 | Hardcoded `localhost:8000` | `retrieve_phase2.py:23` |
| CR-04 | Два экземпляра Celery | `ingest.py:19`, `knowledge.py:12` |
| HR-02 | `ValidationError` от пустого `source_id` | `attribution.py:13` |
| HR-03 | `IndexError` в `knowledge_writer` | `knowledge_writer.py:32` |
| LW-05 | Потенциальный бесконечный цикл | `text_chunker.py:33` |

### Требует исправления до production:

- HR-01: IngestJob не обновляется
- HR-04: Мутация глобального settings
- HR-05: Отсутствие CSRF
- HR-06: Отсутствие rate-limit на login
- HR-07: Строковые Qdrant point IDs
- MD-05: Path traversal в voice_path
- MD-09: Orphaned файлы при DB failure

### Можно отложить (post-MVP backlog):

- MD-01–MD-04, MD-06–MD-10, LW-01–LW-08

---

_Reviewed: 2026-04-19_  
_Reviewer: Claude (gsd-code-reviewer, deep mode)_
