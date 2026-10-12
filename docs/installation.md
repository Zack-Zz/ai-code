# Install ai-code plugins

English | [简体中文](installation.zh-CN.md)

Choose a plugin and install it through Claude Code, Codex or ZCode:

| Plugin | ID | Purpose |
|---|---|---|
| [CodeVow](../plugins/ai-code-workflow/README.md) | `ai-code-workflow` | Planning, TDD, debugging, review and verification |
| [Agent Delegation](../plugins/ai-agent-delegation/README.md) | `ai-agent-delegation` | Handoff to an independent coding assistant session |

The current marketplace has no installable plugins. Available plugins are
determined by its list; the commands below register the source and show how to
install a listed plugin.

## Install from the marketplace

The source is `Zack-Zz/ai-code` at `main`; its marketplace name is
`ai-code`. Register it once, then choose either or both plugins.

### Codex

Register the marketplace:

```sh
codex plugin marketplace add Zack-Zz/ai-code --ref main
```

In the desktop client's Plugins Directory, select `ai-code`, choose
the plugin, and install and enable it. The CLI installation commands are:

```sh
codex plugin add ai-code-workflow@ai-code
codex plugin add ai-agent-delegation@ai-code
```

### Claude Code

```sh
claude plugin marketplace add \
  https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/main/.claude-plugin/marketplace.json
claude plugin install ai-code-workflow@ai-code
claude plugin install ai-agent-delegation@ai-code
```

Choose only the installation command for the plugin you want, then enable it
in the native plugin controls.

### ZCode

In the native plugin marketplace, add this URL:

```text
https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/main/marketplace.json
```

Select `ai-code`, choose the plugin, and install and enable it.
With the macOS bundled CLI:

```sh
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins marketplace add \
  https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/main/marketplace.json
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins install ai-code-workflow@ai-code
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins install ai-agent-delegation@ai-code
```

After installation in any host, start a new session. Your host continues to
manage the account and selected model.

## Downloaded package installation

Open [GitHub Releases](https://github.com/Zack-Zz/ai-code/releases), choose the
plugin's Release, and select the file for your host:
`claude`, `codex` or `zcode`. Use the version shown on that Release.

| Download | When to choose it |
|---|---|
| `<ID>-<VERSION>-<HOST>.zip` | Manual local-market installation; includes the plugin and marketplace |
| `<ID>-<VERSION>-<HOST>-plugin.zip` | Plugin-only archive used by marketplace distribution; has no local marketplace |

The local-market files are under `downloads/` in a Release bundle, and
plugin-only files are under `installers/`. For manual installation, choose the
first format and download `SHA256SUMS`. Compare the archive's SHA256 with its
`downloads/` entry, then unzip to a stable directory. Register the extracted directory
containing the marketplace file, rather than the inner plugin directory:

| Host | Marketplace file in the extracted root | Registration |
|---|---|---|
| Claude Code | `.claude-plugin/marketplace.json` | `claude plugin marketplace add /path/to/extracted` |
| Codex | `.agents/plugins/marketplace.json` | `codex plugin marketplace add /path/to/extracted` |
| ZCode | `marketplace.json` | Add that file through the native marketplace UI |

Select the registered source and install the plugin. Local downloads use
`ai-code-local`; use the name declared in the extracted marketplace. For example:

```sh
claude plugin install ai-code-workflow@ai-code-local
codex plugin add ai-agent-delegation@ai-code-local
```

`-plugin.zip` archives serve marketplace distribution. For manual local
installation, use a download with its marketplace included. Keep the extracted
directory while the local marketplace is registered.

## Update and uninstall

To update, refresh the source in the host's native marketplace controls, update
the installed plugin, then reload or start a new session. For a local download,
use the new package as the registered source.

To uninstall, disable and remove the plugin in the host's native plugin
controls. Remove the marketplace separately if you no longer need its plugins.
Uninstalling a plugin does not remove project records or a separately installed
Agent Bridge.

## Dependencies

| Plugin or feature | Requirements |
|---|---|
| Both plugins | A host with native plugin support, its account and selected model |
| CodeVow Markdown skills | No additional Node.js or Python runtime |
| CodeVow optional tools | Python 3.11+; file staging needs a platform supporting POSIX file operations |
| Agent Delegation | Python 3 and a separately configured `agent-bridge/v1` CLI |
| Agent Bridge | Node.js 22.16+ and the target coding tools, installed and authenticated separately |

For Agent Delegation, follow
[Agent Bridge setup and configuration](https://github.com/Zack-Zz/ai-mcp/blob/main/packages/agent-bridge/README.md#构建与受控配置)
to register the project, target tools and caller session. Set
`AGENT_BRIDGE_BIN` if its executable is outside `PATH`, and use
`AGENT_BRIDGE_CONFIG` and `AGENT_BRIDGE_CALLER_REF` for the configured client.
Use a platform supported by Bridge; native Windows execution is not provided
by this plugin.

Installing a plugin does not install its dependencies.

## Next steps

- [CodeVow usage and configuration](../plugins/ai-code-workflow/docs/usage.md)
- [Agent Delegation examples](../plugins/ai-agent-delegation/README.md)
