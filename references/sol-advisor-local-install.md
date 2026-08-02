# Local Sol Advisor installation

Этот fork использует одноразовую локальную установку role templates до запуска новой
задачи Codex. Runtime `SKILL.md` не ищет plugin, не проверяет provenance и не запускает
installer: он сразу выбирает exact native Luna или Terra role. Отсутствующая native role
— ошибка без fallback.

Из корня fork выполните:

```sh
sh scripts/install-sol-advisor.sh
sh scripts/install-sol-advisor.sh --check
```

По умолчанию target — `$CODEX_HOME/agents`, если задан `CODEX_HOME`; иначе
`$HOME/.codex/agents`. Для изолированной проверки можно указать отдельный target:

```sh
sh scripts/install-sol-advisor.sh --target-dir /path/to/agents
```

Installer добавляет только отсутствующие файлы. Если destination существует и отличается
от vendored template, он завершится ошибкой и не перезапишет этот файл. После успешной
установки начните fresh Codex task, чтобы native runtime обнаружил роли.
