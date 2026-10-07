# 整体 Review 修复交付（2026-10-03）

Directory note (2026-10-07): this is the dated workflow baseline, now under
`plugins/ai-code-workflow/`. Original counts, commands and hashes below are
historical evidence; they do not validate the migration. Current navigation
and shared packaging are described in [the multi-plugin design](../../../../docs/design/2026-10-07-multi-plugin-design.md).

原 Review 的 21 项问题已按下表修复；复审发现的相邻边界缺陷也纳入同一轮回归。交付层级仍为 `implemented_with_acceptance_blocked`，真实宿主 T07 不属于本轮通过声明。

## 问题闭环

| 编号 | 修复结果 | 主要回归 |
|---|---|---|
| R01 | collect/grade 在写入前拒绝场景子目录链接与特殊文件 | linked scenario subroots、outside sentinel |
| R02 | 对同次读取的源字节计算哈希并写入该字节 | published source bytes match receipt |
| R03 | remove 也核对 receipt.managed_root，拒绝外来归属 | receipt copied from another target |
| R04 | host_run/pass 拒绝已声明的非零退出、signal、start_error | declared execution failure |
| R05 | A23/A24 执行捕获包 CLI；校验原始基线、完整发行身份与 provenance | bound runtime mutant、baseline/package drift |
| R06 | 构建测试采用明确的 clean/dirty/no-Git 情境 | provenance context regressions |
| R07 | check/update 共用完整记录校验；任务身份、revision、嵌套字段及安全读取统一 | wrong id/revision、malformed nested records、task metadata link |
| R08 | remove 完成回执生命周期；相同载荷 update 修正错误元数据；真正 no-op 保持原字节 | missing payload、metadata-only update、no-op |
| R09 | receipt 比较包含缺失状态，更新中删除回执报冲突且保留恢复材料 | deleted receipt during update |
| R10 | protected/subject 指纹限定工作区内普通文件；缺失父目录表示不存在 | outside link、persisted escape、missing intermediate |
| R11 | JSON 通过 no-follow/nonblocking 句柄读取，fstat 后按实际 MAX+1 字节限额 | FIFO、growth after stat、linked parent |
| R12 | capture/ref 哈希先验类型再 fullmatch；畸形数据返回稳定错误或逐项失效 | numeric/object/bool/newline hash |
| R13 | 界面文本采用正确转义的 JSON/YAML 字符串，生成后再校验 | quotes/newline/Unicode round trip |
| R14 | 校验技能的实际相对 Markdown 资源链接是否落在资源白名单 | missing/unregistered local link |
| R15 | 私有暂存内验证包与 ZIP 闭包后发布；失败保留原输出 | source/closure fault、transactional output |
| R16 | artifact provenance 严格校验类型与格式 | revision/dirty/source hash malformed |
| R17 | ZCode reviewer 的 inherit、只读 tools、maxTurns 静态约束统一校验 | source and resealed package reviewer mutants |
| R18 | A24 运行真实 update 中断，核对已应用/未应用项与字节备份 | actual interrupted update、later user edit |
| R19 | Python 门禁显式拒绝空 discover，默认汇总器使用该入口 | empty helper and default group |
| R20 | A19 去掉显式 push 授权，使预期“不可 push”与输入一致 | case contract |
| R21 | A18 在基线后保留未提交 staged 修复，用于测试授权 commit | staged diff/HEAD baseline |

复审进一步核实并修复：A24 恢复哈希逐项匹配、并发胜者真实载荷/receipt 校验、A25 全部共享资源（含许可证）一致、构建复制期间来源快照与哈希一致、包内额外 FIFO 拒绝，以及恢复目录链接/畸形与重复归属锁的保护。新增负向用例覆盖源码变化和 mutate-copy-restore，不以绿色汇总代替这些行为断言。

## 验证与产物

- `npm test`：7 项汇总器自测、12 项 Node 技能契约、265 项 Python 测试全部通过。
- `validate --root .`：28 个源码白名单文件校验通过；`npm run lint` 与 `git diff --check` 通过。
- 七个核心模块语句覆盖率 **87.6%**（1839/2100），各模块均 ≥80%，详见 [覆盖率报告](../coverage.md)。CLI/eval 子进程没有完整覆盖率测量，不纳入该比率。
- 新鲜 A23/A24/A25 全部 `overall=pass`，实际执行绑定包 CLI；材料根 `/private/tmp/ai-code-fix21-final-acceptance-04whe_18`，各 `run/` 内保留 grade、命令、stdout/stderr、计划与恢复材料。
- `dist/` 已重建：两端 package check 通过，72 个文件两次同源构建字节完全一致（包含 ZIP）；CI distribution checker 通过。来源哈希以实际包资源与来源元数据独立重算一致。
- 本轮运行环境：Python 3.13.3 / Node 22.16.0；`working_tree_dirty=true` 如实保留，源码 revision 仍为 `2d90761dba57e90f40f21b3fd1dde9482e5a6aaa`。

| 产物 | 文件数 | content_hash | zip_sha256 |
|---|---|---|---|
| zcode | 30 | `9b0ae707cd62025035c997a18091659bb483306be8de9bca8c23ec432618e56e` | `d6b42f55e04fe18a91173a5fcc8d6b67224fb7c0b1661a41f87e98a248f1bb37` |
| codex | 35 | `76900f6bb549ce73802efe86ae4f477386fecc2a7609092326cb9132a66f907c` | `cf5219f69d03037e8f96e47e7ddd545f12e8ded9d17c5b53d32f5a74bb3d2a90` |

双端相同来源树哈希：`588748f3a49d87435532362fff1ecb39fa1be662861e0f8001ee7f6dcead0eb0`。

## 复审与边界

IO/state/owned-files 修复经过独立只读复审与临时目录负向复现；eval 与 packaging 分别交叉审查，复审发现的增量修复再做回归。最终未保留已确认且未修复的 P1/P2。

本轮未修改用户全局配置、未执行模型调用或真实宿主安装，未执行产品仓库 commit/push/tag/merge/PR。原有暂存改名保持不变。完整性检查使用可信源码工具，不能让待检查包自举验证；损坏包的 Python 缓存可能在检查器启动前阻塞，参见 [安装说明](../installation.md)。真实 T07 仍需可用且有授权的宿主会话，参见 [支持矩阵](../support-matrix.md) 与 [既有环境记录](../../evals/blocked-env-2026-10-02.md)。

完整修复前恢复快照：`/private/tmp/ai-code-fix21-20261003-000629-vwdqr3ro/`。本机临时复现材料仅用于本轮审计；可重跑测试与确定性验收生成新证据。
