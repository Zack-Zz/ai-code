export const BOARD_COLUMNS = [
  { id: 'todo', label: '待办' },
  { id: 'in_progress', label: '进行中' },
  { id: 'review', label: '评审中' },
  { id: 'done', label: '完成' },
];

export function getBoardColumn(task, sessions = []) {
  if (task.status === 'archived') return null;
  if (task.status === 'completed') return 'done';
  if (task.attention === 'review') return 'review';
  if (['running', 'waiting', 'failed', 'unknown'].includes(task.attention)) return 'in_progress';
  if (task.hasStarted === true || task.stage > 0 || task.accepted?.some((accepted) => accepted === true)) return 'in_progress';

  // Rebinding can end an idle session without executing it. Legacy ended
  // sessions prove progress only when they explicitly record started=true.
  const hasExecution = sessions.some((session) => session.taskId === task.id && (
    ['running', 'waiting', 'unknown'].includes(session.status)
    || (session.status === 'ended' && session.started === true)
  ));
  if (hasExecution) return 'in_progress';
  return 'todo';
}

const phaseOf = (document) => document.stage ?? ({ 需求: 0, 设计: 1, 验证: 3 })[document.kind];
const present = (value) => typeof value === 'string' && value.trim().length > 0;
const check = (id, label, passed) => ({ id, label, passed: Boolean(passed) });

// Shared by drag planning and ordinary acceptance. The newest current-phase
// version must stand on its own; an older successful report cannot hide a
// newer failure or empty result. Legacy reports have no outcome metadata.
export function getStageReview(state, task) {
  const document = (task.docs || []).filter((item) => phaseOf(item) === task.stage).at(-1);
  const owned = (state.sessions || []).filter((item) => item.taskId === task.id);
  const current = (state.sessions || []).find((item) => item.id === task.sessionId);
  const unconfirmedLegacy = document && document.outcome === undefined && task.attention === 'idle';
  const checks = [
    check('active', '任务须处于可操作状态，请先恢复暂停或归档任务', task.status === 'active'),
    check('stage', '须为有效且尚未验收的当前阶段', Number.isInteger(task.stage) && task.stage >= 0 && task.stage <= 3 && task.accepted?.[task.stage] === false),
    check('prerequisites', '前序阶段须全部验收通过', task.accepted?.length === 4 && task.accepted.slice(0, task.stage).every((accepted) => accepted === true)),
    check('attention', '失败、运行、等待或未知执行须先处理，不能直接提交验收', ['idle', 'review'].includes(task.attention)),
    check('execution', '本任务执行须已确知结束，运行、等待或未知会话须先核查', !owned.some((item) => !['idle', 'ended'].includes(item.status))
      && (!task.sessionId || (current?.taskId === task.id && ['idle', 'ended'].includes(current.status)))),
    check('document', '当前阶段须有非空有效产出及准确的文档版本', document && present(document.id) && present(document.title) && present(document.body)
      && Number.isInteger(document.version) && document.version > 0 && document.kind === ['需求', '设计', '设计', '验证'][task.stage]),
    check('freshness', document ? '当前产出已因返工或修改反馈过期，请生成或保存新版本后再评审' : '当前阶段须有本轮范围内的产出', document && document.stale !== true),
    check('outcome', unconfirmedLegacy ? '旧版材料尚未确认本轮有效，请重新执行或保存新版本' : document ? '失败、等待或未知结果不能作为成功产出，请重新执行或人工保存新版本' : '当前阶段须有可审阅的产出', document && (
      ['review', 'manual'].includes(document.outcome)
      || (document.outcome === undefined && task.attention === 'review')
    )),
  ];
  return {
    checks,
    ...(document ? { document: { id: document.id, title: document.title, version: document.version } } : {}),
  };
}

export function getBoardMove(state, taskId, target) {
  const task = state.tasks.find((item) => item.id === taskId);
  const blocked = (checks, details = {}) => ({ kind: 'blocked', allowed: false, title: '暂时不能移动', reason: checks.filter((item) => !item.passed).map((item) => item.label).join('；'), checks, ...details });
  if (!task) return blocked([check('task', '找不到指定任务', false)]);
  if (!BOARD_COLUMNS.some((column) => column.id === target)) return blocked([check('target', '无效的看板列', false)]);
  const source = getBoardColumn(task, state.sessions);
  const planned = (kind, title, reason, details = {}) => ({ kind, allowed: true, title, reason, checks: [], stage: task.stage, ...details });
  if (source === target) return planned('noop', '位置未变', '任务已经位于此列');
  if (['paused', 'archived'].includes(task.status)) return blocked([check('active', '任务已暂停或归档，请先恢复任务', false)]);
  if (target === 'todo') return blocked([check('history', '已经开工的任务不能退回待办并清除执行与验收历史', false)]);
  if (target === 'in_progress') {
    if (source === 'todo') return planned('prepare', '准备开始任务', '请通过已有流程接入并核验会话；开发与验证还须准备隔离工作区，再明确开始执行');
    if (source === 'review') return planned('feedback', '提出修改反馈', '请填写修改反馈，保留本阶段产出与验收历史');
    if (source === 'done') return planned('reopen', '明确返工', '请确认返工阶段并填写理由，保留历史产出', { stage: 2 });
  }
  if (['review', 'done'].includes(target)) {
    const gate = getStageReview(state, task);
    const checks = [...gate.checks];
    if (target === 'done') {
      checks.push(check('final_stage', '只有最终验证阶段可完成任务，前面阶段须逐一验收', task.stage === 3));
      checks.push(check('review', '当前验证阶段须先进入待验收状态，再明确确认完成', task.attention === 'review'));
    }
    const details = { stage: task.stage, ...(gate.document ? { document: gate.document } : {}) };
    if (checks.some((item) => !item.passed)) return blocked(checks, details);
    return {
      ...planned(target === 'done' ? 'complete' : 'submit_review', target === 'done' ? '验收并完成任务' : '提交当前阶段评审', target === 'done' ? '请审阅当前验证产出并明确确认验收，确认后完成任务' : '请确认提交当前阶段文档；提交只进入人工评审，不会自动验收', details),
      checks,
    };
  }
  return blocked([check('transition', '当前状态不支持此看板迁移', false)]);
}
