# T07 host probes and remaining blockers — 2026-10-02

The 2026-10-01 entry-point diagnosis was incomplete. Both applications bundle
usable official CLIs; no global repair or application restart was needed.
This supersedes the earlier claim that no Codex desktop application or ZCode
headless entry exists. Full A01–A22 acceptance remains pending.

## Codex

- ChatGPT's bundled `codex-cli/bin/codex`: version **0.159.2**.
- Native marketplace add and plugin add/list succeeded in a private temporary
  `CODEX_HOME`; the catalog reports the plugin installed and enabled.
- A real read-only smoke session used the existing `gpt-6.1-sol` selection.
  It discovered the installed workflow path but could not read it:
  `sandbox-exec: sandbox_apply: Operation not permitted` in the nested sandbox.
  This is not a successful skill invocation or policy-loading acceptance.
- Automatic approval review rejected the proposed outer-sandbox retry because
  authorization to send the specific fixture files to the external model
  service was not explicit. Approval for only synthetic fixtures and public
  plugin materials has been requested; no retry bypasses that decision.
- The private temporary credential copy was removed after the probe. Normal
  user configuration, credentials and caches were not modified.

## ZCode

- Bundled `glm/zcode.cjs`: version **0.16.9**, with documented headless
  prompts, app-server, plugin and skill commands.
- Native validation accepted the package with no diagnostics; marketplace
  registration succeeded using isolated storage and a temporary workspace.
- Native project-scope installation attempted to write
  `~/.zcode/cli/config.json` and was denied by the outer filesystem sandbox.
  No ordinary global configuration is authorized for this task. No model
  session or successful installation is claimed.

## Verification boundary

Temporary native registration, package validation and a model's recognition
of a catalog entry do not prove actual skill loading, task behavior, reviewer
restrictions or complete T07. The full host matrix remains unverified;
delivery stays `implemented_with_acceptance_blocked`.
