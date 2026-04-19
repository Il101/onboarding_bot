---
status: complete
phase: 05-bot-access-hardening
source: 05-01-SUMMARY.md, 05-02-SUMMARY.md
started: 2026-04-19T12:21:44Z
updated: 2026-04-19T12:21:44Z
---

## Current Test

[testing complete]

## Tests

### 1. Whitelist policy denies unknown Telegram user_id
expected: Для user_id, которого нет в whitelist, авторизация возвращает deny (`allowed=False`, `reason=not_whitelisted`).
result: pass

### 2. Unauthorized /start is denied before graph invocation
expected: Неавторизованный пользователь получает deny-ответ, при этом graph.ainvoke не вызывается.
result: pass

### 3. Whitelisted user proceeds through normal bot flow
expected: Авторизованный user_id проходит gate, вызывается graph с корректным thread_id и ролью, ответ форматируется с блоком источников.
result: pass

### 4. Graph auth node blocks retrieve for unauthorized identity
expected: При неавторизованной identity граф завершает веткой deny и не вызывает retrieve-узел.
result: pass

### 5. Handler error path returns safe user-facing message
expected: При внутренней ошибке обработчик возвращает безопасное русскоязычное сообщение без утечки traceback.
result: pass

## Summary

total: 5
passed: 5
issues: 0
pending: 0
skipped: 0
blocked: 0

## Gaps

[none yet]
