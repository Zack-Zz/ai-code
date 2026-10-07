# 三宿主发布机制（2026-10-07）

用户明确要求先建立发布机制，覆盖 Claude Code、Codex、ZCode。本轮在现有
多插件构建上实现发布预检、制品准备和独立复验；不执行安装、Git 操作或
对外上架。已有 CodeVow 更名改动保留，安装 ID 与候选版本仍为
ai-code-workflow / 2.0.0。

## 范围与实现顺序

1. 保存当前未提交基线，补 Claude 原生清单、市场和 reviewer 适配，按声明
   宿主构建，保持公共技能和策略字节一致。
2. 以 product.json 的 publisher 为公开署名单源，生成 native author 与 Codex
   developerName，补 CodeVow 的声明性图标和真实上架说明。
3. TDD 实现 release check、prepare、verify，区分完整性、草稿和稳定资格。
4. 生成三端仓库根市场入口及其内容哈希归属记录；CI 检查它们与注册表和
   实际 dist 的一致性，不建立第二份身份/版本清单。
5. 添加手动 GitHub Actions：构建并保存候选制品，可明确选择创建 GitHub
   草稿 Release。公开 Publish、官方投稿和审批继续由用户执行。
6. 完整测试、源/包/ZIP 校验、可复现性与独立审查，交付未提交 diff。

## 三宿主布局

| 宿主 | 插件原生清单 | 市场清单 |
|---|---|---|
| Claude Code | .claude-plugin/plugin.json | .claude-plugin/marketplace.json |
| Codex | 根 plugin.json（portable） | .agents/plugins/marketplace.json |
| ZCode | .zcode-plugin/plugin.json | marketplace.json |

Claude 使用命名空间技能和原生 agents 目录。readonly reviewer 的元数据和
正文按宿主格式生成；未完成实际会话前，一律不宣称工具限制或工作流行为
已经由宿主强制执行。旧 A25 双端证据不自动升级为三端验收。

## 发布输入与独立版本

各插件 product.json 继续是 ID、版本、名称和资源白名单的来源。可选 publisher
对象只含公开 name、url、email；由同一对象注入宿主元数据，不复制认证信息。
图标作为普通白名单资源，不加载外部字体、脚本或 URL。

插件 release.json 为固定路径配置，结构为 schema_version、notes、
readmes（en / zh-CN）、acceptance（每个声明宿主的 null 或证据文件路径）。
不复制产品 ID/版本。notes 和双语 README 使用受控路径；官方源目录只放
安装源码和说明，不混入原始会话、临时凭据、历史机器路径或下载 ZIP。

验收记录绑定 host、version、source_tree_hash、package_content_hash、
host_version，以及非空 artifacts 的路径和 SHA256。工具检查可读文件和
绑定关系，不能自行证明外部会话真实，也不能把 accepted 标记当用户授权。
发布制品只引用状态和哈希，原始会话材料不随制品分发。

版本只支持当前契约的 X.Y.Z。稳定准备要求已提交干净源码，以及规范 tag
ID/vVERSION 解析到当前 HEAD，公开源输入、配置与说明须与 HEAD blob 字节
一致，防止 ignored 公开输入漏出标签；原始私有材料无需提交。本轮不创建 tag。已可信历史制品的相同版本
不得换内容，版本降低拒绝；历史制品路径由调用者选择，完整性不等于证明
它曾被某个平台公开发布。不同插件独立准备和命名，不共享单一根版本。

## 命令与草稿边界

```sh
python3 tooling/plugin_tool.py release check --plugin ai-code-workflow --mode draft
python3 tooling/plugin_tool.py release prepare --plugin ai-code-workflow --mode draft --output release-check
python3 tooling/plugin_tool.py release verify --plugin ai-code-workflow --path release-check
python3 tooling/plugin_tool.py marketplace sync
python3 tooling/plugin_tool.py marketplace sync --check
```

check 为只读报告，prepare 在空输出的私有 staging 内构建、校验、复查输入后
发布到目标目录。输出拒绝 Git 内部目录及其别名。draft 保留 dirty 和未验收事实，metadata/路径/绑定错误仍
失败；stable 对欠缺验收或来源条件返回失败，不能用草稿假装稳定版。
verify 根据可信源码独立重建应有路径、字节和 ZIP 结构，不只重算制品自报
哈希。CLI 保留现有 0/1/2/3/4/5 语义；没有执行代码 hook 的扩展点。

## 制品契约

- packages/：选定插件的三宿主标准分发及原生市场，沿用 dist schema 2。
- downloads/：名称含插件、版本和宿主的下载 ZIP，带对应单插件本地市场。
- submissions/openai/：唯一插件根的 skills-only 投稿 ZIP，无市场兄弟文件。
- submissions/claude/、submissions/zcode/：可供评审的独立源码 ZIP及源目录，
  plugins/ID 内无 artifact.json、ZIP、会话日志；包含对应原生清单和双语 README。
- release-notes.md、SHA256SUMS、release.json：实际版本、来源、资格报告、
  制品闭包和字节哈希，无固定当前时刻以保证同输入可复现。

仓库市场入口指向 ./dist/HOST/ID。marketplaces.lock.json 只记录这三个固定
原生路径的生成哈希，无版本、时间或授权标记。sync 仅更新已归属且未被
用户编辑的内容；未知内容或链接报冲突，按文件原子写入，不声称文件组具有
操作系统整体事务性。check 不写文件。

## GitHub Actions 与外部操作

默认手动任务只构建和保存制品，最小只读权限。创建 GitHub 草稿使用单独
手动开关及写权限步骤，先要求正确现有 tag、复验制品、禁止重用现有 Release
或 clobber 附件。该流程不创建 Git tag、不自动 commit、不调用 OpenAI Publish，
也不代发 Claude 官方投稿或 ZCode PR。

稳定产物与草稿创建选项是不同维度：缺少真实验收时只能准备明确草稿，不能
靠切换 UI 开关跳过稳定检查。正式 Publish 由人检查源码、资格及附件后执行。
云端实际运行和账号权限需后续在该仓库验证，本轮不宣称已在 GitHub 启用。

## 规范依据

[Claude 原生清单](https://code.claude.com/docs/en/plugins-reference)、
[Claude 市场](https://code.claude.com/docs/en/plugin-marketplaces)、
[OpenAI 包结构](https://developers.openai.com/plugins/build/plugins)、
[OpenAI 上架字段](https://developers.openai.com/plugins/deploy/submission)、
[OpenAI ZIP 规则](https://developers.openai.com/plugins/deploy/submission-errors)、
[ZCode 贡献约定](https://github.com/zai-org/zcode-plugins/blob/main/CONTRIBUTING_CN.md)。
官方审核结果、认证身份和真实宿主资格不会由仓库单元测试产生。
