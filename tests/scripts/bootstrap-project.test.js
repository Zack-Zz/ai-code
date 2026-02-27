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

function runBootstrap(target, langs = 'java', tool = 'both') {
  return execFileSync('bash', [SCRIPT, '--target', target, '--langs', langs, '--tool', tool], {
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
  fs.mkdirSync(targetDir, { recursive: true });
  fs.mkdirSync(targetAllDir, { recursive: true });

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

  console.log('\n--langs java --tool all:');

  if (test('copies Claude bootstrap assets for --tool all', () => {
    runBootstrap(targetAllDir, 'java', 'all');
    assert.ok(fs.existsSync(path.join(targetAllDir, 'CLAUDE.md')), 'CLAUDE.md should exist');
    assert.ok(fs.existsSync(path.join(targetAllDir, 'hooks', 'hooks.json')), 'hooks/hooks.json should exist');
    assert.ok(fs.existsSync(path.join(targetAllDir, 'scripts', 'hooks', 'session-start.js')), 'scripts/hooks should exist');
    assert.ok(fs.existsSync(path.join(targetAllDir, 'scripts', 'lib', 'utils.js')), 'scripts/lib should exist');
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
