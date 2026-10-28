const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { pathToFileURL } = require('node:url');

(async () => {
  // Unit boundary: only the native lifecycle hooks are supplied by stand-ins.
  // The separate native-api entry verifies real Cordis injection and the Loader.
  const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'codevow-preset-'));
  const fixture = (name, source) => {
    const root = path.join(temp, 'node_modules', '@deepseek-ai', name);
    fs.mkdirSync(root, { recursive: true });
    fs.writeFileSync(path.join(root, 'package.json'), JSON.stringify({ type: 'module', exports: './index.js' }));
    fs.writeFileSync(path.join(root, 'index.js'), source);
  };
  try {
    fixture('cordis', "export const Service = { init: Symbol.for('test.codevow.init') };");
    fixture('dsh-agent-preset', `
      import { Service } from '@deepseek-ai/cordis';
      export default class AgentPreset {
        static inject = ['agentPresets'];
        static Config = { native: true };
        static [Symbol.for('cordis.group')] = true;
        constructor(ctx, config) { this.ctx = ctx; this.config = config; }
        async *[Service.init]() { yield await this.ctx.agentPresets.register(this.config); }
      }
    `);
    const target = path.join(temp, 'preset.mjs');
    fs.copyFileSync(path.join(__dirname, '../../adapters/dsh/reviewer-preset.js'), target);
    const { default: ReviewerPreset } = await import(pathToFileURL(target));
    const init = Symbol.for('test.codevow.init');
    assert.deepEqual(ReviewerPreset.inject, ['agentPresets']);
    assert.deepEqual(ReviewerPreset.Config, { native: true });
    assert.equal(ReviewerPreset[Symbol.for('cordis.group')], true);

    const entered = Promise.withResolvers();
    const registration = Promise.withResolvers();
    const revoked = Promise.withResolvers();
    const stopDelegation = Promise.withResolvers();
    const events = [];
    const effects = [];
    let registered = false;
    let published = false;
    const ctx = {
      agentPresets: {
        async register(config) {
          assert.equal(config.id, 'codevow-reviewer');
          entered.resolve();
          await registration.promise;
          registered = true;
          events.push('register');
          return () => {
            assert.equal(published, false);
            registered = false;
            events.push('unregister');
          };
        },
      },
      provide(name, value) {
        assert.equal(name, 'codevowReviewerPresetRegistered');
        assert.equal(value, true);
        assert.equal(registered, true, 'a dependent must never observe readiness before registration');
        published = true;
        events.push('publish');
        return async () => {
          published = false;
          events.push('revoke');
          revoked.resolve();
          await stopDelegation.promise;
          events.push('delegation-stopped');
        };
      },
      async effect(run) {
        const disposers = [];
        effects.push(disposers);
        for await (const dispose of run()) disposers.push(dispose);
      },
    };
    const loading = new ReviewerPreset(ctx, { id: 'codevow-reviewer', plugins: [] })[init]();
    await entered.promise;
    assert.equal(published, false, 'parallel consumers must wait while registration is blocked');
    registration.resolve();
    await loading;
    assert.equal(published, true);
    // Cordis unloads independent effects concurrently, but each effect's children
    // must stop in reverse order. The registered preset must outlive delegation.
    const unloading = Promise.all(effects.map(async disposers => {
      for (const dispose of [...disposers].reverse()) await dispose();
    }));
    await revoked.promise;
    assert.equal(registered, true, 'preset removal must await dependent delegation cleanup');
    stopDelegation.resolve();
    await unloading;
    assert.deepEqual(events, ['register', 'publish', 'revoke', 'delegation-stopped', 'unregister']);
    assert.equal(registered, false);

    let failuresPublished = 0;
    const broken = {
      ...ctx,
      agentPresets: { register: async () => { throw new Error('registration rejected'); } },
      provide: () => { failuresPublished++; },
    };
    await assert.rejects(new ReviewerPreset(broken, { id: 'codevow-reviewer', plugins: [] })[init](),
      /registration rejected/);
    assert.equal(failuresPublished, 0, 'a registration failure must not admit delegation');
    console.log('Reviewer registration readiness and ordered cleanup unit contracts passed');
  } finally { fs.rmSync(temp, { recursive: true, force: true }); }
})().catch(error => { console.error(error); process.exitCode = 1; });
