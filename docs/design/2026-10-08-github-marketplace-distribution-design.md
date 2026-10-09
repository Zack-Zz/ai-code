# GitHub 插件市场与制品分发设计

设计日期：2026-10-08（Asia/Shanghai）；执行反馈更新于 2026-10-09。
状态：已公开 CodeVow 1.0.2 prerelease 并部署 preview 市场；三端
原生安装和制品字节已验证，完整宿主验收仍待完成。当前结果见
[原生安装记录](../reviews/2026-10-09-preview-marketplace-native-installation.md)。
[实施与验证记录](../reviews/2026-10-08-github-marketplace-implementation.md)
分别记录代码、环境配置、Git、公开发行与安装状态。

本次补充：多个插件独立发版、市场统一汇总、单插件市场部署的操作入口、
部署计划与状态契约、批量发布的后续边界。第 5.2–5.5 节给出部署操作细节。

用户要求设计项目与 GitHub 设置的调整，使用户通过宿主原生入口安装发行
内容，无需手动下载开发源码或运行构建。本稿按同一仓库
`Zack-Zz/ai-code` 组织；“同仓库还是独立市场仓库”的偏好尚未收到答复，
同仓库是本稿的默认方案。本文不授权创建分支、提交、推送、标签、Release、
远端设置变更或宿主安装。

## 1. 结论与方案选择

GitHub 提供 Git 仓库、Releases、Actions 等能力；具体插件市场协议由
Claude Code、Codex、ZCode 定义。这里的“GitHub 市场”是原生清单加发行
内容的自建市场，不是 GitHub 提供的跨 Agent 统一插件注册中心。

| 方案 | 优点 | 成本与限制 | 选择 |
|---|---|---|---|
| 同仓库：源码分支、发行分支、Release 安装包 | 无额外仓库或跨仓库凭据；用户安装与开发源码分开 | 需要发行分支、三端来源适配、发布状态校验 | 本轮推荐 |
| 独立市场仓库加 Release | 开发权限与发行权限可以分开；市场仓库只含发行内容 | 新增仓库、凭据和跨仓库同步 | 团队需要独立发行权限时再采用 |
| npm 包分发 | Claude、Codex 文档提供包来源；包版本可独立管理 | 新增 package/registry 契约；GitHub Packages 的认证和 ZCode 兼容需验证 | 本轮不引入 |

推荐结构：`main` 维护源码，`codex/marketplace` 为正式市场，
`codex/marketplace-preview` 为试用市场，GitHub Releases 保存各端 ZIP。
发行分支只含市场、安装内容和公开发行记录，不含开发工具、测试及私有材料。
分支采用 `codex/` 前缀，与当前工作区默认分支命名约定一致。

2026-10-08 设计基线中 CodeVow 为 `1.0.1`；三个 acceptance 槽均为空。本设计不把它变成
正式版：先验证试用市场的安装和升级链路，真实行为验收完成后才开放正式
渠道。实际开始实施前重新读取版本、Git 状态和验收记录，不预定下一版本号。

## 2. 三宿主传输契约

按 2026-10-08 阅读的官方文档：

| 宿主 | 本设计的首选插件来源 | 宿主要求与验证边界 |
|---|---|---|
| Claude Code | `source.source=archive`，HTTPS ZIP，`sha256` | 官方要求 2.1.224+；在实际目标版本验证安装和更新 |
| ZCode | `source.source=url`、`type=zip`，HTTPS ZIP、`sha256`、`path` | 注册专用 JSON URL；2026-10-09 首次安装与字节已验证，升级和行为待验收 |
| Codex | `source.source=git-subdir`，发行仓库 URL、版本目录、固定 `sha` | 文档支持 Git 和 npm；本轮不假定市场能直接安装任意 Release ZIP |

官方文档是协议依据，不是当前机器或所有发行渠道的已验收声明。
ZCode 的 ZIP 字段属于其扩展；不能把同一 source 对象复制到另两端。
Codex 下载发行分支里的插件文件，客户端可能执行 Git 获取，但用户不需要
手动 clone 开发源码或运行构建。CodeVow 的 Markdown、Python 文件本身
就是安装内容，不要求编译为二进制才能称为制品。

如果某端的目标客户端未通过以上运输协议验收，不开放该端新市场；
保留旧发行方式，另行决定目标最低版本或降级来源，不能静默改为已支持。

## 3. 目录、渠道和版本

### 3.1 源码分支

`main` 保持现有 `catalog.json`、`plugins/`、`tooling/`、`tests/` 和 `docs/`。
新增根 `distribution.json`，只配置渠道分支、市场名称和运输类型，不维护
插件 ID、版本、publisher 或资源白名单的第二份来源。

| 配置项 | 正式渠道 | 试用渠道 |
|---|---|---|
| 渠道键 | `stable` | `preview` |
| 分支 | `codex/marketplace` | `codex/marketplace-preview` |
| 原生市场名 | `ai-code-stable` | `ai-code-preview` |
| 本地 release mode | `stable` | `draft` |
| GitHub prerelease | `false` | `true` |

repository 从插件 `product.json.repository` 的规范 GitHub 地址派生；
首版要求所有注册插件均指向当前仓库，拒绝隐含跨仓库上传。运输类型限定
为本稿三项，不加入任意 command/hook 扩展。

迁移完成后，`dist/` 改为本地/CI 临时输出并加入 `.gitignore`。
撤销 Git 跟踪不删除本地用户构建，不重写历史提交。迁移切换前保持现有
`dist/` 和旧市场可用，见第 10 节。

### 3.2 发行分支

正式与试用分支具有相同结构，但相互独立：

```text
README.md
.claude-plugin/marketplace.json
.agents/plugins/marketplace.json
marketplace.json
marketplaces.lock.json
plugins/codex/ID/VERSION/        # Codex 完整安装包目录
records/ID/VERSION.json         # 公开来源、制品和验收摘要
channel.json                   # 本渠道每个插件当前指向的版本
```

`ID`、`VERSION` 是布局参数，实际值从经过验证的发行记录派生。
当前目录只需 Codex 安装内容；Claude、ZCode 的清单指向 Release ZIP。
不复制开发源码树、源码测试、CI workflow、工具构建入口或原始验收会话。

版本目录一经写入，不得修改；相同版本相同字节的重检可通过，相同版本
不同字节拒绝。保留旧目录和普通提交历史，以维持已安装版本和固定提交的
可达性；不 force push、不删除发行分支。

`channel.json` 是已发布状态快照，按插件记录版本、Release ID、源码提交、
安装包哈希和 Codex 发行提交。它不是开发版本来源，不能被人工修改以
绕过 `product.json` 或发布检查。多插件独立更新，未发布插件不出现。
发布一个插件不得替换或移除其他插件的条目。

### 3.3 GitHub Releases

继续使用 `ID/vVERSION` 规范源码标签，一个插件版本一个 Release。
标签指向冻结的源码提交，不指向发行分支。将整个标签编码为 URL 的单个
路径段，不用不带版本的 `/latest/download/` 作为市场下载地址。

| 附件 | 用途 |
|---|---|
| `ID-VERSION-HOST-plugin.zip` | 只含一个插件根的宿主安装包，三端均留档 |
| `ID-VERSION-HOST.zip` | 现有带本地市场的手动试用下载包 |
| `ID-VERSION-release-bundle.zip` 及其 `.sha256` | 完整可复验发行套件，含现有投稿材料 |
| `release.json`、`release-notes.md`、`SHA256SUMS` | 版本、来源、模式、验收摘要与文件哈希 |

Release 自动生成的 Source code 下载不是市场安装来源。Actions artifact
仅用于 job 间传递和短期留档，也不是公开市场的长期下载来源。

试用版仍使用现有 `X.Y.Z` 版本语法，以 GitHub prerelease 和独立市场区分，
本轮不扩展 `-beta` 语法。已经公开的试用版不在原标签上换内容或改写
发行记录来冒充正式验收；首次正式版使用新的版本与标签，重新通过 stable
检查。各宿主缓存、市场名称和版本探测必须在实际客户端中验证。

### 3.4 多插件独立发版，市场统一汇总

每个插件的 `product.json` 独立推进版本，每个 `ID/vVERSION` 对应一个
GitHub Release。一个 Release 只保存这个插件的所有声明宿主制品和发行
记录，不把整个仓库的多个插件合并成一个共享版本。根 private
`package.json` 的版本不能作为所有插件的发版版本。

以下版本仅用于说明命名，插件 B 不是当前 catalog 中的正式插件：

| 插件 | 源码标签 | 独立 Release 附件 |
|---|---|---|
| CodeVow | `ai-code-workflow/v1.0.2` | CodeVow 的各端安装包、完整套件、说明、哈希 |
| 插件 B（示例） | `plugin-b/v0.1.0` | 插件 B 自己的各端制品、记录、说明、哈希 |

发布 CodeVow 只更新它的版本和频道指针；插件 B 保持原版本、下载地址和
绑定提交。每个插件只为自己声明的 `hosts` 构建和验收，stable 条件要求
该插件的全部声明宿主通过，不要求仓库中的所有其他插件同时升版或验收。

同一频道的三份原生市场清单分别汇总该频道中已部署且声明支持该宿主的
插件。`catalog.json` 登记一个新插件只表示源码进入构建和测试；插件只有
公开了符合频道资格的 Release 并完成市场部署后，才进入远端市场。
某插件只有 Codex 包时，不生成它的 Claude 或 ZCode 条目。

`build --all` 是统一构建检查，`npm test` 是仓库测试门禁，二者不代表
一次对外发布所有插件。首版 Release 准备和市场部署仍一次选择一个插件。

### 3.5 批量发布的后续边界

首版不增加 `release --all` 或 batch workflow。预留以单插件契约编排的
能力，实际加入批量入口时应补专门测试和界面设计，不提前引入插件依赖
管理、自动安装器或联动版本规则。

批量入口可以共享一次 CI 调度，但每个插件保留独立版本、标签、Release、
验收门禁和结果。一个插件失败时不会自动回退或删除其他已公开 Release，
批次必须报告逐插件状态及失败；不得把部分成功写成整批成功。

后续批量市场部署的契约是：维护者明确选择一组已经公开的插件版本，在
一个计划中检查所有候选和既有频道；任一候选不合格则不推进市场。全部
合格后，可以一次暂存所需 Codex 版本目录，再以一次最终目录提交汇总
这组版本。最终市场清单可一起推进，多个 GitHub Release 的公开仍不是
整体事务。若希望仅部署批次的成功部分，必须重新明确选择并生成新计划，
不能自动跳过失败插件后沿用原批次的“全部通过”结论。

## 4. 安装包与市场的绑定

### 4.1 独立的 hosted installer

现有 `downloads/` ZIP 包含插件目录和本地市场，不能直接复用为 hosted
installer。新增 `installers/ID-VERSION-HOST-plugin.zip`：

```text
ID/
  原生 plugin.json
  skills/、其他白名单内容
  artifact.json
```

唯一插件根下面逐字节对应经过 `package check` 的宿主包，包括其
`artifact.json`；不得出现兄弟市场、其他插件、原始会话或缓存。
ZCode 的 `path=ID`，Claude 使用 ZIP 内下一层的唯一插件根。
Codex 留档 ZIP 与发行分支的版本目录必须逐文件同字节。

保留 `downloads/` 的本地市场用途和 `submissions/` 的官方投稿用途；
投稿 ZIP 继续遵守现有规则，不把这三种 ZIP 混为一种。

### 4.2 原生入口

所有入口从已验证的发布记录生成，不从开发分支当前候选版本猜测“最新”。

| 宿主 | 入口路径 | source 生成规则 |
|---|---|---|
| Claude | `.claude-plugin/marketplace.json` | `archive`、固定版本 Release asset URL、ZIP SHA256 |
| Codex | `.agents/plugins/marketplace.json` | `git-subdir`、仓库 URL、`./plugins/codex/ID/VERSION`、发行提交 `sha` |
| ZCode | `marketplace.json` | `url`、`type=zip`、固定版本 Release asset URL、ZIP SHA256、`path=ID` |

Codex 保留现有 `policy`、`category` 等必要元数据，原生 author/displayName
继续由插件单源生成。若其他宿主要求附加目录字段，应由宿主适配器生成并
验收，不直接复制官方目录的内部元数据。

三个市场、channel 快照和公开记录在同一个 Git 提交中更新，最后通过一次
正常分支推进使用户发现新版。GitHub Release 公开与分支推进不是跨系统
原子操作；故障处理须按第 6 节报告实际阶段。

### 4.3 避免提交哈希自引用

用 `S` 表示源码提交，`D` 表示包含新 Codex 版本目录的发行提交，`C` 表示
最终包含新市场入口的发行提交。市场 pin `D`，不 pin 自己尚未产生的 `C`。

先把 Codex 版本目录写入发行分支得到 `D`，保持旧市场入口；再次读取远端
目录核对字节，然后才在 `C` 中更新三端目录。首次部署时 `D` 可以只有
说明和版本目录，正式入口到 `C` 才产生。这两次写入都在明确授权的远端
部署阶段内，不由本地 `prepare` 暗中执行。

目标插件未声明 Codex 时，跳过安装内容提交 `D`，直接生成目录提交 `C`；
记录的 Codex 发行提交为 `null`，不生成虚假的 Codex source。其他插件
已经存在的 Codex 条目保持原绑定。

## 5. 发布流程与授权

保留本地工具的职责：`check/prepare/verify` 不执行 Git 或网络写入。
发布和市场部署由单独的 GitHub 管理脚本执行，默认只做检查和计划。

| 阶段 | 输入和动作 | GitHub 写入 |
|---|---|---|
| A：本地预检 | 当前源码、可信旧包、测试、构建、包和发行复验 | 无 |
| B：冻结版本 | 用户审阅后提交并推送；用户明确创建和推送标签 | 有，需本次明确授权 |
| C：远端准备 | 从标签解析 `S`，重新测试与构建，准备完整套件 | 默认仅 Actions artifact |
| D：上传草稿 | 显式开启上传，复验 `S` 和完整套件，上传全部附件 | 创建 draft，需明确授权 |
| E：公开版本 | 人工确认 Release 内容及模式，Publish draft | 公开 Release，需明确授权 |
| F：市场部署 | 明确触发部署，校验公开 Release、下载内容和频道，然后推进 `D`、`C` | 写发行分支，需明确授权 |
| G：实际验收 | 从新市场实际安装和更新，核对版本与内容，再检查行为 | 安装操作另行授权 |

上传 draft、Publish、部署市场三个动作分别报告。源码 tag 和 Release 公开
不隐含市场已部署。Environment 审核是 GitHub 的控制机制，不替代当前
会话中的用户授权；任务记录或 accepted 字段也不构成发布授权。

首版只接收本仓库 `main` 历史可达的源码提交，远端规范标签、发行记录的
源码 SHA、冻结源码 blob 必须一致。写权限 workflow 从可信 `main` 运行，
不能因用户输入任意 ref 就执行该 ref 自带的发布脚本。发布维护分支需后续
另行扩展可信来源范围，不隐含允许任意 PR 分支发布。

`stable` 必须保留现有全部宿主的 accepted 字节绑定证据、干净源码、规范
标签和 HEAD blob 校验。`preview` 的远端公开虽然使用本地 draft mode，
仍要求干净源码、正确现有标签、完整制品及明确的 unverified 说明。
GitHub 的 draft 是可见性，工具的 draft 是验收模式，两者不能混淆。

### 5.1 稳定验收材料的 CI 可读性

当前 `capture_release` 读取插件内的原始证据路径；这些材料可能只在本地。
CI 不会因为存在 accepted JSON 就拥有原始材料。首版保留该完整验证，
不设计一个可绕过原文校验的布尔开关或 Agent 批准文件。

优先由维护者制作并审阅可公开的验收材料，在冻结源码之前提交；必须满足
包白名单隔离、证据绑定与隐私要求。不能为使 CI 通过提交含凭据或隐私的
会话原文。如果材料不能公开，stable 远端准备保持失败，另行设计受控私有
证据供给或采用现有本地受控验证流程；本轮不宣称该路径已解决。

工具只能校验哈希和声明，真实会话真实性和结果仍由维护者审阅。

### 5.2 “部署到市场”的含义与当前实现边界

本设计的市场部署是把已经公开并校验的某个插件版本，写入对应发行分支
的原生市场清单及频道记录，使注册了该市场的客户端能够发现并安装它。
此动作包含 Codex 发行内容的发布；Claude 和 ZCode 已公开的安装 ZIP
留在 GitHub Release，市场保存其固定下载地址和哈希。

它不申请官方收录，不创建网站或服务端，不把安装文件写入用户宿主缓存。
公开 GitHub Release 与部署市场分别记录状态，市场部署完成之后才告知
用户刷新市场安装。真实宿主安装和行为验收继续单独报告。

当前已经实现的是 `marketplace sync`：读取并校验本地 `dist/`，生成仓库
根入口；把匹配的 dist 和入口提交推送后实现旧方案的分发。
当前 `release.yml` 默认只准备 Actions artifact，可显式上传 GitHub draft，
没有本文拟新增的 marketplace workflow。本文的部署计划、远端分支推进
和操作者步骤是目标设计，不能当作现在已经可执行的功能。

### 5.3 操作者入口与一次单插件部署

初次配置时，先核对第 8 节的 GitHub 权限与保护条件，按第 10 节走 preview
迁移。发行分支只有在明确授权的 bootstrap 部署中创建，使用无源码父历史
的独立根提交，后续保持正常提交历史。操作前核对所选 ref 不存在；存在
但不是工具管理的有效频道时停止，不把用户已有分支 reset 成发行分支。

完成工具实现后，维护者在 GitHub 的目标操作顺序为：

1. 冻结并审核某个插件版本，明确授权提交、推送和创建规范 source tag。
2. Actions → **Prepare plugin release** → Run workflow，workflow ref 选
   `main`，`plugin` 选目标 ID，现有 `ref` 输入选规范版本 tag；试用选择
   `mode=draft`，正式选择 `mode=stable`。仅准备时保持
   `create_github_draft=false`；明确授权上传草稿时选 `true`。
3. 在 Release 页面核对该版本的全部附件、哈希、源提交和验收摘要。用户
   Publish 草稿；preview 必须标记 pre-release，stable 必须符合稳定资格。
4. Actions → **Deploy plugin marketplace** → Run workflow，workflow ref
   选 `main`，输入 `plugin`、`source_tag`、`channel`，先选择 `action=plan`。
5. 审阅该 run 的 job summary 和计划附件：版本、实际 Release、目录变更、
   保留插件、将部署的分支和全部绑定都应清楚。取得 `plan_hash` 和当时
   的市场分支 `base_commit`。
6. 再运行该 workflow，填写同一插件、tag、channel，选择 `action=deploy`，
   填入审核的 `expected_plan_hash` 与 `expected_market_commit`；完成
   `plugin-marketplace` environment 的批准。若期间市场变化使计划过期，
   流程返回冲突，重新 plan 和 Review，不直接部署新的未审阅计划。
7. workflow 完成远端读回，输出 `marketplace_deployed`、实际市场分支、
   源提交 `S`、安装内容提交 `D`、市场提交 `C`、Release 链接和逐宿主
   的安装来源。维护者再执行已授权的真实客户端安装或升级验收。

source tag 示例形如 `ai-code-workflow/v1.0.2`，但实际版本从已经冻结
并公开的版本中选择；不为执行示例创建新 tag。当前 GitHub 上没有本文
新增 workflow，本节不是用户现在应直接运行的安装命令。

拟新增 marketplace workflow 的固定输入：

| 输入 | 契约 |
|---|---|
| `plugin` | 单个已注册插件 ID，不接受 `all` |
| `source_tag` | 恰好为目标 `ID/vVERSION`；远端解析并与发行记录、源码校验 |
| `channel` | `preview` 或 `stable`；不由 Release 页面标题推断 |
| `action` | `plan` 或 `deploy`，默认 `plan` |
| `expected_plan_hash` | deploy 必填，绑定经审核计划；plan 时不需要 |
| `expected_market_commit` | deploy 必填，绑定已审核频道基础；首次创建使用明确的 `absent` 值 |

`absent` 只表示审核时目标分支不存在，不表示可覆盖任意现有分支。
真正部署时再次验证不存在，远端 ref 创建发生冲突即停止。所有输入按固定
格式校验，采用结构化参数或正确的 shell 引用，不能把 tag 当作 shell 代码。
`plan` 不创建 tag、Release 或远端 ref；只读取远端并生成计划和 Actions
审阅附件。它的 GitHub 权限为只读，不经过 write job。

### 5.4 部署计划与远端执行步骤

计划包含以下确定输入，生成与版本相关的内容均来自可信记录：

- schema、plugin、version、channel、目标分支和市场名称。
- source tag、源码提交 `S`、source tree hash、发行套件 content hash。
- GitHub Release ID、可见性、pre-release 状态，各附件 ID、URL、大小和实际 SHA256。
- 既有市场 `base_commit`、原 channel/记录哈希、原三端清单哈希。
- 新 Codex 版本目录的路径及文件哈希，目标宿主清单和预期来源绑定。
- 保留的其他插件与旧版本目录，预期增加或替换的受管文件。

计划哈希使用排序的规范 JSON，排除自身 `plan_hash`；不使用当前时刻、
下载临时目录或运行次数决定目标版本。最终 `D`/`C` 尚未生成时，计划用
明确的内容绑定与生成规则描述这两次提交，不能预填未知提交 SHA。
`expected_market_commit` 也必须与计划内基础一致，不是单独可放宽的参数。

deploy 从可信 `main` 上的管理代码执行以下步骤：

1. 重新查询规范 tag、Release 和既有频道；重新下载附件并计算 SHA256。
   Release 必须已公开且匿名读取可达，频道/模式/版本/全部宿主资格一致。
2. 从源码提交 `S` 校验输入，根据可信工具重建完整发行闭包，复验收到的
   bundle、installer 和原生清单。不能只信 GitHub 附件文件名或包自报哈希，
   不能运行包内脚本来获取初始信任。
3. 重算计划，与 `expected_plan_hash`、`expected_market_commit` 比对。
   所有旧受管记录、旧版本目录和无关插件条目必须仍然有效。未知文件或
   人工改动不被部署脚本覆盖；需要先 Review 并明确修复。
4. 目标插件声明 Codex 时，在本地 staging 构造仅增加新 Codex 安装目录
   的 `D`；推送前后校验 source tag 未移动，正常推进目标 ref，再从
   远端读取 `D` 的文件核对。未声明 Codex 时跳过该阶段。
5. 从实际安装内容绑定生成各原生市场、channel 及公开记录，组成 `C`。
   保留其他插件原有来源和旧版本目录；再次检查当前 ref 为预期 `D`，
   或未执行 `D` 阶段时的审核基础，然后正常推进分支，不 force push。
6. 按远端 `C` 读回三个市场和公开记录，逐条解析目标 URL、哈希、path、
   Codex `sha`；核对最终分支指向 `C`。成功后记录部署结果。

一次部署所选插件如果没有某宿主，该宿主清单中的其他插件仍原样保留；
没有任何已发布插件的宿主不生成入口。生成时使用完整已部署频道清单，
不得用 `build --plugin` 的单插件本地市场覆盖聚合市场。

`records/ID/VERSION.json` 记录源码和发行绑定、验收摘要、Release ID、
资产及 Codex `D`，不包含尚未生成的自身市场提交 `C`。`C` 在部署运行
结果中报告，避免公开记录再次产生提交哈希自引用。原始验收材料不入分支。

受管分支写入前后均检查 ref；正常 push 拒绝时停止，成功响应不确定时
先读回确认实际状态。保持旧市场有效直到最终 `C` 推进；Release 公开
和 `D` 暂存不能单独报告为已完成市场部署。

若上次运行已写入 `D` 后失败，重试前以当前分支生成新计划并审阅；
暂存目录只有在与这次可信 bundle 逐字节一致时才能认定为本版本待完成
内容。此时复用已经核对的 `D`，不用同版本重新写另一份目录；其他未知
未引用目录不能被顺带认领或覆盖。若最终目录已经完全部署，先完整重检
实际市场和全部绑定，按第 5.5 节返回只读 `already_deployed`，不以过期
计划再次写分支。

### 5.5 部署结果与后续批量编排

运行结果至少报告如下状态，失败以非零退出并保留实际已完成阶段：

| 状态 | 含义 |
|---|---|
| `plan_ready` | 可审阅的部署计划已生成，市场未写入 |
| `blocked` | 缺少公开制品、频道资格、正确标签或稳定验收，未部署 |
| `conflict` | 审核计划或预期 ref 失效，未覆盖现有内容 |
| `published_pending_marketplace` | Release 已公开，最终市场尚未完成 |
| `marketplace_deployed` | 最终目录提交已推进且远端读回通过 |
| `already_deployed` | 远端已有完全相同的版本和来源绑定，重检通过 |

状态描述是部署操作的结果，不是用户授权标记；不得转换为当前会话的
自动 Git/发布许可。`marketplace_deployed` 也不表示客户端已安装，
不表示技能行为 accepted 或官方市场已收录。

后续批量编排在逐插件结果之外输出批次汇总，保持明确的成功、失败与尚未
部署集合；不只返回一个掩盖部分失败的布尔值。首版只有单插件输入，
不把 `build --all` 或多个 Release 已公开解释为批准部署全部插件。

## 6. 历史、并发、失败与恢复

发布检查从频道公开记录取得上一版本，再下载并独立复验其完整发行套件。
源码 tag 上的可信工具核对当前输入；上一包按明确版本的 schema 校验，
不能执行历史包自己的工具作为初始验证器。

同时查询本插件已有 Release 和已有版本目录，拒绝版本降低或在任一渠道
重用已公开版本的不同内容。首版没有历史记录时执行显式 bootstrap 检查，
记录没有可信历史；不能用空目录伪造“已检查历史”。不使用整个仓库的 latest
Release 作为某个插件的上一版本，因为本仓库包含独立版本的多个插件。

同仓库所有发行分支写入共用一个 Actions concurrency group，
`cancel-in-progress=false`；读出的分支 base SHA 也必须参与远端更新条件。
正常 fast-forward push 被拒绝或 API 的预期旧 ref 不一致时，停止并报告，
不能自动 force push。并发锁不能约束仓库外写入者，最终 ref 和旧版本
目录仍须重检。

| 失败位置 | 用户仍能安装的内容 | 后续处理 |
|---|---|---|
| 构建或本地复验失败 | 旧市场版本 | 修复源码，未执行远端写入 |
| 草稿上传中途失败 | 旧市场版本 | 报告草稿 URL 和已上传附件；人工核查后授权恢复，不覆盖未知 draft |
| 已公开 Release，市场部署失败 | 旧市场版本；新 Release 可单独下载 | 标记 published_pending_marketplace，修复后用同一已验证制品重试部署 |
| 已写 `D`，未写 `C` | 市场仍指向旧版本 | 保留未引用的版本目录；核对 `D` 字节后重试最终目录推进 |
| 多插件其他条目发生变化 | 当前市场版本 | 重新审阅最新分支基础，禁止用旧快照覆盖其他插件 |
| `C` 推进完成后验收失败 | 新市场已可见 | 报告实际发布状态；由用户授权停止推荐或恢复旧目录指针，保留原制品 |

同一已完成部署的重试先校验远端目录、文件哈希和记录；完全一致则只读
返回 already_deployed。不删除、不覆盖已公开附件，不自动删除 Release。

市场回退是生成新的目录提交，指向旧的固定 URL、哈希和 `D`；这不保证
客户端自动降级。实际降级需按宿主原生能力验证并操作。Release 撤回或
资产删除与市场回退是不同操作，不由失败处理自动执行。

## 7. 项目改动清单

以下路径是设计时确定的改动范围；实际实现和验证状态以实施记录为准。

| 路径 | 拟调整 |
|---|---|
| `distribution.json`（新增） | 渠道、分支、市场名、限定运输适配，不存第二份产品版本 |
| `tooling/plugin_tools/release/layout.py` | 生成 plugin-only installers，保留下载和投稿包 |
| `tooling/plugin_tools/release/integrity.py` | 安装 ZIP 闭包、SHA256、单插件根和三端来源验证；显式版本化解析 |
| `tooling/plugin_tools/release/core.py`、`metadata.py` | 保持可信源码重建、Git blob 和全部宿主稳定门禁 |
| `tooling/plugin_tools/distribution.py`（新增） | 从经过验证的历史记录生成渠道树、原生来源和部署计划；不执行网络写入 |
| `tooling/plugin_tools/cli.py` | 提供受控的 distribution plan/check 本地入口；旧命令兼容期给出清楚用途 |
| `tooling/plugin_tools/markets.py` | 保留本地 dist 市场能力；迁移后远端入口改用发布记录，不拿当前源码冒充已上线版本 |
| `.github/scripts/create_release_draft.py` | 追加 installers 和独立 SHA256SUMS 附件，保留现有 tag/完整包复验和拒绝覆盖 |
| `.github/scripts/deploy_marketplace.py`（新增） | 公开 Release 查询、下载复验、版本目录和最终目录两个阶段、远端读回 |
| `.github/workflows/ci.yml` | 测试生成产物及可复现性；切换后移除“main 提交的 dist 必须匹配”门禁 |
| `.github/workflows/release.yml` | 手动准备、可选草稿上传；不默默加入 Publish |
| `.github/workflows/marketplace.yml`（新增） | Deploy plugin marketplace：plan 默认只读，deploy 绑定审核计划和基础提交，environment gate、串行写入 |
| `.gitignore`、`dist/`、三个根市场入口 | 完成迁移验收后处理跟踪和旧市场切换；不提前破坏现有安装来源 |
| `AGENTS.md`、插件局部规则、安装说明、发布指南、证据契约 | 更新现行路径、发布阶段和支持边界；保留历史日期与证据 |
| `tests/tooling/`、Release/CLI/GitHub 脚本相关测试 | 为新行为先写有效失败测试，再实现与集成 |

发行套件新增布局使用 release manifest schema 2；已有 artifact schema 1
和 dist index schema 2 保持原义。保留显式 schema 1 历史解析和旧包验证，
不把新路径硬套进历史闭包，不修改旧报告。为新增 channel/record 数据定义
固定字段、路径和 schema；拒绝未知字段与重复 JSON 键，按现有 IO 契约处理。

当前 `marketplaces.lock.json` 的旧归属不能被新逻辑直接覆盖；在迁移步骤中
确认旧字节后显式转换。发行分支上的新 lock 只记录工具所有的三个市场
入口哈希，不代表版本来源、发布批准或整个分支的授权。

源码 CI 仍跑 `validate --all`、`npm test`、lint、全宿主包检查；另生成两次
同来源构建比对内容哈希与 ZIP。发布 CI 从规范现有 tag 读取源码并复验。
写权限 job 使用可信 `main` 上的发布逻辑；候选包的脚本不在持有写凭据
的步骤中执行，`main` 当前版本必须能识别目标发行 schema。

## 8. GitHub 设置与工作流约束

下表是需要配置的目标状态，不是已读取或已应用的远端设置。

| GitHub 设置位置 | 目标状态 | 注意事项 |
|---|---|---|
| Repository → Settings → General | 默认分支保持 `main`；面向匿名用户的市场和制品使用 public 可访问仓库 | 若仓库为 private，先设计客户端认证，不直接改变可见性 |
| Settings → General → Releases | 开启 Enable release immutability | 只保护启用后发布的版本；必须先 draft、上传全部资产，再 Publish |
| Settings → Rules → Rulesets，`main` | 禁止 force push 和删除；要求实际 CI 成功 | 有第二维护者时增加 PR 审阅；单人需明确可执行的维护例外 |
| Tag ruleset，`*/v*` | 限制规范 tag 的创建者，禁止更新和删除 | 标签由明确授权的维护者创建；发布脚本不偷偷创建 tag |
| 发行分支 rulesets | 对两个精确分支禁止删除和 force push | 首版允许经过 environment gate 的普通写入；不要配置使 GITHUB_TOKEN 无法写入的 PR-only 门禁 |
| Settings → Actions → General | 默认 GITHUB_TOKEN 保持只读；允许审核后的 Actions；外部 PR 按 GitHub 要求批准运行 | 各写 job 单独声明 `contents: write`；不把所有 CI 都设为写权限 |
| Settings → Environments | 创建 `plugin-release` 与 `plugin-marketplace` | 分别控制草稿上传与市场部署；不能只在 YAML 写名称却未配置保护规则 |
| 两个 environment 的 deployment refs | 只允许 `main` 执行可信管理 workflow | 输入 source tag 是数据，另校验其属于本仓库且解析到审核的源码提交 |
| 两个 environment 的 reviewers | 若计划和仓库可见性支持，设置维护者审批 | 单人可由自己审阅并触发；不要勾选 Prevent self-review；两人团队再开启此项 |
| Actions/credentials | 同仓库首版使用 GITHUB_TOKEN，不新增长期 PAT | 若后续 restrict updates 策略阻止它，停止配置验收；另设计指定 App 写入者，不声称 token 可绕过规则 |

Actions workflow 的 job permissions 采用最小权限：源校验和打包只读，
上传 draft 与写市场的独立 job 为 `contents: write`。本轮不创建 PR，
所以不需要 `pull-requests: write`；不使用 Packages，所以不需要
`packages: write`。第三方 action 在落地时固定审核过的完整提交 SHA，
更新需重新 Review；只在可信 workflow 中获取写 token，不使用
`pull_request_target` 执行外部 PR 代码。

Environment required reviewers 的可用性取决于 GitHub 计划和 public/private
属性；本轮没有读取账号设置，不能声称这些保护已开启。发行分支正常写入
权限必须用一次实际部署验证，不靠 workflow 的声明推导。

Publish 保持用户在 GitHub 界面执行；首版不增加自动公开开关。公开完成
后显式运行 marketplace workflow 的 plan，再执行经审核的 deploy，输入
契约见第 5.3 节。它自行查找对应 Release，不接受未经校验的下载 URL
或“最新 tag”。GitHub Publish 不自动触发市场写入，main 的 push 也只
触发只读 CI，不能让普通源码变更直接上线所有插件。

## 9. 用户安装和更新入口

正式渠道的目标发行分支为 `Zack-Zz/ai-code` 的 `codex/marketplace`。
已部署的试用渠道为同仓库的 `codex/marketplace-preview` 分支。
Codex 登记带 ref 的 Git 市场；Claude/ZCode 登记该分支各自 JSON 的 HTTPS URL。
Claude 的带 ref Git 入口仍是官方支持的备选方式。
具体客户端是否提供分支选择、是否接受 ref、如何刷新，应逐端实际验收。
界面不能指定分支时，验证其原生 Git source 表达；若仍不支持，采用第 1 节
的独立市场仓库方案，不要求用户手动下载开发仓库作为补救。

Claude Code 验收目标：用该分支的专用 JSON URL 登记，也可用带 ref 的
原生 Git 市场，再以 `ai-code-workflow@ai-code-stable` 或 preview 市场安装；验证首次安装、
市场刷新、升级和新会话加载。运行客户端必须支持 archive source。
2026-10-09 已用官方 `2.1.295` CLI 的 `--marketplace <JSON URL>` 一步完成
注册和安装，35 个缓存文件与 installer ZIP 一致；同版本市场刷新成功。
当前可复制命令见根 README，两版升级与完整行为仍待验收。

Codex 文档中的登记入口可作为待验收操作：

```sh
codex plugin marketplace add Zack-Zz/ai-code --ref codex/marketplace
```

CLI 登记与桌面端安装分别验证；桌面插件目录中选择对应市场后安装，
验证 git-subdir 的固定 SHA、版本目录、cache 内容和更新探测。
文档里的 `url` 在这里是 Git URL，不是任意 Release ZIP URL。

ZCode 的注册输入须使用该端专用清单。2026-10-09 在应用 `3.14.5` 的
内置 CLI `0.16.9` 发现：Git 导入依次查找显式路径、
`.claude-plugin/marketplace.json`、根 `marketplace.json`。同仓库三端布局
因此会先选中 Claude archive，而 ZCode 安装器不支持该来源。直接添加
以下 URL 绕过 Git 清单选择，保留单仓库、单发行分支和原生更新方式：

```text
https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/codex/marketplace-preview/marketplace.json
```

已通过内置原生 CLI 完成注册、安装、启用与同版本市场刷新；35 个缓存文件
与 ZCode installer ZIP 相同，发现 6 个技能。可复制的 macOS 命令见根 README。
两版升级、完整加载和行为另行验收；不增加自行写宿主缓存的安装脚本。

试用和正式市场名不同，同一插件 ID 不表示跨市场自动迁移。切换渠道前
记录现有版本与来源，避免两个市场同时启用重复技能；按宿主原生操作迁移。

## 10. 迁移顺序与验收

1. 先实现 installers 和可信复验、schema 兼容及纯本地 distribution plan/check；
   保留目前 main 上的 dist、市场和 CI 门禁。新行为走 TDD。
2. 配置经过批准的 GitHub 规则、environment、immutability；用户授权建立
   试用发行分支并创建新的候选标签，准备草稿并审阅全部附件。
3. 用户明确公开 prerelease、部署 preview 市场。实际验证三端市场分支登记、
   首次安装、完整加载、升级发现、缓存字节与故障处理。
4. 收集真实工作流行为验收，保持 installation 与 behavior 两类证据分开。
   只有全部声明宿主通过 stable 条件后，准备新的正式版本与正式市场。
5. 切换文档安装入口，并在 README 明确旧 `ai-code-local` 市场迁移方式；
   老用户仍需主动登记新市场，不承诺自动切换来源。
6. 旧入口停用与去跟踪 dist 是一次明确的迁移变更：在三端新入口完成验收
   且迁移说明已经公开后，删除 main 上旧的三个原生市场入口和归属文件、
   撤销 dist 跟踪，更新 CI 与规则。旧 Git refs 仍保留历史发行内容；
   老市场不会继续获得新版本，说明必须清楚告知。

不在用户仅要求设计时执行上述远端或安装操作。

| 验证层 | 必须检查的内容 | 不能据此宣称 |
|---|---|---|
| 单元与集成 | 安装 ZIP 闭包、额外文件/篡改拒绝、同版本换内容拒绝、schema 1/2、URL 编码与固定 SHA | 宿主可安装 |
| 模拟 GitHub API | plan 不写远端；draft 不部署、private 资产拒绝、prerelease/channel 错配、标签移动、附件缺失、哈希不符、审核计划过期、absent 创建冲突、并发 ref 冲突、未知 draft 保留 | 实际 GitHub 权限可用 |
| 多插件部署 | 未发布插件不入市场；只生成声明宿主条目；保留未改插件和旧目录；逐插件历史；D/C 无自引用；同部署幂等重检 | 跨平台整体事务 |
| 真实 GitHub | 一次授权的草稿、公开、ZIP 下载、D/C 推进与远端读回；规则、环境和写权限 | Agent 已遵循技能 |
| 真实宿主安装 | 两个连续版本、native source、发现/安装/刷新/升级、cache 字节、错误哈希拒绝、渠道迁移 | 全部工作流行为已 accepted |
| 真实宿主行为 | 各插件自己的声明能力和验收场景，绑定当前源码及包 | 平台认证或官方目录收录 |

目前缺少真实宿主验收和远端设置证据；本轮设计稿不改变这些状态。

## 11. 官方依据与设计自审

- [GitHub Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)：发行附件与自动源码快照。
- [GitHub Packages](https://docs.github.com/en/packages/learn-github-packages/introduction-to-github-packages)：语言包仓库及认证，本轮不采用。
- [不可变 Release](https://docs.github.com/en/code-security/concepts/supply-chain-security/immutable-releases)、[开启设置](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/establish-provenance-and-integrity/prevent-release-changes)：发布后保护 tag 和附件，先准备完整草稿。
- [GitHub environments](https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/manage-environments)：审批、单人自审、ref 与计划可用性。
- [GitHub token](https://docs.github.com/en/actions/security-for-github-actions/security-guides/automatic-token-authentication)、[rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)：最小权限与 ref 保护；实际账号设置仍需验证。
- [Claude 来源参考](https://code.claude.com/docs/en/plugins/marketplace-reference#archive-plugin-source)：HTTPS archive 与最低客户端版本。
- [OpenAI Docs](https://developers.openai.com/plugins/build/plugins)：市场登记、git-subdir/sha 和 npm 来源；未据此声称支持任意 Release ZIP。
- [ZCode 插件管理](https://zcode.z.ai/cn/docs/plugin)、[ZIP 分发协议](https://github.com/zai-org/zcode-plugins/blob/main/docs/distribution_CN.md)：市场、版本探测与 ZIP 字段。

本稿自审范围：区分源码与发行提交、下载/安装/投稿 ZIP、draft mode 与
GitHub draft、正式和试用市场；检查 D/C 哈希无自引用、单人审批可执行、
多插件历史不会使用全仓 latest、私有证据不会为 CI 入公开源码、旧入口不会
提前失效；补充核对独立 Release 与批量边界、plan/deploy 的审核绑定、
首次分支创建、聚合市场保留、部署与客户端安装的状态区分。上述协议与
设置只给出目标设计，实际落地仍须按验收表验证。
