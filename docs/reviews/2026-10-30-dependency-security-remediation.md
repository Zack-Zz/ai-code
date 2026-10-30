# 依赖安全修复与验证记录

日期：2026-10-30。基线：`af225f3475146c7dfd4ba5dbe3f10828cedc9888`，开始时工作区干净。
本记录覆盖 ai-code 根维护工具链、未注册的 Reed 原型及其默认开发监听地址的修复和本地验收。
截至本地验收阶段未提交推送，未发布或安装插件；后续 Git 交付和线上告警状态须另行回读。

## 基线与计数口径

上一轮从 GitHub 实际读取 35 条开放告警：根锁文件 20 条（11 高危、7 中危、2 低危），
本次新增的原型锁文件 15 条（7 高危、7 中危、1 低危）。原先推送输出的 20 条尚未包含新原型扫描结果。
本轮先保存两份清单、锁文件和配置，再运行 npm 审计，根目录为 15 个受影响包、原型为 6 个。
GitHub 按告警计数，npm 还包含传递影响和包级聚合，两种数量不能直接相减。

临时原始输出和修改前文件保存在 `/private/tmp/ai-code-security-fix-20261030/`；不入发行包。

## 第一批：根工具链

- 固定 `markdownlint-cli 0.50.0`，保留 ESLint 9 主版本；锁文件中的 ESLint / @eslint/js 更新为 9.39.5。
- 刷新 minimatch、brace-expansion、flatted、js-yaml、smol-toml、markdown-it、linkify-it 等受影响传递依赖。
- 更新候选最初仍有 KaTeX 告警，并新增 RE2JS 告警；不把“升级到最新”当作修复证明。
- 根维护环境最低要求明确为 Node.js 22.12.0，开发与发布指南中英文同步；CI 仍使用现有 Node 22 版本线。

上游尚未解除的约束用三个限定父包版本的 overrides 处理：

| 父包 | 子依赖 | 原因与移除条件 |
| --- | --- | --- |
| markdownlint@0.42.0 | re2js 2.8.7 | 上游固定到受影响的 2.8.6；上游改用已修复版本后移除 |
| micromark-extension-math@3.1.0 | katex 0.18.2 | 上游范围 ^0.16 无法取得已修复版本；上游正式支持已修复版本后移除 |
| markdownlint-cli@0.50.0 | run-con 1.3.2 | 1.3.3 引入 ini 7，要求更高 Node 补丁版本；沿用基线中的安全版本与 ini 4.1.3，待上游依赖范围与维护环境兼容后移除 |

RE2JS 与 KaTeX 的修复版本分别依据 [RE2JS 公告](https://github.com/advisories/GHSA-gg6h-894w-4m9c)
和 [KaTeX 公告](https://github.com/advisories/GHSA-238p-pmpm-9mq7)。KaTeX 覆盖跨越上游声明的 ^0.16 范围，
因此另用真实 micromark `mathHtml` → KaTeX 渲染和 CLI 合法／非法 Markdown 输入检查兼容性。
升级上游时需要重新审计和回归，不能将这些覆盖无条件延续到其他版本。

独立复核发现的 Node 声明不一致已修复：首次候选安装出现 ini 的 EBADENGINE；
最终两份 `npm ci --engine-strict` 均通过，无 EBADENGINE。必需依赖的 engines 静态核对均接受 Node 22.12.0。

## 第二批：Reed 原型

| 依赖 | 基线 | 最终锁定 |
| --- | --- | --- |
| Vite | 6.4.2 | 6.4.5 |
| PostCSS | 8.5.16 | 8.5.32 |
| nanoid | 3.3.15 | 3.3.20 |
| Browserslist | 4.28.5 | 4.29.5 |
| source-map-js | 1.2.1 | 1.2.2 |
| baseline-browser-mapping | 2.10.42 | 2.11.34 |

React / React DOM 19.2.0、plugin-react 5.0.4、字体 5.3.0、图标 2.1.10 均保持原锁定值。
原型的最低 Node 要求与维护环境一致，为 22.12.0；README 中英文同步。

`server.host` 从 0.0.0.0 改为 127.0.0.1。新增实际 socket 回归：读取真实 Vite 配置，启动服务器，
检查监听地址及页面 HTTP 响应，最后关闭服务器。没有通过测试代码覆盖 host 来制造通过。
测试进入原型既有 `npm test` 入口；仍不将此未注册原型加入正式插件 catalog。

首次测试遇到已有默认端口占用，属于环境失败；调整测试允许 Vite 自动选择可用端口后，
有效 RED 为地址断言 0.0.0.0 != 127.0.0.1。修改配置后 GREEN，未停止用户原有服务。

开始前记录的 35 个 UI、mock、素材及 Sites 脚手架文件哈希保持不变；不清理浏览器存储、不改变模拟数据。
已有服务器进程需要重新启动才能保证使用新的依赖代码；本轮不宣称用户此前运行的进程已经更新。

## 最终验证

实际环境为 macOS arm64、Node 24.4.1、npm 11.4.2。

| 项目 | 结果 |
| --- | --- |
| 根目录 npm ci --engine-strict | 通过 |
| 原型 npm ci --engine-strict | 通过 |
| 根目录 npm audit --include=dev | 0 告警，退出 0 |
| 原型 npm audit --include=dev | 0 告警，退出 0 |
| 数学渲染与 Markdownlint 正反输入 | 通过 |
| 原型 npm test | 122 项通过，包含真实回环监听测试 |
| 原型 npm run build | 通过，保留 Sites 所需产物 |
| 原型 npm run test:sites | 4 项通过 |
| 根目录 npm test | 6 个测试组全部通过，退出 0；包含 351 项公共工具测试 |
| 根目录 npm run lint | 最终文档更新后通过，退出 0 |
| 登记插件构建及可信源包校验 | 11 个宿主包；目录与归档内容核对通过 |
| 源校验与无跟踪 dist 检查 | 通过 |
| git diff --check | 通过，退出 0 |

包检查器只接受解包后的宿主目录。ZIP 解包后再次用可信源码检查；TGZ 校验摘要、解包并核对与已验证目录的逐文件字节，
不把直接传归档文件给目录检查器造成的错误当作产品缺陷。所有输出均位于临时目录，未改变公开发行资源。
根目录测试的早期未完成运行在依赖兼容修正前停止，不能计为通过；表格只采用最终运行结果。

## 整体 Review 与边界

一名 `code_reviewer` 对根依赖、锁图、覆盖范围、Node 兼容性、原型监听及双语说明做独立只读复核。
其约束为 policy_only，未独立安装、运行应用或执行测试；主代理复核发现并完成全部命令验证。
Node 兼容发现已关闭，后续源码复核未发现新的确定缺陷；最终测试已取得成功终态。

- 未改正式插件源码、product/catalog/distribution、published 快照、业务行为或模拟数据；不提升插件版本。
- 本地验收时未提交推送，因此该阶段不能证明 GitHub 线上告警已经关闭；后续交付须单独回读远端扫描结果。
- 最低 Node 22.12.0 只核对必需依赖引擎元数据，未在该版本实跑；未验证 Linux/Windows。
- Rollup 的 Linux 可选 lzma 包要求更高 Node 版本；源码注明用于交叉构建，当前 Rollup 运行路径未引用，非本轮确认故障。
- 安装仍提示 ESLint 9 上游支持期已结束，本轮保留原主版本兼容；这不等于存在未修复的当前 npm 告警。
- 原型构建仍有大于 500 kB 的分块提示；没有修改页面、做分包或声明性能达标。
