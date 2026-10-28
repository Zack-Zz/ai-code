import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { createRequire } from 'node:module';
import { pathToFileURL } from 'node:url';

/** Load the unmodified built overlays and every real Reviewer plugin, without a model. */
export async function checkNativePreset({ modules, repository, temporary, pass }) {
  const requireNative = createRequire(path.join(path.dirname(modules), 'codevow-preset-check.cjs'));
  const load = name => import(pathToFileURL(requireNative.resolve(name)).href);
  const built = path.join(temporary, 'bundles');
  const build = spawnSync('python3', [path.join(repository, 'tooling/plugin_tool.py'),
    'build', '--all', '--host', 'dsh', '--output', built], {
    cwd: repository, encoding: 'utf8', timeout: 60000,
    env: { ...process.env, PYTHONDONTWRITEBYTECODE: '1' },
  });
  assert.equal(build.status, 0, build.error?.message || build.stderr || build.stdout);
  const dependencies = path.join(temporary, 'node_modules');
  fs.mkdirSync(dependencies);
  fs.symlinkSync(path.join(modules, '@deepseek-ai'), path.join(dependencies, '@deepseek-ai'));
  for (const id of ['codevow', 'codestack']) {
    fs.symlinkSync(path.join(built, 'dsh', id), path.join(dependencies, id));
  }
  const { Context } = await load('@deepseek-ai/cordis');
  const { loadOverlayPatches, composeEntries } = await load('@deepseek-ai/dsh-app-boot');
  const { createScope } = await load('@deepseek-ai/dsh-scope');
  const requireBuilt = createRequire(path.join(temporary, 'codevow-built-check.cjs'));
  const { default: ReviewerPreset } = await import(pathToFileURL(requireBuilt.resolve('codevow/reviewer-preset')));
  const broken = new Context();
  try {
    broken.provide('agentPresets', { register: async () => { throw new Error('preset registration rejected'); } });
    const loading = broken.plugin(ReviewerPreset, { id: 'codevow-reviewer', plugins: [] });
    await assert.rejects(async () => await loading, /preset registration rejected/);
    assert.equal(broken.get('codevowReviewerPresetRegistered'), undefined);
    pass('a failed native preset registration does not publish delegation readiness');
  } finally { await broken.fiber.dispose(); }
  const cancelled = new Context();
  const entered = Promise.withResolvers();
  const finish = Promise.withResolvers();
  let unregistered = 0;
  try {
    cancelled.provide('agentPresets', { register: async () => {
      entered.resolve();
      await finish.promise;
      return () => { unregistered++; };
    } });
    const loading = cancelled.plugin(ReviewerPreset, { id: 'codevow-reviewer', plugins: [] });
    await entered.promise;
    const disposing = loading.ctx.fiber.dispose();
    finish.resolve();
    await disposing;
    assert.equal(cancelled.get('codevowReviewerPresetRegistered'), undefined);
    assert.equal(unregistered, 1, 'registration completing during unload must be cleaned exactly once');
    pass('native unload during registration leaves neither readiness nor a leaked preset');
  } finally { finish.resolve(); await cancelled.fiber.dispose(); }
  const ctx = new Context();
  ctx.baseUrl = `${pathToFileURL(temporary).href}/`;
  try {
    for (const [name, config] of [
      ['@deepseek-ai/cordis-plugin-loader'], ['@deepseek-ai/dsh-system-prompt', {}],
      ['@deepseek-ai/dsh-tools', { mode: 'native' }], ['@deepseek-ai/dsh-agent'],
      ['@deepseek-ai/dsh-session-projection'], ['@deepseek-ai/dsh-fs'],
      ['@deepseek-ai/dsh-subprocess'], ['@deepseek-ai/dsh-working-directory', { defaultDirectory: temporary }],
      ['@deepseek-ai/dsh-subagent', {}], ['@deepseek-ai/dsh-skill'],
      ['@deepseek-ai/dsh-agent-preset-registry', { default: 'codevow-reviewer' }],
    ]) {
      const module = await load(name);
      await ctx.plugin(module.default ?? module, config);
    }
    ctx.subagents.registerProvider({
      name: 'spawn', inheritsParentContext: false,
      capabilities: { agentPreset: true, depthLimit: true, agentOptions: false, outputSchema: false },
      start: async () => { throw new Error('the startup fixture must not execute a model'); },
    });
    const overlays = ['codevow', 'codestack'].map(id => loadOverlayPatches('dsh',
      path.join(built, 'dsh', id, 'cordis.patch.yml')));
    const entries = composeEntries(overlays);
    // The native Loader persists disabled flags into its entry options on disposal.
    const update = rows => ctx.loader.root.update(structuredClone(rows));
    const spawnEntry = entries.find(row => row.id === 'codevow-reviewer-spawn');
    const presetEntry = entries.find(row => row.id === 'codevow-reviewer-preset');
    const spawnFiber = () => [...ctx.loader.entries()].find(row => row.options.id === spawnEntry.id).fiber;
    const assertDelegation = () => {
      assert.ok(spawnFiber(), JSON.stringify([...ctx.loader.entries()].map(row => ({
        id: row.id, disabled: row.disabled, state: row.fiber?.state, error: row.fiber?._error?.message,
      }))));
      assert.equal(spawnFiber().state, 2, spawnFiber()._error?.stack);
      assert.ok(ctx.tools.get('workflow_reviewer'), 'the Reviewer delegation tool must actually be registered');
    };
    // Force the reachable parallel-start interleaving: delegation is encountered
    // before its sibling preset has registered. No timer or import speed decides it.
    await update(entries.map(row => row === presetEntry ? { ...row, disabled: true } : row));
    await ctx.loader.await();
    assert.equal(spawnFiber().state, 0,
      `delegation must wait for its preset, rather than fail: ${spawnFiber()._error?.message}`);
    assert.equal(ctx.tools.get('workflow_reviewer'), undefined);
    await update([spawnEntry, ...entries.filter(row => row !== spawnEntry)]);
    await ctx.loader.await();
    assertDelegation();
    pass('Reviewer delegation waits for a late preset and activates through the real Loader');

    await update(entries.map(row => row === presetEntry ? { ...row, disabled: true } : row));
    await ctx.loader.await();
    assert.equal(ctx.tools.get('workflow_reviewer'), undefined,
      'removing the preset must revoke delegation before unregistering the definition');
    await update([spawnEntry, ...entries.filter(row => row !== spawnEntry)]);
    await ctx.loader.await();
    assertDelegation();
    pass('preset unload and re-enable revoke and restore the actual delegation tool');

    const oldFibers = [...ctx.loader.entries()].map(row => row.fiber).filter(Boolean);
    await update([]);
    // Removed entries no longer belong to loader.await()'s live tree.
    await Promise.all(oldFibers.map(fiber => fiber.dispose()));
    await ctx.loader.await();
    assert.equal(ctx.tools.get('workflow_reviewer'), undefined);
    await update([spawnEntry, ...entries.filter(row => row !== spawnEntry)]);
    await ctx.loader.await();
    assertDelegation();
    pass('parallel cold loading with delegation listed first still activates the complete bundle');
    const preset = (await ctx.agentPresets.list()).find(row => row.id === 'codevow-reviewer');
    assert.ok(preset, 'the built overlay must register the Reviewer preset');
    assert.equal(preset.broken, undefined, `Reviewer activation failed: ${preset.broken}`);
    pass('the official RC2 Loader activates the complete built Reviewer preset');

    const agent = { id: 'preset-regression', session: { id: 'preset-regression' } };
    let scope;
    await ctx.plugin(Object.assign(owner => { scope = createScope(owner, agent); }, {
      inject: ['loader', 'agentPresets', 'agents', 'tools', 'systemPrompt'],
    }));
    agent.ctx = scope.ctx;
    assert.deepEqual(await ctx.agentPresets.mount(agent.ctx, 'codevow-reviewer'), { id: 'codevow-reviewer' });
    const disposeAgent = await ctx.agents.register(agent);
    try {
      assert.equal(ctx.agentPresets.composedPreset(agent.ctx), 'codevow-reviewer');
      assert.deepEqual(ctx.tools.schemas(agent).map(tool => tool.name).sort(), ['glob', 'grep', 'read']);
      pass('the real preset mounts and exposes only its actual read, grep and glob tools');
    } finally {
      await disposeAgent();
      await scope.dispose();
    }
    const skills = (await ctx.skills.list({ cwd: temporary })).map(skill => [skill.name, skill.provider]);
    assert.deepEqual(skills.sort(), [
      ['code-standards', 'codestack'], ['debugging', 'codevow'], ['review', 'codevow'],
      ['review-results', 'codevow'], ['tdd', 'codevow'], ['verification', 'codevow'], ['workflow', 'codevow'],
    ].sort());
    pass('both built overlays retain all seven skills and their provider identities');
  } finally {
    await ctx.fiber.dispose();
  }
}
