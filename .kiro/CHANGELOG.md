# Kiro Support Changelog

## 2024-12 - Initial Kiro Support

### Added

#### Steering Files (`.kiro/steering/`)
- `ai-code-core.md` - Core principles and quality guidelines (always included)
- `agents-overview.md` - Reference to 13 specialized agent guidelines (always included)
- `security-checklist.md` - Security best practices and common vulnerabilities (always included)
- `coding-standards.md` - Immutability, file organization, error handling (always included)
- `tdd-workflow.md` - Test-driven development methodology (fileMatch: test files)
- `multi-language-workflow.md` - Language-specific commands (fileMatch: source files)

#### Hooks Configuration (`.kiro/hooks/`)
- `hooks.json` - Event-based automations:
  - `file-edited-format` - Auto-format code files when edited
  - `file-edited-console-warn` - Warn about console.log in production code
  - `prompt-submit-security` - Security checklist reminder on commit/push/deploy
  - `agent-stop-session-summary` - Session summary when agent stops

#### MCP Configuration (`.kiro/settings/`)
- `mcp.json` - MCP server template with:
  - filesystem - File system access (disabled by default, configure path first)
  - github - GitHub API access (disabled, requires token)
  - postgres - PostgreSQL database access (disabled, requires connection string)
  - brave-search - Web search via Brave Search API (disabled, requires API key)

**All MCP servers are disabled by default for security. Configure before enabling.**

#### Documentation
- `.kiro/README.md` - Comprehensive Kiro configuration guide
- `.kiro/CHANGELOG.md` - This file

#### Bootstrap Script Enhancement
- Enhanced `scripts/bootstrap-project.sh` to support `--tool kiro`
- Copies all 6 steering files
- Copies hooks configuration
- Copies MCP template
- Provides setup instructions

#### Main Documentation Updates
- Updated `README.md` with Kiro IDE Support section
- Updated `README.zh-CN.md` with Kiro setup instructions
- Added Kiro to Quick Start options

### Features

#### Automatic Context Loading
- Steering files automatically load based on `inclusion` setting
- `always` - Loaded in every session
- `fileMatch` - Loaded when specific file types are in context

#### Event-Based Automations
- Hooks trigger on file edits, prompt submissions, and agent stops
- Customizable hook actions (askAgent, runCommand)
- File pattern matching for targeted hooks

#### MCP Integration
- Template configuration for common MCP servers
- Easy setup with placeholder replacement
- Disabled by default for security

#### Agent Guidelines Reference
- 13 specialized agent workflows available as reference
- Adapted for Kiro's non-delegating architecture
- Clear guidance on when to apply each agent's principles

### Differences from Claude Code

Kiro uses a different configuration structure:
- Guidelines: `steering/` instead of `rules/`
- Inclusion: `inclusion: always` instead of `alwaysApply`
- File matching: `fileMatchPattern` supported (Claude Code doesn't have this)
- Hooks: `.kiro/hooks/hooks.json` instead of root `hooks.json`
- MCP: `.kiro/settings/mcp.json` instead of `config.json`
- Agents: Reference guidelines only (no native delegation)

### Usage

```bash
# Bootstrap a new project
scripts/bootstrap-project.sh --target /path/to/project --langs java,python --tool kiro

# Or use this repo directly
# Open in Kiro - steering files load automatically
```

### Next Steps

Users should:
1. Open project in Kiro
2. Configure MCP servers in `.kiro/settings/mcp.json` (replace `YOUR_*_HERE`)
3. Review hooks in `.kiro/hooks/hooks.json`
4. Customize steering files as needed

### Known Limitations

- Kiro doesn't support native agent delegation (use guidelines as reference)
- MCP servers require manual API key configuration
- Hooks use `askAgent` type (not `runCommand` for shell commands)

### Future Enhancements

Potential improvements:
- Language-specific steering files (Java, Python, Go, etc.)
- More hook examples for common workflows
- Integration with Kiro's native features as they evolve
- CI validation for Kiro configuration files
