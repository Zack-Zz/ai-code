// Disposable local API fixture; no network or persistent business data.
function listApplicationEnds(productLineId) {
  return { productLineId, applicationEnds: [] };
}

function initializeApplicationEnds(productLineId) {
  return { productLineId, applicationEnds: ['web', 'mobile'] };
}

module.exports = { listApplicationEnds, initializeApplicationEnds };
