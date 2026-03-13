/**
 * Tests for scripts/bootstrap-project.sh
 *
 * Run with: node tests/scripts/bootstrap-project.test.js
 */

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { execFileSync } = require('child_process');

const SCRIPT = path.join(__dirname, '..', '..', 'scripts', 'bootstrap-project.sh');

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

function runBootstrap(target, langs = 'java', tool = 'both', layout = 'project-full', extraArgs = []) {
  return execFileSync('bash', [SCRIPT, '--target', target, '--langs', langs, '--tool', tool, '--layout', layout, ...extraArgs], {
    encoding: 'utf8',
    stdio: ['pipe', 'pipe', 'pipe'],
    timeout: 20000
  });
}

function runTests() {
  console.log('\n=== Testing bootstrap-project.sh ===\n');

  let passed = 0;
  let failed = 0;

  const tempRoot = fs.mkdtempSync(path.join(os.tmpdir(), 'ai-code-bootstrap-test-'));
  const targetDir = path.join(tempRoot, 'target-java-project');
  const targetAllDir = path.join(tempRoot, 'target-all-project');
  const targetGoDir = path.join(tempRoot, 'target-go-project');
  const targetAutoDir = path.join(tempRoot, 'target-auto-project');
  fs.mkdirSync(targetDir, { recursive: true });
  fs.mkdirSync(targetAllDir, { recursive: true });
  fs.mkdirSync(targetGoDir, { recursive: true });
  fs.mkdirSync(targetAutoDir, { recursive: true });

  console.log('--langs java --tool both:');

  if (test('copies Java workflow checklist to target project', () => {
    runBootstrap(targetDir, 'java', 'both');
    const workflowPath = path.join(targetDir, 'JAVA_WORKFLOW.md');
    assert.ok(fs.existsSync(workflowPath), 'JAVA_WORKFLOW.md should exist');
    const content = fs.readFileSync(workflowPath, 'utf8');
    assert.ok(content.includes('Java Workflow Checklist'), 'workflow file should contain title');
    assert.ok(content.includes('mvn -q test'), 'workflow should include Maven test command');
  })) passed++; else failed++;

  if (test('copies Java skill metadata file (agents/openai.yaml)', () => {
    const metadataPath = path.join(
      targetDir,
      '.agents',
      'skills',
      'springboot-tdd',
      'agents',
      'openai.yaml'
    );
    assert.ok(fs.existsSync(metadataPath), 'springboot-tdd openai.yaml should exist');
    const content = fs.readFileSync(metadataPath, 'utf8');
    assert.ok(content.includes('display_name: "Spring Boot TDD"'), 'metadata should contain display_name');
    assert.ok(content.includes('allow_implicit_invocation: true'), 'metadata should allow implicit invocation');
  })) passed++; else failed++;

  if (test('writes bootstrap manifest to target project', () => {
    const manifestPath = path.join(targetDir, '.ai-code.json');
    assert.ok(fs.existsSync(manifestPath), '.ai-code.json should exist');
    const data = JSON.parse(fs.readFileSync(manifestPath, 'utf8'));
    assert.strictEqual(data.langs, 'java', 'manifest should record langs');
    assert.strictEqual(data.tool, 'both', 'manifest should record tool');
    assert.strictEqual(data.layout, 'project-full', 'manifest should record layout');
    assert.strictEqual(data.copy_codex_config, 'false', 'manifest should record codex config copy mode');
  })) passed++; else failed++;

  if (test('does not copy project .codex/config.toml by default', () => {
    assert.ok(!fs.existsSync(path.join(targetDir, '.codex', 'config.toml')), '.codex/config.toml should not exist by default');
  })) passed++; else failed++;

  console.log('\n--langs java --tool all:');

  if (test('copies Claude bootstrap assets for --tool all', () => {
    runBootstrap(targetAllDir, 'java', 'all');
    assert.ok(fs.existsSync(path.join(targetAllDir, 'CLAUDE.md')), 'CLAUDE.md should exist');
    assert.ok(fs.existsSync(path.join(targetAllDir, 'hooks', 'hooks.json')), 'hooks/hooks.json should exist');
    assert.ok(fs.existsSync(path.join(targetAllDir, 'scripts', 'hooks', 'session-start.js')), 'scripts/hooks should exist');
    assert.ok(fs.existsSync(path.join(targetAllDir, 'scripts', 'lib', 'utils.js')), 'scripts/lib should exist');
  })) passed++; else failed++;

  if (test('copies project .codex/config.toml only when explicitly requested', () => {
    const targetConfigDir = path.join(tempRoot, 'target-codex-config-project');
    fs.mkdirSync(targetConfigDir, { recursive: true });
    runBootstrap(targetConfigDir, 'js', 'codex', 'project-full', ['--copy-codex-config']);
    assert.ok(fs.existsSync(path.join(targetConfigDir, '.codex', 'config.toml')), '.codex/config.toml should exist when --copy-codex-config is used');
  })) passed++; else failed++;

  console.log('\n--langs go --tool codex:');

  if (test('copies Go enforcement templates when go is selected', () => {
    runBootstrap(targetGoDir, 'go', 'codex');
    assert.ok(fs.existsSync(path.join(targetGoDir, 'Makefile')), 'Makefile should exist for Go projects');
    assert.ok(fs.existsSync(path.join(targetGoDir, '.golangci.yml')), '.golangci.yml should exist for Go projects');
    assert.ok(
      fs.existsSync(path.join(targetGoDir, '.github', 'workflows', 'go-ci.yml')),
      '.github/workflows/go-ci.yml should exist for Go projects'
    );
    const makefileContent = fs.readFileSync(path.join(targetGoDir, 'Makefile'), 'utf8');
    assert.ok(makefileContent.includes('test-race'), 'Makefile should include race test target');
  })) passed++; else failed++;

  console.log('\n--langs js --tool auto (default):');

  if (test('auto mode defaults to single-tool bootstrap (codex)', () => {
    execFileSync('bash', [SCRIPT, '--target', targetAutoDir, '--langs', 'js'], {
      encoding: 'utf8',
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: 20000
    });
    assert.ok(fs.existsSync(path.join(targetAutoDir, '.codex', 'codex.md')), 'auto should bootstrap codex assets');
    assert.ok(!fs.existsSync(path.join(targetAutoDir, '.kiro')), 'auto should not bootstrap kiro by default');
    assert.ok(!fs.existsSync(path.join(targetAutoDir, 'CLAUDE.md')), 'auto should not bootstrap claude by default');
    assert.ok(!fs.existsSync(path.join(targetAutoDir, '.agents', 'skills')), 'auto global-first should not copy skills');
  })) passed++; else failed++;

  // Cleanup temp directory
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
