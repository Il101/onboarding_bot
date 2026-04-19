---
status: complete
phase: 04-runtime-integration
source: 04-01-SUMMARY.md, 04-02-SUMMARY.md
started: 2026-04-19T09:41:08Z
updated: 2026-04-19T09:41:45Z
---

## Current Test

[testing complete]

## Tests

### 1. Ingest Telegram triggers extraction
expected: После успешной загрузки Telegram-данных задача ingestion завершается без ошибки и автоматически запускается этап извлечения знаний (без ручного старта следующего шага).
result: pass

### 2. Ingest PDF triggers extraction
expected: После успешной загрузки PDF ingestion завершает индексацию и автоматически ставит задачу извлечения знаний.
result: pass

### 3. SOP dispatch only for publishable knowledge
expected: Генерация SOP запускается только когда есть publishable grouped units; при review-only/низкой уверенности SOP не запускается.
result: pass

### 4. Query uses real retrieval with stable envelope
expected: Запрос к /api/knowledge/query отвечает по реальным данным retrieval и всегда возвращает совместимый контракт ответа: answer, confidence, sources, fallback_used.
result: pass

### 5. Safe fallback on retrieval issues or low relevance
expected: Если retrieval недоступен или релевантность низкая, API не падает с 500 и возвращает безопасный fallback-ответ с корректными полями источников.
result: pass

### 6. Bot contract compatibility for grounded answers
expected: Интеграция с ботом принимает ответ без адаптерных поломок: атрибуция источников и поля grounded-ответа остаются совместимыми.
result: pass

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
