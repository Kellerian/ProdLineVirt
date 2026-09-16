---
name: execute-plan
description: >-
  Выполняет план из .plans/ по подзадачам: backend
  (developer → code-review → tech-writer) или frontend
  (frontend-developer → frontend-code-review → frontend-tech-writer), затем
  user-doc-writer (user-guides + WHATSNEW.md). Используй при /execute-plan,
  /run-plan, Build в Plan mode, продолжении плана
  или запросе реализовать пункты чеклиста.
disable-model-invocation: true
---

# Execute Plan

Алиас для skill `execute-development-cycle`. Следуй **всем** инструкциям из:

`.cursor/skills/execute-development-cycle/SKILL.md`

## Вход

Пользователь передаёт путь к плану, например:

```text
/execute-plan .plans/backlog/2026-06-15-my-feature.md
```

Если путь не указан — найди последний или явно названный файл с незавершёнными пунктами `- [ ]` в `.plans/in_progress/`, затем в `.plans/backlog/`, затем в корне `.plans/` (legacy).

## Режим

- План уже есть → пропусти фазу planner; если `status: cancelled` — перенеси в `.plans/cancelled/` и остановись; иначе перенеси в `.plans/in_progress/` (если ещё в `backlog/` или корне `.plans/`), начни с первой `- [ ]`.
- Плана нет → сначала `plan-development`, затем перенос в `in_progress` и цикл по подзадачам.
- При завершении всех подзадач и `user-doc-writer` — перенос в `.plans/complete/`.
- При отмене плана (`status: cancelled`) — перенос в `.plans/cancelled/`.
