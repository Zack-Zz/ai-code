# Installing CodeVow

English | [简体中文](installation.zh-CN.md)

See the unified [installation guide](../../../docs/installation.md) for
marketplace installation, Release downloads, updates, removal and dependencies.

Choose [Codex desktop and CLI](../../../docs/installation.md#codex),
[Claude Code desktop and CLI](../../../docs/installation.md#claude-code),
[ZCode desktop and macOS bundled CLI](../../../docs/installation.md#zcode), or
[DeepSeek Harness desktop and standalone npm CLI](../../../docs/installation.md#deepseek-harness).

CodeVow `codevow` 1.0.7 is published; its DSH bundle and public index declare
minimum `>=0.2.1-rc.2` in `engines.dsh` and DSH peers. RC3 and later versions pass
this version gate. A range match does not certify future APIs, and real desktop
acceptance remains pending.
The desktop app bundles Node.js and pnpm and needs no separate npm CLI installation.

For configuration, task records and optional project file staging, see
[Using CodeVow](usage.md).

## Google Antigravity

The current source candidate adds this native target. After publication, use the
[Antigravity guide](../../../docs/installation.md#google-antigravity) and its
immutable GitHub version path. Existing released packages do not include this
adapter. Native installation, loading and skill behavior remain unverified.
