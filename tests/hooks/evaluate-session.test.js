/**
 * Tests for scripts/hooks/evaluate-session.js
 *
 * Run with: node tests/hooks/evaluate-session.test.js
 */

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');
const { spawnSync } = require('child_process');

const evaluateScript = path.join(__dirname, '..', '..', 'scripts', 'hooks', 'evaluate-session.js');
const configPath = path.join(__dirname, '..', '..', 'skills', 'continuous-learning', 'config.json');

function test(name, fn) {
  try {
    fn();
    console.log(`  ✓ ${name}`);
    return true;
  } catch (err) {
    console.log(`  ✗ ${name}`);
    console.log(`    Error: ${err.message}`);
    return false;
  }
}

function createTestDir() {
  return fs.mkdtempSync(path.join(os.tmpdir(), 'eval-session-test-'));
}

function cleanupTestDir(testDir) {
  fs.rmSync(testDir, { recursive: true, force: true });
}

function createTranscript(dir, userCount, assistantCount = userCount) {
  const filePath = path.join(dir, 'transcript.jsonl');
  const lines = [];

  for (let i = 0; i < userCount; i++) {
    lines.push(JSON.stringify({ type: 'user', content: `Message ${i + 1}` }));
  }
  for (let i = 0; i < assistantCount; i++) {
    lines.push(JSON.stringify({ type: 'assistant', content: `Response ${i + 1}` }));
  }

  fs.writeFileSync(filePath, lines.join('\n') + '\n');
  return filePath;
}

function runEvaluate({ stdin = {}, env = {}, rawInput = null } = {}) {
  const root = createTestDir();
  const assistantHome = path.join(root, '.claude');
  fs.mkdirSync(assistantHome, { recursive: true });

  const result = spawnSync('node', [evaluateScript], {
    encoding: 'utf8',
    input: rawInput === null ? JSON.stringify(stdin) : rawInput,
    timeout: 10000,
    env: {
      ...process.env,
      HOME: root,
      USERPROFILE: root,
      AI_CODE_HOME: assistantHome,
      ...env
    }
  });

  cleanupTestDir(root);

  return {
    code: result.status || 0,
    stdout: result.stdout || '',
    stderr: result.stderr || ''
  };
}

function withConfig(content, fn) {
  let originalContent = null;
  let hadOriginal = false;

  try {
    originalContent = fs.readFileSync(configPath, 'utf8');
    hadOriginal = true;
  } catch {
    hadOriginal = false;
  }

  fs.writeFileSync(configPath, content, 'utf8');

  try {
    return fn();
  } finally {
    if (hadOriginal) {
      fs.writeFileSync(configPath, originalContent, 'utf8');
    } else {
      fs.unlinkSync(configPath);
    }
  }
}

function runTests() {
  console.log('\n=== Testing evaluate-session.js ===\n');

  let passed = 0;
  let failed = 0;

  console.log('Threshold boundary (default min=10):');

  if (test('skips sessions below threshold and evaluates at threshold', () => {
    let dir = createTestDir();
    try {
      let transcript = createTranscript(dir, 9);
      let result = runEvaluate({ stdin: { transcript_path: transcript } });
      assert.strictEqual(result.code, 0);
      assert.ok(result.stderr.includes('Session too short (9 messages)'));

      cleanupTestDir(dir);
      dir = createTestDir();
      transcript = createTranscript(dir, 10);
      result = runEvaluate({ stdin: { transcript_path: transcript } });
      assert.strictEqual(result.code, 0);
      assert.ok(result.stderr.includes('Session has 10 messages'));
      assert.ok(result.stderr.includes('evaluate for extractable patterns'));
    } finally {
      cleanupTestDir(dir);
    }
  })) passed++; else failed++;

  if (test('counts only user messages', () => {
    const dir = createTestDir();
    try {
      const transcript = createTranscript(dir, 5, 50);
      const result = runEvaluate({ stdin: { transcript_path: transcript } });
      assert.strictEqual(result.code, 0);
      assert.ok(result.stderr.includes('Session too short (5 messages)'));
    } finally {
      cleanupTestDir(dir);
    }
  })) passed++; else failed++;

  console.log('\nInput handling:');

  if (test('exits 0 for missing or nonexistent transcript paths', () => {
    let result = runEvaluate({ stdin: {} });
    assert.strictEqual(result.code, 0);
    assert.strictEqual(result.stderr, '');

    result = runEvaluate({ stdin: { transcript_path: '/nonexistent/path/transcript.jsonl' } });
    assert.strictEqual(result.code, 0);
    assert.strictEqual(result.stderr, '');
  })) passed++; else failed++;

  if (test('handles invalid or empty stdin gracefully', () => {
    let result = runEvaluate({ rawInput: 'not valid json' });
    assert.strictEqual(result.code, 0);

    result = runEvaluate({ rawInput: '' });
    assert.strictEqual(result.code, 0);
  })) passed++; else failed++;

  if (test('falls back to CLAUDE_TRANSCRIPT_PATH when stdin is invalid JSON', () => {
    const dir = createTestDir();
    try {
      const transcript = createTranscript(dir, 15);
      const result = runEvaluate({
        rawInput: 'invalid json {{{',
        env: { CLAUDE_TRANSCRIPT_PATH: transcript }
      });
      assert.strictEqual(result.code, 0);
      assert.ok(result.stderr.includes('Session has 15 messages'));
    } finally {
      cleanupTestDir(dir);
    }
  })) passed++; else failed++;

  console.log('\nTranscript parsing:');

  if (test('treats empty transcripts and assistant-only transcripts as too short', () => {
    const dir = createTestDir();
    try {
      const emptyTranscript = path.join(dir, 'empty.jsonl');
      fs.writeFileSync(emptyTranscript, '');
      let result = runEvaluate({ stdin: { transcript_path: emptyTranscript } });
      assert.strictEqual(result.code, 0);
      assert.ok(result.stderr.includes('Session too short (0 messages)'));

      const assistantOnly = path.join(dir, 'assistant-only.jsonl');
      fs.writeFileSync(
        assistantOnly,
        Array.from({ length: 20 }, (_, i) => JSON.stringify({ type: 'assistant', content: `Response ${i}` })).join('\n') + '\n'
      );
      result = runEvaluate({ stdin: { transcript_path: assistantOnly } });
      assert.strictEqual(result.code, 0);
      assert.ok(result.stderr.includes('Session too short (0 messages)'));
    } finally {
      cleanupTestDir(dir);
    }
  })) passed++; else failed++;

  if (test('counts valid user markers even when the file contains malformed lines or spaced colons', () => {
    const dir = createTestDir();
    try {
      const malformed = path.join(dir, 'mixed.jsonl');
      const malformedLines = [];
      for (let i = 0; i < 12; i++) {
        malformedLines.push(JSON.stringify({ type: 'user', content: `msg ${i}` }));
      }
      malformedLines.push('not valid json');
      malformedLines.push('still not valid');
      fs.writeFileSync(malformed, malformedLines.join('\n') + '\n');

      let result = runEvaluate({ stdin: { transcript_path: malformed } });
      assert.strictEqual(result.code, 0);
      assert.ok(result.stderr.includes('Session has 12 messages'));

      const spaced = path.join(dir, 'spaced.jsonl');
      const spacedLines = [];
      for (let i = 0; i < 12; i++) {
        spacedLines.push(`{"type" : "user", "content": "msg ${i}"}`);
        spacedLines.push(`{"type" : "assistant", "content": "resp ${i}"}`);
      }
      fs.writeFileSync(spaced, spacedLines.join('\n') + '\n');

      result = runEvaluate({ stdin: { transcript_path: spaced } });
      assert.strictEqual(result.code, 0);
      assert.ok(result.stderr.includes('Session has 12 messages'));
    } finally {
      cleanupTestDir(dir);
    }
  })) passed++; else failed++;

  console.log('\nConfig handling:');

  if (test('respects custom min_session_length from config', () => {
    withConfig(JSON.stringify({ min_session_length: 3 }), () => {
      const dir = createTestDir();
      try {
        const transcript = createTranscript(dir, 4);
        const result = runEvaluate({ stdin: { transcript_path: transcript } });
        assert.strictEqual(result.code, 0);
        assert.ok(result.stderr.includes('Session has 4 messages'));
      } finally {
        cleanupTestDir(dir);
      }
    });
  })) passed++; else failed++;

  if (test('falls back to defaults when config file is invalid JSON', () => {
    withConfig('NOT VALID JSON {{{', () => {
      const dir = createTestDir();
      try {
        const transcript = createTranscript(dir, 12);
        const result = runEvaluate({ stdin: { transcript_path: transcript } });
        assert.strictEqual(result.code, 0);
        assert.ok(result.stderr.includes('Failed to parse config'));
        assert.ok(result.stderr.includes('Session has 12 messages'));
      } finally {
        cleanupTestDir(dir);
      }
    });
  })) passed++; else failed++;

  if (test('uses learned_skills_path from config with ~ expansion', () => {
    withConfig(JSON.stringify({
      min_session_length: 10,
      learned_skills_path: '~/custom-learned-skills-dir'
    }), () => {
      const dir = createTestDir();
      try {
        const transcript = createTranscript(dir, 12);
        const result = runEvaluate({ stdin: { transcript_path: transcript } });
        assert.strictEqual(result.code, 0);
        assert.ok(result.stderr.includes('custom-learned-skills-dir'));
        assert.ok(!result.stderr.includes('~/custom-learned-skills-dir'));
      } finally {
        cleanupTestDir(dir);
      }
    });
  })) passed++; else failed++;

  console.log('\nResults:');
  console.log(`Passed: ${passed}`);
  console.log(`Failed: ${failed}`);
  console.log(`Total:  ${passed + failed}`);

  process.exit(failed > 0 ? 1 : 0);
}

if (require.main === module) {
  runTests();
}
