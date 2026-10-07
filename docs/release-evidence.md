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
  "version": "2.0.0",
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

对每个宿主分别验证原生清单、市场发现、安装加载、技能触发、工作流授权
边界、Reviewer 行为和包内工具的可用性。记录到达的验证层次及未完成项；
脚本测试不能证明宿主实际遵循 Markdown。只做到了原生加载就不能据此将
全部行为写成 accepted。旧双端场景不能替代 Claude Code 的真实记录。

稳定准备要求这些材料在构建环境可读且绑定一致。当前 GitHub workflow
不会自动获取私有验收材料：若材料未包含在选定 ref 的可公开源码中，CI 将
因缺失而失败。含私密信息的会话日志应保留本地，在可控环境做 stable 检查；
不得为让 CI 通过而提交敏感原文。可公开的证据须先由人审核，再决定是否
提交。源码仓库公开与发布制品公开是两个不同边界。

证据 JSON 的 accepted 是事实声明，工具无法自行证明会话真实性、平台审核
或模型效果。由 Agent 写入 accepted 也不授权 tag、Release、投稿或 Publish。
详见[发布流程](publishing.md)。
