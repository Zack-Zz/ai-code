# Isolated DeepSeek Harness API checks

English | [简体中文](README.zh-CN.md)

This separate entry builds both DSH bundles and loads their unmodified overlays
through the published Loader and PresetRegistry. It checks that every Reviewer
plugin activates, the delegation tool `workflow_reviewer` actually registers,
the preset mounts, and its real tool surface contains only `read`, `grep` and
`glob`. It also runs real Cordis, AgentRegistry, Tools and Skill
APIs with synthetic agents and tool definitions to check native permission
execution, scope changes and provider lifecycle without a model or user profile.
It does not establish full Web-profile, real filesystem-tool or model acceptance.
Missing dependencies fail; the ordinary `npm test` does not skip this entry and
claim it passed — it runs the local contract suite separately.

`native-preset.mjs`, called by this entry, forces delegation to load before its
preset, then enables the preset and checks that the waiting delegation activates.
It also checks preset disable/re-enable and parallel cold loading with delegation
listed first. Each successful load must register the actual `workflow_reviewer`
tool; finding a preset in the registry alone is insufficient. The adapter inherits
the official AgentPreset lifecycle and publishes its registration as the
`codevowReviewerPresetRegistered` dependency of the official subagent tool. On
unload, delegation is revoked before preset registration is released.

The synthetic `spawn` provider is a loading fixture. It advertises the capabilities
needed to register the official delegation tool, but its `start` method throws
if called. These checks never execute a model or prove a completed delegation.
Permission checks separately exercise real Tools dispatch with fixture tools;
the mounted preset exposes only `read`, `grep` and `glob`. Real filesystem access
and workspace isolation require separate host evidence.

A separate [Desktop probe on 2026-10-28](../../docs/verification/2026-10-28-dsh-reviewer-startup.md)
verified the local 1.0.8 candidate on DSH Desktop `0.2.1-rc.3` after native
installation and a normal restart. A standard parent called `workflow_reviewer`
once; the spawned `codevow-reviewer` child exposed only `glob`, `grep` and `read`,
successfully read the fixture and completed its review back to the parent. Fixture
hashes were unchanged. This covers that read-only delegation and restart scenario;
active-Reviewer disable, forbidden write-call probes, long sessions and complete
four-host acceptance remain unverified. The release acceptance slots remain null;
the public release and marketplace remain 1.0.7.

Create a disposable directory outside the checkout. Install these exact packages
with scripts disabled and an isolated cache, preserving the generated lockfile:

```sh
npm install --prefix /private/tmp/codevow-native-api \
  --cache /private/tmp/codevow-native-cache --ignore-scripts --no-audit --no-fund --save-exact \
  @deepseek-ai/cordis@4.0.5 \
  @deepseek-ai/cordis-plugin-loader@1.0.6 @deepseek-ai/dsh-app-boot@0.2.1-rc.2 \
  @deepseek-ai/dsh-scope@0.2.1-rc.2 @deepseek-ai/dsh-tools@0.2.1-rc.2 \
  @deepseek-ai/dsh-system-prompt@0.2.1-rc.2 @deepseek-ai/dsh-agent@0.2.1-rc.2 \
  @deepseek-ai/dsh-skill@0.2.1-rc.2 @deepseek-ai/dsh-skill-filesystem@0.2.1-rc.2 \
  @deepseek-ai/dsh-agent-tool-presentation@0.2.1-rc.2 \
  @deepseek-ai/dsh-agent-preset@0.2.1-rc.2 @deepseek-ai/dsh-agent-preset-registry@0.2.1-rc.2 \
  @deepseek-ai/dsh-tool-subagent@0.2.1-rc.2 @deepseek-ai/dsh-persona@0.2.1-rc.2 \
  @deepseek-ai/dsh-tool-fs@0.2.1-rc.2 @deepseek-ai/dsh-tool-fs-search@0.2.1-rc.2 \
  @deepseek-ai/dsh-session-projection@0.2.1-rc.2 @deepseek-ai/dsh-subagent@0.2.1-rc.2 \
  @deepseek-ai/dsh-fs@0.2.1-rc.2 @deepseek-ai/dsh-subprocess@0.2.1-rc.2 \
  @deepseek-ai/dsh-working-directory@0.2.1-rc.2
DSH_NATIVE_NODE_MODULES=/private/tmp/codevow-native-api/node_modules \
  node plugins/codevow/tests/dsh/native-api.mjs
```

Run from the repository root. Node.js `v24.4.1` was used in the local check.
The script requires Python 3.11+ for the build and validates both bundle templates'
minimum runtime and peer ranges with the official DSH compatibility evaluator:
RC1 and older are rejected; RC2, RC3, stable and later prerelease versions match.
CodeVow additionally declares `@deepseek-ai/cordis` `~4.0.5`; its DSH peers remain
`>=0.2.1-rc.2`.
The exact installed RC2 packages remain the reproducible API-composition baseline;
matching a version range does not establish full runtime acceptance on RC3 or later.
The script also validates the RC2 configuration schema, loads only each plugin's
bundled skills, checks the actual rendered workflow length, and verifies rejection through the real Tools
pipeline. No host profile, global configuration or credentials are read or changed.
