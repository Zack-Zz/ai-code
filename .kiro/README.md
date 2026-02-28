# Kiro Configuration for ai-code

This directory contains Kiro-specific configuration files for the ai-code toolkit.

## Directory Structure

```
.kiro/
├── steering/              # Steering files (auto-loaded by Kiro)
│   ├── ai-code-core.md           # Core principles (always included)
│   ├── agents-overview.md        # Agent guidelines reference (always included)
│   ├── security-checklist.md     # Security best practices (always included)
│   ├── coding-standards.md       # Coding standards (always included)
│   ├── tdd-workflow.md           # TDD methodology (fileMatch: test files)
│   └── multi-language-workflow.md # Language-specific commands (fileMatch: source files)
├── hooks/                 # Hook configurations
│   └── hooks.json                # Event-based automations
├── settings/              # Kiro settings
│   └── mcp.json                  # MCP server configurations
└── README.md              # This file
```

## Steering Files

Steering files provide context and guidelines to Kiro. They are automatically loaded based on their `inclusion` setting:

### Always Included
These files are loaded in every Kiro session:
- `ai-code-core.md` - Core behavior and quality principles
- `agents-overview.md` - Reference to 13 specialized agent guidelines
- `security-checklist.md` - Security requirements and common vulnerabilities
- `coding-standards.md` - Immutability, file organization, error handling

### Conditionally Included (fileMatch)
These files are loaded when specific file types are in context:
- `tdd-workflow.md` - Loaded when working with test files (*.test.*, *.spec.*)
- `multi-language-workflow.md` - Loaded when working with source files (*.java, *.py, *.go, *.ts, etc.)

## Hooks

Hooks in `.kiro/hooks/hooks.json` provide event-based automations:

### Available Hooks
1. **file-edited-format** - Auto-format code files when edited
2. **file-edited-console-warn** - Warn about console.log in production code
3. **prompt-submit-security** - Security checklist reminder on commit/push/deploy
4. **agent-stop-session-summary** - Session summary when agent stops

### Hook Events
Kiro supports these hook events:
- `fileEdited` - When a file is saved
- `fileCreated` - When a new file is created
- `fileDeleted` - When a file is deleted
- `promptSubmit` - When a message is sent to Kiro
- `agentStop` - When Kiro finishes processing
- `userTriggered` - Manual trigger by user

## MCP Configuration

MCP (Model Context Protocol) servers provide additional capabilities to Kiro.

**All MCP servers are disabled by default for security.**

### Configuration File
`.kiro/settings/mcp.json` contains MCP server definitions.

### Setup Steps
1. Open `.kiro/settings/mcp.json`
2. For filesystem server:
   - Replace `/path/to/allowed/directory` with actual allowed path
   - Set `disabled: false` to enable
3. For other servers:
   - Replace `YOUR_*_HERE` placeholders with actual API keys
   - Set `disabled: false` to enable
4. Restart Kiro after changes

### Available MCP Servers (Template)
- **filesystem** - File system access (disabled, configure allowed directory first)
- **github** - GitHub API access (disabled, requires GITHUB_PERSONAL_ACCESS_TOKEN)
- **postgres** - PostgreSQL database access (disabled, requires connection string)
- **brave-search** - Web search via Brave Search API (disabled, requires BRAVE_API_KEY)

For more MCP servers, see `mcp-configs/mcp-servers.json` in the ai-code repository root.

## Quick Start

### 1. Bootstrap a New Project
```bash
# From ai-code repository root
scripts/bootstrap-project.sh --target /path/to/your-project --langs java,python --tool kiro
```

This will copy:
- All steering files to `.kiro/steering/`
- Hooks configuration to `.kiro/hooks/hooks.json`
- MCP template to `.kiro/settings/mcp.json`
- Documentation files (README.md, QUICK_START.md, CHANGELOG.md)

### 2. Configure MCP Servers (Optional)
```bash
cd /path/to/your-project
# Edit MCP configuration
vim .kiro/settings/mcp.json
# Replace YOUR_*_HERE with actual API keys
# Set disabled: false for servers you want to use
```

### 3. Open in Kiro
```bash
# Open the project directory in Kiro
# Steering files will be automatically loaded
```

## Customization

### Adding Custom Steering Files
Create new `.md` files in `.kiro/steering/` with frontmatter:

```markdown
---
inclusion: always
---

# Your Custom Steering

Your guidelines here...
```

Or use `fileMatch` for conditional inclusion:

```markdown
---
inclusion: fileMatch
fileMatchPattern: ".*\\.tsx?$"
---

# TypeScript-Specific Guidelines

Your TypeScript guidelines here...
```

### Adding Custom Hooks
Edit `.kiro/hooks/hooks.json` to add new hooks:

```json
{
  "id": "your-hook-id",
  "name": "Your Hook Name",
  "description": "What this hook does",
  "when": {
    "type": "fileEdited",
    "patterns": ["*.ts"]
  },
  "then": {
    "type": "askAgent",
    "prompt": "Your prompt to Kiro"
  }
}
```

## Differences from Claude Code

Kiro uses a different configuration structure than Claude Code:

| Feature | Claude Code | Kiro |
|---------|-------------|------|
| Guidelines | `rules/` directory | `steering/` directory |
| Inclusion | `alwaysApply` field | `inclusion: always` |
| File matching | Not supported | `inclusion: fileMatch` |
| Hooks | `hooks.json` in root | `.kiro/hooks/hooks.json` |
| MCP | `config.json` | `.kiro/settings/mcp.json` |
| Agents | Native delegation | Reference guidelines only |

## Agent Guidelines Reference

While Kiro doesn't have native agent delegation like Claude Code, you can reference agent guidelines from the repository:

- `agents/planner.md` - Implementation planning
- `agents/tdd-guide.md` - Test-driven development
- `agents/code-reviewer.md` - Code quality review
- `agents/security-reviewer.md` - Security audits
- And 9 more specialized agents

See `AGENTS.md` in the repository root for the complete list.

## Skills Reference

The ai-code repository includes 50+ skills with detailed patterns and workflows:

- `skills/tdd-workflow/` - TDD methodology
- `skills/security-review/` - Security patterns
- `skills/backend-patterns/` - API, database, caching
- `skills/frontend-patterns/` - React, Next.js patterns
- And many more...

These skills are referenced in steering files but not directly copied to Kiro projects.

## Troubleshooting

### Steering Files Not Loading
- Check frontmatter syntax (must have `---` delimiters)
- Verify `inclusion` field is set correctly
- Ensure file is in `.kiro/steering/` directory

### Hooks Not Triggering
- Verify hook syntax in `.kiro/hooks/hooks.json`
- Check that event type matches Kiro's supported events
- Ensure file patterns match the files you're editing

### MCP Servers Not Working
- Verify API keys are set correctly (no `YOUR_*_HERE` placeholders)
- Check that `disabled: false` for servers you want to use
- Ensure required dependencies are installed (npx will auto-install)

## Resources

- **ai-code Repository**: https://github.com/Zack-Zz/ai-code
- **Kiro Documentation**: Check Kiro's official documentation for steering and hooks
- **MCP Protocol**: https://modelcontextprotocol.io/

## Contributing

To improve Kiro support in ai-code:
1. Fork the repository
2. Make changes to `.kiro/` directory
3. Test with `scripts/bootstrap-project.sh --tool kiro`
4. Submit a pull request

## License

MIT - Same as the ai-code repository
