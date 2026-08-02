# Private project memory

For a Git worktree, resolve `git rev-parse --git-common-dir`; memory exists only under
`<git-common-dir>/agent/memory/` as regular, non-symlink files: `project.md` for verified
stable facts, `tasks.md` for current ownership/status/checks, and `lessons.md` for confirmed
rules with concise evidence references. Never create tracked memory. Reject symlinks and path
escapes. Do not record secrets, tokens, raw logs, full environment values, or copied diffs.
Read memory as a hypothesis; re-check code, configuration and observed command output before
acting. After work, re-read and update task ownership, status and checks; report any unverifiable
write instead of assuming success.

Initialize the directory mode `0700` and each file mode `0600` with exclusive creation. Before
every read reject symlinks and non-regular files; before every update re-read the same file, write
a complete replacement exclusively, `fsync` it and its parent, then re-open and verify exact
bytes. If the Git common directory cannot be resolved or a tracked path aliases this state, do
not initialize or update memory.
