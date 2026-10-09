# 外置 Bridge 与薄客户端

需要 Python 3（仅标准库）和已安装、已配置的 `agent-bridge/v1` 外置 CLI。
插件不包含或自动安装 Bridge、引擎、MCP server、凭据或任务服务。
`AGENT_BRIDGE_BIN` 可由用户受控环境指定单个可执行文件路径；没有 shell
命令、任意 executor 或可执行 hook 参数。配置使用 CLI `--config` 或受控
`AGENT_BRIDGE_CONFIG`；caller 用 `--caller-ref` 或 `AGENT_BRIDGE_CALLER_REF`。
caller 必须来自已有可信宿主绑定，不能为了通过 preflight 编造。

包内 [tools/bridge_client.py](../../../tools/bridge_client.py) 负责结构化 argv、
通过 stdin 传递 spec/message、API/operation/requestId 检查、错误传递和最小 receipt。
源码测试使用 scripts 同文件；入包后从稳定插件目录调用 tools 路径。
不拼接 shell，不修改权限，不持有任务状态，不自动重试或换目标。
客户端读取调用者提供的 spec/message 文件后，以结构化 argv 中的
`--spec-file -` 或 `--message-file -` 和 subprocess stdin 发送给外置 Bridge。
不会创建控制输入临时文件，因此宿主临时目录回落当前项目时也不会造成
`DIRTY_SOURCE`。外置 CLI 必须支持该 stdin 契约；不支持时直接保留错误，
不回退到临时文件或自动重试。receipt 仍按已声明路径原子写入。

以下命令在插件发行目录运行。输入路径由调用工具以结构化 argv 传递；不要
把自然语言、用户路径或 `$()` 等内容插入 shell 字符串。所有操作输出 JSON。

```sh
python3 -B tools/bridge_client.py --caller-ref caller-id engine list
python3 -B tools/bridge_client.py --caller-ref caller-id preflight --engine claude-code --project project-id --spec-file spec.json
python3 -B tools/bridge_client.py --caller-ref caller-id task start --engine claude-code --caller-engine codex --project project-id --spec-file spec.json --intent-file intent.json --request-id handoff-id --receipt-file receipt.json
python3 -B tools/bridge_client.py --caller-ref caller-id task get task-id --receipt-file receipt.json
python3 -B tools/bridge_client.py --caller-ref caller-id task list
python3 -B tools/bridge_client.py --caller-ref caller-id task watch task-id --cursor event-cursor --wait-ms 10000
python3 -B tools/bridge_client.py --caller-ref caller-id artifact list --task task-id
python3 -B tools/bridge_client.py --caller-ref caller-id artifact read result-id --task task-id --offset 0 --limit 8192
python3 -B tools/bridge_client.py --caller-ref caller-id task continue task-id --message-file follow-up.txt --request-id continuation-id
python3 -B tools/bridge_client.py --caller-ref caller-id task cancel task-id --request-id cancel-id
```

start 的 intent.json 格式见[交接契约](handoff-contract.md)。queued 响应不会
提前有 sessionId；receipt 记录 null，后续 get --receipt-file 补录同任务的
真实 sessionId。也可调用 Python BridgeClient.refresh_receipt(path)，该方法
仅查询回执中的准确 taskId。已有 sessionId 不能切换为另一个 session。
自然语言识别
由宿主技能核对当前用户上下文；CLI 不尝试用 NLP 证明用户身份。同 engine
时，当前用户明确要求独立会话才在 start 上添加 `--independent-session`。
start 内部先做同目标 preflight；展示或单独 preflight 不创建任务。
默认 workspacePolicy 由 Bridge 选择 isolated；仅用户需要现有工作区且符合
项目约束时给 preflight/start 同时添加 `--workspace-policy existing`。该字段只在外层 CLI，
不能写入 TaskSpec，更不能借此扩大权限或覆盖其他人的已有改动。

直接调用外置 Bridge CLI 是另一明确入口，它不要求先经过本客户端；API 与
权限判定仍归同一 Bridge 服务。客户端不会篡改 TaskSpec 为通过验证。

stdout 是完整 JSON `{apiVersion, operation, requestId?, data}` 或
`{apiVersion, operation, requestId?, error:{code,message,executionDisposition?}}`。
exit 0 表示操作成功，查询到任务 failed 仍是成功查询；exit 2 表示预期拒绝，
exit 1 表示系统/连接/版本/JSON 错误。不要把这些退出码与任务终态混用。
非法 stdout 和 stderr 不回显，避免意外输出凭据。

Bridge 响应超时/身份不匹配/非法 JSON 时，不能假定写操作没有启动。
先 task list/get 查归属任务，以同一 requestId 恢复；客户端绝不盲目重试。
receipt 写入失败明确报告已 start，查询同 requestId，不能重新生成任务。
receipt 仅存请求与任务绑定；存在其他绑定的 receipt 或符号链接不会覆盖。
POSIX 回执写入使用同目录私有 `.回执文件名.agent-bridge-lock` 跨进程互斥，
归属检查与原子发布均在锁内。锁文件保留，进程退出后内核释放锁，不按PID
清理；繁忙、冲突或不安全锁返回上述回执失败，先按原requestId对账。
当前未声明 Windows 原生 Bridge 执行或回执写入支持。
该文件不保存目标描述、凭据、原始输出或授权 flag，也不是人类证明。

get/watch/continue/cancel 必须使用准确 taskId。Bridge 核对 caller 归属与准确
session，禁止 `--last` 或“最近会话”；续接使用新写操作 requestId，发生同一
续接请求的网络重试时复用该 ID。artifact read 只能读取登记产物，不提供
任意文件路径。取消返回后继续查询实际终态。
