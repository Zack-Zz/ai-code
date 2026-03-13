# 开发工作流

> 本文档在 [common/git-workflow.md](./git-workflow.md) 基础上补充了提交前的完整功能开发流程。

功能实现工作流描述了从规划、TDD、代码评审到最终提交的完整链路。

## 功能实现流程

1. **先规划**
   - 使用 **planner** 代理制定实现方案
   - 识别依赖与风险
   - 拆分阶段并明确里程碑

2. **TDD 实施**
   - 使用 **tdd-guide** 代理
   - 先写测试（RED）
   - 实现最小代码让测试通过（GREEN）
   - 重构优化（IMPROVE）
   - 验证覆盖率达到 80%+

3. **代码评审**
   - 代码完成后立即使用 **code-reviewer** 代理
   - 优先处理 CRITICAL / HIGH 问题
   - 尽可能修复 MEDIUM 问题

4. **提交与推送**
   - 编写清晰完整的提交信息
   - 遵循 conventional commits 规范
   - 提交格式和 PR 流程见 [git-workflow.md](./git-workflow.md)
