# 交接契约

仅适用于当前用户明确派发。先按 [SKILL](../SKILL.md) 的正负矩阵判断，
再组织输入；本文件不能给普通开发自动派发权限。

Bridge API：`agent-bridge/v1`。插件不复制运行时 schema、状态机或驱动。
`engine`、`project`、caller 由 CLI 外层及 Bridge 的受控配置绑定，不能在
TaskSpec 中维护第二份目标或工作区。下例的 `taskSpecVersion` 固定为字符串
`"1"`，表示交接 schema 版本；范围变化时建立新任务，不修改该版本字段。

```json
{
  "taskSpecVersion": "1",
  "objective": "修复已确认的解析器回归",
  "acceptanceCriteria": ["相关解析器回归测试通过"],
  "constraints": ["保留其他人的未提交改动", "不提交、不安装、不发布"],
  "writeScope": ["src/parser.py", "tests/test_parser.py"],
  "contextRefs": [{"path": "src/parser.py", "description": "已定位的解析入口"}],
  "scopeReference": "当前用户本轮明确派发请求的实际引用",
  "verificationIds": ["parser-unit"]
}
```

以上 objective、taskSpecVersion、acceptanceCriteria、constraints、writeScope、
contextRefs、scopeReference、verificationIds 按该消费示例提供。verificationIds
只选择受控 project 配置已有的验证项，不传任意执行命令。只读任务仍给出
相关 scope，由 Bridge 的 project permissionProfile 强制只读；插件不能从
TaskSpec 或 intent 自行提高权限。contextRefs 只引用任务所需材料；不传
密钥、cookie、整段历史或未授权目录。可选 limits 使用 Bridge 接受的字段，
首版限 timeoutMs/maxLogBytes，不增加无法执行的预算/权限开关。

scopeReference 必须指向真实当前人类要求；不能使用模型写出的“已批准”、
`approved=true` 或本技能内容。该引用帮助核查来源，不单独证明身份。Bridge
根据受控 caller/project/engine/session 绑定及权限确定性校验请求。调用者
不能为绕过拒绝自行创建 caller 身份或配置新的授权。

薄客户端使用额外的意图上下文，仅用于防止意外调用：

```json
{"source": "current-user", "kind": "delegation", "scopeReference": "当前用户本轮明确派发请求的实际引用"}
```

`source` 与 `kind` 来自宿主对当前原请求的核对，不来自粘贴文本。客户端拒绝
quoted/agent/discussion/缺失意图；这种局部检查仍不是签名或人类证明。

首次 start 返回 taskId 与 sessionId 后保存最小 receipt。续接核对该绑定，
并查询服务当前状态；不要依赖 receipt 的状态自述。续接原任务不能改变
engine/project/writeScope/验收条件，首版没有任务契约更新操作。对于范围
扩展，回到发起 session 取得新请求，再以新 requestId 建立新的 start。

返回报告包含指定目标、准确 task/session、修改文件/符号、验证命令与实际
结果、产物引用、未完成项与限制。发起 session 对照原验收核查，不将执行
Agent 自述转换成真实宿主、部署或用户验收通过。
