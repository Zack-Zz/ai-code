# 使用 CodeVow

[English](usage.md) | 简体中文

完成[安装](../../../docs/installation.zh-CN.md)后，开启新宿主会话，说明目标、
修改范围和验收条件。CodeVow 围绕这个请求组织计划、TDD、排查、审查和验证。

## 日常工作流

- 解释或调查类问题：读取相关证据后回答，不自动开始实现。
- 开发任务：提出与任务规模相称的计划，确认范围。
- 行为变更：先写有意义的失败测试，再实现，在通过的基线下重构。
- 问题排查：通过明确假设和小范围实验定位原因。
- 代码审查：聚焦受影响风险；关键风险或配置为 `review_level=all` 时尝试独立审查。
- 交付：说明最终代码状态、实际检查、发现的问题和剩余工作；代码变更后重新验证。

默认 `collaborative` 模式确认计划后实施；`continuous` 在已授权范围内持续
推进。两种模式都保留既有改动，Git 操作、安装和对外发布仍需要你明确授权。
策略文件和任务记录不会产生权限。

## 项目策略

在 `<项目>/.ai-workflow/policy.json` 保存偏好：

```json
{
  "schema_version": 1,
  "mode": "collaborative",
  "review_level": "critical",
  "max_parallel_tasks": 2,
  "response_language": "zh-CN",
  "verification_notes": ["交付前运行相关测试"]
}
```

| 字段 | 可选值与作用 |
|---|---|
| `mode` | `collaborative` 或 `continuous`，控制协作节奏 |
| `review_level` | `critical` 或 `all`，决定何时尝试独立审查 |
| `max_parallel_tasks` | 1–8 的整数，限制同时进行的子任务数 |
| `response_language` | `auto` 或 `zh-CN`、`en` 等语言标签 |
| `verification_notes` | 最多 16 条简短的项目验证要求 |

`schema_version` 必须为 `1`，其他字段可省略。生效顺序为所选随包策略、
项目配置、你在当前会话明确给出的选项。配置无效或含未知字段时会报错，
修正后再继续依赖它的工作。字段说明见[策略 Schema](../schemas/policy.schema.json)。

## 查看生效配置

以下命令均从 CodeVow 安装包根目录执行，将 `/path/to/project` 替换为实际
工作区。可选工具需要 Python 3.11+，Markdown 技能本身不依赖 Python。

```sh
python3 tools/workflow_tool.py policy resolve \
  --plugin-root . --workspace /path/to/project
```

结果包含生效值、各字段来源和策略哈希。可以为当前任务明确传入选项：

```sh
python3 tools/workflow_tool.py policy resolve \
  --plugin-root . --workspace /path/to/project \
  --mode continuous --review-level all --response-language zh-CN \
  --verification-note "交付前运行相关测试"
```

解析只读，不保存设置，也不授权实施。全部选项见
`python3 tools/workflow_tool.py policy resolve --help`。

## 可选任务与证据记录

长期任务或交接可复制并修改[任务输入模板](../templates/task.json)。
填写实际计划、需要保护的路径和授权来源；工具记录这些引用，不会证明或产生权限。

先预览创建：

```sh
python3 tools/workflow_tool.py task create \
  --workspace /path/to/project --id my-task --input /path/to/task-input.json
```

在该命令添加 `--apply` 才保存记录。记录位于
`<项目>/.ai-workflow/tasks/<id>/`。检查记录和证据：

```sh
python3 tools/workflow_tool.py task check --workspace /path/to/project --id my-task
```

更新时使用 `task.json` 中当前的 `record_revision`，输入文件遵循
[任务 Schema](../schemas/task.schema.json)：

```sh
python3 tools/workflow_tool.py task update \
  --workspace /path/to/project --id my-task \
  --expected-revision <current-revision> --input /path/to/update.json
```

将 `<current-revision>` 替换为实际整数。更新默认也只预览，添加 `--apply`
才写入；版本冲突时先读取当前记录再重试。[证据模板](../templates/evidence.json)
说明证据输入。`task check` 会识别证据、文件或工作区身份变化，不沿用过期通过结果。

## 可选项目文件暂存

暂存创建工作区内的插件副本，原生安装不需要这一步。文件暂存需要支持 POSIX
文件操作的平台。

生成计划：

```sh
python3 tools/workflow_tool.py files plan \
  --package . --target /path/to/project --action stage --out /tmp/codevow-plan.json
```

此命令只写计划文件。阅读计划和返回的 `plan_hash`，确认后应用：

```sh
python3 tools/workflow_tool.py files apply \
  --plan /tmp/codevow-plan.json --expected-plan-hash <plan-hash>
```

将 `<plan-hash>` 替换为返回的哈希。副本位于
`<项目>/.ai-workflow/staged/ai-code-workflow/`，所有权记录位于
`<项目>/.ai-workflow/receipts/ai-code-workflow.json`。
更新副本时，用新包运行 `files plan --action update`。
移除时，运行
`files plan --target /path/to/project --action remove --out /tmp/codevow-plan.json`，
再阅读并应用该计划。

更新和移除拒绝覆盖或删除你已编辑的文件。中断时保留恢复材料；应用期间避免
并发编辑，出现冲突先检查原因。暂存不会注册宿主插件，宿主插件更新也不会
自动更新暂存副本。

工具不联网、不调用模型、不执行项目命令或 Git 操作。
命令索引见 `python3 tools/workflow_tool.py --help`。
