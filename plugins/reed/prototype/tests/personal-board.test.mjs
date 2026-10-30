import test from 'node:test';
import assert from 'node:assert/strict';
import { BOARD_COLUMNS, getBoardColumn } from '../src/personal-board.js';
import * as board from '../src/personal-board.js';
import { createInitialState, reduce } from '../src/model.js';

const task = (fields = {}) => ({
  id: 'LOCAL-BOARD', stage: 0, status: 'active', attention: 'idle',
  accepted: [false, false, false, false], sync: 'synced',
  sessionId: null, sessionIds: [], docs: [], notes: [],
  workspace: { ready: false, verified: false, path: '', branch: '' },
  ...fields,
});
const session = (status, fields = {}) => ({
  id: `session-${status}`, taskId: 'LOCAL-BOARD', stage: 0, status, ...fields,
});
const deepFreeze = (value) => {
  Object.values(value).forEach((item) => {
    if (item && typeof item === 'object') deepFreeze(item);
  });
  return Object.freeze(value);
};
const move = (state, id, target) => {
  assert.equal(typeof board.getBoardMove, 'function', '看板须提供可重新校验的只读迁移计划');
  return board.getBoardMove(state, id, target);
};
const boardState = (fields = {}, sessions = []) => ({ tasks: [task(fields)], sessions });
// Most cases model a new explicitly saved document; legacy cases omit outcome.
const output = (fields = {}) => ({ id: 'output-1', title: '需求说明.md', version: 1, kind: '需求', stage: 0, body: '有效产出', outcome: 'manual', ...fields });

test('拖拽四列只计划对应操作，不伪造开工或清除历史', () => {
  const fresh = boardState();
  assert.equal(move(fresh, 'LOCAL-BOARD', 'todo').kind, 'noop');
  assert.equal(move(fresh, 'LOCAL-BOARD', 'in_progress').kind, 'prepare');
  assert.equal(move(boardState({ attention: 'review' }), 'LOCAL-BOARD', 'in_progress').kind, 'feedback');
  const reopened = move(boardState({ status: 'completed', stage: 3, accepted: [true, true, true, true] }), 'LOCAL-BOARD', 'in_progress');
  assert.equal(reopened.kind, 'reopen');
  assert.equal(reopened.stage, 2);
  for (const fields of [{ hasStarted: true }, { attention: 'review' }, { status: 'completed' }]) {
    assert.equal(move(boardState(fields), 'LOCAL-BOARD', 'todo').allowed, false);
  }
  for (const status of ['paused', 'archived']) {
    const plan = move(boardState({ status }), 'LOCAL-BOARD', 'review');
    assert.equal(plan.kind, 'blocked');
    assert.ok(plan.checks.some((check) => !check.passed));
  }
  assert.equal(move(fresh, 'LOCAL-BOARD', 'invalid').allowed, false);
  assert.equal(move(fresh, 'missing', 'review').allowed, false);
});

test('只有当前阶段有效产出且前序已验收才能明确提交评审', () => {
  const valid = boardState({ docs: [output()] });
  const plan = move(deepFreeze(valid), 'LOCAL-BOARD', 'review');
  assert.equal(plan.kind, 'submit_review');
  assert.equal(plan.allowed, true);
  assert.deepEqual(plan.document, { id: 'output-1', title: '需求说明.md', version: 1 });
  assert.equal(plan.stage, 0);
  for (const fields of [
    { docs: [] }, { docs: [output({ body: '  ' })] },
    { docs: [output({ stage: 1 })] }, { docs: [output({ outcome: 'failed' })] },
    { docs: [output({ outcome: 'waiting' })] }, { docs: [output({ outcome: 'unknown' })] },
    { stage: 1, accepted: [false, false, false, false], docs: [output({ stage: 1, kind: '设计' })] },
  ]) {
    const blocked = move(boardState(fields), 'LOCAL-BOARD', 'review');
    assert.equal(blocked.allowed, false, JSON.stringify(fields));
    assert.ok(blocked.checks.some((check) => !check.passed));
  }
  assert.deepEqual(valid.tasks[0].accepted, [false, false, false, false]);
  assert.equal(valid.tasks[0].attention, 'idle');
});

test('失败与任何本任务运行占用都不能靠拖拽进入评审或完成', () => {
  for (const target of ['review', 'done']) {
    for (const attention of ['failed', 'unknown', 'running', 'waiting']) {
      assert.equal(move(boardState({ attention, stage: 3, accepted: [true, true, true, false], docs: [output({ stage: 3, kind: '验证' })] }), 'LOCAL-BOARD', target).allowed, false, `${target}/${attention}`);
    }
    for (const status of ['running', 'waiting', 'unknown']) {
      assert.equal(move(boardState({ attention: target === 'done' ? 'review' : 'idle', stage: 3, accepted: [true, true, true, false], docs: [output({ stage: 3, kind: '验证' })] }, [session(status)]), 'LOCAL-BOARD', target).allowed, false, `${target}/${status}`);
    }
  }
  assert.equal(move(boardState({ docs: [output()] }, [session('running', { taskId: 'OTHER' })]), 'LOCAL-BOARD', 'review').allowed, true);
});

test('旧文档没有 outcome 时纯计划反映已知失败等待未知，人工新版本保留身份', () => {
  for (const attention of ['failed', 'waiting', 'unknown']) {
    const state = deepFreeze(boardState({ attention, docs: [output({ outcome: undefined })] }));
    const before = structuredClone(state);
    const gate = board.getStageReview(state, state.tasks[0]);
    assert.equal(gate.checks.find((item) => item.id === 'outcome').passed, false, attention);
    const plan = move(state, 'LOCAL-BOARD', 'review');
    assert.equal(plan.allowed, false, attention);
    assert.equal(plan.checks.find((item) => item.id === 'outcome').passed, false, attention);
    assert.deepEqual(state, before);

    const manual = boardState({ attention, docs: [output({ outcome: 'manual' })] });
    const manualPlan = move(manual, 'LOCAL-BOARD', 'review');
    assert.equal(manualPlan.checks.find((item) => item.id === 'outcome').passed, true, attention);
    assert.equal(manualPlan.checks.find((item) => item.id === 'attention').passed, false, attention);
    assert.equal(manualPlan.allowed, false, attention);
  }
});

test('空闲旧版材料须重新确认本轮有效，兼容当前明确待验收的旧版材料', () => {
  const state = deepFreeze(boardState({ hasStarted: true, attention: 'idle', docs: [output({ outcome: undefined })] }));
  const before = structuredClone(state);
  const gate = board.getStageReview(state, state.tasks[0]);
  const outcome = gate.checks.find((item) => item.id === 'outcome');
  assert.equal(outcome.passed, false);
  assert.equal(outcome.label, '旧版材料尚未确认本轮有效，请重新执行或保存新版本');
  const plan = move(state, 'LOCAL-BOARD', 'review');
  assert.equal(plan.allowed, false);
  assert.ok(plan.reason.includes(outcome.label));
  assert.deepEqual(state, before);

  const legacyReview = boardState({ attention: 'review', docs: [output({ outcome: undefined })] });
  assert.ok(board.getStageReview(legacyReview, legacyReview.tasks[0]).checks.every((item) => item.passed));
  const initial = createInitialState();
  assert.ok(board.getStageReview(initial, initial.tasks[0]).checks.every((item) => item.passed), 'REQ-1042 当前旧版设计待验收保持兼容');
  for (const outcome of ['manual', 'review']) {
    assert.equal(move(boardState({ docs: [output({ outcome })] }), 'LOCAL-BOARD', 'review').allowed, true);
  }
});

test('完成只计划最终验证待验收，不能跳过阶段或把草稿当作全部完成', () => {
  const final = { stage: 3, attention: 'review', accepted: [true, true, true, false], docs: [output({ stage: 3, kind: '验证' })] };
  const plan = move(boardState(final), 'LOCAL-BOARD', 'done');
  assert.equal(plan.kind, 'complete');
  assert.equal(plan.allowed, true);
  for (const fields of [{ stage: 2 }, { attention: 'idle' }, { accepted: [true, false, true, false] }, { docs: [output({ stage: 3, kind: '验证', body: '' })] }, { docs: [output({ stage: 3, kind: '设计' })] }]) {
    assert.equal(move(boardState({ ...final, ...fields }), 'LOCAL-BOARD', 'done').allowed, false);
  }
});

test('过期成功产出阻止评审与完成，纯计划保留原文档和版本', () => {
  const state = deepFreeze(boardState({ stage: 3, attention: 'idle', accepted: [true, true, true, false], docs: [output({ stage: 3, kind: '验证', outcome: 'review', stale: true })] }));
  const before = structuredClone(state);
  const plan = move(state, 'LOCAL-BOARD', 'review');
  assert.equal(plan.allowed, false);
  assert.equal(plan.checks.find((item) => item.id === 'freshness').passed, false);
  const reviewState = structuredClone(state);
  reviewState.tasks[0].attention = 'review';
  const completePlan = move(reviewState, 'LOCAL-BOARD', 'done');
  assert.equal(completePlan.allowed, false);
  assert.equal(completePlan.checks.find((item) => item.id === 'freshness').passed, false);
  assert.deepEqual(state, before);
});

test('个人看板提供固定的工作进展列及顺序', () => {
  assert.deepEqual(BOARD_COLUMNS, [
    { id: 'todo', label: '待办' },
    { id: 'in_progress', label: '进行中' },
    { id: 'review', label: '评审中' },
    { id: 'done', label: '完成' },
  ]);
});

test('尚未开工的需求任务在待办列', () => {
  assert.equal(getBoardColumn(task()), 'todo');
  assert.equal(getBoardColumn(task(), []), 'todo');
});

test('流程阶段与工作进展独立，推进到任一后续阶段仍在进行中', () => {
  for (const stage of [1, 2, 3]) {
    assert.equal(getBoardColumn(task({ stage })), 'in_progress', `阶段 ${stage}`);
  }
  assert.equal(getBoardColumn(task({ accepted: [true, false, false, false] })), 'in_progress');
  assert.equal(getBoardColumn(task({ accepted: [false, false, true, false] })), 'in_progress');
  assert.equal(getBoardColumn(task({ accepted: [true, true, true, true] })), 'in_progress', '验收位不代替完成状态');
});

test('任意阶段的人工验收都进入评审中，优先于已有阶段进展', () => {
  for (const stage of [0, 1, 2, 3]) {
    assert.equal(getBoardColumn(task({ stage, attention: 'review' })), 'review', `阶段 ${stage}`);
  }
});

test('运行、等待、失败和待核查都保留在进行中', () => {
  for (const attention of ['running', 'waiting', 'failed', 'unknown']) {
    assert.equal(getBoardColumn(task({ attention })), 'in_progress', attention);
  }
});

test('完成状态优先于人工验收、失败和会话执行状态', () => {
  for (const attention of ['idle', 'review', 'failed', 'unknown', 'running']) {
    assert.equal(getBoardColumn(task({ status: 'completed', attention }), [session('running')]), 'done', attention);
  }
});

test('归档从个人看板移除，优先于归档前完成状态和全部验收位', () => {
  const archived = task({
    status: 'archived', archivedFrom: 'completed', stage: 3, attention: 'review',
    accepted: [true, true, true, true],
  });
  assert.equal(getBoardColumn(archived, [session('running')]), null);
});

test('属于本任务的活动会话或明确启动过的结束会话可证明已经开工', () => {
  for (const status of ['running', 'waiting', 'unknown']) {
    assert.equal(getBoardColumn(task(), [session(status)]), 'in_progress', status);
  }
  assert.equal(getBoardColumn(task(), [session('ended', { started: true })]), 'in_progress');
  assert.equal(getBoardColumn(task({ hasStarted: true })), 'in_progress');
});

test('旧结束会话可能只因重新绑定而关闭，不能单独推断已开工', () => {
  assert.equal(getBoardColumn(task(), [session('ended')]), 'todo');
  assert.equal(getBoardColumn(task(), [session('ended', { started: false })]), 'todo');
});

test('绑定空闲会话、准备工作区和本地草稿都不构成开工证据', () => {
  const prepared = task({
    sessionId: 'session-idle', sessionIds: ['session-idle'],
    workspace: { ready: true, verified: true, path: '/workspace/draft', branch: 'reed/draft' },
    docs: [{ id: 'draft', title: '需求说明.md', body: '本地编辑草稿', stage: 0 }],
    notes: ['已整理需求'],
  });
  assert.equal(getBoardColumn(prepared, [session('idle')]), 'todo');
});

test('缺少会话数据时不从关联 ID、草稿或反馈文字虚构已开工', () => {
  const missingHistory = task({
    sessionId: 'missing', sessionIds: ['missing'], notes: ['已停止', '返工需求'],
    docs: [{ id: 'draft', title: '需求说明.md', body: '草稿', stage: 0 }],
  });
  assert.equal(getBoardColumn(missingHistory), 'todo');
  assert.equal(getBoardColumn(task({ stage: 2 })), 'in_progress');
  assert.equal(getBoardColumn(task({ attention: 'review' })), 'review');
});

test('跨任务关联会话不能证明本任务开工，会话归属比关联 ID 更可靠', () => {
  const linked = task({ sessionId: 'session-ended', sessionIds: ['session-ended'] });
  for (const status of ['running', 'waiting', 'unknown', 'ended']) {
    assert.equal(getBoardColumn(linked, [session(status, { taskId: 'OTHER' })]), 'todo', status);
  }
  assert.equal(getBoardColumn(linked, [session('ended', { taskId: 'OTHER' }), session('idle')]), 'todo');
  assert.equal(getBoardColumn(linked, [session('ended', { taskId: 'OTHER' }), session('running', { id: 'owned' })]), 'in_progress');
});

test('暂停保持真实工作进展列', () => {
  assert.equal(getBoardColumn(task({ status: 'paused' })), 'todo');
  assert.equal(getBoardColumn(task({ status: 'paused', stage: 1 })), 'in_progress');
  assert.equal(getBoardColumn(task({ status: 'paused', hasStarted: true }), [session('ended')]), 'in_progress');
  assert.equal(getBoardColumn(task({ status: 'paused', attention: 'review' })), 'review');
  assert.equal(getBoardColumn(task({ status: 'paused', attention: 'unknown' })), 'in_progress');
});

test('同步冲突与同步待核查独立于工作进展', () => {
  for (const sync of ['pending', 'conflict', 'unknown']) {
    assert.equal(getBoardColumn(task({ sync })), 'todo', sync);
    assert.equal(getBoardColumn(task({ sync, stage: 2 })), 'in_progress', sync);
    assert.equal(getBoardColumn(task({ sync, attention: 'review' })), 'review', sync);
    assert.equal(getBoardColumn(task({ sync, status: 'completed' })), 'done', sync);
  }
});

test('停止、修改反馈和返工到需求后，真实执行历史使任务留在进行中', () => {
  let state = reduce(createInitialState(), { type: 'CREATE_TASK', title: '个人看板流程' });
  const id = state.tasks.at(-1).id;
  const act = (type, fields = {}) => {
    state = reduce(state, { type, taskId: id, ...fields });
    return state.tasks.find((item) => item.id === id);
  };
  let current = act('BIND_SESSION', { host: 'Codex' });
  assert.equal(getBoardColumn(current, state.sessions), 'todo');
  act('START_STAGE');
  current = act('STOP_STAGE');
  assert.equal(current.stage, 0);
  assert.equal(current.attention, 'idle');
  assert.equal(getBoardColumn(current, state.sessions), 'in_progress');
  act('START_STAGE');
  current = act('FINISH_STAGE', { outcome: 'review' });
  assert.equal(getBoardColumn(current, state.sessions), 'review');
  current = act('REQUEST_CHANGES', { feedback: '补充需求边界' });
  assert.equal(getBoardColumn(current, state.sessions), 'in_progress');
  act('START_STAGE');
  act('FINISH_STAGE', { outcome: 'review' });
  act('ACCEPT_STAGE');
  current = act('REOPEN_STAGE', { stage: 0, reason: '需求范围变更' });
  assert.equal(current.sessionId, null);
  assert.deepEqual(current.accepted, [false, false, false, false]);
  assert.equal(getBoardColumn(current, state.sessions), 'in_progress');
});

test('连续绑定空闲会话与关联外任务历史不算开工', () => {
  let state = reduce(createInitialState(), { type: 'CREATE_TASK', title: '仅绑定任务' });
  const id = state.tasks.at(-1).id;
  const act = (type, fields = {}) => {
    state = reduce(state, { type, taskId: id, ...fields });
    return state.tasks.find((item) => item.id === id);
  };
  act('BIND_SESSION', { host: 'Codex' });
  const current = act('BIND_SESSION', { host: 'Claude Code' });
  assert.equal(state.sessions.find((item) => item.id === current.sessionIds[0]).status, 'ended');
  assert.equal(getBoardColumn(current, state.sessions), 'todo');
  assert.equal(getBoardColumn(act('LINK_SESSION', { sessionId: 'session-requirement' }), state.sessions), 'todo');
});

test('已有演示任务保留真实开工事实，停止等待和返工需求不会退回待办', () => {
  let state = createInitialState();
  state = reduce(state, { type: 'STOP_STAGE', taskId: 'REQ-1043' });
  assert.equal(getBoardColumn(state.tasks.find((item) => item.id === 'REQ-1043'), state.sessions), 'in_progress');
  state = reduce(state, { type: 'REOPEN_STAGE', taskId: 'REQ-1042', stage: 0, reason: '范围变更' });
  assert.equal(getBoardColumn(state.tasks.find((item) => item.id === 'REQ-1042'), state.sessions), 'in_progress');
  assert.equal(getBoardColumn(state.tasks.find((item) => item.id === 'LOCAL-1'), state.sessions), 'todo');
});

test('旧缓存等待任务停止后保留进行中，不因 attention 归闲丢失开工事实', () => {
  const state = createInitialState();
  const waiting = state.tasks.find((item) => item.id === 'REQ-1043');
  delete waiting.hasStarted;
  assert.equal(waiting.stage, 0);
  assert.equal(getBoardColumn(waiting, state.sessions), 'in_progress');
  const next = reduce(state, { type: 'STOP_STAGE', taskId: waiting.id });
  const stopped = next.tasks.find((item) => item.id === waiting.id);
  assert.equal(stopped.attention, 'idle');
  assert.equal(next.sessions.find((item) => item.id === stopped.sessionId).status, 'ended');
  assert.equal(getBoardColumn(stopped, next.sessions), 'in_progress');
  assert.equal(waiting.hasStarted, undefined, '旧缓存输入仍保持原样');
});

test('旧缓存验证任务返工需求后保留进行中，不因阶段与验收位重置丢失进展', () => {
  const state = createInitialState();
  const verifying = state.tasks.find((item) => item.id === 'REQ-1039');
  delete verifying.hasStarted;
  assert.equal(getBoardColumn(verifying, state.sessions), 'in_progress');
  const next = reduce(state, { type: 'REOPEN_STAGE', taskId: verifying.id, stage: 0, reason: '重新确认需求' });
  const reopened = next.tasks.find((item) => item.id === verifying.id);
  assert.equal(reopened.stage, 0);
  assert.equal(reopened.attention, 'idle');
  assert.deepEqual(reopened.accepted, [false, false, false, false]);
  assert.equal(getBoardColumn(reopened, next.sessions), 'in_progress');
});

test('分类是纯投影，不修改任务、阶段、验收记录或会话历史', () => {
  const current = deepFreeze(task({ status: 'paused', sync: 'conflict', hasStarted: true }));
  const history = deepFreeze([session('ended'), session('running', { taskId: 'OTHER' })]);
  const before = structuredClone({ current, history });
  assert.equal(getBoardColumn(current, history), 'in_progress');
  assert.equal(getBoardColumn(current, history), 'in_progress');
  assert.deepEqual({ current, history }, before);
});
