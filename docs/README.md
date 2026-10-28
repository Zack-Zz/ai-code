# ai-code documentation

English | [简体中文](README.zh-CN.md)

Choose a current guide by what you want to do. Dated design and verification
records appear in the reference section at the end.

## Use plugins

- [Installation](installation.md): desktop and CLI installation, updates and removal for [Codex](installation.md#codex), [Claude Code](installation.md#claude-code), [ZCode](installation.md#zcode) and [DeepSeek Harness](installation.md#deepseek-harness).
- [Identity migration](migrations/2026-10-27-plugin-identities.md): reinstall retired plugin IDs as `codevow` and `codestack`; the dated guide retains the original migration versions.
- [CodeVow](../plugins/codevow/README.md): features, examples and configuration.
- [Detailed CodeVow usage](../plugins/codevow/docs/usage.md): configuration, task records and optional file tools.
- [Agent Delegation](../plugins/ai-agent-delegation/README.md): requirements, handoffs, continuation and cancellation.
- [CodeStack](../plugins/codestack/README.md): selected Java, data-access and multilingual frontend conventions and current marketplace installation.
- [Agent Bridge setup](https://github.com/Zack-Zz/ai-mcp/blob/main/packages/agent-bridge/README.md#构建与受控配置): preparation of the external runtime.

## Develop plugins

- [Development guide](../CONTRIBUTING.md): environment, existing plugins, tests, builds and local trials.
- [Plugin authoring](plugin-authoring.md): identity, resources, adapters, registration and tests for a new plugin.
- [Architecture](architecture.md): repository structure and the responsibilities of shared tooling, plugins and the external runtime.

## Maintain releases

- [Publishing guide](publishing.md): preparation, host acceptance, GitHub Releases and marketplace updates.
- [Release evidence contract](release-evidence.md): acceptance materials, public digests and CI data requirements.

## Design and historical material

- [Designs](design/): dated specifications and design decisions.
- [Development and verification records](reviews/): checks tied to their dates, source and environments.
- [CodeVow designs](../plugins/codevow/docs/design/) and [verification records](../plugins/codevow/docs/reviews/): internal design and test context.
- [Migration origins](../plugins/codevow/docs/migration.md) and [historical material](../plugins/codevow/docs/bel-history/README.md): provenance, licenses and early records.

Use the current guides above for everyday installation and development.
Historical material retains its original dates and commands for reference.
