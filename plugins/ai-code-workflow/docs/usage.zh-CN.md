# 使用 CodeVow

[English](usage.md) | 简体中文

完成[安装](../../../docs/installation.zh-CN.md)后，开启新宿主会话，说明目标、
修改范围和验收条件。CodeVow 围绕这个请求组织计划、TDD、排查、审查和验证。

## 选择协作模式

模式决定助手在动手修改前是否等待你确认方案。根据你希望的工作方式选择：

| 模式 | 如何开始工作 | 适合什么时候用 |
|---|---|---|
| `collaborative` — 协作模式（默认） | 助手先调查、说明准备怎么改，等你确认方案后再动手修改。 | 你希望先看过方案，再开始实施。 |
| `continuous` — 连续执行模式 | 你明确要求实施任务后，助手简要说明计划，就在你授权的范围内继续完成。 | 目标和范围已经清楚，你希望助手直接推进到交付。 |

例如，你说：“修复登录超时，只修改认证模块，并运行相关测试。”

- `collaborative`：助手调查后说明修复方案，等你确认，再开始修改。
- `continuous`：助手调查并简要说明计划后，就在你限定的范围内完成修复和测试。

进入实施后，两种模式都会持续完成编码、测试和审查，无需你逐步批准普通操作。
已经确认过的方案会直接复用；范围或关键方案发生实质变化时，助手会就变动部分
重新确认。

两种模式的测试、审查和验证要求相同，都会保留你已有的改动。
仅询问或要求排查时，助手保持只读；已授权任务中的后续问句不会取消你已经
允许的工作。提交、推送、打标签、合并、创建 PR、安装和对外发布仍需要你
明确要求；切换模式或写入任务记录不会代替你的授权。

在[项目策略](#项目策略)中设置默认模式，也可以在会话里告诉助手本次使用哪种
模式。仅说“使用 continuous”不会让助手开始修改，还需要说明要实施的任务和
修改范围。

## 接入项目入口

技能 description 帮助宿主选用 CodeVow 技能。安装和这些描述不保证宿主在每个
请求前先读取 `workflow`。编程相关任务需要常驻入口时，使用宿主实际提供且
你已核对加载方式的项目指令入口，由你主动添加简短的路由指令，例如：

```text
对于本项目的编程相关任务，先加载已安装的 CodeVow workflow 技能，判定任务类型，
并核对真实用户会话中的授权。
没有开发授权时，询问、排查和独立审查默认只读；确认缺陷不代表允许写测试、
诊断文件或修复。已授权开发中的后续问句不撤销授权；明确停止和范围限制仍有效。
collaborative 模式先展示改动说明，等待适用确认；已有确认覆盖当前范围时复用。
在已确认范围内持续推进；continuous 模式不会新增授权。
常驻入口保持简短，只按当前节点需要加载其他技能正文，并复用有效上下文。
workflow 无法加载时，先告知用户并保持只读。
```

常驻入口与具体技能正文分开。工作流规则只维护在[技能](../skills/workflow/SKILL.md)
中；此片段负责路由，无需将完整工作流复制进项目指令。只读取当前节点需要的
技能和引用资料，复用有效上下文，不要求每个请求加载全部六个技能。

请使用宿主实际提供的项目指令入口，先核对它在当前会话中的加载方式；此片段
仅供你主动接入。CodeVow 不会静默修改已有 `AGENTS.md`、`CLAUDE.md` 或宿主
设置。此片段不依赖固定安装缓存路径，也不声称随包 `AGENTS.md` 自动生效。
具体接入位置及其加载
行为仍需在你的实际宿主会话中验证。

核对入口加载时，可以明确请求：“加载已安装的 CodeVow workflow 技能，告诉我
是否能读取；本次检查保持只读。”加载成功只证明当前会话可访问，不能证明未来
每个请求都会自动路由或遵循。加载失败时，助手应先告知并保持只读，不应假装
CodeVow 已启用。

## 日常工作流

- 没有开发授权时，询问、排查和独立审查默认只读；发现或确认缺陷不代表允许
  写测试、诊断文件或修复。已授权开发中的后续问句不撤销授权；明确停止和
  范围限制仍有效。
- 开发任务：按[所选模式](#选择协作模式)说明计划并开始实施。
- 行为变更：先写有意义的失败测试，再实现，在通过的基线下重构。
- 问题排查：通过明确假设和小范围实验定位原因。
- 代码审查：聚焦受影响风险；关键风险或配置为 `review_level=all` 时尝试独立审查。
- 交付：说明最终代码状态、实际检查、发现的问题和剩余工作；代码变更后重新验证。

## 与子智能体协作

CodeVow 在宿主已有的智能体能力上补充简短协作提醒。助手根据任务依赖、写入
重叠和实际交付收益选择串行或并行，并遵守你的要求和宿主限制。

- 两个独立模块的接口已经明确时，可以并行实现，再整合并检查组合后的结果。
- 共享接口尚未确定时，先明确接口再进行依赖它的实现；无关工作可以继续推进。

委派时交代必要上下文、明确的修改范围和预期结果。共享工作区中的重叠写入
需要协调，并保留他人的修改。独立工作区可以分别产生候选补丁，再统一整合，
但仍可能共享数据库或端口等资源。接管中断的工作前，先检查实际状态和已有
改动。主助手核实返回的产物和整合后的结果；各部分测试通过不等于完整变更
已经可用。

`max_parallel_tasks` 是上限，不是目标人数。调度、权限和隔离由宿主提供；
CodeVow 不强制建立代理流水线、worktree 或任务记录。原有授权和审查规则
继续适用。

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
| `mode` | `collaborative`（先确认方案再修改，默认）或 `continuous`（在你授权的任务范围内直接推进），见[模式选择](#选择协作模式) |
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
