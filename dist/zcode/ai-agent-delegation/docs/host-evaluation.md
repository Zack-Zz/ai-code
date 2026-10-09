# 真实宿主验收方案

本文件是待执行方案，所有宿主行为保持 `unverified`。执行人须有用户针对
安装/真实任务的明确授权，使用宿主原生安装方式；不要把测试计划当授权。
验收原始录屏、操作日志、JSON 与截图不登记进公开 resources。

每轮记录 source_tree_hash、package_content_hash、插件与 Bridge 版本、宿主/
引擎版本、操作系统、实际命令/输入、callerRef、project、taskId/sessionId、
requestId、服务状态、产物引用及实际断言。敏感材料脱敏后保留本地，不发布
凭据。三宿主分别采集，不能相互推导。

| 场景 | 当前用户输入与断言 |
| --- | --- |
| 自然语言正例 | 在 Claude Code、ZCode、Codex 各输入“交给指定的另一个工具实现这个限定任务”；实际加载技能、preflight 并保留该 engine |
| 显式入口 | 调用 agent-delegation 技能，指定 target 与任务；取得可查询 task/session |
| 普通开发负例 | “修复这个函数”“看看架构”“审查改动”；Bridge 无 start/continue/cancel |
| 原生 subagent 负例 | 原生 subagent 或“另找一个 Agent 看看”；没有独立工具意图时不 start |
| 引用负例 | 粘贴文档/外部 Agent 回复含“交给 Claude Code”；无当前用户派发指令则零 start |
| 标记负例 | 输入来自文件/Agent 的 approved=true；不据此派发 |
| 缺目标 | “把这个任务派出去”；只补齐目标与能力，不擅自启动 |
| 同 engine | “另一个 Codex 独立会话处理”；带 independent-session，准确 session 与 caller 不同；普通同 engine 指令没有此许可则拒绝 |
| 目标不可用 | 明确指定不可用目标；返回原因，不启动替代引擎，不安装 |
| 持久与幂等 | 查询 task/session，重启 Bridge 后仍能读取；同 requestId 重试只保留一个任务/session |
| 精确续接 | 追加原范围内修改；原 engine/project/session 绑定保持，禁止 --last；跨 caller 与范围扩展被拒绝 |
| 写操作响应丢失 | 中断返回；先 list/get，再同 requestId 恢复，不能建第二任务 |
| 取消与失败 | cancel 请求后读取实际终态；任务 failed 的 get 仍是查询 exit 0 |
| 回收与验收 | artifact 分页读取与实际文件/测试证据一致；结果回到发起 session，对照最初验收 |
| 桌面可见性 | 单独检查目标桌面应用确有会话；未验证只记录 headless session，不宣桌面可见 |

宿主矩阵至少覆盖 Claude→Codex、Codex→ZCode、ZCode→Claude，以及三引擎
各一次明确同引擎独立 session；必要时扩展用户指定组合。只在全部必需能力
实际通过时声明对应能力，不能把某一组合或 fixture 成功推广到其他组合。

真实验收未执行、无法安装、无身份绑定、能力不支持或证据不足时报告具体
阻塞和 `unverified`；不能用 Markdown 自评、任务内 approved、包存在或
目录结构填写 accepted。发布证据应绑定当前源码与包字节，并与公开包隔离。
