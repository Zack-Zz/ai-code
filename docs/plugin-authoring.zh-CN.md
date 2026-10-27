# 接入一个 AI 插件

[English](plugin-authoring.md) | 简体中文

本指南适用于在 ai-code 仓库加入独立的 AI 相关插件。先定义插件用途、最小
内容和实际目标宿主，再注册目录。已有 workflow 只是一个插件实例；新插件
不必包含它的策略、任务记录、Reviewer 或六份技能。

环境准备、修改现有插件和本地试用先看[开发指南](../CONTRIBUTING.zh-CN.md)。
本指南聚焦新增插件。所有命令在仓库根运行，维护规则见 [AGENTS.md](../AGENTS.md)，
发行操作见[发布指南](publishing.zh-CN.md)。

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
插件的相对路径列入资源。README 面向使用者说明用途、安装方式、使用步骤和必要依赖。
发布前流程、宿主验收与开发测试记录放在维护文档中，不写入用户 README。

面向外部读者的 README、安装、使用、配置及其他公开说明必须中英双语，默认
英文，顶部提供双向语言切换，双语指南之间的链接保持所选语言。设计、实现、
验证记录和内部维护资料可以仅用中文，不要求全部翻译；已有译文可以保留。

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
中维护第二份开发版本。新的公开版本仅使用 `X.Y.Z` 或 `X.Y.Z-preview.N`，
数字禁止前导零，不接受其他后缀或 build metadata；preview 序号按数字比较，
同核心正式版在所有 preview 之后。发行种类由版本派生。

`hosts` 必填且非空，当前接受 `claude`、`codex`、`zcode`、`dsh`；每个声明
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
`host/template/body/target`，当前接受已声明的 Claude Code / ZCode 宿主及 agents/*.md 目标，
只做数据化正文合成，不执行代码 hook。

纯资源能被校验和打包，不能证明某个运行能力已可用。新的宿主组件形态必须
先明确原生清单、启动/权限行为及真实会话验收，再扩展支持。

### 可选市场展示元数据

在 `product.json` 中声明 `host_listings`，可为指定宿主启用市场展示元数据。
每个键对应的宿主必须已在 `hosts` 中声明。`claude: {}` 启用 `displayName`；
ZCode 必须且只能声明 `icon_path` 与 `icon_url`，启用 `displayName` 和 `icon`。
生成的 `displayName` 始终来自显示名称的唯一来源 `product.display_name`，
不要在 `host_listings` 或适配模板中复制名称。

CodeVow 可使用已有公开 PNG，声明片段如下：

```json
{
  "host_listings": {
    "claude": {},
    "zcode": {
      "icon_path": "assets/codevow.png",
      "icon_url": "https://raw.githubusercontent.com/Zack-Zz/ai-code/91dec3a64731f8de2fb68e49bce9f4228289bbbd/plugins/codevow/assets/codevow.png"
    }
  }
}
```

该片段要求 `hosts` 已声明 `claude`、`zcode`，且 PNG 已登记到 `resources`。
用于其他插件时，宿主和资源声明需一起匹配。`icon_path` 是显式资源白名单中
PNG 或 SVG 文件的规范打包 **target**；`icon_url` 对应实际 **source** 路径，
必须属于 `repository` 声明的同一 GitHub 仓库，source 与 target 可以不同。
URL 使用 HTTPS `raw.githubusercontent.com`，固定到完整的 40 位 Git commit SHA；
拒绝 branch、`main`、tag、凭据、query string 和 fragment。

未声明 listing 的宿主保持原有输出。已声明的元数据会生成到本地市场，并记录到
正式发行记录中供公开市场使用。原生插件清单继续遵守各宿主契约，该选项不向
ZCode manifest 额外添加品牌字段。Claude Code 不读取 PNG `icon` 字段，因此
其空对象只启用安装前的市场显示名称，见官方
[目录展示字段说明](https://code.claude.com/docs/en/plugins/manifest-reference#directory-listing-fields)。

URL 静态校验不能证明图片可访问或宿主实际展示成功；URL 获取与真实宿主验证
需分别报告。包括 CodeVow 1.0.3 在内的冻结公开记录不可手工修改。源码变更提交后，
通过正常[发行流程](publishing.zh-CN.md)发布后续新版本，公开市场才会更新。

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

声明 Claude Code 时提供 `adapters/claude/plugin.json`，构建输出
`.claude-plugin/plugin.json`。`displayName` 从 product 派生，namespace ID
保持稳定。可选 `publisher` 只含公开 `name`、HTTPS `url` 和 `email`；工具
统一生成 native author 与 Codex developerName，不在适配模板复制署名。

开发市场由工具统一生成，不需要新插件提供 marketplace 模板。公开 main
市场从已核验正式发行记录生成，不从当前开发清单直接同步。workflow
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
python3 tooling/plugin_tool.py build --plugin ai-example --host codex --output /tmp/ai-example-packages
python3 tooling/plugin_tool.py package check \
  --path /tmp/ai-example-packages/codex/ai-example --host codex --root .
npm run lint
```

`/tmp/ai-example-packages` 必须不存在或为空；重复验证使用新的空目录。`--all` 可校验
或构建全部登记插件。`--host all` 按各插件 hosts 生成对应产物。

包检查使用可信仓库 `--root` 独立重建预期资源闭包，重算实际文件哈希并
核对原生清单和市场 source。不要调用尚未验证的包自己的 Python 文件作为
初始验证器。`ok` 不表示作者身份已认证，也不表示宿主实际执行了组件。

公共包检查拒绝全部未登记文件，包括可以被 Python 执行的 `.pyc` 缓存。
先验证发行包，再运行包内代码；需要保持产物可复验时使用 Python `-B`
或 `PYTHONDONTWRITEBYTECODE=1`。采集注册插件的输入及复查时始终从仓库根遍历目录，
不把插件子目录重新作为允许跟随父目录链接的信任根。

构建输出 `<output>/index.json` 使用 schema_version 2，按 plugins/ID/hosts/HOST 记录
各包路径和哈希，按 hosts/HOST 记录聚合市场。插件自己的 artifact 保持自身
身份和来源。修改一个插件时核对兄弟插件内容和哈希不受影响。

开发市场使用显式空输出目录，注册对应的 `<output>/<host>`：

```sh
python3 tooling/plugin_tool.py marketplace sync --output /tmp/ai-example-development
python3 tooling/plugin_tool.py marketplace check --root .
```

sync 在临时目录生成注册源码的三端开发市场；check 只读核验公开快照的
冻结源码 S、安装内容与固定 Codex 分发提交 D，不要求正式版本等于当前
开发版本。`dist/` 是被忽略的临时构建输出，不得提交或推送；CI 拒绝跟踪
该目录，公开制品保存为 Release 附件。

需要发行准备时增加插件 `release.json` 和可移植双语说明，见
[发布指南](publishing.zh-CN.md) 与[验收契约](release-evidence.zh-CN.md)。这些输入属于
发布机制；仅构建资源包的插件无需被强制套用当前 skills-only 上架 profile。

## 6. 交付与原生验收

每个宿主目录有名为 `ai-code-local` 的聚合市场；各插件 ZIP 只包含自身包和
单插件市场。解压到稳定目录后按宿主原生方式注册，见现有
[用户安装指南](installation.zh-CN.md#下载包安装)中的本地市场步骤。
原生命令与版本支持仍需对应插件实际验证。

catalog 登记和开发试用不等于正式发行。新预览版只进入 GitHub Prerelease；
正式版本通过源码与包检查、公开并成功同步后才进入 main 单市场。真实宿主
验收单独报告；尚未验收的宿主保持 `unverified`，不阻止技术发布。
同一 ID 只有一个当前入口，没有正式版的插件暂不出现在公开市场。
`published/index.json` 与正式记录描述已上线版本，不是第二份开发版本来源。

插件支持说明要分别报告源校验、脚本测试、包检查、原生加载和实际行为。
记录宿主版本、模型、包哈希及会话证据；尚未验收写 `unverified`。为 MCP
增加普通资源文件不代表配置发现、认证、server 启动或工具调用已经支持。

交付时保留未提交改动，给出摘要、diff、验证结果和剩余限制，等待用户
Review。commit、push、tag、merge、PR、安装与发布仍遵守独立授权边界。

## DeepSeek Harness 适配

具有宿主专属资源的产品使用 product schema 2；冻结源码和未变化插件仍可读取
schema 1。将 `dsh` 登记到 hosts，原生模板为 `adapters/dsh/package.json`，
patch、locale 等在 `host_resources.dsh` 中使用显式 source/target/include 白名单。

DSH 清单声明 `type: module`、精确 engines.dsh、exports 和 dsh.bundle.patch。
name、version、精确 files 清单由可信 product 输入生成。禁止私有 bundle 和
安装生命周期脚本。展示使用 locale/en.json、locale/zh.json 的 meta.title、
meta.description 及包内图标；清单校验不能替代真实宿主验收。

Host 层挂载官方 skill-filesystem 提供方，使用唯一 providerName、
includeDefaultRoots:false 和按包目录解析的 bundledSkillDir；技能仍是共享资源。
纯资源 bundle 不需要自定义模块。只有 CodeVow 提供 Reviewer guard，并以固定
json-string 转换从共同审查合同生成 reviewer-persona.json，不支持任意构建 hook。

DSH 原生安装器为 package/ 根目录的 npm TGZ。包含 DSH 的构建索引使用 schema 3，
字段为 archive、archive_sha256、archive_format:npm-tgz；原三端 ZIP 字段保留。
本地 format-1 索引仅为结构预览，开发使用原生绝对目录安装；公开 Git 入口必须
在发布后生成。
