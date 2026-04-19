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
- [x] **Phase 3: Telegram Bot** - Q&A бот с мульти-turn контекстом, цитированием источников и защитой от галлюцинаций
- [x] **Phase 4: Runtime Integration Hardening** - Сквозная runtime-интеграция ingestion -> extraction -> retrieval для реальной базы знаний
- [ ] **Phase 5: Bot Access Hardening** - Реальная авторизация Telegram-пользователей через whitelist user_id и интеграция роли без hardcode
- [ ] **Phase 6: Web Admin Panel** - Веб-интерфейс для управления источниками, рецензирования знаний и аналитики
- [x] **Phase 7: Verification Evidence Backfill** - Закрытие orphaned-gaps через фазовые VERIFICATION-артефакты и обновление трассируемости

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
- [x] 03-03-PLAN.md — Telegram transport integration: handlers, presentation with sources, thumbs feedback wiring

### Phase 4: Runtime Integration Hardening
**Goal**: Закрыть разрывы интеграции между ingestion, extraction и retrieval, чтобы Telegram-бот отвечал на основе реальных данных компании, а не seed-данных
**Depends on**: Phase 3
**Requirements**: KNW-01, KNW-02, KNW-03, KNW-04, BOT-01
**Gap Closure:** Closes milestone audit gaps for Phase 1 -> 2 -> 3 wiring and grounded employee Q&A flow
**Success Criteria** (what must be TRUE):
  1. Завершение ingestion инициирует extraction/SOP pipeline через runtime orchestration (без ручного запуска)
  2. `/api/knowledge/query` использует реальный retrieval из индекса/хранилища знаний вместо статических seed
  3. Ответы retrieval содержат корректный attribution к реальным источникам
  4. Сквозной поток сотрудника (вопрос в Telegram -> retrieval -> grounded answer) проходит на реальных данных
**Plans**: 2 plans

Plans:
- [x] 04-01-PLAN.md — Wire ingestion runtime to extraction/SOP orchestration with automated integration checks
- [x] 04-02-PLAN.md — Replace seed-based knowledge query with real retrieval-backed path while preserving bot contract

### Phase 5: Bot Access Hardening
**Goal**: Убрать hardcoded роль в Telegram-боте и внедрить реальную авторизацию пользователей через whitelist Telegram user_id
**Depends on**: Phase 4
**Requirements**: BOT-05
**Gap Closure:** Closes milestone audit gap for runtime authorization source in Telegram transport
**Success Criteria** (what must be TRUE):
  1. Роль/доступ вычисляется из whitelist источника (конфиг/БД), а не из hardcoded значения
  2. Неавторизованный user_id стабильно получает deny-path без вызова retrieval/LLM
  3. Авторизованный user_id проходит обычный workflow бота
**Plans**: TBD

### Phase 6: Web Admin Panel
**Goal**: Администратор управляет всей системой через веб-интерфейс: загружает источники, рецензирует знания, управляет пользователями и отслеживает аналитику использования
**Depends on**: Phase 5
**Requirements**: ADM-01, ADM-02, ADM-03, ADM-04, ADM-05, ADM-06, ADM-07
**Success Criteria** (what must be TRUE):
  1. Администратор загружает PDF документы и подключает Telegram export (JSON + голосовые файлы) через веб-интерфейс
  2. Администратор просматривает список извлечённых знаний с фильтрацией по темам и источникам, а также редактирует и одобряет знания перед публикацией
  3. Администратор может удалить или отклонить некорректные знания
  4. Администратор управляет пользователями и ролями (admin, employee)
  5. Dashboard показывает популярные вопросы, среднюю оценку ответов и активность пользователей
**Plans**: TBD
**UI hint**: yes

### Phase 7: Verification Evidence Backfill
**Goal**: Устранить orphaned-требования из milestone audit через создание/обновление phase-level VERIFICATION артефактов и согласование traceability-статусов
**Depends on**: Phase 6
**Requirements**: ING-01, ING-02, ING-03, ING-04, ING-05, ING-06, KNW-01, KNW-02, KNW-03, KNW-04, BOT-01, BOT-02, BOT-03, BOT-04
**Gap Closure:** Closes milestone audit orphaned verification evidence gaps for phases 1-4
**Success Criteria** (what must be TRUE):
  1. Для фаз 1-4 существуют корректные `*-VERIFICATION.md` с покрытием требований
  2. REQUIREMENTS и milestone audit больше не помечают ING/KNW/BOT(01-04) как orphaned
  3. Повторный `/gsd-audit-milestone` не содержит verification-orphan gaps по фазам 1-4
**Plans**: 3 plans

Plans:
- [x] 07-01-PLAN.md — Build strict verification backfill validator and regression tests
- [x] 07-02-PLAN.md — Backfill phase-level VERIFICATION artifacts for phases 1-4
- [x] 07-03-PLAN.md — Reconcile REQUIREMENTS/ROADMAP/milestone audit and enforce no-orphaned assertion

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation & Data Ingestion | 6/6 | Completed | 2026-04-18 |
| 2. Knowledge Extraction & RAG | 3/3 | Completed | 2026-04-18 |
| 3. Telegram Bot | 3/3 | Completed | 2026-04-19 |
| 4. Runtime Integration Hardening | 2/2 | Completed | 2026-04-19 |
| 5. Bot Access Hardening | 0/? | Not started | - |
| 6. Web Admin Panel | 0/? | Not started | - |
| 7. Verification Evidence Backfill | 3/3 | Completed | 2026-04-19 |
