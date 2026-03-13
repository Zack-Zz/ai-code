/**
 * Tests for scripts/lib/session-aliases.js
 *
 * Run with: node tests/lib/session-aliases.test.js
 */

const assert = require('assert');
const fs = require('fs');
const os = require('os');
const path = require('path');

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

function createTempDir(prefix) {
  return fs.mkdtempSync(path.join(os.tmpdir(), prefix));
}

function cleanup(dir) {
  fs.rmSync(dir, { recursive: true, force: true });
}

function loadFreshAliasesModule() {
  delete require.cache[require.resolve('../../scripts/lib/session-aliases')];
  delete require.cache[require.resolve('../../scripts/lib/utils')];
  return require('../../scripts/lib/session-aliases');
}

function withIsolatedAliases(fn) {
  const root = createTempDir('aliases-test-');
  const assistantHome = path.join(root, '.claude');
  const previousHome = process.env.AI_CODE_HOME;

  fs.mkdirSync(assistantHome, { recursive: true });
  process.env.AI_CODE_HOME = assistantHome;

  try {
    const aliases = loadFreshAliasesModule();
    return fn({ root, assistantHome, aliases });
  } finally {
    if (previousHome === undefined) {
      delete process.env.AI_CODE_HOME;
    } else {
      process.env.AI_CODE_HOME = previousHome;
    }
    cleanup(root);
    delete require.cache[require.resolve('../../scripts/lib/session-aliases')];
    delete require.cache[require.resolve('../../scripts/lib/utils')];
  }
}

function runTests() {
  console.log('\n=== Testing session-aliases.js ===\n');

  let passed = 0;
  let failed = 0;

  console.log('loadAliases:');

  if (test('returns the default structure when the aliases file does not exist', () => {
    withIsolatedAliases(({ aliases }) => {
      const data = aliases.loadAliases();
      assert.strictEqual(data.version, '1.0');
      assert.deepStrictEqual(data.aliases, {});
      assert.strictEqual(data.metadata.totalCount, 0);
    });
  })) passed++; else failed++;

  if (test('resets to defaults for invalid JSON and invalid structure', () => {
    withIsolatedAliases(({ aliases }) => {
      const aliasesPath = aliases.getAliasesPath();
      fs.writeFileSync(aliasesPath, 'not valid json');
      assert.deepStrictEqual(aliases.loadAliases().aliases, {});

      fs.writeFileSync(aliasesPath, JSON.stringify({ nope: true }));
      assert.deepStrictEqual(aliases.loadAliases().aliases, {});
    });
  })) passed++; else failed++;

  if (test('backfills version and metadata for older files', () => {
    withIsolatedAliases(({ aliases }) => {
      const aliasesPath = aliases.getAliasesPath();
      fs.writeFileSync(aliasesPath, JSON.stringify({
        aliases: {
          demo: {
            sessionPath: '/tmp/session',
            createdAt: '2026-01-01T00:00:00.000Z',
            updatedAt: '2026-01-01T00:00:00.000Z',
            title: 'Demo'
          }
        }
      }));

      const loaded = aliases.loadAliases();
      assert.strictEqual(loaded.version, '1.0');
      assert.strictEqual(loaded.metadata.totalCount, 1);
      assert.ok(loaded.metadata.lastUpdated);
    });
  })) passed++; else failed++;

  console.log('\nCRUD:');

  if (test('creates and resolves a new alias', () => {
    withIsolatedAliases(({ aliases }) => {
      const result = aliases.setAlias('my-session', '/sessions/one', 'First');
      assert.strictEqual(result.success, true);
      assert.strictEqual(result.isNew, true);

      const resolved = aliases.resolveAlias('my-session');
      assert.deepStrictEqual(resolved, {
        alias: 'my-session',
        sessionPath: '/sessions/one',
        createdAt: resolved.createdAt,
        title: 'First'
      });
      assert.ok(resolved.createdAt);
    });
  })) passed++; else failed++;

  if (test('updates an alias and preserves createdAt', () => {
    withIsolatedAliases(({ aliases }) => {
      aliases.setAlias('my-session', '/sessions/one', 'First');
      const first = aliases.resolveAlias('my-session');

      const result = aliases.setAlias('my-session', '/sessions/two', 'Second');
      const second = aliases.resolveAlias('my-session');

      assert.strictEqual(result.success, true);
      assert.strictEqual(result.isNew, false);
      assert.strictEqual(second.sessionPath, '/sessions/two');
      assert.strictEqual(second.title, 'Second');
      assert.strictEqual(second.createdAt, first.createdAt);
    });
  })) passed++; else failed++;

  if (test('renames, updates title, and deletes aliases', () => {
    withIsolatedAliases(({ aliases }) => {
      aliases.setAlias('draft', '/sessions/one', 'Draft');

      const renamed = aliases.renameAlias('draft', 'published');
      assert.strictEqual(renamed.success, true);
      assert.strictEqual(aliases.resolveAlias('draft'), null);
      assert.strictEqual(aliases.resolveAlias('published').sessionPath, '/sessions/one');

      const updated = aliases.updateAliasTitle('published', '');
      assert.strictEqual(updated.success, true);
      assert.strictEqual(aliases.resolveAlias('published').title, null);

      const deleted = aliases.deleteAlias('published');
      assert.strictEqual(deleted.success, true);
      assert.strictEqual(aliases.resolveAlias('published'), null);
    });
  })) passed++; else failed++;

  console.log('\nValidation:');

  if (test('rejects invalid alias names and invalid session paths', () => {
    withIsolatedAliases(({ aliases }) => {
      assert.strictEqual(aliases.setAlias('', '/sessions/one').success, false);
      assert.strictEqual(aliases.setAlias('list', '/sessions/one').success, false);
      assert.strictEqual(aliases.setAlias('bad name', '/sessions/one').success, false);
      assert.strictEqual(aliases.setAlias('a'.repeat(129), '/sessions/one').success, false);
      assert.strictEqual(aliases.setAlias('valid', '').success, false);
      assert.strictEqual(aliases.setAlias('valid', '   ').success, false);
      assert.strictEqual(aliases.setAlias('valid', 42).success, false);
      assert.strictEqual(aliases.resolveAlias('bad/name'), null);
    });
  })) passed++; else failed++;

  if (test('rejects invalid rename and title update operations', () => {
    withIsolatedAliases(({ aliases }) => {
      aliases.setAlias('alpha', '/sessions/one', 'Alpha');
      aliases.setAlias('beta', '/sessions/two', 'Beta');

      assert.strictEqual(aliases.renameAlias('missing', 'gamma').success, false);
      assert.strictEqual(aliases.renameAlias('alpha', 'beta').success, false);
      assert.strictEqual(aliases.renameAlias('alpha', 'list').success, false);
      assert.strictEqual(aliases.updateAliasTitle('missing', 'Title').success, false);
      assert.strictEqual(aliases.updateAliasTitle('alpha', 123).success, false);
    });
  })) passed++; else failed++;

  console.log('\nListing and lookup:');

  if (test('lists aliases by recency and supports search and limit', () => {
    withIsolatedAliases(({ aliases }) => {
      const data = aliases.loadAliases();
      data.aliases.old = {
        sessionPath: '/sessions/old',
        createdAt: '2026-01-01T00:00:00.000Z',
        updatedAt: '2026-01-01T00:00:00.000Z',
        title: 'Legacy Session'
      };
      data.aliases.newest = {
        sessionPath: '/sessions/new',
        createdAt: '2026-02-01T00:00:00.000Z',
        updatedAt: '2026-03-01T00:00:00.000Z',
        title: 'Fresh Session'
      };
      data.aliases.noDates = {
        sessionPath: '/sessions/nodate',
        title: 'No Dates'
      };
      assert.strictEqual(aliases.saveAliases(data), true);

      const all = aliases.listAliases();
      assert.deepStrictEqual(all.map(item => item.name), ['newest', 'old', 'noDates']);

      const searched = aliases.listAliases({ search: 'fresh' });
      assert.strictEqual(searched.length, 1);
      assert.strictEqual(searched[0].name, 'newest');

      const limited = aliases.listAliases({ limit: 1 });
      assert.strictEqual(limited.length, 1);
      assert.strictEqual(limited[0].name, 'newest');
    });
  })) passed++; else failed++;

  if (test('resolves session aliases and finds all aliases for a session path', () => {
    withIsolatedAliases(({ aliases }) => {
      aliases.setAlias('a1', '/sessions/shared', 'One');
      aliases.setAlias('a2', '/sessions/shared', 'Two');
      aliases.setAlias('other', '/sessions/other', 'Other');

      assert.strictEqual(aliases.resolveSessionAlias('a1'), '/sessions/shared');
      assert.strictEqual(aliases.resolveSessionAlias('/sessions/direct'), '/sessions/direct');

      const names = aliases.getAliasesForSession('/sessions/shared').map(item => item.name).sort();
      assert.deepStrictEqual(names, ['a1', 'a2']);
    });
  })) passed++; else failed++;

  console.log('\ncleanupAliases:');

  if (test('removes aliases whose sessions no longer exist', () => {
    withIsolatedAliases(({ aliases }) => {
      aliases.setAlias('keep', '/sessions/keep', 'Keep');
      aliases.setAlias('drop-1', '/sessions/drop-1', 'Drop');
      aliases.setAlias('drop-2', '/sessions/drop-2', 'Drop');

      const result = aliases.cleanupAliases((sessionPath) => sessionPath === '/sessions/keep');
      assert.strictEqual(result.success, true);
      assert.strictEqual(result.totalChecked, 3);
      assert.strictEqual(result.removed, 2);
      assert.deepStrictEqual(result.removedAliases.map(item => item.name).sort(), ['drop-1', 'drop-2']);
      assert.ok(aliases.resolveAlias('keep'));
      assert.strictEqual(aliases.resolveAlias('drop-1'), null);
    });
  })) passed++; else failed++;

  if (test('returns an error for invalid cleanup callback', () => {
    withIsolatedAliases(({ aliases }) => {
      const result = aliases.cleanupAliases('not-a-function');
      assert.strictEqual(result.success, undefined);
      assert.strictEqual(result.totalChecked, 0);
      assert.ok(result.error.includes('function'));
    });
  })) passed++; else failed++;

  console.log('\nPersistence details:');

  if (test('saveAliases writes metadata and loadAliases returns it on disk', () => {
    withIsolatedAliases(({ aliases }) => {
      const data = aliases.loadAliases();
      data.aliases.persisted = {
        sessionPath: '/sessions/persisted',
        createdAt: '2026-01-01T00:00:00.000Z',
        updatedAt: '2026-01-02T00:00:00.000Z',
        title: 'Persisted'
      };

      assert.strictEqual(aliases.saveAliases(data), true);

      const aliasesPath = aliases.getAliasesPath();
      const onDisk = JSON.parse(fs.readFileSync(aliasesPath, 'utf8'));
      assert.strictEqual(onDisk.metadata.totalCount, 1);
      assert.ok(onDisk.metadata.lastUpdated);
      assert.strictEqual(onDisk.aliases.persisted.title, 'Persisted');
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
