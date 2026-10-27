// Baseline suite for the node_status fixture (grader assertions are separate).
const assert = require('assert');
const { transition } = require('./status.js');

// idle -> active -> done
assert.strictEqual(transition('idle', 'start'), 'active');
assert.strictEqual(transition('active', 'finish'), 'done');
assert.strictEqual(transition('done', 'reset'), 'idle');

// error paths
assert.throws(() => transition('nope', 'start'), /unknown state/);
assert.throws(() => transition('idle', 'finish'), /not allowed/);

// input not mutated (frozen-object contract)
const frozen = Object.freeze({ state: 'idle' });
assert.doesNotThrow(() => transition(frozen.state, 'start'));

console.log('node_status baseline: all assertions passed');
