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

  if (test('syncs config.toml into custom codex home', () => {
    execFileSync('bash', [SCRIPT, '--home', codexHome], {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: 15000
    });
    const target = path.join(codexHome, 'config.toml');
    assert.ok(fs.existsSync(target), 'target config.toml should exist');
    const sourceContent = fs.readFileSync(SOURCE, 'utf8');
    const targetContent = fs.readFileSync(target, 'utf8');
    assert.strictEqual(targetContent, sourceContent, 'synced file should match source');
  })) passed++; else failed++;

  if (test('creates backup when target config already exists', () => {
    const target = path.join(codexHome, 'config.toml');
    fs.writeFileSync(target, 'old-config');
    execFileSync('bash', [SCRIPT, '--home', codexHome], {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: 15000
    });
    const backups = fs.readdirSync(codexHome).filter((f) => f.startsWith('config.toml.bak.'));
    assert.ok(backups.length > 0, 'backup file should be created');
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
