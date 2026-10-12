# ai-code

English | [简体中文](README.zh-CN.md)

ai-code is a collection of AI coding plugins for Claude Code, Codex and ZCode.
They help you plan tasks, develop code, review changes and collaborate with
other coding assistants.

The project organizes reusable skills, rules and helper tools into independent
plugins. Choose the plugins you need or build your own. Each plugin owns its
features and configuration, with shared tooling for packaging and distribution.

## Project contents

| Plugin | Purpose | Guide |
|---|---|---|
| **CodeVow** | Plan changes, develop with TDD, debug problems, review code and verify results | [CodeVow](plugins/ai-code-workflow/README.md) |
| **Agent Delegation** | Hand tasks to independent Claude Code, Codex or ZCode sessions and bring results back; requires Agent Bridge | [Agent Delegation](plugins/ai-agent-delegation/README.md) |

Agent Bridge lives in [ai-mcp](https://github.com/Zack-Zz/ai-mcp), where it connects
coding assistants and manages tasks. ai-code owns the plugins and their usage rules.

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
assistant from GitHub Releases. The marketplace name is `ai-code-preview`, from
`Zack-Zz/ai-code` at `main`. Available plugins are listed in the marketplace;
it currently has no installable plugins.

- [Installation guide](docs/installation.md): marketplace installation, downloaded packages, updates and removal for Claude Code, Codex and ZCode.
- [CodeVow guide](plugins/ai-code-workflow/README.md): task examples, collaboration modes and project configuration.
- [Agent Delegation guide](plugins/ai-agent-delegation/README.md): requirements, handoffs, continuation and cancellation.

After installation, start a new session and describe what you want to do.

## Develop and contribute

Start with the [development guide](CONTRIBUTING.md) to set up your environment,
change an existing plugin, run tests, build packages and try them locally.

For a new plugin, follow the [plugin authoring guide](docs/plugin-authoring.md).
See the [architecture](docs/architecture.md) for project boundaries and the
[maintainer publishing guide](docs/publishing.md) for releases.

## FAQ and other information

**Do I need Node.js or Python?** CodeVow's Markdown skills need neither runtime;
its optional management tools need Python 3.11+. Agent Delegation needs Python 3
and an external Agent Bridge. Each plugin's guide lists its requirements. Source
development requirements are in the development guide.

**Must I use both plugins together?** You can choose them independently. CodeVow
organizes coding work in your current session. Agent Delegation handles tasks
you explicitly hand to an independent session.

**How do I update or report a problem?** Follow the installation guide for
updates. Submit problems and suggestions through
[GitHub Issues](https://github.com/Zack-Zz/ai-code/issues), including the plugin,
coding assistant and steps to reproduce. The [documentation index](docs/README.md)
links the current guides and reference material.

## License and provenance

[MIT](LICENSE); see [NOTICE](NOTICE). The repository's early history derives from
Affaan Mustafa's ai-code. CodeVow evolved from backend-engineering-lite, whose
license is preserved in the
[plugin directory](plugins/ai-code-workflow/LICENSES/backend-engineering-lite.txt).
