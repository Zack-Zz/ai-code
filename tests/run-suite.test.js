/**
 * Tests for the unified test runner (tests/run-suite.js).
 *
 * The runner must:
 * - execute every group even when an earlier group fails;
 * - decide success purely from subprocess exit status / spawn errors / signal
 *   termination, never from parsing test output;
 * - exit non-zero if any group fails, cannot start, or is killed by a signal;
 * - exit zero only when every group exits zero.
 *
 * Scenarios use throwaway fake test processes in a temp dir; real tests are
 * never modified to manufacture outcomes.
 *
 * Run with: node tests/run-suite.test.js
 */

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const RUNNER = path.join(__dirname, 'run-suite.js');

const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'run-suite-test-'));

function writeScript(name, body) {
  const file = path.join(tmp, name);
  fs.writeFileSync(file, `#!/usr/bin/env node\n${body}\n`);
  return file;
}

/** Run the runner against a groups spec; returns { status, stdout } */
function runRunner(groups) {
  const spec = path.join(tmp, 'spec.json');
  fs.writeFileSync(spec, JSON.stringify(groups));
  const r = spawnSync('node', [RUNNER, spec], { encoding: 'utf8' });
  return { status: r.status, stdout: (r.stdout || '') + (r.stderr || '') };
}

/** A real runner copied into a disposable repository, without recursive self tests. */
function repository(name, entries) {
  const root = path.join(tmp, name);
  fs.mkdirSync(path.join(root, 'tests'), { recursive: true });
  fs.copyFileSync(RUNNER, path.join(root, 'tests/run-suite.js'));
  fs.copyFileSync(path.join(__dirname, 'run_python_tests.py'), path.join(root, 'tests/run_python_tests.py'));
  fs.writeFileSync(path.join(root, 'tests/__init__.py'), '');
  fs.mkdirSync(path.join(root, 'tests/tooling'));
  fs.writeFileSync(path.join(root, 'tests/tooling/__init__.py'), '');
  fs.writeFileSync(path.join(root, 'tests/tooling/test_ok.py'),
    'import unittest\nclass TestTools(unittest.TestCase):\n def test_ok(self): self.assertTrue(True)\n');
  fs.writeFileSync(path.join(root, 'tests/run-suite.test.js'), 'process.exit(0);');
  fs.mkdirSync(path.join(root, 'tests/skills'));
  fs.writeFileSync(path.join(root, 'tests/skills/run-skills.js'), 'process.exit(0);');
  fs.writeFileSync(path.join(root, 'catalog.json'), JSON.stringify({ schema_version: 1, plugins: entries }));
  return root;
}

function plugin(root, relative, status = 0) {
  const folder = path.join(root, relative, 'tests/skills');
  fs.mkdirSync(folder, { recursive: true });
  const marker = path.join(root, `${path.basename(relative)}.marker`);
  fs.writeFileSync(path.join(folder, 'run-skills.js'),
    `require('fs').writeFileSync(${JSON.stringify(marker)}, process.cwd()); process.exit(${status});`);
  return marker;
}

function runRepository(root) {
  const r = spawnSync('node', [path.join(root, 'tests/run-suite.js')], { encoding: 'utf8' });
  return { status: r.status, stdout: (r.stdout || '') + (r.stderr || '') };
}

function test(name, fn) {
  try {
    fn();
    console.log(`  \u2713 ${name}`);
    return true;
  } catch (error) {
    console.log(`  \u2717 ${name}`);
    console.log(`    Error: ${error.message}`);
    return false;
  }
}

function runTests() {
  console.log('\n=== Testing run-suite.js (unified test entry) ===\n');
  let passed = 0;
  let failed = 0;

  // Fake processes print deliberately misleading "Passed:/Failed:" text to
  // prove the runner ignores output and trusts exit statuses only.
  const failQuietly = writeScript('fail-quietly.js',
    'console.log("Passed: 999 Failed: 0"); process.exit(1);');
  const passLoudly = writeScript('pass-loudly.js',
    'console.log("Failed: 77 Passed: 0"); process.exit(0);');
  const plainPass = writeScript('plain-pass.js', 'process.exit(0);');
  const plainFail = writeScript('plain-fail.js', 'process.exit(1);');
  const markerWriter = writeScript('marker-writer.js',
    `require('fs').writeFileSync(${JSON.stringify(path.join(tmp, 'second-ran.marker'))}, 'ok'); process.exit(0);`);
  const selfKill = writeScript('self-kill.js',
    'process.kill(process.pid, "SIGKILL");');
  const missingBin = path.join(tmp, 'definitely-missing-binary');

  const g = (name, cmd, args) => ({ name, cmd, args });

  if (test('first group fails -> second group still executes -> runner fails', () => {
    fs.rmSync(path.join(tmp, 'second-ran.marker'), { force: true });
    const { status } = runRunner([
      g('A', 'node', [failQuietly]),
      g('B', 'node', [markerWriter]),
    ]);
    assert.notStrictEqual(status, 0, 'runner must exit non-zero when group A fails');
    assert.ok(fs.existsSync(path.join(tmp, 'second-ran.marker')),
      'group B must still have executed after group A failed');
  })) passed++; else failed++;

  if (test('second group fails -> runner fails (despite misleading output)', () => {
    const { status } = runRunner([
      g('A', 'node', [passLoudly]),
      g('B', 'node', [plainFail]),
    ]);
    assert.notStrictEqual(status, 0, 'runner must exit non-zero when group B fails');
  })) passed++; else failed++;

  if (test('all groups pass -> runner exits zero (despite misleading output)', () => {
    const { status } = runRunner([
      g('A', 'node', [passLoudly]),
      g('B', 'node', [plainPass]),
    ]);
    assert.strictEqual(status, 0, 'runner must exit zero only when all groups pass');
  })) passed++; else failed++;

  if (test('group cannot start (missing executable) -> runner fails', () => {
    const { status, stdout } = runRunner([
      g('A', 'node', [plainPass]),
      g('B', missingBin, []),
    ]);
    assert.notStrictEqual(status, 0, 'runner must exit non-zero when a group cannot start');
    assert.ok(stdout.includes(missingBin), 'runner should name the group that failed to start');
  })) passed++; else failed++;

  if (test('group terminated by signal -> runner fails', () => {
    const { status } = runRunner([
      g('A', 'node', [plainPass]),
      g('B', 'node', [selfKill]),
    ]);
    assert.notStrictEqual(status, 0, 'runner must exit non-zero when a group is killed by a signal');
  })) passed++; else failed++;

  if (test('empty group list -> runner fails (no vacuous success)', () => {
    const { status, stdout } = runRunner([]);
    assert.notStrictEqual(status, 0, 'an empty test group list must not be reported as success');
    assert.ok(stdout.length > 0, 'runner should explain why an empty group list fails');
  })) passed++; else failed++;

  if (test('default Python gate uses the guarded helper and rejects empty discovery', () => {
    const root = repository('empty-python-root', [{ path: 'plugins/first' }]);
    plugin(root, 'plugins/first');
    fs.rmSync(path.join(root, 'tests/tooling/test_ok.py'));
    const result = runRepository(root);
    assert.notStrictEqual(result.status, 0, 'empty Python discovery must fail the default gate');
    assert.ok(result.stdout.includes('no Python tests discovered'),
      'default gate must invoke the helper with an explicit empty-suite failure');
  })) passed++; else failed++;

  if (test('catalog runs every registered plugin in its own root', () => {
    const root = repository('two-plugins', [{ path: 'plugins/first' }, { path: 'plugins/second' }]);
    const first = plugin(root, 'plugins/first');
    const second = plugin(root, 'plugins/second');
    const result = runRepository(root);
    assert.strictEqual(result.status, 0, result.stdout);
    assert.ok(fs.existsSync(first), 'first registered plugin must run');
    assert.ok(fs.existsSync(second), 'second registered plugin must run');
    assert.strictEqual(fs.readFileSync(first, 'utf8'), fs.realpathSync(path.join(root, 'plugins/first')));
    assert.strictEqual(fs.readFileSync(second, 'utf8'), fs.realpathSync(path.join(root, 'plugins/second')));
  })) passed++; else failed++;

  if (test('failed registered plugin does not suppress the next plugin', () => {
    const root = repository('failing-plugin', [{ path: 'plugins/first' }, { path: 'plugins/second' }]);
    const first = plugin(root, 'plugins/first', 1);
    const second = plugin(root, 'plugins/second');
    const result = runRepository(root);
    assert.notStrictEqual(result.status, 0);
    assert.ok(fs.existsSync(first), 'failing plugin must have run');
    assert.ok(fs.existsSync(second), 'following plugin must still run');
  })) passed++; else failed++;

  if (test('registered plugin without known test groups fails the gate', () => {
    const root = repository('missing-plugin-tests', [{ path: 'plugins/first' }]);
    fs.mkdirSync(path.join(root, 'plugins/first/tests'), { recursive: true });
    const result = runRepository(root);
    assert.notStrictEqual(result.status, 0);
    assert.ok(result.stdout.includes('no test groups'), result.stdout);
  })) passed++; else failed++;

  if (test('empty catalog cannot report a passing plugin gate', () => {
    const root = repository('empty-catalog', []);
    assert.notStrictEqual(runRepository(root).status, 0);
  })) passed++; else failed++;

  if (test('catalog rejects traversal and duplicate registration', () => {
    for (const [name, entries] of [
      ['traversal', [{ path: '../escape' }]],
      ['duplicates', [{ path: 'plugins/first' }, { path: 'plugins/first' }]],
      ['unknown-entry', [{ path: 'plugins/first', command: 'anything' }]],
    ]) {
      const root = repository(name, entries);
      plugin(root, 'plugins/first');
      assert.notStrictEqual(runRepository(root).status, 0, name);
    }
  })) passed++; else failed++;

  if (test('symlinked registered roots and test runners cannot execute outside the repository', () => {
    const outside = path.join(tmp, 'outside');
    const marker = plugin(tmp, 'outside');
    const root = repository('symlink-root', [{ path: 'plugins/first' }]);
    fs.mkdirSync(path.join(root, 'plugins'));
    fs.symlinkSync(outside, path.join(root, 'plugins/first'));
    assert.notStrictEqual(runRepository(root).status, 0);
    assert.ok(!fs.existsSync(marker), 'outside root runner must not execute');
    const root2 = repository('symlink-runner', [{ path: 'plugins/first' }]);
    fs.mkdirSync(path.join(root2, 'plugins/first/tests'), { recursive: true });
    fs.symlinkSync(path.join(outside, 'tests/skills'), path.join(root2, 'plugins/first/tests/skills'));
    assert.notStrictEqual(runRepository(root2).status, 0);
    assert.ok(!fs.existsSync(marker), 'outside symlinked runner must not execute');
  })) passed++; else failed++;

  console.log(`\nPassed: ${passed}`);
  console.log(`Failed: ${failed}`);

  fs.rmSync(tmp, { recursive: true, force: true });
  process.exit(failed > 0 ? 1 : 0);
}

runTests();
