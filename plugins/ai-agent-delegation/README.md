# Agent Delegation 源码

独立插件 `ai-agent-delegation` 的首版候选，版本与资源闭包只由 product.json
维护。提供明确派发单技能、三宿主适配和外置 Bridge 薄客户端。插件不复制
运行时、驱动、任务状态或 CodeVow 流程。

产品说明见 [中文发行 README](release/README_CN.md)、
[支持矩阵](docs/support-matrix.md)和[宿主验收方案](docs/host-evaluation.md)。
release README 的相对链接以发行包根目录为基准。宿主支持当前均 unverified。

在仓库根运行插件本地测试：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 plugins/ai-agent-delegation/tests/run_python_tests.py
```

根 catalog 登记后，公共入口 validate/build/package check、npm test 由公共层
统一处理。此插件无独立 build/runtime/安装器。发布 acceptance 当前全部
为 null，待真实源/包绑定验收；测试通过不自动授权 Git、安装或发布。

当前功能源码已覆盖明确派发、同工具独立会话、交接、回执和结果回收。
ZCode 的公开 CLI 适配由 Bridge 提供；当前 standalone 与桌面账户入口
差异属于原生能力限制，不在本插件内复制认证、伪造授权或切换模型。
