const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '../..');
const product = JSON.parse(fs.readFileSync(path.join(root, 'product.json')));
assert.equal(product.product_id, 'codestack');
assert.equal(product.schema_version, 2);
assert.ok(product.hosts.includes('dsh'));
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'adapters/dsh/package.json')));
assert.equal(manifest.type, 'module');
assert.deepEqual(manifest.dsh, { bundle: { patch: './cordis.patch.yml' } });
assert.equal(manifest.engines.dsh, '>=0.2.1-rc.2');
for (const requirement of Object.values(manifest.peerDependencies)) {
  assert.equal(requirement, manifest.engines.dsh, 'DSH peers retain the same minimum as the runtime');
}
assert.ok(!manifest.scripts && !manifest.private);
const patch = fs.readFileSync(path.join(root, 'adapters/dsh/cordis.patch.yml'), 'utf8');
assert.match(patch, /includeDefaultRoots: false/);
assert.match(patch, /watch: false/);
assert.match(patch, /bundledSkillDir:/);
assert.match(patch, /providerName: codestack/);
assert.ok(!('version' in manifest) && !('name' in manifest), 'product owns generated identity');
assert.equal(JSON.parse(fs.readFileSync(path.join(root, 'release.json'))).acceptance.dsh, null);
console.log('DSH bundle identity and native provider contracts passed');
const skill = fs.readFileSync(path.join(root, 'skills/code-standards/SKILL.md'), 'utf8');
const instructions = skill.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, '').trim();
// Mirror DSH renderSkillContent framing with the repository's 300-character path budget.
const rendered = `<skill_content name="code-standards">\n<skill_resources>\nBase directory for this skill: ${'x'.repeat(300)}\nResolve relative paths mentioned by this skill against the base directory before using them. Load referenced resources only as needed.\n</skill_resources>\n\n<skill_instructions>\n${instructions}\n</skill_instructions>\n</skill_content>`;
const renderedLength = [...rendered].length;
assert.ok(renderedLength < 8192, `CodeStack DSH skill length ${renderedLength} must fit the 8192-point pressure-pruning budget`);
for (const resource of ['java.md', 'java-design.md']) {
  const body = fs.readFileSync(path.join(root, 'skills/code-standards/references', resource), 'utf8');
  assert.ok([...body].length < 7000, `${resource}: reserve room for read framing`);
}
assert.match(fs.readFileSync(path.join(root, 'skills/code-standards/references/java.md'), 'utf8'), /java-design.md/);
assert.ok(!product.host_resources.dsh.some(entry => entry.source.endsWith('.js')), 'CodeStack has no custom executable module');
