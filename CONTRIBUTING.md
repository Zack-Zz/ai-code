# Developing ai-code

English | [简体中文](CONTRIBUTING.zh-CN.md)

This guide is for changing the source. To install and use plugins, read the
[user installation guide](docs/installation.md). Run commands from the repository
root unless stated otherwise.

## Environment

- Node.js 22.12+ and npm for the test runner and static checks.
- Python 3.11+ for plugin tooling and Python tests.
- A development platform with POSIX file operations for controlled file tools and their tests.

Get the source and install the repository's maintenance dependencies:

```sh
git clone https://github.com/Zack-Zz/ai-code.git
cd ai-code
npm ci --no-audit --no-fund
python3 tooling/plugin_tool.py list
```

With an existing checkout, install dependencies from its repository root.

Read the root [AGENTS.md](AGENTS.md) and the target plugin's `AGENTS.md` first.
The plugin's `product.json` owns its version, hosts and packaged resources;
the root `package.json` is maintenance tooling.

For AI-assisted plugin creation, validation, version preparation and release work,
use the project skill [$ai-code-plugin-release](.agents/skills/ai-code-plugin-release/SKILL.md).
It reads the relevant authoring, publishing and evidence guides for the current task.

## Change an existing plugin

Locate the plugin and update its features and tests:

| Component | Main source | Tests |
|---|---|---|
| CodeVow | `plugins/codevow/skills/`, `policies/`, `scripts/workflow/` | Node skill contracts and plugin Python tests |
| Agent Delegation | `plugins/ai-agent-delegation/skills/`, `scripts/bridge_client.py` | Plugin Python tests |
| CodeStack | `plugins/codestack/skills/code-standards/` | Node discovery, package and runner contracts; separate behavioral evaluations |
| Shared tooling | `tooling/plugin_tools/` | `tests/run_python_tests.py` |

For behavior changes, write a meaningful failing test, implement the smallest
change and run it green. For documentation, check content, links and formatting.
Register new packaged resources in the plugin's `product.json` whitelist.

To run the plugin tests separately:

```sh
node plugins/codevow/tests/skills/run-skills.js
PYTHONDONTWRITEBYTECODE=1 python3 plugins/codevow/tests/run_python_tests.py
PYTHONDONTWRITEBYTECODE=1 python3 plugins/ai-agent-delegation/tests/run_python_tests.py
node plugins/codestack/tests/skills/run-skills.js
```

CodeStack's [evaluation cases](plugins/codestack/evals/cases.md)
separate rule selection, task outcomes and native host loading. Contract tests and
package checks do not prove those behaviors. Keep its runtime skill and references
in English; human-facing guides remain bilingual.

## Check and build

```sh
python3 tooling/plugin_tool.py validate --all
PYTHONDONTWRITEBYTECODE=1 npm test
npm run lint
python3 tooling/plugin_tool.py build --all --host all --output /tmp/ai-code-dev-packages
```

The output must be absent or empty; use a new empty directory for another build.
To work on one plugin, replace `--all` with `--plugin codevow`. Select
`claude`, `codex`, `zcode`, `dsh` or `all` with `--host`.

Check each generated package against trusted source. For CodeVow on Codex:

```sh
python3 tooling/plugin_tool.py package check \
  --path /tmp/ai-code-dev-packages/codex/codevow --host codex --root .
```

Apply the same check to every selected host package before release. The unified
`npm test` runs shared tooling and all registered plugins; an empty or failing
test group fails the suite.

## Try locally

Each host subdirectory in the build contains the `ai-code-local` development
marketplace. Register the directory for your coding assistant. For CodeVow on
Codex:

```sh
codex plugin marketplace add /tmp/ai-code-dev-packages/codex
codex plugin add codevow@ai-code-local
```

For Claude Code and ZCode, follow the local-market steps in
[downloaded package installation](docs/installation.md#downloaded-package-installation).
Start a new session and check the skills and task results. After editing source,
build again, update the plugin in your assistant and start a new session.

You can also generate a separate development marketplace into an empty output:

```sh
python3 tooling/plugin_tool.py marketplace sync --output /tmp/ai-code-dev-market
```

Keep build output in temporary directories. `dist/` is ignored and must not be
committed as source. Local trials do not change the public marketplace files.

## Add a plugin

Follow the [plugin authoring guide](docs/plugin-authoring.md) to create the
directory, declare resources, add host adapters, register it in `catalog.json`
and provide tests. Plugins own their features, versions and resources; shared
tooling handles registration, packaging and checks.

## Documentation and delivery

User READMEs explain current features, installation and usage. Development steps
belong in this guide. Pre-publication checks belong in the
[maintainer publishing guide](docs/publishing.md), with data requirements in the
[evidence contract](docs/release-evidence.md). Current guides use the current
interfaces. Dated design and verification records remain in
[reference material](docs/README.md#design-and-historical-material).

Include relevant source, tests and documentation when submitting a change, and
report the checks you ran. Publication, marketplace updates and user installation
are separate operations described in the maintenance guide.

## Verify DSH API composition

After the normal `npm test` and trusted package checks, the optional isolated
published-API test can use an existing development dependency directory:

```sh
DSH_NATIVE_NODE_MODULES=/absolute/isolated/node_modules node plugins/codevow/tests/dsh/native-api.mjs
```

It requires the exact published DSH 0.2.1-rc.2 packages and Cordis 4.0.5. Missing
or incompatible dependencies fail the command; they are not a passing skip.
This entry builds the two DSH bundles and activates their real overlays and
Reviewer preset through the official Loader. It also uses real
Cordis/Tools/AgentRegistry/Skill APIs with synthetic agents and tool definitions.
It does not run models, install a user profile, or prove
complete Web UI, filesystem-tool, spawn or lifecycle acceptance. Keep dependency
installation and its cache in a temporary development directory.
