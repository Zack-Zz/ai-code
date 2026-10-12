# 发布验收证据契约

[English](release-evidence.md) | 简体中文

技术发布与真实宿主验收是两个独立结果。宿主槽仍为 `null` 或 pending 时，
正式 Release 与市场更新可以继续；脚本测试、包哈希或发布成功都不能证明
原生安装、技能调用与运行行为。只有真实场景完成且材料经维护者核对后才能
使用 `accepted`。本指南保留可选的严格证据格式与导出契约，普通发布无需
维护者手写验收 JSON。安装见[用户指南](installation.zh-CN.md)，发布见
[发布指南](publishing.zh-CN.md)。

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
  "version": "1.0.0",
  "source_tree_hash": "REPLACE_WITH_CURRENT_SOURCE_SHA256",
  "package_content_hash": "REPLACE_WITH_CURRENT_CODEX_PACKAGE_SHA256",
  "host_version": null,
  "summary": "尚未执行真实宿主验收",
  "artifacts": []
}
```

上例仅展示字段，版本须取目标插件的 product.json，哈希须使用实际值，不能
直接作为有效记录。实际值来自
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

## 独立的宿主验证

源码检查、包完整性、Release 公开、市场同步与宿主运行验证分别报告。
技术就绪的正式报告可以同时出现 `publication_ready=true` 和非空
`pending_acceptance`；列出 `accepted_hosts`、pending 宿主和 `limitations`，
不能把 pending 解释成验收通过。

分别检查 Claude Code 的固定 archive URL/SHA256、ZCode 的 ZIP
URL/SHA256/path，以及 Codex 固定分发提交中的安装目录。记录市场登记、
发现、首次安装、更新、实际加载内容和错误哈希拒绝，再验证技能调用、授权
边界、适用插件的 Reviewer 行为及包内工具。只说明实际达到的验证层次，
原生加载不代表所有行为通过。每个声称 accepted 的宿主都须有独立真实记录。
发布后的宿主实测可以作为独立验证报告绑定测试版本及字节，无需修改不可变
Release 或其冻结源码。

`null` 槽不要求私有文件。若填写了证据路径，普通本地
`release check/prepare/verify` 会读取实际 JSON 和原始材料并严格核验绑定；
失效、缺失或错误证据是错误，不能当作通过。干净的 CI checkout 可显式使用
`--committed-acceptance` 核验经审核的公开摘要而不读取私有正文，Actions
使用此模式。没有摘要且没有证据引用时，宿主保持 pending，技术发布可继续。
工具不从环境变量切换模式，也不静默忽略已提供的坏记录。

## 可选的严格验收导出

全部声明宿主均完成字节绑定验收后，在保留私有记录和日志的本地源码执行：

```sh
python3 tooling/plugin_tool.py release acceptance-export --plugin ai-code-workflow
```

导出器逐项读取并核验记录和实际日志；任何宿主 pending、文件缺失或哈希
不匹配都会拒绝导出。结果仅为目标插件的 `release/acceptance-proof.json`，
包含身份、版本、源哈希、全部宿主包哈希、精确公开输入哈希，以及证据和
日志的规范路径与 SHA256，不含 summary、日志或验收 JSON 正文。
导出和 committed 读取共用 1 MiB 上限；相同导出幂等，既有摘要变化须先
审阅，再显式使用 `--replace`。不能手写摘要代替真实测试。

审阅摘要后，在已授权的发布过程中将它与最终公开源码一起冻结在规范标签
`ID/vVERSION`，原始材料保留在插件内被忽略的私有路径。摘要不包含所在提交
的 SHA，避免自引用。committed 核验要求干净源码、规范标签、摘要字节等于
HEAD Git blob，并重算公开输入与包哈希。工作区或 HEAD 已有的摘要不能因
损坏、删除、未提交或过期而回退到私有模式。同一冻结源码的两种模式生成
相同完整制品字节。

源码、说明、配置或包字节变化会使旧绑定失效。若继续声称验收通过，须重新
执行相关宿主验证并导出。若准备尚未验收的新版本，本地 `prepare-version`
helper 可明确重置旧证据引用、移除有效生成摘要，保留私有文件与发布历史，
预览会列出所有变化。新宿主保持 unverified，清空槽不代表验收通过。

摘要是维护者的事实声明，不是平台认证、签名服务，也不能证明 CI 重跑了
私有会话。CI 无法仅凭哈希证明会话真实性或模型效果。证据 JSON、Agent
写入的 `accepted`、计划哈希和摘要都不授予 commit、push、tag、发布、部署、
安装或官方目录投稿权限。已授权的 Actions 发布仍使用 `plugin-release` 和
`plugin-marketplace`，环境若配置审核人，运行可能暂停等待审核。详见
[发布流程](publishing.zh-CN.md)。
