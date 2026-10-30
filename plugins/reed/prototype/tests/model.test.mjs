import test from 'node:test';
import assert from 'node:assert/strict';
import { STAGES, createInitialState, reduce } from '../src/model.js';
import * as board from '../src/personal-board.js';
import { DEMO_CONNECTOR_ID } from '../src/sources.js';

const get = (state, id = 'REQ-1042') => state.tasks.find((task) => task.id === id);
const act = (state, type, fields = {}) => reduce(state, { type, taskId: 'REQ-1042', ...fields });
const local = () => {
  const state = act(createInitialState(), 'CREATE_TASK', { title: '新增本地任务' });
  assert.equal(state.tasks.at(-1)?.title, '新增本地任务', 'CREATE_TASK 应添加任务');
  return { state, id: state.tasks.at(-1).id };
};
const bound = (state, id) => act(state, 'BIND_SESSION', { taskId: id, host: 'Codex' });
const moveAction = (state, id, target) => {
  const plan = board.getBoardMove?.(state, id, target);
  return { type: 'MOVE_BOARD', taskId: id, target, expectedStage: plan?.stage, documentId: plan?.document?.id, documentVersion: plan?.document?.version };
};

test('看板明确提交当前草稿评审，再用普通验收推进，保留原状态及文档快照事件', () => {
  let { state, id } = local();
  state = act(state, 'SAVE_DOCUMENT', { taskId: id, title: '需求草稿.md', body: '明确验收标准', kind: '需求' });
  const before = structuredClone(state);
  const action = moveAction(state, id, 'review');
  const reviewed = reduce(state, action);
  assert.equal(get(reviewed, id).attention, 'review');
  assert.equal(get(reviewed, id).hasStarted, true);
  assert.equal(get(reviewed, id).stage, 0);
  assert.deepEqual(state, before);
  assert.deepEqual(get(reviewed, id).docs, get(before, id).docs);
  assert.throws(() => reduce(reviewed, action), /重复|迁移|操作/);
  const accepted = act(reviewed, 'ACCEPT_STAGE', { taskId: id });
  assert.equal(get(accepted, id).stage, 1);
  assert.equal(accepted.events.at(-1).documentId, action.documentId);
  assert.equal(accepted.events.at(-1).documentVersion, action.documentVersion);
});

test('MOVE_BOARD 拒绝直接开始、反馈、返工及缺少或陈旧的确认快照', () => {
  let { state, id } = local();
  assert.throws(() => reduce(state, moveAction(state, id, 'in_progress')), /现有|准备|操作/);
  state = act(state, 'SAVE_DOCUMENT', { taskId: id, title: '需求草稿.md', body: '第一版', kind: '需求' });
  const action = moveAction(state, id, 'review');
  assert.throws(() => reduce(state, { ...action, expectedStage: undefined }), /快照|阶段/);
  assert.throws(() => reduce(state, { ...action, documentId: undefined }), /快照|文档/);
  assert.throws(() => reduce(state, { ...action, documentVersion: 99 }), /快照|文档/);
  state = act(state, 'SAVE_DOCUMENT', { taskId: id, title: '需求草稿.md', body: '第二版', kind: '需求' });
  assert.throws(() => reduce(state, action), /快照|文档/);
  state = reduce(state, moveAction(state, id, 'review'));
  assert.throws(() => reduce(state, moveAction(state, id, 'in_progress')), /现有|反馈|操作/);
  const snapshot = { expectedStage: 0, documentId: get(state, id).docs.at(-1).id, documentVersion: 2 };
  const next = act(state, 'ACCEPT_STAGE', { taskId: id, ...snapshot });
  assert.throws(() => act(next, 'ACCEPT_STAGE', { taskId: id, ...snapshot }), /快照|阶段/);
});

test('看板完成必须确认最终验证当前文档，重复或更换文档不可意外验收', () => {
  let state = createInitialState();
  const id = 'REQ-1039';
  assert.throws(() => reduce(state, moveAction(state, id, 'done')), /失败|评审|验收/);
  state = act(state, 'RETRY_STAGE', { taskId: id });
  state = act(state, 'START_STAGE', { taskId: id });
  state = act(state, 'FINISH_STAGE', { taskId: id, outcome: 'review' });
  const action = moveAction(state, id, 'done');
  const changed = act(state, 'SAVE_DOCUMENT', { taskId: id, title: '验证报告.md', body: '人工补全检查结论', kind: '验证' });
  assert.throws(() => reduce(changed, action), /快照|文档/);
  const completed = reduce(state, action);
  assert.equal(get(completed, id).status, 'completed');
  assert.deepEqual(get(completed, id).accepted, [true, true, true, true]);
  assert.throws(() => reduce(completed, action), /重复|迁移|操作/);
  assert.equal(completed.events.at(-1).documentId, action.documentId);
});

test('普通验收也检查当前非空有效产出、阶段前序及所有本任务执行占用', () => {
  for (const mutate of [
    (state) => { get(state).docs = []; },
    (state) => { get(state).docs.at(-1).body = ' '; },
    (state) => { get(state).docs.at(-1).outcome = 'failed'; },
    (state) => { get(state).accepted[0] = false; },
    (state) => { state.sessions.push({ id: 'unexpected', taskId: 'REQ-1042', status: 'unknown' }); },
    (state) => { state.sessions.find((item) => item.id === get(state).sessionId).status = 'running'; },
  ]) {
    const state = createInitialState();
    mutate(state);
    const before = structuredClone(state);
    assert.throws(() => act(state, 'ACCEPT_STAGE'), /产出|正文|验收|失败|执行|未知/);
    assert.deepEqual(state, before);
  }
});

test('失败等待未知生成文档保留 outcome，RETRY 不能把旧失败报告洗成可评审产出', () => {
  for (const outcome of ['failed', 'waiting', 'unknown']) {
    let { state, id } = local();
    state = act(bound(state, id), 'START_STAGE', { taskId: id });
    state = act(state, 'FINISH_STAGE', { taskId: id, outcome });
    assert.equal(get(state, id).docs.at(-1).outcome, outcome);
    if (outcome !== 'failed') continue;
    state = act(state, 'RETRY_STAGE', { taskId: id });
    assert.throws(() => reduce(state, moveAction(state, id, 'review')), /失败|产出/);
    get(state, id).attention = 'review';
    assert.throws(() => act(state, 'ACCEPT_STAGE', { taskId: id }), /失败|产出/);
    get(state, id).attention = 'idle';
    state = act(state, 'SAVE_DOCUMENT', { taskId: id, title: '需求说明.md', body: '人工重新整理后的有效需求', kind: '需求' });
    assert.doesNotThrow(() => reduce(state, moveAction(state, id, 'review')));
  }
  let state = createInitialState();
  delete get(state, 'REQ-1039').docs.at(-1).outcome;
  state = act(state, 'RETRY_STAGE', { taskId: 'REQ-1039' });
  assert.equal(get(state, 'REQ-1039').docs.at(-1).outcome, 'failed');
  assert.throws(() => reduce(state, moveAction(state, 'REQ-1039', 'review')), /失败|产出/);
});

test('失败后人工保存的新版本在明确重试清理状态后仍可提交评审', () => {
  let state = createInitialState();
  const id = 'REQ-1039';
  state = act(state, 'SAVE_DOCUMENT', { taskId: id, title: '验证报告.md', body: '人工重新检查全部验证项，结论通过', kind: '验证' });
  assert.throws(() => reduce(state, moveAction(state, id, 'review')), /失败/);
  state = act(state, 'RETRY_STAGE', { taskId: id });
  assert.equal(get(state, id).docs.at(-1).outcome, 'manual');
  assert.doesNotThrow(() => reduce(state, moveAction(state, id, 'review')));
});

test('旧缓存失败报告经同阶段返工后也不能被重新提交为成功产出', () => {
  let state = createInitialState();
  const id = 'REQ-1039';
  delete get(state, id).docs.at(-1).outcome;
  const before = structuredClone(state);
  state = act(state, 'REOPEN_STAGE', { taskId: id, stage: 3, reason: '核查失败验证' });
  assert.equal(get(state, id).docs.at(-1).outcome, 'failed');
  assert.throws(() => reduce(state, moveAction(state, id, 'review')), /失败|产出/);
  assert.equal(get(before, id).docs.at(-1).outcome, undefined);
});

test('完成返工开发后旧开发和验证产出均过期，新版本逐阶段恢复评审且保留上游及历史', () => {
  let { state, id } = local();
  const titles = ['需求.md', '设计.md', '开发.md', '验证.md'];
  const kinds = ['需求', '设计', '设计', '验证'];
  for (let stage = 0; stage < 4; stage += 1) {
    state = act(state, 'SAVE_DOCUMENT', { taskId: id, title: titles[stage], body: `阶段${stage}原始产出`, kind: kinds[stage] });
    state = reduce(state, moveAction(state, id, 'review'));
    state = act(state, 'ACCEPT_STAGE', { taskId: id });
  }
  const completed = structuredClone(state);
  state = act(state, 'REOPEN_STAGE', { taskId: id, stage: 2, reason: '开发逻辑需要修正并重新验证' });
  assert.equal(board.getBoardMove(state, id, 'review').allowed, false, '返工不能重新提交旧成功报告');
  assert.throws(() => reduce(state, moveAction(state, id, 'review')), /过期|返工|新版本/);
  const gate = board.getStageReview(state, get(state, id));
  assert.equal(gate.checks.find((item) => item.id === 'freshness').passed, false);
  assert.deepEqual(get(state, id).accepted, [true, true, false, false]);
  assert.deepEqual(get(state, id).docs.slice(0, 2), get(completed, id).docs.slice(0, 2));
  assert.ok(get(state, id).docs.slice(2).every((document) => document.stale === true));
  const forgedReview = structuredClone(state);
  get(forgedReview, id).attention = 'review';
  assert.throws(() => act(forgedReview, 'ACCEPT_STAGE', { taskId: id }), /过期|返工|新版本/);

  state = act(state, 'SAVE_DOCUMENT', { taskId: id, title: titles[2], body: '修正后的开发记录', kind: kinds[2] });
  assert.notEqual(get(state, id).docs.at(-1).stale, true);
  assert.equal(board.getBoardMove(state, id, 'review').allowed, true);
  state = reduce(state, moveAction(state, id, 'review'));
  state = act(state, 'ACCEPT_STAGE', { taskId: id });
  assert.equal(board.getBoardMove(state, id, 'review').allowed, false, '开发重新验收不刷新旧验证报告');
  state = act(state, 'SAVE_DOCUMENT', { taskId: id, title: titles[3], body: '重新验证通过', kind: kinds[3] });
  state = reduce(state, moveAction(state, id, 'review'));
  state = reduce(state, moveAction(state, id, 'done'));
  assert.equal(get(state, id).status, 'completed');
  assert.deepEqual(get(state, id).docs.slice(0, 4).map(({ stale: _stale, ...document }) => document), get(completed, id).docs);
  assert.deepEqual(get(state, id).docs.map((document) => document.version), [1, 1, 1, 1, 2, 2]);
  assert.equal(get(state, id).hasStarted, true);
  assert.deepEqual(state.events.slice(0, completed.events.length), completed.events);
});

test('修改反馈使当前阶段全部旧版本过期，人工保存或重新执行的新材料才可再次验收', () => {
  for (const method of ['manual', 'agent']) {
    const original = createInitialState();
    let state = act(original, 'REQUEST_CHANGES', { feedback: '补充失败恢复边界' });
    const previousDocs = get(original).docs;
    assert.equal(board.getBoardMove(state, 'REQ-1042', 'review').allowed, false, method);
    assert.throws(() => reduce(state, moveAction(state, 'REQ-1042', 'review')), /过期|反馈|新版本/);
    assert.deepEqual(get(state).docs[0], previousDocs[0], '已验收需求文档保持有效');
    assert.ok(get(state).docs.filter((document) => document.stage === 1).every((document) => document.stale === true));
    assert.deepEqual(get(state).docs.map(({ stale: _stale, ...document }) => document), previousDocs);
    if (method === 'manual') {
      state = act(state, 'SAVE_DOCUMENT', { title: '补偿方案.md', body: '已补充失败恢复边界', kind: '设计' });
      assert.equal(board.getBoardMove(state, 'REQ-1042', 'review').allowed, true);
      state = reduce(state, moveAction(state, 'REQ-1042', 'review'));
    } else {
      state = act(state, 'START_STAGE');
      state = act(state, 'FINISH_STAGE', { outcome: 'review' });
    }
    assert.notEqual(get(state).docs.at(-1).stale, true);
    assert.equal(get(state).docs.at(-1).version, 3);
    assert.doesNotThrow(() => act(state, 'ACCEPT_STAGE'));
    assert.deepEqual(get(original).docs, previousDocs);
  }
});

test('初始任务展示六种工作状态，默认设计待验收没有伪造工作区', () => {
  const state = createInitialState();
  assert.deepEqual(STAGES, ['需求', '设计', '开发', '验证']);
  assert.equal(state.tasks.length, 6);
  const task = get(state);
  assert.equal(task.title, '成员导入失败后自动补偿');
  assert.equal(task.stage, 1);
  assert.equal(task.attention, 'review');
  assert.equal(task.workspace.ready, false);
  assert.equal(task.workspace.verified, false);
  assert.deepEqual(task.accepted, [true, false, false, false]);
  assert.ok(task.docs.some((doc) => doc.title === '补偿方案.md' && doc.version === 2));
  assert.equal(state.sessions.find((session) => session.id === task.sessionId).status, 'ended');
});

test('Agent 结束仅进入人工验收，验收后才移动阶段且保留历史', () => {
  let { state, id } = local();
  state = bound(state, id);
  state = act(state, 'START_STAGE', { taskId: id });
  state = act(state, 'FINISH_STAGE', { taskId: id, outcome: 'review' });
  assert.equal(get(state, id).stage, 0);
  assert.equal(get(state, id).accepted[0], false);
  assert.equal(state.sessions.find((s) => s.id === get(state, id).sessionId).status, 'ended');
  const doc = get(state, id).docs[0];
  state = act(state, 'ACCEPT_STAGE', { taskId: id });
  assert.equal(get(state, id).stage, 1);
  assert.deepEqual(get(state, id).accepted, [true, false, false, false]);
  assert.equal(get(state, id).attention, 'idle');
  assert.ok(get(state, id).docs.some((item) => item.id === doc.id));
});

test('拒绝缺少前序验收、会话、隔离目录及目录核验的执行', () => {
  let { state, id } = local();
  assert.throws(() => act(state, 'START_STAGE', { taskId: id }), /会话/);
  state = act(state, 'ACCEPT_STAGE');
  assert.throws(() => act(state, 'BIND_SESSION', { host: 'Codex' }), /工作区/);
  state = act(state, 'PREPARE_WORKSPACE');
  assert.equal(get(state).workspace.verified, false);
  state = bound(state, 'REQ-1042');
  assert.equal(get(state).workspace.verified, true);
  state.tasks.find((task) => task.id === 'REQ-1042').accepted[1] = false;
  assert.throws(() => act(state, 'START_STAGE'), /验收/);
  state.tasks.find((task) => task.id === 'REQ-1042').accepted[1] = true;
  state.tasks.find((task) => task.id === 'REQ-1042').workspace.verified = false;
  assert.throws(() => act(state, 'START_STAGE'), /核验/);
});

test('同一任务不能重复启动，同一会话不能被另一任务占用', () => {
  let { state, id } = local();
  state = bound(state, id);
  state = act(state, 'START_STAGE', { taskId: id });
  assert.throws(() => act(state, 'START_STAGE', { taskId: id }), /运行/);
  const other = get(state);
  other.attention = 'idle';
  other.sessionId = get(state, id).sessionId;
  assert.throws(() => act(state, 'START_STAGE'), /会话/);
});

test('未知执行保留归属，不允许盲目重试、停止、归档或重新绑定', () => {
  let { state, id } = local();
  state = act(bound(state, id), 'START_STAGE', { taskId: id });
  const sessionId = get(state, id).sessionId;
  state = act(state, 'FINISH_STAGE', { taskId: id, outcome: 'unknown' });
  assert.equal(get(state, id).sessionId, sessionId);
  assert.equal(state.sessions.find((s) => s.id === sessionId).status, 'unknown');
  for (const type of ['RETRY_STAGE', 'STOP_STAGE', 'ARCHIVE_TASK', 'BIND_SESSION']) {
    assert.throws(() => act(state, type, { taskId: id, host: 'Codex' }), /未知/);
  }
});

test('暂停不会假装停止执行；活跃执行不能归档，确认停止释放会话', () => {
  let { state, id } = local();
  state = act(bound(state, id), 'START_STAGE', { taskId: id });
  state = act(state, 'TOGGLE_PAUSE', { taskId: id });
  assert.equal(get(state, id).status, 'paused');
  assert.equal(get(state, id).attention, 'running');
  assert.equal(state.sessions.find((s) => s.id === get(state, id).sessionId).status, 'running');
  assert.throws(() => act(state, 'ARCHIVE_TASK', { taskId: id }), /执行/);
  state = act(state, 'STOP_STAGE', { taskId: id });
  assert.equal(get(state, id).attention, 'idle');
  assert.equal(state.sessions.find((s) => s.id === get(state, id).sessionId).status, 'ended');
  state = act(state, 'ARCHIVE_TASK', { taskId: id });
  assert.equal(get(state, id).status, 'archived');
});

test('等待继续与失败重试不同；反馈保留文档并追加版本', () => {
  let { state, id } = local();
  state = act(bound(state, id), 'START_STAGE', { taskId: id });
  state = act(state, 'FINISH_STAGE', { taskId: id, outcome: 'waiting' });
  assert.throws(() => act(state, 'RESUME_STAGE', { taskId: id, reply: '  ' }), /答复/);
  state = act(state, 'RESUME_STAGE', { taskId: id, reply: '重复手机号跳过并记录原因' });
  assert.equal(get(state, id).attention, 'running');
  assert.ok(get(state, id).notes.includes('重复手机号跳过并记录原因'));
  assert.ok(state.events.at(-1).text.includes('重复手机号跳过并记录原因'));
  state = act(state, 'FINISH_STAGE', { taskId: id, outcome: 'failed' });
  assert.throws(() => act(state, 'RESUME_STAGE', { taskId: id }), /等待/);
  state = act(state, 'RETRY_STAGE', { taskId: id });
  state = act(state, 'START_STAGE', { taskId: id });
  state = act(state, 'FINISH_STAGE', { taskId: id, outcome: 'review' });
  assert.throws(() => act(state, 'REQUEST_CHANGES', { taskId: id, feedback: '  ' }), /反馈/);
  state = act(state, 'REQUEST_CHANGES', { taskId: id, feedback: '补充边界' });
  const before = get(state, id).docs.length;
  state = act(bound(state, id), 'START_STAGE', { taskId: id });
  state = act(state, 'FINISH_STAGE', { taskId: id, outcome: 'review' });
  assert.equal(get(state, id).docs.length, before + 1);
  assert.deepEqual(get(state, id).docs.map((d) => d.version), [1, 2, 3, 4]);
  assert.deepEqual(get(state, id).notes, ['重复手机号跳过并记录原因', '补充边界']);
});

test('导入按外部编号去重，本地编辑独立于同步状态与阶段状态', () => {
  let state = createInitialState();
  state = act(state, 'IMPORT_TASK', { connectorId: demoId, externalId: 'REQ-X', title: '云效需求' });
  const id = state.tasks.at(-1).id;
  const count = state.tasks.length;
  state = act(state, 'IMPORT_TASK', { connectorId: demoId, externalId: 'REQ-X', title: '重复导入' });
  assert.equal(state.tasks.length, count);
  state = act(state, 'UPDATE_TASK', { taskId: id, title: '本地修订' });
  assert.equal(get(state, id).sync, 'pending');
  assert.equal(get(state, id).stage, 0);
  assert.equal(get(state, id).attention, 'idle');
  state = act(state, 'SET_SYNC', { taskId: id, value: 'conflict' });
  state = act(state, 'RESOLVE_SYNC', { taskId: id, choice: 'pause' });
  assert.equal(get(state, id).sync, 'conflict');
  state = act(state, 'RESOLVE_SYNC', { taskId: id, choice: 'local' });
  assert.equal(get(state, id).sync, 'pending');
  state = act(state, 'SET_SYNC', { taskId: id, value: 'conflict' });
  state = act(state, 'RESOLVE_SYNC', { taskId: id, choice: 'remote' });
  assert.equal(get(state, id).sync, 'synced');
  state = act(state, 'SET_SYNC', { taskId: id, value: 'unknown' });
  assert.throws(() => act(state, 'RESOLVE_SYNC', { taskId: id, choice: 'local' }), /未知/);
  assert.doesNotThrow(() => act(state, 'RESOLVE_SYNC', { taskId: id, choice: 'pause' }));
});

test('最终验证通过后必须人工验收才完成任务', () => {
  let state = createInitialState();
  const id = state.tasks.find((task) => task.stage === 3).id;
  state = act(state, 'RETRY_STAGE', { taskId: id });
  state = act(state, 'START_STAGE', { taskId: id });
  state = act(state, 'FINISH_STAGE', { taskId: id, outcome: 'review' });
  assert.equal(get(state, id).status, 'active');
  state = act(state, 'ACCEPT_STAGE', { taskId: id });
  assert.equal(get(state, id).status, 'completed');
  assert.deepEqual(get(state, id).accepted, [true, true, true, true]);
});

test('reducer 不修改输入，新状态和初始样本彼此隔离，拒绝非法参数', () => {
  const state = createInitialState();
  const snapshot = structuredClone(state);
  const next = act(state, 'ACCEPT_STAGE');
  assert.deepEqual(state, snapshot);
  assert.notEqual(next, state);
  assert.ok(next.events.length > state.events.length);
  assert.throws(() => act(state, 'CREATE_TASK', { title: '' }), /标题/);
  assert.throws(() => act(state, 'ACCEPT_STAGE', { taskId: 'missing' }), /任务/);
  assert.throws(() => act(state, 'SET_SYNC', { value: 'invalid' }), /同步/);
  assert.throws(() => act(state, 'INVALID'), /操作/);
  next.tasks[0].notes.push('修改');
  assert.deepEqual(createInitialState(), snapshot);
});

test('普通任务设计产出使用通用文档标题，既有补偿方案继续追加版本', () => {
  let { state, id } = local();
  state = act(bound(state, id), 'START_STAGE', { taskId: id });
  state = act(state, 'FINISH_STAGE', { taskId: id, outcome: 'review' });
  state = act(state, 'ACCEPT_STAGE', { taskId: id });
  state = act(bound(state, id), 'START_STAGE', { taskId: id });
  state = act(state, 'FINISH_STAGE', { taskId: id, outcome: 'review' });
  assert.equal(get(state, id).docs.at(-1).title, '设计方案.md');
  state = act(state, 'REQUEST_CHANGES', { feedback: '补充失败日志' });
  state = act(bound(state, 'REQ-1042'), 'START_STAGE');
  state = act(state, 'FINISH_STAGE', { outcome: 'review' });
  assert.equal(get(state).docs.at(-1).title, '补偿方案.md');
  assert.equal(get(state).docs.at(-1).version, 3);
});

test('暂停禁止新执行；错误目录、会话关联和前序验收不能通过门禁', () => {
  let state = act(createInitialState(), 'ACCEPT_STAGE');
  state = bound(act(state, 'PREPARE_WORKSPACE'), 'REQ-1042');
  const mismatched = structuredClone(state);
  get(mismatched).workspace.path = '/workspace/wrong';
  assert.throws(() => act(mismatched, 'START_STAGE'), /核验/);
  const unaccepted = structuredClone(state);
  get(unaccepted).accepted[0] = false;
  get(unaccepted).attention = 'review';
  assert.throws(() => act(unaccepted, 'ACCEPT_STAGE'), /验收/);
  state = act(state, 'TOGGLE_PAUSE');
  assert.throws(() => act(state, 'START_STAGE'), /暂停/);
  const waiting = createInitialState().tasks.find((task) => task.attention === 'waiting');
  assert.throws(() => act(createInitialState(), 'ARCHIVE_TASK', { taskId: waiting.id }), /执行/);
});

test('验证失败可明确返工开发，保留历史和隔离资源但需重新接入会话', () => {
  const state = createInitialState();
  const original = state.tasks.find((task) => task.stage === 3);
  const next = act(state, 'REOPEN_STAGE', { taskId: original.id, stage: 2, reason: '修复旧会话权限缓存' });
  const task = get(next, original.id);
  assert.equal(task.stage, 2);
  assert.equal(task.status, 'active');
  assert.equal(task.attention, 'idle');
  assert.deepEqual(task.accepted, [true, true, false, false]);
  assert.equal(task.sessionId, null);
  assert.deepEqual(task.sessionIds, original.sessionIds);
  assert.deepEqual(task.docs, original.docs.map((document) => ({ ...document, stale: true })));
  assert.equal(task.workspace.ready, true);
  assert.equal(task.workspace.path, original.workspace.path);
  assert.equal(task.workspace.verified, false);
  assert.ok(next.events.length > state.events.length);
  assert.ok(next.events.at(-1).text.includes('修复旧会话权限缓存'));
  assert.throws(() => act(next, 'START_STAGE', { taskId: original.id }), /会话/);
  assert.doesNotThrow(() => act(bound(next, original.id), 'START_STAGE', { taskId: original.id }));
  assert.equal(original.stage, 3);
});

test('已完成任务可返工更早阶段，拒绝未来阶段、缺少理由及活跃执行返工', () => {
  let state = createInitialState();
  const id = state.tasks.find((task) => task.stage === 3).id;
  state = act(state, 'RETRY_STAGE', { taskId: id });
  state = act(state, 'START_STAGE', { taskId: id });
  state = act(state, 'FINISH_STAGE', { taskId: id, outcome: 'review' });
  state = act(state, 'ACCEPT_STAGE', { taskId: id });
  state = act(state, 'REOPEN_STAGE', { taskId: id, stage: 1, reason: '验收标准调整' });
  assert.equal(get(state, id).status, 'active');
  assert.deepEqual(get(state, id).accepted, [true, false, false, false]);
  assert.throws(() => act(state, 'REOPEN_STAGE', { taskId: id, stage: 2, reason: '无效跳转' }), /阶段/);
  assert.throws(() => act(state, 'REOPEN_STAGE', { taskId: id, stage: -1, reason: '无效跳转' }), /阶段/);
  assert.throws(() => act(state, 'REOPEN_STAGE', { taskId: id, stage: 0.5, reason: '无效跳转' }), /阶段/);
  assert.throws(() => act(state, 'REOPEN_STAGE', { taskId: id, stage: 0, reason: '  ' }), /理由/);
  const runningId = state.tasks.find((task) => task.attention === 'running').id;
  assert.throws(() => act(state, 'REOPEN_STAGE', { taskId: runningId, stage: 1, reason: '返工' }), /执行/);
  const waitingId = state.tasks.find((task) => task.attention === 'waiting').id;
  assert.throws(() => act(state, 'REOPEN_STAGE', { taskId: waitingId, stage: 0, reason: '返工' }), /执行/);
  state = act(state, 'FINISH_STAGE', { taskId: runningId, outcome: 'unknown' });
  assert.throws(() => act(state, 'REOPEN_STAGE', { taskId: runningId, stage: 1, reason: '返工' }), /未知/);
});

test('未知执行只可明确人工核查，核查完成释放归属并保留人工验收门禁', () => {
  let { state, id } = local();
  state = act(bound(state, id), 'START_STAGE', { taskId: id });
  assert.throws(() => act(state, 'RECONCILE_STAGE', { taskId: id, outcome: 'review' }), /未知/);
  state = act(state, 'FINISH_STAGE', { taskId: id, outcome: 'unknown' });
  const badSession = structuredClone(state);
  badSession.sessions.find((session) => session.id === get(badSession, id).sessionId).taskId = 'another-task';
  assert.throws(() => act(badSession, 'RECONCILE_STAGE', { taskId: id, outcome: 'review' }), /会话/);
  assert.throws(() => act(state, 'RECONCILE_STAGE', { taskId: id, outcome: 'idle' }), /结果/);
  assert.throws(() => act(state, 'RETRY_STAGE', { taskId: id }), /未知/);
  const count = get(state, id).docs.length;
  const reviewed = act(state, 'RECONCILE_STAGE', { taskId: id, outcome: 'review' });
  assert.equal(get(reviewed, id).attention, 'review');
  assert.equal(get(reviewed, id).accepted[0], false);
  assert.equal(get(reviewed, id).docs.length, count + 1);
  assert.equal(reviewed.sessions.find((session) => session.id === get(reviewed, id).sessionId).status, 'ended');
  assert.ok(reviewed.events.at(-1).text.includes('人工核查'));
  const failed = act(state, 'RECONCILE_STAGE', { taskId: id, outcome: 'failed' });
  assert.equal(get(failed, id).attention, 'failed');
  assert.equal(get(failed, id).docs.length, count + 1);
  assert.doesNotThrow(() => act(failed, 'RETRY_STAGE', { taskId: id }));
  const running = act(state, 'RECONCILE_STAGE', { taskId: id, outcome: 'running' });
  assert.equal(get(running, id).attention, 'running');
  assert.equal(get(running, id).sessionId, get(state, id).sessionId);
  assert.equal(get(running, id).docs.length, count);
  assert.equal(running.sessions.find((session) => session.id === get(running, id).sessionId).status, 'running');
  assert.throws(() => act(running, 'ARCHIVE_TASK', { taskId: id }), /执行/);
});

test('云效阶段验收及返工标为待同步，既有冲突和未知同步状态不被覆盖', () => {
  for (const sync of ['synced', 'pending', 'conflict', 'unknown']) {
    const state = createInitialState();
    get(state).sync = sync;
    const expected = ['conflict', 'unknown'].includes(sync) ? sync : 'pending';
    const accepted = act(state, 'ACCEPT_STAGE');
    assert.equal(get(accepted).sync, expected);
    const reopened = act(state, 'REOPEN_STAGE', { stage: 0, reason: '补充验收标准' });
    assert.equal(get(reopened).sync, expected);
  }
  let { state, id } = local();
  state = act(bound(state, id), 'START_STAGE', { taskId: id });
  state = act(state, 'FINISH_STAGE', { taskId: id, outcome: 'review' });
  state = act(state, 'ACCEPT_STAGE', { taskId: id });
  assert.equal(get(state, id).sync, 'synced');
  state = act(state, 'REOPEN_STAGE', { taskId: id, stage: 0, reason: '补充说明' });
  assert.equal(get(state, id).sync, 'synced');
});

test('当前阶段可保存本地文档并追加版本，保留旧正文与状态', () => {
  let { state, id } = local();
  state = act(state, 'SAVE_DOCUMENT', { taskId: id, title: '需求草稿.md', body: '# 目标\n补全失败处理', kind: '需求' });
  const original = structuredClone(state);
  state = act(state, 'SAVE_DOCUMENT', { taskId: id, title: '需求草稿.md', body: '# 目标\n补全失败处理与验收标准', kind: '需求' });
  assert.deepEqual(get(state, id).docs.map((doc) => doc.version), [1, 2]);
  assert.equal(get(state, id).docs[0].body, '# 目标\n补全失败处理');
  assert.equal(get(state, id).docs[1].stage, 0);
  assert.equal(get(state, id).stage, 0);
  assert.equal(get(state, id).attention, 'idle');
  assert.equal(get(state, id).accepted[0], false);
  assert.equal(get(original, id).docs.length, 1);
  assert.ok(state.events.at(-1).text.includes('需求草稿.md'));
  assert.throws(() => act(state, 'SAVE_DOCUMENT', { taskId: id, title: ' ', body: '内容', kind: '需求' }), /标题/);
  assert.throws(() => act(state, 'SAVE_DOCUMENT', { taskId: id, title: '草稿.md', body: ' ', kind: '需求' }), /正文/);
  assert.throws(() => act(state, 'SAVE_DOCUMENT', { taskId: id, title: '草稿.md', body: '内容', kind: '未知' }), /类型/);
  assert.throws(() => act(state, 'SAVE_DOCUMENT', { taskId: id, title: '草稿.md', body: '内容', kind: '验证' }), /阶段/);
});

test('文档保存拒绝执行中、暂停、已验收阶段；开发文档与已验收设计文档区分', () => {
  let state = createInitialState();
  const save = (target, fields = {}) => act(target, 'SAVE_DOCUMENT', { title: '补偿方案.md', body: '修改内容', kind: '设计', ...fields });
  assert.doesNotThrow(() => save(state));
  state = act(state, 'ACCEPT_STAGE');
  assert.throws(() => save(state), /返工/);
  state = save(state, { title: '开发记录.md' });
  assert.equal(get(state).docs.at(-1).stage, 2);
  state = act(state, 'REOPEN_STAGE', { stage: 1, reason: '调整补偿设计' });
  assert.doesNotThrow(() => save(state));
  const accepted = structuredClone(state);
  get(accepted).accepted[1] = true;
  assert.throws(() => save(accepted), /验收|返工/);
  state = act(state, 'TOGGLE_PAUSE');
  assert.throws(() => save(state), /暂停/);
  for (const attention of ['running', 'waiting', 'unknown']) {
    const target = createInitialState();
    get(target).attention = attention;
    assert.throws(() => save(target), /执行|未知/);
  }
});

test('历史会话关联幂等且不会接管其他任务的执行会话', () => {
  const state = createInitialState();
  const source = state.tasks.find((task) => task.attention === 'running');
  const originalSession = structuredClone(state.sessions.find((session) => session.id === source.sessionId));
  const next = act(state, 'LINK_SESSION', { sessionId: source.sessionId });
  assert.ok(get(next).sessionIds.includes(source.sessionId));
  assert.equal(get(next).sessionId, get(state).sessionId);
  assert.deepEqual(next.sessions.find((session) => session.id === source.sessionId), originalSession);
  assert.deepEqual(get(next, source.id), source);
  assert.deepEqual(next.branches, state.branches);
  assert.equal(get(state).sessionIds.length + 1, get(next).sessionIds.length);
  const again = act(next, 'LINK_SESSION', { sessionId: source.sessionId });
  assert.deepEqual(again, next);
  assert.throws(() => act(next, 'LINK_SESSION', { sessionId: 'missing' }), /会话/);
});

test('开发返工设计后生成独立设计文档，不把开发记录当作已验收设计文档', () => {
  let state = createInitialState();
  const id = state.tasks.find((task) => task.attention === 'running').id;
  state = act(state, 'FINISH_STAGE', { taskId: id, outcome: 'review' });
  state = act(state, 'REOPEN_STAGE', { taskId: id, stage: 1, reason: '设计边界需要调整' });
  state = act(bound(state, id), 'START_STAGE', { taskId: id });
  state = act(state, 'FINISH_STAGE', { taskId: id, outcome: 'review' });
  assert.equal(get(state, id).docs.at(-1).title, '设计方案.md');
  assert.equal(get(state, id).docs.at(-1).stage, 1);
  assert.equal(get(state, id).docs[0].title, '开发记录.md');
  assert.equal(get(state, id).docs[0].stage, 2);
});

test('云效冲突选择真正应用远端标题，本地选择保留编辑且同步成功回读远端值', () => {
  let state = createInitialState();
  const originalTitle = get(state).title;
  assert.equal(get(state).remoteTitle, originalTitle);
  state = act(state, 'UPDATE_TASK', { title: '本地补偿范围' });
  assert.equal(get(state).remoteTitle, originalTitle);
  state = act(state, 'SET_SYNC', { value: 'conflict' });
  const remoteTitle = `${originalTitle}（范围已调整）`;
  assert.equal(get(state).remoteTitle, remoteTitle);
  assert.equal(get(state).title, '本地补偿范围');
  const remote = act(state, 'RESOLVE_SYNC', { choice: 'remote' });
  assert.equal(get(remote).title, remoteTitle);
  assert.equal(get(remote).sync, 'synced');
  const local = act(state, 'RESOLVE_SYNC', { choice: 'local' });
  assert.equal(get(local).title, '本地补偿范围');
  assert.equal(get(local).sync, 'pending');
  assert.equal(get(local).remoteTitle, remoteTitle);
  const synced = act(local, 'SET_SYNC', { value: 'synced' });
  assert.equal(get(synced).remoteTitle, '本地补偿范围');
  const imported = act(state, 'IMPORT_TASK', { connectorId: demoId, externalId: 'REQ-REMOTE', title: '远端新需求' });
  assert.equal(imported.tasks.at(-1).remoteTitle, '远端新需求');
});

test('编辑本地标题不能抹掉冲突或未知同步，暂停处理也保留两边字段', () => {
  for (const sync of ['conflict', 'unknown']) {
    let state = act(createInitialState(), 'SET_SYNC', { value: sync });
    const remoteTitle = get(state).remoteTitle;
    state = act(state, 'UPDATE_TASK', { title: '进一步本地修改' });
    assert.equal(get(state).title, '进一步本地修改');
    assert.equal(get(state).remoteTitle, remoteTitle);
    assert.equal(get(state).sync, sync);
    const paused = act(state, 'RESOLVE_SYNC', { choice: 'pause' });
    assert.equal(get(paused).title, '进一步本地修改');
    assert.equal(get(paused).remoteTitle, remoteTitle);
    assert.equal(get(paused).sync, sync);
    if (sync === 'unknown') assert.throws(() => act(state, 'RESOLVE_SYNC', { choice: 'remote' }), /未知/);
  }
});

test('归档与恢复保持每个任务独立生命周期，重复归档不覆盖原状态', () => {
  for (const status of ['active', 'paused', 'completed']) {
    let state = createInitialState();
    const id = status === 'completed' ? state.tasks.find((task) => task.stage === 3).id : 'REQ-1042';
    if (status === 'paused') state = act(state, 'TOGGLE_PAUSE', { taskId: id });
    if (status === 'completed') {
      state = act(state, 'RETRY_STAGE', { taskId: id });
      state = act(state, 'START_STAGE', { taskId: id });
      state = act(state, 'FINISH_STAGE', { taskId: id, outcome: 'review' });
      state = act(state, 'ACCEPT_STAGE', { taskId: id });
    }
    const before = structuredClone(get(state, id));
    const otherTasks = state.tasks.filter((task) => task.id !== id);
    const archived = act(state, 'ARCHIVE_TASK', { taskId: id });
    assert.equal(get(archived, id).status, 'archived');
    assert.equal(get(archived, id).archivedFrom, status);
    const again = act(archived, 'ARCHIVE_TASK', { taskId: id });
    assert.deepEqual(again, archived);
    const restored = act(again, 'RESTORE_TASK', { taskId: id });
    const task = get(restored, id);
    assert.equal(task.status, status);
    for (const key of ['stage', 'accepted', 'attention', 'docs', 'notes', 'sessionId', 'sessionIds', 'workspace']) {
      assert.deepEqual(task[key], before[key]);
    }
    assert.deepEqual(restored.tasks.filter((item) => item.id !== id), otherTasks);
    assert.deepEqual(restored.events.slice(0, state.events.length), state.events);
    assert.throws(() => act(restored, 'RESTORE_TASK', { taskId: id }), /归档/);
  }
});

test('需求阶段本地任务归档后可恢复继续工作', () => {
  let { state, id } = local();
  state = act(state, 'ARCHIVE_TASK', { taskId: id });
  state = act(state, 'RESTORE_TASK', { taskId: id });
  assert.equal(get(state, id).stage, 0);
  assert.equal(get(state, id).status, 'active');
  assert.doesNotThrow(() => act(bound(state, id), 'START_STAGE', { taskId: id }));
});

test('需求占用设计文档名时，设计产出避让并可继续编辑当前阶段版本', () => {
  let { state, id } = local();
  const saveRequirement = (title) => {
    state = act(state, 'SAVE_DOCUMENT', { taskId: id, title, body: '# 需求内容', kind: '需求' });
  };
  saveRequirement('设计方案.md');
  saveRequirement('设计方案（设计阶段）.md');
  state = act(bound(state, id), 'START_STAGE', { taskId: id });
  state = act(state, 'FINISH_STAGE', { taskId: id, outcome: 'review' });
  state = act(state, 'ACCEPT_STAGE', { taskId: id });
  state = act(bound(state, id), 'START_STAGE', { taskId: id });
  state = act(state, 'FINISH_STAGE', { taskId: id, outcome: 'review' });
  const generated = get(state, id).docs.at(-1);
  assert.equal(generated.title, '设计方案（设计阶段 2）.md');
  assert.equal(generated.version, 1);
  assert.equal(generated.stage, 1);
  assert.throws(() => act(state, 'SAVE_DOCUMENT', { taskId: id, title: '设计方案.md', body: '试图修改需求', kind: '设计' }), /返工/);
  state = act(state, 'SAVE_DOCUMENT', { taskId: id, title: generated.title, body: '# 修改后的设计', kind: '设计' });
  assert.equal(get(state, id).docs.at(-1).version, 2);
  state = act(state, 'REQUEST_CHANGES', { taskId: id, feedback: '补齐幂等边界' });
  state = act(state, 'START_STAGE', { taskId: id });
  state = act(state, 'FINISH_STAGE', { taskId: id, outcome: 'review' });
  const regenerated = get(state, id).docs.at(-1);
  assert.equal(regenerated.title, generated.title);
  assert.equal(regenerated.version, 3);
  assert.equal(get(state, id).docs.find((item) => item.title === '设计方案.md').body, '# 需求内容');
});

test('旧归档缓存必须显式选择恢复状态和理由，完成状态必须全部验收', () => {
  const legacy = act(createInitialState(), 'ARCHIVE_TASK');
  delete get(legacy).archivedFrom;
  assert.throws(() => act(legacy, 'RESTORE_TASK'), /归档前状态|指定/);
  assert.throws(() => act(legacy, 'RESTORE_TASK', { restoreStatus: 'active', reason: '  ' }), /理由/);
  assert.throws(() => act(legacy, 'RESTORE_TASK', { restoreStatus: 'invalid', reason: '核查旧任务' }), /状态/);
  assert.throws(() => act(legacy, 'RESTORE_TASK', { restoreStatus: 'completed', reason: '核查旧任务' }), /验收/);
  for (const restoreStatus of ['active', 'paused']) {
    const restored = act(legacy, 'RESTORE_TASK', { restoreStatus, reason: '已人工核查早期演示缓存' });
    assert.equal(get(restored).status, restoreStatus);
    assert.deepEqual(get(restored).accepted, get(legacy).accepted);
    assert.deepEqual(get(restored).docs, get(legacy).docs);
    assert.equal(get(restored).stage, get(legacy).stage);
    assert.equal(get(restored).archivedFrom, undefined);
    assert.ok(restored.events.at(-1).text.includes('人工指定旧任务恢复状态'));
    assert.ok(restored.events.at(-1).text.includes('已人工核查早期演示缓存'));
  }
  const fullyAccepted = structuredClone(legacy);
  get(fullyAccepted).stage = 3;
  get(fullyAccepted).accepted = [true, true, true, true];
  const completed = act(fullyAccepted, 'RESTORE_TASK', { restoreStatus: 'completed', reason: '已核对全部人工验收记录' });
  assert.equal(get(completed).status, 'completed');
});

test('新归档只能按原状态恢复，显式旧缓存选项不能覆盖或绕过损坏状态', () => {
  const archived = act(act(createInitialState(), 'TOGGLE_PAUSE'), 'ARCHIVE_TASK');
  assert.throws(() => act(archived, 'RESTORE_TASK', { restoreStatus: 'active', reason: '试图覆盖原状态' }), /覆盖|指定/);
  assert.equal(get(act(archived, 'RESTORE_TASK')).status, 'paused');
  const corrupted = structuredClone(archived);
  get(corrupted).archivedFrom = 'invalid';
  assert.throws(() => act(corrupted, 'RESTORE_TASK', { restoreStatus: 'active', reason: '不能假装是缺失状态' }), /归档前状态/);
});

test('只有成功开始执行才记录 hasStarted，准备与重新绑定不标记开工', () => {
  let { state, id } = local();
  assert.equal(get(state, id).hasStarted, false);
  assert.throws(() => act(state, 'START_STAGE', { taskId: id }), /会话/);
  assert.equal(get(state, id).hasStarted, false);
  state = act(state, 'PREPARE_WORKSPACE', { taskId: id });
  state = act(state, 'SAVE_DOCUMENT', { taskId: id, title: '需求说明.md', body: '本地草稿', kind: '需求' });
  state = bound(bound(state, id), id);
  state = act(state, 'LINK_SESSION', { taskId: id, sessionId: 'session-requirement' });
  assert.equal(get(state, id).hasStarted, false);
  state = act(state, 'START_STAGE', { taskId: id });
  assert.equal(get(state, id).hasStarted, true);
});

test('hasStarted 在停止、暂停、修改反馈、返工、归档与恢复后保持事实', () => {
  let { state, id } = local();
  const transition = (type, fields = {}) => {
    state = act(state, type, { taskId: id, ...fields });
    assert.equal(get(state, id).hasStarted, true, type);
  };
  state = act(bound(state, id), 'START_STAGE', { taskId: id });
  assert.equal(get(state, id).hasStarted, true);
  transition('TOGGLE_PAUSE');
  transition('STOP_STAGE');
  transition('ARCHIVE_TASK');
  transition('RESTORE_TASK');
  transition('TOGGLE_PAUSE');
  transition('START_STAGE');
  transition('FINISH_STAGE', { outcome: 'review' });
  transition('REQUEST_CHANGES', { feedback: '补充验收边界' });
  transition('START_STAGE');
  transition('FINISH_STAGE', { outcome: 'review' });
  transition('ACCEPT_STAGE');
  transition('REOPEN_STAGE', { stage: 0, reason: '更新需求范围' });
  assert.equal(get(state, id).stage, 0);
  assert.equal(get(state, id).attention, 'idle');
  assert.deepEqual(get(state, id).accepted, [false, false, false, false]);
});

test('旧缓存依据明确执行 attention 补齐开工事实，输入缓存不被修改', () => {
  for (const attention of ['running', 'waiting', 'review', 'failed', 'unknown']) {
    const state = createInitialState();
    const task = get(state, 'LOCAL-1');
    delete task.hasStarted;
    task.attention = attention;
    const next = act(state, 'UPDATE_TASK', { taskId: task.id, title: '更新标题' });
    assert.equal(get(next, task.id).hasStarted, true, attention);
    assert.equal(task.hasStarted, undefined, attention);
  }
});

test('旧缓存的已推进阶段和已验收事实在返工清空前补齐开工事实', () => {
  for (const fields of [{ stage: 3 }, { accepted: [true, false, false, false] }]) {
    const state = createInitialState();
    const task = get(state, 'LOCAL-1');
    delete task.hasStarted;
    Object.assign(task, fields);
    const next = act(state, 'REOPEN_STAGE', { taskId: task.id, stage: 0, reason: '更新需求范围' });
    assert.equal(get(next, task.id).hasStarted, true);
    assert.equal(get(next, task.id).stage, 0);
    assert.deepEqual(get(next, task.id).accepted, [false, false, false, false]);
  }
});

test('旧缓存归档前的可靠开工事实经过恢复与返工继续保留', () => {
  let state = createInitialState();
  delete get(state).hasStarted;
  state = act(state, 'ARCHIVE_TASK');
  assert.equal(get(state).hasStarted, true);
  state = act(state, 'RESTORE_TASK');
  state = act(state, 'REOPEN_STAGE', { stage: 0, reason: '重新梳理需求' });
  assert.equal(get(state).hasStarted, true);
});

test('旧缓存仅有 ended、草稿、工作区或跨任务历史不能补齐开工事实', () => {
  let { state, id } = local();
  state = bound(bound(state, id), id);
  state = act(state, 'PREPARE_WORKSPACE', { taskId: id });
  state = act(state, 'SAVE_DOCUMENT', { taskId: id, title: '需求说明.md', body: '本地草稿', kind: '需求' });
  delete get(state, id).hasStarted;
  state = act(state, 'LINK_SESSION', { taskId: id, sessionId: 'session-requirement' });
  state = act(state, 'ARCHIVE_TASK', { taskId: id });
  state = act(state, 'RESTORE_TASK', { taskId: id });
  assert.notEqual(get(state, id).hasStarted, true);
});

test('连接配置在任务查找之前处理，创建时不需要任务且保持模拟断开状态', () => {
  const state = reduce(createInitialState(), { type: 'CREATE_CONNECTOR', name: '云效 · 组织二', organizationId: 'org-2', organizationName: '组织二', endpoint: '', projects: ['成员中心'], syncMode: 'bidirectional' });
  assert.equal(state.connectors.at(-1).status, 'disconnected');
  assert.equal(state.connectors.at(-1).enabled, true);
  assert.equal(state.connectors.at(-1).provider, 'yunxiao');
});

test('初始任务及实体分别记录自己的来源，不把任务 Connector 传播给 Agent 和本地对象', () => {
  const state = createInitialState();
  const task = get(state);
  assert.deepEqual(task.origin, { kind: 'connector', connectorId: 'connector-yunxiao-demo', externalId: task.externalId });
  assert.equal(task.docs[0].origin.kind, 'connector');
  assert.equal(task.docs[0].origin.externalId, task.externalId, '云效需求原文引用所属工作项编号，不能把本地文档 ID 当作外部编号');
  const otherRequirement = get(state, 'REQ-1045');
  assert.equal(otherRequirement.docs[0].origin.externalId, otherRequirement.externalId);
  assert.deepEqual(task.docs[1].origin, { kind: 'host', host: 'Codex' });
  assert.deepEqual(state.sessions[0].origin, { kind: 'host', host: 'Codex' });
  assert.deepEqual(state.branches[0].origin, { kind: 'local', system: 'git', repo: 'member-service' });
  assert.deepEqual(state.events[0].origin, { kind: 'local', system: 'reed' });
});

const demoId = DEMO_CONNECTOR_ID;
const newConnector = (state, overrides = {}) => reduce(state, { type: 'CREATE_CONNECTOR', name: '云效 · 另一个组织', organizationId: 'org-2', organizationName: '组织二', endpoint: '', projects: ['成员中心'], syncMode: 'bidirectional', ...overrides });
const importTask = (state, connectorId = demoId, externalId = 'REQ-SAME', fields = {}) => reduce(state, { type: 'IMPORT_TASK', connectorId, externalId, title: '模拟远端任务', ...fields });

test('导入显式连接并按连接实例和外部编号去重，不同连接同名项目同编号独立', () => {
  let state = newConnector(createInitialState());
  const id = state.connectors.at(-1).id;
  assert.throws(() => reduce(state, { type: 'IMPORT_TASK', externalId: 'REQ-X', title: '缺少连接' }), /Connector|连接/);
  assert.throws(() => importTask(state, id), /连接/);
  state = reduce(state, { type: 'TEST_CONNECTOR', connectorId: id, outcome: 'connected' });
  state = importTask(state);
  state = importTask(state, id);
  assert.equal(state.tasks.filter((task) => task.externalId === 'REQ-SAME').length, 2);
  const before = state.tasks.length;
  state = importTask(state, id);
  assert.equal(state.tasks.length, before);
  assert.deepEqual(state.tasks.at(-1).origin, { kind: 'connector', connectorId: id, externalId: 'REQ-SAME' });
  assert.throws(() => importTask(state, id, 'REQ-P', { project: '其他项目' }), /项目/);
});

test('连接改名保留来源 id，停用保留数据但阻止导入与同步，本地操作仍可继续', () => {
  let state = importTask(createInitialState());
  const taskId = state.tasks.at(-1).id;
  state = reduce(state, { type: 'UPDATE_CONNECTOR', connectorId: demoId, name: '新名称' });
  assert.equal(state.tasks.at(-1).origin.connectorId, demoId);
  state = reduce(state, { type: 'TOGGLE_CONNECTOR', connectorId: demoId });
  const tasks = structuredClone(state.tasks);
  assert.throws(() => importTask(state), /停用|连接/);
  assert.throws(() => act(state, 'SET_SYNC', { taskId, value: 'synced' }), /停用|连接/);
  state = act(state, 'SET_SYNC', { taskId, value: 'conflict' });
  assert.throws(() => act(state, 'RESOLVE_SYNC', { taskId, choice: 'local' }), /停用|连接/);
  assert.throws(() => act(state, 'RESOLVE_SYNC', { taskId, choice: 'remote' }), /停用|连接/);
  state = act(state, 'RESOLVE_SYNC', { taskId, choice: 'pause' });
  state = act(state, 'UPDATE_TASK', { taskId, title: '本地仍可修改' });
  state = act(state, 'SAVE_DOCUMENT', { taskId, title: '需求.md', kind: '需求', body: '离线整理' });
  state = act(state, 'TOGGLE_PAUSE', { taskId });
  assert.equal(get(state, taskId).status, 'paused');
  assert.equal(state.tasks.length, tasks.length);
  assert.deepEqual(get(state, taskId).origin, tasks.at(-1).origin);
});

test('只读连接允许拉取和本地工作，但所有模拟推送入口都拒绝', () => {
  let state = reduce(createInitialState(), { type: 'UPDATE_CONNECTOR', connectorId: demoId, syncMode: 'read_only' });
  state = importTask(state);
  const taskId = state.tasks.at(-1).id;
  state = act(state, 'UPDATE_TASK', { taskId, title: '本地修改' });
  assert.throws(() => act(state, 'SET_SYNC', { taskId, value: 'synced' }), /只读|双向/);
  state = act(state, 'SET_SYNC', { taskId, value: 'conflict' });
  assert.throws(() => act(state, 'RESOLVE_SYNC', { taskId, choice: 'local' }), /只读|双向/);
  assert.doesNotThrow(() => act(state, 'RESOLVE_SYNC', { taskId, choice: 'remote' }));
});

test('连接身份有引用后冻结，配置白名单拒绝凭据且验证 HTTPS 与项目', () => {
  const state = createInitialState();
  for (const fields of [{ organizationId: 'new-org' }, { endpoint: 'https://example.test/api' }]) {
    assert.throws(() => reduce(state, { type: 'UPDATE_CONNECTOR', connectorId: demoId, ...fields }), /身份|新连接|引用/);
  }
  for (const tokenKey of ['token', 'password', 'apiKey', 'access_token', 'authorization', 'secret']) {
    assert.throws(() => newConnector(state, { [tokenKey]: 'never-store' }), /凭据/);
    assert.throws(() => reduce(state, { type: 'UPDATE_CONNECTOR', connectorId: demoId, [tokenKey]: 'never-store' }), /凭据/);
  }
  for (const endpoint of ['http://example.test', 'https://user:pass@example.test', 'https://example.test?q=secret', 'https://example.test/#fragment', 'not-a-url']) {
    assert.throws(() => newConnector(state, { endpoint }), /HTTPS|地址|endpoint/);
  }
  for (const fields of [{ name: '' }, { organizationId: '' }, { projects: [] }, { projects: [''] }, { syncMode: 'invalid' }]) {
    assert.throws(() => newConnector(state, fields));
  }
  const result = newConnector(state, { endpoint: 'https://example.test/api', arbitrary: 'ignore-me' });
  assert.equal(result.connectors.at(-1).arbitrary, undefined);
  assert.equal(result.connectors.at(-1).endpoint, 'https://example.test/api');
});

test('旧连接只能改名，不可启用测试或修改身份，旧任务保留本地使用能力', () => {
  let state = createInitialState();
  delete state.connectors;
  delete get(state).origin;
  state = act(state, 'UPDATE_TASK', { title: '旧任务本地标题' });
  const connectorId = get(state).origin.connectorId;
  assert.equal(connectorId, 'connector-yunxiao-legacy');
  state = reduce(state, { type: 'UPDATE_CONNECTOR', connectorId, name: '保留来源' });
  for (const action of [
    { type: 'TOGGLE_CONNECTOR' }, { type: 'TEST_CONNECTOR', outcome: 'connected' },
    { type: 'UPDATE_CONNECTOR', projects: ['成员中心'] }, { type: 'UPDATE_CONNECTOR', organizationId: 'new' },
  ]) assert.throws(() => reduce(state, { ...action, connectorId }), /旧|来源|配置/);
  assert.throws(() => act(state, 'SET_SYNC', { value: 'synced' }), /连接|配置/);
});

test('新手工文档、Agent产出、会话、工作区与事件各记录准确来源', () => {
  let state = importTask(createInitialState());
  const taskId = state.tasks.at(-1).id;
  state = act(state, 'SAVE_DOCUMENT', { taskId, title: '需求.md', kind: '需求', body: '手工编写' });
  assert.deepEqual(get(state, taskId).docs.at(-1).origin, { kind: 'local', system: 'reed', actor: 'manual' });
  state = act(state, 'PREPARE_WORKSPACE', { taskId });
  assert.deepEqual(get(state, taskId).workspace.origin, { kind: 'local', system: 'git', repo: 'member-service' });
  assert.deepEqual(state.branches.at(-1).origin, { kind: 'local', system: 'git', repo: 'member-service' });
  state = act(state, 'BIND_SESSION', { taskId, host: 'Claude Code' });
  assert.deepEqual(state.sessions.at(-1).origin, { kind: 'host', host: 'Claude Code' });
  state = act(state, 'START_STAGE', { taskId });
  state = act(state, 'FINISH_STAGE', { taskId, outcome: 'review' });
  assert.deepEqual(get(state, taskId).docs.at(-1).origin, { kind: 'host', host: 'Claude Code' });
  assert.deepEqual(state.events.at(-1).origin, { kind: 'local', system: 'reed' });
});

test('刚创建的本地和导入任务连未准备的工作区也有自身本地 Git 来源', () => {
  const created = act(createInitialState(), 'CREATE_TASK', { title: '全新任务' });
  assert.deepEqual(created.tasks.at(-1).origin, { kind: 'local', system: 'reed' });
  assert.deepEqual(created.tasks.at(-1).workspace.origin, { kind: 'local', system: 'git', repo: 'member-service' });
  const imported = importTask(createInitialState());
  assert.deepEqual(imported.tasks.at(-1).workspace.origin, { kind: 'local', system: 'git', repo: 'member-service' });
});

test('未知或模拟失败连接不能导入或同步，非法操作不修改输入', () => {
  let state = createInitialState();
  assert.throws(() => importTask(state, 'missing'), /连接/);
  state = reduce(state, { type: 'TEST_CONNECTOR', connectorId: demoId, outcome: 'error' });
  const before = structuredClone(state);
  assert.throws(() => importTask(state), /连接/);
  assert.throws(() => act(state, 'SET_SYNC', { value: 'synced' }), /连接/);
  assert.throws(() => reduce(state, { type: 'TEST_CONNECTOR', connectorId: demoId, outcome: 'invalid' }), /结果/);
  assert.deepEqual(state, before);
});

test('无引用连接修改组织或地址后必须重新测试，修改显示与同步配置保留连接状态', () => {
  for (const identity of [{ organizationId: 'different-org' }, { endpoint: 'https://example.test/api' }]) {
    let state = newConnector(createInitialState());
    const connectorId = state.connectors.at(-1).id;
    state = reduce(state, { type: 'TEST_CONNECTOR', connectorId, outcome: 'connected' });
    state = reduce(state, { type: 'UPDATE_CONNECTOR', connectorId, ...identity });
    assert.equal(state.connectors.at(-1).status, 'disconnected', '新身份尚未经模拟测试，不应沿用旧身份的已连接状态');
    assert.throws(() => importTask(state, connectorId), /连接/);
    state = reduce(state, { type: 'TEST_CONNECTOR', connectorId, outcome: 'connected' });
    assert.doesNotThrow(() => importTask(state, connectorId));
    state = reduce(state, { type: 'UPDATE_CONNECTOR', connectorId, name: '新显示名', organizationName: '新组织显示名', projects: ['成员中心', '其他项目'], syncMode: 'read_only' });
    assert.equal(state.connectors.at(-1).status, 'connected');
    state = reduce(state, { type: 'UPDATE_CONNECTOR', connectorId, ...identity });
    assert.equal(state.connectors.at(-1).status, 'connected', '相同身份重复保存不要求重测');
  }
});

test('连接创建和改名按去空白及英文大小写唯一校验，拒绝时不改来源且保留自己原名', () => {
  let state = newConnector(createInitialState(), { name: '  Team Alpha  ' });
  const alphaId = state.connectors.at(-1).id;
  const before = structuredClone(state);
  assert.throws(() => newConnector(state, { name: ' team ALPHA ' }), /名称|重名|唯一/);
  assert.deepEqual(state, before);
  state = newConnector(state, { name: 'Team Beta' });
  const betaId = state.connectors.at(-1).id;
  const beforeRename = structuredClone(state);
  assert.throws(() => reduce(state, { type: 'UPDATE_CONNECTOR', connectorId: betaId, name: ' TEAM alpha ' }), /名称|重名|唯一/);
  assert.deepEqual(state, beforeRename);
  state = reduce(state, { type: 'UPDATE_CONNECTOR', connectorId: alphaId, name: ' Team Alpha ' });
  assert.equal(state.connectors.find((item) => item.id === alphaId).name, 'Team Alpha');
  assert.deepEqual(state.tasks, before.tasks);
});

test('旧来源改名也拒绝其他连接的名称，但保留自己的名称和原任务来源', () => {
  let state = createInitialState();
  delete get(state).origin;
  state = act(state, 'UPDATE_TASK', { title: '旧任务' });
  const connectorId = get(state).origin.connectorId;
  const legacyName = state.connectors.find((item) => item.id === connectorId).name;
  const before = structuredClone(state);
  assert.throws(() => reduce(state, { type: 'UPDATE_CONNECTOR', connectorId, name: ` ${state.connectors[0].name} ` }), /名称|重名|唯一/);
  assert.deepEqual(state, before);
  state = reduce(state, { type: 'UPDATE_CONNECTOR', connectorId, name: ` ${legacyName} ` });
  assert.equal(state.connectors.find((item) => item.id === connectorId).name, legacyName);
  assert.deepEqual(state.tasks, before.tasks);
});
