# 共享数据库 Review 样例

[English](README.md) | 简体中文

这是匿名的 Python 标准库内部评估样例。只在 `evals/prepare.py` 生成的临时副本
运行；需要 Python 3.11+ 与 SQLite，不访问账号、宿主或外部服务。

## 业务要求与执行模型

多个应用实例服务请求，共享同一个数据库，每个请求使用独立连接。调度可以在
SQL 语句之间切换请求。`registry.register` 在同一事务提交登记和 pending
发件箱记录。`find_registration` 是写事务外可选的预查询；查不到不代表占有键。
对于 `(tenant_id, request_key)`，首个提交的登记生效：并发或重复调用返回同一
ID、保留首个 payload，并只留下一个持久投递意图。不同租户的相同请求键互不
影响。当前未提供要求串行化无关键的业务约束。

已接受的登记和投递意图必须跨进程重启保留，直到投递结果明确。样例提供 schema
与登记实现，没有实现投递 worker 或外部接收方。外部调用可能在接收方已提交后
超时。接收方幂等行为、延迟分布和生产争用率尚未确认。`proposal.md` 是候选
方案，不是已实现或批准的契约。

计数器有独立要求：每个成功的 `increment` 加一，两个成功请求应将 10 变为 12。
`counter_before.py` 为旧实现，`counter_after.py` 为候选重构，`counter.diff`
展示真实源码改动。在此 SQLite 连接模型中，读取不会启动写事务，`write_value`
单独提交事务；候选实现的 helper 允许在真实读写边界暂停并重放。

## 检查与重放

按当前场景阅读 `schema.sql`、`registry.py`、两版计数器及方案。在已准备的
`workspace` 中运行：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B exercise.py
```

`exercise.py` 对全新临时数据库建立两个独立连接，按固定语句顺序重放，并输出
实际持久结果。不使用 sleep、概率竞争或远端依赖。退出后删除数据库，源码
不变。命令只证明本地 SQL 样例和一种可达交错，不证明生产吞吐、锁公平性、
worker 恢复或模型行为。保留源码哈希、原始输出与真实 Agent 会话作为独立证据，
不能从此命令推导宿主验收通过。
