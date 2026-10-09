# CodeVow 首个 GitHub Release

日期：2026-10-09。版本：`1.0.2`。渠道：preview / GitHub prerelease。

## 已完成

- 中英文根 README 新增普通用户安装入口：选择宿主 ZIP、核对
  `SHA256SUMS`、解压、注册 `ai-code-local` 并通过宿主原生方式安装。
  明确下载 ZIP、plugin-only installer 与 GitHub 自动源码快照的区别。
- README 提交 `e11578a8981b9993c8aaca5a0d70f4570c48e117` 已推送 main；
  两份公开 README 与该提交的字节一致。源码与发行使用独立的干净 checkout，
  没有纳入工作区另一插件的未提交改动。
- 规范 annotated tag `ai-code-workflow/v1.0.2` 已推送，远端解引用仍为
  上述源码提交。标签对象为 `656af63503e121b44db6d0f1a948aa98c753276d`。
- [源码 CI](https://github.com/Zack-Zz/ai-code/actions/runs/37873536037)
  和 [Prepare plugin release](https://github.com/Zack-Zz/ai-code/actions/runs/37873785451)
  均为 completed/success；发布环境审核后草稿上传成功。
- 草稿包含 11 个上传资产，发布前逐一将 GitHub 展示的 SHA256 与本地从
  同一标签重建的字节哈希比较，全部一致。
- 已公开 [CodeVow 1.0.2](https://github.com/Zack-Zz/ai-code/releases/tag/ai-code-workflow%2Fv1.0.2)，
  Release ID 为 `407432151`，发布时间为北京时间 2026-10-09 10:27:42。
  公开 REST 读回确认 `draft=false`、`prerelease=true`、`immutable=true`。
  11 个上传资产的名称、大小、上传状态和服务端 SHA256 与重建结果全部一致。
- Release 正文包含中英文安装链接，并保留构建时的验收记录；附件中的
  `mode=draft` 是构建检查模式，不是当前 GitHub Release 的公开状态。

## 发行绑定与验证边界

完整发行 ZIP 为 `ai-code-workflow-1.0.2-release-bundle.zip`，SHA256：
`fe2d851fa414b3a6f55be32fac717312a58bb87cfc1abeb04af919563dcaec03`。
发行源树 SHA256：
`24793827cd6d0c2d2e890a12f671575afd1cf9ba5b1a68d7f4355e0b711e6ae9`。

本地从干净标签 prepare/verify 通过，套件 240 文件。公开后的三端下载 ZIP、
三端 installer、校验文件、release.json 和 release-notes.md 已实际下载，
其字节哈希与本地重建结果一致。完整发行 ZIP 的服务端哈希已匹配；完整
下载与解包复验另行记录，不从服务端哈希推导实际下载完成。

三端包的内容哈希：

| 宿主 | package content hash |
|---|---|
| Claude Code | `123b97ed42c1c95fccf9a9d91aa6c400a01b82b45c398abbdd8b14a18ae07f2c` |
| Codex | `8be1c00221e33f52aeacbbd378b7e4277adb3ee1b0bce95fb058a25f06eabab4` |
| ZCode | `14859e17e4d7c87a48998328b6d9125492e53fcf4c8a70c53933bce3dcf2eea1` |

## 尚未完成

此次仅发布 Release，没有部署 preview 市场。公开查询时
`codex/marketplace-preview` 仍不存在，不能把 Release 的公开状态当成
市场部署成功。README 当前提供的是下载资产后注册本地市场的试用步骤。

Claude Code、Codex、ZCode 的真实安装、升级、加载和工作流行为均未验收，
三个 acceptance 槽仍为空；本次不安装宿主插件，也不修改用户全局配置或缓存。
正式 stable 发行仍须满足全部声明宿主的字节绑定验收要求。
