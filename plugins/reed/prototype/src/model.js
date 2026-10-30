import { applyConnectorAction, canWriteConnector, mappingIssues, mappedTaskStatus } from './connectors.js';
import { getBoardMove, getStageReview } from './personal-board.js';
import { createDemoConnector, DEMO_CONNECTOR_ID, normalizeState } from './sources.js';

export const STAGES = ['需求', '设计', '开发', '验证'];

const ownsExecution = (task) => ['running', 'waiting', 'unknown'].includes(task.attention);
const requireThat = (condition, reason) => { if (!condition) throw new Error(reason); };
const text = (value, label) => {
  requireThat(typeof value === 'string' && value.trim().length > 0, `请填写${label}`);
  return value.trim();
};
const nextId = (items, prefix) => {
  let number = items.length + 1;
  while (items.some((item) => item.id === `${prefix}-${number}`)) number += 1;
  return `${prefix}-${number}`;
};
const blankTask = (id, title, project = '成员中心') => ({
  id, title, project, source: '本地', origin: { kind: 'local', system: 'reed' }, stage: 0, status: 'active', attention: 'idle', hasStarted: false,
  accepted: [false, false, false, false], sync: 'synced', remoteTitle: null, repo: 'member-service',
  workspace: { ready: false, verified: false, path: '', branch: '', origin: { kind: 'local', system: 'git', repo: 'member-service' } },
  sessionId: null, sessionIds: [], docs: [], notes: [],
});
const documentStage = (kind) => ({ 需求: 0, 设计: 1, 验证: 3 })[kind];
const doc = (id, title, version, kind, body, stage = documentStage(kind)) => ({ id, title, version, kind, body, stage });

export function createInitialState() {
  const primary = {
    ...blankTask('REQ-1042', '成员导入失败后自动补偿'), source: '云效', externalId: 'REQ-1042',
    stage: 1, attention: 'review', accepted: [true, false, false, false],
    sessionId: 'session-design', sessionIds: ['session-requirement', 'session-design'],
    docs: [
      doc('doc-1042-req-1', '需求说明.md', 1, '需求', '# 成员导入失败后自动补偿\n\n导入结果不受异步绑定失败影响；再次导入时补偿缺失的成员来源绑定。\n\n## 验收标准\n- 失败只记录日志，导入继续成功。\n- 未变更的重复导入也能触发补偿。\n- 补偿调用保持幂等。'),
      doc('doc-1042-design-1', '补偿方案.md', 1, '设计', '# 补偿方案 V1\n\n在成员导入完成后异步检查来源绑定，记录失败原因。'),
      doc('doc-1042-design-2', '补偿方案.md', 2, '设计', '# 补偿方案\n\n## 方案概述\n导入成功后异步补齐成员来源绑定，补偿失败保留记录。\n\n## 处理原则\n补偿失败仅记录日志，不影响导入结果。重复导入可再次补偿。\n\n## 验收关注点\n- 旧数据来源绑定可补齐\n- 补偿失败可追溯\n- 重复操作不产生重复绑定'),
    ],
  };
  const waiting = { ...blankTask('REQ-1043', '批量邀请成员支持重复校验'), source: '云效', externalId: 'REQ-1043', attention: 'waiting', sessionId: 'session-wait', sessionIds: ['session-wait'], notes: ['需要确认重复手机号的处理规则。'] };
  const failed = { ...blankTask('REQ-1039', '成员角色变更后刷新权限'), source: '云效', externalId: 'REQ-1039', stage: 3, attention: 'failed', accepted: [true, true, true, false], sessionId: 'session-verify', sessionIds: ['session-verify'], workspace: { ready: true, verified: true, path: '/workspace/reed/req-1039', branch: 'reed/req-1039' }, docs: [doc('doc-1039-verify-1', '验证报告.md', 1, '验证', '# 验证报告\n\n18 项检查通过，1 项失败：角色变更后的旧会话权限缓存未刷新。\n\n需要修复后重新验证。')] };
  failed.docs[0].outcome = 'failed';
  const running = { ...blankTask('REQ-1040', '机构列表新增状态筛选'), source: '云效', externalId: 'REQ-1040', stage: 2, attention: 'running', accepted: [true, true, false, false], sessionId: 'session-develop', sessionIds: ['session-develop'], workspace: { ready: true, verified: true, path: '/workspace/reed/req-1040', branch: 'reed/req-1040' } };
  const idle = blankTask('LOCAL-1', '整理成员导入常见问题');
  const design = { ...blankTask('REQ-1045', '邀请链接支持有效期配置'), source: '云效', externalId: 'REQ-1045', stage: 1, accepted: [true, false, false, false], sync: 'pending', docs: [doc('doc-1045-req-1', '需求说明.md', 1, '需求', '# 邀请链接有效期\n\n支持管理员配置邀请链接有效期，默认七天。')] };
  return normalizeState({
    connectors: [createDemoConnector()],
    tasks: [primary, waiting, failed, running, idle, design].map((task) => ({
      ...task,
      origin: task.source === '云效' ? { kind: 'connector', connectorId: DEMO_CONNECTOR_ID, externalId: task.externalId } : task.origin,
      docs: task.docs.map((document) => ({ ...document, origin: document.kind === '需求' ? { kind: 'connector', connectorId: DEMO_CONNECTOR_ID, externalId: task.externalId } : { kind: 'host', host: 'Codex' } })),
      // These demo samples already have an active execution or accepted work.
      hasStarted: task.stage > 0 || task.attention === 'waiting',
      remoteTitle: task.source === '云效' ? task.title : null,
      sourceWorkItemType: task.source === '云效' ? 'requirement' : undefined,
    })),
    sessions: [
      { id: 'session-requirement', title: '成员导入 · 需求梳理', host: 'Codex', taskId: primary.id, stage: 0, status: 'ended', branch: '', verified: true },
      { id: 'session-design', title: '成员导入 · 补偿设计', host: 'Codex', taskId: primary.id, stage: 1, status: 'ended', branch: '', verified: true },
      { id: 'session-wait', title: '邀请成员 · 规则确认', host: 'Claude Code', taskId: waiting.id, stage: 0, status: 'waiting', branch: '', verified: true },
      { id: 'session-verify', title: '权限刷新 · 验证', host: 'Codex', taskId: failed.id, stage: 3, status: 'ended', branch: failed.workspace.branch, verified: true },
      { id: 'session-develop', title: '机构筛选 · 开发', host: 'Codex', taskId: running.id, stage: 2, status: 'running', branch: running.workspace.branch, verified: true },
    ],
    branches: [
      { id: 'branch-1039', repo: failed.repo, name: failed.workspace.branch, path: failed.workspace.path, taskId: failed.id, sessionId: failed.sessionId, status: 'ready', pr: null },
      { id: 'branch-1040', repo: running.repo, name: running.workspace.branch, path: running.workspace.path, taskId: running.id, sessionId: running.sessionId, status: 'busy', pr: null },
    ],
    events: [
      { id: 'event-1', taskId: primary.id, text: '需求阶段已人工验收通过', time: '09:20', origin: { kind: 'local', system: 'reed' } },
      { id: 'event-2', taskId: primary.id, text: 'Codex 已结束设计会话，补偿方案 V2 等待验收', time: '10:42', origin: { kind: 'local', system: 'reed' } },
      { id: 'event-3', taskId: failed.id, text: '验证失败：旧会话权限缓存未刷新', time: '10:48', origin: { kind: 'local', system: 'reed' } },
      { id: 'event-4', taskId: running.id, text: '已核验隔离工作区，开始开发', time: '10:55', origin: { kind: 'local', system: 'reed' } },
    ],
  });
}

function assertActive(task) {
  requireThat(task.status === 'active', task.status === 'paused' ? '任务已暂停，请先恢复任务' : '任务已完成或归档，不能执行此操作');
}
function assertKnownIdle(task) {
  requireThat(task.attention !== 'unknown', '执行状态未知，请先人工核实会话归属');
  requireThat(!ownsExecution(task), '当前仍有执行中的会话，请先确认停止');
}
function assertPrerequisites(task) {
  requireThat(task.accepted.slice(0, task.stage).every(Boolean), '前序阶段尚未验收通过');
}
function executionContext(state, task) {
  assertPrerequisites(task);
  const session = state.sessions.find((item) => item.id === task.sessionId);
  requireThat(session && session.taskId === task.id && session.stage === task.stage && session.verified, '请绑定并核验当前阶段的 Agent 会话');
  requireThat(!state.tasks.some((other) => other.id !== task.id && other.sessionId === session.id && ownsExecution(other)), '该会话正被另一任务占用');
  if (task.stage >= 2) {
    requireThat(task.workspace.ready, '请先准备隔离工作区');
    const branch = state.branches.find((item) => item.taskId === task.id && item.name === task.workspace.branch && item.path === task.workspace.path);
    requireThat(task.workspace.verified && task.workspace.path && branch && branch.sessionId === session.id && session.branch === branch.name, '工作区目录、分支与会话尚未核验一致');
  }
  return session;
}
function setBranchStatus(state, task, status) {
  state.branches.filter((branch) => branch.taskId === task.id).forEach((branch) => { branch.status = status; });
}
function markStageSyncPending(task) {
  if (task.source === '云效' && !['conflict', 'unknown'].includes(task.sync)) task.sync = 'pending';
}
function availableResultTitle(task, preferred) {
  const occupied = (title) => task.docs.some((item) => item.title === title && (item.stage ?? documentStage(item.kind)) !== task.stage);
  if (!occupied(preferred)) return preferred;
  const dot = preferred.lastIndexOf('.');
  const stem = dot > 0 ? preferred.slice(0, dot) : preferred;
  const extension = dot > 0 ? preferred.slice(dot) : '';
  let suffix = 1;
  let candidate;
  do {
    candidate = `${stem}（${STAGES[task.stage]}阶段${suffix === 1 ? '' : ` ${suffix}`}）${extension}`;
    suffix += 1;
  } while (occupied(candidate));
  return candidate;
}
function appendResult(task, outcome, host) {
  const kind = task.stage === 0 ? '需求' : task.stage === 3 ? '验证' : '设计';
  const designTitle = task.docs.find((item) => item.kind === '设计' && (item.stage ?? 1) === 1)?.title || '设计方案.md';
  const title = availableResultTitle(task, ['需求说明.md', designTitle, '开发记录.md', '验证报告.md'][task.stage]);
  const version = Math.max(0, ...task.docs.filter((item) => item.title === title && (item.stage ?? documentStage(item.kind)) === task.stage).map((item) => item.version)) + 1;
  const summary = { review: '模拟 Agent 已完成本阶段产出，等待人工审阅与验收。', failed: '模拟检查未通过，请查看失败原因并在确认后重试。', waiting: '模拟 Agent 等待补充信息。', unknown: '模拟执行状态未知，需人工核实会话和产出。' }[outcome];
  task.docs.push(doc(`${task.id}-stage-${task.stage}-v${version}`, title, version, kind, `# ${STAGES[task.stage]}阶段产出 V${version}\n\n任务：${task.title}\n\n${summary}\n\n${task.notes.length ? `## 补充反馈\n${task.notes.map((note) => `- ${note}`).join('\n')}` : '## 检查要点\n- 覆盖当前阶段目标与边界。\n- 确认遗留问题与下一步。'}\n\n> 本内容由本地演示生成，未经真实 Agent 执行。`, task.stage));
  task.docs.at(-1).outcome = outcome;
  task.docs.at(-1).origin = { kind: 'host', host };
}

function assertDocumentSnapshot(task, document, action, required = false) {
  if (!required && !['expectedStage', 'documentId', 'documentVersion'].some((key) => action[key] !== undefined)) return;
  requireThat(action.expectedStage === task.stage, '阶段确认快照已失效，请重新检查当前阶段');
  requireThat(document && action.documentId === document.id && action.documentVersion === document.version, '文档确认快照已失效，请重新审阅当前文档版本');
}

function availableConnector(state, id, write = false, project = null, workItemType = null) {
  requireThat(typeof id === 'string' && id.trim(), '请显式选择 Connector 连接');
  const connector = state.connectors.find((item) => item.id === id);
  requireThat(connector, '找不到指定 Connector 连接');
  requireThat(!connector.legacy && connector.enabled && connector.status === 'connected', '连接未配置、已停用或未连接，请先检查模拟连接');
  if (project) {
    requireThat(connector.projects.includes(project), '任务项目已移出此连接的同步范围，保留来源与本地工作');
    requireThat(workItemType === connector.workItemType, '工作项类型未记录或已移出同步范围，保留来源与本地工作');
  }
  if (write) {
    requireThat(connector.syncMode === 'bidirectional', '只读连接不能推送，请使用双向同步连接');
    requireThat(mappingIssues(connector).length === 0, '状态映射尚未完成或失效，请先配置映射');
    requireThat(canWriteConnector(connector), '写入权限未通过检测，请先重新检测连接');
  }
  return connector;
}
export function reduce(state, action) {
  requireThat(action && typeof action.type === 'string', '缺少有效操作');
  const next = normalizeState(state);
  const emit = (taskId, message, details = {}) => next.events.push({ id: nextId(next.events, 'event'), taskId, text: message, time: '刚刚', origin: { kind: 'local', system: 'reed' }, ...details });
  if (applyConnectorAction(next, action)) return next;
  if (['CREATE_TASK', 'IMPORT_TASK'].includes(action.type)) {
    const externalId = action.type === 'IMPORT_TASK' ? text(action.externalId, '云效工作项编号') : null;
    const connector = externalId ? availableConnector(next, action.connectorId) : null;
    const project = action.project?.trim() || connector?.projects[0] || '成员中心';
    if (connector) requireThat(connector.projects.includes(project), '所选项目不在该连接的配置中');
    if (externalId && next.tasks.some((task) => task.origin?.kind === 'connector' && task.origin.connectorId === connector.id && task.origin.externalId === externalId && task.project === project)) return next;
    const title = text(action.title, '任务标题');
    const task = blankTask(nextId(next.tasks, externalId ? 'IMPORTED' : 'LOCAL'), title, project);
    if (externalId) Object.assign(task, { source: '云效', externalId, sourceWorkItemType: connector.workItemType, remoteTitle: title, origin: { kind: 'connector', connectorId: connector.id, externalId } });
    next.tasks.push(task);
    emit(task.id, externalId ? `已导入云效工作项 ${externalId}` : '已创建本地任务');
    return next;
  }
  const task = next.tasks.find((item) => item.id === action.taskId);
  requireThat(task, '找不到指定任务');
  // Preserve reliable progress from old caches before stop/rework clears it.
  // An ended session alone may be an unused binding and is not evidence.
  if (['running', 'waiting', 'review', 'failed', 'unknown'].includes(task.attention)
    || task.stage > 0 || task.accepted?.some((accepted) => accepted === true)) {
    task.hasStarted = true;
  }
  // Preserve known failure identity before retry or same-stage rework clears
  // attention. An explicit manual revision already has its own outcome.
  if (task.attention === 'failed') {
    const latest = task.docs.filter((item) => (item.stage ?? documentStage(item.kind)) === task.stage).at(-1);
    if (latest && latest.outcome === undefined) latest.outcome = 'failed';
  }
  const session = () => next.sessions.find((item) => item.id === task.sessionId);
  const acceptStage = () => {
    assertActive(task);
    assertPrerequisites(task);
    const gate = getStageReview(next, task);
    assertDocumentSnapshot(task, gate.document, action);
    requireThat(task.attention === 'review', '当前阶段尚未进入待验收状态');
    requireThat(gate.checks.every((item) => item.passed), gate.checks.filter((item) => !item.passed).map((item) => item.label).join('；'));
    task.accepted[task.stage] = true;
    emit(task.id, `${STAGES[task.stage]}阶段已人工验收通过`, { stage: task.stage, documentId: gate.document.id, documentVersion: gate.document.version });
    if (task.stage === 3) task.status = 'completed';
    else { task.stage += 1; task.sessionId = null; }
    task.attention = 'idle';
    markStageSyncPending(task);
  };
  switch (action.type) {
    case 'SAVE_DOCUMENT': {
      assertActive(task);
      assertKnownIdle(task);
      requireThat(!task.accepted[task.stage], '当前阶段已经验收，请先返工后修改文档');
      requireThat(['需求', '设计', '验证'].includes(action.kind), '不支持的文档类型');
      const expectedKind = ['需求', '设计', '设计', '验证'][task.stage];
      requireThat(action.kind === expectedKind, '只能保存当前阶段文档，请先返工到对应阶段');
      const title = text(action.title, '文档标题');
      text(action.body, '文档正文');
      const history = task.docs.filter((item) => item.title === title);
      requireThat(history.every((item) => (item.stage ?? documentStage(item.kind)) === task.stage), '该文档属于其他阶段，请先返工到对应阶段再修改');
      const version = Math.max(0, ...history.map((item) => item.version)) + 1;
      task.docs.push(doc(`${task.id}-document-${task.docs.length + 1}`, title, version, action.kind, action.body, task.stage));
      task.docs.at(-1).outcome = 'manual';
      task.docs.at(-1).origin = { kind: 'local', system: 'reed', actor: 'manual' };
      emit(task.id, `已保存本地文档 ${title} V${version}，保留历史版本`);
      break;
    }
    case 'LINK_SESSION': {
      const linked = next.sessions.find((item) => item.id === action.sessionId);
      requireThat(linked, '找不到需要关联的历史会话');
      if (task.sessionIds.includes(linked.id)) return next;
      task.sessionIds.push(linked.id);
      emit(task.id, `已关联历史会话「${linked.title}」，执行归属保持不变`);
      break;
    }
    case 'ACCEPT_STAGE': {
      acceptStage();
      break;
    }
    case 'MOVE_BOARD': {
      const plan = getBoardMove(next, task.id, action.target);
      requireThat(plan.allowed, plan.reason);
      requireThat(['submit_review', 'complete'].includes(plan.kind), '此迁移须通过现有准备、反馈或返工操作；同列或重复提交不能直接执行');
      assertDocumentSnapshot(task, plan.document, action, true);
      if (plan.kind === 'complete') acceptStage();
      else {
        task.attention = 'review';
        task.hasStarted = true;
        emit(task.id, `${STAGES[task.stage]}阶段产出已明确提交人工评审`, { stage: task.stage, documentId: plan.document.id, documentVersion: plan.document.version });
      }
      break;
    }
    case 'REOPEN_STAGE': {
      assertKnownIdle(task);
      requireThat(Number.isInteger(action.stage) && action.stage >= 0 && action.stage <= task.stage, '返工阶段必须是当前或更早阶段');
      const reason = text(action.reason, '返工理由');
      task.docs.filter((item) => (item.stage ?? documentStage(item.kind)) >= action.stage).forEach((item) => { item.stale = true; });
      task.accepted = task.accepted.map((accepted, index) => index < action.stage ? accepted : false);
      task.stage = action.stage;
      task.status = 'active';
      task.attention = 'idle';
      task.sessionId = null;
      task.workspace.verified = false;
      setBranchStatus(next, task, 'ready');
      next.branches.filter((branch) => branch.taskId === task.id).forEach((branch) => { delete branch.sessionId; });
      markStageSyncPending(task);
      task.notes.push(`返工${STAGES[task.stage]}：${reason}`);
      emit(task.id, `已明确返工${STAGES[task.stage]}阶段：${reason}；保留历史产出，等待重新接入会话`);
      break;
    }
    case 'RECONCILE_STAGE': {
      requireThat(task.attention === 'unknown', '只有执行状态未知的阶段需要人工核查');
      requireThat(['review', 'failed', 'running'].includes(action.outcome), '不支持的人工核查结果');
      const current = executionContext(next, task);
      requireThat(current.status === 'unknown', '当前会话状态与未知执行不一致，请重新核查');
      task.attention = action.outcome;
      const isRunning = action.outcome === 'running';
      current.status = isRunning ? 'running' : 'ended';
      setBranchStatus(next, task, isRunning ? 'busy' : 'ready');
      if (!isRunning) appendResult(task, action.outcome, current.host);
      const result = { review: '确认会话已结束，产出等待人工验收', failed: '确认执行失败，可检查后重试', running: '确认仍在执行，保留会话占用' }[action.outcome];
      emit(task.id, `模拟人工核查：${result}`);
      break;
    }
    case 'PREPARE_WORKSPACE': {
      assertActive(task);
      assertKnownIdle(task);
      if (task.workspace.ready) return next;
      const slug = task.id.toLowerCase().replace(/[^a-z0-9-]/g, '-');
      task.workspace = { ready: true, verified: false, path: `/workspace/reed/${slug}`, branch: `reed/${slug}`, origin: { kind: 'local', system: 'git', repo: task.repo } };
      next.branches.push({ id: nextId(next.branches, 'branch'), repo: task.repo, name: task.workspace.branch, path: task.workspace.path, taskId: task.id, status: 'ready', pr: null, origin: { kind: 'local', system: 'git', repo: task.repo } });
      emit(task.id, '已准备模拟隔离工作区，等待绑定会话核验目录');
      break;
    }
    case 'BIND_SESSION': {
      assertActive(task);
      assertKnownIdle(task);
      const host = text(action.host, 'Agent 宿主');
      const branch = next.branches.find((item) => item.taskId === task.id && item.path === task.workspace.path && item.name === task.workspace.branch);
      if (task.stage >= 2) requireThat(task.workspace.ready && branch, '请先准备隔离工作区');
      const current = session();
      if (current && current.status === 'idle') current.status = 'ended';
      const newSession = { id: nextId(next.sessions, 'session'), title: `${task.title} · ${STAGES[task.stage]}`, host, taskId: task.id, stage: task.stage, origin: { kind: 'host', host }, status: 'idle', branch: task.workspace.branch, verified: true };
      next.sessions.push(newSession);
      task.sessionId = newSession.id;
      task.sessionIds.push(newSession.id);
      if (branch) { branch.sessionId = newSession.id; task.workspace.verified = true; }
      emit(task.id, `已绑定 ${host} 模拟会话${branch ? '，目录与分支已核验' : ''}`);
      break;
    }
    case 'START_STAGE': {
      assertActive(task);
      requireThat(task.attention !== 'unknown', '执行状态未知，请先人工核实');
      requireThat(task.attention !== 'running', '当前阶段正在运行，不能重复启动');
      requireThat(task.attention === 'idle', '请先处理当前阶段的等待、失败或验收事项');
      const boundSession = executionContext(next, task);
      requireThat(['idle', 'ended'].includes(boundSession.status), '会话仍在运行或状态未知，不能启动');
      boundSession.status = 'running';
      task.attention = 'running';
      task.hasStarted = true;
      setBranchStatus(next, task, 'busy');
      emit(task.id, `开始${STAGES[task.stage]}阶段模拟执行`);
      break;
    }
    case 'FINISH_STAGE': {
      requireThat(['running', 'waiting'].includes(task.attention), '当前没有运行或等待中的阶段');
      requireThat(['review', 'failed', 'waiting', 'unknown'].includes(action.outcome), '不支持的执行结果');
      requireThat(session(), '执行会话不存在');
      task.attention = action.outcome;
      session().status = ['review', 'failed'].includes(action.outcome) ? 'ended' : action.outcome;
      setBranchStatus(next, task, ['review', 'failed'].includes(action.outcome) ? 'ready' : 'busy');
      appendResult(task, action.outcome, session().host);
      emit(task.id, { review: 'Agent 已结束，阶段产出等待人工验收', failed: '阶段执行失败，等待检查后重试', waiting: 'Agent 等待补充信息', unknown: '执行状态未知，保留会话归属待人工核实' }[action.outcome]);
      break;
    }
    case 'REQUEST_CHANGES':
      assertActive(task);
      requireThat(task.attention === 'review', '只有待验收阶段可以提出修改');
      task.notes.push(text(action.feedback, '修改反馈'));
      task.docs.filter((item) => (item.stage ?? documentStage(item.kind)) === task.stage).forEach((item) => { item.stale = true; });
      task.attention = 'idle';
      emit(task.id, '已记录修改反馈，保留现有产出与验收历史');
      break;
    case 'RESUME_STAGE': {
      assertActive(task);
      requireThat(task.attention === 'waiting', '只有等待中的阶段可以继续');
      const reply = text(action.reply, '等待事项答复');
      requireThat(executionContext(next, task).status === 'waiting', '会话不在等待状态，请先核实');
      session().status = 'running';
      task.attention = 'running';
      task.notes.push(reply);
      emit(task.id, `已补充答复，继续模拟执行：${reply}`);
      break;
    }
    case 'RETRY_STAGE': {
      assertActive(task);
      requireThat(task.attention !== 'unknown', '执行状态未知，不能盲目重试');
      requireThat(task.attention === 'failed', '只有已知失败的阶段可以重试');
      task.attention = 'idle';
      emit(task.id, '已确认失败，阶段可重新启动');
      break;
    }
    case 'STOP_STAGE':
      requireThat(task.attention !== 'unknown', '执行状态未知，不能盲目停止');
      requireThat(['running', 'waiting'].includes(task.attention), '当前没有执行中的阶段');
      requireThat(session(), '执行会话不存在');
      session().status = 'ended';
      task.attention = 'idle';
      setBranchStatus(next, task, 'ready');
      emit(task.id, '已确认停止模拟执行，会话已结束');
      break;
    case 'TOGGLE_PAUSE':
      requireThat(['active', 'paused'].includes(task.status), '已完成或归档的任务不能暂停');
      task.status = task.status === 'active' ? 'paused' : 'active';
      emit(task.id, task.status === 'paused' ? '任务已暂停；正在执行的会话保持原状态' : '任务已恢复');
      break;
    case 'ARCHIVE_TASK':
      if (task.status === 'archived') return next;
      assertKnownIdle(task);
      task.archivedFrom = task.status;
      task.status = 'archived';
      emit(task.id, '任务已归档');
      break;
    case 'RESTORE_TASK': {
      requireThat(task.status === 'archived', '只有已归档任务可以恢复');
      if (task.archivedFrom === undefined) {
        requireThat(['active', 'paused', 'completed'].includes(action.restoreStatus), '缺少归档前状态，请显式指定旧任务恢复状态');
        const reason = text(action.reason, '旧任务恢复理由');
        requireThat(action.restoreStatus !== 'completed' || (task.accepted.length === 4 && task.accepted.every((accepted) => accepted === true)), '全部阶段验收通过后才能人工指定为已完成');
        task.status = action.restoreStatus;
        emit(task.id, `人工指定旧任务恢复状态：${{ active: '进行中', paused: '暂停', completed: '已完成' }[task.status]}；理由：${reason}`);
        break;
      }
      requireThat(['active', 'paused', 'completed'].includes(task.archivedFrom), '缺少有效的归档前状态，请先核查任务历史');
      requireThat(action.restoreStatus === undefined, '已有归档前状态，不能人工指定覆盖');
      task.status = task.archivedFrom;
      emit(task.id, `任务已恢复为${{ active: '进行中', paused: '暂停', completed: '已完成' }[task.status]}，阶段与历史产出保持不变`);
      break;
    }
    case 'SET_SYNC':
      requireThat(['synced', 'pending', 'conflict', 'unknown'].includes(action.value), '无效的同步状态');
      if (action.value === 'synced' && task.origin?.kind === 'connector') {
        const connector = availableConnector(next, task.origin.connectorId, true, task.project, task.sourceWorkItemType);
        task.remoteStatus = mappedTaskStatus(connector, task, next.sessions);
      }
      task.sync = action.value;
      if (action.value === 'conflict') task.remoteTitle = `${(task.remoteTitle || task.title).replace(/（范围已调整）$/, '')}（范围已调整）`;
      if (action.value === 'synced') task.remoteTitle = task.title;
      emit(task.id, `模拟同步状态：${{ synced: '已同步', pending: '待同步', conflict: '存在冲突', unknown: '未知' }[action.value]}`);
      break;
    case 'RESOLVE_SYNC':
      requireThat(['local', 'remote', 'pause'].includes(action.choice), '无效的冲突处理操作');
      if (action.choice === 'pause') { emit(task.id, '已暂缓同步，保留当前字段与同步状态'); break; }
      requireThat(task.sync !== 'unknown', '同步结果未知，不能自动选择字段，请先核实');
      requireThat(task.sync === 'conflict', '当前没有需要处理的同步冲突');
      if (task.origin?.kind === 'connector') availableConnector(next, task.origin.connectorId, action.choice === 'local', task.project, task.sourceWorkItemType);
      if (action.choice === 'remote') task.title = text(task.remoteTitle, '模拟远端标题');
      task.sync = action.choice === 'local' ? 'pending' : 'synced';
      emit(task.id, action.choice === 'local' ? '已选择本地字段，等待模拟推送' : '已选择云效字段，模拟同步完成');
      break;
    case 'UPDATE_TASK':
      task.title = text(action.title, '任务标题');
      markStageSyncPending(task);
      emit(task.id, '已保存本地任务标题');
      break;
    default:
      throw new Error('不支持的操作');
  }
  return next;
}
