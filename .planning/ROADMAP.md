# Roadmap: V-Brain

## Overview

V-Brain превращает разрозненные рабочие чаты (Telegram) и документы (PDF) в структурированную базу знаний и AI-ментора для новых сотрудников. Путь: загрузить источники -> извлечь и проиндексировать знания -> отвечать через Telegram-бота -> управлять через веб-админку. Каждая фаза доставляет завершённый горизонт возможностей.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3, 4): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation & Data Ingestion** - Парсинг источников, PII-анонимизация и индексация в векторной БД
- [x] **Phase 2: Knowledge Extraction & RAG** - Извлечение знаний LLM, генерация SOP и RAG-пайплайн с гибридным поиском
- [ ] **Phase 3: Telegram Bot** - Q&A бот с мульти-turn контекстом, цитированием источников и защитой от галлюцинаций
- [ ] **Phase 4: Web Admin Panel** - Веб-интерфейс для управления источниками, рецензирования знаний и аналитики

## Phase Details

### Phase 1: Foundation & Data Ingestion
**Goal**: Система может принять Telegram JSON export и PDF документы, очистить данные от шума, анонимизировать PII, и проиндексировать в векторной БД (Qdrant) с гибридным поиском
**Depends on**: Nothing (first phase)
**Requirements**: ING-01, ING-02, ING-03, ING-04, ING-05, ING-06
**Success Criteria** (what must be TRUE):
  1. Администратор загружает Telegram JSON export и система извлекает текстовые сообщения с метаданными (автор, дата, чат), отфильтровывая служебные сообщения и шум
  2. Система транскрибирует голосовые сообщения из Telegram export через Groq Whisper API и включает транскрипцию в общий поток обработки
  3. Система загружает PDF документ с кириллицей и извлекает из него текст
  4. Во всех извлечённых данных ФИО, телефоны, email и ИНН заменены на токены до любой дальнейшей обработки
  5. Обработанные данные индексируются в Qdrant с hybrid search (векторный + BM25), и каждый фрагмент хранит source attribution
**Plans**: 6 plans

Plans:
- [x] 01-01-PLAN.md — Project infrastructure, config, models, test fixtures
- [x] 01-02-PLAN.md — Telegram JSON parser, noise filter, chronological grouping
- [x] 01-03-PLAN.md — PDF parser (Docling) and voice transcription (Groq Whisper)
- [x] 01-04-PLAN.md — PII anonymization (Presidio + custom Russian recognizers)
- [x] 01-05-PLAN.md — Text/Telegram chunking, embedding generation, Qdrant indexing
- [x] 01-06-PLAN.md — Celery task orchestration, REST API endpoints, integration

### Phase 2: Knowledge Extraction & RAG
**Goal**: LLM извлекает структурированные знания из проиндексированных данных, генерирует SOP-инструкции, а RAG-пайплайн возвращает релевантные ответы на основе гибридного поиска с reranking
**Depends on**: Phase 1
**Requirements**: KNW-01, KNW-02, KNW-03, KNW-04
**Success Criteria** (what must be TRUE):
  1. Система автоматически извлекает структурированные знания из анонимизированного текста и группирует их по темам
  2. LLM генерирует читаемые Markdown SOP-инструкции из кластеризованных знаний на основе чатов
  3. RAG-пайплайн находит релевантные фрагменты через гибридный поиск (векторный + BM25) и возвращает контекст для генерации ответа
  4. Каждый ответ RAG-пайплайна содержит ссылку на оригинальный источник (сообщение/документ)
**Plans**: 3 plans

Plans:
- [x] 02-01-PLAN.md — Contracts and policy gates for extraction/RAG thresholds and attribution schema
- [x] 02-02-PLAN.md — Structured extraction + SOP generation pipeline with confidence gate and Celery orchestration
- [x] 02-03-PLAN.md — Hybrid retrieval + reranking + fallback synthesis and knowledge query API

### Phase 3: Telegram Bot
**Goal**: Новый сотрудник задаёт вопрос через Telegram бот на русском языке и получает точный ответ с цитированием источников, защитой от галлюцинаций и учётом контекста диалога
**Depends on**: Phase 2
**Requirements**: BOT-01, BOT-02, BOT-03, BOT-04, BOT-05
**Success Criteria** (what must be TRUE):
  1. Авторизованный сотрудник отправляет вопрос боту и получает ответ на русском языке, основанный на базе знаний
  2. При низкой уверенности бот возвращает "Я не знаю -- обратитесь к коллеге" вместо галлюцинированного ответа
  3. Бот учитывает контекст диалога -- пользователь может задавать уточняющие вопросы без повторения контекста
  4. Пользователь может оценить ответ (thumbs up/down), и обратная связь записывается для анализа
  5. Неавторизованный пользователь не получает доступ к боту -- при /start запрашивается проверка роли
**Plans**: 3 plans

Plans:
- [x] 03-01-PLAN.md — Phase 3 contracts/tests foundation: bot state, auth gate, feedback persistence
- [x] 03-02-PLAN.md — LangGraph policy workflow: retrieval, summarization, fallback/clarify/answer decisions
- [ ] 03-03-PLAN.md — Telegram transport integration: handlers, presentation with sources, thumbs feedback wiring

### Phase 4: Web Admin Panel
**Goal**: Администратор управляет всей системой через веб-интерфейс: загружает источники, рецензирует знания, управляет пользователями и отслеживает аналитику использования
**Depends on**: Phase 2
**Requirements**: ADM-01, ADM-02, ADM-03, ADM-04, ADM-05, ADM-06, ADM-07
**Success Criteria** (what must be TRUE):
  1. Администратор загружает PDF документы и подключает Telegram export (JSON + голосовые файлы) через веб-интерфейс
  2. Администратор просматривает список извлечённых знаний с фильтрацией по темам и источникам, а также редактирует и одобряет знания перед публикацией
  3. Администратор может удалить или отклонить некорректные знания
  4. Администратор управляет пользователями и ролями (admin, employee)
  5. Dashboard показывает популярные вопросы, среднюю оценку ответов и активность пользователей
**Plans**: TBD
**UI hint**: yes

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Data Ingestion | 6/6 | Completed | 2026-04-18 |
| 2. Knowledge Extraction & RAG | 3/3 | Completed | 2026-04-18 |
| 3. Telegram Bot | 3/3 | Completed | 2026-04-19 |
| 4. Web Admin Panel | 0/? | Not started | - |
