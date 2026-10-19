#!/usr/bin/env node
// Package contracts only: passing this runner does not certify model behavior.
const fs = require('node:fs');
const path = require('node:path');
const { spawnSync } = require('node:child_process');

const files = fs.readdirSync(__dirname)
  .filter((file) => file.endsWith('.test.js'))
  .sort()
  .map((file) => path.join(__dirname, file));

if (files.length === 0) {
  console.error('CodeStack has no contract test files.');
  process.exit(1);
}

const childEnvironment = { ...process.env };
delete childEnvironment.NODE_TEST_CONTEXT;
let status = 0;
for (const file of files) {
  const result = spawnSync(process.execPath, [file], { stdio: 'inherit', env: childEnvironment });
  if (result.error || result.signal || result.status === null) {
    console.error(result.error?.message || `Test process terminated: ${result.signal || 'unknown status'}`);
    status = status || 1;
  } else if (result.status !== 0) {
    status = status || result.status;
  }
}
process.exit(status);
