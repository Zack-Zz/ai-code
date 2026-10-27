# Shared database review fixture

English | [简体中文](README.zh-CN.md)

This anonymous Python standard-library fixture is internal evaluation material.
Run only in the temporary copy produced by `evals/prepare.py`; it needs Python
3.11+ and SQLite, and accesses no accounts, hosts or external services.

## Requirements and execution model

Several application instances serve requests against one database. Each request
has its own connection. The scheduler can switch requests between SQL statements.
`registry.register` commits registration and its pending outbox row together.
`find_registration` is an optional preflight outside that write transaction; a
missing preflight result does not reserve a key. For `(tenant_id, request_key)`,
the first committed registration wins: concurrent or repeated calls return its
ID, preserve its payload and leave one durable delivery intent. The same request
key in a different tenant is independent. No requirement to serialize unrelated
keys has been supplied.

An accepted registration and delivery intent must survive process restarts until
delivery is resolved. The schema and registration implementation are provided;
no delivery worker or external receiver is implemented. The external call may
time out after the receiver has committed. The receiver's idempotency behavior,
latency distribution and production contention rate have not been established.
`proposal.md` is a candidate design, not an implemented or approved contract.

The counter requirement is separate: every successful `increment` adds one;
two successful requests from 10 must leave 12. `counter_before.py` is the previous
implementation; `counter_after.py` is a proposed refactor and `counter.diff`
shows the actual source change. Reads do not start a write transaction in this
SQLite connection model, and `write_value` commits its own transaction. The
refactor's helpers let the replay pause at its real read/write boundary.

## Inspect and replay

Read `schema.sql`, `registry.py`, both counter versions and the proposal as
needed for the assigned case. In a prepared `workspace` run:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B exercise.py
```

`exercise.py` opens two independent connections to a fresh temporary database,
replays fixed statement ordering and prints actual persisted results. There are
no sleeps, probability-based races or remote dependencies. The database is removed
on exit; source files remain unchanged. This proves the local SQL examples and
one reachable ordering, not production throughput, lock fairness, worker recovery
or agent behavior. Keep source hashes, raw output and the real agent transcript
as separate evidence. Do not infer host acceptance from this command.
