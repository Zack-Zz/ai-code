const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { pathToFileURL } = require('node:url');
(async () => {
  // Unit boundary only: scope identity is supplied by this minimal native API stand-in.
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'codevow-guard-'));
  try {
    const source = fs.readFileSync(path.join(__dirname, '../../adapters/dsh/reviewer-guard.js'), 'utf8');
    fs.writeFileSync(path.join(temp, 'guard.mjs'), source.replace("import { scopeChainOf, scopeOf } from '@deepseek-ai/dsh-scope'", "const scopeOf = ctx => ctx.scope; const scopeChainOf = scope => scope?.chain || []"));
    const { apply } = await import(pathToFileURL(path.join(temp, 'guard.mjs')));
    const composition = {};
    const listeners = new Map();
    const agents = [];
    const effects = [];
    const guards = [];
    let restrictions = 0;
    let released = 0;
    let failRestriction = false;
    const ctx = {
      scope: composition,
      agents: { list: () => agents },
      get(key) { return this[key]; },
      on: (name, fn) => { listeners.set(name, fn); return () => listeners.delete(name); },
      effect: fn => effects.push(fn()),
      logger: { warn() {} },
      tools: { guard: fn => { guards.push(fn); return () => guards.splice(guards.indexOf(fn), 1); } },
    };
    const reviewer = { id: 'review', ctx: { scope: { chain: [composition] }, tools: { restrict: ({ allow }) => {
      assert.deepEqual(allow, ['read', 'grep', 'glob']);
      if (failRestriction) throw Error('unknown read tool');
      restrictions++;
      listeners.get('tools/change')?.(); // The native registry emits synchronously: must be idempotent.
      return () => { released++; listeners.get('tools/change')?.(); };
    } } } };
    agents.push(reviewer);
    apply(ctx);
    assert.equal(guards.length, 1, 'final guard must be installed before admitting work');
    assert.equal(restrictions, 1, 'restored reviewer must be restricted exactly once');
    for (const tool of ['bash', 'write', 'workflow_reviewer', 'web_search', 'subagent']) {
      assert.match(guards[0]({ name: tool }), /CodeVow Reviewer/);
    }
    assert.equal(guards[0]({ name: 'read' }), undefined);
    reviewer.ctx.scope.chain = [];
    listeners.get('tools/change')();
    assert.equal(released, 1, 'leaving preset must release restriction');
    reviewer.ctx.scope.chain = [composition];
    listeners.get('tools/change')();
    assert.equal(restrictions, 2);
    listeners.get('agent/disposed')({ agent: reviewer });
    assert.equal(released, 2);
    agents.length = 0;
    const newReviewer = { ...reviewer, id: 'new-reviewer' };
    failRestriction = true;
    await assert.rejects(listeners.get('agent/created')({ agent: newReviewer }), /unknown read tool/);
    assert.equal(guards.length, 1, 'failure must retain final denial');
    failRestriction = false;
    agents.push(newReviewer);
    await listeners.get('agent/created')({ agent: newReviewer });
    effects.reverse().forEach(dispose => dispose());
    assert.equal(released, 3, 'unload must release agent-owned effects');
    assert.equal(guards.length, 0);
    assert.throws(() => apply({ ...ctx, scope: undefined }), /scope/);
    assert.throws(() => apply({ ...ctx, agents: undefined }), /agents/);
    console.log('Reviewer lifecycle and final denial unit contracts passed (not native host acceptance)');
  } finally { fs.rmSync(temp, { recursive: true, force: true }); }
})().catch(error => { console.error(error); process.exitCode = 1; });
