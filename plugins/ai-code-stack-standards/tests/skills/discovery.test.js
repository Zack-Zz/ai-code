const assert = require('node:assert/strict');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { test } = require('node:test');

const repository = path.resolve(__dirname, '../../../..');

test('the public catalog discovers CodeStack as an independent plugin', () => {
  const result = spawnSync('python3', ['-B', path.join(repository, 'tooling/plugin_tool.py'), 'list'], {
    cwd: repository,
    encoding: 'utf8',
    timeout: 30000,
  });
  assert.ifError(result.error);
  assert.equal(result.signal, null, result.stderr);
  assert.equal(result.status, 0, result.stderr || result.stdout);

  const catalog = JSON.parse(result.stdout);
  const plugin = catalog.plugins.find((entry) => entry.product_id === 'ai-code-stack-standards');
  assert.ok(plugin, 'The successful public list response must include CodeStack.');
  assert.equal(plugin.display_name, 'CodeStack');
  assert.equal(plugin.path, 'plugins/ai-code-stack-standards');
  assert.deepEqual([...plugin.hosts].sort(), ['claude', 'codex', 'zcode']);
});
