# Installing AI Code Workflow

Run the shared build from the ai-code repository root:

```sh
python3 tooling/plugin_tool.py build --plugin ai-code-workflow --host all --output dist-check
```

The selected empty output receives `zcode/` and `codex/` host roots. Examples
below use `dist/` for a generated distribution at the repository root; replace
it with your actual build output. Each host root contains plugin directories,
a local marketplace named `ai-code-local`, and one ZIP per plugin. ZCode's
marketplace is `marketplace.json`; Codex's is
`.agents/plugins/marketplace.json`. Each ZIP contains only its plugin and a
single-plugin marketplace. The repository's multi-plugin packaging contract
is in [the authoring guide](../../../docs/plugin-authoring.md).

**The candidate distribution model is: download/unzip, then register the
local marketplace root and install natively.** No host is assumed to install
a ZIP directly, and this tool never writes into host caches or global config
on its own.

## ZCode

1. Take `dist/zcode/` (from the repository or the ZIP candidate — unzip it
   anywhere stable; the path is registered, so avoid temp locations).
2. In ZCode: plugin marketplace → add marketplace → point it at
   `dist/zcode/marketplace.json` (or the directory).
3. Install and enable `ai-code-workflow`. The package uses the native
   `.zcode-plugin/plugin.json` manifest; skills appear under their six names
   and a read-only reviewer agent `workflow-reviewer` (model=inherit, tools
   Read/Grep/Glob, maxTurns=12) is registered as `agents/workflow-reviewer.md`.
4. Start a **new session** and verify the skills are listed before relying on
   them. Cache visibility or a settings page entry alone is not proof — see
   "Verifying an installation".

## Codex

1. Take `dist/codex/`.
2. Register the local marketplace root:
   `codex plugin marketplace add /path/to/dist/codex`
   (the marketplace file is `dist/codex/.agents/plugins/marketplace.json`, with
   `source.path` relative to that root), then install `ai-code-workflow` via
   the ChatGPT desktop app or, on CLI 0.159.2,
   `codex plugin add ai-code-workflow@ai-code-local` for a distribution built
   by the shared tool. Check your actual version's `plugin --help`; command
   availability varies. The 2026-10-02 probes established that CLI command
   shape for the older single-plugin market, not acceptance of this migrated
   distribution. The workflow-specific legacy build retains its own market
   template/name, which must be used when registering that output.
3. Local installs are copied into `~/.codex/plugins/cache/...` and loaded
   from the cache copy — after updating, confirm the loaded copy matches this
   build's `artifact.json` `content_hash` (see below).
4. Start a new session and verify.

## Verifying an installation

```sh
# use the checker from a trusted repository or previously verified tool copy
python3 /path/to/trusted-ai-code/tooling/plugin_tool.py package check \
  --path /path/to/ai-code-workflow --host zcode \
  --root /path/to/trusted-ai-code                # or --host codex
```

`ok: true` proves the copy's integrity (file closure, hashes, manifests,
marketplace resolution). Native caches may contain only the package, so
check the distribution first, then compare the installed artifact's file
hashes and content hash with
`dist/index.json` at `plugins.ai-code-workflow.hosts.<host>`. The shared
index uses `schema_version: 2`. A matching manifest alone
does not establish that the cache contains this build or that skills ran.

The copy being examined must not provide its own initial verifier: Python
imports run before the checker, so a damaged package or cache can fail or
block at startup. Hash checks compare declared bytes; they do not
authenticate the package author. Built ZIPs exclude bytecode caches; only
regular, recognized cache files are passive during later checks.

The workflow-specific source entry is
`plugins/ai-code-workflow/scripts/workflow_tool.py` from the repository root;
the installed entry remains `<package>/tools/workflow_tool.py`. The examples
below run from the package root. Shared packaging does not change
policy/task/files behavior or the workspace `.ai-workflow` paths.

## Staging files into a project (optional, explicit)

If you want the package's files materialized inside a project (not only
installed in the host), use the receipted staging tool:

```sh
# preview (writes only the plan file; never touches the project)
python3 tools/workflow_tool.py files plan \
  --package /path/to/dist/zcode/ai-code-workflow \
  --target /path/to/your/project --action stage --out /tmp/plan.json

# inspect plan.json, then apply
python3 tools/workflow_tool.py files apply --plan /tmp/plan.json \
  --expected-plan-hash <plan_hash from the plan report>
```

Staged files live only under
`<project>/.ai-workflow/staged/ai-code-workflow/`, tracked by a receipt at
`<project>/.ai-workflow/receipts/ai-code-workflow.json`. `update` replaces
changed owned files (never your edits), `remove` deletes only owned files
whose content still matches the receipt; interrupted operations leave a
pending marker plus a backup directory with a recovery basis instead of being
replayed blindly. **Staging success is not host installation success** —
register with the host separately.

Management writes use directory handles and reject links below the selected
root. Tool writers coordinate through the product lock. A late new file is
never overwritten; replacements recheck content immediately before rename.
POSIX has no atomic content comparison plus replacement against an unrelated
editor that ignores locks: avoid concurrent external edits during apply and
inspect conflicts/recovery state. This is not an OS sandbox.

## Updating and rolling back

Build the new dist, then `files plan --action update` + `apply`. Rolling back
is the same operation with an older, `package check`-verified package —
there is no force mode that bypasses user-edit protection.

## Requirements

- Host: ZCode or Codex, versions actually verified (see
  [support matrix](support-matrix.md) — not yet host-verified on any machine at
  publication of this candidate).
- Management tools: Python 3.11+ (3.13 baseline), standard library only.
  Native Markdown skills need no Python at all; the tools are used for
  policy resolution, task records, staging and package checks.
- Development/CI of this repository: Node 22+.
