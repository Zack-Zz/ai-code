/**
 * Tests for scripts/sync-codex-global-config.sh
 *
 * Run with: node tests/scripts/sync-codex-global-config.test.js
 */

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

const SCRIPT = path.join(__dirname, '..', '..', 'scripts', 'sync-codex-global-config.sh');
const SOURCE = path.join(__dirname, '..', '..', '.codex', 'config.toml');

function test(name, fn) {
  try {
    fn();
    console.log(`  \u2713 ${name}`);
    return true;
  } catch (err) {
    console.log(`  \u2717 ${name}`);
    console.log(`    Error: ${err.message}`);
    return false;
  }
}

function runTests() {
  console.log('\n=== Testing sync-codex-global-config.sh ===\n');

  let passed = 0;
  let failed = 0;

  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'ai-code-codex-global-sync-'));
  const codexHome = path.join(tempRoot, '.codex');

  if (test('writes reference config without overwriting active config by default', () => {
    fs.mkdirSync(codexHome, { recursive: true });
    const activeTarget = path.join(codexHome, 'config.toml');
    fs.writeFileSync(activeTarget, 'active-config');
    execFileSync('bash', [SCRIPT, '--home', codexHome], {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: 15000
    });
    const target = path.join(codexHome, 'config.toml.reference');
    assert.ok(fs.existsSync(target), 'reference config.toml should exist');
    const sourceContent = fs.readFileSync(SOURCE, 'utf8');
    const targetContent = fs.readFileSync(target, 'utf8');
    const activeContent = fs.readFileSync(activeTarget, 'utf8');
    assert.strictEqual(targetContent, sourceContent, 'reference file should match source');
    assert.strictEqual(activeContent, 'active-config', 'active config should stay unchanged by default');
  })) passed++; else failed++;

  if (test('creates backup and applies config only when explicitly requested', () => {
    const target = path.join(codexHome, 'config.toml');
    fs.writeFileSync(target, 'old-config');
    execFileSync('bash', [SCRIPT, '--home', codexHome, '--apply-config'], {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: 15000
    });
    const backups = fs.readdirSync(codexHome).filter((f) => f.startsWith('config.toml.bak.'));
    assert.ok(backups.length > 0, 'backup file should be created');
    const sourceContent = fs.readFileSync(SOURCE, 'utf8');
    const activeContent = fs.readFileSync(target, 'utf8');
    assert.strictEqual(activeContent, sourceContent, 'active config should match source after explicit apply');
  })) passed++; else failed++;

  fs.rmSync(tempRoot, { recursive: true, force: true });

  console.log('\nResults:');
  console.log(`  Passed: ${passed}`);
  console.log(`  Failed: ${failed}`);
  console.log(`  Total:  ${passed + failed}`);

  process.exit(failed > 0 ? 1 : 0);
}

if (require.main === module) {
  runTests();
}
