# Install ai-code plugins

English | [简体中文](installation.zh-CN.md)

CodeVow **1.0.6** (`codevow`) and CodeStack **1.0.0** (`codestack`) are published
in the shared **ai-code** marketplace. The [release index](../published/index.json)
and each host's refreshed listing are authoritative for available versions.
Each plugin is installed independently; you can use either or both.
[Agent Delegation](../plugins/ai-agent-delegation/README.md) remains unpublished.

## Choose your application

| Host | Desktop instructions | Terminal instructions | Marketplace source |
|---|---|---|---|
| Codex | [Desktop](#codex-desktop) | [CLI](#codex-cli) | `Zack-Zz/ai-code`, branch `main` |
| Claude Code | [Desktop Code tab](#claude-code-desktop) | [CLI](#claude-code-cli) | Claude-specific manifest or `Zack-Zz/ai-code#main` |
| ZCode | [Desktop](#zcode-desktop) | [Bundled macOS CLI](#zcode-cli) | Root `marketplace.json` URL |
| DeepSeek Harness | [Desktop](#deepseek-harness-desktop) | [Standalone CLI / Web](#deepseek-harness-cli) | Native DSH index or Release TGZ |

You do not need to clone this repository or build a plugin. Desktop installation
uses each application's native plugin controls. Run `sh` blocks in a system
terminal; slash commands belong inside an assistant session. Run each command
only after the previous one succeeds. Register a market
once and skip its add command when the correct source is already registered.

## Reinstall after the ID change

| Remove the previous ID | Install the published ID | Version |
|---|---|---|
| `ai-code-workflow` | `codevow` | 1.0.6 |
| `ai-code-stack-standards` | `codestack` | 1.0.0 |

1. Refresh `ai-code` and confirm the new entries are visible and compatible.
2. Remove installed previous IDs through the host's plugin controls or the CLI
   commands below. They share skill names with the new plugins.
3. Install and enable the new IDs, then start a fresh session.
4. Keep the project's `.ai-workflow/` directory, including policy, tasks and evidence.

If the new versions are already installed, remove only the remaining old IDs.
A retired entry can disappear from the market while its old local installation
still exists. Do not edit plugin caches or global settings by hand.
See the [migration guide](migrations/2026-10-27-plugin-identities.md).

## Codex

### Codex desktop

1. Open the **Plugins Directory** and select the **ai-code** source.
2. Refresh the source with the commands below; add it first only if absent.
   Reopen the directory and confirm both replacement entries are available.
   Restart the desktop app if the source is still absent.
3. In installed plugin controls, remove `ai-code-workflow` and
   `ai-code-stack-standards` if present. The CLI removal commands also work when
   those retired IDs are no longer offered by the current market.
4. Open **CodeVow** and **CodeStack**, install each desired plugin and enable it.
5. Confirm versions **1.0.6** and **1.0.0**, then start a new chat.

```sh
codex plugin marketplace add Zack-Zz/ai-code --ref main
codex plugin marketplace upgrade ai-code
```

Use Codex's native marketplace registration; no manual `config.toml` changes are
needed. See the [official marketplace guide](https://developers.openai.com/plugins/build/plugins#add-a-marketplace-from-the-cli).

### Codex CLI

Use a CLI that provides `codex plugin`. Register the source only if absent:

```sh
codex --version
codex plugin marketplace add Zack-Zz/ai-code --ref main
codex plugin marketplace upgrade ai-code
```

Confirm the replacement entries in the refreshed market before ID migration.
Run each removal only if that previous plugin is installed:

```sh
codex plugin remove ai-code-workflow@ai-code
codex plugin remove ai-code-stack-standards@ai-code
```

Install and check both published plugins:

```sh
codex plugin add codevow@ai-code
codex plugin add codestack@ai-code
codex plugin list --marketplace ai-code
```

Expect **installed, enabled** and the versions above. The market uses
`.agents/plugins/marketplace.json` and fixed Git subdirectories. Start a new
Codex session after installation or removal.

## Claude Code

Use **Claude Code 2.1.224+**: this market's `archive` source requires that minimum.
These steps cover Claude Code local sessions, including the desktop app's **Code**
tab; they are not instructions for ordinary Claude chat or Cowork.
[Source requirements](https://code.claude.com/docs/en/plugins/marketplace-reference#archive-plugin-source).

### Claude Code desktop

1. Open a local project in the desktop app's **Code** tab.
2. Click **+** beside the prompt and choose **Add plugins**. If the menu says
   **Plugins**, select **Plugins → Browse plugins**. Use **Manage plugins** for
   enable/disable/removal.
3. If `ai-code` is not listed, register it with the CLI command below, then reopen
   the plugin browser. Otherwise refresh the existing source. Confirm both
   replacement entries are available before removing old installations.
4. Remove installed previous IDs at their original scope. Select **CodeVow** and
   **CodeStack**, choose user/project/local scope and install each desired plugin.
5. Check the installed versions and enabled state, then start a new session.

```sh
claude plugin marketplace add "Zack-Zz/ai-code#main"
claude plugin marketplace update ai-code
```

Local desktop and terminal sessions on the same machine share Claude Code
settings. This does not install plugins into a cloud session or another machine.
See the [desktop plugin guide](https://code.claude.com/docs/en/desktop#install-plugins).

### Claude Code CLI

Register the Claude manifest only if the market is absent, then refresh:

```sh
claude --version
claude plugin marketplace add https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/main/.claude-plugin/marketplace.json
claude plugin marketplace update ai-code
```

Confirm the replacement entries in the refreshed plugin browser before migration.
Remove installed previous IDs. These examples use `user` scope;
use `project` or `local` instead when that is where the old plugin was installed.

```sh
claude plugin uninstall ai-code-workflow@ai-code --scope user
claude plugin uninstall ai-code-stack-standards@ai-code --scope user
```

Install both plugins for the current user and inspect the result:

```sh
claude plugin install codevow@ai-code --scope user
claude plugin install codestack@ai-code --scope user
claude plugin list
```

Start a new session, or run `/reload-plugins` **inside an existing Claude Code
session**. `/plugin` → **Installed** shows scope and enabled state. Skills appear
with names such as `/codevow:workflow` and `/codestack:code-standards`.
See [installation and scope](https://code.claude.com/docs/en/discover-plugins).

## ZCode

### ZCode desktop

1. Open a workspace, then **Settings → Plugins**.
2. Open **Create → Add plugin marketplace** and enter this full URL, or refresh
   the existing source if it already uses this URL:

   ```text
   https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/main/marketplace.json
   ```

3. Confirm **CodeVow 1.0.6** and **CodeStack 1.0.0** are available in the personal
   **ai-code** market, then remove installed previous IDs in **Manage installed**.
4. Install **CodeVow** and **CodeStack** and confirm each is enabled.
5. Check the installed versions, then start a new session.

Use the full URL: adding only the repository can select the Claude manifest,
whose `archive` source is unsupported by ZCode. If the error mentions
`unsupported ... archive`, remove the incorrect market source in **Marketplace
sources**, add the full URL above, and refresh. Source removal and plugin
uninstallation are separate operations.
See the [ZCode plugin guide](https://zcode.z.ai/en/docs/plugin).

### ZCode CLI

The example uses the application-bundled CLI on **macOS**, with ZCode at
`/Applications/ZCode.app` and `node` on `PATH`. Adjust the application path if
needed; other platforms can use the desktop procedure above.

```sh
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins marketplace add \
  https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/main/marketplace.json
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins marketplace update ai-code
```

Skip the add command for a correctly registered source. Confirm the replacement
entries in the refreshed desktop market before migration, then remove only
installed previous IDs:

```sh
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins uninstall ai-code-workflow@ai-code
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins uninstall ai-code-stack-standards@ai-code
```

Install, enable and check both plugins:

```sh
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins install codevow@ai-code
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins install codestack@ai-code
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins enable codevow@ai-code
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins enable codestack@ai-code
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins list
```

Start a new session and check the Plugin skills group.

## DeepSeek Harness

### Version compatibility

The published CodeVow 1.0.6 and CodeStack 1.0.0 bundles and index declare the exact
DSH version **`0.2.1-rc.2`**. They do **not** declare compatibility with
**`0.2.1-rc.3`**. Check **About DeepSeek Harness** on desktop or the actual CLI's
`--version` before installing. An incompatible market entry can have a disabled
Install button. Installing npm or using a TGZ does not remove the version check.
Do not use a version exemption as evidence of compatibility.

Desktop uses the same underlying application, but full Desktop and Web host
acceptance is still **pending**. CodeVow requires Agent Preset and the spawn
backend; minimal/SDK/ACP profiles are outside the declared trial scope.
This guide documents native installation routes, not a completed rc.3 adaptation.
The [published index](../published/dsh/index.json) is the current compatibility source.

### DeepSeek Harness desktop

**Use the installed desktop app. It includes its Node/pnpm installation runtime;
you do not need a separate npm CLI installation or a Web trial profile.**

1. Check the application version and compatibility above.
2. Open **Plugins**. Beside **Experimental plugins**, choose **More** and enable
   **Custom plugin markets**. It is an optional built-in feature.
3. Open **Discover → Add index source**; for an existing source use
   **Manage index sources…** and refresh. Add:

   ```text
   https://raw.githubusercontent.com/Zack-Zz/ai-code/main/published/dsh/index.json
   ```

4. Select **CodeVow** or **CodeStack**. Review the version, compatibility and fixed
   Git commit/subdirectory, then confirm installation **only for a compatible
   version**. Current rc.3 users need a compatible plugin release before this step.
5. Check the **Installed** tab and enabled bundle state. Restart the application
   if needed and create a fresh session to inspect its skills.

The index installs prebuilt Git bundles. The Release TGZ files are an additional
native package format; the plugins do not need an npm registry publication.
See [Desktop's bundled runtime](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.1-rc.3/apps/desktop/README.md#application-overview),
[Custom plugin markets](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.1-rc.3/packages/experimental/plugin-market-bundle/README.md#use-this-package)
and [Discover](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.1-rc.3/packages/client/ui-plugin-market/README.md#use-this-package).

### DeepSeek Harness CLI

These steps launch an independent **Web profile**, not the Desktop app's profile.
Use the official npm launcher pinned to the compatible runtime. Prepare Node.js
24+ and `pnpm` on `PATH`; the upstream repository also supports Node 22.19+ in
its 22.x range. This system-pnpm prerequisite applies to the standalone npm CLI,
not Desktop's bundled installer.

Download [CodeVow's TGZ](https://github.com/Zack-Zz/ai-code/releases/download/codevow%2Fv1.0.6/codevow-1.0.6-dsh-plugin.tgz)
and [CodeStack's TGZ](https://github.com/Zack-Zz/ai-code/releases/download/codestack%2Fv1.0.0/codestack-1.0.0-dsh-plugin.tgz),
plus each Release's `SHA256SUMS`. Check each TGZ against its corresponding
`installers/` checksum entry. The commands assume the files are in `$HOME/Downloads`;
replace those paths on another platform.

```sh
cd /path/to/your/project
npx --yes @deepseek-ai/dsh@0.2.1-rc.2 --version
```

Choose an **unused** profile name. Run this next command only once:
**`--from-default-profile` replaces an existing same-name profile, including its
plugin dependencies and user patch.** Do not run it on an existing Desktop or
personal profile.

```sh
npx --yes @deepseek-ai/dsh@0.2.1-rc.2 --profile ai-code-trial --from-default-profile web --dump-config
```

Install the prebuilt bundles into that profile, inspect configuration, and start it:

```sh
npx --yes @deepseek-ai/dsh@0.2.1-rc.2 plugin --profile ai-code-trial add "$HOME/Downloads/codevow-1.0.6-dsh-plugin.tgz"
npx --yes @deepseek-ai/dsh@0.2.1-rc.2 plugin --profile ai-code-trial add "$HOME/Downloads/codestack-1.0.0-dsh-plugin.tgz"
npx --yes @deepseek-ai/dsh@0.2.1-rc.2 --profile ai-code-trial --dump-config
npx --yes @deepseek-ai/dsh@0.2.1-rc.2 --profile ai-code-trial
```

Open the URL printed by the command (default `http://127.0.0.1:3080`). In
**Settings → Models**, configure and save your model credentials. Use **Choose
workspace** to select the project before starting a session. On later launches,
use only the last startup command: do not repeat profile initialization.
The Web UI can also install through the index using the same Plugins steps above.
See the [official CLI reference](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.1-rc.2/apps/cli/README.md)
and [Web setup guide](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.1-rc.2/docs/user/guide/index.md).

### First use and removal in Harness

In a fresh, compatible session, try `/workflow` for CodeVow or `/code-standards`
for CodeStack. For a read-only check, ask the assistant to list those skills and
load their instructions without changing project files. `/review` invokes the
review skill; its native read-only Reviewer still requires separate runtime
verification. Discovery does not prove automatic selection or task correctness.

On Desktop, disable and uninstall the bundle in **Plugins → Installed**. For the
standalone profile, use the same pinned CLI and the exact profile that owns it:

```sh
npx --yes @deepseek-ai/dsh@0.2.1-rc.2 plugin --profile ai-code-trial remove codevow
npx --yes @deepseek-ai/dsh@0.2.1-rc.2 plugin --profile ai-code-trial remove codestack
```

For Git-bundle upgrades, remove and install the compatible replacement through
the same host/profile, then restart where needed. There are no old DSH IDs to
migrate. Keep profile initialization out of upgrade/removal commands.

## Downloaded package installation

For Claude Code, Codex and ZCode, open the plugin's public
[Release](https://github.com/Zack-Zz/ai-code/releases) and select the host file.

| File | Use |
|---|---|
| `<ID>-<VERSION>-<HOST>.zip` | Local-market download, including market metadata |
| `<ID>-<VERSION>-<HOST>-plugin.zip` | Plugin-only archive used by the public market |
| `<ID>-<VERSION>-dsh-plugin.tgz` | Native Harness package; use its host/profile procedure above |

Download `SHA256SUMS` from the same plugin/version Release. Verify ZIP download
hashes against `downloads/`, and native installer hashes against `installers/`.
Extract a local-market ZIP into a stable directory and register that extracted
root, not its inner plugin directory:

| Host | Manifest under the extracted root | Register |
|---|---|---|
| Codex | `.agents/plugins/marketplace.json` | `codex plugin marketplace add /path/to/extracted` |
| Claude Code | `.claude-plugin/marketplace.json` | `claude plugin marketplace add /path/to/extracted` |
| ZCode | `marketplace.json` | Add that file through the desktop market UI |

Install from **ai-code-local**, the name declared by these local downloads.
For example, use `codex plugin add codevow@ai-code-local` or
`claude plugin install codevow@ai-code-local --scope user`. Keep the extracted
source directory while it is registered.

## Check installation

- Check the installed ID, version, source and enabled state in native plugin
  controls or the host's list command. New and old IDs must not both be enabled.
- In a fresh session, ask: “Load the installed CodeVow workflow and CodeStack
  code-standards instructions, report whether both can be read, and stay read-only.”
- CodeVow provides `workflow`, `tdd`, `debugging`, `review`, `review-results` and
  `verification`; CodeStack provides `code-standards`. The selector syntax differs
  by host, so use its skill picker or natural-language request when unsure.
- Package integrity, installation, skill visibility and actual behavior are
  separate checks. Building or listing a skill is not real-host acceptance.

## Update and uninstall

Refresh the market first. A catalog refresh does not by itself prove that the
running session has loaded a new installed version. For CodeStack, substitute
`codestack` in these CodeVow examples; apply the operation to both when needed.

| Host | Update | Uninstall |
|---|---|---|
| Codex | `codex plugin marketplace upgrade ai-code`; inspect the version in desktop controls and reinstall through native remove/add if it remains stale | `codex plugin remove codevow@ai-code` |
| Claude Code | `claude plugin marketplace update ai-code`, then `claude plugin update codevow@ai-code --scope user` | `claude plugin uninstall codevow@ai-code --scope user` |
| ZCode desktop | Marketplace sources → refresh `ai-code`, then Manage installed → Check updates | Installed plugin details → Uninstall |
| ZCode macOS CLI | After market refresh, `node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins update codevow@ai-code` | `node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins uninstall codevow@ai-code` |
| Harness | Refresh the index; check compatibility, then use the same host/profile's remove/install procedure above | Plugins → Installed, or the pinned profile removal command above |

After changes, reload or start a new session; restart Harness where needed.
Remove the market source separately if it is no longer needed. Plugin removal
must not be used as a reason to delete project `.ai-workflow/` records.

## Troubleshooting and requirements

| Symptom / feature | Check |
|---|---|
| New IDs missing | Refresh the correct `ai-code` source; compare the release index. Registering/removing a source and installing/uninstalling a plugin are separate operations. |
| Duplicate workflow or standards skills | Remove installed previous IDs, then start a new session. |
| Claude `archive` unsupported | Check 2.1.224+, correct manifest, and use the CLI install path if the interactive panel still refuses it. |
| ZCode `archive` unsupported | Replace the market source with the root `marketplace.json` URL above. |
| Harness Install disabled | Compare actual DSH runtime with the index's exact `engines.dsh`; current rc.3 is not covered. |
| Harness installed but skills absent | Check bundle enablement, restart/new session, required services and profile compatibility; do not infer activation from package installation. |
| CodeVow optional Python tools | Python 3.11+; optional file staging requires POSIX file operations. Markdown skills do not require Python. |
| CodeStack | No additional runtime or dependency on another ai-code plugin. |

Each host manages its account and model. The unpublished Agent Delegation plugin
additionally requires Python 3 and a configured `agent-bridge/v1` CLI;
[Bridge setup](https://github.com/Zack-Zz/ai-mcp/blob/main/packages/agent-bridge/README.md#构建与受控配置)
requires its own supported platform and authenticated target tools.

## Next steps

- [CodeVow usage and configuration](../plugins/codevow/docs/usage.md)
- [CodeStack conventions](../plugins/codestack/README.md)
- [Agent Delegation source examples](../plugins/ai-agent-delegation/README.md)
