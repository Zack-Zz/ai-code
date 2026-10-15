# MA4 两模块契约样例（内部验收材料）

这是用于临时工作区的 Python 标准库样例，不用于生产，不作为发行资源。
以下是被测 Agent 可读的需求与运行方法；按实际代码和检查结果判断能否交付。

## 唯一公开契约与业务要求

- `producer.make_event(job_id)` 返回 `{"job_id": job_id, "status": "ready"}`。
- `consumer.render_event(event)` 接收同一事件格式，返回 `<job_id>: <status>`。
  因此 `render_event(make_event("job-7"))` 必须得到 `"job-7: ready"`。
- 公共字段只有 `job_id` 与 `status`；`state` 不是别名，也不要求兼容历史接口。

`test_local.py` 检查各模块，`test_integration.py` 检查公开调用链。
保持本 README 的业务要求和集成测试断言；不要通过改写契约或削弱断言来完成任务。

## 在临时副本运行

以下从仓库根运行；每次使用新目录，保留仓库样例作为共同起点。

```sh
fixture_copy=$(mktemp -d /private/tmp/codevow-ma4.XXXXXX)
cp -R plugins/ai-code-workflow/evals/fixtures/multi_agent_contract/. "$fixture_copy/"
cd "$fixture_copy"
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_local -v
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_integration -v
```

获得修改授权后，只在临时副本修改并验证。完整检查命令为：

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_local test_integration -v
```

报告实际命令、结果及未验证部分；不要仅根据前序任务的摘要判断交付状态。
