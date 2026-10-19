const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { test } = require('node:test');

function runFixture(files) {
  const directory = fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()), 'codestack-runner-'));
  try {
    fs.copyFileSync(path.join(__dirname, 'run-skills.js'), path.join(directory, 'run-skills.js'));
    for (const [name, body] of Object.entries(files)) {
      fs.writeFileSync(path.join(directory, name), body);
    }
    return spawnSync(process.execPath, [path.join(directory, 'run-skills.js')], {
      encoding: 'utf8', timeout: 30000,
    });
  } finally {
    fs.rmSync(directory, { recursive: true, force: true });
  }
}

test('an empty contract group fails', () => {
  const result = runFixture({});
  assert.ifError(result.error);
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /no contract test files/);
});

test('a real passing child succeeds', () => {
  const result = runFixture({
    'passing.test.js': "require('node:test').test('passes', () => require('node:assert/strict').equal(2 + 2, 4));\n",
  });
  assert.ifError(result.error);
  assert.equal(result.status, 0, result.stderr + result.stdout);
});

test('a failing child cannot be hidden by passing output or a passing sibling', () => {
  const result = runFixture({
    'passing.test.js': "require('node:test').test('passes', () => {});\n",
    'failing.test.js': "console.log('ALL TESTS PASSED'); process.exit(7);\n",
  });
  assert.ifError(result.error);
  assert.equal(result.status, 7);
});

test('a signalled child fails the group', () => {
  const result = runFixture({
    'signal.test.js': "process.kill(process.pid, 'SIGTERM');\n",
  });
  assert.ifError(result.error);
  assert.equal(result.status, 1);
});
