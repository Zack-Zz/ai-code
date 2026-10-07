# Codex adapter capabilities

Current probe date: 2026-10-02. Portable root `plugin.json` and the native
`.agents/plugins/marketplace.json` are generated separately from ZCode.

| Capability | Status | Evidence and limits |
|---|---|---|
| discovery | unverified for the final bundle | Native add/list succeeded in an isolated profile; a smoke session saw the earlier probe bundle in its skill catalog. Full current-bundle loading is pending. |
| explicit_invocation | unverified | Read commands failed in the nested sandbox before the skill body loaded. |
| automatic_selection | unverified | No qualifying unprompted selection case completed. |
| policy_loading | unverified | Packaged resolver and material-level consumer probe passed; actual host execution remains pending. |
| native_subagents | unverified | No runtime reviewer case completed; absence of custom plugin-agent fields does not prove the host lacks subagents. |
| reviewer_restriction | unverified; enforcement=policy_only | Shared contract gives read-only instructions; no host allowlist is claimed. |
| workspace_isolation | unverified | Native read-only sandbox selected, but nested sandbox setup prevented file reads. |

## Native probes

- Ordinary terminal wrapper still fails with ENOENT.
- ChatGPT bundles an official CLI at
  `/Applications/ChatGPT.app/Contents/Resources/codex-cli/bin/codex`, version
  0.159.2. The earlier statement that no desktop app exists was incorrect.
- `plugin marketplace add`, `plugin add ai-code-workflow@ai-code-workflow-local`
  and `plugin list --json` succeeded using temporary CODEX_HOME.
- Existing model selection gpt-6.1-sol was preserved. The real smoke session
  recognized the installed skill path but returned the nested-sandbox error.
- An outer-sandbox retry was rejected by automatic approval review pending
  explicit authorization for sending synthetic test material to the service.
  No sandbox bypass, model switch or ordinary global repair was performed.

See [current blockage details](../../evals/blocked-env-2026-10-02.md).
Native installation evidence and full task acceptance are separate layers.
