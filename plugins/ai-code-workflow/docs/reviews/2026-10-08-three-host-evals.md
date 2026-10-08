# CodeVow 1.0.1：三端验收与发行收尾记录

日期：2026-10-08。范围为用户确认的发行一致性和三端确定性验收工具链。
首次交付时，源码、发行物和市场入口已更新，改动保留未提交；未安装宿主、
运行模型会话、创建标签或发布。后续兼容修复及提交前验证见文末，三个
release acceptance 槽仍为 null。

## 修改范围与归属

- 在已有 Claude 证据输入修复之上实现三端样例和评分；既有 state/schema、
  collect/grade 输入扩展及其测试未回滚，也不作为本轮新写的全部代码。
- A23/A24/A25 为 product.json 实际声明宿主准备包。A23/A24 执行所选包内
  文件暂存、更新、移除、故障恢复和并发检查；A25 检查全部声明包及共同资源。
- A25 使用校验后的源码快照和场景来源绑定，完整比较生成 Reviewer 内容。
  grader_version 为 1.2.0，prepared/index 字段和一次性运行语义不变。
- 产品版本升为 1.0.1；更新当前说明、三端 dist/、ZIP、原生市场及其归属回执。
  历史版本、原日期、测试数和两端材料保留原范围。

## TDD 与审查

1. 首轮 Python RED：40 项中 14 个失败，暴露缺失宿主、Claude 共同资源漂移
   误通过及硬编码宿主；Node 契约 RED 为 9 通过、1 失败。
2. 损坏 Claude checker 输出的 3 个子场景先失败，再实现退出状态、JSON 形状
   与缺失哈希的失败结果保留。
3. 独立只读 code_reviewer 发现生成 Agent 追加正文和产品排除规则来源两个
   盲点；主 Agent 在隔离样例中复现两者错误 pass。追加 RED 为 10 项筛选测试
   中 5 个子场景失败，随后补完整正文匹配、闭字段验证和源码快照绑定。
4. 独立复审确认两项已解决，未发现新增可行动问题。审查为源码和调用链检查，
   未运行宿主；测试执行与发行整合由主 Agent 完成。

## 首次交付验证（兼容修复前）

| 验证 | 结果 |
|---|---|
| `npm test` | 4 组通过：公共 Python 129、插件 Python 300、Node 汇总器 13、技能契约 13 |
| eval 定向测试 | 45 项通过，含 3 场景 × 3 宿主 prepare→collect→grade、重复评分拒绝和失败路径 |
| review regression 定向测试 | 32 项通过 |
| `npm run lint` | ESLint 与 Markdownlint 通过 |
| 公共 `validate --all` 与插件专属 `validate` | 通过，版本 1.0.1 |
| 三端可信源码包检查 | Claude 34、Codex 39、ZCode 34 个包内文件通过 |
| 两次同源构建 | 117 个发行文件字节完全一致，包含 ZIP；独立发行比较通过 |
| `marketplace sync --check` | 三端入口与回执通过，changed=[] |
| draft `release prepare` / `release verify` | 对照可信 1.0.0 本地基线包通过，publication_ready=false |
| `git diff --check` | 通过 |

公共包检查从可信仓库执行 `tooling/plugin_tool.py package check`，没有使用待
检查包作为初始验证器。A25 的随包 CLI 结果是执行证据，仍不替代公共可信
检查。原生安装、技能触发、策略遵循、Reviewer 工具限制和业务效果未验收。

## 本轮来源与制品哈希

公共发行 source_tree_hash：
`5a4c92e2b9bb26632c9eb0e6bf47c99ea83cafcdc795feabb45678d6586c942d`。

| 宿主 | package_content_hash |
|---|---|
| Claude Code | `5eaeab01d2fc5844fe4f05de6bb00c6db689233bd355c686d8528ce556bade3d` |
| Codex | `a8d4bfcce7e381390b3eaf6b8c9e046beefbcff54215db31c650b105eb78fc7f` |
| ZCode | `2b6d6d1a69c6c0775a64674a2430ef8197bf71193427136dee061f083c95b835` |

workflow 专属 builder 的场景来源哈希使用其既有算法：
`8ced18413aac99dee11a0579eb7c3bb7f41c556ada9d24d86555c2c8763f470d`。
它与公共发行来源哈希的输入编码不同，不可互相替代。A25 在专属场景内绑定
其来源；发布证据使用公共工具返回的当前来源和对应宿主 package_content_hash。

发行索引保留真实 Git provenance：source_revision 为
`0932e15d1036563da47d15b5795ad81ea1d3cca3`，working_tree_dirty=true。
这是未提交候选的事实，不是 1.0.1 的已发布提交或规范标签。

## 复审后的兼容修复与提交前验证

后续只读复审发现 P2：合法旧式 product.json 省略可选 generated_agents 时，
构建器仍生成 Reviewer，评分器却误将该文件作为共同资源，造成 A25 错误
失败。同一份两端输入在 HEAD 基线通过、修复前版本失败，各端包检查均通过。
用户随后明确授权修复，并在确认无问题后 commit、push。

修复沿用 standalone builder 的宿主生成规则，在缺省和显式声明两种情况下
都完整核对 Reviewer；显式声明验证、源码快照绑定及任意排除拒绝继续保留。
没有把 generated_agents 改成必填字段，也没有新增受控操作权限。

- 有效 RED：新增 2 项测试中的 5 个子场景失败，覆盖缺省宿主、显式两端、
  显式三端，以及 Claude/ZCode 旧格式 Reviewer 正文漂移的错误诊断。
- GREEN：同一组测试通过；独立 code_reviewer 确认该 P2 已关闭，未发现新增
  可行动问题。审查只读，不宣称自行执行宿主或发布验证。
- 最终 `npm test` 四组通过：公共 Python 129、插件 Python 302、Node 汇总器
  13、技能契约 13，合计 431 项 Python 测试及 26 项 Node 检查。
- lint、公共及插件专属源码校验、三端可信包检查、新鲜构建与 dist/ 比较、
  marketplace sync --check、draft release prepare/verify、git diff --check
  全部通过。eval 合计 47 项，完整三端与失败保护由统一门禁重新执行。

兼容修复位于不入包的 evals 和测试中，包内来源与内容哈希保持上表数值。
本节记录提交前验证；实际 commit、push 结果以 Git 记录为准。规范标签、
正式发布和真实宿主验收不属于这次 Git 授权，也没有被标记完成。
