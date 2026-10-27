# Add an AI Plugin

English | [简体中文](plugin-authoring.zh-CN.md)

This guide covers adding an independent AI-related plugin to the ai-code
repository. Define the plugin's purpose, minimum contents, and actual target hosts
before registering its directory. The existing workflow is one plugin instance;
a new plugin does not need its policies, task records, Reviewer, or six skills.

For environment setup, changes to existing plugins, and local trials, start with
the [development guide](../CONTRIBUTING.md). This guide focuses on adding plugins.
Run all commands from the repository root. See [AGENTS.md](../AGENTS.md) for
maintenance rules and the [publishing guide](publishing.md) for release operations.

## 1. Create an independent source directory

A minimal Codex plugin with one skill might look like this:

```text
plugins/ai-example/
  product.json
  README.md
  AGENTS.md
  LICENSE
  skills/example/SKILL.md
  adapters/codex/plugin.json
  adapters/codex/interfaces.json
  tests/
```

`ai-example` is a placeholder in this guide, not an available production plugin.
Use lowercase kebab-case for the actual ID; matching the directory name to the ID
is recommended. Each plugin owns its version, license, and documentation. Do not
list relative paths into sibling plugins as resources. The user README explains
the purpose, installation, usage, and required dependencies. Keep pre-release
procedures, host acceptance, and development test records in maintainer documents,
not in the user README.

Documentation for external readers, including READMEs, installation, usage and
configuration guides, must be available in English and Chinese. English is the
default; place reciprocal language links at the top and keep links between
bilingual guides in the selected language. Design, implementation, verification
records and internal maintenance material may remain Chinese-only. Existing
translations can be retained.

## 2. Declare identity, hosts, and resources

`product.json`:

```json
{
  "schema_version": 1,
  "product_id": "ai-example",
  "display_name": "AI Example",
  "version": "1.0.0",
  "repository": "https://github.com/Zack-Zz/ai-code",
  "license": "MIT",
  "hosts": ["codex"],
  "core_skills": ["example"],
  "shared_skills": [],
  "resources": [
    {"source": "LICENSE", "target": "LICENSE", "include": []}
  ]
}
```

Declare identity, version, and the allowlist only in this manifest. Do not maintain
a second development version in the catalog, root package.json, or marketplace.
New public versions use only `X.Y.Z` or `X.Y.Z-preview.N`. Numbers must not have
leading zeros; other suffixes and build metadata are rejected. Preview sequence
numbers are compared numerically, and a stable version follows all previews with
the same core version. The release kind is derived from the version. Start a new
plugin at stable version `1.0.0`, then follow the
[plugin version increments](publishing.md#plugin-version-increments).

`hosts` is required and must be nonempty. The supported values are currently
`claude`, `codex`, `zcode`, and `dsh`. Declare native templates at
`adapters/<host>/plugin.json`, or `adapters/dsh/package.json` for DSH.

Declared skills automatically contribute their `skills/<name>/SKILL.md`. Register
reference documents, scripts, and additional resources used by skills in
resources. For example:

```json
{"source": "skills/example/references", "target": "skills/example/references", "include": ["guide.md"]}
```

When source is a file, include must be `[]`. When source is a directory, include
must list each relative filename explicitly. Do not use wildcards or automatic
recursive packaging. Files must exist. Absolute paths, `..`, symbolic links,
cache files, and duplicate targets are rejected. Relative Markdown references in
the package must resolve within the allowlisted resource closure.

`core_skills` and `shared_skills` may be omitted or empty. When populated, they
must not overlap, and the metadata name must match the skill directory name.
`profiles` and `generated_agents` may also be omitted or empty: declare them only
when the plugin needs profile labels or controlled Agent text composition.
profiles is only a list of unique names. Each plugin validates its policy
resources and actual behavior; the shared layer does not require policies files.
Each generated Agent entry contains `host/template/body/target`. Currently,
declared Claude Code / ZCode hosts and agents/*.md targets are accepted. Generation
only composes text from data and does not execute code hooks.

Validation and packaging of resources do not prove that a runtime capability is
available. Before supporting a new host component type, establish its native
manifest, startup and permission behavior, and acceptance in a real session.

### Optional marketplace listing metadata

Declare `host_listings` in `product.json` to enable marketplace display metadata
for selected hosts. Each key must name a host already declared in `hosts`.
`claude: {}` enables `displayName`; ZCode requires exactly `icon_path` and
`icon_url` and enables both `displayName` and `icon`. The generated `displayName`
always comes from `product.display_name`, the single source for the display name.
Do not repeat the name in `host_listings` or adapter templates.

For CodeVow, this declaration fragment uses its existing public PNG:

```json
{
  "host_listings": {
    "claude": {},
    "zcode": {
      "icon_path": "assets/codevow.png",
      "icon_url": "https://raw.githubusercontent.com/Zack-Zz/ai-code/91dec3a64731f8de2fb68e49bce9f4228289bbbd/plugins/codevow/assets/codevow.png"
    }
  }
}
```

This fragment requires `claude` and `zcode` in `hosts`, and the PNG registered in
`resources`. Adapt the host and resource declarations together for another
plugin. `icon_path` is the normalized packaged **target** of an explicitly
allowlisted PNG or SVG file. `icon_url` must point to its actual **source** path
in the same GitHub repository declared by `repository`; source and target may
differ. Use an HTTPS `raw.githubusercontent.com` URL with a full fixed 40-character
Git commit SHA. Branches, `main`, tags, credentials, query strings, and fragments
are rejected.

Hosts without a listing declaration retain their existing output. Declared
metadata is generated in local marketplaces and captured in stable release
records for the public marketplace. Native plugin manifests continue to follow
each host's own contract; this option adds no branding fields to the ZCode
manifest. Claude Code does not read the PNG `icon` field, so its empty object
enables only the marketplace name shown before installation. See the official
[directory listing field reference](https://code.claude.com/docs/en/plugins/manifest-reference#directory-listing-fields).

Static URL validation does not establish that the image is reachable or displayed
by the host. Report URL retrieval and real host verification separately. Frozen
public records, including CodeVow 1.0.3, must not be edited by hand. After committing
the source change, publish a subsequent version through the normal
[release workflow](publishing.md) to update the public marketplace.

## 3. Provide host adapters

Skill frontmatter uses single-line name, description, and optional origin fields:

```markdown
---
name: example
description: Explain the concrete AI task this skill handles.
---

# Example

Describe the task, inputs, actions and evidence expected from the assistant.
```

A minimal `adapters/codex/plugin.json` template can be:

```json
{
  "description": "Help an AI assistant with a concrete task",
  "license": "MIT"
}
```

The shared build injects name/version from product.json. Do not maintain a second
release version in the template. Existing plugins can serve as references for
more complete native interfaces, but host-specific manifests must reflect actual
capabilities. Do not treat unknown fields as supported features. Passing the
repository's structural validation with this minimal template does not mean the
plugin has passed acceptance in a real host.

For the Codex skill above, provide `adapters/codex/interfaces.json`:

```json
{
  "schema_version": 1,
  "skills": {
    "example": {
      "display_name": "AI Example",
      "short_description": "Help with a concrete AI task",
      "brand_color": "#2563EB",
      "default_prompt": "Use $example to help with this task.",
      "allow_implicit_invocation": true
    }
  }
}
```

The skill set must match the plugin manifest. The shared build generates each
`skills/<name>/agents/openai.yaml`; do not maintain another copy of interface
metadata in the source skill directory. Plugins without skills do not need this
skill interface file. When declaring ZCode, provide its native plugin.json. If
Agents are needed, explicitly register their generation metadata and write the
plugin's own behavior checks.

When declaring Claude Code, provide `adapters/claude/plugin.json`; the build emits
`.claude-plugin/plugin.json`. `displayName` is derived from product, and the
namespace ID stays stable. Optional `publisher` contains only public `name`, an
HTTPS `url`, and `email`. Tooling generates native author and Codex developerName
consistently; do not duplicate attribution in adapter templates.

Tooling generates the development marketplace centrally. New plugins do not need
marketplace templates. The public main marketplace is generated from verified
stable release records, not directly synchronized from current development
manifests. Old templates retained by workflow are only for its dedicated build.

## 4. Register the directory and integrate tests

Add this entry to the plugins array in the root `catalog.json`:

```json
{"path": "plugins/ai-example"}
```

The registry stores only paths. Unknown fields, duplicate directories, duplicate
IDs, and paths that escape the repository are rejected. A directory that exists
but is not registered is not built automatically.

Write meaningful failing tests for the plugin's actual behavior. Run RED before
implementing GREEN. For each production plugin, the unified gate discovers the
following controlled entry points through the catalog; at least one must exist:

- `tests/skills/run-skills.js`: the Node skill/resource contract group.
- `tests/run_python_tests.py`: the plugin's own Python test aggregator.

Each entry point runs in its own subprocess. It must reject empty test groups and
propagate failures, startup errors, or signals as a nonzero exit status. The
unified gate fails if a new plugin has neither entry point. Confirm that
`npm test` actually executes the new group. The shared
`tests/run_python_tests.py` runs only repository-wide tooling tests; plugin Python
entry points run independently to avoid collisions between tests packages with
the same name. Do not add arbitrary command hooks. Empty groups, assertions that
only check file existence, and tests that duplicate the implementation cannot
replace behavior checks. Validate document and resource changes according to
their impact; do not add tests mechanically.

New shared tooling behavior also requires a valid RED first. Use minimal fixtures
to verify shared rules; do not register test fixtures as production plugins.

## 5. Validate, build, and check

```sh
python3 tooling/plugin_tool.py list
python3 tooling/plugin_tool.py validate --plugin ai-example
npm test
python3 tooling/plugin_tool.py build --plugin ai-example --host codex --output /tmp/ai-example-packages
python3 tooling/plugin_tool.py package check \
  --path /tmp/ai-example-packages/codex/ai-example --host codex --root .
npm run lint
```

`/tmp/ai-example-packages` must be absent or empty. Use a fresh empty directory
when repeating validation. `--all` validates or builds every registered plugin.
`--host all` generates outputs for each plugin's declared hosts.

Package checking independently rebuilds the expected resource closure from the
trusted repository specified by `--root`, recalculates actual file hashes, and
checks native manifests and marketplace source. Do not use an unverified
package's own Python files as the initial validator. `ok` does not mean the
author's identity is certified or the host has actually executed its components.

Shared package checks reject all unregistered files, including `.pyc` cache files
that Python can execute. Verify the release package before running code inside
it. To keep outputs reproducibly verifiable, use Python `-B` or
`PYTHONDONTWRITEBYTECODE=1`. Always traverse from the repository root when
collecting and rechecking registered plugin inputs. Do not treat a plugin
subdirectory as a new trust root that permits following links in parent
directories.

The build output `<output>/index.json` uses schema_version 3 when DSH is included (legacy builds use 2). It records each
package's path and hash under plugins/ID/hosts/HOST and aggregate marketplaces
under hosts/HOST. Each plugin's artifact retains its own identity and provenance.
When changing one plugin, verify that sibling plugin contents and hashes are
unaffected.

Use an explicit empty output directory for the development marketplace and
register the corresponding `<output>/<host>`:

```sh
python3 tooling/plugin_tool.py marketplace sync --output /tmp/ai-example-development
python3 tooling/plugin_tool.py marketplace check --root .
```

sync generates development marketplaces for registered source plugins across the
declared hosts in a temporary directory. check performs read-only verification of
the public snapshot's frozen source S, installation contents, and fixed Codex
distribution commit D. The stable version need not equal the current development
version. `dist/` is ignored temporary build output and must not be committed or
pushed. CI rejects tracked files in that directory. Public artifacts are stored
as Release attachments.

For release preparation, add the plugin's `release.json` and portable bilingual
documentation. See the [publishing guide](publishing.md) and
[acceptance contract](release-evidence.md). These inputs belong to the release
mechanism. A plugin that only builds resource packages does not have to adopt the
current skills-only submission profile.

## 6. Delivery and native acceptance

Each host directory has an aggregate marketplace named `ai-code-local`. Each
plugin ZIP contains only its own package and a single-plugin marketplace. Extract
it to a stable directory and register it through the host's native method. See
the local marketplace steps under
[downloaded package installation](installation.md#downloaded-package-installation)
in the existing user installation guide. Native commands and version support
still require actual verification for the relevant plugin.

Catalog registration and development trials do not constitute a production
release. New previews appear only as GitHub Prereleases. A stable version enters
the single main marketplace after passing source/package checks, being published,
and completing synchronization. Real host acceptance is reported independently;
pending hosts remain `unverified` and do not block technical publication. Each ID has only one
current entry. Plugins without a stable release do not yet appear in the public
marketplace. `published/index.json` and stable records describe deployed versions;
they are not a second source for development versions.

Plugin support statements must report source validation, script tests, package
checks, native loading, and actual behavior separately. Record the host version,
model, package hash, and session evidence; use `unverified` until acceptance is
complete. Adding ordinary resource files for MCP does not imply support for
configuration discovery, authentication, server startup, or tool invocation.

Leave changes uncommitted on delivery. Provide a summary, diff, validation
results, and remaining limitations for user Review. Commit, push, tag, merge, PR,
installation, and publication retain their separate authorization boundaries.

## DeepSeek Harness adapters

Products with host-specific resources use product schema 2. Schema 1 remains
readable for frozen source and unchanged plugins. Declare `dsh` in `hosts`, put
its native template in `adapters/dsh/package.json`, and register patch, locale
and other files with `host_resources.dsh` using the same explicit
`source`/`target`/`include` contract as shared resources.

The DSH manifest declares `type: module`, exact `engines.dsh`, package exports
and `dsh.bundle.patch`. Name, version and exact packaged `files` are generated
from trusted product inputs. Install lifecycle scripts and private bundles are
rejected. Use `locale/en.json` and `locale/zh.json` with `meta.title` and
`meta.description`, plus a packaged icon. Runtime acceptance is independent.

Mount the official skill-filesystem provider at Host scope with a unique
provider name, `includeDefaultRoots: false` and a package-resolved
`bundledSkillDir`. Keep skills in shared resources. A data-only bundle does not
need a custom module. CodeVow alone declares its Reviewer guard and generates
`reviewer-persona.json` via the fixed `json-string` transform from the shared
review contract; no arbitrary build hook is supported.

DSH installers are npm TGZs with a `package/` root. Build output with DSH uses
schema 3 and records `archive`, `archive_sha256`, `archive_format: npm-tgz`;
legacy host ZIP entries retain their existing fields. The local DSH format-1
index is a structural preview. Use native absolute-directory installation for
local development; public Git entries are generated only after publication.
