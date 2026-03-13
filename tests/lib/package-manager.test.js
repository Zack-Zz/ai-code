/**
 * Tests for scripts/lib/package-manager.js
 *
 * Run with: node tests/lib/package-manager.test.js
 */

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');

const pm = require('../../scripts/lib/package-manager');

function test(name, fn) {
  try {
    fn();
    console.log(` ✓ ${name}`);
    return true;
  } catch (err) {
    console.log(` ✗ ${name}`);
    console.log(` Error: ${err.message}`);
    return false;
  }
}

function createTempDir(prefix) {
  return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

function cleanup(dir) {
  fs.rmSync(dir, { recursive: true, force: true });
}

function withEnv(overrides, fn) {
  const previous = {};
  for (const [key, value] of Object.entries(overrides)) {
    previous[key] = process.env[key];
    if (value === null || value === undefined) {
      delete process.env[key];
    } else {
      process.env[key] = value;
    }
  }

  try {
    return fn();
  } finally {
    for (const [key, value] of Object.entries(previous)) {
      if (value === undefined) {
        delete process.env[key];
      } else {
        process.env[key] = value;
      }
    }
  }
}

function withIsolatedHome(fn) {
  const home = createTempDir('pm-home-');
  try {
    return withEnv({
      AI_CODE_HOME: path.join(home, '.claude'),
      AI_CODE_PACKAGE_MANAGER: null,
      CLAUDE_PACKAGE_MANAGER: null
    }, () => fn(home));
  } finally {
    cleanup(home);
  }
}

function runTests() {
  console.log('\n=== Testing package-manager.js ===\n');

  let passed = 0;
  let failed = 0;

  console.log('Constants:');

  if (test('exports supported package managers and detection order', () => {
    assert.deepStrictEqual(Object.keys(pm.PACKAGE_MANAGERS), ['npm', 'pnpm', 'yarn', 'bun']);
    assert.strictEqual(pm.DETECTION_PRIORITY[0], 'pnpm');
    assert.strictEqual(pm.DETECTION_PRIORITY[pm.DETECTION_PRIORITY.length - 1], 'npm');
  })) passed++; else failed++;

  console.log('\ndetectFromLockFile:');

  if (test('detects lock files using declared priority', () => {
    const dir = createTempDir('pm-lock-');
    try {
      fs.writeFileSync(path.join(dir, 'package-lock.json'), '{}');
      fs.writeFileSync(path.join(dir, 'pnpm-lock.yaml'), 'lockfileVersion: 9');
      assert.strictEqual(pm.detectFromLockFile(dir), 'pnpm');
    } finally {
      cleanup(dir);
    }
  })) passed++; else failed++;

  if (test('returns null when no known lock file exists', () => {
    const dir = createTempDir('pm-lock-empty-');
    try {
      assert.strictEqual(pm.detectFromLockFile(dir), null);
    } finally {
      cleanup(dir);
    }
  })) passed++; else failed++;

  console.log('\ndetectFromPackageJson:');

  if (test('reads packageManager field and ignores invalid values', () => {
    const dir = createTempDir('pm-pkgjson-');
    try {
      fs.writeFileSync(path.join(dir, 'package.json'), JSON.stringify({ packageManager: 'yarn@4.6.0' }));
      assert.strictEqual(pm.detectFromPackageJson(dir), 'yarn');

      fs.writeFileSync(path.join(dir, 'package.json'), JSON.stringify({ packageManager: '@scope/pkg@1.0.0' }));
      assert.strictEqual(pm.detectFromPackageJson(dir), null);

      fs.writeFileSync(path.join(dir, 'package.json'), '{not valid json');
      assert.strictEqual(pm.detectFromPackageJson(dir), null);
    } finally {
      cleanup(dir);
    }
  })) passed++; else failed++;

  console.log('\ngetPackageManager:');

  if (test('prefers AI_CODE_PACKAGE_MANAGER and keeps CLAUDE_PACKAGE_MANAGER as fallback', () => {
    withEnv({
      AI_CODE_PACKAGE_MANAGER: 'pnpm',
      CLAUDE_PACKAGE_MANAGER: 'yarn'
    }, () => {
      const result = pm.getPackageManager();
      assert.strictEqual(result.name, 'pnpm');
      assert.strictEqual(result.source, 'environment');
    });

    withEnv({
      AI_CODE_PACKAGE_MANAGER: null,
      CLAUDE_PACKAGE_MANAGER: 'yarn'
    }, () => {
      const result = pm.getPackageManager();
      assert.strictEqual(result.name, 'yarn');
      assert.strictEqual(result.source, 'environment');
    });
  })) passed++; else failed++;

  if (test('uses project config before package.json and lock file', () => {
    const dir = createTempDir('pm-priority-');
    try {
      fs.mkdirSync(path.join(dir, '.claude'), { recursive: true });
      fs.writeFileSync(path.join(dir, '.claude', 'package-manager.json'), JSON.stringify({ packageManager: 'bun' }));
      fs.writeFileSync(path.join(dir, 'package.json'), JSON.stringify({ packageManager: 'pnpm@9.0.0' }));
      fs.writeFileSync(path.join(dir, 'package-lock.json'), '{}');

      const result = withEnv({
        AI_CODE_PACKAGE_MANAGER: null,
        CLAUDE_PACKAGE_MANAGER: null
      }, () => pm.getPackageManager({ projectDir: dir }));

      assert.strictEqual(result.name, 'bun');
      assert.strictEqual(result.source, 'project-config');
    } finally {
      cleanup(dir);
    }
  })) passed++; else failed++;

  if (test('uses isolated global config and finally defaults to npm', () => {
    withIsolatedHome(() => {
      let result = pm.getPackageManager({ projectDir: createTempDir('pm-empty-project-') });
      assert.strictEqual(result.name, 'npm');
      assert.strictEqual(result.source, 'default');

      pm.setPreferredPackageManager('bun');
      result = pm.getPackageManager({ projectDir: createTempDir('pm-empty-project-2') });
      assert.strictEqual(result.name, 'bun');
      assert.strictEqual(result.source, 'global-config');
    });
  })) passed++; else failed++;

  console.log('\nPersistence:');

  if (test('setPreferredPackageManager writes under AI_CODE_HOME', () => {
    withIsolatedHome(() => {
      const saved = pm.setPreferredPackageManager('pnpm');
      assert.strictEqual(saved.packageManager, 'pnpm');
      const configPath = path.join(process.env.AI_CODE_HOME, 'package-manager.json');
      const onDisk = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      assert.strictEqual(onDisk.packageManager, 'pnpm');
      assert.ok(onDisk.setAt);
    });
  })) passed++; else failed++;

  if (test('setProjectPackageManager writes .claude/package-manager.json in the project', () => {
    const dir = createTempDir('pm-project-write-');
    try {
      const saved = pm.setProjectPackageManager('bun', dir);
      assert.strictEqual(saved.packageManager, 'bun');
      const configPath = path.join(dir, '.claude', 'package-manager.json');
      const onDisk = JSON.parse(fs.readFileSync(configPath, 'utf8'));
      assert.strictEqual(onDisk.packageManager, 'bun');
      assert.ok(onDisk.setAt);
    } finally {
      cleanup(dir);
    }
  })) passed++; else failed++;

  console.log('\ngetRunCommand:');

  if (test('formats commands for each supported package manager', () => {
    withEnv({ AI_CODE_PACKAGE_MANAGER: 'npm', CLAUDE_PACKAGE_MANAGER: null }, () => {
      assert.strictEqual(pm.getRunCommand('lint'), 'npm run lint');
      assert.strictEqual(pm.getRunCommand('build'), 'npm run build');
    });
    withEnv({ AI_CODE_PACKAGE_MANAGER: 'pnpm', CLAUDE_PACKAGE_MANAGER: null }, () => {
      assert.strictEqual(pm.getRunCommand('lint'), 'pnpm lint');
    });
    withEnv({ AI_CODE_PACKAGE_MANAGER: 'yarn', CLAUDE_PACKAGE_MANAGER: null }, () => {
      assert.strictEqual(pm.getRunCommand('install'), 'yarn');
    });
    withEnv({ AI_CODE_PACKAGE_MANAGER: 'bun', CLAUDE_PACKAGE_MANAGER: null }, () => {
      assert.strictEqual(pm.getRunCommand('test'), 'bun test');
    });
  })) passed++; else failed++;

  if (test('rejects unsafe script names', () => {
    assert.throws(() => pm.getRunCommand('test; rm -rf /'), /unsafe characters/);
    assert.throws(() => pm.getRunCommand('../evil'), /unsafe characters/);
    assert.throws(() => pm.getRunCommand('/absolute/path'), /unsafe characters/);
  })) passed++; else failed++;

  if (test('allows scoped names without allowing traversal segments', () => {
    withEnv({ AI_CODE_PACKAGE_MANAGER: 'npm', CLAUDE_PACKAGE_MANAGER: null }, () => {
      assert.strictEqual(pm.getRunCommand('@scope/my-script'), 'npm run @scope/my-script');
      assert.throws(() => pm.getRunCommand('@scope/../evil'), /unsafe characters/);
    });
  })) passed++; else failed++;

  console.log('\ngetExecCommand:');

  if (test('formats binary execution commands for each package manager', () => {
    withEnv({ AI_CODE_PACKAGE_MANAGER: 'npm', CLAUDE_PACKAGE_MANAGER: null }, () => {
      assert.strictEqual(pm.getExecCommand('prettier', '--write .'), 'npx prettier --write .');
    });
    withEnv({ AI_CODE_PACKAGE_MANAGER: 'pnpm', CLAUDE_PACKAGE_MANAGER: null }, () => {
      assert.strictEqual(pm.getExecCommand('eslint', '.'), 'pnpm dlx eslint .');
    });
    withEnv({ AI_CODE_PACKAGE_MANAGER: 'yarn', CLAUDE_PACKAGE_MANAGER: null }, () => {
      assert.strictEqual(pm.getExecCommand('eslint', '.'), 'yarn dlx eslint .');
    });
    withEnv({ AI_CODE_PACKAGE_MANAGER: 'bun', CLAUDE_PACKAGE_MANAGER: null }, () => {
      assert.strictEqual(pm.getExecCommand('tsc', '--noEmit'), 'bunx tsc --noEmit');
    });
  })) passed++; else failed++;

  if (test('rejects unsafe binary names and argument payloads', () => {
    assert.throws(() => pm.getExecCommand('../passwd'), /unsafe characters/);
    assert.throws(() => pm.getExecCommand('tool', 'file.js\necho injected'), /unsafe whitespace/);
    assert.throws(() => pm.getExecCommand('tool', '--flag "quoted"'), /unsafe characters/);
    assert.throws(() => pm.getExecCommand('tool', {}), /Arguments must be a string/);
  })) passed++; else failed++;

  console.log('\nHelpers:');

  if (test('getCommandPattern matches supported command variants', () => {
    const regex = new RegExp(pm.getCommandPattern('dev'));
    assert.ok(regex.test('npm run dev'));
    assert.ok(regex.test('pnpm dev'));
    assert.ok(regex.test('yarn dev'));
    assert.ok(regex.test('bun run dev'));
    assert.ok(!regex.test('cargo run'));
  })) passed++; else failed++;

  if (test('getSelectionPrompt reflects current configuration contract', () => {
    const prompt = pm.getSelectionPrompt();
    assert.ok(prompt.includes('AI_CODE_PACKAGE_MANAGER'));
    assert.ok(prompt.includes('CLAUDE_PACKAGE_MANAGER'));
    assert.ok(prompt.includes('lock file'));
  })) passed++; else failed++;

  console.log('\n=== Test Results ===');
  console.log(`Passed: ${passed}`);
  console.log(`Failed: ${failed}`);
  console.log(`Total:  ${passed + failed}`);

  process.exit(failed > 0 ? 1 : 0);
}

if (require.main === module) {
  runTests();
}
