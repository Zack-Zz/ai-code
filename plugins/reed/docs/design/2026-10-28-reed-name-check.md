# Reed：名称使用与商标初步核查

查阅日期：2026-10-27 至 2026-10-28（Asia/Shanghai）。对象：本地 Agent 研发工作流插件 Reed，不设中文名。

## 1. 结论与当前决定

**Reed 已有多处公开软件使用、包名占用和美国有效商标记录，不能称为未占用或已清权的名字。** 本轮未核实完全相同定位的研发工作流产品，但找到了「离线工作区＋Agent/MCP」的邻近同名项目，搜索辨识有实际重叠。

用户已选择 Reed，本轮继续用这个名字完成设计，不擅自改名。`plugins/reed/` 是 ai-code 仓库内部目录；目录可用不等于公开品牌、域名、包名或商标可用。本轮没有注册、购买、发布或联系任何第三方。

商标是否冲突取决于地区、标识及具体商品服务等因素；同类号并不自动等于侵权，不同用途也不自动免责。本报告是初查，**没有完成商标清权，也不判断他人的使用属于恶意侵占**。[USPTO 混淆可能性说明](https://www.uspto.gov/trademarks/search/likelihood-confusion)

## 2. 已核实的公开使用

| 对象 | 一手证据与事实 | 对 Reed 的影响 |
| --- | --- | --- |
| 同名离线工作区 | [is2b007/Reed](https://github.com/is2b007/Reed) 面向分支叙事游戏设计和生产，公开描述为 offline-first；仓库说明包含 SQLite、CLI/MCP、Git/PR 和人工审核 | 受众不同，但名称、本地工作区和 Agent 工具关键词相邻，存在辨识重叠 |
| 同名自托管软件 | [simonives/reed](https://github.com/simonives/reed) 是自托管 RSS 阅读器，提供 REST API 与 MCP | Reed 在个人/自托管工具领域也已有使用 |
| AI 产品和域名 | [Reed.ai 官方站](https://www.reed.ai/) 运营 AI 招聘 Agent | `reed.ai` 已实际使用；不把「Reed AI」当作无人使用的组合；该站与下节商标持有人不据同名推定为同一主体 |
| npm 裸包 | [官方注册表 reed](https://registry.npmjs.org/reed) 的 latest 为 `0.9.8-2`，描述为 Redis/Markdown 博客核心，指向 [ProjectMoon/reed](https://github.com/ProjectMoon/reed) | 裸名已存在，不计划覆盖；读取元数据没有安装或执行该包 |
| PyPI 裸包 | [reed](https://pypi.org/project/reed/) 是 Reed 招聘 API 的客户端，页面提供 `0.0.4` | Python 裸项目名已有使用 |
| 既有 CLI | [reed-cli](https://pypi.org/project/reed-cli/) 公开以 `reed` 命令处理文章转换 | 将来全局命令可能冲突，应优先内部入口或有作用域的调用 |

npm 网页本轮可能受限；官方注册表元数据可读取。上表证明存在使用，不证明当前维护质量、市场规模或权利范围。

## 3. 美国官方库的实际查询

在 [USPTO Trademark Search](https://tmsearch.uspto.gov/) 实际打开浏览器，使用 Wordmark 搜索 `REED`；排除 Dead，勾选 009、042，关闭 Coordinated。最终界面显示 38 条结果。这是搜索系统的广义匹配，包含复合文字等，不是「38 个相同 Reed 商标」，也不是只检索两个类号就覆盖了全部近似标识。

本轮实际展开/读取了下列相关条目：

| 文字 | 申请序列号 | 本次界面状态/主体 | 看到的范围与限制 |
| --- | --- | --- | --- |
| REED | 76227894 | LIVE / REGISTERED；RELX INC. | 结果列出 009、016、035、041、042；展开含出版物、会议与在线信息等长描述。部分计算机软件词句在方括号内，不能将这些词句未经案卷核实就作为当前有效开发软件范围 |
| REED AI | 99116965 | LIVE / REGISTERED；Reed AI Ventures Inc. | 009 和 042 的展开内容为面向沟通、语言教育及学习/言语障碍用户的 AI 软件和 SaaS，具体用途与本项目不同；仍应作为近似标识交给专业检索评估 |

回查入口：[REED 案件](https://tsdr.uspto.gov/#caseNumber=76227894&caseSearchType=US_APPLICATION&caseType=DEFAULT&searchType=statusSearch)、[REED AI 案件](https://tsdr.uspto.gov/#caseNumber=99116965&caseSearchType=US_APPLICATION&caseType=DEFAULT&searchType=statusSearch)。TSDR 静态抓取未返回完整案卷；上述状态来自本轮官方搜索界面的实际读取，不是从第三方商标聚合站推断。

原始观察材料：

- [官方筛选结果文字快照](assets/name-check-2026-10-28/uspto-reed-live-009-042.txt)
- [官方筛选结果界面](assets/name-check-2026-10-28/uspto-reed-live-009-042.jpg)
- [REED 商品服务展开文字](assets/name-check-2026-10-28/uspto-reed-76227894-goods.txt)
- [REED AI 商品服务展开文字](assets/name-check-2026-10-28/uspto-reed-ai-99116965-goods.txt)
- [REED AI 商品服务界面](assets/name-check-2026-10-28/uspto-reed-ai-99116965-goods.jpg)

这些是本轮公共查询证据，结果和权利状态可能变化。没有逐案审阅证书、修订、转让、争议和实际商业使用，不能称为正式法律意见。

## 4. 未完成的检索

| 范围 | 本轮实际情况 | 不能得出的结论 |
| --- | --- | --- |
| 中国商标局 | [官方查询入口](https://sbj.cnipa.gov.cn/sbj/sbcx/) 抓取返回 403；[国家知识产权局办事入口](https://www.cnipa.gov.cn/col/col253/index.html) 可定位服务 | 未完成中国 REED 的有效/近似商标检索，不能说中国没有冲突 |
| WIPO | [Global Brand Database](https://www.wipo.int/en/web/global-brand-database/index) 介绍页可读，查询站返回验证页面，未完成结果检索 | 不能说国际可注册；WIPO 也建议按需要另查国家/地区注册簿 |
| 其他地区 | 未完成 EUIPO、英国及其他目标地区查询 | 不承诺全球唯一或全球可用 |
| 域名/市场/账号 | 只核实 `reed.ai` 已实际使用；未完整查候选域名和四宿主插件市场名称 | DNS、搜索无结果或某个市场不存在，都不等于域名/品牌可注册 |
| 近音、变体、图形、未注册使用 | 有限关键词公开使用核查，未做完整近似或未注册权利调查 | 不把搜索命中数量当法律风险分数 |

## 5. 对当前工程的建议

1. 本轮界面和设计规格继续使用 Reed；没有中文名。描述性定位可写「Agent workflow workbench」，不把描述当成已经消除混淆的措施。
2. 仓库内使用 `plugins/reed/` 与拟定插件 ID `reed`，首次正式清单建立前再核查 ai-code 自身目录/市场中的身份冲突。此处没有注册外部名称。
3. 将来需要 npm 包时采用实际拥有的用户/组织 scope，例如 `@<已拥有的作用域>/reed`；不假定 `@ai-code` 已拥有或可用。[npm scope 规则](https://docs.npmjs.com/cli/v11/using-npm/scope/)
4. 不依赖抢占裸命令 `reed` 或 `reed.ai`；公共安装入口可先沿用 ai-code 市场、插件身份及宿主原生入口。
5. 在公开品牌投入、商业分发或注册前，按目标地区、实际软件/服务范围进行专业商标检索，并带上 76227894、99116965 及邻近同名软件。是否保留名字是基于该检索的后续决定，本轮不自动放弃或替换 Reed。

## 6. 证据与交付边界

公开使用由独立只读研究助手收集，主代理回读了相关官方仓库、Reed.ai、PyPI 和 npm 注册表，并亲自在美国官方查询界面核对结果和商品服务。中国、WIPO 和其他地区的未完成部分如上保留。

本报告只保存公开资料和查询快照；没有创建商标申请、付费查询、域名购买、包发布、平台账号或插件市场注册。
