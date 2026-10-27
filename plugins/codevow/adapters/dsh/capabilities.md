# DeepSeek Harness capability boundary

English | [简体中文](capabilities.zh-CN.md)

The candidate bundle targets the published DeepSeek Harness `0.2.1-rc.2` APIs.
The design started from upstream commit `22ddee3792402c3e70ec5f86a63c3e3e895a2f60`;
the installed RC2 API uses official `agent-tool-presentation` with `mode: native`
and `modelSelectionSettings: false` for preset-specific spawning. A Web profile must provide
agentPresets, agents, tools, systemPrompt, subagents spawn and sessionProjections;
Loader injection reports missing dependencies rather than falling back.

`workflow_reviewer` selects `codevow-reviewer`, with inherited model routing and
no selectable alternative preset. The shared reviewer contract becomes a JSON
string at build time. Native read/grep/glob definitions, an Agent-owned restriction
and a composition-scoped final guard enforce the tool boundary. Search tools may
start a fixed ripgrep process; there is no general shell tool. File read roots
remain the host's configuration: `reviewer_restriction` and `workspace_isolation`
need separate acceptance evidence. Creation failure does not admit queued work.
Recomposition, restoration, disposal and unload are handled explicitly.

Unit contracts and package integrity do not certify native activation, model
behavior, installation or lifecycle acceptance. All release acceptance slots
remain null. The package's Python tools retain the Python 3.11+ requirement.
