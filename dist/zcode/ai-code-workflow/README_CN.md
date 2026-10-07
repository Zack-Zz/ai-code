# CodeVow · AI 编码工作流

CodeVow 帮助 AI 编码助手与你确认计划、使用 TDD、按证据排查、审查风险并
验证最终代码状态。插件 ID 为 `ai-code-workflow`。本包是自建市场试用候选，版本
和哈希由生成的原生清单与发行记录提供。

[English](README.md)

## 包内能力与支持边界

包含六个 Markdown 技能：workflow、tdd、debugging、review、verification、
review-results；两份协作策略 collaborative 与 continuous；以及可选的
本地 Python 策略解析、工作区任务/证据记录和带回执暂存工具。
Claude Code 与 ZCode 包内的 Reviewer 使用 inherit、Read/Grep/Glob、
maxTurns=12，并由同一份审查职责正文生成。Codex 包生成六份原生技能界面。

已提供 Claude Code、Codex、ZCode 三种包结构。**所有真实宿主验收仍为
unverified**。包格式、哈希与脚本测试通过不能证明技能发现、自动调用、策略
加载或只读限制生效；这些行为需要明确授权的新宿主会话验证。

## 依赖、联网与写入

使用你已有的宿主、账号与模型选择。原生 Markdown 技能不需要 Node.js 或
Python；可选管理命令需要 Python 3.11+ 标准库，以及支持 POSIX 目录句柄和
no-follow 文件操作的平台；已验证开发环境之外的平台支持仍未验收。本包不包含外部 Python/Node
依赖、MCP 服务、后台服务或模型路由。

Python 工具不联网、不调用模型、不执行 Git 写操作。宿主可以使用自己的
模型服务，并在原生安装/更新时下载插件内容，遵守你的宿主设置。原生安装
会写宿主管理的插件/配置位置。明确执行 task ... --apply 才写所选工作区的
.ai-workflow/tasks/；files apply 写暂存的自有文件、回执和备份。任务记录、
模式切换与 approved 标记永不产生用户授权。

## 按宿主原生方式安装

下载所需宿主的候选包，解压到稳定目录。市场根是包含原生市场文件的目录，
不是 ai-code-workflow 插件目录。生成市场默认名为 ai-code-local；若获得
另一种源码包，按其真实声明的市场名称安装。

Claude Code 市场文件为 .claude-plugin/marketplace.json：

```sh
claude plugin marketplace add /path/to/extracted/claude
claude plugin install ai-code-workflow@ai-code-local
```

Codex 市场文件为 .agents/plugins/marketplace.json：

```sh
codex plugin marketplace add /path/to/extracted/codex
```

重启支持该市场的桌面客户端，在插件目录选择 ai-code-local 来源并安装
CodeVow。CLI 命令依实际版本而变，先检查 plugin --help。ZCode 使用原生市场
界面注册解压目录的 marketplace.json，再安装 ai-code-workflow。本包不会
自动执行安装器，安装/启用成功也不等于模型行为验收。

开启新会话，核对发现的技能、加载的包哈希，再用一个小的已授权开发任务
核实计划、有效 RED/GREEN、风险审查和最终状态验证确实发生。

## 从安装包根目录使用可选工具

```sh
python3 tools/workflow_tool.py policy resolve --plugin-root . --workspace /path/to/project
python3 tools/workflow_tool.py task create --workspace /path/to/project --id demo --input templates/task.json
python3 tools/workflow_tool.py task check --workspace /path/to/project --id demo
```

task create 默认预检查，只有显式 --apply 才写入。可选暂存先生成并阅读计划：

```sh
python3 tools/workflow_tool.py files plan --package . --target /path/to/project --action stage --out /tmp/codevow-plan.json
python3 tools/workflow_tool.py files apply --plan /tmp/codevow-plan.json --expected-plan-hash <实际计划哈希>
```

更新/移除拒绝覆盖用户编辑或取得未拥有文件的所有权；中断保留恢复资料。
暂存与宿主安装分开。执行下载包的 Python 文件之前，应先用可信源码仓库
工具验证完整性；被检查包不能担任自己的初始验证器。

## 来源、许可证与限制

源码：[Zack-Zz/ai-code](https://github.com/Zack-Zz/ai-code)，插件源码目录为
plugins/ai-code-workflow/。publisher 是维护者声明，不代表身份认证或宿主
背书。公开发布/晋升须另行授权，声明哪些宿主已支持须有对应实际验收。

MIT，见 [LICENSE](LICENSE)、[NOTICE](NOTICE) 与保留的
[backend-engineering-lite 许可证](LICENSES/backend-engineering-lite.txt)。
历史工作流证据与支持矩阵留在源码仓库，保持原日期。本候选不宣称真实宿主
已验收，也不提供自动交易、部署或 Git 发布能力。
