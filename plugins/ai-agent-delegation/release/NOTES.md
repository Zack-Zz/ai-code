# Agent Delegation candidate

Candidate scope: a single explicit delegation skill, Claude Code/Codex/ZCode
adapters, a Python standard-library consumer of external agent-bridge/v1, and
consumer/skill/resource tests. Explicit target selection, independent-session
intent, exact continuation IDs, stable write request IDs and bounded artifact
access are documented and tested at the client boundary.

All native host behavior is unverified. Runtime/engine integration, desktop
visibility and native MCP loading are separate gates. No original host acceptance
artifacts are included in public packages. This candidate adds no automatic
installation, global configuration edits, model pipeline or publishing authority.
