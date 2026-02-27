# ai-code Usage (Quick)

This is the local, concise usage guide for `ai-code`.

## 1) Pick Your Tool

- Codex/ChatGPT: use `.codex/` + `AGENTS.md` + `codex.md`
- Claude Code: use plugin/rules/commands/hook assets
- Kiro: use `.kiro/steering/`
- Cursor/OpenCode: use `.cursor/` / `.opencode/`

## 2) Bootstrap a New Project

```bash
scripts/bootstrap-project.sh --target /path/to/project --langs java
scripts/bootstrap-project.sh --target /path/to/project --langs java,python,go
```

Optional tool mode:

```bash
scripts/bootstrap-project.sh --target /path/to/project --langs java --tool auto
scripts/bootstrap-project.sh --target /path/to/project --langs java --tool codex
scripts/bootstrap-project.sh --target /path/to/project --langs java --tool kiro
scripts/bootstrap-project.sh --target /path/to/project --langs java --tool claude
scripts/bootstrap-project.sh --target /path/to/project --langs java --tool both
scripts/bootstrap-project.sh --target /path/to/project --langs java --tool all
```

## 3) Language Strategy

- Common skills are always included (security, tdd, verification, coding standards).
- Java projects add Spring/Java-specific skills.
- JS projects add frontend/e2e skills.
- Python/Go projects add corresponding language skills.

## 4) Recommended Practice

- Keep `~/.codex/config.toml` for global model/MCP defaults.
- Keep project instructions in project root (`AGENTS.md`, `codex.md`).
- Avoid global full-skill installs; inject only needed skills per project.

## 5) Unified Runtime Paths (Codex + Claude)

`ai-code` hook scripts now support shared path/tool overrides:

```bash
# Select assistant mode
export AI_CODE_TOOL=codex   # or claude

# Force a custom state directory (sessions, learned skills, aliases)
export AI_CODE_HOME=/path/to/assistant-home
```

Per-command overrides are also supported:

```bash
node scripts/hooks/session-start.js --tool codex
node scripts/hooks/session-end.js --tool claude --home /tmp/ai-code-home
```

Path defaults:
- `AI_CODE_HOME` set: always use that directory
- `AI_CODE_TOOL=codex`: defaults to `~/.codex`
- otherwise defaults to `~/.claude`
