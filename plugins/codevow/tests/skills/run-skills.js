#!/usr/bin/env node
/**
 * Aggregates every tests/skills/*.test.js (contract tests for skill sources)
 * and aggregates a strict verdict from exit statuses only — output is never
 * parsed. These are structural contract checks; they do not certify model
 * behavior in a real host session.
 */

const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const dir = __dirname;
const files = fs.readdirSync(dir).filter((f) => f.endsWith('.test.js')).sort();

if (files.length === 0) {
  console.error('Error: no skills contract tests found under tests/skills/.');
  process.exit(1);
}

let failed = false;
for (const file of files) {
  console.log(`\n━━━ skills: ${file} ━━━`);
  const result = spawnSync('node', [path.join(dir, file)], { stdio: 'inherit' });
  if (result.error) {
    console.error(`✗ ${file}: failed to start (${result.error.message})`);
    failed = true;
  } else if (result.signal) {
    console.error(`✗ ${file}: terminated by signal ${result.signal}`);
    failed = true;
  } else if (result.status !== 0) {
    console.error(`✗ ${file}: exit status ${result.status}`);
    failed = true;
  } else {
    console.log(`✓ ${file}`);
  }
}

console.log(`\n${failed ? 'SKILLS CONTRACT TESTS FAILED' : 'SKILLS CONTRACT TESTS PASSED'} (${files.length} file${files.length === 1 ? '' : 's'})`);
process.exit(failed ? 1 : 0);
