[English](2026-10-27-identity-migration.md) | 简体中文

# 2026-10-27 插件身份迁移

安装 ID 从 `ai-code-workflow` 变为 `codevow`。本次源码变更不会修改用户安装。
通过宿主原生方式卸载旧插件，刷新同一个 `ai-code` 市场，再安装并启用新 ID，开启新会话。
新旧插件技能名称相同，应先卸载旧版，避免同名技能遮蔽。DSH 首次安装没有旧 DSH 插件需要卸载。
实际入口以已发布记录为准，候选源码不代表已上线；旧 Release、标签和冻结文件继续保留。

项目 `.ai-workflow/` 中 policy、tasks、evidence 的结构与目录不变。文件暂存工具按新身份使用
`.ai-workflow/staged/codevow` 与 `.ai-workflow/receipts/codevow.json`。旧身份的暂存、回执和备份
保留，不自动认领或迁移。旧工具生成但尚未应用的 files 计划会被新工具拒绝，请用新包重新生成，
不要修改计划来替换身份或路径。旧会话恢复行为须逐宿主验收。
