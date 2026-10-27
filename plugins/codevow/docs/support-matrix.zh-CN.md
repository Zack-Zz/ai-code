[English](support-matrix.md) | 简体中文

# 当前支持与验证边界

当前源码身份为 `codevow`，声明 Claude Code、Codex、ZCode、DeepSeek Harness 四个制品目标。
DSH 候选目标是 `0.2.1-rc.2` 的 Web profile，必须提供原生 preset、Agent、工具、提示词与 spawn
服务；缺依赖由原生 Loader 报告无法激活。Reviewer 的 read/grep/glob 白名单与文件系统隔离
分别记录，读取权限根复用宿主配置。四端 acceptance 保持 null。

本地结构、单元测试和包检查不证明原生加载、自动调用、权限执行、安装或生命周期验收。
[英文页中的历史记录](support-matrix.md)保留原有日期、命令和结论，不构成本轮通过。
