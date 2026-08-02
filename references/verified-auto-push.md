# Verified automatic push

Use only for an existing tracking upstream and one local task commit ahead of it. Policy is
fail-closed: workstation policy is required; a project policy may only restrict it; a fresh user
veto always wins. Require clean index/worktree, exact owned-path attribution, passed checks,
secret-scan and attribution evidence, candidate-bound patch digest, fresh-veto evidence, and a
fresh reviewer verdict exactly `ship`.

Run `verified_push.py check` first. It writes a unique mode-0600 canonical authorization and emits
only canonical JSON containing `authorization`, `sha256`, and `attempt`, without pushing. Then run
`execute` with that exact path and digest. Execute re-validates every byte, policy,
candidate, upstream and remote/ref identity, pushes only the exact non-force refspec, verifies the
exact remote OID with `ls-remote --refs`, and writes a redacted strict-schema receipt. A started
journal is reconciled before transport: remote candidate becomes success, remote base consumes
that authorization as absent, and a divergent or unavailable result becomes terminal unknown.
The helper requires exactly one configured push URL. It stores only its SHA-256 and captures the
exact endpoint again immediately before the started journal. Every live base check uses that
endpoint; transport is exactly `git push -- <captured-endpoint> <candidate>:<ref>`, where `--`
ends option parsing and the captured endpoint appears once; then
same-process reconciliation reuses the same in-memory endpoint without rereading configuration.
Restarted recovery resolves the endpoint anew; missing, multiple, or hash-drifted configuration
becomes terminal unknown without querying or transporting to the new endpoint.
Authorization expiry blocks transport that has not started. It does not block strict validation
of an existing success receipt or reconciliation of an immutable started journal. Those recovery
paths never push: they revalidate current local bindings, policy, evidence bytes and remote
identity. The authorization binds evidence that was fresh before transport; recovery may accept
its now-stale veto timestamp solely to determine the already-started outcome.

Evidence schema v1 binds candidate and raw-binary patch digest to nonempty check digests,
structured secret scan, exact attribution paths, QA `pass`, reviewer `ship`, and fresh-veto
`clear`. The helper records only digests, not remote URLs. It verifies live `ls-remote` base
before check and execute. A failed push is reconciled identically. After attempt 1 is proven
absent, a fresh `check` may issue immutable attempt 2; the consumed authorization never transports
again, a third authorization is refused, and terminal unknown forbids every retry.
