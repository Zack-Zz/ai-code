const assert = require('node:assert/strict');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { test } = require('node:test');

test('frontend oracle calibration rejects contract regressions without scoring model behavior', () => {
  const script = path.resolve(__dirname, '../../evals/fixtures/frontend-i18n/calibrate.js');
  const result = spawnSync(process.execPath, [script], {
    encoding: 'utf8', timeout: 30000,
  });
  assert.ifError(result.error);
  assert.equal(result.signal, null, result.stderr);
  assert.equal(result.status, 0, result.stdout + result.stderr);
  assert.match(result.stdout, /explicit-false-bypasses-confirmation: exit 1, 13\/17 functional; organization unscored/);
  assert.match(result.stdout, /9 hand-control outcomes matched/);
});
