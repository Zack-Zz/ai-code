# Installing CodeVow

English | [简体中文](installation.zh-CN.md)

See the unified [installation guide](../../../docs/installation.md) for
marketplace installation, Release downloads, updates, removal and dependencies.

Choose [Codex desktop and CLI](../../../docs/installation.md#codex),
[Claude Code desktop and CLI](../../../docs/installation.md#claude-code),
[ZCode desktop and macOS bundled CLI](../../../docs/installation.md#zcode), or
[DeepSeek Harness desktop and standalone npm CLI](../../../docs/installation.md#deepseek-harness).

CodeVow `codevow` 1.0.6 is published; its DSH bundle and public index still pin
`engines.dsh` and DSH peers to exact `0.2.1-rc.2`. The local 1.0.7 candidate uses
minimum `>=0.2.1-rc.2` for both, accepting RC3 and later versions at the version
gate. It is not yet in the public index or Releases. A range match does not
certify future APIs, and real desktop acceptance remains pending.
The desktop app bundles Node.js and pnpm and needs no separate npm CLI installation.

For configuration, task records and optional project file staging, see
[Using CodeVow](usage.md).
