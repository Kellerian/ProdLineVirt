---
name: execute-development-cycle
description: >-
  Оркестрирует полный цикл разработки: планирование (planner), реализация
  (developer или frontend-developer), ревью с циклом исправлений
  (code-review или frontend-code-review), документация (tech-writer или
  frontend-tech-writer) по каждой подзадаче, затем user-doc-writer для
  пользовательской документации и WHATSNEW.md. Используй при /dev-cycle,
  /execute-plan, запросах на полную реализацию задачи, end-to-end разработку,
  выполнение плана из .plans/ или когда нужно пройти все этапы от плана до
  документации.
disable-model-invocation: true
---
# Execute Development Cycle

Используй этот skill, когда пользователь просит `/dev-cycle`, `/execute-plan`, `/run-plan`, полную реализацию задачи, end-to-end разработку или продолжение плана из `.plans/`.

Основная сессия — **оркестратор**: не пишет код, не делает code review и не пишет документацию сама. Запускает субагентов через Task tool, группирует независимые подзадачи в **волны** и отслеживает прогресс.

## Цепочки

```text
planner → волны независимых подзадач (внутри волны — параллельно):

  backend:  (developer ↔ code-review)* → tech-writer
  frontend: (frontend-developer ↔ frontend-code-review)* → frontend-tech-writer

  после всех подзадач плана:
  user-doc-writer → user-guides + WHATSNEW.md
```

## Выбор стека подзадачи

Определи стек **перед** запуском реализации:

1. Поле **Стек** в плане: `backend` | `frontend` | `mixed`
2. Иначе — по файлам и сути задачи:

| Стек | Признаки |
|------|----------|
| **frontend** | `.tsx`, `.jsx`, UI в `src/`, хуки, компоненты, стили UI, `vite.config.*`, SPA-роутинг, тексты/формы экранов |
| **backend** | `.py`, сервер, API без UI, БД, скрипты, `requirements.txt`, сборка exe |
| **mixed** | Явно и backend, и frontend в одной подзадаче |

Для **mixed** — выполни обе цепочки последовательно (сначала backend, если frontend зависит от API) или попроси `planner` разбить подзадачу.

## Параллельное выполнение (волны)

Перед запуском **сгруппируй** незавершённые подзадачи в волны.

### Когда подзадачи можно выполнять параллельно

В одной волне — только подзадачи, которые **одновременно**:

- не имеют **Зависимостей** друг на друга (поле «нет» или зависимости только от уже выполненных `- [x]`);
- **не пересекаются по файлам** в **Файлы/модули** (и по смыслу не правят одну и ту же логику);
- не требуют результата друг друга для реализации или ревью.

**Типичный случай:** #2 backend (API) и #3 frontend (экран) без общих файлов и без cross-зависимостей → **одна волна, параллельно**.

**Нельзя параллельно:** #4 «подключить UI к новому endpoint» зависит от #2 → #4 в **следующей** волне после #2.

### Алгоритм волн

1. Собери все `- [ ]` с учётом **Зависимостей**.
2. **Волна 1** — подзадачи без незакрытых зависимостей, попарно проверь пересечение файлов; непересекающиеся объедини в волну.
3. Запусти **все подзадачи волны параллельно** — каждая проходит свой полный цикл (2.1 → 2.2 → 2.3).
4. Дождись завершения **всех** подзадач волны; отметь `- [x]`, обнови план.
5. Повтори для следующей волны, пока чеклист не закрыт.

### Как запускать параллельно

- Несколько Task-вызовов в **одном сообщении** (по одному implementer на подзадачу).
- `run_in_background: true` при Multitask Mode или при явном параллельном запуске.
- Оркестратор **координирует** review и docs **по каждой подзадаче отдельно** после её implement; две подзадачи в волне могут быть на разных фазах (одна на review, другая на implement) — это нормально.
- Единственное частое пересечение — `CHANGES.LOG`: допустимо; при конфликте merge оркестратором после волны.
- Обновление `Plan File` (`- [x]`, frontmatter) — **только оркестратором**, после завершения подзадачи.

### Когда только последовательно

- Подзадачи в одной волне **нельзя** безопасно разделить (общие файлы или зависимость).
- Пользователь явно просит последовательное выполнение.
- После сбоя параллельной волны — повтор только упавших подзадач.

## Общие правила

- Используй корень активного workspace как `Full Repository Path`.
- **Между волнами** — последовательно; **внутри волны** — параллельно, если критерии выше выполнены.
- **Внутри одной подзадачи** — implement → review → docs **строго последовательно**.
- `run_in_background: false` для одиночной подзадачи без параллели; `true` — при параллельном запуске волны.
- Не выполняй работу субагентов сам.
- После каждого субагента — краткий статус в чат (1–3 строки).
- Обновляй файл плана: чеклист `- [x]`, frontmatter `status`, `updated`.
- **Жизненный цикл файла плана:** `backlog/` → `in_progress/` при старте выполнения; `in_progress/` → `complete/` при полном завершении; любая папка → `cancelled/` при `status: cancelled` (см. ниже).
- Коммиты и push — только по явному запросу пользователя.
- При сбое субагента: исправь вызов и повтори **один раз**; при повторной неудаче — остановись с блокером.
- Лимит цикла реализация ↔ ревью: **максимум 15 итераций** на подзадачу. При превышении — остановись и спроси пользователя.
- Backend-код ревьюит только `code-review`; frontend — только `frontend-code-review`.

## Фаза 0: Вход

Определи режим:

| Режим | Условие | Действие |
|-------|---------|----------|
| Новая задача | Описана задача, плана нет | Фаза 1 (planner) |
| Существующий план | Указан `.plans/**/*.md` или «продолжи план» | Пропусти planner, начни с первой `- [ ]` (Фаза 2) |

Извлеки из запроса: `Task`, `Context`, `Constraints`, `Existing Plan` (если есть).

### Разрешение пути к плану

Если путь не указан или файл не найден — ищи по имени/slug в порядке:

1. `.plans/in_progress/`
2. `.plans/backlog/`
3. `.plans/` (legacy — планы в корне до введения `backlog/`)
4. `.plans/complete/` (только если пользователь явно просит продолжить завершённый план)

### Перенос плана в `in_progress` (старт выполнения)

Перед Фазой 2 (или сразу после Фазы 1, если план только что создан) **оркестратор** переносит файл плана:

- **Из:** `.plans/backlog/<filename>.md` (или `.plans/<filename>.md` для legacy)
- **В:** `.plans/in_progress/<filename>.md`

Если файл уже в `.plans/in_progress/` — не переноси повторно.

Действия:

1. Создай `.plans/in_progress/`, если нет.
2. Перемести файл (Windows: `Move-Item`; Linux/macOS: `mv`). Предпочтительно `git mv`, если файл под версионным контролем.
3. Обнови `Plan File` на новый путь.
4. Frontmatter: `status: in_progress`, `updated: <сегодня>`.

### Перенос плана в `cancelled` (отмена)

Если в `Plan File` frontmatter `status: cancelled` (пользователь отменил план, planner зафиксировал отмену, или оркестратор завершает отмену):

- **В:** `.plans/cancelled/<filename>.md`
- **Из:** текущее расположение (`backlog/`, `in_progress/`, корень `.plans/` и т.д.)
- Создай `.plans/cancelled/`, если нет. Предпочтительно `git mv`.
- **Не запускай** выполнение подзадач для плана со `status: cancelled`.
- При обновлении `status` на `cancelled` в ходе сессии — перенеси файл сразу после правки frontmatter.

## Фаза 1: Планирование

Запусти ровно один субагент `planner`:

- `subagent_type: "planner"`
- `readonly: true`
- `description: "Development Planner"`

```text
Full Repository Path: <абсолютный путь>
Task: <описание задачи>
Context: <контекст из чата>
Constraints: <ограничения, если есть>
Existing Plan: <путь к .plans/*.md или пусто>
Custom Instructions: <если есть>
```

После завершения:

- Запомни путь к файлу плана (`Plan File`).
- Если planner вернул блокирующие открытые вопросы — **остановись** и передай их пользователю.
- Иначе выполни **перенос в `in_progress`** (см. выше) и перейди к Фазе 2.

## Фаза 2: Цикл по подзадачам (волнами)

1. Построй **волны** незавершённых подзадач (см. «Параллельное выполнение»).
2. Для текущей волны запусти полный цикл **каждой** подзадачи (параллельно, если в волне >1).
3. Пропускай `- [x]`.

Определи `Stack` подзадачи и выбери агентов:

| Stack | Implementer | Reviewer | Documenter |
|-------|-------------|----------|------------|
| backend | `developer` | `code-review` | `tech-writer` |
| frontend | `frontend-developer` | `frontend-code-review` | `frontend-tech-writer` |

В чате для волны: `Wave W: [#2 backend] + [#3 frontend] → parallel` или для одной: `[#N/<total>] <title> [<stack>] → implement → review → docs`

### 2.1 Реализация

**Backend** — `subagent_type: "developer"`, `readonly: false`, `description: "Developer — subtask #N"`

**Frontend** — `subagent_type: "frontend-developer"`, `readonly: false`, `description: "Frontend Developer — subtask #N"`

```text
Full Repository Path: <абсолютный путь>
Plan File: <путь к .plans/*.md>
Subtask ID: N
Subtask Title: <название>
Subtask Stack: backend | frontend
Subtask Description: <описание из плана>
Files/Modules: <из плана>
Acceptance Criteria: <критерии готовности>
Context: <контекст задачи и предыдущих подзадач>
Constraints: <ограничения>
Custom Instructions: Реализуй только эту подзадачу. Следуй правилам в .cursor/rules/. Обнови CHANGES.LOG при существенных изменениях. Не выходи за scope подзадачи.
```

### 2.2 Ревью с циклом исправлений

Повторяй, пока reviewer не вернёт «no issues» или не исчерпан лимит итераций.

**Backend review** — `subagent_type: "code-review"`, `readonly: true`, `description: "Code Review — subtask #N"`

**Frontend review** — `subagent_type: "frontend-code-review"`, `readonly: true`, `description: "Frontend Code Review — subtask #N"`

```text
Full Repository Path: <абсолютный путь>
Diff: uncommitted changes
Custom Instructions: Ревью только изменений, относящихся к подзадаче #N «<название>» [<stack>] из плана <Plan File>. Игнорируй несвязанные правки, если они есть.
```

Интерпретация:

- `Code review: no issues` / `Frontend code review: no issues` (или аналог) → переход к 2.3.
- **Critical** или **Warning** → передай findings implementer на исправление, затем снова review.
- Только **Suggestion** без Critical/Warning → считай ревью пройденным; кратко перечисли suggestions в статусе.

**Исправления** — тот же implementer, что в 2.1:

- `description: "Developer — fix review #N (iter X)"` или `"Frontend Developer — fix review #N (iter X)"`

```text
Full Repository Path: <абсолютный путь>
Plan File: <путь>
Subtask ID: N
Subtask Stack: backend | frontend
Mode: fix-review-findings
Review Findings: <полная таблица findings от reviewer>
Custom Instructions: Исправь только замечания ревью. Не расширяй scope. Обнови CHANGES.LOG при необходимости.
```

### 2.3 Документация

После успешного review:

**Backend** — `subagent_type: "tech-writer"`, `readonly: false`, `description: "Tech Writer — subtask #N"`

**Frontend** — `subagent_type: "frontend-tech-writer"`, `readonly: false`, `description: "Frontend Tech Writer — subtask #N"`

```text
Full Repository Path: <абсолютный путь>
Task: Документировать выполненную подзадачу #N «<название>»
Scope: update existing
Context: <что сделал implementer, затронутые файлы>
Target Docs: <из плана или по ClientTypes / docs/<app>/frontend/ и user-guides/>
Source Changes: uncommitted changes
Plan File: <путь>
Custom Instructions: Документируй только подзадачу #N. Для frontend: техническая документация в docs/<app>/frontend/, пользовательские инструкции по UI — в docs/<app>/user-guides/. Обнови CHANGES.LOG.
```

Для новой документации укажи `Scope: new docs`.

### 2.4 Завершение подзадачи

- Отметь в `Plan File`: `- [x] N. <название>`.
- Обнови `updated` в frontmatter.
- Статус: `Subtask #N done → docs updated`.
- Перейди к **следующей волне** или завершению плана, когда все подзадачи текущей волны отмечены `- [x]`.

## Фаза 3: Пользовательская документация (после всех подзадач)

Когда **все** пункты чеклиста `- [x]` — запусти **один** субагент `user-doc-writer`:

- `subagent_type: "user-doc-writer"`
- `readonly: false`
- `description: "User Doc Writer — plan completion"`

```text
Full Repository Path: <абсолютный путь>
Task: Актуализировать пользовательскую документацию и WHATSNEW.md по завершённому плану
Plan File: <путь к .plans/*.md>
Context: <список выполненных подзадач, краткое описание изменений из чата>
Source Changes: uncommitted changes
Custom Instructions: Собери все пользовательские изменения по всему плану (не по одной подзадаче). Обнови docs/<app>/user-guides/ и WHATSNEW.md простым языком без технических деталей. CHANGES.LOG не правь.
```

**Не пропускай** эту фазу, даже если подзадачи не затрагивали UI — субагент сам определит, есть ли что добавить в WHATSNEW.

## Фаза 4: Завершение плана

После успешного `user-doc-writer`:

1. Frontmatter: `status: completed`, `updated: <сегодня>`.
2. **Перенеси** файл плана в `.plans/complete/`:
   - **Из:** `.plans/in_progress/<filename>.md` (или текущий `Plan File`)
   - **В:** `.plans/complete/<filename>.md`
   - Создай `.plans/complete/`, если нет. Предпочтительно `git mv`.
3. Обнови `Plan File` на новый путь.

Итог:

```text
Development cycle complete
Plan: .plans/complete/<filename>
Subtasks: N/N completed
Tech docs: <обновлённые docs/... из tech-writer / frontend-tech-writer>
User docs: <обновлённые user-guides/...>
WHATSNEW.md: updated
CHANGES.LOG: updated
Open items: <suggestions или вопросы, если остались>
```

## Что не делать

- Не запускай `bugbot` и `security-review`, если пользователь явно не попросил.
- Не пропускай review перед documenter (tech-writer / frontend-tech-writer).
- Не пропускай `user-doc-writer` после закрытия всех подзадач плана.
- Не отмечай подзадачу выполненной при незакрытых Critical/Warning.
- Не параллель **внутри одной подзадачи** (implement и review одновременно).
- Не запускай параллельно подзадачи с **пересечением файлов** или **незакрытыми зависимостями**.
- Не используй `code-review` для frontend-кода и `frontend-code-review` для backend.
- Не дублируй в чат полные тексты плана или документов.

## Примеры вызова

```text
/dev-cycle Добавить retry-логику в orchestrator API с документацией
```

```text
/execute-plan .plans/backlog/2026-06-13-orchestrator-retry-logic.md
```

```text
/dev-cycle Добавить экран настроек в React UI с инструкцией для пользователя
```

```text
/dev-cycle REST API для заказов + React-экран списка (backend и frontend параллельно, интеграция — после)
```
