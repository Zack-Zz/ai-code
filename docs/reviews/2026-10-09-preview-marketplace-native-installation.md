# CodeVow preview 市场部署与原生安装

日期：2026-10-09（Asia/Shanghai）。插件：`ai-code-workflow`，版本：`1.0.2`。
这是[首次 Release 记录](2026-10-09-codevow-first-release.md)之后的执行结果，
保留前一报告在其记录时点的事实。发行文件和源码标签没有改写。

## 远端发行与市场

- [Release](https://github.com/Zack-Zz/ai-code/releases/tag/ai-code-workflow%2Fv1.0.2)
  ID `407432151`，`draft=false`、`prerelease=true`、`immutable=true`。
  全部 11 个上传资产已实际下载；大小和 SHA256 与干净标签重建结果一致。
  完整发行 ZIP 已下载并作为部署输入复验，不能再把它记为仅服务端哈希匹配。
- [preview 分支](https://github.com/Zack-Zz/ai-code/tree/codex/marketplace-preview)
  已部署，市场名 `ai-code-preview`，只有 CodeVow `1.0.2`。
  D、C 实际 Git 树和文件字节均与部署计划一致；匿名 HTTPS 读取 C 的
  三端市场 JSON，与实际 Git C 的对应文件一致。

| 绑定 | 值 |
|---|---|
| 源码 S | `e11578a8981b9993c8aaca5a0d70f4570c48e117` |
| 规范标签 | `ai-code-workflow/v1.0.2` |
| reviewed plan hash | `664e5cc429f9caa12946b16d9c23f9cfa1853da2dcb101aec098a7e8439e62a9` |
| 基础状态 | `absent`，`bootstrap=true` |
| 发行内容 D | `acaea90f84690b2d9f074126d41217c2aeec2918` |
| 市场目录 C | `3f469eb5f25f9edc85d1e2451541e8cfc97c025e` |
| 完整发行 ZIP SHA256 | `fe2d851fa414b3a6f55be32fac717312a58bb87cfc1abeb04af919563dcaec03` |
| 源树哈希 | `24793827cd6d0c2d2e890a12f671575afd1cf9ba5b1a68d7f4355e0b711e6ae9` |

Claude 清单使用固定 archive URL/hash；ZCode 根清单使用固定 ZIP URL/hash/path；
Codex 使用 D 中 `plugins/codex/ai-code-workflow/1.0.2` 及固定 D SHA。
三个 installer ZIP 的 SHA256：

| 宿主 | SHA256 |
|---|---|
| Claude | `343ad1e68cf1e5c246ffe76d74050b166603671921ac4e47021853ec1acaa533` |
| Codex | `1bc06c203c061c44523d04f8496238d0f4a7273822ddb1537afe9f5cdb0c58a6` |
| ZCode | `1756d3a189755625d20242f714a4859ddd6c2590d5ba9311c02e241adff4ea28` |

## 部署执行方式与限制

首次实时 plan 暴露 GitHub 仓库元信息 REST 路径的尾斜杠问题：
`GET /repos/Zack-Zz/ai-code/` 返回 404。测试先复现 URL 差异，再最小修复为空
relative 时使用规范路径；编码 tag/query 的路径保持不变。
`4f01aa4ddc0c8a14dcff1365b3a8458edfad02cf` 已推送 main，49 个相关测试、
lint 和 diff 检查通过；独立 reviewer 对此修复及部署读回风险进行了审查。
[该提交的 CI](https://github.com/Zack-Zz/ai-code/actions/runs/37878786784)
实际读回为 completed/success。

本轮市场部署通过本机执行，**没有运行市场 Actions workflow，也没有验证
其 GITHUB_TOKEN 和环境审批路径**。浏览器无法完成 Actions 调度；匿名
GitHub API 剩余额度不足以逐 blob 读取待部署树，使用以下受限传输方式：

- 生产 plan/check/deploy 与 GitWriter 仍负责计划重算、版本与源码约束、
  D/C 提交、正常推送和基础状态检查；没有 force push。
- 制品读取使用已下载的 immutable Release 资产。部署前实时 REST 复核
  Release ID、immutable 状态和每个资产的 ID、名称、大小、digest、URL、
  上传状态，再复核实际文件 SHA256；套件和独立 installer 继续由生产逻辑复验。
- Git 读取通过同仓库 SSH，完整枚举 ls-tree，校验路径、类型、模式、
  blob object hash 与实际 archive 字节。tar 使用 umask 0022，拒绝隐藏或改写
  tracked 文件的 export-ignore/export-subst 结果。

临时传输适配没有提交或入包，没有修改 GitHub 环境保护、规则或凭据。
这是实际部署方式的记录，不替代未来对 Actions 部署路径的验证。
工作区另一插件及生成市场的未提交变更没有进入冻结源码、Release 或本次市场。

## Codex

Codex CLI `0.154.0`，通过原生命令：

```sh
codex plugin marketplace add Zack-Zz/ai-code --ref codex/marketplace-preview --json
codex plugin add ai-code-workflow@ai-code-preview --json
```

原生 list 读回 `installed=true`、`enabled=true`、版本 `1.0.2`，git-subdir
路径和固定 SHA 与 D 一致。缓存位于宿主自己的版本目录；40 个文件的完整
闭包和每个文件字节与已下载、经可信源码复验的 Codex installer ZIP 一致。
内容哈希为 `8be1c00221e33f52aeacbbd378b7e4277adb3ee1b0bce95fb058a25f06eabab4`。

通用 package check 首次对版本命名缓存报目录名及父市场 wrapper 不匹配。
该检查针对发行布局，不能直接作为原生缓存检查；没有改名缓存或放宽检查器。
后续使用完整文件集合和逐字节对比确认安装内容。

两次 `codex plugin marketplace upgrade ai-code-preview` 都在 Git clone 30 秒
超时，并返回 `fatal: early EOF`。随后一次仅对命令设置同仓库 SSH URL
映射、一次仅对命令使用本机已存在的 HTTP 代理重试，也都超时；用户提供
完整三项 Bash 代理变量后再次重试，仍超时，共五次。没有修改
全局 Git、代理或市场来源。失败后安装/启用状态、固定 SHA 和缓存
字节仍一致；刷新成功、ref 保留与跨版本更新不能据此记为通过。

## ZCode

应用 `3.14.5`，内置插件 CLI `0.16.9`，入口为应用资源里的
`/Applications/ZCode.app/Contents/Resources/glm/zcode.cjs`；PATH 没有独立 zcode 命令。

原生界面首先添加 Git URL 和 preview ref，显示市场与一个 CodeVow 条目。
但其缓存的根清单保存了 Claude archive 来源。读取实际 CLI 的
`Qat` → `PJr` → `Tre`/`Xat` 调用链确认：Git 导入优先选择
`.claude-plugin/marketplace.json`，再选根 `marketplace.json`。
安装器 `ict` 不支持 archive；`url` + `type=zip` 则经过 `KGr`/`Yun`
下载、校验 SHA256，并按 path 提取插件。

通过原生命令移除本轮新注册、尚无安装插件的预览市场，再直接注册同分支的
ZCode JSON URL；没有手工编辑缓存或全局配置：

```sh
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins marketplace remove ai-code-preview
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins marketplace add \
  https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/codex/marketplace-preview/marketplace.json
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins install ai-code-workflow@ai-code-preview
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins marketplace update ai-code-preview
```

安装回执为 `1.0.2 [enabled]`；原生 list 发现 6 个技能、没有 diagnostics。
35 个缓存文件完整闭包及字节与 ZCode installer ZIP 一致，内容哈希为
`14859e17e4d7c87a48998328b6d9125492e53fcf4c8a70c53933bce3dcf2eea1`。
原有 21 个插件的版本、启用状态保持不变；其他市场保留。同版本市场刷新
成功，不等于跨版本升级通过。UI 安装交互未完整验证，以上结果来自原生 CLI。

## Claude Code

本机起始版本 `2.1.177`，低于 archive 来源要求的 `2.1.224`。
用户明确允许官方更新，并明确授权三端原生注册、安装与启用。
两次 `claude update` 都尝试更新 `2.1.295`，因 socket 连接关闭而失败。
随后从 `https://claude.ai/install.sh` 下载、检查并运行官方安装脚本，
完成官方 CLI 下载；独立与版本 `2.1.295` 官方 manifest 重算 SHA256，
darwin-arm64 二进制为 239695888 字节，哈希
`0116ee2e0a513900b633d9951367f18747686478e2b462805b8c31609f047f70`。

用这份官方 CLI 执行一键安装及同版本刷新：

```sh
claude plugin install ai-code-workflow --marketplace \
  https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/codex/marketplace-preview/.claude-plugin/marketplace.json --json
claude plugin marketplace update ai-code-preview
```

命令中的 `claude` 在此次执行时是官方脚本下载的 `2.1.295` 可执行文件完整
路径，不能把它当成默认启动器已经升级。install 返回 JSON `outcome=ok`，
user scope；原生 list 读回 `1.0.2`、`enabled=true`。35 个缓存文件的完整
闭包和字节与 Claude installer ZIP 一致；内容哈希为
`123b97ed42c1c95fccf9a9d91aa6c400a01b82b45c398abbdd8b14a18ae07f2c`。
原有 9 个插件登记的版本、scope 和启用状态保持不变，原有市场保留。
清单刷新成功，同版本刷新不代表跨版本升级通过。

原生宿主更新单独记录：官方脚本在原生安装阶段长时间未完成；取消后脚本
输出 Installation complete 并返回 0，但默认 `claude --version` 仍为
`2.1.177`，启动器仍指向旧版本，新版本目标文件为 0 字节。因此没有把
这个退出码记作更新通过，也没有手工替换启动器或版本文件。脚本自动清理
其下载文件。之后确认本机既有 Clash HTTP 代理监听，并仅给一条官方
`claude update` 命令设置标准代理变量重试，约 6 分钟未完成后取消；读回
仍为旧启动器和 0 字节目标。随后通过官方 `install 2.1.295 --force`
重试修复本次未完成安装，非交互执行仍停在 Installing。真实终端重试仍在
运行；只读网络计数确认安装进程在接收数据，不能把控制台无新输出和目标
尚未落盘直接当成卡死。前面的取消过早，不据此断言安装器故障。
截至本次记录，默认启动器仍为 `2.1.177`，宿主更新尚未通过验证。
没有启用系统代理、修改 PATH、手工复制版本文件或
增加第二套安装。两次原始 update 有 socket 关闭错误；后续挂起的具体根因
尚未确定，不将其推断为已证实的锁或网络问题。

## 验证边界

本轮已取得三端注册、安装、启用的明确用户授权，更新 Claude 也另有明确授权。
采用宿主原生入口；未通过编辑宿主缓存来伪造安装结果。

安装、启用、静态技能发现和制品字节相同，不证明模型会自动调用技能、
执行完整 TDD、遵守策略或保持 Reviewer 只读约束。没有改写 acceptance 槽，
没有准备 stable、创造第二个版本或声称两版升级完成。
