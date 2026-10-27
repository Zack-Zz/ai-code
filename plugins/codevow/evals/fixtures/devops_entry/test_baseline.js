const assert = require('assert');
const { getProductLineEntries, activateEntry } = require('./devops.js');
const { initializeApplicationEnds } = require('./api.js');

assert.deepStrictEqual(getProductLineEntries().find((entry) => entry.id === 'applications'),
  { id: 'applications', label: '产品线应用端' });
assert.deepStrictEqual(activateEntry('applications', 'line-1'), {
  productLineId: 'line-1', applicationEnds: [],
});
assert.throws(() => activateEntry('applications', ''), /productLineId is required/);
assert.throws(() => activateEntry('missing', 'line-1'), /unknown entry/);

// Initialization exists in the API; navigation does not yet expose it.
assert.deepStrictEqual(initializeApplicationEnds('line-1'), {
  productLineId: 'line-1', applicationEnds: ['web', 'mobile'],
});
console.log('devops_entry baseline: all assertions passed');
