# V-Brain — AI Knowledge Extractor & Mentor

Система извлечения бизнес-знаний из рабочих чатов (Telegram) и документов (PDF), которая превращает разрозненную информацию в структурированную базу знаний и AI-ментора для новых сотрудников.

**Суть:** новый сотрудник задаёт вопрос в Telegram-боте и получает точный ответ на основе реальных внутренних коммуникаций и документов компании — без участия владельца или наставника.

## Возможности

- Загрузка PDF документов и Telegram JSON экспортов через веб-интерфейс
- PII-анонимизация (ФИО, телефоны, email, ИНН) перед обработкой
- Извлечение структурированных знаний с помощью LLM
- Гибридный поиск (векторный + BM25) с reranking
- Telegram-бот с мульти-turn контекстом и цитированием источников
- Веб-админка: управление источниками, знаниями, пользователями, аналитика
- Авторизация пользователей бота через whitelist Telegram user_id

## Стек

Python 3.12 · FastAPI · LlamaIndex · Qdrant · PostgreSQL · Redis · Celery · python-telegram-bot · Docling · Presidio · HTMX · Alpine.js · Tailwind CSS

---

## Быстрый старт

### Требования

- Python 3.12+
- Docker + Docker Compose
- `uv` — менеджер пакетов (`pip install uv`)
- Telegram Bot Token ([@BotFather](https://t.me/BotFather))
- API ключ OpenAI или Anthropic (для LLM)
- API ключ Groq — опционально, для транскрипции голосовых сообщений

### 1. Установить зависимости

```bash
uv sync
```

### 2. Создать `.env`

```env
# LLM (выбрать один)
OPENAI_API_KEY=sk-...
# ANTHROPIC_API_KEY=sk-ant-...

# Telegram бот
TELEGRAM_BOT_TOKEN=123456:ABC-...

# Groq (для голосовых сообщений, опционально)
GROQ_API_KEY=gsk_...

# Веб-админка
ADMIN_PASSWORD=ваш_пароль

# Пользователи бота: Telegram user_id → роль
# Роли: employee, mentor, admin
TELEGRAM_USER_ROLES={"123456789": "admin", "987654321": "employee"}

# Инфраструктура (docker-compose — оставить как есть)
DATABASE_URL=postgresql+psycopg2://vbrain:vbrain@localhost:5432/vbrain
REDIS_URL=redis://localhost:6379/0
QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### 3. Запустить инфраструктуру

```bash
docker compose up -d
mkdir -p data/uploads
```

### 4. Применить миграции БД

```bash
uv run alembic upgrade head
```

### 5. Запустить сервисы

В трёх отдельных терминалах:

```bash
# API + веб-админка
uv run uvicorn src.api.main:app --reload --port 8000

# Celery (фоновые задачи)
uv run celery -A src.tasks.ingest worker --loglevel=info

# Telegram бот
uv run python -m src.bot.telegram_app
```

---

## Веб-админка

Открыть: **http://localhost:8000/admin**

Войти с паролем из `ADMIN_PASSWORD`.

| Раздел | Что делать |
|--------|-----------|
| **Источники** | Загрузить PDF или Telegram JSON экспорт; смотреть статус обработки |
| **Знания** | Просматривать извлечённые знания, одобрять / отклонять / редактировать |
| **Пользователи** | Добавлять и удалять пользователей бота по Telegram user_id |
| **Аналитика** | Статистика использования, оценки ответов, популярные вопросы |

### Как экспортировать Telegram чат

1. Telegram Desktop → **Настройки → Экспорт данных чата**
2. Формат **JSON**, включить голосовые сообщения
3. Загрузить `result.json` (и `.ogg` файлы) в раздел «Источники»

---

## Telegram бот

Узнать свой user_id: написать любому боту-определителю ID или написать `/start` вашему боту — он ответит ID если не авторизован.

Добавить пользователя в веб-админке раздел «Пользователи» или сразу в `.env`:
```env
TELEGRAM_USER_ROLES={"ВАШ_ID": "admin"}
```

Использование: просто написать вопрос на русском. Бот ответит с цитатами источников. Оценить ответ кнопками 👍 / 👎.

---

## Тесты

```bash
uv run pytest tests/ -q
```

---

## Типичные проблемы

| Проблема | Решение |
|----------|---------|
| `ModuleNotFoundError` | `uv sync` |
| БД не подключается | `docker compose up -d`, подождать 5 сек |
| Бот не отвечает | Проверить `TELEGRAM_BOT_TOKEN`, добавить user_id в `TELEGRAM_USER_ROLES` |
| PDF не обрабатывается | Убедиться что Celery запущен и Redis доступен |
| Embeddings долго грузятся | Первый запуск: модель `multilingual-e5-large` (~560 МБ) скачивается один раз |
