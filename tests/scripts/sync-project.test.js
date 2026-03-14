/**
 * Tests for scripts/sync-project.sh
 *
 * Run with: node tests/scripts/sync-project.test.js
 */

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

const BOOTSTRAP = path.join(__dirname, '..', '..', 'scripts', 'bootstrap-project.sh');
const SYNC = path.join(__dirname, '..', '..', 'scripts', 'sync-project.sh');

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

function run(cmd, args) {
  return execFileSync(cmd, args, {
    encoding: 'utf8',
    stdio: ['pipe', 'pipe', 'pipe'],
    timeout: 30000
  });
}

function runTests() {
  console.log('\n=== Testing sync-project.sh ===\n');

  let passed = 0;
  let failed = 0;

  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'ai-code-sync-test-'));
  const targetDir = path.join(tempRoot, 'target-project');
  fs.mkdirSync(targetDir, { recursive: true });

  console.log('sync using manifest:');

  if (test('sync reuses manifest when langs/tool are omitted', () => {
    run('bash', [BOOTSTRAP, '--target', targetDir, '--langs', 'js', '--tool', 'codex']);
    const manifestPath = path.join(targetDir, '.ai-code.json');
    assert.ok(fs.existsSync(manifestPath), 'manifest should exist after bootstrap');

    const markerPath = path.join(targetDir, '.codex', 'codex.md');
    fs.writeFileSync(markerPath, 'stale-content');

    run('bash', [SYNC, '--target', targetDir]);
    const content = fs.readFileSync(markerPath, 'utf8');
    assert.ok(content.includes('Codex GUI Project Guide'), 'sync should overwrite .codex/codex.md from latest bootstrap');
    assert.ok(!fs.existsSync(path.join(targetDir, '.codex', 'config.toml')), 'sync should keep project codex config absent when manifest says false');
  })) passed++; else failed++;

  if (test('sync falls back to legacy .ai-code/bootstrap.json manifest', () => {
    const legacyDir = path.join(tempRoot, 'legacy-manifest-project');
    fs.mkdirSync(legacyDir, { recursive: true });
    run('bash', [BOOTSTRAP, '--target', legacyDir, '--langs', 'js', '--tool', 'codex']);

    const newManifestPath = path.join(legacyDir, '.ai-code.json');
    const legacyManifestDir = path.join(legacyDir, '.ai-code');
    const legacyManifestPath = path.join(legacyManifestDir, 'bootstrap.json');
    fs.mkdirSync(legacyManifestDir, { recursive: true });
    fs.copyFileSync(newManifestPath, legacyManifestPath);
    fs.rmSync(newManifestPath);

    run('bash', [SYNC, '--target', legacyDir]);
    assert.ok(fs.existsSync(path.join(legacyDir, '.codex', 'codex.md')), 'sync should work with legacy manifest');
  })) passed++; else failed++;

  if (test('sync accepts explicit langs/tool overrides', () => {
    run('bash', [SYNC, '--target', targetDir, '--langs', 'java', '--tool', 'all']);
    assert.ok(fs.existsSync(path.join(targetDir, 'CLAUDE.md')), 'explicit --tool all should copy Claude assets');
    assert.ok(fs.existsSync(path.join(targetDir, '.kiro', 'steering', 'ai-code-core.md')), 'explicit --tool all should copy Kiro assets');
    assert.ok(!fs.existsSync(path.join(targetDir, 'commands')), 'global-first sync should not copy commands');
    assert.ok(!fs.existsSync(path.join(targetDir, 'rules')), 'global-first sync should not copy rules');
    assert.ok(!fs.existsSync(path.join(targetDir, 'hooks')), 'global-first sync should not copy hooks');
    assert.ok(fs.existsSync(path.join(targetDir, '.agents', 'skills')), 'global-first sync should copy selected skills');
    assert.ok(fs.existsSync(path.join(targetDir, '.agents', 'skills', 'springboot-tdd', 'SKILL.md')), 'java sync should include springboot-tdd skill');
  })) passed++; else failed++;

  if (test('sync supports explicit codex config copy override', () => {
    run('bash', [SYNC, '--target', targetDir, '--langs', 'js', '--tool', 'codex', '--copy-codex-config']);
    assert.ok(fs.existsSync(path.join(targetDir, '.codex', 'config.toml')), 'sync with --copy-codex-config should copy .codex/config.toml');
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
