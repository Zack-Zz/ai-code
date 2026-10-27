# Registration protection proposal

English | [简体中文](#中文)

This is a design submitted for review. The current implementation remains
`registry.py` and `schema.sql`; proposed components below do not exist yet.

1. Before registration, acquire a distributed lease keyed by tenant and request
   key with a fixed 30-second expiry; release it in `finally`. The proposed
   reason is to avoid duplicate SQL work during bursts. Traffic and contention
   measurements are not yet available. The current unique constraint remains.
2. Keep registration and pending outbox insertion in the existing transaction.
   Retry the whole transaction at most three times only for a database busy
   error, rolling back each failed attempt. Backoff and an overall request
   deadline remain to be specified. The database enforces identity; the lease
   is also described as preventing every duplicate registration.
3. Add a worker to scan pending outbox rows after startup and periodically.
   Workers claim work with a conditional update and an expiring claim token;
   only the current token may acknowledge completion. This is intended to
   recover work after crashes. Claim schema and transaction boundaries need a
   separate implementation design. Sending remains outside a database
   transaction. The receiver is sent the registration ID as an idempotency key,
   but its key retention and deduplication contract have not been checked.
4. Retry remote transport errors and timeouts up to three times. If all attempts
   time out, compensate by deleting the registration and its outbox row in one
   transaction so the caller can submit the same request key again. Completed
   remote calls are not queried during compensation. No cancellation API has
   been supplied. This is described as restoring the state before registration.

Review the responsibilities and interactions against the supplied requirements,
code and execution model. Record required facts that are still missing, relevant
correctness/reliability/maintenance costs, and proportionate next steps. A design
review does not authorize implementation.

## 中文

[English](#registration-protection-proposal) | 简体中文

这是待 Review 的设计。当前实现仍是 `registry.py` 与 `schema.sql`；下列新增
组件尚不存在。

1. 登记前按租户和请求键获取分布式租约，固定 30 秒过期，在 `finally` 中释放。
   理由是减少突发流量下重复 SQL 工作；目前没有流量或争用测量。保留现有唯一
   约束。同时将租约描述为防止一切重复登记。
2. 保留现有登记和 pending 发件箱插入事务。只在数据库 busy 错误时重试整个
   事务，最多三次，每次失败先回滚。退避和请求总截止时间尚待确定。数据库
   负责保证身份唯一。
3. 新增 worker，在启动后及周期性扫描 pending 发件箱。通过条件更新和可过期
   claim token 认领，只有当前 token 可确认完成，目的是崩溃后恢复。claim
   schema 和事务边界需要单独设计；发送不处于数据库事务中。以登记 ID 作为
   接收方幂等键，但尚未核实接收方的键保留和去重契约。
4. 远端传输错误和超时最多重试三次。全部超时后，以同一事务删除登记和发件箱
   作为补偿，让调用方能再次使用原请求键。补偿时不查询远端完成状态，当前
   没有取消 API；方案将其描述为恢复到登记前状态。

依据所给需求、源码和执行模型审查各层职责与交互。记录缺失的关键事实、正确性/
可靠性/维护成本及相称的下一步。设计 Review 不授予实施权限。
