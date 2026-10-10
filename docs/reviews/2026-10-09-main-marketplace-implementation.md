# main 统一分发实施与验证

日期：2026-10-09（Asia/Shanghai）。本轮为本地代码实施，Git 交付与远端发布
分别记录；不把测试 fixture 的 accepted 状态当作真实宿主验收。

前段保留首次交付快照；最终代码与验证结果以文末“Review 后修复”记录为准。

## 范围与基线

基线 HEAD 为 `fbb3614`，开始时已有 `.gitignore` 注释与新版设计的 dist
排除补充；均保留并继续完善。工作区的 dist 已忽略，跟踪文件数为 0。
基线 `npm test` 通过五个组，原有插件源码、版本和实际 acceptance 槽不变。

需求为 main 统一源码和公开市场、同插件 ID 的单一正式入口、预览版仅公开
Release、独立插件版本、GitHub 构建制品，以及 dist 不进入新提交。
市场内部名称继续为 `ai-code-preview`，未执行全局重命名。

## 实施结果

- 公共版本模块支持 `X.Y.Z` 与 `X.Y.Z-preview.N`，严格语法、数值顺序和
  历史 bundle 比较共用一套规则；历史 numeric Prerelease 仍可复验。
- `distribution.json` 改为 schema 2、main、latest-stable。正式发行记录、
  当前指针与回执使用 `published/`；三份根市场只从该状态生成。
- GitWriter 仅 patch 审阅过的 main 发布路径，保留源码对象、执行位及链接；
  实际 D 的安装字节先写入，C 的清单再固定 D，拒绝旧基准和强推。
- 公开快照独立读取实际 S/D，重算包与 installer 哈希；检查已发布状态不
  重读私有原始日志，也不生成新的宿主验收结论。
- 开发市场必须显式输出到临时目录。根市场迁移只接受精确匹配的旧开发
  清单和所有权回执，未知或用户编辑的内容拒绝覆盖。
- CI、Release plugin、Sync plugin marketplace 已调整；版本后缀决定
  发布种类，三端 ZIP 在 runner 生成，正式成功后显式调用同步任务。
- Draft 与公开步骤分开，上传附件后逐件回读字节及来源再公开；不覆盖
  既有版本。包括供应 Draft 回执的入口，也拒绝与源码声明不同的目标仓库。
- 双语 README、作者指南、架构、发布指南和 AGENTS 已更新。CodeVow 的
  历史发行材料未改；其旧 CI 回归测试改为直接验证本地比较器，保留全部
  损坏拒绝断言，不再解析已经移除的 committed-dist 步骤。

## RED 与修复证据

以下为实际退出 1 的目标行为失败，非缺少测试依赖：

| 目标 | RED 原因 | 修复后的检查 |
| --- | --- | --- |
| 预览语法与顺序 | registry 拒绝 preview、放行前导零；旧整数拆分无法比较 preview | 版本、注册、构建与历史比较测试 |
| main 安全写入 | 旧配置无 main；写入器拒绝 main，却允许创建旧试用分支 | 真实 bare Git 的源码/模式/链接保留与旧分支拒绝 |
| 正式默认入口 | 旧 planner/deploy 仍读取 channels 双分支结构 | 正式快照、固定 D、多插件、幂等、过期和失败回执 |
| 无 dist 的公开检查 | 检查仍强制读取缺失的 dist | 空正式市场与干净源码快照检查 |
| 开发输出与受控迁移 | CLI 无 initialize 或显式 output 参数 | 迁移回执、开发输出和源树不变 |
| 公共 S/D 验证 | Git archive 父目录被误拒绝，后续检查误需私有证据文件 | 真实 S/D/C 且私有证据未入 Git、验证后删除 |
| 旧 installer 被重写 | 修改摘要并同步重算所有清单回执仍被放行 | 从 S 重算实际 installer SHA/大小，拒绝伪造 |
| preview 同步回执 | 工作流 summary 强索引不存在的 main lease 字段 | 执行 inline Python 验证成功退出且无部署 lease |
| 新发行种类 | numeric 未验收版本可被创建为 Prerelease | 新 stable 必须通过 stable 门禁，preview 与后缀一致 |
| 跨仓库写入 | Draft 或已有回执可针对其他仓库继续调用 GitHub | 写前目标绑定，错误输入在任何网络调用前拒绝 |

基线和测试日志保存在当前工作会话的临时目录，不进入公开插件包。
真实 Git/ZIP/本地 HTTP 用于验证传输和写入逻辑，GitHub API 写入使用 fake
transport，没有在本轮创建真实 Release、tag 或部署提交。

## 验证状态

最后功能改动完成后运行 `npm test`，退出 0，五个组全部通过：公共 Python
215 项、CodeVow Python 302 项、Agent Delegation Python 35 项，加上汇总器
13 项 Node 测试和两份技能契约文件。日志为本次工作会话的
`/tmp/ai-code-main-final-suite.log`。没有用此前通过结果代替最后代码状态。

已完成的定向检查：

- main 部署测试 22 项、工作流与公开快照测试 12 项，以及历史比较器回归
  32 项通过；发布保护加入后另行运行对应测试。
- `npm run lint`、公共 `validate --all`、`marketplace check`、tracked-dist
  检查与 `git diff --check` 通过。
- 官方 checksum 验证的 actionlint `v1.7.12` 检查三份 YAML 通过；没有运行
  shellcheck/pyflakes，不能把语法检查当作真正 Actions 成功。
  发布步骤使用的 `gh release edit` 参数也与本机 help 及
  [官方说明](https://cli.github.com/manual/gh_release_edit)核对。
- 未复制 dist、node_modules 或 Git 元数据的源码快照，在
  `/tmp/ai-code-clean-checkout-qb8ebwi0/source` 完成 source validate、公开市场
  check、两插件三端构建及六包独立 package check。
- CodeVow 资源源哈希仍为
  `24793827cd6d0c2d2e890a12f671575afd1cf9ba5b1a68d7f4355e0b711e6ae9`；
  Agent Delegation 资源源哈希仍为
  `69b69870234f86c9d8e45e0e3b3a7ae0a932ab8cecfe62d07ff52e4bd2b6214c`。

主代理审阅全部整合 diff；code_implementer 独立负责版本模块、流水线及
文档。另一个 code_reviewer 独立静态审阅 main 租约/受管写入/D/C 历史
以及公共 S/D/私有日志边界，两个限定范围均无已确认 finding。该 reviewer
未运行测试、调用远端或审阅全部工作流，最终验证由主代理完成。

## Git、发布与宿主边界

本地根市场已通过受控迁移成为空正式快照。仓库 `.agents` 路径需要限定
写权限；第一次受保护路径失败后只回退了本次已完成的第一项写入，再以
已授权的仓库路径权限完成迁移。没有触碰用户全局市场或宿主缓存。

本轮未 commit、push、tag、创建 PR 或改变 GitHub 设置，未部署远端新
机制；新的三份 YAML、环境审批、GITHUB_TOKEN main 写入和公开回读需要
Git 交付后实际执行验证。没有把本地 fake transport 当作远端环境通过。

CodeVow `1.0.2` 的原标签、不可变 Prerelease 和旧 preview 分支保持历史
试用用途。CodeVow 和 Agent Delegation 的真实 stable 验收尚未完成，根
市场不列出任何正式插件。第一份正式入口须由真正合格的新版本生成；
本轮不把旧预览标志改成正式，也不修改 acceptance 来放行。

三端 main 来源迁移、原生加载、连续两个正式版本升级及 Codex 先前的
市场刷新超时均未在本轮重新验收。用户可 review 本地 diff 后，分别授权
Git 交付与真实发布/安装操作；此前有日期的安装证据保留原适用范围。

## Review 后修复

四项确认缺陷已修复，改动继续保留未提交：

1. GitHub 干净 checkout 缺少私有验收材料：新增本地严格验收后的
   `release acceptance-export`，只输出 `release/acceptance-proof.json` 的
   公开哈希声明。维护者审核后随源码标签冻结；Prepare、Draft、Publish、
   市场计划、部署和历史复验显式使用 committed 验收。默认本地命令仍要求
   实际私有文件；声明自身绑定 HEAD，所有公开输入、宿主包与私有摘要精确
   核对。原始日志、summary 和验收 JSON 正文不复制到声明或公开包。
2. CodeVow 自带工具拒绝 preview：product、schema、回执复用一致的规范
   版本规则；包内独立工具支持 preview 的检查、stage、update 重读和 remove。
3. 初始化覆盖并发编辑：固定使用最初已验证的字节作为基准，不重新采纳
   后来的人工修改；完成前重新检查全部文件。
4. 初始化中断后无法重试：以被忽略的 `.marketplace-initialize.json` 保存
   已验证基准，恢复时仅接受原值或目标值；遇到人工修改、未知所有权回执或
   链接均拒绝。全部目标完成后才删除恢复记录。

独立复审补充的保护也完成有效 RED/GREEN：HEAD 已有声明时，隐藏删除
不能回退到本地验收；导出与 CI 读取共用 1 MiB 上限；后续编辑已完成的
初始化目标时保留恢复记录；空根中的未知旧回执不被删除。

有效 RED 日志为本轮临时文件：`/tmp/ai-code-initialize-red.log`、
`/tmp/ai-code-handoff-red.log`、`/tmp/ai-code-proof-boundary-red.log`、
`/tmp/ai-code-initialize-final-check-red.log` 和
`/tmp/ai-code-initialize-ownership-red.log`。preview 的 RED/GREEN 由独立
code_implementer 实际执行，主代理在最终统一门禁重新验证。

最终 `npm test` 退出 0，五组通过：公共 Python 230 项、CodeVow Python
308 项、Agent Delegation Python 35 项、Node 汇总器 13 项与两份技能契约。
日志为 `/tmp/ai-code-review-fixes-final-suite.log`。其中新 handoff 10 项
用真实 Git、ZIP 和本地 HTTP 验证：私有文件未入 Git 的干净 clone，成功
完成 stable 准备、附件发布校验和市场计划；与本地 strict 模式的完整
bundle 逐字节相同。GitHub 调用仍为 fake transport，不是实际远端发布。

统一门禁首次重跑时 8 项旧 Draft 测试缺少真实 HEAD，已补齐临时 Git
fixture，保留未绑定制品的原始断言；定向 16 项及最终统一门禁均通过。
最终 lint、actionlint、source validate、公开市场 check、tracked-dist 与
`git diff --check` 通过。两插件六个宿主包均完成构建和独立 package check，
输出为 `/tmp/ai-code-fixes-packages-pb7semj3/packages`。

主代理检查整合 diff 并执行最终验证；code_implementer 独立实现 preview
兼容；code_reviewer 独立审查验收摘要、调用链与初始化恢复的最后代码，
本限定范围无未解决阻塞项。Reviewer 未独立执行测试或远端操作。

CodeVow 资源源哈希已变为
`6c06940053f2317ccce71f9f4c31b312971e389a1df2b18e9cf76812f0ea6c42`；
其版本和实际 acceptance 槽未修改。Agent Delegation 资源哈希不变。
后续发行必须使用新版本并重新做真实宿主验收，不能覆盖不可变的 1.0.2。
声明是维护者事实记录，不是会话真实性认证；两个环境审核仍承担发布授权。
POSIX 逐文件原子替换不构成与外部编辑者之间的完整目录事务。

本轮没有 Git 交付、远端设置变更或真实宿主安装。实际 GitHub Actions、
首次正式 Release 与连续版本的三端升级验收继续作为独立后续工作。

## 2026-10-10 再审与交付检查

用户授权本轮重新 review，确认无问题后 commit、push 到 main。主代理重新
审查当前整合 diff、版本与市场生成、初始化恢复和文档；独立 code_reviewer
重新审查三份 workflow、发布/同步 helper、验收传播与失败路径，确认 finding
为 0，并实际运行 5 个限定模块，68 项通过。此前结论未代替本轮检查。

最终代码重新执行 `npm test`，退出 0，五组全部通过：公共 Python 230 项、
CodeVow Python 308 项、Agent Delegation Python 35 项、Node 汇总器 13 项
及两份技能契约。日志为 `/tmp/ai-code-main-delivery-2026-10-10-tests.log`。
lint、source validate、公开市场 check、tracked-dist、actionlint 和
`git diff --check` 均通过；两插件六个宿主包重新构建并独立检查通过，输出
为 `/tmp/ai-code-main-delivery-2026-10-10-fd460j0v/packages`。

交付前本地 main 与远端 main 均为 `fbb3614`，所有改动属于本轮已审查范围。
Git 交付只发布源码与流水线配置；不创建插件标签、Release 或安装插件。
远端 Actions 的运行结果、受保护环境实际权限与真实宿主验收另行记录。
