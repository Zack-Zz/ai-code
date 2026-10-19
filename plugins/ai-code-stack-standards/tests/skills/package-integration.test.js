const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawnSync } = require('node:child_process');
const { test } = require('node:test');

const repository = path.resolve(__dirname, '../../../..');
const source = path.resolve(__dirname, '../..');
const identity = 'ai-code-stack-standards';
const skillPath = 'skills/code-standards/SKILL.md';
const references = ['data-access.md', 'frontend.md', 'java.md', 'jpa.md', 'mybatis.md'];
const referenceDirectory = 'skills/code-standards/references';
const iconPath = 'assets/codestack.png';

function runTool(root, ...args) {
  const result = spawnSync('python3', ['-B', path.join(repository, 'tooling/plugin_tool.py'), '--root', root, ...args], {
    cwd: repository, encoding: 'utf8', timeout: 60000,
  });
  assert.ifError(result.error);
  assert.equal(result.signal, null, result.stderr);
  return result;
}

function succeeds(result) {
  assert.equal(result.status, 0, result.stdout + result.stderr);
  return result;
}

function withSourceFixture(callback) {
  const temporary = fs.mkdtempSync(path.join(fs.realpathSync(os.tmpdir()), 'codestack-package-'));
  try {
    const root = path.join(temporary, 'repository');
    const plugin = path.join(root, 'plugins', identity);
    fs.mkdirSync(path.dirname(plugin), { recursive: true });
    fs.cpSync(source, plugin, { recursive: true });
    fs.writeFileSync(path.join(root, 'catalog.json'), JSON.stringify({
      schema_version: 1, plugins: [{ path: `plugins/${identity}` }],
    }));
    succeeds(runTool(root, 'validate', '--all'));
    callback({ root, plugin, temporary });
  } finally {
    fs.rmSync(temporary, { recursive: true, force: true });
  }
}

function listFiles(directory, prefix = '') {
  return fs.readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const relative = prefix ? `${prefix}/${entry.name}` : entry.name;
    return entry.isDirectory()
      ? listFiles(path.join(directory, entry.name), relative)
      : [relative];
  });
}

test('trusted tooling builds and independently checks all three host packages', () => {
  withSourceFixture(({ root, plugin, temporary }) => {
    const output = path.join(temporary, 'packages');
    succeeds(runTool(root, 'build', '--plugin', identity, '--host', 'all', '--output', output));
    const index = JSON.parse(fs.readFileSync(path.join(output, 'index.json'), 'utf8'));
    const packages = index.plugins[identity].hosts;
    assert.deepEqual(Object.keys(packages).sort(), ['claude', 'codex', 'zcode']);

    for (const [host, entry] of Object.entries(packages)) {
      const packageRoot = path.join(output, entry.package_dir);
      const checked = succeeds(runTool(root, 'package', 'check', '--path', packageRoot, '--host', host));
      assert.equal(JSON.parse(checked.stdout).ok, true);
      assert.deepEqual(fs.readdirSync(path.join(packageRoot, referenceDirectory)).sort(), references);
      for (const relative of [skillPath, ...references.map((name) => `${referenceDirectory}/${name}`)]) {
        assert.deepEqual(fs.readFileSync(path.join(packageRoot, relative)), fs.readFileSync(path.join(plugin, relative)));
      }
      assert.ok(fs.existsSync(path.join(packageRoot, iconPath)), 'The CodeStack PNG must be packaged for every host.');
      assert.deepEqual(fs.readFileSync(path.join(packageRoot, iconPath)), fs.readFileSync(path.join(plugin, iconPath)));
      assert.ok(listFiles(packageRoot).every((relative) =>
        !relative.split('/').some((part) => ['tests', 'evals', 'AGENTS.md'].includes(part))),
      'Development instructions, tests and evaluation fixtures must not enter a host package.');
    }

    const codexPackage = path.join(output, packages.codex.package_dir);
    const codexManifest = JSON.parse(fs.readFileSync(path.join(codexPackage, 'plugin.json'), 'utf8'));
    const codexInterface = codexManifest.extensions['com.openai'].interface;
    assert.equal(codexInterface.logo, `./${iconPath}`);
    assert.equal(codexInterface.composerIcon, `./${iconPath}`);
    const zcodeMarket = JSON.parse(fs.readFileSync(path.join(output, 'zcode/marketplace.json'), 'utf8'));
    const zcodeEntry = zcodeMarket.plugins.find((entry) => entry.name === identity);
    assert.equal(zcodeEntry.displayName, 'CodeStack');
    assert.match(zcodeEntry.icon, /^https:\/\/raw\.githubusercontent\.com\/Zack-Zz\/ai-code\/[0-9a-f]{40}\/plugins\/ai-code-stack-standards\/assets\/codestack\.png$/);
    fs.appendFileSync(path.join(codexPackage, referenceDirectory, 'jpa.md'), '\nUnexpected rule change.\n');
    const tampered = runTool(root, 'package', 'check', '--path', codexPackage, '--host', 'codex');
    assert.notEqual(tampered.status, 0, tampered.stdout + tampered.stderr);
    assert.match(tampered.stdout + tampered.stderr, /jpa\.md/);
  });
});

const brokenSources = [
  {
    name: 'an unresolved rule reference',
    mutate(plugin) {
      fs.appendFileSync(path.join(plugin, skillPath), '\n[Missing required rule](references/missing-rule.md)\n');
    },
    diagnostic: /missing-rule\.md/,
  },
  ...['jpa.md', 'frontend.md'].map((rule) => ({
    name: `a required rule omitted from the resource allowlist (${rule})`,
    mutate(plugin) {
      const filename = path.join(plugin, 'product.json');
      const product = JSON.parse(fs.readFileSync(filename, 'utf8'));
      const original = JSON.stringify(product.resources);
      product.resources = product.resources.filter((entry) => entry.source !== `${referenceDirectory}/${rule}`);
      for (const entry of product.resources) {
        if (entry.source === referenceDirectory) {
          entry.include = entry.include.filter((name) => name !== rule);
        }
      }
      assert.notEqual(JSON.stringify(product.resources), original, `The fixture must actually remove the ${rule} allowance.`);
      fs.writeFileSync(filename, JSON.stringify(product));
    },
    diagnostic: new RegExp(rule.replaceAll('.', '\\.')),
  })),
  {
    name: 'a marketplace icon omitted from the resource allowlist',
    mutate(plugin) {
      const filename = path.join(plugin, 'product.json');
      const product = JSON.parse(fs.readFileSync(filename, 'utf8'));
      product.resources = product.resources.filter((entry) => entry.source !== iconPath);
      fs.writeFileSync(filename, JSON.stringify(product));
    },
    diagnostic: /icon_path.*registered PNG/,
  },
  {
    name: 'a Codex interface bound to the wrong skill',
    mutate(plugin) {
      const filename = path.join(plugin, 'adapters/codex/interfaces.json');
      const interfaces = JSON.parse(fs.readFileSync(filename, 'utf8'));
      interfaces.skills['unrelated-skill'] = interfaces.skills['code-standards'];
      delete interfaces.skills['code-standards'];
      fs.writeFileSync(filename, JSON.stringify(interfaces));
    },
    diagnostic: /skills|interface/,
  },
];

for (const mutation of brokenSources) {
  test(`trusted tooling rejects ${mutation.name} before publishing output`, () => {
    withSourceFixture(({ root, plugin, temporary }) => {
      mutation.mutate(plugin);
      const validated = runTool(root, 'validate', '--all');
      assert.equal(validated.status, 2, validated.stdout + validated.stderr);
      assert.match(validated.stdout + validated.stderr, mutation.diagnostic);
      const output = path.join(temporary, 'rejected-output');
      const built = runTool(root, 'build', '--plugin', identity, '--host', 'all', '--output', output);
      assert.equal(built.status, 2, built.stdout + built.stderr);
      assert.equal(fs.existsSync(output), false, 'An invalid plugin must not publish package output.');
    });
  });
}
