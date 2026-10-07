# T07 real-session acceptance — environment blockage record (2026-10-01)

Historical record, superseded by [2026-10-02 probes](blocked-env-2026-10-02.md).
The earlier entry-point search was incomplete: both applications have bundled
CLIs. Preserve this note as history, not the current diagnosis.

Delivery status for real-host acceptance: **blocked_env** for every declared
host combination on this machine. No A01–A22 host session was run; no
`accepted` claim is made anywhere in this delivery. Deterministic manager and
package checks (A23–A25) DID run for real via `evals/grade.py` and passed.

## ZCode — blocked

- Entry attempted: `which zcode` → not found. No headless CLI exists.
- `/Applications/ZCode.app` exists and is the authoring session's own host;
  no documented automation entry to create an isolated new session, and
  driving/restarting the running desktop app is outside the authorized scope.
- Missing conditions: a user-driven fresh ZCode session (new chat) with the
  package registered from `dist/zcode`, following docs/installation.md.

## Codex — blocked

- Entry attempted: `codex --version` →
  `Error: spawn .../@openai/codex-darwin-arm64/vendor/aarch64-apple-darwin/codex/codex ENOENT`
  (wrapper present at `~/.nvm/.../bin/codex`, native binary missing — unchanged
  from the design-phase probe on 2026-10-01).
- `~/.codex/` exists with `auth.json`; not modified (out of bounds).
- No Codex/OpenAI desktop app under `/Applications`.
- Repairing the global npm install is out of bounds for this work.
- Missing conditions: a working `codex` CLI or desktop install, then the
  manual acceptance path in docs/installation.md.

## What this does NOT mean

Static checks, package checks and the deterministic eval scenarios passing do
not substitute for host behavior evidence. Capability statuses in
`adapters/*/capabilities.md` remain `unverified` until real sessions exist.
Overall delivery level: `implemented_with_acceptance_blocked` (T07 pending).
