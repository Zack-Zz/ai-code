#!/usr/bin/env node
/**
 * Unified test entry: runs every test group and aggregates a strict verdict.
 *
 * Usage:
 *   node tests/run-suite.js            # run the repo's real test groups
 *   node tests/run-suite.js SPEC.json  # run groups from a spec file
 *                                        ([{ name, cmd, args, cwd? }, ...])
 *
 * Verdict rules (exit status only, test output is never parsed):
 *   - every group runs even if an earlier one failed;
 *   - a group that cannot start, exits non-zero, or is killed by a signal
 *     marks the whole run failed;
 *   - exit code is 0 only when all groups exited 0.
 */

const { spawnSync } = require('child_process');
const fs = require('fs');
const path = require('path');

const root = path.resolve(__dirname, '..');

function safePath(relative) {
  const target = path.resolve(root, relative);
  const parts = path.relative(root, target).split(path.sep);
  if (parts[0] === '..' || path.isAbsolute(path.relative(root, target))) {
    throw new Error(`path escapes repository: ${relative}`);
  }
  let current = root;
  for (const part of parts) {
    current = path.join(current, part);
    if (!fs.existsSync(current)) {
      // lstat also detects dangling symlinks, which existsSync cannot see.
      try {
        if (fs.lstatSync(current).isSymbolicLink()) throw new Error(`symlink: ${relative}`);
      } catch (error) {
        if (error.code !== 'ENOENT') throw error;
      }
      return target;
    }
    if (fs.lstatSync(current).isSymbolicLink()) throw new Error(`symlink: ${relative}`);
  }
  return target;
}

function defaultGroups() {
  const catalog = JSON.parse(fs.readFileSync(safePath('catalog.json'), 'utf8'));
  if (!catalog || catalog.schema_version !== 1 || !Array.isArray(catalog.plugins) ||
      catalog.plugins.length === 0 || Object.keys(catalog).some((key) => !['schema_version', 'plugins'].includes(key))) {
    throw new Error('catalog must contain schema_version 1 and a non-empty plugins array');
  }
  const groups = [
    { name: 'node: run-suite self tests', cmd: process.execPath, args: [safePath('tests/run-suite.test.js')], cwd: root },
    { name: 'python: public tooling unit/integration', cmd: 'python3', args: [safePath('tests/run_python_tests.py')], cwd: root }
  ];
  const seen = new Set();
  for (const entry of catalog.plugins) {
    if (!entry || Object.keys(entry).length !== 1 || typeof entry.path !== 'string' ||
        !/^plugins\/[A-Za-z0-9][A-Za-z0-9._-]*$/.test(entry.path) || seen.has(entry.path)) {
      throw new Error(`invalid or duplicate plugin registration: ${JSON.stringify(entry)}`);
    }
    seen.add(entry.path);
    const pluginRoot = safePath(entry.path);
    if (!fs.existsSync(pluginRoot) || !fs.statSync(pluginRoot).isDirectory()) {
      throw new Error(`registered plugin directory is missing: ${entry.path}`);
    }
    const runners = [
      { suffix: 'tests/skills/run-skills.js', cmd: process.execPath, label: 'node: skills contract tests' },
      { suffix: 'tests/run_python_tests.py', cmd: 'python3', label: 'python: unit/integration' }
    ];
    let found = false;
    for (const runner of runners) {
      const file = safePath(`${entry.path}/${runner.suffix}`);
      if (fs.existsSync(file)) {
        if (!fs.statSync(file).isFile()) throw new Error(`test runner must be a file: ${file}`);
        groups.push({ name: `${entry.path} ${runner.label}`, cmd: runner.cmd, args: [file], cwd: pluginRoot });
        found = true;
      }
    }
    if (!found) groups.push({ name: entry.path, error: 'no test groups found for registered plugin' });
  }
  return groups;
}

function loadGroups() {
  const specPath = process.argv[2];
  if (!specPath) return defaultGroups();

  let spec;
  try {
    spec = JSON.parse(fs.readFileSync(specPath, 'utf8'));
  } catch (error) {
    console.error(`Error: cannot read spec ${specPath}: ${error.message}`);
    process.exit(1);
  }
  if (!Array.isArray(spec) || spec.some((g) => !g || !g.cmd || !Array.isArray(g.args))) {
    console.error(`Error: spec ${specPath} must be an array of { name, cmd, args[, cwd] }`);
    process.exit(1);
  }
  return spec;
}

let groups;
try {
  groups = loadGroups();
} catch (error) {
  console.error(`Error: cannot load test groups: ${error.message}`);
  process.exit(1);
}
let failed = false;

if (groups.length === 0) {
  console.error('Error: test group list is empty — refusing to report vacuous success.');
  process.exit(1);
}

for (const group of groups) {
  const label = group.name || `${group.cmd} ${group.args.join(' ')}`;
  console.log(`\n━━━ ${label} ━━━`);

  if (group.error) {
    console.error(`✗ ${label}: ${group.error}`);
    failed = true;
    continue;
  }

  const result = spawnSync(group.cmd, group.args, {
    cwd: group.cwd,
    stdio: 'inherit'
  });

  if (result.error) {
    console.error(`✗ ${label}: failed to start (${result.error.message})`);
    failed = true;
  } else if (result.signal) {
    console.error(`✗ ${label}: terminated by signal ${result.signal}`);
    failed = true;
  } else if (result.status !== 0) {
    console.error(`✗ ${label}: exit status ${result.status}`);
    failed = true;
  } else {
    console.log(`✓ ${label}`);
  }
}

console.log(`\n${failed ? 'SUITE FAILED' : 'SUITE PASSED'} (${groups.length} group${groups.length === 1 ? '' : 's'})`);
process.exit(failed ? 1 : 0);
