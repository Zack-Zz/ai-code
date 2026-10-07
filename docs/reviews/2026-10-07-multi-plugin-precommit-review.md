# 多插件改造提交前审查（2026-10-07）

结论：修复后可以提交。独立审查确认的 2 项 P1、1 项 P2 均已修复并用
原始场景复验；当前无剩余阻塞或应修复项。用户已明确授权审查通过后
commit、push，本次不创建 PR、不安装或发布宿主插件。

## 审查范围

审查覆盖插件注册到输入采集、引用闭包、生成资源、两端构建、ZIP、可信包
检查、测试门禁、CI，以及 workflow 原命令和受管文件生命周期。
公共工具、测试/CI、workflow 迁移分别由未编写对应实现的审查员复核。
只读约束来自任务指令，不宣称宿主强制阻止审查员写入。

Git HEAD 仍为旧版仓库，本轮完整版本依赖此前未提交的 workflow 基线和旧
资源清理，均纳入提交范围。没有把临时快照、测试日志、node_modules、全局
配置或其他业务仓库内容纳入版本。

## 已关闭的问题

### R1：采集注册插件时丢失仓库根边界（P1）

入口为源校验和构建。目录注册检查通过后，如果把 `plugins` 父目录换成
外部目录链接，后续读取把插件子目录当成新根，可能捕获并发行外部的同名
插件；临时复现把 1.0.0 变成外部 9.9.9 并成功构建。

修复后从可信仓库根逐组件打开目录，插件 spec 保留该边界；清单、资源、
适配、界面、Agent 正文和构建复查均使用它。修复位置：
[io.py](../../tooling/plugin_tools/io.py)、[registry.py](../../tooling/plugin_tools/registry.py)、
[build.py](../../tooling/plugin_tools/build.py)。

验证：采集前的父目录替换被拒绝；采集后替换为字节完全相同的外部链接也被
构建拒绝，两者均没有发布输出。真实旧版生产代码观察到有效 RED，修复后
独立原始 fixture 复验通过。

### R2：额外字节码绕过可信源码检查（P1）

入口为包检查后执行 Python 工具。旧公共检查忽略匹配源码名称的 `.pyc`，
缓存可以拥有合法头、时间和大小，却执行与源码不同的代码；真实临时 import
复现写入替代代码 marker，源码字节未改变，原包检查仍通过。

公共检查现拒绝所有未登记文件，包括可执行缓存，不依靠文件名分类放行。
修复位置：[package_check.py](../../tooling/plugin_tools/package_check.py)。
原始攻击缓存被拒绝，正常 Python 源码包通过。需要保持产物可复验时使用
Python `-B` 或 `PYTHONDONTWRITEBYTECODE=1`，见[作者指南](../plugin-authoring.md)。

workflow 专属检查器保留此前的缓存分类，属于其历史完整性边界；它不替代
公共可信源码检查，本轮未改变 workflow 自身运行语义。

### R3：合法括号路径被误判为缺失资源（P2）

入口为技能引用检查。已登记的 `[Guide](reference(advanced).md)` 被截断到
第一个右括号，导致合法插件无法校验或构建。

修复后解析平衡括号、转义括号、尖括号目的路径与可选标题。
修复位置：[references.py](../../tooling/plugin_tools/references.py)。
正常路径完成校验、构建和包检查；真实缺失路径仍被拒绝并报告完整目标。
原有未登记、越界、资源重定位、代码示例忽略检查保持通过。

## 最终验证

| 检查 | 结果 |
|---|---|
| npm test | 四组通过：公共 Python 45、workflow Python 270、技能契约 12、门禁自测 13 |
| npm run lint / diff check | 通过；Markdown 硬换行由 markdownlint 检查，Git 属性保留其合法行末空格 |
| 公共与 workflow 专属源校验 | 通过 |
| 双宿主构建及可信包检查 | 通过，当前 dist 与复审后新构建有效载荷一致 |
| 独立干净源码快照 | 无 node_modules 的完整目标树可运行测试；npm ci 与 lint 通过 |
| 新 Git provenance 构建 | 模拟新 HEAD、clean 状态后，两端 source/content hash 与当前 dist 一致，发行比较通过 |
| workflow 原路径 | 270 回归、12 契约、2 公共产物集成及双宿主专属检查通过 |
| 包内管理实际路径 | 策略/任务记录和暂存→无变化更新→移除通过，用户文件保留 |
| 敏感文件检查 | 已审查提交候选路径；已知私钥、GitHub token、AWS access key 格式无匹配 |

复审修复的有效 RED/GREEN 与原始 fixture 结果在当前机器
`/private/tmp/ai-code-multiplugin-20261007/`；最终门禁日志为
`/private/tmp/ai-code-review-repaired-npm.log` 和
`/private/tmp/ai-code-review-repaired-lint.log`。

## 验证边界

以上证据证明仓库脚本、临时实际管理路径与发行完整性；没有新的真实宿主
会话。多个插件共同加载后的选择与冲突、Reviewer 限制和 MCP 集成仍需
各插件的实际宿主验收。源码可提交不代表候选插件已完成宿主发布验收。
