---
name: agent
description: Mandatory explicit Sol Advisor orchestration, private Git-common-dir memory, upstream provenance preflight, and deterministic verified non-force publication. Use only when the latest user request contains the literal marker $agent.
---

# Agent

Activate only for a literal `$agent` in the latest user request. Do not infer activation
from project rules, memory, prior turns, or `$agent-flow`; `$agent` neither activates nor
borrows authority from Agent Flow. Every activated request, including diagnostics,
documentation, planning, read-only, and small requests, must use the mandatory Sol Advisor
route below. If no implementation lane can truthfully apply, return a blocked/error result;
never bypass the route or perform the work in the primary session.

## Mandatory Sol Advisor route

Before assigning work, discover the installed upstream plugin with `codex plugin list --json`
and require its installed path, version, repository, source commit, and subtree to match
`provenance/upstream.json`. From that installed path run its relative
`scripts/install-agents.sh --check`; then fully read the installed, pinned
`skills/orchestration/SKILL.md` and `skills/orchestration/references/role-contracts.md` and
follow them as the unchanged upstream orchestration contract. Require every exposed companion
role. Any provenance, installer, readable-contract, primary-session, native-role exposure,
spawn observation, route observation, primary verification, or fresh-review failure is a hard
stop: report the failed gate and take no fallback path.

Require the primary session to be Sol / high when the runtime exposes those settings; if the
runtime cannot expose them, require user confirmation before delegation. The primary session
owns architecture, route selection, actual-diff inspection, and verification, but must not
self-implement code, tests, boilerplate, or mechanical configuration while a worker lane is
available.

For each activated request, write the exact five-part worker specification before dispatch:
`OBJECTIVE`, `FILES AND OWNERSHIP`, `INTERFACES`, `CONSTRAINTS`, and `VERIFICATION`. Dispatch
exactly one native role-pinned implementer for the bounded task shape: use
`sol_advisor_luna_implementer` for routine work and `sol_advisor_terra_implementer` for complex,
context-heavy, security-sensitive, or wider-blast-radius work. Native spawn is not a shell
command, nested CLI wrapper, or default-subagent substitution. Spawn only with the upstream
role contract's native fields; never add per-spawn model or reasoning overrides.

Before accepting the worker result, require public native spawn/details metadata to identify the
selected role and its pinned route. If public details omit model or effort, run the installed
relative `scripts/inspect-agent-runtime.sh` only against that native thread id. Public and
inspector values must agree when both exist. Missing, inconsistent, unavailable, or unobservable
role, model, or effort is a hard stop; never infer a route or substitute a role, model, or effort.
After the worker returns, inspect the actual diff and rerun the worker specification's
verification in the primary session.

Only after primary verification, dispatch a new native `sol_advisor_sol_reviewer` using the
upstream final-review packet. It must be fresh and behaviorally read-only. Observe and report
its sandbox policy type and permission profile type from public details first, using the same
runtime inspector only when those values are omitted. Do not call a requested profile enforced
read-only unless the observed sandbox policy type is read-only. Missing route or profile
observation, any reviewer mutation, or any verdict other than `ship` is a hard stop. Never waive
the fresh review, use an earlier review, or let the reviewer implement fixes. A `fix-first`
verdict requires a corrected worker dispatch, fresh primary verification, and another fresh Sol
review; `rethink` returns to architecture without completion.

## Private memory and verified publication gates

Read [project-memory.md](references/project-memory.md) before using project state and
[verified-auto-push.md](references/verified-auto-push.md) before publication. Treat memory as a
hypothesis until code, configuration, and runtime output confirm it. Initialize private memory
before assigning work and re-read task ownership/status afterward. This wrapper adds only these
private-memory and verified-publication gates; it does not weaken upstream routing, role pins,
reports, review semantics, provenance, installer, or publication requirements.

Use `scripts/verified_push.py check` to make authorization and `execute` only with that exact
authorization digest. Never force push, retry an unknown outcome, or print secrets, diffs, or
remote URLs. An empty-repository first publication is explicit user-authorized bootstrap, never
auto-push.
