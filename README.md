# ai-code

English | [简体中文](README.zh-CN.md)

> Source candidate: CodeVow now uses `codevow` (1.0.6) and CodeStack uses
> `codestack` (1.0.0), including a `dsh` adapter. This change is not published yet.
> The frozen published snapshot still determines what can be installed today.
> Use the new-ID commands below after those entries appear in the marketplace.
> See the [identity migration](docs/migrations/2026-10-27-plugin-identities.md).

ai-code is a collection of AI coding plugins for Claude Code, Codex, ZCode and DeepSeek Harness.
They help you plan tasks, develop code, review changes and collaborate with
other coding assistants.

The project organizes reusable skills, rules and helper tools into independent
plugins. Choose the plugins you need or build your own. Each plugin owns its
features and configuration, with shared tooling for packaging and distribution.

## Project contents

| Plugin | Purpose | Guide |
|---|---|---|
| **CodeVow** | Plan changes, develop with TDD, debug problems, review code and verify results | [CodeVow](plugins/codevow/README.md) |
| **Agent Delegation** | Hand tasks to independent Claude Code, Codex or ZCode sessions and bring results back; requires Agent Bridge | [Agent Delegation](plugins/ai-agent-delegation/README.md) |
| **CodeStack** | Apply selected Java, data-access and multilingual frontend conventions to the current change or review | [CodeStack](plugins/codestack/README.md) |

| Path | Contents |
|---|---|
| `plugins/` | Plugin source, usage guides, configuration, adapters and tests |
| `tooling/` | Shared validation, build, package checking and distribution tools |
| `tests/` | Shared tooling tests and the plugin test suite |
| `docs/` | Installation, development, maintenance and reference documentation |
| `catalog.json` | Registered plugin directories |
| `published/` | Release records and installation content used by the marketplace |

## Install and use

Install through the ai-code marketplace or download a package for your coding
assistant from GitHub Releases. The marketplace name is `ai-code`, from
`Zack-Zz/ai-code` at `main`. The repository's current
[release record](published/index.json) and host marketplace manifests determine
stable availability and versions. **CodeVow** (`codevow`) and **CodeStack**
(`codestack`) share this marketplace and are installed and released
independently. Refresh the marketplace in your host before selecting a plugin.
Agent Delegation currently has source only and has not entered the stable marketplace.

Run the following CLI commands in your system terminal, one at a time after
each succeeds. If you have already added `ai-code` with the correct source,
start with the second command to refresh the marketplace.

### Codex CLI quick start

```sh
codex plugin marketplace add Zack-Zz/ai-code --ref main
codex plugin marketplace upgrade ai-code
codex plugin add codevow@ai-code
```

### Claude Code CLI quick start

Use **Claude Code 2.1.224 or later**:

```sh
claude plugin marketplace add https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/main/.claude-plugin/marketplace.json
claude plugin marketplace update ai-code
claude plugin install codevow@ai-code --scope user
```

After installation, restart the session or run `/reload-plugins` inside your
Claude Code session. GitHub shorthand is also supported; see the
[installation guide](docs/installation.md#claude-code).

### ZCode

Open a workspace in the ZCode desktop app, then go to **Settings → Plugins →
Create → Add plugin marketplace**. Add the
[dedicated marketplace JSON](https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/main/marketplace.json),
then select `ai-code` and install and enable CodeVow. A repository-only source
selects the Claude manifest first, whose `archive` transport ZCode does not
support, so use this URL. For the macOS bundled CLI commands, see the
[ZCode installation guide](docs/installation.md#zcode).

For detailed installation steps and plugin usage:

- [Installation guide](docs/installation.md): full marketplace registration and installation steps, downloaded packages, updates, removal and troubleshooting for Claude Code, Codex, ZCode and DeepSeek Harness.
- [CodeVow guide](plugins/codevow/README.md): task examples, collaboration modes and project configuration.
- [Agent Delegation guide](plugins/ai-agent-delegation/README.md): requirements, handoffs, continuation and cancellation.
- [CodeStack guide](plugins/codestack/README.md): supported rule scope, automatic selection and marketplace availability.

After installation, start a new session and describe what you want to do.

### DeepSeek Harness

The source candidate provides two standard DSH bundles, with native profile,
TGZ and fixed Git installation. Start with the [Harness installation steps](docs/installation.md#deepseek-harness).
The stable DSH index will be available after publication; native runtime
acceptance remains separate from package verification.

## Develop and contribute

Start with the [development guide](CONTRIBUTING.md) to set up your environment,
change an existing plugin, run tests, build packages and try them locally.

For a new plugin, follow the [plugin authoring guide](docs/plugin-authoring.md).
See the [architecture](docs/architecture.md) for project boundaries and the
[maintainer publishing guide](docs/publishing.md) for releases.

## FAQ and other information

**Do I need Node.js or Python?** CodeVow's Markdown skills need neither runtime;
its optional management tools need Python 3.11+. Agent Delegation needs Python 3
and an external Agent Bridge. CodeStack provides Markdown instructions and needs
no additional runtime. Each plugin's guide lists its requirements. Source
development requirements are in the development guide.

**Must I use all three plugins together?** Each plugin can be used independently.
CodeVow organizes coding work in your current session. Agent Delegation handles
tasks you explicitly hand to an independent session. CodeStack supplies selected
code and project conventions without requiring either plugin. Marketplace availability
is separate from these functional relationships.

**How do I update or report a problem?** Follow the installation guide for
updates. Submit problems and suggestions through
[GitHub Issues](https://github.com/Zack-Zz/ai-code/issues), including the plugin,
coding assistant and steps to reproduce. The [documentation index](docs/README.md)
links the current guides and reference material.

## License and provenance

[MIT](LICENSE); see [NOTICE](NOTICE). The repository's early history derives from
Affaan Mustafa's ai-code. CodeVow evolved from backend-engineering-lite, whose
license is preserved in the
[plugin directory](plugins/codevow/LICENSES/backend-engineering-lite.txt).
