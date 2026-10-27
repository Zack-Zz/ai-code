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
    const overlays = ['codevow', 'codestack'].map(id => loadOverlayPatches('dsh',
      path.join(built, 'dsh', id, 'cordis.patch.yml')));
    await ctx.loader.root.update(composeEntries(overlays));
    await ctx.loader.await();
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
