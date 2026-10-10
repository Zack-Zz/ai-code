# 发布验收证据契约

这是发布工具的数据契约，不是验收结论或用户授权。CodeVow 三个宿主当前均
为 `unverified`。只在真实宿主场景已经完成、由维护者核对材料后使用 accepted。

## 发布配置

每个插件的 `release.json` 只声明路径和宿主槽：

```json
{
  "schema_version": 1,
  "notes": "release/NOTES.md",
  "readmes": {"en": "release/README.md", "zh-CN": "release/README_CN.md"},
  "acceptance": {"claude": null, "codex": null, "zcode": null}
}
```

acceptance 必须恰好覆盖 product.json 的 hosts。`null` 表示尚无验收；有记录
时填插件目录内的规范相对路径，拒绝绝对路径、`..`、符号链接和跨插件读取。
配置和证据 JSON 拒绝重复/未知字段。说明为非空 UTF-8 Markdown。

## 验收记录

记录固定字段为 schema_version、status、host、version、source_tree_hash、
package_content_hash、host_version、summary、artifacts。例如未验收记录：

```json
{
  "schema_version": 1,
  "status": "unverified",
  "host": "codex",
  "version": "1.0.2",
  "source_tree_hash": "REPLACE_WITH_CURRENT_SOURCE_SHA256",
  "package_content_hash": "REPLACE_WITH_CURRENT_CODEX_PACKAGE_SHA256",
  "host_version": null,
  "summary": "尚未执行真实宿主验收",
  "artifacts": []
}
```

上例的哈希是待替换占位符，不能直接作为有效记录。实际值来自
`release check --plugin ID --mode draft` 的 source_tree_hash 和
readiness.package_content_hashes；使用当前对应宿主值，不能用 ZIP 哈希或
artifact.json 文件哈希替代 package_content_hash。

accepted 记录须包含非空 host_version、summary 和 artifacts，每项为
`{"path":"private/acceptance/codex-session.txt","sha256":"实际64位小写SHA256"}`。
模型、平台版本、测试命令、原生加载和行为结果、验证者及时间写在会话材料
中；summary 简述结果和仍有的限制。路径仍锚定于该插件源码目录，文件内容
的实际 SHA256 必须一致。每条记录的宿主、版本、源哈希和包哈希全部与当前
候选相符。unverified 不允许声称 host_version 或携带验收 artifacts。

原始材料路径不能是公开源输入、发布说明或配置，也不能借硬链接/相同字节
副本把材料登记成公开输入。发布工具只将状态、路径绑定和哈希写入机器
记录；原始材料及验收 JSON 的正文不复制到发布制品。人工仍须检查公开
白名单和文档内容，工具不识别任意文本片段中的敏感信息。

## 实际验收与 CI

1.0.2 候选新增运输验收边界：分别验证 Claude 的固定 archive URL/SHA256、
ZCode 的 ZIP URL/SHA256/path，以及 Codex 固定发行提交中的版本目录。
每端至少两个连续版本，记录市场分支登记、发现、首次安装、刷新、升级、
cache 字节及错误哈希拒绝。下载成功、渠道 deployed 和安装成功各自记录，
不能据此把工作流行为写成 accepted。schema 2 installer 的完整性测试与
schema 1 历史复验也只证明制品层，不证明宿主运输支持。

Release、市场计划/部署与运行行为证据相互独立。计划哈希、记录文件、
GitHub prerelease 或 accepted 标记均不产生 Git、Publish 或部署授权。
既有 2026-10-08 的 1.0.1 验证记录保留原版本、日期和哈希；不作为 1.0.2
候选或新运输协议本轮通过的证据。

对每个宿主分别验证原生清单、市场发现、安装加载、技能触发、工作流授权
边界、Reviewer 行为和包内工具的可用性。记录到达的验证层次及未完成项；
脚本测试不能证明宿主实际遵循 Markdown。只做到了原生加载就不能据此将
全部行为写成 accepted。旧双端场景不能替代 Claude Code 的真实记录。

默认本地 `release check/prepare/verify` 仍要求验收 JSON 与原始材料可读，
逐项检查实际字节。GitHub 的干净 checkout 使用维护者审核后随源码冻结的
哈希声明，不从环境变量或文件缺失自动选择验收模式。

完成全部宿主验收后，在保留私有文件的本地源码执行：

```bash
python3 tooling/plugin_tool.py release acceptance-export --plugin ai-code-workflow
```

命令按原本的严格规则读取所有验收记录和日志；任何宿主 pending、缺失文件
或哈希不匹配都拒绝导出。结果固定为该插件的
`release/acceptance-proof.json`，仅包含身份、版本、源哈希、所有宿主包哈希、
精确公开输入哈希、验收文件与日志的规范路径和 SHA256。不包含 summary、
日志或验收 JSON 的正文。导出与 CI 读取共用 1 MiB 上限；既有摘要内容变化
时须先审阅，再显式使用 `--replace`，完全相同的导出幂等。

审核摘要后，将它与最终公开输入一起提交并创建规范标签；原始材料留在
被忽略的插件内 `private/` 路径。摘要不包含最终提交 SHA，避免文件与所在
提交自引用；Actions 单独确认摘要字节等于标签所在 HEAD 的 Git blob，要求
干净源码和规范标签，并重算所有公开输入与包哈希。源码、说明、配置或包
字节改变后须重新执行验收与导出，旧摘要不能继续使用。

Actions 的 Prepare、Draft、Publish、市场计划/部署及历史复验显式使用
`committed_acceptance`。本地需要重现该模式时可传
`--committed-acceptance`；普通本地命令继续检查实际私有文件。存在于工作区
或 HEAD 的摘要不能因损坏、删除、未提交或过期而回退到本地模式；无摘要的
历史调用仍只能使用完整私有材料通过原规则。公开制品保存原有私有输入
摘要，不包含私有正文，两种模式对同一冻结源码生成相同的完整制品字节。

这份摘要是维护者经过本地验证后提交的事实声明，不是签名服务或平台认证，
CI 无法重新证明私有会话真实性。不得手写摘要代替验收。`plugin-release`
和 `plugin-marketplace` 的人工审核继续承担各自的发布授权，不新增远端密钥。

证据 JSON 的 accepted 是事实声明，工具无法自行证明会话真实性、平台审核
或模型效果。由 Agent 写入 accepted 也不授权 tag、Release、投稿或 Publish。
详见[发布流程](publishing.md)。
