# 插件身份统一与 DeepSeek Harness 原生支持方案

日期：2026-10-27（Asia/Shanghai）。状态：本地实施、Review 和验证完成；尚未提交或发布。原始研究基线保留，接口示例按下方实施调整更新，结果见[实施记录](../reviews/2026-10-27-plugin-identities-dsh-implementation.md)。

后续版本更正：用户明确指定 CodeVow `1.0.6`、CodeStack `1.0.0`，并要求新插件从
`1.0.0` 起步、后续默认只加一个补丁版本。下方原始候选建议及示例保留设计背景，
其中的 `2.0.0` / `0.2.0` 已被此次指定替代；当前版本以各插件的 `product.json`
和[现行发布规范](../publishing.zh-CN.md#插件版本升级规范)为准。

用户已确认接受插件改名后重新安装，随后授权按本方案实施、同步文档、Review 和验证，要求先不提交和发布。隔离开发依赖用于验证，不安装用户宿主 profile，不修改全局配置。

## 1. 结论与实施目标

将两个已发布插件的安装 ID 统一为 `codevow`、`codestack`，展示名称继续使用 CodeVow、CodeStack。Claude Code、Codex、ZCode 和新增的 DeepSeek Harness 使用同一产品 ID，各宿主保留自己的原生包格式。

Harness 的宿主标识统一为 `dsh`，适配源码位于 `adapters/dsh/`。它采用官方的 `package.json` → `dsh.bundle` → `cordis.patch.yml` → profile 组合机制：

- 两个独立 bundle，各自可安装、启停和卸载。
- 技能通过官方 `@deepseek-ai/dsh-skill-filesystem` 挂载，由已有 `skill` 工具和 `/技能名` 调用。
- CodeStack 只有声明式适配和 Markdown 资源，不新增业务运行逻辑。
- CodeVow 复用现有 Python 辅助工具；Reviewer 使用官方 spawn、Agent Preset 和原生工具限制。
- 发布使用 GitHub Release 和固定 Git 子目录；提供官方格式的插件索引，不新增 npm 发布渠道。

不复制技能正文到 DSH 专用分支，不编写技能安装器、独立 agent runtime、MCP 桥或新的工作流调度器。CodeVow 的开发确认规则仍是技能指令，不将此次接入宣传为对全部项目写入的强制运行时拦截。

## 2. 事实基线、授权和范围

### 2.1 已核对的基线

| 项目 | 本轮基线 |
| --- | --- |
| ai-code | `main`，`2843ffd3199c787af87b1548c65fbd1af2dfe856`；开始时工作区干净 |
| 已发布 CodeVow | `ai-code-workflow`，`1.0.5`，三个宿主 |
| 已发布 CodeStack | `ai-code-stack-standards`，`0.1.0`，三个宿主 |
| 上游仓库 | `deepseek-ai/deepseek-harness` 的 `master` |
| 上游固定提交 | `22ddee3792402c3e70ec5f86a63c3e3e895a2f60`，本轮重新读取分支确认 |
| 上游包版本候选 | 已读包清单为 `0.2.1-rc.3`；尚未运行该宿主 |

上游仍处于 developer preview。首轮实现以该提交对应的 API 为设计基线；实际安装验收须记录 CLI/应用报告的运行时版本，不能用源码版本代替运行版本。

### 2.2 本次范围

覆盖两个已发布插件的身份、当前源码目录、四端适配、资源闭包、构建检查、发行数据、市场切换、双语公开说明及验收场景。

`ai-agent-delegation` 尚未进入当前正式市场，保持其现有 ID、目录和宿主声明；本次仅验证公共工具改动不破坏它。不修改用户的全局配置、宿主缓存、模型、凭据或其他业务仓库。

实现、版本准备、Git 交付、实际发布和用户安装分开执行。本方案中的命令是后续实施规格，不是本轮已执行记录。

## 3. 身份与版本决定

| 项目 | 旧值 | 目标值 |
| --- | --- | --- |
| CodeVow ID / 源码目录 | `ai-code-workflow` / `plugins/ai-code-workflow/` | `codevow` / `plugins/codevow/` |
| CodeStack ID / 源码目录 | `ai-code-stack-standards` / `plugins/ai-code-stack-standards/` | `codestack` / `plugins/codestack/` |
| 展示名称 | CodeVow / CodeStack | 保持品牌大小写 |
| 公开市场名 / 仓库名 | `ai-code` | 保持 |
| 技能名 | `workflow`、`tdd`、`code-standards` 等 | 保持，不以插件 ID 代替技能名 |
| 项目状态目录 | `.ai-workflow/` | 保持，沿用现有 policy/task/evidence 数据契约 |

首发目标版本建议为 CodeVow `2.0.0`、CodeStack `0.2.0`：明确表达安装身份变更，并继续各自的版本演进。本轮不修改版本；正式准备时仍通过 `release prepare-version` 预览并应用，按当时发行历史复核候选版本。

当前源码中的 `product_id`、适配元数据、技能 `origin`、活动 Schema 的 `$id`、独立工具的包路径和提示、CI choices、活动 fixture 及双语指南统一更新。`product.json` 继续是 ID、展示名称和版本的唯一权威；DSH `package.json` 的 name/version，以及 locale 和索引中的品牌标题均由它生成。

迁移不改项目 policy/task/evidence 的结构和状态目录。修改 Schema 标识时核查现有 `$ref`，对旧项目输入做回归读取，不能靠目录改名使已有记录失效。

## 4. Harness 标准接入契约

### 4.1 原生包与资源布局

CodeStack 的 DSH 包是无自定义执行模块的数据组合包。CodeVow 仅额外携带薄的 Reviewer 权限适配模块：

```text
<id>/
  package.json                  DSH bundle 清单，生成 name/version/展示信息
  cordis.patch.yml              原生组合层
  skills/                       所有宿主共用的技能及 references
  assets/                       图标
  locale/en.json / zh.json       官方 meta.title / meta.description 展示元信息
  README.md / README_CN.md       英文默认、中文切换
  LICENSE / artifact.json       许可及公共构建来源

  policies/ schemas/ templates/ tools/    仅 CodeVow，沿用现有资源闭包
  reviewer-guard.js                      仅 CodeVow，DSH 专用
  reviewer-persona.json                  仅 CodeVow，由共享审查合同生成
```

`package.json` 的必要结构以下例为准。`files` 在构建时由目标闭包生成精确清单，下面仅缩写展示：

```json
{
  "name": "codestack",
  "version": "0.2.0",
  "type": "module",
  "description": "Selected coding conventions for the current change or review",
  "license": "MIT",
  "exports": { "./package.json": "./package.json", "./locale/*.json": "./locale/*.json" },
  "icon": "./assets/codestack.png",
  "files": ["cordis.patch.yml", "skills", "assets", "locale", "README.md", "README_CN.md", "LICENSE", "artifact.json"],
  "engines": { "dsh": "0.2.1-rc.2" },
  "dsh": { "bundle": { "patch": "./cordis.patch.yml" } }
}
```

初始兼容范围锁定可安装并完成原生 API 组合验证的精确 DSH 版本；完整带模型宿主验收仍独立记录。若首测版本不同，先复核 API 再更新范围。扩宽版本范围需有相应兼容测试，不直接声明无上限的 `>=`。

展示信息采用官方 `locale/en.json`、`locale/zh.json` 中的 `meta.title` 和 `meta.description`，配合导出的 locale 资源及包内 `icon`；不假造根清单的 `title` 字段。CodeVow 另导出 Reviewer 权限模块子路径，供 patch 以稳定包名引用。包内 README 默认英文并提供中文切换。

不设置 `private: true`，不添加 `prepare`、`postinstall` 或其他依赖安装脚本。CodeVow 的适配使用可直接加载的 ESM JavaScript，不让用户从 Git 安装时临时编译 TypeScript。宿主公共包通过精确约束的 peer 声明复用安装中的实例，不把另一套 Harness 打进制品；缺失服务应明确报错。

### 4.2 技能发现采用官方文件系统提供方

两个 bundle 各在 Host 层插入一个具有唯一行 ID 和提供方名称的官方 `skill-filesystem` 实例；不覆盖宿主已有实例，不改写用户的 standard/preset 配置：

```yaml
- insert:
    - id: codestack-skills
      name: '@deepseek-ai/dsh-skill-filesystem'
      config:
        providerName: codestack
        includeDefaultRoots: false
        watch: false
        bundledSkillDir: !!js process.getBuiltinModule('node:path').join(process.getBuiltinModule('node:path').dirname(process.getBuiltinModule('node:module').createRequire(baseUrl).resolve('codestack/package.json')), 'skills')
```

CodeVow 使用同一形态，替换为 `codevow-skills`、`codevow`。包目录的解析方式沿用上游官方 preset 中 `createRequire(baseUrl).resolve(.../package.json)` 的做法；`bundledSkillDir` 与 `includeDefaultRoots: false` 的组合已由提供方源码确认。

- 只扫描本插件的 `skills/`，避免再次扫描用户根目录、泄露仓库内部维护技能或产生重名注册。
- `bundled` 来源使用 rank 600，低于同层项目、自定义和用户根；近层技能可遮蔽外层，rank 只在同层生效，不能承诺任何 scope 下都由用户定义获胜。
- 提供方保留技能目录的 `resourceBase`，相对引用继续以真实安装目录解析；`tools/workflow_tool.py` 保持从插件根定位。
- 发布资源不由模型写回，使用 `watch: false`；更新/卸载经官方 profile 重组与生命周期完成。没有 HMR 的 profile 需要重启。
- 模型调用使用官方 `skill`；用户显式调用是 `/workflow`、`/code-standards`，不是宿主无证据的 `$codevow` 或自造 slash 命令。
- 标准 Web profile 是首轮完整支持对象。Headless/SDK/ACP/minimal 本轮不声明支持；缺少必需服务时不能仅以“Reviewer 不可用”声称整个 bundle 已安全降级。

### 4.3 CodeVow Reviewer 使用原生子代理组合

使用官方 `@deepseek-ai/dsh-agent-preset` 声明一个独立 `codevow-reviewer`，不会切换用户默认 preset。Host 层另挂官方 `@deepseek-ai/dsh-tool-subagent`：

```yaml
config:
  provider: spawn
  toolName: workflow_reviewer
  agentPreset: codevow-reviewer
  modelSelectionSettings: false
```

完整 CodeVow 要求目标 profile 提供 `agentPresets`、Agent/工具/系统提示词服务以及 `subagents` 的 spawn 后端。Reviewer 声明和专用工具行显式声明 `agentPresets` 等所需 Loader 注入，等待服务就绪，避免启动顺序造成错误。缺服务按原生 Loader 报告未满足依赖/无法激活，视为该 profile 不受支持；不自行降级到父级通用 preset。CLI 包依赖安装成功也不能视为这些服务已具备，H01/H07 必须核对安装结果与运行激活诊断。

省略 `allowedAgentPresets`，使模型不能将审查切到其他 preset；不配置已废弃的 `persona`、`toolFilter` 字段。模型、提供方和推理强度沿用父级的默认路由，不新增固定模型分工。委派深度沿用宿主设置；达到上限时报告不可用，不绕过限制。

该 preset 只组合以下能力：

1. 官方 persona，正文从共同的 `reviewer-contract.md` 在构建时生成 `reviewer-persona.json`；不维护另一份审查职责文本。
2. RC2 官方 `agent-tool-presentation`，配置 `mode: native`，使用工具服务内置的原生执行方式，避免引入 PTC 代码执行传输。
3. 官方 `tool-fs`，配置 `read: true`、`readImage: false`、`write: false`、`edit: false`。
4. 官方 `tool-fs-search`，提供 `grep`、`glob`。
5. 很薄的 `reviewer-guard.js`，仅绑定原生限制和清理，不管理 agent 循环、任务存储或模型。

权限适配采用两层：在 Reviewer 的 `agent/created` 生命周期中，对 **`agent.ctx`** 调用 `tools.restrict({allow: ['read', 'grep', 'glob']})`，隐藏继承的其他工具；在 preset scope 注册 `tools.guard()`，对非白名单调用执行最终拒绝。不能直接在 preset scope 限制自己的工具，因为 `restrict` 对本层注册有例外，而且会拒绝未知工具名。

guard 模块还须维护每个 Agent 的限制 disposer，并按 `scopeChainOf(scopeOf(agent.ctx))` 是否包含本 Reviewer composition scope 调和：挂载时扫描现有 Agent；创建时安装；`tools/change` 时为进入该 preset 的 Agent 安装、为离开的 Agent 释放；销毁或模块卸载时清理。参考上游委派工具已有的 ancestry/reconcile 机制，保持幂等，先登记安装状态再触发会再次发事件的操作。仅监听创建事件不够，因为空白会话切换 preset 会 recompose 而不会重新创建 Agent。创建时限制失败应阻止工作放行；调和失败报告诊断且不能移除仍适用的最终 guard。

最终拒绝同样覆盖 Host 继承的 `workflow_reviewer`、通用子代理、shell、网络、插件管理和写工具。限制注册失败则拒绝创建 Reviewer；上游会在放行排队工作前等待串行 `agent/created` 监听器。不得失败后降级到无限制 preset。

搜索可由官方实现启动固定参数的 ripgrep 子进程，因此只声明“无通用 shell 工具”，不声明“无任何进程”。工具白名单也不等于独立文件系统沙箱：读取权限根复用宿主配置，委托范围按共享合同约束；能力记录分别报告 `reviewer_restriction` 和 `workspace_isolation`。如果后者没有实测证据，保留未验证状态。

CodeVow 的 review 技能需增加 DSH 工具的发现与调用说明：委派时提供目标、差异、约束和已有验证记录；spawn 不继承对话正文。仍由主代理核验 findings。宿主/当前 profile 不具备该能力时，沿用已有“独立审查不可用”的披露规则，不把 self-review 写成独立审查。

### 4.4 Python 工具和长上下文

继续打包现有 `tools/workflow_tool.py` 和模块，使用宿主原生 shell 工具按绝对路径调用；不实现 JavaScript 版 policy/task/files 服务。Python 环境要求沿用现有工具声明；没有 Python 时，保留技能中已有的手工 policy 解析路径，能力说明如实区分。

当前发布文件的字符数核算发现 `workflow/SKILL.md` 为 12,376，CodeStack `java.md` 为 8,770。Harness 标准 preset 的工具结果修剪阈值为 8,192 个 Unicode 码点，默认保留头部 4,096 和尾部 1,024；**它在压缩压力触发后运行，不是加载时立刻裁剪**。

实现时对共同资源做一次语义保持的整理：将 workflow 的授权边界、入口和必要决策留在短主技能，将详细计划、委派和工具说明转为明确按需读取的 references；CodeStack 保留完整规则，拆出过长规则章节。规则选取入口、交叉引用和禁止事项必须保持可达。

不通过覆写用户的 standard preset 来关闭压缩或全局抬高阈值。测试实际 `skill` 渲染结果和引用文件读取分页的长度，给包装与路径预留空间；长会话验收另验证压缩后必要规则仍可恢复。全部宿主共用整理后的文件并保持同哈希，需要回归原三个宿主的技能契约。

## 5. 原生安装、索引与分发

### 5.1 两种受支持的安装来源

首轮同时准备原生 tarball 和固定 Git bundle，但不要求用户发布到 npm：

| 来源 | 制品 / 入口 | 用途 |
| --- | --- | --- |
| Release tarball | `<id>-<version>-dsh-plugin.tgz` | 下载后由官方 CLI 安装，便于离线交付与字节核对 |
| Git 子目录 | `published/dsh/<id>/<version>/`，固定实际提交 D | 索引和在线安装的正式来源 |

用户后续安装形式如下；尖括号为发布时生成的真实值：

```sh
dsh plugin --profile <已有profile> add ./codevow-2.0.0-dsh-plugin.tgz
dsh plugin --profile <已有profile> add 'git+https://github.com/Zack-Zz/ai-code.git#<D>&path:/published/dsh/codevow/2.0.0'
```

本地开发使用 `dsh plugin --profile <隔离profile> add <构建包的绝对目录>`。需要完整 Web 体验时先用官方 `--from-default-profile web` 创建一个新名字的测试 profile，再安装；`dsh plugin` 自己初始化的 profile 以 base 为基础，不自动等于 Web profile。

tarball 遵循 npm 的 `package/` 根目录格式，由公共构建工具以排序路径、固定时间戳/权限和固定 gzip 元数据生成。拒绝逃逸、符号链接、重复成员、特殊文件和缓存；独立检查器解包后从可信源码重算全部文件和哈希，不执行包内脚本。不把现有三端 ZIP 改后缀充当 DSH 安装包。

### 5.2 官方格式的插件索引

新增公开索引 `published/dsh/index.json`，URL 为 `https://raw.githubusercontent.com/Zack-Zz/ai-code/main/published/dsh/index.json`。该路径是本仓库的选择，不是 Harness 自动扫描的约定。用户在官方“自定义插件索引”功能中添加这个 URL；普通直接安装不依赖该实验性发现功能。

索引按上游 `format: 1` 生成，title/description 使用 `en`、`zh` 本地化对象；插件 name 为 `codevow`、`codestack`，展示 title 为品牌名称。每个当前稳定入口绑定精确 version、真实 Release 发布时间、与包一致的 `engines.dsh`，以及：

```json
{
  "type": "git",
  "url": "https://github.com/Zack-Zz/ai-code",
  "commit": "<实际40位分发提交D>",
  "path": "published/dsh/codevow/2.0.0"
}
```

这是字段形态示意，含占位符时不可作为有效索引发布。图标使用固定 D 上的 HTTPS 文件 URL；不依赖重定向。索引需要实测 HTTP 2xx、UTF-8、JSON 校验和包信息一致性。

沿用 `latest-stable` 策略：索引只列当前正式入口；preview 只发 Release，不写索引，不利用 Harness“没有 stable 时回退 preview”的能力。索引由本仓库受审核的发布记录生成，不从上游参考生成器扫描默认分支候选或依赖它识别本仓库的 `ID/vVERSION` 标签。

### 5.3 保持冻结源码 S 与安装提交 D 分离

先从冻结源码 S 构建、独立检查、公开 Release；正式部署阶段先将 Codex 和 DSH 必需安装文件写入同一 main 提交 D，再在后续提交 C 更新发行记录、当前指针、四份原生市场清单和回执。Git 类型入口全部固定 D，不引用移动分支或试图引用包含索引自身的 C。

DSH 安装目录与 tarball 去掉 `package/` 前缀后的文件闭包一致。`published/dsh/` 只保存原生 Git 安装所需文件，不保存 ZIP、TGZ、测试材料、私有验收或整个临时构建目录。根维护规则相应扩展到 DSH，`dist/` 继续禁止跟踪。

计划 schema 3 增加按宿主分组的 `git_install_files`，保存经可信源与原生安装器独立复验后的候选文件内容；候选 record 的 `git_installs.<host>.files` 保存同一受管路径到 SHA256 的映射，尚无分发提交时 revision 仅在候选阶段允许为 null。两份清单、来源 S、安装器哈希和全部字节都进入计划哈希。

D 阶段写本次候选的 `published/codex/<id>/<version>/` 与 `published/dsh/<id>/<version>/` 精确闭包，并在同一提交写入 `published/staged/<id>/<version>.json` 暂存回执；不更新 DSH plugin index 或当前指针。`stage_files`、`_existing`、GitWriter 路径策略与恢复逻辑同时扩展：候选路径之外的文件拒绝；已存在的待提交闭包须完整且同字节才能复用，部分或不同内容拒绝。写入后回读实际 D 的两端树，重算文件清单与包哈希，C 阶段才将非 null 的实际 D 绑定到正式记录与指针。

暂存回执 schema 1 固定包含产品 ID、版本、S、规范源码标签、源码闭包哈希、真实 Release 的 ID/URL、各安装器的名称/格式/大小/哈希、包哈希、按宿主分组的精确安装文件哈希、原计划基准 B、配置哈希和已审阅 plan hash；不含尚未产生的 D，不复制私有材料。它只描述待同步制品，不是正式发行记录或操作授权。

main CI 的 `marketplace check` 必须独立识别该中间态：即使没有传入 candidate，也从暂存回执读取声明，回到 S/标签重建并校验候选闭包、原 B 的配置与计划来源；按现有远端核验层核对公开 Release/安装器字节。只接受回执精确列出的文件，与正式 records 引用的闭包取并集；无回执的孤立目录、缺文件、错误哈希、身份/来源不符或冲突回执均拒绝。完整有效的 D 以“当前市场仍为旧版本；存在已验证 pending distribution”通过完整性门禁并输出 pending 列表，不宣称部署完成。离线无法完成的远端检查单独披露，不能据此降级源字节验证。

C 在一次原子提交中写正式记录、指针、退役事实、四市场和 lock，并删除对应暂存回执；安装文件保持不变。只有正式记录精确接收了相同来源、安装器和文件闭包，才允许消费回执。D 的历史 Git 提交保留回执原文；它的删除不等于删除冻结发行历史。暂存回执路径、闭字段和精确删除权限一起纳入 GitWriter 与计划复验。

中断后重新取 main 基准并重新计划，回读已核验的 D 暂存回执及其完整闭包后复用。D 将文件和回执原子写入，正常中断两者始终同时存在；没有回执的未记录安装目录一律拒绝，不因传入候选包就放行，也不推测 SHA。正式记录不接受 null revision。

## 6. 旧身份退役与历史保留

只修改 product ID 会让新旧插件同时出现在当前市场：现有分发按 ID 追加指针，并要求历史发行身份均有指针。因此需要显式退役契约，不能删除旧记录或做全仓文本替换。

### 6.1 数据设计

可信 `distribution.json` 升为新 schema，增加一次性一对一映射：

```json
{
  "identity_replacements": {
    "ai-code-workflow": "codevow",
    "ai-code-stack-standards": "codestack"
  }
}
```

该映射不复制版本、资源或展示名称，只声明迁移关系。验证旧 ID 已发行、新 ID 在当前 catalog、无环、无身份重叠、无多个旧 ID 指向同一目标；首轮拒绝链式替换。

`published/index.json` 升为 schema 3，分开保存 `plugins` 当前指针与 `retired` 的 old→new 映射。配置中的待迁移声明不能提前隐藏旧插件；只有新 ID 的正式 Release 完整验证、其声明宿主均具备入口、同一次市场提交成功后，才原子移除相应旧指针、加入新指针并写入 retired。

当前指针的字段形态如下；这是占位示例，0、尖括号和省略含义均不能用于实际发行数据：

```json
{
  "schema_version": 3,
  "plugins": {
    "codevow": {
      "version": "2.0.0",
      "source_revision": "<S>",
      "source_tree_hash": "<sha256>",
      "release_id": 0,
      "installers": { "claude": "<sha256>", "codex": "<sha256>", "zcode": "<sha256>", "dsh": "<sha256>" },
      "git_revisions": { "codex": "<D>", "dsh": "<D>" }
    }
  },
  "retired": { "ai-code-workflow": "codevow" }
}
```

`installers` 精确覆盖该记录声明的宿主，`git_revisions` 只包含使用 Git 安装的宿主；非 Git 宿主不填 null 占位。每个 pointer 必须等于其正式 record 的重算 snapshot，记录仍由 `<id>/<version>` 唯一定位。两插件分批切换时，另一插件可继续是旧 ID 的三端 active pointer，并且 `git_revisions` 仅有 codex。

两个插件可分别切换，每次只退役本次成功发布的对应旧 ID。切换后四份市场均从 active pointers 生成；不会在部分宿主退役、其他宿主仍发布旧 ID。失败时旧入口继续可用；不能先退役再等待发布新插件。

### 6.2 历史与反向验证

原样保留旧 Release、标签、附件、`published/releases/<旧ID>/`、`published/codex/<旧ID>/`、旧提交与它们记录的哈希。旧冻结源码仍按旧 catalog 和身份验证。

新的检查器将全部历史发行身份划分为 active 和 retired：active 精确覆盖未退役身份，指向其最高已同步稳定记录；retired 不得有 active pointer，目标必须已激活。退役事实单调追加，后续更新不得删除映射或让旧 ID 重新进入市场。

当前所有权回执由工具生成更新；旧提交中的回执保留。新回执除四份市场清单外绑定当前 index 字节，计划哈希绑定配置、退役变化和完整目标文件树。未知改动、并发 main 提交、旧 ID 再次发布或同版本不同字节均拒绝。

新 `published/marketplaces.lock.json` 使用 schema 2，字段固定为 `schema_version`、`files`、`published_index_sha256`。`files` 的键精确为 `.claude-plugin/marketplace.json`、`.agents/plugins/marketplace.json`、`marketplace.json`、`published/dsh/index.json`；值为对应字节的 SHA256。`published_index_sha256` 单独绑定 `published/index.json`，不哈希回执自身。DSH plugin index 是受管市场文件，与 active/retired 所在的 published index 明确区分。

### 6.3 用户迁移

旧用户通过各宿主原生方式卸载旧 ID，刷新同一个 `ai-code` 市场，安装新 ID，启用并开始新会话。DSH 首次安装不存在旧 DSH 插件需要迁移。

不自动卸载、不写宿主缓存、不创建旧 ID 的隐形安装别名；新旧插件提供相同技能名，因此迁移说明应要求先卸载旧插件。`.ai-workflow/` 项目数据保留。旧会话恢复能否加载旧插件内容属于宿主行为，逐宿主记录，不承诺无感续接。

当前操作文档只给新 ID。一次性迁移步骤放在有日期的迁移说明和此次双语发行说明中；历史报告保留旧命令、日期与结论。

## 7. 公共构建与发行数据改造

### 7.1 宿主格式不是简单增加一个字符串

目前 HOSTS、原生 manifest/marketplace 路径、ZIP 安装器、`codex_revision`/`codex_files` 都有三端假设。新增有限的宿主格式映射，明确各端清单、索引、安装器和传输；不增加任意代码 hook 或可执行配置插件。

| 宿主 | 原生 manifest | 当前市场 | 原生安装器 | 正式传输 |
| --- | --- | --- | --- | --- |
| claude | `.claude-plugin/plugin.json` | `.claude-plugin/marketplace.json` | ZIP | archive |
| codex | `plugin.json` | `.agents/plugins/marketplace.json` | ZIP | git-subdir |
| zcode | `.zcode-plugin/plugin.json` | `marketplace.json` | ZIP | url-zip |
| dsh | `package.json` | `published/dsh/index.json` | npm TGZ | 固定 Git bundle 子目录 |

公共校验区分四种原生清单/条目形态，不能让 dsh 落入“非 Codex 都使用 source 字符串”的分支。原三端传输行为保持。

### 7.2 资源与记录契约

为 product 增加可选 `host_resources`，按宿主列出显式 source/target/include 资源，用于 DSH patch、Reviewer guard 等；共同 resources 仍逐端相同。DSH 包清单模板位于 `adapters/dsh/package.json`，身份和版本由 product 覆盖生成；模板不成为第二个版本来源。每端独立检查目标冲突、链接和引用闭包。

Reviewer persona 是明确登记的生成资源，构建器只将共享 Markdown 合同序列化为 JSON；检查器从可信源独立重算，不能执行任意生成脚本。现有 Claude/ZCode 的 generated agents 维持其 `.md` 机制，不将 DSH preset 塞进 Markdown agent 模板。

新正式分发记录使用 schema 3，将 Git 安装绑定归一为 `git_installs`：

```json
{
  "git_installs": {
    "codex": { "revision": "<D>", "files": { "<受管安装文件>": "<sha256>" } },
    "dsh": { "revision": "<D>", "files": { "<受管安装文件>": "<sha256>" } }
  }
}
```

schema 2 旧记录的 `codex_revision`、`codex_files` 仅在读取时归一，绝不回写历史记录。新当前指针使用按宿主区分的 Git revisions；Release 制品记录保留各宿主的实际文件名、格式、大小、包哈希和安装器哈希，不能把 TGZ 当成 ZIP 验证。

schema 变更固定如下，均实施闭字段验证：两个迁移产品的 product schema 为 2，公共工具继续读取无新字段的旧 product schema 1；新的构建索引、Release bundle manifest、正式分发 record、plan、published index 及 distribution 配置为 3；lock 为 2；artifact 的文件哈希结构仍为 1。旧 Release 配置的 schema 1 不变，acceptance 按产品实际 hosts 覆盖。

旧 schema 2 published index 在内存中转换：沿用既有 snapshot 字段，将非 null `codex_revision` 放入 `git_revisions.codex`，去掉旧专属字段，`retired` 初始化为空。旧 record 的 codex 字段对应 `git_installs.codex`；其余宿主不产生 Git 项。转换结果只供新算法计算，旧 index/lock/records 的实际字节先按旧 schema 校验，不悄悄重写。

加入 dsh 源码支持后、首次新版本部署前，旧三端公开快照仍应通过检查；不能要求手工预写第四份空市场来让 CI 变绿。首次新部署在 C 原子生成新版 index、四市场与回执；旧正式 records 始终保留旧 schema。legacy 和新版市场路径集合依据已验证的 snapshot/lock schema 分派；独立验证过的 `published/staged/` 回执及其精确文件闭包可与二者共存，不能因此放开任意 published 路径。GitWriter 同时识别 DSH 安装前缀、plugin index 和暂存回执。

本地 `marketplace sync --output <空目录>` 为 dsh 生成独立开发索引；本地安装优先使用官方目录安装，不向正式索引写本机绝对路径，不覆盖公开 main 文件。

## 8. 文件与职责清单

| 范围 | 需要处理的主要内容 |
| --- | --- |
| 当前插件源码 | 两个目录迁移、product、adapters、release、技能 origin、Schema 标识、包内 README、辅助工具中的固定身份 |
| catalog / 项目规则 | catalog 仅登记新路径；根及插件 AGENTS、CONTRIBUTING、项目技能中的活动示例与四端边界 |
| 公共校验与渲染 | `registry.py`、`rendering.py`、`listings.py`、`references.py`、`cli.py`：dsh 清单、host_resources、生成资源、索引形态 |
| 包构建与检查 | `build.py`、`package_check.py`、`release/layout.py`、`release/integrity.py`：确定性 TGZ、独立闭包复验、四端包清单 |
| 版本与证据 | `release/core.py`、`acceptance.py`、`metadata.py`、`preparation.py`、插件 release.json：四端槽位、身份迁移、旧摘要失效处理 |
| 分发与市场 | `distribution.py`、`markets.py`：新旧 schema、active/retired、Git 安装提交、DSH 索引、回执、幂等与并发 |
| CI / 发布控制 | 三份 workflow 及 `.github/scripts/`：新 ID choices、TGZ 附件回读、D/C 两阶段、正式市场检查与预览隔离 |
| CodeVow 专属工具 | `scripts/workflow/` 的 HOSTS、产品校验、独立 build/package 与新路径；保持现有命令与退出码语义 |
| 测试和当前文档 | 原三端回归、新端及迁移用例、匿名 fixture；公开说明中英双语，内部本设计可中文 |

不能全局替换 `published/`、历史设计/review/evals 记录、旧资产 URL、标签或冻结哈希。旧图标 URL 只要仍指向有效不可变文件可暂时继续使用；更新活动 URL 必须先有实际可读取的固定提交，不能填写尚不存在的 SHA。

## 9. 实施顺序与验收门槛

每个行为变更先写有效失败测试，再最小实现、跑绿。以下阶段各自产生可审阅差异，最后统一验收。

1. **身份与退役基础**：新增 active/retired 契约和旧记录兼容测试；完成当前源码目录/ID 迁移，公开快照仍保留旧版本且校验通过。
2. **DSH 公共包格式与 CodeStack**：实现 bundle、声明式提供方、host_resources、TGZ、独立检查与原生索引；先验证最简单插件。
3. **CodeVow 与 Reviewer**：原样打包 Python 工具，增加原生 preset、spawn 工具、scope 限制与共享 persona；不改变默认用户 preset。
4. **共同技能结构整理**：拆分长正文，验证引用闭包、核心授权约束和四端共同资源哈希。
5. **发布控制与迁移说明**：四端正式构建、附件回读、Git 安装 D、市场 C、身份退役、双语说明和目标版本准备。
6. **独立检查与真实验收**：按下表分别记录；完成代码 Review 后交付未提交改动。后续 Git/公开发行须有对应授权，用户按原生流程重新安装。

### 9.1 本地与脚本门禁

| 范围 | 必须覆盖 |
| --- | --- |
| 身份 | 两个目标插件在当前 catalog 只使用新 ID，其余插件保留；旧冻结记录仍按旧 ID 校验；技能名和项目数据目录保留 |
| 资源 | 白名单、引用闭包、包清单 files、跨宿主共同哈希、host-only 文件不泄漏、链接和逃逸拒绝 |
| TGZ | npm 根格式、确定性、篡改/重复/特殊成员拒绝、解包后与可信源及 Git 安装内容一致 |
| 原生适配 | 官方提供方、包目录解析、无安装脚本、CodeStack 无自定义 JS，两个 provider 共存及卸载清理 |
| Reviewer | 首轮只有 read/grep/glob；直接发起禁止工具被拒绝；全局工具不漏入；scope、重载、恢复及创建失败不降级 |
| 分发 | 两阶段 D/C、D+暂存回执可独立通过 main CI、C 消费回执、孤立/篡改 staging 拒绝、固定 SHA、同版本幂等、并发拒绝、旧 schema、active/retired、退休 ID 不复活、preview 不入市场 |
| 历史与回执 | 旧 record/安装文件逐字节保留，未知文件拒绝；旧三端快照与新版四端快照分别按其 schema 验证 |

实现后的标准检查包括：`validate --all`、`npm test`、`npm run lint`、`check_no_dist.py`、全部注册插件的全部声明宿主构建、逐包独立检查、两个目标插件的 draft release check/prepare/verify。构建输出使用新建的空临时目录。`npm test` 仍需发现所有正式插件测试，不以只跑 dsh 测试代替公共门禁。

DSH 的 API 组合测试精确锁定所用官方依赖；不使用 mock 声称原生宿主加载通过。普通 Python/结构测试、真实 Cordis 组合测试、带模型的宿主场景分开报告。

### 9.2 真实宿主验收

| 编号 | 场景 | 成功条件 |
| --- | --- | --- |
| H01 | DSH 目录 / TGZ / 固定 Git 安装 | manifest、版本、bundle 层与包内字节正确；不要求安装时构建许可；缺服务 profile 的激活诊断明确，不误报完整可用 |
| H02 | DSH 技能发现与显式调用 | 两插件同时可见，`/workflow`、`/code-standards` 加载正确全文，引用路径有效 |
| H03 | 自动选择与任务结果 | 匿名任务实际选中适用技能，规则效果与不适用边界分别有记录 |
| H04 | CodeVow policy / Python | 安装路径解析、默认/项目策略、错误处理与无 Python 披露符合现有契约 |
| H05 | 原生 Reviewer | 独立 spawn、正确 preset、只读工具、禁止调用拒绝、结果回传；主代理复核 findings |
| H06 | 长会话 | 压缩压力后没有把缺失规则当作已加载，必要指令可按引用恢复 |
| H07 | 生命周期 | 两插件分别启停、卸载、重新安装；HMR/重启与缺服务诊断准确；空白会话双向切换 Reviewer/standard 后限制正确增删，不影响普通会话 |
| H08 | 索引发现 | 官方添加索引、HTTPS 无重定向、正确来源确认、精确 commit/path/engines、安装结果一致 |
| H09 | 原三个宿主改名迁移 | 卸载旧 ID、刷新市场、安装新 ID、开启新会话；技能与 CodeVow 项目数据回归 |

每端记录实际宿主版本、平台、模型、安装来源、制品哈希和验收材料。工具白名单与文件权限根分别验证；未运行的 profile/平台/模型标记未验证。发布成功和包检查通过都不能代替上述结果。

技术发行仍沿用仓库既有规则：未验收槽位可保持 null/pending，不把它写成 accepted。对外声称 DSH 原生支持已实测时，至少须有目标 Web profile 的加载、调用、引用、生命周期和适用 Reviewer 场景证据；缺项明确列出，不借本方案产生通过标记。

## 10. 发布失败与恢复

- 新 Release 未完成：旧市场不变，不退役旧 ID。
- Release 已公开而 D/C 未完成：报告“已发布、市场待同步”；同版本同字节可重试，不覆盖附件或移动标签。
- D 已写入、C 未完成：旧入口继续工作；保留暂存回执及安装文件，main CI 验证 pending 完整性；重新按当时 main 基准生成计划，不强推、不把 orphan 目录当作可忽略内容，也不删除历史文件。
- C 已切换后发现问题：停止后续发行；退役旧 ID 保持退役，以新 ID 的更高版本发布修复或恢复先前行为。新 pointer 不能直接指向旧 ID 的 record，也不重新激活旧 ID；本次方案不提供恢复旧身份的例外通道。
- 宿主不兼容：按照 engines 正常拒绝；不要求用户开启版本豁免、允许任意安装脚本或关闭权限保护。

## 11. 本轮方案核验与实施前检查

本轮做了本仓库及上游固定提交的源码/配置核对、公开版本检查、技能字符数核算和文档结构检查。另由只读探索代理核对身份退役链路，由架构顾问核对原生 Reviewer 与提供方层级；主代理决定最终方案。

方案阶段只完成只读核对；实施后的源码、构建、测试、原生 API 组合及宿主验收边界另见本次实施与验证记录，不将方案核对结果当成实现通过。

开始实现前重新核对当前分支、已有改动、发行指针和上游版本；若上游 API 或用户范围变化，更新受影响设计后再实现。没有变化时沿用本方案，不重新推导已确认的 ID 选择和重新安装决定。

## 12. 证据与参考

### 本仓库当前实现

- [产品与宿主校验](../../tooling/plugin_tools/registry.py)：当前三端 HOSTS、资源和 generated agents 限制。
- [原生清单渲染](../../tooling/plugin_tools/rendering.py)：当前 manifest/marketplace 形态和资源生成。
- [正式分发](../../tooling/plugin_tools/distribution.py)：ID 指针、历史记录、D/C 与受管路径校验，尤其 `_existing` 的身份集合相等条件。
- [公开快照检查](../../tooling/plugin_tools/markets.py)：回到冻结源码校验旧 ID、制品与固定 Codex 安装目录。
- [发行结构](../../tooling/plugin_tools/release/layout.py)、[部署控制](../../.github/scripts/deploy_marketplace.py)：当前 ZIP 假设和 Codex 专属字段。
- [已发布指针](../../published/index.json)、[证据契约](../release-evidence.md)：当前已发布版本与验收边界。
- [CodeVow 清单](../../plugins/codevow/product.json)、[CodeStack 清单](../../plugins/codestack/product.json)：本方案写作时的当前路径；实际目录迁移后同步这些活动引用。

### Harness 官方固定提交

以下均为 `22ddee3792402c3e70ec5f86a63c3e3e895a2f60`，用于设计依据，不代表已运行验收：

- [组合包、profile 与安装](https://github.com/deepseek-ai/deepseek-harness/blob/22ddee3792402c3e70ec5f86a63c3e3e895a2f60/docs/user/develop/basic/publish.zh.md)：`dsh.bundle`、patch、Git 安装与脚本授权。
- [插件展示元信息](https://github.com/deepseek-ai/deepseek-harness/blob/22ddee3792402c3e70ec5f86a63c3e3e895a2f60/docs/cookbook/adding-a-package.zh.md#plugin-display-metadata)：locale、品牌标题、图标与包字段回退；内部 monorepo 包约束不直接套到第三方 bundle。
- [技能文件系统提供方](https://github.com/deepseek-ai/deepseek-harness/blob/22ddee3792402c3e70ec5f86a63c3e3e895a2f60/packages/skill/skill-filesystem/src/index.ts)：独立提供方、资源根、bundled rank 与生命周期。
- [官方技能路径解析示例](https://github.com/deepseek-ai/deepseek-harness/blob/22ddee3792402c3e70ec5f86a63c3e3e895a2f60/packages/bundle/web-app/presets/cordis.patch.yml)：使用 baseUrl 和包清单定位技能目录。
- [技能注册与分层](https://github.com/deepseek-ai/deepseek-harness/blob/22ddee3792402c3e70ec5f86a63c3e3e895a2f60/packages/skill/skill/src/index.ts)、[技能调用工具](https://github.com/deepseek-ai/deepseek-harness/blob/22ddee3792402c3e70ec5f86a63c3e3e895a2f60/packages/skill/tool-skill/README.zh.md)：resourceBase、同名遮蔽、`skill` 与 `/name`。
- [原生子代理](https://github.com/deepseek-ai/deepseek-harness/blob/22ddee3792402c3e70ec5f86a63c3e3e895a2f60/packages/subagent/tool-subagent/README.zh.md)、[preset 选择源码](https://github.com/deepseek-ai/deepseek-harness/blob/22ddee3792402c3e70ec5f86a63c3e3e895a2f60/packages/subagent/tool-subagent/src/preset-selection.ts)：spawn 与独立 preset，废弃字段和路由约束。
- [工具约束源码](https://github.com/deepseek-ai/deepseek-harness/blob/22ddee3792402c3e70ec5f86a63c3e3e895a2f60/packages/core/tools/src/index.ts)、[创建生命周期](https://github.com/deepseek-ai/deepseek-harness/blob/22ddee3792402c3e70ec5f86a63c3e3e895a2f60/packages/core/agent/src/index.ts)：restrict/guard 的 scope 和首轮前监听器。
- [文件工具配置](https://github.com/deepseek-ai/deepseek-harness/blob/22ddee3792402c3e70ec5f86a63c3e3e895a2f60/packages/fs/tool-fs/README.zh.md)、[工具结果修剪](https://github.com/deepseek-ai/deepseek-harness/blob/22ddee3792402c3e70ec5f86a63c3e3e895a2f60/packages/compaction/compaction-tool-result-pruner/README.zh.md)：只读组合与压力触发的长度预算。
- [索引格式](https://github.com/deepseek-ai/deepseek-harness/blob/22ddee3792402c3e70ec5f86a63c3e3e895a2f60/docs/user/guide/plugin-market.zh.md)、[索引服务](https://github.com/deepseek-ai/deepseek-harness/blob/22ddee3792402c3e70ec5f86a63c3e3e895a2f60/packages/boot/plugin-market/README.zh.md)：Git commit/path、安装目标、HTTPS 与升级边界。
- [运行版本兼容与 profile 加载](https://github.com/deepseek-ai/deepseek-harness/blob/22ddee3792402c3e70ec5f86a63c3e3e895a2f60/packages/boot/app-boot/README.zh.md)：engines 优先、peer 回退、preset 与 profile 组合检查。

## 13. 实施调整（2026-10-27）

- 官方 npm 当前可安装的是 `0.2.1-rc.2`；RC3 源码中的独立 native executor 包尚未发布。改按已发布 RC2 的 `agent-tool-presentation`（mode:native）和 `modelSelectionSettings:false` 适配，engines/peer 精确对应 RC2。原始 Git 研究提交仍保留，实际 API 证据以隔离安装的官方 RC2 包和组合测试为准。
- D 暂存文件与 receipt 必须原子存在；取消无 receipt 的 orphan 目录恢复例外。独立 main 检查与计划生成都拒绝孤立目录。
- 含 DSH 的 build/Release 索引使用 schema 3；纯旧格式构建继续输出 schema 2，以保持旧源码制品的可重算字节。正式分发记录与计划统一使用 schema 3，并只读兼容旧记录。
- 可选 files 工具暂存与回执命名空间跟随新 ID，旧空间保留但不被新插件认领；旧 ID 文件计划须重新生成，policy/tasks/evidence 原有目录和数据契约保留。
- 技术验证、原生 API 组合和真实带模型会话分开报告；依赖安装成功不等于 H01–H09 全部通过。
