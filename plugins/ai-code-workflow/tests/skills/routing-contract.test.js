/**
 * Source wiring only: every directly callable skill reaches the same request
 * and authorization contract before its specialist steps. Real decisions need
 * the natural-request host scenarios in evals/cases.json.
 */
const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..', '..');
const read = (name) => fs.readFileSync(path.join(root, name), 'utf8');
const contract = 'request-and-authorization-context';
const workflow = read('skills/workflow/SKILL.md');
const anchors = [...workflow.matchAll(/^#{1,6} (.+)$/gm)]
  .map((match) => match[1].toLowerCase().replace(/[^a-z0-9 -]/g, '').replace(/ /g, '-'));
let failures = 0;

for (const name of ['tdd', 'debugging', 'review', 'verification', 'review-results']) {
  try {
    const body = read(`skills/${name}/SKILL.md`);
    const links = [...body.matchAll(/\[[^\]]+\]\((\.\.\/workflow\/SKILL\.md)#([^ )]+)\)/g)]
      .filter((match) => match[2] === contract);
    assert.strictEqual(links.length, 1, `${name}: one shared authorization entry reference`);
    assert.ok(anchors.includes(contract), 'shared authorization anchor must resolve');
    assert.ok(links[0].index < body.indexOf('\n## '), `${name}: check precedes specialist steps`);
    console.log(`PASS ${name}: direct entry reaches shared contract`);
  } catch (error) {
    failures++;
    console.error(error.message);
  }
}

try {
  const entries = JSON.parse(read('adapters/codex/interfaces.json')).skills;
  for (const name of ['workflow', 'tdd', 'debugging', 'review', 'verification']) {
    assert.ok(entries[name].short_description.length >= 25 &&
      entries[name].short_description.length <= 64, `${name}: UI description length`);
    assert.ok(entries[name].default_prompt.includes(`$${name}`), `${name}: explicit skill invocation`);
    assert.strictEqual(entries[name].allow_implicit_invocation, true, `${name}: stays discoverable`);
  }
  const manifest = JSON.parse(read('adapters/codex/plugin.json'));
  assert.deepStrictEqual(manifest.extensions['com.openai'].interface.defaultPrompt,
    [entries.workflow.default_prompt], 'plugin entry and workflow interface must agree');
  console.log('PASS native entry metadata stays consistent and discoverable');
} catch (error) {
  failures++;
  console.error(error.message);
}
process.exit(failures ? 1 : 0);
