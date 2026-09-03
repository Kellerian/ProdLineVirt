# Example — crystallized task thesis

Based on `execution-modes-config` structure; inbox path before kickoff.

````markdown
# `agent_work/inbox/execution-modes-config_prompt.md`
**Created**: `2026-06-25 20:00`

> Вынести дефолты параллелизма оркестратора и суб-оркестратора (`Orch mode`, `Sub-orch mode`) в user-editable конфиг — один файл вместе с git-дефолтами, с resolver-процедурой и сохранением приоритета явных маркеров в плане.

## Суть задачи

Сейчас дефолты `Orch mode: N=1` и `Sub-orch mode: SEQUENTIAL` захардкожены в `.cursor/rules/05-execution-modes.mdc`. Чтобы глобально включить, например, `PARALLEL` для независимых фаз или микро-шагов, нужно править rule-файл или дублировать маркеры в каждом плане. Нужно расширить существующий `.cursor/config/pipeline-defaults.yaml` по образцу уже реализованного `resolve_pipeline_policy()` для `git_policy` / `work_mode`.

## Проблема

- Дефолты параллелизма только в `.mdc` — нет user-editable yaml.
- Оркестратор и суб-оркестратор читают `05-execution-modes.mdc` inline; Architect пишет маркеры «на глаз», без единого конфига.
- `git_policy` уже в yaml, а `orch_mode` / `sub_orch_mode` — нет: два разных источника дефолтов для одного runtime.
- Overlap-анализ оркестратора не документирован относительно yaml-дефолта — нужна явная семантика.

## Желаемый результат

Пользователь правит `.cursor/config/pipeline-defaults.yaml`:

```yaml
defaults:
  git_policy: checkpoint
  work_mode: agent_only
  orch_mode: N=1              # N=1 | PARALLEL
  sub_orch_mode: SEQUENTIAL   # SEQUENTIAL | PARALLEL
```

— и новые планы Architect'а, и runtime оркестратора/суб-оркестратора используют эти дефолты, если в плане нет явного маркера. Явные `Orch mode:` / `Sub-orch mode:` в плане по-прежнему имеют приоритет.

## Цели

1. Расширить `pipeline-defaults.yaml`: ключи `defaults.orch_mode`, `defaults.sub_orch_mode`; опциональные override в `plans[<basename>]`.
2. Добавить в `05-execution-modes.mdc` процедуру `resolve_execution_modes()` с приоритетом: маркер фазы/подзадачи → Policy target плана → `plans[basename]` → `defaults` → fallback (`N=1`, `SEQUENTIAL`).
3. Обновить `orchestrator.md`: вызывать resolver перед overlap-анализом; yaml-дефолт применяется когда на фазе нет `Orch mode:`.
4. Обновить `sub-orchestrator.md`: resolver для `Sub-orch mode` когда маркер на подзадаче отсутствует.
5. Обновить `architect.md`: читать yaml при создании плана; писать маркеры только при отклонении от resolved defaults.
6. Bootstrap-план этой фичи: `git_policy: none` на всех подзадачах (правки только `.cursor/`).

## Вне scope

- Product code (`executive.py`, assets, отчёты).
- Перенос `progress_bar`, `Architect depth` в yaml.
- Объединение `model-overrides.yaml` и `pipeline-defaults.yaml`.
- Автоматический push / merge веток.
- Массовое обновление существующих `plan/*.md`.

## Затрагиваемая область

`.cursor/config/pipeline-defaults.yaml`, `.cursor/rules/05-execution-modes.mdc`, `.cursor/agents/orchestrator.md`, `.cursor/agents/sub-orchestrator.md`, `.cursor/agents/architect.md`, опционально `.cursor/skills/orchestrator/SKILL.md`.

## Ограничения

- **Нельзя ломать:** overlap-анализ оркестратора; direct QA-only path; sequential prerequisite gate в sub-orchestrator.
- **Conservative fallback:** `orch_mode: N=1`, `sub_orch_mode: SEQUENTIAL`.
- **Коммит этой фичи:** `git_policy: none` на подзадачи до PASS Shared Pipeline.

## Критерии готовности

- [ ] `pipeline-defaults.yaml` содержит `orch_mode` и `sub_orch_mode`; смена `defaults.sub_orch_mode` на `PARALLEL` меняет поведение sub-orchestrator без правки `.mdc`.
- [ ] `resolve_execution_modes()` описан в одном месте (`05-execution-modes.mdc`).
- [ ] Приоритет: явный маркер в плане > Policy target > `plans[]` > `defaults` > fallback.
- [ ] Orchestrator и Sub-orchestrator используют resolved defaults при отсутствии маркеров.
- [ ] Architect пишет Execution target из конфига; маркеры только при override.

## Риски и неясности

- **Overlap vs yaml PARALLEL:** если defaults `orch_mode: PARALLEL`, но подзадачи пересекаются по файлам — overlap-анализ должен побеждать для overlapping groups.
- **Единый resolver:** предпочтительно отдельная `resolve_execution_modes()` в rule 05 (rule 12 остаётся git-only).

## Исходные формулировки заказчика

> «можно ли вынести паралелизм в конфиг файл для оркестратора и суборкестратора чтобы задавалось из одного файла?»

> «да» — оформить задачу (prompt + plan)

---

**Task slug:** `execution-modes-config`  
**Handoff:** `/orchestrator execution-modes-config`
````
