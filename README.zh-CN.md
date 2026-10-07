# ai-code

[English](README.md) | 简体中文

一个承载多个 **AI 相关插件** 的仓库。每个插件独立维护源码、身份、版本、
资源、测试与支持声明；公共工具负责目录注册、源校验、可复现构建和本地市场
生成，插件行为留在各自目录内。

首个插件是 **CodeVow · AI 编码工作流**（`ai-code-workflow`），用于 AI 编码助手的
工程协作。其他插件形态在有具体需求时扩展；仓库不要求所有插件具备工作流
技能、策略或任务记录。

## 插件目录

| 插件 | 用途 | 版本与支持状态 |
|---|---|---|
| [CodeVow](plugins/ai-code-workflow/README.zh-CN.md) | 计划、TDD、排查、审查、验证与交付证据 | `2.0.0` 自建市场试用候选；[真实宿主验收仍未完成](plugins/ai-code-workflow/docs/support-matrix.md) |

`catalog.json` 只登记插件目录；各目录的 `product.json` 是插件 ID、版本和
资源白名单的唯一来源。根目录的私有 Node 包用于仓库维护，其版本不作为
任何插件的发行版本。

## 快速开始

在仓库根目录执行，需要 Python 3.11+ 与 Node 22+：

```sh
python3 tooling/plugin_tool.py list
python3 tooling/plugin_tool.py validate --all
npm test
python3 tooling/plugin_tool.py build --all --host all --output dist-check
python3 tooling/plugin_tool.py package check \
  --path dist-check/codex/ai-code-workflow --host codex --root .
```

输出目录必须不存在或为空。只处理一个插件时，将 `--all` 替换为
`--plugin ai-code-workflow`。`--host` 支持 `claude`、`codex`、`zcode` 与 `all`，
各插件只为自己声明的宿主生成产物。

发行目录包含名为 `ai-code-local` 的聚合本地市场、独立插件包和独立 ZIP。
每个 ZIP 只包含该插件与对应的单插件市场；解压到稳定目录后，通过宿主原生
插件机制注册并安装。操作见插件的
[安装文档](plugins/ai-code-workflow/docs/installation.md)。
三端发布预检、制品准备/复验、仓库市场和手动 GitHub 草稿流程见
[发布指南](docs/publishing.md)。稳定制品要求真实宿主验收证据。

源校验、包完整性和测试通过不代表原生加载成功或模型遵循技能。真实宿主验收
及其证据由各插件分别维护。

## 仓库结构

| 路径 | 用途 |
|---|---|
| `catalog.json` | 显式注册的插件目录列表 |
| `plugins/<id>/` | 插件自包含的源码、清单、资源、适配、测试与文档 |
| `tooling/plugin_tool.py` | 公共校验、构建、包检查、市场同步与 release 入口 |
| `tooling/` | 通用源校验、构建与市场生成工具 |
| `tests/` | 公共工具测试与统一门禁 |
| `docs/plugin-authoring.md` | 新插件接入及宿主声明指南 |
| `docs/publishing.md` | 三端发布资料、制品、验收和渠道操作 |
| `.github/workflows/release.yml` | 手动准备制品，可选创建 GitHub 草稿 |
| `docs/design/2026-10-07-multi-plugin-design.md` | 多插件边界、数据契约与迁移计划 |
| `dist/` | 从已注册源码生成、可重建的发行目录 |

## 开发与验证

- 修改前读取根 `AGENTS.md` 和目标插件的局部维护规则。
- 行为变更使用有意义的 RED、GREEN 测试；`npm test` 覆盖公共工具与全部
  已注册插件的测试组。
- 安装本地维护依赖后执行 `npm run lint`。
- 插件 ID、版本独立维护；所有入包资源都必须登记；不同插件的源码和哈希
  边界保持清晰。
- 接入步骤见[作者指南](docs/plugin-authoring.md)。新的运行集成需要独立设计
  和宿主验证。

CodeVow 的策略解析、任务记录与带回执暂存工具仍位于源码中的
`plugins/ai-code-workflow/scripts/workflow_tool.py`，随包入口为
`tools/workflow_tool.py`；这些能力属于该插件。

## 许可证与来源

MIT——见 [LICENSE](LICENSE) 与 [NOTICE](NOTICE)。仓库早期历史派生自
Affaan Mustafa 的 ai-code。CodeVow 的迁移来源与保留的
backend-engineering-lite 许可证见该插件的
[README](plugins/ai-code-workflow/README.zh-CN.md) 和
[迁移文档](plugins/ai-code-workflow/docs/migration.md)。
