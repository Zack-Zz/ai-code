# GitHub 插件市场实施计划

日期：2026-10-08。依据：已获用户同意的 GitHub 市场与制品分发设计。

目标：生成独立安装包，提供可审阅且受哈希约束的市场部署，准备 CodeVow
首个 GitHub 试用发行；保留现有市场直到新运输协议完成真实宿主验收。
技术栈：Python 标准库、unittest、现有 Node 测试汇总、GitHub Actions。
本计划不授权 Git commit/push/tag；这些动作在具体结果准备完成后单独确认。

## 任务与所有权

- [ ] 安装包与复验：安装制品工作者负责 `release/layout.py`、
  `release/integrity.py`、`release/core.py`、`create_release_draft.py` 和相关
  制品测试。先增加 installer 根闭包和 tamper 失败测试，再实现 schema 2，
  兼容 schema 1 历史验证。不得改 CLI、distribution 或 workflow。
- [ ] 市场生成：市场目录工作者负责 `distribution.py`、根
  `distribution.json`、`tests/tooling/test_distribution.py`。
  先用实际 bundle 测试 preview 来源、stable 门禁、其他插件保留、固定
  URL/SHA、计划过期与 ID/版本冲突，再实现纯本地生成。不得修改 release
  模块、CLI、GitHub 脚本和 workflow。
- [ ] 部署：主会话负责 `.github/scripts/deploy_marketplace.py`、部署测试。
  用本地 Git 仓库及受控 API fixture 先验证 plan 不写、lease/哈希拒绝、
  D/C 两阶段、bootstrap、重试和远端读回，再实现网络与 Git 管理入口。
- [ ] 集成：主会话更新 CLI、Actions、操作文档、CodeVow 版本说明和旧
  dist；不纳入其他未提交文档。新增 workflow 只手动触发，plan 默认。
- [ ] 验证：定向 unittest → `npm test` → validate/lint → 可信制品与 ZIP
  复验 → 同来源重复构建 → 自审及独立审阅。
- [ ] 发布交付：查询远端标签与 Release，准备具体 commit/tag/附件清单，
  确认明确 Git 授权后执行；新版本保持 preview/unverified，报告 Release、
  市场部署、宿主验收分别达到的状态。

## 公共接口

制品模块继续导出 `check_release/prepare_release/verify_release`。
schema 2 的安装包路径为 `installers/ID-VERSION-HOST-plugin.zip`。
`layout.payload` 与 `layout.record` 支持显式 schema 版本，使旧 schema 1
能按其历史路径闭包重建；本轮新 prepare 默认 schema 2。

纯目录模块提供：

```python
load_config(root)
plan_distribution(root, spec, bundle, release_info, channel,
                  market_files=None, base_commit="absent")
stage_files(plan)
finalize_files(plan, codex_revision=None)
check_plan(plan, expected_hash=None, expected_commit=None)
```

`market_files` 为相对路径到 bytes 的完整既有发行树；必须检查全部旧受管
文件与记录，不执行其中任何脚本。计划为可 JSON 序列化的数据，包含所有
需要生成的安装文件数据和其哈希，采用明确编码，排除原始证据。计划
哈希排除自身字段，不含当前时间。`stage_files` 返回 D 阶段新增文件；
`finalize_files` 返回包含原有文件的完整最终发行树；Codex pin 实际 D，
没有 Codex 时使用 null。部署脚本以可信 bundle 重新生成计划再写入，
不能仅凭传入计划的自报哈希建立信任。

`release_info` 来自 GitHub 读取并实际下载验证后的固定结构，包含
`id/tag_name/draft/prerelease/html_url/assets`；资产含
`id/name/size/browser_download_url/sha256`。须匹配规范 tag、GitHub 仓库和
expected installer；transport URL 不接受调用者任意地址。

## 检查命令

每个工作者记录实际有效 RED 和 GREEN 命令及结果。主会话运行：

```sh
python3 tests/run_python_tests.py
npm test
python3 tooling/plugin_tool.py validate --all
npm run lint
```

包和 release 检查使用可信仓库工具，输出到仓库外的空目录。远端设置、
Release 和分支操作遵守已审阅设计；未取得账号权限或宿主安装授权的检查
如实报告，不能用模拟结果替代实际状态。
