/**
 * Contract checks for the v1 skill sources, Codex interface metadata and the
 * acceptance case/fixture inventory. These are STRUCTURE and REFERENCE checks
 * only — they never certify model behavior in a real host session (that is
 * T07's job via evals/).
 *
 * Run with: node tests/skills/core-skills.test.js
 */

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..', '..');
const read = (rel) => fs.readFileSync(path.join(root, rel), 'utf8');
const exists = (rel) => fs.existsSync(path.join(root, rel));

function parseFrontmatter(rel) {
  const text = read(rel);
  const lines = text.split('\n');
  assert.strictEqual(lines[0], '---', `${rel}: must start with frontmatter`);
  const meta = {};
  let ended = false;
  for (let i = 1; i < lines.length; i++) {
    if (lines[i] === '---') { ended = true; break; }
    const m = lines[i].match(/^([A-Za-z_][A-Za-z0-9_-]*):[ \t]*(\S.*)$/);
    assert.ok(m, `${rel}: frontmatter keys must be single-line (line ${i + 1})`);
    const [, key, value] = m;
    assert.ok(!meta[key], `${rel}: duplicate frontmatter key ${key}`);
    meta[key] = value.trim();
  }
  assert.ok(ended, `${rel}: unterminated frontmatter`);
  return meta;
}

function test(name, fn) {
  try {
    fn();
    console.log(`  \u2713 ${name}`);
    return true;
  } catch (error) {
    console.log(`  \u2717 ${name}`);
    console.log(`    Error: ${error.message}`);
    return false;
  }
}

const CORE = ['workflow', 'tdd', 'debugging', 'review', 'verification'];
const ALL_SKILLS = [...CORE, 'review-results'];

function runTests() {
  console.log('\n=== Testing v1 skill contracts (structure only) ===\n');
  let passed = 0, failed = 0;

  const cases = [
    ['six skills exist with valid single-line frontmatter', () => {
      for (const name of ALL_SKILLS) {
        const meta = parseFrontmatter(`skills/${name}/SKILL.md`);
        assert.strictEqual(meta.name, name);
        assert.ok(meta.description && meta.description.length > 10, `${name}: needs a description`);
        for (const key of Object.keys(meta)) {
          assert.ok(['name', 'description', 'origin'].includes(key), `${name}: unknown frontmatter key ${key}`);
        }
      }
    }],

    ['each skill body carries its load-bearing contract concepts', () => {
      const expectations = {
        workflow: ['read-only', 'depth', 'short', 'standard', 'architectural', 'critical', 'authorization', 'tdd', 'debugging', 'review', 'verification'],
        tdd: ['RED', 'GREEN', 'REFACTOR', 'environment', 'baseline', 'refactor'],
        debugging: ['hypothesis', 'experiment', 'evidence', 'reproduction'],
        review: ['independent', 'review-results', 'reviewer-contract.md', 'policy_only', 'critical'],
        verification: ['levels', 'final code state', 'stale'],
      };
      for (const [name, concepts] of Object.entries(expectations)) {
        const body = read(`skills/${name}/SKILL.md`).toLowerCase();
        for (const concept of concepts) {
          assert.ok(body.includes(concept.toLowerCase()), `${name}: missing contract concept '${concept}'`);
        }
      }
    }],

    ['review keeps a single shared reviewer contract and delegates presentation', () => {
      assert.ok(exists('skills/review/references/reviewer-contract.md'));
      const contract = read('skills/review/references/reviewer-contract.md');
      assert.ok(contract.includes('policy_only') || contract.includes('host_allowlist'));
      assert.ok(contract.toLowerCase().includes('do not fix'));
    }],

    ['workflow plans before implementation and separates authorizations', () => {
      const body = read('skills/workflow/SKILL.md');
      assert.ok(/collaborative/.test(body) && /continuous/.test(body));
      assert.ok(/never creates authorization|never imply|grants nothing/i.test(body));
    }],

    ['Codex interfaces.json is the single interface metadata source', () => {
      const interfaces = JSON.parse(read('adapters/codex/interfaces.json'));
      assert.strictEqual(interfaces.schema_version, 1);
      const names = Object.keys(interfaces.skills).sort();
      assert.deepStrictEqual(names, [...ALL_SKILLS].sort());
      for (const [name, data] of Object.entries(interfaces.skills)) {
        assert.deepStrictEqual(
          Object.keys(data).sort(),
          ['allow_implicit_invocation', 'brand_color', 'default_prompt', 'display_name', 'short_description'],
          `${name}: interface entry fields`);
        assert.strictEqual(typeof data.allow_implicit_invocation, 'boolean');
      }
    }],

    ['review-results interface values migrated verbatim from the retired yaml', () => {
      const data = JSON.parse(read('adapters/codex/interfaces.json')).skills['review-results'];
      assert.strictEqual(data.display_name, 'Review Results');
      assert.strictEqual(data.brand_color, '#3B82F6');
      assert.strictEqual(
        data.short_description,
        'Turn technical review findings into clear business flows, impact, decisions, and clickable evidence');
      assert.strictEqual(
        data.default_prompt,
        'Present these review findings using the review-results decision-first format');
      assert.strictEqual(data.allow_implicit_invocation, true);
      // the old per-skill metadata position is retired — no second source
      assert.ok(!exists('skills/review-results/agents'),
        'skills/review-results/agents/ must not exist (metadata migrated to interfaces.json)');
    }],

    ['cases.json defines exactly A01..A25 with the fixed shape', () => {
      const doc = JSON.parse(read('evals/cases.json'));
      assert.strictEqual(doc.schema_version, 1);
      const ids = doc.cases.map((c) => c.case_id);
      const expected = Array.from({ length: 25 }, (_, i) => `A${String(i + 1).padStart(2, '0')}`);
      assert.deepStrictEqual(ids, expected);
      const fixedFields = ['case_id', 'kind', 'fixture', 'policy_mode', 'turns', 'checks', 'required_evidence', 'critical'];
      const fixtures = ['python_labels', 'python_auth', 'node_status', 'state_resume', 'git_permissions', 'managed_package'];
      const methods = ['file_hash', 'behavior_test', 'process_status', 'trace_order', 'git_state', 'package_check', 'manual_review'];
      const effects = ['blocking', 'unsupported_scope', 'informational'];
      for (const c of doc.cases) {
        assert.deepStrictEqual(Object.keys(c).sort(), [...fixedFields].sort(), `${c.case_id}: exact fields`);
        assert.ok(['agent', 'manager', 'package'].includes(c.kind), `${c.case_id}: kind`);
        assert.ok(fixtures.includes(c.fixture), `${c.case_id}: unknown fixture ${c.fixture}`);
        assert.ok(['collaborative', 'continuous'].includes(c.policy_mode));
        assert.ok(c.turns.length >= 1);
        for (const t of c.turns) {
          assert.deepStrictEqual(Object.keys(t).sort(), ['content', 'phase', 'role']);
          assert.strictEqual(t.role, 'user');
          assert.ok(t.content.length > 5, `${c.case_id}: turn content is a real input`);
        }
        assert.ok(c.checks.length >= 1);
        for (const chk of c.checks) {
          assert.deepStrictEqual(Object.keys(chk).sort(), ['check_id', 'expected', 'failure_effect', 'method']);
          assert.ok(methods.includes(chk.method), `${c.case_id}/${chk.check_id}: method`);
          assert.ok(effects.includes(chk.failure_effect), `${c.case_id}/${chk.check_id}: failure_effect`);
          assert.ok(chk.expected && chk.expected.length > 10, `${c.case_id}/${chk.check_id}: expected must be concrete`);
        }
        assert.ok(Array.isArray(c.required_evidence) && c.required_evidence.length >= 1);
        assert.strictEqual(typeof c.critical, 'boolean');
      }
      const criticalSet = ids.filter((id, i) => doc.cases[i].critical);
      assert.deepStrictEqual(
        criticalSet,
        ['A02', 'A03', 'A06', 'A09', 'A13', 'A14', 'A15', 'A16', 'A18', 'A19', 'A20', 'A21'],
        'critical flag must mark exactly the acceptance-matrix key set');
    }],

    ['all six fixtures exist with their required props', () => {
      assert.ok(exists('evals/fixtures/python_labels/labels.py'));
      assert.ok(exists('evals/fixtures/python_labels/test_baseline.py'));
      assert.ok(exists('evals/fixtures/python_labels/mutations/a04_break_labels.py'));
      assert.ok(exists('evals/fixtures/python_labels/extras/test_history_failure.py'));
      assert.ok(exists('evals/fixtures/python_auth/auth.py'));
      assert.ok(exists('evals/fixtures/python_auth/audit.py'));
      assert.ok(exists('evals/fixtures/python_auth/test_baseline.py'));
      assert.ok(exists('evals/fixtures/node_status/status.js'));
      assert.ok(exists('evals/fixtures/node_status/test_baseline.js'));
      assert.ok(exists('evals/fixtures/node_status/user/notes.md'));
      assert.ok(exists('evals/fixtures/state_resume/calc.py'));
      assert.ok(exists('evals/fixtures/state_resume/.ai-workflow/tasks/resume-demo/task.json'));
      assert.ok(exists('evals/fixtures/state_resume/.ai-workflow/tasks/other-task/task.json'));
      assert.ok(exists('evals/fixtures/state_resume/.ai-workflow/tasks/resume-demo/evidence/ev-baseline.json'));
      assert.ok(exists('evals/fixtures/git_permissions/setup.py'));
      assert.ok(exists('evals/fixtures/managed_package/README.md'));
    }],

    ['state_resume fixture ships one deliberately stale evidence fingerprint', () => {
      const task = JSON.parse(read('evals/fixtures/state_resume/.ai-workflow/tasks/resume-demo/task.json'));
      const evidence = JSON.parse(read('evals/fixtures/state_resume/.ai-workflow/tasks/resume-demo/evidence/ev-baseline.json'));
      const realCalcSha = require('crypto').createHash('sha256')
        .update(read('evals/fixtures/state_resume/calc.py')).digest('hex');
      assert.notStrictEqual(
        evidence.subject_fingerprints['calc.py'], realCalcSha,
        'fixture must ship a stale calc.py fingerprint to exercise re-validation');
      const registered = task.evidence_refs[0].content_sha256;
      const actual = require('crypto').createHash('sha256')
        .update(fs.readFileSync(path.join(root, 'evals/fixtures/state_resume/.ai-workflow/tasks/resume-demo/evidence/ev-baseline.json')))
        .digest('hex');
      assert.strictEqual(registered, actual, 'registered evidence hash must match the shipped file');
    }],
  ];

  for (const [name, fn] of cases) {
    if (test(name, fn)) passed++; else failed++;
  }

  console.log(`\nPassed: ${passed}`);
  console.log(`Failed: ${failed}`);
  process.exit(failed > 0 ? 1 : 0);
}

runTests();
