#!/usr/bin/env node
/** Isolated published-API composition, without models or a user profile.
 * DSH_NATIVE_NODE_MODULES=/absolute/isolated/node_modules node tests/dsh/native-api.mjs
 * Missing dependencies fail; the ordinary contract runner does not invoke this entry.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { createRequire } from 'node:module';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { checkNativePreset } from './native-preset.mjs';

const modules = process.env.DSH_NATIVE_NODE_MODULES;
assert.ok(modules && path.isAbsolute(modules) && fs.statSync(modules).isDirectory(),
  'DSH_NATIVE_NODE_MODULES must name an existing isolated node_modules directory');
const requireNative = createRequire(path.join(path.dirname(modules), 'codevow-api-check.cjs'));
const load = name => import(pathToFileURL(requireNative.resolve(name)).href);
const version = name => JSON.parse(fs.readFileSync(requireNative.resolve(`${name}/package.json`))).version;
const expected = '0.2.1-rc.2';
const dependencies = ['scope', 'tools', 'system-prompt', 'agent', 'skill', 'skill-filesystem',
  'agent-tool-presentation', 'tool-subagent', 'app-boot', 'agent-preset-registry',
  'session-projection', 'fs', 'subprocess', 'working-directory', 'subagent'];
for (const dependency of dependencies) assert.equal(version(`@deepseek-ai/dsh-${dependency}`), expected);
assert.equal(version('@deepseek-ai/cordis'), '4.0.5');
assert.equal(version('@deepseek-ai/cordis-plugin-loader'), '1.0.6');
const { Context } = await load('@deepseek-ai/cordis');
const { evaluatePluginCompatibility } = await load('@deepseek-ai/dsh-app-boot');
const { createScope, bindScopeParent } = await load('@deepseek-ai/dsh-scope');
const { default: SystemPrompt } = await load('@deepseek-ai/dsh-system-prompt');
const { default: Tools, defineContentToolFixture } = await load('@deepseek-ai/dsh-tools');
const { default: Agents } = await load('@deepseek-ai/dsh-agent');
const { default: Skills, renderSkillContent } = await load('@deepseek-ai/dsh-skill');
const SkillFilesystem = await load('@deepseek-ai/dsh-skill-filesystem');
const NativePresentation = await load('@deepseek-ai/dsh-agent-tool-presentation');
const ToolSubagent = await load('@deepseek-ai/dsh-tool-subagent');
const yaml = requireNative('js-yaml');
const pluginRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const repository = path.resolve(pluginRoot, '../..');
const temporary = fs.mkdtempSync(path.join(path.dirname(modules), '.codevow-native-api-'));
let count = 0;
const pass = message => { count++; console.log(`PASS ${count}: ${message}`); };
const ctx = new Context();
const fibers = [];
const mount = async (plugin, config) => {
  const fiber = await ctx.plugin(plugin, config);
  fibers.push(fiber);
  return fiber;
};
try {
  await checkNativePreset({ modules, repository, temporary, pass });
  const expressionTag = new yaml.Type('tag:yaml.org,2002:js', {
    kind: 'scalar', construct: expression => ({ expression }),
  });
  const schema = yaml.DEFAULT_SCHEMA.extend([expressionTag]);
  const patch = yaml.load(fs.readFileSync(path.join(pluginRoot, 'adapters/dsh/cordis.patch.yml'), 'utf8'), { schema });
  const rows = patch.flatMap(operation => operation.insert || []);
  const reviewerConfig = rows.find(row => row.id === 'codevow-reviewer-spawn').config;
  const validated = await ToolSubagent.Config['~standard'].validate(reviewerConfig);
  assert.ok(!validated.issues, JSON.stringify(validated.issues));
  assert.equal(validated.value.modelSelectionSettings, false);
  assert.equal(validated.value.agentPreset, 'codevow-reviewer');
  assert.equal(validated.value.allowedAgentPresets, undefined);
  assert.deepEqual(Object.keys(reviewerConfig).sort(), ['agentPreset', 'modelSelectionSettings', 'provider', 'toolName']);
  const preset = rows.find(row => row.id === 'codevow-reviewer-preset').config;
  const presentation = preset.plugins.find(row => row.id === 'codevow-reviewer-executor');
  assert.equal(presentation.name, '@deepseek-ai/dsh-agent-tool-presentation');
  assert.deepEqual((await NativePresentation.Config['~standard'].validate(presentation.config)).value, { mode: 'native' });
  pass('the actual patch uses published RC2 preset selection and native presentation schemas');
  for (const id of ['codevow', 'codestack']) {
    const manifest = JSON.parse(fs.readFileSync(path.join(repository, 'plugins', id, 'adapters/dsh/package.json')));
    const product = JSON.parse(fs.readFileSync(path.join(repository, 'plugins', id, 'product.json')));
    const bundle = { ...manifest, name: id, version: product.version };
    for (const [name, requirement] of Object.entries(manifest.peerDependencies)) {
      if (name === '@deepseek-ai/cordis') {
        assert.equal(requirement, '~4.0.5');
        continue;
      }
      assert.equal(requirement, manifest.engines.dsh);
      assert.equal(evaluatePluginCompatibility({ name: id, version: product.version,
        peerDependencies: { [name]: requirement } }, {}, version(name)), undefined);
    }
    const peerOnly = { ...bundle };
    delete peerOnly.engines;
    for (const [runtime, supported] of [
      ['0.2.0', false], ['0.2.1-rc.1', false], ['0.2.1-rc.2', true],
      ['0.2.1-rc.3', true], ['0.2.1', true], ['0.2.2-rc.1', true], ['0.2.2', true],
    ]) {
      for (const declaration of [bundle, peerOnly]) {
        const issue = evaluatePluginCompatibility(declaration, {}, runtime);
        assert.equal(issue === undefined, supported, `${id} runtime ${runtime}: ${JSON.stringify(issue)}`);
      }
    }
    assert.equal(manifest.engines.dsh, `>=${expected}`);
  }
  pass('both bundles reject runtimes below RC2 and accept RC2, RC3 and later versions through the official matcher');

  // Copy the exact source module beneath this isolated dependency tree, without rewriting imports.
  fs.copyFileSync(path.join(pluginRoot, 'adapters/dsh/reviewer-guard.js'), path.join(temporary, 'guard.mjs'));
  const Guard = await import(pathToFileURL(path.join(temporary, 'guard.mjs')).href);
  await mount(SystemPrompt, {});
  await mount(Tools, { mode: 'native' });
  await mount(Agents);
  await mount(Skills);
  const providers = [];
  for (const id of ['codevow', 'codestack']) providers.push(await mount(SkillFilesystem, {
    providerName: id, includeDefaultRoots: false, watch: false,
    bundledSkillDir: path.join(repository, 'plugins', id, 'skills'),
  }));
  assert.deepEqual((await ctx.skills.list({ cwd: temporary })).map(skill => skill.name).sort(),
    ['code-standards', 'debugging', 'review', 'review-results', 'tdd', 'verification', 'workflow']);
  pass('two official filesystem providers coexist with only bundled skill roots');
  const workflow = await ctx.skills.get('workflow', { cwd: temporary });
  assert.equal(workflow.provider, 'codevow');
  assert.equal(workflow.resourceBase.kind, 'directory');
  assert.equal(workflow.resourceBase.path, path.join(pluginRoot, 'skills/workflow'));
  assert.ok([...renderSkillContent(workflow)].length < 8192);
  assert.ok(fs.existsSync(path.join(workflow.resourceBase.path, 'references/execution.md')));
  pass(`official skill rendering retains resourceBase and fits pruning budget (${[...renderSkillContent(workflow)].length} code points)`);
  let forbiddenRuns = 0;
  const definitions = new Map();
  const register = name => {
    const dispose = ctx.tools.register(defineContentToolFixture({ name, description: `fixture ${name}`,
      parameters: {}, execute: async () => {
        if (!['read', 'grep', 'glob'].includes(name)) forbiddenRuns++;
        return [{ type: 'text', text: `ran:${name}` }];
      } }));
    definitions.set(name, dispose);
  };
  for (const name of ['read', 'grep', 'glob', 'write', 'bash', 'workflow_reviewer', 'web_search']) register(name);
  const reviewerKey = {};
  const standardKey = {};
  let composition;
  await mount(Object.assign(inner => { composition = createScope(inner, reviewerKey); },
    { inject: ['tools', 'systemPrompt', 'agents'] }));
  await composition.ctx.plugin(NativePresentation, { mode: 'native' });
  const guard = await composition.ctx.plugin(Guard);
  const makeAgent = async (id, parent) => {
    const agent = { id, session: { id } };
    const binding = bindScopeParent(agent, parent);
    let scope;
    await mount(Object.assign(inner => { scope = createScope(inner, agent); },
      { inject: ['tools', 'systemPrompt', 'agents'] }));
    agent.ctx = scope.ctx;
    const dispose = await ctx.agents.register(agent);
    return { agent, scope, binding, dispose };
  };
  const reviewer = await makeAgent('reviewer', reviewerKey);
  const names = agent => ctx.tools.schemas(agent).map(tool => tool.name).sort();
  assert.deepEqual(names(reviewer.agent), ['glob', 'grep', 'read']);
  pass('native serial agent creation restricts the first tool surface');
  const call = (agent, name) => ctx.tools.execute({ callId: `call-${name}`, name,
    arguments: {}, agent, signal: new AbortController().signal });
  assert.equal((await call(reviewer.agent, 'read')).isError, false);
  for (const name of ['write', 'bash', 'workflow_reviewer', 'web_search']) {
    assert.equal((await call(reviewer.agent, name)).isError, true);
  }
  assert.equal(forbiddenRuns, 0);
  pass('native dispatch rejects hidden write, shell, delegation and web calls');
  const ownWrite = reviewer.agent.ctx.tools.register(defineContentToolFixture({ name: 'write',
    description: 'own-scope bypass probe', parameters: {}, execute: async () => {
      forbiddenRuns++; return [{ type: 'text', text: 'bypass' }];
    } }));
  const blocked = await call(reviewer.agent, 'write');
  assert.equal(blocked.isError, true);
  assert.match(JSON.stringify(blocked), /CodeVow Reviewer/);
  assert.equal(forbiddenRuns, 0);
  ownWrite();
  pass('composition guard denies even an own-scope tool exempt from restrict');
  reviewer.binding.rebind(standardKey);
  ctx.emit('tools/change');
  assert.ok(names(reviewer.agent).includes('bash'));
  assert.equal((await call(reviewer.agent, 'write')).isError, false);
  reviewer.binding.rebind(reviewerKey);
  ctx.emit('tools/change');
  assert.deepEqual(names(reviewer.agent), ['glob', 'grep', 'read']);
  pass('blank-session scope recomposition releases and reinstalls restrictions');
  const normal = await makeAgent('normal', standardKey);
  assert.ok(names(normal.agent).includes('bash'));
  assert.equal((await call(normal.agent, 'write')).isError, false);
  pass('an unrelated standard agent retains native tool access');
  await guard.dispose();
  assert.ok(names(reviewer.agent).includes('bash'));
  const restored = await composition.ctx.plugin(Guard);
  assert.deepEqual(names(reviewer.agent), ['glob', 'grep', 'read']);
  pass('unload cleans agent effects and reload reconciles existing agents');
  definitions.get('glob')();
  await assert.rejects(makeAgent('missing-tool', reviewerKey), /unknown.*glob/);
  assert.equal(ctx.agents.get('missing-tool'), undefined);
  register('glob');
  assert.equal((await call(reviewer.agent, 'bash')).isError, true);
  pass('native failed creation rolls back and keeps the final guard active');
  await reviewer.dispose();
  assert.equal(ctx.agents.get('reviewer'), undefined);
  await restored.dispose();
  await normal.dispose();
  pass('native agent disposal completes without retaining registry entries');
  await providers[0].dispose();
  assert.deepEqual((await ctx.skills.list({ cwd: temporary })).map(skill => skill.name), ['code-standards']);
  await providers[1].dispose();
  assert.deepEqual(await ctx.skills.list({ cwd: temporary }), []);
  pass('provider unload removes only its own skills and closes both providers');
  console.log(JSON.stringify({ ok: true, checks: count, dsh: expected, cordis: version('@deepseek-ai/cordis'),
    boundary: 'real built overlays and Loader/Preset activation, plus Cordis/Tools/AgentRegistry/Skill APIs with synthetic agents; no model, profile or real filesystem-tool execution acceptance' }));
} finally {
  for (const fiber of fibers.reverse()) await fiber.dispose();
  fs.rmSync(temporary, { recursive: true, force: true });
}
