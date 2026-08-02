---
name: agent
description: Explicit project orchestration, private Git-common-dir memory, upstream Sol Advisor preflight, and deterministic verified non-force publication. Use only when the latest user request contains the literal marker $agent.
---

# Agent

Activate only for a literal `$agent` in the latest user request. Do not infer activation
from project rules, memory, prior turns, or `$agent-flow`; `$agent` neither activates nor
borrows authority from Agent Flow.

Before delegation, discover the installed upstream plugin with `codex plugin list --json` and
require its installed path, version, repository, source commit, and subtree to match
`provenance/upstream.json`. From that installed path run its relative
`scripts/install-agents.sh --check`; then fully read the installed, pinned
`skills/orchestration/SKILL.md` and `skills/orchestration/references/role-contracts.md` and follow
them as the unchanged upstream orchestration contract. Require every exposed companion role.
Never substitute a missing role or silently fall back. Require a fresh Sol reviewer and preserve
its observed sandbox/permission profile. Any provenance, installer, role, or readable-contract
failure stops orchestration.

Read [project-memory.md](references/project-memory.md) before using project state and
[verified-auto-push.md](references/verified-auto-push.md) before publication. Treat memory
as a hypothesis until code, configuration, and runtime output confirm it. Use
`scripts/verified_push.py check` to make authorization and `execute` only with that exact
authorization digest. Never force push, retry an unknown outcome, or print secrets, diffs,
or remote URLs.

This wrapper adds only the private-memory and verified-publication gates below; it does not alter
upstream routing, role pins, reports, or review semantics. Write five-part worker specifications
(objective, ownership, interfaces, constraints,
verification), inspect the actual diff in the primary session, and require a fresh Sol review.
Initialize private memory before assigning work and re-read task ownership/status afterward.
An empty-repository first publication is explicit user-authorized bootstrap, never auto-push.
