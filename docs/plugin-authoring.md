# 接入一个 AI 插件

本指南适用于在 ai-code 仓库加入独立的 AI 相关插件。先定义插件用途、最小
内容和实际目标宿主，再注册目录。已有 workflow 只是一个插件实例；新插件
不必包含它的策略、任务记录、Reviewer 或六份技能。

所有命令在仓库根运行。维护规则见 [AGENTS.md](../AGENTS.md)，公共字段和
发行索引见 [多插件规格](design/2026-10-07-multi-plugin-design.md)。

## 1. 建立独立源码目录

一个只有单份技能、面向 Codex 的最小例子：

```text
plugins/ai-example/
  product.json
  README.md
  AGENTS.md
  LICENSE
  skills/example/SKILL.md
  adapters/codex/plugin.json
  adapters/codex/interfaces.json
  tests/
```

`ai-example` 仅为指南占位符，不是已提供的正式插件。实际 ID 使用小写
kebab-case，建议目录名与 ID 一致。每个插件自有版本、许可证与说明，不将兄弟
插件的相对路径列入资源。README 要说明用途、依赖、支持状态和验证边界。

## 2. 声明身份、宿主和资源

`product.json`：

```json
{
  "schema_version": 1,
  "product_id": "ai-example",
  "display_name": "AI Example",
  "version": "0.1.0",
  "repository": "https://github.com/Zack-Zz/ai-code",
  "license": "MIT",
  "hosts": ["codex"],
  "core_skills": ["example"],
  "shared_skills": [],
  "resources": [
    {"source": "LICENSE", "target": "LICENSE", "include": []}
  ]
}
```

身份、版本和白名单只写在该清单。不要在 catalog、根 package.json 或市场
中维护第二份版本。`hosts` 必填且非空，当前接受 `codex`、`zcode`；每个声明
宿主都必须有真实 `adapters/<host>/plugin.json`。

声明的技能自动贡献其 `skills/<name>/SKILL.md`。技能引用的参考文档、脚本
和额外资源需登记到 resources。例如：

```json
{"source": "skills/example/references", "target": "skills/example/references", "include": ["guide.md"]}
```

source 是文件时 include 必须为 `[]`；source 是目录时 include 必须逐个列出
相对文件名。不要使用通配符或自动递归打包。文件必须真实存在；拒绝绝对
路径、`..`、符号链接、缓存文件和重复目标。包内相对 Markdown 引用必须在
白名单闭包中可以解析。

`core_skills`、`shared_skills` 可省略或为空；有值时互不重叠，元数据 name
与技能目录名一致。`profiles` 与 `generated_agents` 也可省略或为空：只有
需要 profile 标签或受控 Agent 文本合成的插件才声明。profiles 只是唯一名称列表，
策略资源和实际行为由该插件自行校验，公共层不强制 policies 文件。生成 Agent 每项为
`host/template/body/target`，当前仅接受已声明的 ZCode 宿主及 agents/*.md 目标，
只做数据化正文合成，不执行代码 hook。

纯资源能被校验和打包，不能证明某个运行能力已可用。新的宿主组件形态必须
先明确原生清单、启动/权限行为及真实会话验收，再扩展支持。

## 3. 提供宿主适配

技能 frontmatter 使用单行 name、description 和可选 origin：

```markdown
---
name: example
description: Explain the concrete AI task this skill handles.
---

# Example

Describe the task, inputs, actions and evidence expected from the assistant.
```

`adapters/codex/plugin.json` 最小模板可为：

```json
{
  "description": "Help an AI assistant with a concrete task",
  "license": "MIT"
}
```

公共构建从 product.json 注入 name/version，不在模板维护第二份发行版本。
更完整的原生界面可参考已有插件，但宿主特有清单要符合其真实能力，不将
未知字段当作已支持特性。该最小模板通过仓库结构校验不等于真实宿主已验收。

对上例的 Codex 技能，提供 `adapters/codex/interfaces.json`：

```json
{
  "schema_version": 1,
  "skills": {
    "example": {
      "display_name": "AI Example",
      "short_description": "Help with a concrete AI task",
      "brand_color": "#2563EB",
      "default_prompt": "Use $example to help with this task.",
      "allow_implicit_invocation": true
    }
  }
}
```

技能集合必须与该插件清单一致；公共构建生成各自
`skills/<name>/agents/openai.yaml`，不在源码技能目录维护第二份界面元数据。
无技能插件不要求这份技能界面文件。声明 ZCode 时提供其原生 plugin.json；
若需要 Agent，显式登记生成元数据并编写插件自己的行为检查。

公共市场由工具统一生成，不需要新插件提供 marketplace 模板。workflow
保留的旧模板只供自己的专属 build 使用。

## 4. 注册目录并接入测试

在根 `catalog.json` 的 plugins 数组中添加：

```json
{"path": "plugins/ai-example"}
```

注册表只存路径，拒绝未知字段、重复目录、重复 ID 和逃逸路径。目录存在但
未登记不会被自动构建。

为插件真实行为编写有意义的失败测试，执行 RED 后再实现 GREEN。统一门禁
按 catalog 为每个正式插件发现以下受控入口，至少必须存在一个：

- `tests/skills/run-skills.js`：Node 技能/资源契约组。
- `tests/run_python_tests.py`：插件自己的 Python 测试汇总。

每个入口独立子进程运行，自身须拒绝空测试组并将失败、启动错误或 signal
传为非零。新插件若没有任一入口，统一门禁判失败；确认 `npm test` 实际
执行新组。公共 `tests/run_python_tests.py` 只运行仓库通用工具测试，插件
Python 入口独立运行以避免同名 tests 包冲突。不要新增任意命令 hook。
不能用空组、仅有文件存在断言或重复实现的测试代替行为检查。文档和资源
修改根据影响做校验，无需机械增加测试。

新增公共工具行为时，同样先给有效 RED；用最小 fixture 验证通用规则，
不把测试样例登记成正式插件。

## 5. 校验、构建和检查

```sh
python3 tooling/plugin_tool.py list
python3 tooling/plugin_tool.py validate --plugin ai-example
npm test
python3 tooling/plugin_tool.py build --plugin ai-example --host codex --output dist-example
python3 tooling/plugin_tool.py package check \
  --path dist-example/codex/ai-example --host codex --root .
npm run lint
```

`dist-example` 必须不存在或为空；重复验证使用新的空目录。`--all` 可校验
或构建全部登记插件。`--host all` 按各插件 hosts 生成对应产物。

包检查使用可信仓库 `--root` 独立重建预期资源闭包，重算实际文件哈希并
核对原生清单和市场 source。不要调用尚未验证的包自己的 Python 文件作为
初始验证器。`ok` 不表示作者身份已认证，也不表示宿主实际执行了组件。

公共包检查拒绝全部未登记文件，包括可以被 Python 执行的 `.pyc` 缓存。
先验证原始发行包，再运行包内代码；需要保持产物可复验时使用 Python `-B`
或 `PYTHONDONTWRITEBYTECODE=1`。workflow 专属检查器的历史缓存分类不能
替代公共可信源码检查。采集注册插件的输入及复查时始终从仓库根遍历目录，
不把插件子目录重新作为允许跟随父目录链接的信任根。

根 `dist/index.json` 使用 schema_version 2，按 plugins/ID/hosts/HOST 记录
各包路径和哈希，按 hosts/HOST 记录聚合市场。插件自己的 artifact 保持自身
身份和来源。修改一个插件时核对兄弟插件内容和哈希不受影响。

## 6. 交付与原生验收

每个宿主目录有名为 `ai-code-local` 的聚合市场；各插件 ZIP 只包含自身包和
单插件市场。解压到稳定目录后按宿主原生方式注册，见现有
[安装说明](../plugins/ai-code-workflow/docs/installation.md) 中的市场路径约定。
原生命令与版本支持仍需对应插件实际验证。

插件支持说明要分别报告源校验、脚本测试、包检查、原生加载和实际行为。
记录宿主版本、模型、包哈希及会话证据；尚未验收写 `unverified`。为 MCP
增加普通资源文件不代表配置发现、认证、server 启动或工具调用已经支持。

交付时保留未提交改动，给出摘要、diff、验证结果和剩余限制，等待用户
Review。commit、push、tag、merge、PR、安装与发布仍遵守独立授权边界。
