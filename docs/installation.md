# Install ai-code plugins

English | [简体中文](installation.zh-CN.md)

> Source candidate: CodeVow now uses `codevow` (2.0.0) and CodeStack uses
> `codestack` (0.2.0), including a `dsh` adapter. This change is not published yet.
> The frozen published snapshot still determines what can be installed today.
> Use the new-ID commands below after those entries appear in the marketplace.
> See the [identity migration](migrations/2026-10-27-plugin-identities.md).

Install published plugins through Claude Code, Codex or ZCode. The repository's
current [release record](../published/index.json) and host marketplace
manifests determine stable availability and versions; refresh your host's listing
before installation. CodeVow and CodeStack share `ai-code` and are independent:

| Plugin | ID | Purpose | Stable marketplace |
|---|---|---|---|
| [CodeVow](../plugins/codevow/README.md) | `codevow` | Planning, TDD, debugging, review and verification | See current release record |
| [Agent Delegation](../plugins/ai-agent-delegation/README.md) | `ai-agent-delegation` | Handoff to an independent coding assistant session | Not yet published |
| [CodeStack](../plugins/codestack/README.md) | `codestack` | Selected Java, data-access and multilingual frontend conventions | See current release record |

The commands below install CodeVow. To install CodeStack, use
`codestack@ai-code` in the same host's install command, or select
CodeStack in its marketplace UI after refreshing. You may install either plugin
or both. Agent Delegation remains source-only and is not yet listed for stable
installation. See the [development guide](../CONTRIBUTING.md) for source development.

## Install from the marketplace

The source is `Zack-Zz/ai-code` at `main`; its marketplace name is `ai-code`.
You do not need to clone the source repository or build packages. Your coding
assistant fetches the registered source itself. Register the source once, then
install a plugin listed in that marketplace.

Run the `sh` command blocks below in your system terminal, outside an interactive
coding-assistant session. Run each command after the previous one succeeds. If
`ai-code` is already registered with the correct source, skip the registration
command and continue with the marketplace refresh and plugin installation.

Each host has its own marketplace manifest and installation source:

| Host | Registration method | Manifest in this repository | Plugin installation source |
|---|---|---|---|
| Codex | GitHub repository at `main` | `.agents/plugins/marketplace.json` | `git-subdir` |
| Claude Code | Direct manifest URL, or GitHub repository at `main` | `.claude-plugin/marketplace.json` | `archive` |
| ZCode | Direct manifest URL | `marketplace.json` | `url` with `type: zip` |
| DeepSeek Harness | Explicit native plugin index | `published/dsh/index.json` | Fixed Git bundle or downloaded TGZ |

### Codex

Use a Codex version that supports native plugin marketplaces. Register the
GitHub source, refresh its listing, then install CodeVow.
`owner/repo` is a supported GitHub shorthand:

```sh
codex plugin marketplace add Zack-Zz/ai-code --ref main
codex plugin marketplace upgrade ai-code
codex plugin add codevow@ai-code
```

Check the plugin's status with:

```sh
codex plugin list --marketplace ai-code
```

Codex reads `.agents/plugins/marketplace.json`. You can also select `ai-code`
in the desktop client's Plugins Directory, choose CodeVow, and install and
enable it there. Start a new session after installation.

### Claude Code

Use **Claude Code 2.1.224 or later**. This marketplace uses the `archive`
plugin source, which requires that minimum version according to the
[Claude Code marketplace reference](https://code.claude.com/docs/en/plugins/marketplace-reference#plugin-sources).
Check your version with `claude --version` before installing.

Register the Claude-specific manifest URL, refresh its listing, then install
CodeVow for your user on this machine:

```sh
claude plugin marketplace add https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/main/.claude-plugin/marketplace.json
claude plugin marketplace update ai-code
claude plugin install codevow@ai-code --scope user
claude plugin list
```

As an alternative to the URL registration, Claude Code also supports GitHub
shorthand and reads `.claude-plugin/marketplace.json`:

```sh
claude plugin marketplace add "Zack-Zz/ai-code#main"
```

Choose one registration method; the GitHub command replaces only the first
command in the installation block above. After installation, restart Claude Code
or run this command **inside an existing Claude Code session**:

```text
/reload-plugins
```

You can inspect and enable CodeVow in the Installed tab of `/plugin`. See the
[official shell installation guide](https://code.claude.com/docs/en/discover-plugins#install-from-your-shell)
for scope and loading behavior.

If the interactive plugin panel reports an unsupported source despite meeting
the version requirement, run the marketplace update and plugin install commands
above in your terminal, then restart the session. That error alone does not
establish that the CLI version is too old.

### ZCode

In the ZCode desktop app, open a workspace, then go to **Settings → Plugins →
Create → Add plugin marketplace**. Add this direct manifest URL:

```text
https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/main/marketplace.json
```

Use the direct URL for this repository. ZCode's Git import can select
`.claude-plugin/marketplace.json` before the root manifest when you add only
`Zack-Zz/ai-code`. The Claude manifest uses `archive`, which the ZCode installer
does not support. The root manifest uses ZCode's `url` / `type: zip` source.

If you already added the repository and see
`Plugin source is invalid or unsupported for codevow@ai-code: archive`,
remove that `ai-code` source in the marketplace-source panel, add the direct URL
above, and refresh it before opening the plugin details or installing.

Select `ai-code`, choose CodeVow, and install and enable it. Alternatively, on
**macOS with ZCode installed at `/Applications/ZCode.app`**, use the bundled CLI
to register the source, refresh its listing, install and enable CodeVow:

```sh
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins marketplace add \
  https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/main/marketplace.json
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins marketplace update ai-code
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins install codevow@ai-code
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins enable codevow@ai-code
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins list
```

This example requires `node` on `PATH`. Adjust the application path if ZCode is
installed elsewhere. On other platforms, use the desktop steps above.

After installation in any host, start a new session. Your host continues to
manage the account and selected model.

## DeepSeek Harness

The `dsh` adapter targets the standard Web profile and declares `engines.dsh`
`0.2.1-rc.2`; real host acceptance is still pending. CodeVow needs the native
Agent Preset service and spawn backend. Minimal/SDK/ACP profiles are outside the
initial support scope. Package installation alone does not prove activation.

Use an unused profile name for a local trial. The first command creates a Web
profile and prints its composed configuration; it must not replace an existing
profile containing your settings. After downloading the matching Release TGZ:

```sh
dsh --profile ai-code-trial --from-default-profile web --dump-config
dsh plugin --profile ai-code-trial add ./codevow-2.0.0-dsh-plugin.tgz
dsh plugin --profile ai-code-trial add ./codestack-0.2.0-dsh-plugin.tgz
dsh --profile ai-code-trial --dump-config
dsh --profile ai-code-trial
```

For a source trial, replace the TGZ argument with the absolute built package
directory, such as `/private/tmp/ai-code-packages/dsh/codevow`. No install-time
build scripts are supplied. Use `/workflow` or `/code-standards` in a new session;
references remain inside each installed bundle. CodeStack has no custom runtime.
CodeVow uses native spawn for its read-only Reviewer and existing Python tools.

After stable publication, enable Harness's optional **Custom plugin index**
bundle and add the `published/dsh/index.json` raw HTTPS URL from this repository.
This is an explicit index source, not an automatically discovered repository
manifest. Confirm the fixed Git commit and bundle subdirectory shown by Harness
before installing. Direct TGZ/directory installation does not need this feature.
The index lists stable releases only.

For Git installation, use the exact commit and subdirectory generated in the
published index, never the source repository root. The Git bundle is prebuilt.
Git-installed bundles follow the host's uninstall/reinstall update procedure.
For removal use `dsh plugin --profile ai-code-trial remove codevow` (or
`codestack`); restart where HMR is unavailable. No custom installer or cache edit
is required.

## Downloaded package installation

These ZIP marketplace steps apply to Claude Code, Codex and ZCode. Harness uses
the native TGZ/profile procedure above.

Open [GitHub Releases](https://github.com/Zack-Zz/ai-code/releases), choose the
published plugin's Release, and select the file for your host: `claude`, `codex`
or `zcode`. Consult the current repository release record; use only a
public Release that actually exists for the plugin you want and confirm its version
and assets on that Release page.

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
claude plugin install codevow@ai-code-local
codex plugin add codevow@ai-code-local
```

`-plugin.zip` archives serve marketplace distribution. For manual local
installation, use a download with its marketplace included. Keep the extracted
directory while the local marketplace is registered.

## Update and uninstall

Marketplace refresh fetches the latest catalog. To update an installed plugin
from your terminal, use the commands for your host:

Claude Code:

```sh
claude plugin marketplace update ai-code
claude plugin update codevow@ai-code --scope user
```

ZCode on macOS:

```sh
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins marketplace update ai-code
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins update codevow@ai-code
```

For Codex, run `codex plugin marketplace upgrade ai-code`, then check the
installed version in the native plugin controls. After any update, reload or
start a new session. For a local download, use the new package as the registered
source.

To uninstall, disable and remove the plugin in the host's native plugin
controls. Remove the marketplace separately if you no longer need its plugins.
Uninstalling a plugin does not remove project records or a separately installed
Agent Bridge.

## Dependencies

| Plugin or feature | Requirements |
|---|---|
| Each plugin | A host with native plugin support, its account and selected model |
| Claude Code stable marketplace installation | Claude Code **2.1.224+** for `archive` sources |
| CodeVow Markdown skills | No additional Node.js or Python runtime |
| CodeStack instructions | No additional runtime or dependency on another ai-code plugin |
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

- [CodeVow usage and configuration](../plugins/codevow/docs/usage.md)
- [Agent Delegation examples](../plugins/ai-agent-delegation/README.md)
- [CodeStack scope and marketplace availability](../plugins/codestack/README.md)
