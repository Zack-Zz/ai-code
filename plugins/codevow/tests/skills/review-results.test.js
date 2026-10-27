/**
 * Contract tests for the human-readable review-results skill.
 *
 * Run with: node tests/skills/review-results.test.js
 *
 * Integration tests that asserted retired entry points (agents/, commands/,
 * contexts/, scripts/bootstrap-project.sh) delegated to this skill were
 * removed together with those features; only the skill's presentation
 * contract is asserted here.
 */

const assert = require('assert');
const fs = require('fs');
const path = require('path');

const root = path.join(__dirname, '..', '..');

function read(relativePath) {
  return fs.readFileSync(path.join(root, relativePath), 'utf8');
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

function runTests() {
  console.log('\n=== Testing review-results skill ===\n');
  let passed = 0;
  let failed = 0;

  if (test('defines a reader-first review contract', () => {
    const skill = read('skills/review-results/SKILL.md');
    const requiredConcepts = [
      '一句话结论',
      '业务链路',
      '异常节点',
      '问题产生位置',
      '业务入口',
      '影响扩散位置',
      '缺失测试',
      '用户感受',
      '修复目标',
      '验证边界',
    ];
    for (const concept of requiredConcepts) {
      assert.ok(skill.includes(concept), `Missing review concept: ${concept}`);
    }
  })) passed++; else failed++;

  if (test('keeps the primary clickable code link next to the abnormal node', () => {
    const skill = read('skills/review-results/SKILL.md');
    assert.match(skill, /异常节点[\s\S]{0,240}问题代码：\[[^\]]+\]\(\/[^)]+:\d+\)/);
    const linkIndex = skill.indexOf('问题代码：[');
    const fencesBeforeLink = (skill.slice(0, linkIndex).match(/```/g) || []).length;
    assert.strictEqual(
      fencesBeforeLink % 2,
      0,
      'Primary code link must not be inside a fenced code block because it would not be clickable'
    );
  })) passed++; else failed++;

  if (test('defines one unambiguous severity to action mapping', () => {
    const skill = read('skills/review-results/SKILL.md');
    assert.match(skill, /CRITICAL[\s\S]{0,120}阻塞/);
    assert.match(skill, /HIGH[\s\S]{0,120}阻塞/);
    assert.match(skill, /MEDIUM[\s\S]{0,120}应修复/);
    assert.match(skill, /LOW[\s\S]{0,120}可选优化/);
  })) passed++; else failed++;

  console.log(`\nPassed: ${passed}`);
  console.log(`Failed: ${failed}`);
  process.exit(failed > 0 ? 1 : 0);
}

runTests();
