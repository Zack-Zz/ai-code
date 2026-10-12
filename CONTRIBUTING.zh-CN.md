# ai-code 开发指南

[English](CONTRIBUTING.md) | 简体中文

本指南面向修改 ai-code 源码的开发者。安装和使用插件请阅读[用户安装指南](docs/installation.zh-CN.md)。
除特别说明外，以下命令都在仓库根目录运行。

## 环境准备

- Node.js 22+ 和 npm：运行测试汇总器与静态检查。
- Python 3.11+：运行插件工具和 Python 测试。
- 支持 POSIX 文件操作的开发环境：运行受控文件管理工具和相关测试。

获取源码并安装仓库维护依赖：

```sh
git clone https://github.com/Zack-Zz/ai-code.git
cd ai-code
npm ci --no-audit --no-fund
python3 tooling/plugin_tool.py list
```

已有 checkout 时，直接进入仓库根目录安装依赖。

开发前阅读根 [AGENTS.md](AGENTS.md) 和目标插件的 `AGENTS.md`。插件版本、
宿主和入包资源以目标插件的 `product.json` 为准，根 `package.json` 用于维护工具。

## 修改现有插件

先定位目标插件，再修改对应的功能与测试：

| 插件 | 主要源码 | 测试入口 |
|---|---|---|
| CodeVow | `plugins/ai-code-workflow/skills/`、`policies/`、`scripts/workflow/` | Node 技能契约和插件 Python 测试 |
| Agent Delegation | `plugins/ai-agent-delegation/skills/`、`scripts/bridge_client.py` | 插件 Python 测试 |
| 公共工具 | `tooling/plugin_tools/` | `tests/run_python_tests.py` |

行为变更先写有意义的失败测试，再做最小实现并跑绿。文档调整按影响检查内容、
链接和格式。新增入包资源时更新插件 `product.json` 的显式白名单。

需要单独运行目标插件测试时：

```sh
node plugins/ai-code-workflow/tests/skills/run-skills.js
PYTHONDONTWRITEBYTECODE=1 python3 plugins/ai-code-workflow/tests/run_python_tests.py
PYTHONDONTWRITEBYTECODE=1 python3 plugins/ai-agent-delegation/tests/run_python_tests.py
```

## 完整检查与构建

```sh
python3 tooling/plugin_tool.py validate --all
PYTHONDONTWRITEBYTECODE=1 npm test
npm run lint
python3 tooling/plugin_tool.py build --all --host all --output /tmp/ai-code-dev-packages
```

输出目录必须不存在或为空；再次构建时使用新的空目录。只处理一个插件可将
`--all` 改成 `--plugin ai-code-workflow`，`--host` 可选 `claude`、`codex`、
`zcode` 或 `all`。

用可信源码独立检查生成的包，以 CodeVow 的 Codex 包为例：

```sh
python3 tooling/plugin_tool.py package check \
  --path /tmp/ai-code-dev-packages/codex/ai-code-workflow --host codex --root .
```

发布前对选定插件的每个宿主包执行相同检查。统一 `npm test` 覆盖公共工具
和全部已注册插件；空测试组或任一组失败会使整体失败。

## 本地试用

构建目录的每个宿主子目录包含名为 `ai-code-local` 的开发市场。按你使用的
编码助手注册对应目录；下面以 Codex 和 CodeVow 为例：

```sh
codex plugin marketplace add /tmp/ai-code-dev-packages/codex
codex plugin add ai-code-workflow@ai-code-local
```

Claude Code 与 ZCode 的本地市场操作见[下载包安装](docs/installation.zh-CN.md#下载包安装)。
试用后新建会话，检查技能和实际任务结果。修改源码后重新构建，在编码助手
中更新插件，再开启新会话。

也可以通过以下命令生成单独的开发市场，输出目录同样必须为空：

```sh
python3 tooling/plugin_tool.py marketplace sync --output /tmp/ai-code-dev-market
```

构建产物放在临时目录。`dist/` 被 Git 忽略，不能作为源码提交；本地试用不修改
仓库的公开市场清单。

## 新增插件

按[插件作者指南](docs/plugin-authoring.zh-CN.md)建立目录、声明资源、提供宿主适配，
登记到 `catalog.json` 并接入插件测试。每个插件独立维护功能、版本和资源，
公共工具负责注册、构建与包检查。

## 文档与交付

用户 README 说明当前功能、安装和使用。开发步骤放在开发指南，发布前检查
放在[维护者发布指南](docs/publishing.zh-CN.md)，验收数据放在[证据契约](docs/release-evidence.zh-CN.md)。
当前指南使用现行接口；带日期的设计与验证报告保留在[参考资料](docs/README.zh-CN.md#设计与历史资料)。

提交改动时包含相关源码、测试和文档，说明实际运行的检查及结果。发布、市场
更新和用户安装是各自独立的操作，按维护指南处理。
