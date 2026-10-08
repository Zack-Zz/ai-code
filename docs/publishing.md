# CodeVow 三端发布（更新于 2026-10-08）

公开名称为 **CodeVow**，安装 ID 为 `ai-code-workflow`，当前候选版本 `1.0.1`。
用户确认新插件尚未安装后，将首个 CodeVow 版本定为 `1.0.0`；此前工程
候选 `2.0.0` 留在历史记录中，后续发版正常递增。

分发主渠道是 GitHub 自建市场，覆盖 Claude Code、Codex、ZCode。当前为
试用候选，三端真实宿主验收仍未完成；官方目录认证、投稿与审核没有执行。

## 自建市场的最短发布路径

本仓库本身就是市场，不需要另建网站、服务器或申请官方收录。三端根入口
指向 `dist/` 内的原生包，市场名称为 `ai-code-local`，安装 ID 为
`ai-code-workflow`，展示名为 CodeVow。

1. 核对本轮源码，完成 `validate --all`、`npm test`、lint、可信包检查，以及
   `marketplace sync --check`；构建产物必须与当前源码一致。
2. Review 后完整提交并推送源码、图标、`dist/` 和三个根入口。只有推送后的
   ref 才能供其他人从 GitHub 注册市场；本地未提交文件不能代替远端分发。
3. 在三端添加 `Zack-Zz/ai-code` 并安装 CodeVow，记录实际加载和行为。试用
   状态保持 `unverified`，不得把下载或安装成功说成稳定版行为验收。

Claude Code：

```sh
claude plugin marketplace add Zack-Zz/ai-code
claude plugin install ai-code-workflow@ai-code-local
```

Codex：

```sh
codex plugin marketplace add Zack-Zz/ai-code --ref main
```

重启支持该市场的桌面客户端，在插件目录选择 `ai-code-local` 来源，安装
CodeVow；CLI 负责登记市场，客户端实际能力须按当前版本验证。
[OpenAI 市场说明](https://developers.openai.com/plugins/build/plugins)

ZCode：打开工作区，进入设置 → 插件 → 创建 → 添加插件市场，填仓库地址，
在“个人”的 `ai-code-local` 分组选择 CodeVow 安装。
[ZCode 市场说明](https://zcode.z.ai/cn/docs/plugin)

后续改动升高插件版本，重建 `dist/`，同步市场并校验，再 Review、commit/push。
试用分发可跟随 main，不需要使用下面的官方投稿套件；正式 stable 制品仍
遵守本项目的干净源码、规范标签和全部声明宿主验收门禁。GitHub 草稿
Release 属于可选留档渠道，创建标签或 Release 需要对应授权。

## 1. 准备资料与版本

`plugins/ai-code-workflow/product.json` 是身份、版本、宿主、公开 publisher
和白名单的唯一来源。当前署名采用 `Zack-Zz` 和公开 GitHub 主页，无邮箱；
这只是展示资料，官方目录账号认证需另行完成；自建市场按原生方式分发。
CodeVow 的 PNG 发布图标与 SVG 备用标识均已登记入包，三端共用品牌。

插件的 `release.json` 配置发布说明、双语包说明及每个声明宿主的验收路径，
不复制身份或版本。`release/NOTES.md` 维护当版变化；`release/README.md` 和
`README_CN.md` 是供投稿源码套件使用的可移植说明。不要放入凭据或机器路径。

版本使用 `X.Y.Z`，每个插件独立推进。首次公开版本内容确定后，后续改动应
升版；同版本不得对应不同内容。当前规范标签为 `ai-code-workflow/v1.0.1`，必须
指向冻结源码的 HEAD。稳定资格和 GitHub 草稿上传均核对公开输入与该提交
的 Git blob 字节一致，被忽略但列入公开资源的文件不能漏在标签之外。原始
私有验收材料只验证哈希，不要求提交。创建和推送标签需要用户单独授权。

## 2. 本地预检、准备与复验

在仓库根运行，输出目录必须不存在或为空。建议放到仓库外，避免干扰 Git
工作区状态。Python 管理工具要求 3.11+ 和 POSIX 受控目录读写；其他系统
尚未验收。原生技能文本不需要 Python。

```sh
python3 tooling/plugin_tool.py validate --all
npm test
npm run lint
python3 tooling/plugin_tool.py release check --plugin ai-code-workflow --mode draft
python3 tooling/plugin_tool.py release prepare --plugin ai-code-workflow --mode draft --output /tmp/codevow-release
python3 tooling/plugin_tool.py release verify --plugin ai-code-workflow --path /tmp/codevow-release
```

`draft` 允许未提交和未验收事实，同时仍拒绝无效资料、错误路径、字节绑定
及不完整制品。`stable` 要求干净 Git、规范现有标签和所有声明宿主的实际
验收记录；缺少任何项返回非零。`ok: true` 仅表示该模式的检查通过；查看
`publication_ready`、`pending_acceptance` 和 `limitations` 判断后续缺项。

`verify` 使用可信当前源码重建整个应有闭包和 ZIP 内容；仅重算制品自己的
哈希无法通过。检查不安装、不上传、不操作 Git。

复验旧草稿时，`bundle_provenance` / `bundle_readiness` 保留包内历史记录，
`current_source` 报告当前 Git 状态。顶层 `publication_ready` 只有在两者均
满足资格且来源一致时才为 true，包内自报 clean 不能覆盖当前工作区的事实。

以后准备新版本时，给 `check`、`prepare`、`verify` 提供
`--previous /可信旧发布包/release.json`：工具检查旧包实际文件及归档，拒绝
同版本内容变化和版本降低。旧包由维护者选择并可信保存，本地完整性检查
不能证明它曾公开发布；遗漏该参数不会自动查询平台历史。

## 3. 制品和仓库市场

| 产物 | 用途 |
|---|---|
| `packages/` | 标准三宿主目录、单插件 ZIP、市场与索引 |
| `downloads/ID-VERSION-HOST.zip` | 解压后注册本地市场的试用下载包 |
| `submissions/openai/ID-VERSION.zip` | 唯一插件根的 OpenAI skills-only 投稿包 |
| `submissions/claude/`、`submissions/zcode/` | 独立源码 ZIP、`plugins/ID/` 和原生市场，供渠道检查及人工提交 |
| `release.json`、`SHA256SUMS`、`release-notes.md` | 来源、资格、文件闭包和字节哈希 |

下载 ZIP 带本地市场，不能直接替代 OpenAI 投稿 ZIP；投稿套件不含下载包、
原始会话或 artifact.json。哈希清单路径相对于完整发布包根。

根市场指向已生成的 `./dist/HOST/ID`：

| 宿主 | 仓库市场入口 |
|---|---|
| Claude Code | `.claude-plugin/marketplace.json` |
| Codex | `.agents/plugins/marketplace.json` |
| ZCode | `marketplace.json` |

先用公共构建生成最终 `dist/`，再运行：

```sh
python3 tooling/plugin_tool.py marketplace sync
python3 tooling/plugin_tool.py marketplace sync --check
```

`marketplaces.lock.json` 只记生成文件的内容哈希，不是版本或授权来源。sync
拒绝未知内容、用户编辑和符号链接；check 只读。提交并推送完整市场及匹配的
`dist/` 后才能向用户提供远端仓库市场；本地文件存在不代表已上线。原生
安装命令见[安装说明](../plugins/ai-code-workflow/docs/installation.md)。

## 4. 真实宿主验收记录

`release.json.acceptance` 的三个槽目前均为 `null`。在对应宿主真实加载、
运行场景并核对结果后，记录宿主和模型版本、插件与包哈希、命令、会话和
结论，再填本插件内证据 JSON 的相对路径。记录格式见
[发布证据契约](release-evidence.md)。当前 A25 检查三端包的共同资源和来源，
仍不证明宿主运行；旧双端 A25 记录不能冒充新的三端验收。

工具核对源、包和原始材料哈希，不证明外部会话真实性，也不将 `accepted`
解释为用户发布授权。原始材料只在本地验证，公开制品只含状态和绑定哈希；
发布者仍需审阅全部白名单和说明，避免主动把敏感材料登记为公开资源。

## 5. GitHub 手动流程

[release.yml](../.github/workflows/release.yml) 仅接受 `workflow_dispatch`。默认
`create_github_draft=false`，只校验、测试、构建和保存 30 天的 Actions artifact，
使用 `contents: read`。源 ref 默认 main，也可选择已存在的规范版本标签。

需要 GitHub 草稿时显式打开开关；独立 job 使用 `contents: write` 和
`plugin-release` environment。仓库管理员应配置该 environment 的审核人、
允许的 ref 与 tag 保护规则；代码声明 environment 不代表这些规则已启用。
该 job 复验收到的完整制品、干净 Git、现有本地及远端标签指向的提交，拒绝
已有 Release，并始终使用 `gh release create --draft --verify-tag`，不创建标签。
[GitHub CLI 行为](https://cli.github.com/manual/gh_release_create)

草稿附件包括三端下载 ZIP、完整发布包 ZIP 及其 SHA256、发布记录和说明。
完整包包含投稿套件，避免同名投稿 ZIP 在 GitHub 附件中冲突。Actions 上传
显式保留 native 隐藏目录，下载后再次复验。草稿和附件可由人审阅，正式
Publish 不自动执行。云端权限、实际 workflow 运行和网络调用尚未验证。

若远端调用中途失败，可能留下一份附件不全的草稿；流程失败退出、不自动
重试或覆盖。人工核查和清理后再处理。远端标签读取与创建是独立请求，流程在
创建前后复查；创建后发现移动或无法确认时失败退出并保留草稿链接，供人
检查，不自动删除。需依赖仓库 tag 保护，直到人工 Publish 前再次核对绑定。

## 6. 官方收录参考（当前不使用）

**Claude Code**：先通过自身市场分发，原生清单为
`.claude-plugin/plugin.json`。实际投稿前执行当地版本的
`claude plugin validate --strict <插件目录>` 并做真实安装会话。当前官方文档
将 Anthropic directory 的申请指向开发者门户；该目录与
`claude-plugins-official` 官方市场是不同入口，后者收录需咨询官方渠道。
本机制先生成 Claude Code 源码套件，不承诺其 Code-only Agent 在其他应用
可用，也不代填旧表单或默认通过 PR 投稿。
[Claude 发布文档](https://code.claude.com/docs/en/plugins/publish)

**Codex / OpenAI**：CodeVow 无 MCP，使用 portable 根 plugin.json 的 skills-only
路径；开发者认证、后台上传独立投稿 ZIP、审核、获批后人工发布。原生字段
和图标检查在本地执行，但目录资格及最终分类由后台决定。目前工具实现
SVG/PNG 图标及已核对的 Developer Tools、Productivity 分类子集；不代表平台
所有合法格式或分类。未来加入 MCP、hooks、apps 时需独立设计和渠道验证，
当前发布 profile 会拒绝这些组件。
[OpenAI 提交要求](https://developers.openai.com/plugins/deploy/submission)、
[唯一根 ZIP 规则](https://developers.openai.com/plugins/deploy/submission-errors)

**ZCode**：Fork 官方插件仓库，将 `submissions/zcode/` 中所需源码和登记项
人工合并到 Fork；保留官方其他插件条目，不整份覆盖其市场。运行官方
`scripts/validate.py`、`scripts/build_dist.py`，完成真实 ZCode 验证，再由用户
授权提交 PR；维护者负责审核和发布。HTTPS ZIP 市场的 URL/SHA256/path 协议
是另一种分发方式，当前源码套件不自动提供线上 URL。
[ZCode 贡献要求](https://github.com/zai-org/zcode-plugins/blob/main/CONTRIBUTING_CN.md)、
[分发协议](https://github.com/zai-org/zcode-plugins/blob/main/docs/distribution_CN.md)

根 Node 包为 private 维护工具，不执行 npm publish。正式发布前核对
[支持矩阵](../plugins/ai-code-workflow/docs/support-matrix.md) 和各渠道当时要求。
