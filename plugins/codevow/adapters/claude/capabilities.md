# Claude Code package target

Status as of 2026-10-07: **unverified** for native discovery, explicit invocation,
automatic selection, policy loading, native subagents, reviewer restrictions
and workspace isolation. The adapter supplies format/configuration only.

The native plugin manifest is `.claude-plugin/plugin.json`; the local market
is `.claude-plugin/marketplace.json`. Reviewer frontmatter declares
`tools: Read, Grep, Glob`, `model: inherit` and `maxTurns: 12`; the body is composed
from `skills/review/references/reviewer-contract.md`. Enforcement remains
`policy_only` until a real host session confirms the declared restrictions.

Format sources: [manifest reference](https://code.claude.com/docs/en/plugins-reference),
[marketplace guide](https://code.claude.com/docs/en/plugin-marketplaces),
[subagent reference](https://code.claude.com/docs/en/sub-agents), read 2026-10-07.
No native installation or model session has been run by this change. The
historical Codex/ZCode A25 evidence does not certify Claude Code.
