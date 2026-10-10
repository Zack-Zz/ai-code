# main 统一源码与插件分发改造

日期：2026-10-09（Asia/Shanghai）。状态：已按本稿实施本地代码与空正式市场，
最终验证见[实施记录](../reviews/2026-10-09-main-marketplace-implementation.md)；
尚未提交、推送或验证远端 Actions 与新 main 宿主链路。
本稿替代旧设计中的双市场分支目标；旧设计与验收报告保留各自日期的事实。

Review 后补齐的执行契约：本地严格验收通过后，由 `release acceptance-export`
生成仅含哈希的 `release/acceptance-proof.json`，维护者审核后随公开源码标签
冻结；GitHub 使用显式 committed 验收模式，重验摘要的 HEAD 字节、公开输入
和全部宿主包哈希，私有正文不上传。摘要是维护者事实声明，不是平台认证。
根市场初始化以已验证快照为写入基准，持久化临时恢复记录，中断可重试，
未知回执与人工修改拒绝覆盖，完成前全量复验。具体格式与命令见
[证据契约](../release-evidence.md)和[发布流程](../publishing.md)。

## 1. 已确认的发布规则

1. `Zack-Zz/ai-code` 是统一的 GitHub 市场来源；源码和公开市场都使用 `main`。
2. 一个市场对一个插件 ID 只提供一个当前安装入口，不增加预览插件别名。
3. 新预览版本使用 `X.Y.Z-preview.N`，例如 `1.0.4-preview.1`；正式版本使用
   `X.Y.Z`，例如 `1.0.4`。每个插件独立维护版本、标签和 Release。
4. 预览版仅发布 GitHub Prerelease，不改变市场。市场当前为 `1.0.3` 时，
   发布 `1.0.4-preview.1` 后仍安装 `1.0.3`；`1.0.4` 正式发布并成功同步后才更新。
5. 默认入口始终指向该插件最新已成功同步的正式版本。没有正式版本的插件
   暂不出现在新的公开市场中，不回退到预览版。
6. 本轮不执行市场名称统一为 `ai-code` 的调整。新的统一入口先沿用已上线的
   `ai-code-preview` 内部标识，不创建尚未上线的 `ai-code-stable`。
   内部市场名称不再决定版本状态；将来的重命名需要单独设计原生迁移。
7. 先保留旧 `codex/marketplace-preview` 及其固定提交，停止向它发布新版本。
   切换来源与删除旧分支是不同操作，迁移不默认删除任何历史引用。
8. `dist/` 及其内容不得进入新的 Git 提交或远端分支。插件包由 GitHub Actions
   从冻结源码构建，公开 ZIP 保存为 Release 附件，不把 dist 回写到仓库。

“一个当前入口”不删除历史 Release。不同历史版本可以留档，但不能在根
市场中通过重复的插件 ID 冒充版本选择器。当前 Codex CLI `0.154.0` 的
`plugin add` 没有 `--version` 或 channel 参数；本方案不依赖这种能力。

## 2. 当前代码与目标的差距

本轮读取的本地基线为 `main` 的 `b09371f`，工作区干净。catalog 已包含
CodeVow 与 Agent Delegation；源码注册不等于插件已经公开或正式发布。

| 现状 | 改造 |
| --- | --- |
| `distribution.json` 将 stable/preview 绑定到两个市场分支和名称 | 改为 main、一个市场身份、latest-stable 规则和三端传输配置 |
| 根三份市场清单是 `ai-code-local`，引用已跟踪的 `dist/` | 根清单成为公开市场，只从已验证的正式发行记录生成 |
| `markets.py` 从当前开发源码和 `dist/` 同步根清单 | 开发市场生成到临时输出；公开市场由发行状态生成 |
| 版本只接受三个数字，历史比较直接拆成整数元组 | 使用统一的版本解析与比较，支持 preview 序号 |
| `distribution.py` 验证发行分支的完整树 | 验证 main 的明确受管路径，保持源码与其他内容不变 |
| `GitWriter` 只允许两条旧分支，按完整文件树写入 | 仅发布 main 的已审阅路径差异，验证基准提交和回读 |
| CI/release 要求提交的 dist 与最新源码构建一致 | 临时构建验证源码；另行验证公开市场与冻结发行版本一致 |

补充核对：用户新增 dist 排除约束时，工作区已推进至 `fbb3614`；
`.gitignore` 已包含 `dist/`，`git ls-files dist` 为空。原先“dist 不应忽略”的
注释已过时，本次修正。CI/release 的 committed-dist 校验仍需在实施时移除。

## 3. 项目目录与数据责任

```text
catalog.json                             开发插件路径注册
plugins/<id>/product.json                开发身份、版本、宿主与资源权威
plugins/<id>/                            插件源码
distribution.json                       main、市场身份与传输规则
tooling/、tests/、docs/                   公共工具、门禁与文档

.agents/plugins/marketplace.json         Codex 公开市场
.claude-plugin/marketplace.json          Claude Code 公开市场
marketplace.json                         ZCode 公开市场
published/index.json                     每个插件当前正式版本及发行记录引用
published/marketplaces.lock.json         公开清单的所有权与哈希回执
published/releases/<id>/<version>.json    不可变的正式发行来源与制品记录
published/codex/<id>/<version>/           Codex 原生安装内容

dist/                                   本地/CI 临时构建，不再跟踪
```

配置新 schema 为 2；配置不复制插件 ID、版本或资源清单：

```json
{
  "schema_version": 2,
  "source_branch": "main",
  "marketplace": {
    "branch": "main",
    "name": "ai-code-preview",
    "version_policy": "latest-stable"
  },
  "transports": {
    "claude": "archive",
    "codex": "git-subdir",
    "zcode": "url-zip"
  }
}
```

`product.json` 描述正在开发的版本；`published/index.json` 描述已经上线的
版本。两者允许不同，后者不是另一份开发版本来源。正式版本记录至少绑定
插件 ID、版本、源标签、冻结源码提交 S、Release ID、源码闭包哈希、每端
安装包哈希和 Codex 分发提交 D。根清单只能从这些记录和当前指针生成。

开发市场保留在构建输出中，供作者显式加载。`marketplace sync` 不再用最新
开发源码覆盖根公开市场；命令及 `--check` 分别明确开发生成与公开快照检查。
根市场的哈希回执迁入 `published/`，不同时保留两个所有权权威。

### 3.1 dist 排除与 GitHub 构建

源码提交无需附带本地生成包。GitHub Actions 的职责为：

```text
冻结源码标签 S
  → GitHub runner 检出源码、安装锁定依赖
  → 测试、构建三端包、独立检查、计算哈希
  → Actions artifact 传递已验证的完整发行套件
  → 审核后上传并公开 GitHub Release 附件
  → 仅正式版本同步 main 的市场入口
```

runner 上可以生成 `dist/`，也可以构建到 `RUNNER_TEMP` 下的空目录；两者都
只是任务的工作文件，不执行 dist 的 git add、commit 或 push。Actions
artifact 具有保留期限，用于 job 间传递与验证留档，不作为公开市场的长期
下载链接；Release 附件保存固定版本的安装 ZIP、校验和及公开发行材料。

忽略规则不自动撤销既有 Git 跟踪；本次工作区已完成该目录的排除，实施时
仍要核对最终索引与提交树。CI 增加独立检查，拒绝任何已跟踪的 `dist/`
文件，包括经 `git add -f` 加入的文件；市场写入器也不得允许该路径。
现有版本标签与历史提交不因排除目录而改写。

本约束针对临时输出 `dist/`。Claude/ZCode 安装内容直接取自 Release ZIP；
当前已验证的 Codex 传输仍需要固定 Git 子目录，因此 `published/codex/`
只保存那个正式版本必需的原生安装文件，不复制整个 dist 或 ZIP。它是
宿主协议要求的分发内容，不能将任意构建输出换个目录名后绕过排除规则。
如果后续要求所有生成内容均不得进入 Git，Codex 传输需另外选型并实际
验证，不能假定它已支持任意 Release ZIP。

## 4. 版本与发行状态

新增公共版本模块，替换 registry、包检查、release 历史检查、distribution
及部署脚本中分散的正则和整数拆分。比较遵循 SemVer，本轮公开版本语法
限定为 `X.Y.Z` 与 `X.Y.Z-preview.N`；数字禁止前导零，不引入 build metadata。

关键顺序为 `preview.2 < preview.10 < 同核心版本的正式版`。预览版本号必须
对应 `prerelease=true`；新的正式发行必须无预览后缀、`prerelease=false`，
并通过现有 stable 验收门禁。历史版本继续按其原始记录验证。

GitHub Draft 只表示未公开。内部 release `mode=draft/stable` 描述验收门禁，
不能与 GitHub Draft/Prerelease 混为同一个状态。对外发布种类从新版本语法
派生，不让操作员自由组合互相矛盾的版本、渠道和 prerelease 标志。

CodeVow `1.0.2` 是已发布的历史 Prerelease，虽然没有 preview 后缀，仍保留
其标签、附件和状态。不得改名、覆盖附件或直接改标志来成为新正式版。
预览转正式需要新的规范版本与标签；最终正式包要重新完成字节绑定验收。
具体下一版本号在发版时依据插件改动与当前历史确定，示例不是发版指令。

## 5. 三宿主分发

| 宿主 | 市场来源 | 插件内容来源 |
| --- | --- | --- |
| Codex | `Zack-Zz/ai-code` 的 main 根清单 | `published/codex/<id>/<version>/`，固定实际提交 D |
| Claude Code | main 的专用市场 JSON | 该插件正式 Release 的 archive ZIP 和 sha256 |
| ZCode | main 的专用市场 JSON | 该插件正式 Release 的 URL ZIP、路径与 sha256 |

三个清单表达同一组已正式发布的插件，分别使用已验证的宿主格式。每个
插件只出现在自己声明支持的宿主中。Release URL 固定具体插件标签和附件，
不用仓库 `/latest/download/`，也不把 Source code ZIP 或 Actions artifact
作为长期安装来源。

Codex 继续采用已验证的 Git 子目录传输；用户无需手动 clone 和构建。
Git 获取可能包含仓库其他内容，不能宣称客户端完全不传输开发源码。
`--sparse` 的优化和刷新能力要实际验证，不把它作为协议成立的前提。

预览版页面明确标注“预览，未加入默认市场”。Release 提供各端包、哈希和
预览验证说明，本轮不承诺三端均有同 ID 的任意版本一键安装命令，也不
增加自动安装器、第二市场、插件别名或发行快照标签。

## 6. main 市场更新算法

正式发行从冻结源码标签 S 读取；发布控制工具和路径策略从可信 main 读取。
不能因为旧标签带有旧 `distribution.json` 就再次写入旧分支。

1. 读取公开 Release，核实标签、正式状态、完整附件、字节哈希及所有声明
   宿主的 stable 验收。用可信工具与 S 的源码核对，不执行附件自带验证器。
2. 读取 main 基准 B 与受管状态。生成完整可审阅计划：选定插件、新旧版本、
   文件增删、来源 S、附件哈希、基准 B 和计划哈希。只更新选定插件。
3. 在 `plugin-marketplace` 审核后复算计划。B 或字节改变即拒绝，重新生成
   计划，不自动覆盖并发开发提交，不 force push。
4. 先向 main 写入该版本 Codex 安装目录，形成实际提交 D。此时根市场仍
   保持旧正式版本。检查 D 的目录和包闭包与 Release 一致。
5. 再写入正式发行记录、当前指针、根市场和回执，形成提交 C；Codex 清单
   固定 D，不使用移动 main，也不尝试让清单引用包含自身的 C。
6. 回读 C 和公开清单，确认三端版本、附件与 D 的引用一致，输出回执。

D、C 都是 main 上的普通提交，不再建立发行分支。两个阶段之间发生并发
提交时停止发布，保留旧市场及已写入的 D，记录“制品已准备，市场待更新”；
重新计划后可识别相同字节的已暂存版本。失败不移除源码或其他插件记录。

受管范围严格限定为上述公开清单和 `published/`。受管目录中的未知内容、
人工编辑、链接或特殊文件拒绝覆盖；范围外的文件、模式和 Git 对象必须
保持不变。不要把旧全树发布器简单改成允许 main 后就运行。

同版本同字节为幂等成功；同版本不同字节拒绝。旧版本或延迟事件不得倒退
当前指针。最高版本按插件独立比较，不按整个仓库最新 Release 的时间判断。
已经发布的正式 Release 尚未同步时，状态明确显示“已发布，市场待更新”。

## 7. GitHub 工作流

2026-10-09 通过 GitHub API 确认四项 active workflow：三个仓库 YAML 和
GitHub 管理的 `dynamic/dependabot/update-graph`。Actions 页面右侧的多条
历史 run 不是多份工作流定义。

| 工作流 | 是否保留 | 改造后的职责 |
| --- | --- | --- |
| CI，`ci.yml` | 保留并调整 | 源校验、统一测试、临时构建、独立包检查、lint、公开发行快照检查 |
| Prepare plugin release，`release.yml` | 保留并改为 Release plugin | 从 main 历史冻结标签构建单插件三端包，校验后创建及公开 Release |
| Deploy plugin marketplace，`marketplace.yml` | 保留并改为 Sync plugin marketplace | 正式 Release 的计划、审核、main 路径更新和公开回读；预览跳过 |
| Dependency Graph | 保留 | GitHub 依赖图和 Dependabot 所需数据，不参与发版；不新增对应 YAML |

### 7.1 CI

保留 main push 和指向 main 的 PR 触发。继续以 `npm test` 验证所有注册
插件；只将与本次发布机制有关的断言迁入统一门禁，不额外重构插件行为。
使用锁文件执行 `npm ci`。构建到空临时目录并逐包检查。

移除“已提交 dist 等于当前构建”的要求。公开清单检查核对冻结发行记录、
安装目录、SHA 固定引用和所有权回执；不能要求已上线版本等于开发版本。
检查无正式发行的源码候选未进入市场、preview 未进入默认入口。

### 7.2 Release plugin

仍以 main 上的手动入口执行，输入插件 ID、既有规范源码标签和操作
`prepare/publish`。版本与 preview/stable 从选定插件清单派生，先核实标签
确实属于该插件且源码提交可从可信 main 到达，不用执行时移动的 HEAD
代替冻结源码。准备 job 只有读取权限，验收报告与公开写权限分开。

`prepare` 只产出可复验 bundle；`publish` 在 `plugin-release` 环境审核后
创建 GitHub Draft、上传完整附件、核对附件，再公开为 Prerelease 或正式
Release。保留现有 draft helper 的不公开职责，公开动作使用独立、受控步骤。
现有同版本 Release 不覆盖，远端标签移动或附件不一致时拒绝公开。

预览发布到此结束；正式发布成功后直接调用市场同步的可复用任务。
手工在 GitHub 网页公开的正式 Release，通过 main 的 Sync 手动入口补偿。

### 7.3 Sync plugin marketplace

提供 `workflow_call` 和 main 的 `workflow_dispatch`；手动入口继续支持
plan/apply 和已审阅基准、哈希。Release 流水线调用时先生成可下载计划与
job summary，审核后 apply，仍须重新验证同一基准与哈希。

调用端 job 必须授予被调用写入 job 所需的权限上限；可复用工作流不能从
调用端的只读 token 自行提升到 contents:write。同步中的 plan job 仍显式
降为只读，apply job 才使用写权限，不能为整条流水线统一开放写权限。

不要依赖 GITHUB_TOKEN 公开 Release 或 push main 自动启动另一工作流。
GitHub 对这类事件有防递归规则，正式发布流程应显式调用同步任务。
两个受保护环境仅允许 main 部署，因此本轮不把 `release: published`
的标签 ref 直接当成受保护部署入口；checkout main 不能改变事件 ref。

继续按仓库串行，防止多插件并发更新覆盖彼此。apply 使用普通 fast-forward
push；失败后的重试重新获取基准并生成计划，不盲目重放写操作。
GITHUB_TOKEN 写入的 D/C 不能假定会自动触发 CI，因此发布任务自身要在
写入前运行必要检查，并在最终回读后验证公开快照。

## 8. GitHub 设置

| 设置 | 目标 |
| --- | --- |
| 默认源码与市场分支 | main |
| `plugin-release` | 复用已授权环境：main 可部署、Zack-Zz 审核、无新增密钥 |
| `plugin-marketplace` | 同上；计划与版本差异可见后才审核部署 |
| Actions 权限 | 默认 contents:read；只有 Release/市场写入 job 获取 contents:write |
| Release immutability | 保持启用；附件上传、验证完成后才公开 |
| Dependency Graph/Dependabot | 保留，不作为发行或宿主验收通过标志 |
| main 的规则与保护 | 不为了机器发布关闭保护或给机器人自动增加绕过权限 |

本轮只读查询确认：远端 main 为同一 `b09371f`，branch API 返回
`protected=false`，rulesets API 返回空数组；两个环境均只有 `main` 类型为
branch 的部署规则，审核人为 `Zack-Zz`。这不证明运行时 GITHUB_TOKEN 已有
写入能力。首次写 main 前仍核对当时有效保护与 token 权限；若不允许直接
push，则生成受管内容 PR，通过现有保护要求后合并，再回读确认。不要默默
替换成 PAT 或新增高权限密钥。

## 9. 迁移与实施顺序

1. 版本模块先走有效失败测试，再替换全部比较与校验入口。保留历史
   `1.0.2` Prerelease 的读取及复验，不修改已公开字节。
2. 实现新配置、正式发行记录、唯一当前指针和公开市场生成；区分源码
   catalog 与已上线清单，覆盖多插件、未发布候选及预览隔离。
3. 将部署器改为 main 受管路径更新、实际 D/C 绑定、并发拒绝和失败回执。
   移除旧全树/双分支路径的写入能力；只读历史兼容继续保留。
4. 调整三份 YAML 和辅助脚本，保留两个环境与 Dependency Graph。
5. 开发市场迁入临时构建输出；切换根清单。旧根清单与 lock 只有在与已知
   迁移前回执完全一致时才替换，未知编辑拒绝覆盖。
6. 给 dist 增加忽略规则并停止 Git 跟踪；本地文件与历史 Git 内容不删除。
   更新 AGENTS、作者指南、发布指南和双语 README，避免再要求提交 dist。
7. 发布前 review 与统一门禁通过后，按本次授权边界分别提交、推送；通过
   GitHub 实际执行验证后再切换用户市场来源。第一份正式市场需要真正通过
   stable 验收的新版本，不能把现有 1.0.2 预览版直接当作正式入口。

旧 preview 分支在迁移期间作为已安装 `1.0.2` 的兼容来源，不向其中追加
新版本。它的存在不表示新系统仍采用双分支。无正式版的过渡阶段，在文档
中明确新的默认市场尚无可安装正式版本，旧预览安装属于历史试用。

## 10. 验收与用户升级

最低测试场景：

- `preview.2` 与 `preview.10` 排序、非法版本、预览/正式标志冲突。
- 发布预览版不触碰 main 市场；没有正式版时不出现预览默认入口。
- 单插件新正式版仅更新该插件，兄弟插件和 main 范围外文件不变。
- 同版本字节冲突、延迟旧版本、标签移动、未知文件、目录链接均拒绝。
- 基准改变拒绝；D 已写入但 C 失败时旧入口可用、回执准确且能重新计划。
- 冻结源码 S、Release 附件、D 的目录与 C 的清单跨层字节一致。
- 正式发布后的显式工作流调用、环境审核、写入权限与公开回读实际通过。
- dist 已被忽略且没有跟踪文件；干净 runner 无预置 dist 也能构建发行套件；
  CI 对强制加入的 dist 文件失败，部署器拒绝写入 dist。

运行 `npm test`、公共源校验、临时构建、独立包检查与 lint；验证集对最终
代码状态有效。文档或脚本检查不代替真实 Actions 执行和原生宿主验收。

用户侧区分“市场可用版本”“本机已安装版本”“会话已加载版本”。更新先
刷新市场，再升级插件，再核对已安装版本和哈希，按宿主要求重新加载。
README 按宿主列出经过验证的原生命令和自动更新设置，不宣称发布后本机
必然立即升级。三端至少验证连续两个正式版本的安装、升级与最终加载；
Codex 先前刷新超时必须重新排查并验收。

## 11. 依据与验证边界

- [SemVer 规范](https://semver.org/)：版本语法、预览优先级与版本内容不可改。
- [OpenAI 插件分发](https://developers.openai.com/plugins/build/plugins)：
  根市场、Git 子目录来源与固定 ref/sha；本机 CLI 帮助补充接口核对。
- [Claude 插件更新](https://code.claude.com/docs/en/discover-plugins#keep-plugins-updated)：
  市场刷新、插件更新与会话加载是不同状态，第三方市场自动更新有独立设置。
- [GitHub 工作流触发](https://docs.github.com/en/actions/how-tos/write-workflows/choose-when-workflows-run/trigger-a-workflow)：
  GITHUB_TOKEN 事件的防递归限制与显式调用需求。
- [GitHub 依赖图](https://docs.github.com/en/code-security/concepts/supply-chain-security/dependency-graph-data)：
  GitHub 管理的依赖图任务，与本项目发布无关。
- [GitHub Actions artifact](https://docs.github.com/en/actions/tutorials/store-and-share-data)
  与 [Release](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)：
  runner 构建输出可独立上传；任务留档与公开插件分发分开存储。

本稿来自当前工具/YAML、只读 GitHub workflow 与 rulesets 查询，以及一个
只读 code_explorer 对 Codex 单入口能力的补充核对。还读取了 main 分支、
两个环境及其部署规则。没有将设计、静态检查或
既有三端 1.0.2 安装记录当作新机制已实现、已部署或升级已验收的证据。
