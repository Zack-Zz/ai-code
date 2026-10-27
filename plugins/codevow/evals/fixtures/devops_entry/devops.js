// Disposable DevOps navigation fixture, not a production application.
const defaultApi = require('./api.js');

function getProductLineEntries() {
  return [{ id: 'applications', label: '产品线应用端' }];
}

function activateEntry(entryId, productLineId, api = defaultApi) {
  if (!productLineId) {
    throw new Error('productLineId is required');
  }
  if (entryId === 'applications') {
    return api.listApplicationEnds(productLineId);
  }
  throw new Error(`unknown entry: ${entryId}`);
}

module.exports = { getProductLineEntries, activateEntry };
