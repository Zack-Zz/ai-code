# GitHub 市场实现与发布准备记录

日期：2026-10-08。候选：CodeVow `1.0.2`，首个 GitHub 发行拟使用 preview。

## 已实现与本地验证

- schema 2 发行套件新增三端 plugin-only installer；保留 downloads 和
  submissions，显式兼容 schema 1 历史包。
- 固定正式/试用渠道，单插件独立 Release，聚合市场保留其他已发布插件。
- 本地 distribution plan/check；远端部署默认 plan，经审核 hash/base
  绑定后才执行 D/C 分阶段推进，远端读回及固定安装提交校验。
- 公开历史包从实际 Release 下载复验并传入 previous；已有 Codex 安装
  提交实际树必须与记录闭包一致，不能仅自改记录和哈希。
- 部署失败保留阶段、已知 D/C 或不确定的 attempted revision，非零退出
  仍保存结果；Actions 以 always 上传恢复记录。
- 写权限管理脚本来自可信 main，与冻结的源码 checkout 分开；原生
  Actions 固定实际查询过的 commit SHA；草稿模式标记 GitHub prerelease。
- 保留旧 main 市场和 dist，三端包重建到 1.0.2；真实运输验收通过前不
  取消 dist 跟踪，不把首次试用发行冒充 stable。

`npm test` 四组通过：汇总器 13 项、公共工具 Python 168 项、技能契约
13 项、CodeVow Python 302 项。其后失败恢复的最后一处空 ref 保护已用
定向部署/工作流 19 项测试检查并通过。`npm run lint`、源 validate、YAML 语法、可信
dist 对比、市场 sync --check、git diff --check 通过。

本地审阅套件 `/tmp/codevow-1.0.2-review-bundle` 240 文件 prepare/verify
通过，诚实记录 dirty、无规范标签、三端 unverified。发布前须从冻结并
打标签的干净源码重新构建，不直接上传这个审阅包。

本轮使用两名 code_implementer 并行实现安装制品和纯市场目录，主会话
完成部署、CLI、Actions、集成与验证；另有 code_reviewer 对部署风险独立
只读审阅。已修复确认的历史 pin、计划容量、失败恢复缺陷；最终只读
复查未发现剩余确认缺陷。审阅者未运行测试，测试结果由主会话确认。

## 远端观察与剩余步骤

GitHub 只读查询：Zack-Zz/ai-code 为 public，main 原始提交
`92ee5846ce202c04d2c5def1f49a0402bbcf23b7`，查询时无 tag、无 Release。
当前浏览器确认 release immutability 已启用；本轮未声称由脚本开启。

用户明确授权后，已创建并配置 `plugin-release`、`plugin-marketplace`。
浏览器及公开 REST API 均确认：required reviewer 为 Zack-Zz，
prevent_self_review=false，can_admins_bypass=false，部署策略只有
`main` 分支，没有 tag 策略；未添加 secret 或 variable。
首次创建曾被自动审批拒绝，原因是持久访问边界需明确授权；得到用户
针对两个环境及上述范围的授权后继续完成，没有绕过拒绝。

准备公开：只提交本轮发布机制、CodeVow 元数据、生成包和本设计/实现记录；
保留其他未提交架构文档和 ai-agent-delegation 目录。待取得明确 Git 授权，
再推送源码、创建 `ai-code-workflow/v1.0.2`，从干净源码复建并上传完整
Release 草稿，公开为 prerelease，生成与审阅 preview 市场部署计划。

两个 environment 配置已验收；仓库分支/tag rulesets、真实 Actions、Release
上传与公开、preview 分支推进和真实宿主安装均尚未验收。
用户后续明确要求 Review，无问题后 commit、push；该源码提交和推送已获
本次授权，tag 与市场分支推进仍单独处理。当前三端 acceptance 槽仍为空；
本记录不产生 Git、发布、安装或权限变更授权。

## 最终提交前 Review

主会话检查安装包 schema 兼容、可信源码重建、CLI 和发行附件；独立
code_reviewer 重新检查真实部署及 CI 路径，确认两处有效更新缺陷：

1. 同一插件的新版本减少 hosts 时，旧空宿主市场入口残留，造成闭包拒绝。
   已用失败回归覆盖三端缩减和共享市场保留；现在只允许删除本次审核计划
   确认的三个固定市场入口，历史 records 和版本目录保持。
2. 支持的 repository 地址带 `.git` 时，入口没有规范化，产生错误 API
   路由及重复 `.git` 的 Git 地址。已用入口捕获失败测试修复，管理脚本
   共享市场模块的规范化逻辑。

修复后的部署、目录和 workflow 定向回归 47 项通过；独立只读复查未发现
剩余确认缺陷。最终 `npm test` 四组通过：汇总器 13 项、公共 Python
173 项、技能契约 13 项、插件 Python 302 项；源码、市场、lint 与 diff
检查通过。真实 GitHub workflow 执行和宿主验收不从这些本地检查推导。
