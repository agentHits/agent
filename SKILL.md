---
name: agent
description: Локальный Sol Advisor fast path по умолчанию для задач: native role-pinned делегирование, проверка фактического diff и свежий Sol review. Literal $agent остаётся совместимым явным триггером.
---

# Agent

Для задач по умолчанию активируй этот локальный маршрут Sol Advisor. Literal `$agent`
остаётся совместимым явным триггером. Не выводи из него полномочия Agent Flow:
`$agent` не получает их сам по себе.

## Локальный fast path

Это намеренный local fork Sol Advisor. До начала runtime пользователь однократно
запускает `scripts/install-sol-advisor.sh`, который ставит vendored role templates в
`$CODEX_HOME/agents` либо `$HOME/.codex/agents` и отказывается перезаписывать
конфликтующий файл. Новая задача Codex требуется, чтобы native runtime обнаружил
установленные роли.

В runtime доверяй install-time role templates: не выполняй per-request plugin
discovery, provenance lookup, installer `--check`, чтение upstream contract или
`inspect-agent-runtime.sh`. Это не ослабляет pins: custom-agent TOML остаётся
источником модели и reasoning effort. При отсутствии точной native role заверши
маршрут ошибкой без fallback, замены роли, модели или reasoning effort.

Основная сессия сохраняет архитектуру, выбор lane, инспекцию фактического diff и
повторный запуск проверок. Она не должна подменять доступного implementation worker.

## Native implementation route

Сначала напиши worker specification ровно из пяти разделов: `OBJECTIVE`, `FILES AND
OWNERSHIP`, `INTERFACES`, `CONSTRAINTS` и `VERIFICATION`. Укажи, что worker не один в
кодовой базе, обязан сохранить чужие правки и меняет только owned files.

Для routine, полностью определённой работы сразу делегируй native
`sol_advisor_luna_implementer`; его vendored template pin’ит `gpt-5.6-luna` и `max`.
Для context-heavy, higher-risk или wider-blast-radius работы сразу делегируй native
`sol_advisor_terra_implementer`; его vendored template pin’ит `gpt-5.6-terra` и `max`.
Не добавляй per-spawn model или reasoning override. Если выбранная точная роль не
доступна, верни ошибку; не используй built-in либо похожую роль.

После результата worker основная сессия обязана:

- Inspect actual working-tree diff и подтвердить, что изменены только owned files.
- Повторно запустить все команды из `VERIFICATION` и сверить результаты с
  `OBJECTIVE` и `INTERFACES`.
- При ошибке сформировать исправленную спецификацию и повторно делегировать её
  подходящей native роли.

Отчёт worker — только утверждение, а не доказательство выполнения.

## Fresh Sol review

Только после успешной primary verification запусти новый native
`sol_advisor_sol_reviewer`. Его vendored template pin’ит `gpt-5.6-sol` и `high` и
запрашивает read-only sandbox. Передай stated goal, полный allowed change set или diff,
interfaces и constraints, а также фактическое verification evidence. Явно потребуй
behaviorally read-only review и ровно один verdict: `ship`, `fix-first` или `rethink`.

Прими результат только с verdict `ship`. При `fix-first` worker исправляет названные
пункты, затем основная сессия заново проверяет diff и запускает новый fresh Sol review.
При `rethink` вернись к архитектуре и не объявляй completion. Reviewer не реализует
исправления и не расширяет scope.

## Private memory and verified publication gates

Перед использованием project state прочитай [project-memory.md](references/project-memory.md),
а перед publication — [verified-auto-push.md](references/verified-auto-push.md). Считай
память гипотезой до подтверждения кодом, конфигурацией и фактическим выводом команд.
Инициализируй private memory до делегирования и повторно прочитай ownership/status после
работы.

Для publication используй `scripts/verified_push.py check`; `execute` разрешён только
с exact authorization digest. Никогда не force push, не повторяй неизвестный исход и не
печатай secrets, diffs или remote URLs. Первичная публикация пустого repository требует
явного разрешения пользователя.

## Completion contract

Завершение задачи требует по порядку: успешной primary verification и нового verdict
Sol `ship`.

Если publication не запрашивалась и это managed Git task с существующей task-overlay
записью и явно non-read-only режимом, зафиксируй terminal outcome штатной командой
`python3 "$HOME/.codex/skills/agent-flow/scripts/task-overlay.py" finish --repo <repo> --task-id <task-id> --status done --completion-reason no-publication-requested`. Затем штатный helper сам пытается доказать disposable или equivalent sandbox: удаляет его только при proof, иначе автоматически сохраняет retained task overlay с reason code. Это безопасный завершённый исход, не ручное действие пользователя.

Для read-only, non-Git задач и задач без существующей task-overlay записи lifecycle-мутация
не требуется и не предлагается: зафиксируй безопасный no-op/reporting outcome, описав
результат проверки и отсутствие lifecycle-действия.

Для запрошенной publication требуются доказанные gate из `verified_push.py check` и
требуемая авторизация перед `execute`; `task-overlay cleanup-published` допустим только
после подтверждённой publication. Не обещай безусловное удаление и не используй
`rm -rf` или force push.

При mismatch, dirty state или неполном proof не объявляй completion: выполни repair,
либо retained task overlay до получения доказательств.
