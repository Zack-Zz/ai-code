// Disposable acceptance fixture, not business code.
// Transition table: idle --start--> active --finish--> done; reset returns to idle.
// Scenarios (A03/A06) add a `paused` state test-first; the baseline must not have it.

const TRANSITIONS = {
  idle: { start: 'active' },
  active: { finish: 'done' },
  done: { reset: 'idle' },
};

function transition(state, event) {
  const table = TRANSITIONS[state];
  if (!table) {
    throw new Error(`unknown state: ${state}`);
  }
  const next = table[event];
  if (!next) {
    throw new Error(`event ${event} not allowed from ${state}`);
  }
  return next;
}

module.exports = { transition, TRANSITIONS };
