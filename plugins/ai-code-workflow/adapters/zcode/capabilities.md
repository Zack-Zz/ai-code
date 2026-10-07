# ZCode adapter capabilities

Current probe date: 2026-10-02. Native metadata validation is distinct from
real session behavior.

| Capability | Status | Evidence and limits |
|---|---|---|
| discovery | unverified | Package validation passed, but isolated installation did not complete. |
| explicit_invocation | unverified | No real task session completed. |
| automatic_selection | unverified | No qualifying selection case completed. |
| policy_loading | unverified | Resolver and material-level consumer check passed; no runtime loading claim. |
| native_subagents | unverified | Reviewer definition is generated, not executed in the current host. |
| reviewer_restriction | unverified; enforcement=policy_only | Read/Grep/Glob definition and shared instructions are not proof of enforced permissions. |
| workspace_isolation | unverified | Explicit isolated storage/workspace used for probes; installation still attempted a global config write. |

## Native probes

The application bundles `glm/zcode.cjs` (0.16.9), including headless prompt,
app-server, plugins and skills commands. The earlier claim that no headless
entry exists was an incomplete search.

Native `plugins validate` returned ok=true with no diagnostics. Marketplace
add succeeded with temporary ZCODE_STORAGE_DIR and ZCODE_DATA_BASE_DIR.
`plugins install ... --scope project` then attempted to write
`~/.zcode/cli/config.json` and was blocked by the filesystem sandbox. Ordinary
user configuration is not modified or authorized for this task; no successful
installation or model task is claimed.

See [current blockage details](../../evals/blocked-env-2026-10-02.md).
Historical BEL observations remain historical and are not v1 acceptance.
