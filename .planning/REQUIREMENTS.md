# Requirements: V-Brain

**Defined:** 2026-04-17
**Core Value:** Новый сотрудник может получить ответ на любой рабочий вопрос за секунды, используя знания извлечённые из реальных коммуникаций и документов компании

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Data Ingestion & Security

- [ ] **ING-01**: Система анонимизирует PII в тексте (ФИО, телефоны, email, ИНН) через Presidio + кастомные русские распознаватели перед любой обработкой
- [ ] **ING-02**: Система парсит Telegram JSON export (result.json) и извлекает текстовые сообщения с метаданными (автор, дата, чат)
- [ ] **ING-03**: Система транскрибирует голосовые сообщения из Telegram export через Groq Whisper API и включает транскрипцию в пайплайн обработки
- [ ] **ING-04**: Система фильтрует шум из Telegram логов (service messages, приветствия, короткие ответы <5 слов, bot messages)
- [ ] **ING-05**: Система извлекает текст из PDF документов с поддержкой кириллицы
- [ ] **ING-06**: Система поддерживает пакетную обработку (batch processing) больших объёмов данных с прогресс-трекингом

### Knowledge Extraction & Indexing

- [ ] **KNW-01**: LLM извлекает структурированные знания из анонимизированного текста и группирует по темам
- [ ] **KNW-02**: LLM генерирует SOP инструкции (Markdown) из кластеризованных знаний на основе чатов
- [ ] **KNW-03**: Система индексирует извлечённые знания в векторной БД (Qdrant) с hybrid search (векторный + BM25 для русского)
- [ ] **KNW-04**: Каждый фрагмент знания хранит source attribution (ссылка на оригинальное сообщение/документ)

### Telegram Bot

- [ ] **BOT-01**: Новый сотрудник задаёт вопрос через Telegram бот и получает ответ на русском языке на основе RAG
- [ ] **BOT-02**: Бот возвращает "Я не знаю — обратитесь к коллеге" при confidence ниже порога (предотвращение галлюцинаций)
- [ ] **BOT-03**: Бот учитывает контекст диалога (предыдущие вопросы в сессии)
- [ ] **BOT-04**: Пользователь может оценить ответ (thumbs up/down) для обратной связи
- [ ] **BOT-05**: Доступ к боту только для авторизованных сотрудников (проверка роли при /start)

### Web Admin Panel

- [ ] **ADM-01**: Администратор может загружать PDF документы через веб-интерфейс
- [ ] **ADM-02**: Администратор может подключить Telegram export (JSON + голосовые файлы) для обработки
- [ ] **ADM-03**: Администратор может просматривать список извлечённых знаний с фильтрацией по темам и источникам
- [ ] **ADM-04**: Администратор может редактировать и одобрять знания перед публикацией в RAG (review gate)
- [ ] **ADM-05**: Администратор может удалять или отклонять некорректные знания
- [ ] **ADM-06**: Система поддерживает управление пользователями и ролями (admin, employee)
- [ ] **ADM-07**: Dashboard показывает аналитику: популярные вопросы, средняя оценка ответов, активность пользователей

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Multi-Source & Advanced Ingestion

- **ING-V2-01**: Live Telegram integration (bot слушает чат в реальном времени, не только export)
- **ING-V2-02**: Парсинг видео инструкций (Loom/записи экрана)

### AI Improvements

- **AI-V2-01**: Fine-tuning embedding модели на доменной лексике бизнеса
- **AI-V2-02**: Мультиязычная поддержка (ответы на языке вопроса)

### Collaboration

- **COL-V2-01**: Режим "задать вопрос эксперту" — эскалация unanswered вопросов владельцу
- **COL-V2-02**: Встроенная система заметок сотрудников к знаниям

## Out of Scope

| Feature | Reason |
|---------|--------|
| Парсинг видео (Loom) | Высокая сложность, текстовых источников достаточно для MVP |
| Мобильное приложение | Telegram бот + веб покрывают все сценарии |
| Мульти-тенант архитектура | Один клиент, но закладываем масштабирование |
| OAuth авторизация | Простой логин достаточен для MVP |
| Dify.ai как core pipeline | Кастомная логика (PII, Telegram, SOP) требует программного контроля |

## Traceability

Which phases cover which requirements. Reconciled against phase-level VERIFICATION artifacts (01-04) and strict no-orphaned gate.

| Requirement | Phase | Status |
|-------------|-------|--------|
| ING-01 | Phase 1 | Satisfied (01-VERIFICATION) |
| ING-02 | Phase 1 | Satisfied (01-VERIFICATION) |
| ING-03 | Phase 1 | Satisfied (01-VERIFICATION) |
| ING-04 | Phase 1 | Satisfied (01-VERIFICATION) |
| ING-05 | Phase 1 | Satisfied (01-VERIFICATION) |
| ING-06 | Phase 1 | Satisfied (01-VERIFICATION) |
| KNW-01 | Phase 2 / 4 | Satisfied (02-VERIFICATION, 04-VERIFICATION) |
| KNW-02 | Phase 2 / 4 | Satisfied (02-VERIFICATION, 04-VERIFICATION) |
| KNW-03 | Phase 2 / 4 | Satisfied overall (partial delegation in 04-VERIFICATION) |
| KNW-04 | Phase 2 / 4 | Satisfied overall (partial delegation in 04-VERIFICATION) |
| BOT-01 | Phase 3 / 4 | Satisfied (03-VERIFICATION, 04-VERIFICATION) |
| BOT-02 | Phase 3 / 4 | Satisfied overall (partial delegation in 04-VERIFICATION) |
| BOT-03 | Phase 3 | Satisfied (03-VERIFICATION) |
| BOT-04 | Phase 3 | Satisfied (03-VERIFICATION) |
| BOT-05 | Phase 5 | In progress (05-01 test scaffolding committed) |
| ADM-01 | Phase 6 | Pending |
| ADM-02 | Phase 6 | Pending |
| ADM-03 | Phase 6 | Pending |
| ADM-04 | Phase 6 | Pending |
| ADM-05 | Phase 6 | Pending |
| ADM-06 | Phase 6 | Pending |
| ADM-07 | Phase 6 | Pending |

**Coverage:**
- v1 requirements: 22 total
- Mapped to phases: 22
- Unmapped: 0
- Verified satisfied (Phases 1-4): 14
- Unsatisfied/pending: 8 (BOT-05 in progress + ADM-01..ADM-07)

---
*Requirements defined: 2026-04-17*
*Last updated: 2026-04-19 after verification evidence reconciliation*
