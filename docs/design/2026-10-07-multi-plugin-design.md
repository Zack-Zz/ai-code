# ai-code 多插件仓库改造规格（2026-10-07）

用户确认的方向是让同一仓库承载多个与 AI 相关的插件，未来插件形态暂不
固定。本轮直接完成目录、通用发行工具、测试和文档迁移；不再次等待计划
确认，也不执行 Git 提交或外部发布。

本文是本轮目录、通用清单及发行索引的现行规格。原 workflow 的行为契约
保留在插件目录；历史设计和验收报告保留原日期及证据，不作为本轮通过记录。

## 目标与边界

- 每个插件自包含，可独立维护身份、版本、源码、资源、测试和支持声明。
- 目录注册不复制插件元数据；公共工具不调用插件任意代码来完成构建。
- 已有 `ai-code-workflow` 保持 ID、候选版本 `2.0.0`、六技能、两策略和
  policy/task/files 的运行语义，用户现有 `.ai-workflow` 不迁移。
- 提供单插件和全部插件的校验、构建，生成聚合市场与互不包含的插件 ZIP。
- 用第二个最小测试 fixture 证明通用工具不要求 workflow 专属内容；不新增
  第二个虚构的正式插件。

本轮不增加运行时、SDK、依赖调度、安装器、任意构建 hook 或强制多角色
流程。将来可以登记 MCP 等插件类型，但目录和文件能被打包不等于其运行
配置、认证、启动和宿主加载已经支持。

## 目录和责任

```text
ai-code/
  catalog.json
  tooling/plugin_tool.py
  tooling/
  tests/
  docs/plugin-authoring.md
  docs/design/2026-10-07-multi-plugin-design.md
  plugins/
    ai-code-workflow/
      product.json
      AGENTS.md
      README.md
      skills/ policies/ schemas/ templates/
      scripts/ adapters/ evals/ docs/ tests/
      LICENSE NOTICE LICENSES/
  dist/
```

| 层 | 维护内容 | 不承担的责任 |
|---|---|---|
| 仓库 | 插件目录注册、公共工具、统一门禁、作者指南、根维护规则 | 不替各插件决定行为、版本或验收结论 |
| 插件 | 自己的清单、技能/工具、适配、资源、测试和支持证据 | 不修改兄弟插件或宿主全局配置 |
| 发行产物 | 由选定插件和公共构建规则生成的包、市场、ZIP、索引 | 不反向成为产品元数据来源 |

`plugins/<id>/` 为源码根。root `README` 描述插件集合；插件 `README` 描述
自身用途。root `AGENTS.md` 为通用规则；插件 `AGENTS.md` 保留自身规则。
公共工具和 workflow 管理工具分开维护。

## 注册与身份

根 `catalog.json` 使用固定结构：

```json
{
  "schema_version": 1,
  "plugins": [
    {"path": "plugins/ai-code-workflow"}
  ]
}
```

每项只有 `path`。路径是仓库内规范化相对路径，必须指向包含 `product.json`
的真实插件目录，形状为 `plugins/<规范目录名>`；建议目录名与插件 ID 一致。
拒绝重复目录、重复插件 ID、未知
字段、绝对路径、父目录逃逸、符号链接和缺失文件。未注册目录不会自动入包。

各插件的 `product.json` 独立提供 `product_id`、`display_name`、`version`、
`repository`、`license` 和资源白名单；根 private `package.json` 仅服务
维护，不再与插件版本绑定。版本是插件自己的 `X.Y.Z` 候选版本，不表示已发布。

## 通用插件清单

保持 `schema_version: 1`，沿用身份和显式资源映射，增加宿主与可选生成元数据。

| 字段 | 通用要求 | workflow 的局部要求 |
|---|---|---|
| `hosts` | 必填、非空、不重复；当前接受 `zcode`、`codex` | 两个既有宿主均保留 |
| `core_skills`、`shared_skills` | 可省略或为空；有值时不重复且互不相交，对应真实 SKILL.md | 保留五核心技能和 review-results |
| `profiles` | 可省略或为空的唯一名称列表；行为与资源由插件自行校验 | 固定 collaborative、continuous，并校验两份策略 |
| `generated_agents` | 可省略或为空；当前仅接受已声明的 zcode，每项严格包含 host、template、body、target | 只声明现有 ZCode workflow-reviewer 合成 |
| `resources` | 显式 source/target/include 映射；入包所需文件均真实存在 | 保留原工具、策略、模板、schema 与许可证白名单 |

资源源路径相对插件源码根，目标路径相对安装包根。文件 source 的 include
必须为 `[]`；目录 source 必须列出明确的相对文件名。拒绝通配符、父目录
逃逸、链接、缓存以及重复目标。声明的技能贡献各自 `skills/<name>/SKILL.md`；
其引用的额外文档、脚本和资源仍需单独列入 resources。

每个声明宿主要求 `adapters/<host>/plugin.json`。Codex 的技能界面来源为
该插件 `adapters/codex/interfaces.json`，由公共工具生成对应 openai.yaml；
无技能插件不因此被强制要求六份 workflow 元数据。

`generated_agents` 是受控数据拼接：使用 template 的 frontmatter 和 body
正文输出到 target。所有路径和宿主必须在插件边界内；工具不执行模板代码，
不动态 import 插件模块。workflow 的只读工具白名单、inherit 和 maxTurns
等约束继续由 workflow 的专属校验及测试维护。

通用工具不会把 task/evidence schema、两种协作模式、Reviewer 或
`.ai-workflow` 状态目录列为每个插件必需组件。

## 两套命令入口

以下公共命令从仓库根运行：

```sh
python3 tooling/plugin_tool.py list
python3 tooling/plugin_tool.py validate --all
python3 tooling/plugin_tool.py validate --plugin ai-code-workflow
python3 tooling/plugin_tool.py build --all --host all --output dist-check
python3 tooling/plugin_tool.py build --plugin ai-code-workflow --host codex --output dist-codex
python3 tooling/plugin_tool.py package check --path dist-check/codex/ai-code-workflow --host codex --root .
```

`--all` 与 `--plugin` 明确选择范围；build 的输出目录必须不存在或为空。
`--host all` 取每个插件声明的宿主。定向宿主仅为所选集合中声明该宿主的
插件构建；没有适用插件时拒绝假成功。

包检查的 `--root` 指向可信源码仓库，用注册表和插件清单独立重建预期闭包，
而不是只相信待检查包的 artifact 文件列表。公共 CLI 对无效数据、未知选择、
不合法路径和检查失败返回非零；不得改动 workflow 原有 0/1/2/3/4/5 语义。

workflow 源码入口仍为：

```sh
python3 plugins/ai-code-workflow/scripts/workflow_tool.py validate --root plugins/ai-code-workflow
python3 plugins/ai-code-workflow/scripts/workflow_tool.py policy resolve \
  --plugin-root plugins/ai-code-workflow --workspace /path/to/project
```

其原有 task、files、build、package 命令继续用于该插件。随包入口保持
`tools/workflow_tool.py`。工作流专属 build 可生成单插件发行目录并使用原
适配模板；公共 build 不调用该命令，不读取插件自己的 marketplace 模板。

## 产物结构

```text
dist/
  index.json
  zcode/
    marketplace.json
    ai-code-workflow/
    ai-code-workflow-2.0.0.zip
  codex/
    .agents/plugins/marketplace.json
    ai-code-workflow/
    ai-code-workflow-2.0.0.zip
```

每个宿主根包含选中且支持该宿主的插件。聚合市场名统一为 `ai-code-local`；
ZCode 清单在 `marketplace.json`，Codex 清单在 `.agents/plugins/marketplace.json`。
市场条目的 ID、版本和相对 source 由各插件清单生成，不能把所有条目重写成
同一个插件身份。

每个 `<id>-<version>.zip` 只包含自身包目录和对应宿主的单插件市场；解压后
可注册独立市场，不包含兄弟插件、其他 ZIP 或源码工作记录。ZIP 的条目顺序、
时间和权限固定；同输入与 Git 上下文应产生相同字节。

公共 `dist/index.json` 使用 `schema_version: 2`：

```json
{
  "schema_version": 2,
  "source_revision": null,
  "working_tree_dirty": true,
  "plugins": {
    "ai-code-workflow": {
      "version": "2.0.0",
      "source_tree_hash": "<actual SHA256>",
      "hosts": {
        "codex": {
          "package_dir": "codex/ai-code-workflow",
          "package_content_hash": "<actual SHA256>",
          "zip": "codex/ai-code-workflow-2.0.0.zip",
          "zip_sha256": "<actual SHA256>",
          "files_count": 0
        }
      }
    }
  },
  "hosts": {
    "codex": {
      "marketplace": "codex/.agents/plugins/marketplace.json",
      "marketplace_sha256": "<actual SHA256>"
    }
  }
}
```

上例仅说明键和层级，哈希、Git 身份、文件数必须来自真实构建。每个插件包的
artifact 保持自身产品 ID、版本、宿主、profiles、来源与内容哈希，不借用
兄弟插件的来源。更改一个插件时，它自己的来源和包哈希应变化，其他插件
不受影响；聚合市场因成员或版本变化更新。

## 构建与检查边界

公共工具按白名单捕获输入快照，将插件清单、资源及宿主适配纳入自身来源
哈希，在私有 staging 中生成完整发行目录。检查包和 ZIP 后才发布输出；
失败不删除现有输出或用户晚到文件。拒绝额外活动文件、缺失资源、畸形
artifact、错误市场 source、伪造/不一致哈希和跨插件身份混用。

历史 workflow 包检查仍维持六技能、两策略、reviewer、task/evidence 和
许可证的专属闭包约束。通用层增加扩展能力，不放松已有工作流保护。

## 已授权的执行顺序

| 步骤 | 交付物 | 验证重点 |
|---|---|---|
| 1. 保存与核对基线 | 原有改动边界、统一门禁基线 | 不丢用户改动，环境错误不冒充 RED |
| 2. 通用契约与有效 RED | 注册表、插件选择、资源和宿主的失败测试 | 最小第二插件不要求 workflow 内容 |
| 3. 最小公共实现 | catalog、通用 CLI、校验/构建/检查 | 身份、闭包、哈希、市场、单插件 ZIP |
| 4. 迁移 workflow | plugins/ai-code-workflow 及专属规则 | 原 ID/版本/运行路径和保护不漂移 |
| 5. 门禁与文档 | 根/插件说明、作者指南、CI 与测试入口 | 全部实际测试组进入统一门禁，历史证据保留 |
| 6. 独立复核与交付 | 当前 diff、通过结果、限制 | 真实宿主状态单列，未提交等待用户 Review |

统一门禁按 catalog 发现每个插件的 `tests/skills/run-skills.js` 和
`tests/run_python_tests.py`；每个正式插件至少有其中一个受控入口，缺失入口
判失败。每组独立子进程运行，避免插件同名 tests 包相互污染；入口自身
拒绝空组，根 Python 入口只测试公共工具，不加载任意测试命令 hook。

本轮必须覆盖单插件/多插件、不同宿主声明、重复身份、路径逃逸、缺失资源、
资源目标冲突、伪造哈希、市场解析、兄弟插件隔离及可复现 ZIP。旧 workflow
回归、统一门禁自身测试、source validate、构建后的目录与解压包检查及 lint
一起执行；通过结果由实际命令记录，本文不预填验收状态。

真实加载、技能触发、Reviewer 限制和 MCP 运行仍要求独立宿主会话；本轮
迁移不改变 [workflow 支持矩阵](../../plugins/ai-code-workflow/docs/support-matrix.md)
中历史报告的日期或验收边界。
