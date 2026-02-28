# Kiro Integration Guide

This document describes the complete Kiro integration in the ai-code toolkit.

## Overview

The ai-code toolkit now provides comprehensive support for Kiro IDE through:
- 6 steering files with automatic context loading
- 4 event-based hooks for automation
- MCP server configuration template
- Enhanced bootstrap script for easy setup
- Complete documentation

## What Was Added

### 1. Steering Files (`.kiro/steering/`)

| File | Inclusion | Purpose |
|------|-----------|---------|
| `ai-code-core.md` | always | Core principles and quality guidelines |
| `agents-overview.md` | always | Reference to 13 specialized agent workflows |
| `security-checklist.md` | always | Security best practices and vulnerability examples |
| `coding-standards.md` | always | Immutability, file organization, error handling |
| `tdd-workflow.md` | fileMatch: `*.test.*`, `*.spec.*` | Test-driven development methodology |
| `multi-language-workflow.md` | fileMatch: source files | Language-specific commands and workflows |

**Key Features:**
- Automatic loading based on `inclusion` setting
- Conditional loading with `fileMatchPattern` for context-aware guidance
- Consistent with ai-code's core principles
- Adapted for Kiro's non-delegating architecture

### 2. Hooks Configuration (`.kiro/hooks/hooks.json`)

Four event-based hooks for common workflows:

| Hook ID | Event | Action |
|---------|-------|--------|
| `file-edited-format` | fileEdited | Checks if formatting is needed |
| `file-edited-console-warn` | fileEdited | Warns about console.log statements |
| `prompt-submit-security` | promptSubmit | Security checklist reminder on commit |
| `agent-stop-session-summary` | agentStop | Provides session summary |

**Supported Events:**
- `fileEdited`, `fileCreated`, `fileDeleted`
- `promptSubmit`, `agentStop`, `userTriggered`

### 3. MCP Configuration (`.kiro/settings/mcp.json`)

Template configuration for 4 common MCP servers:

| Server | Purpose | Status |
|--------|---------|--------|
| filesystem | File system access | Disabled (configure path first) |
| github | GitHub API operations | Disabled (needs token) |
| postgres | PostgreSQL database | Disabled (needs connection string) |
| brave-search | Web search | Disabled (needs API key) |

**All servers disabled by default for security.**

**Setup Required:**
- Replace `YOUR_*_HERE` placeholders with actual credentials
- Set `disabled: false` to enable
- Adjust paths and connection strings

### 4. Documentation

| File | Purpose |
|------|---------|
| `.kiro/README.md` | Comprehensive configuration guide |
| `.kiro/QUICK_START.md` | 2-minute setup guide with common workflows |
| `.kiro/CHANGELOG.md` | Version history and changes |
| `docs/KIRO_INTEGRATION.md` | This file - integration overview |

### 5. Bootstrap Script Enhancement

Enhanced `scripts/bootstrap-project.sh` with Kiro support:

```bash
# New usage
scripts/bootstrap-project.sh --target /path/to/project --langs java,python --tool kiro

# What it copies
- All 6 steering files → .kiro/steering/
- Hooks configuration → .kiro/hooks/hooks.json
- MCP template → .kiro/settings/mcp.json
```

**Tool Modes:**
- `--tool kiro` - Kiro only
- `--tool both` - Codex + Kiro
- `--tool all` - Codex + Kiro + Claude
- `--tool auto` - Detect from existing directories

### 6. Main Documentation Updates

**README.md:**
- Added "Kiro IDE Support" section with full details
- Updated Quick Start with Kiro option
- Added comparison table (Kiro vs Claude Code)

**README.zh-CN.md:**
- Added Kiro setup instructions in Chinese
- Updated Quick Start section

## Architecture Decisions

### Why Steering Files Instead of Rules?

Kiro uses `steering/` directory with `inclusion` frontmatter, different from Claude Code's `rules/` with `alwaysApply`. We adapted to Kiro's native format for better integration.

### Why Reference-Only Agents?

Kiro doesn't support native agent delegation like Claude Code. Instead, we provide agent guidelines as reference material that users can mentally apply to their workflows.

### Why Separate MCP Configuration?

Kiro uses `.kiro/settings/mcp.json` instead of root-level `config.json`. We follow Kiro's convention for better organization and isolation.

### Why FileMatch for Conditional Loading?

Kiro supports `fileMatchPattern` for context-aware loading. This allows TDD guidelines to load only when working with test files, reducing cognitive load.

## Comparison with Other Assistants

| Feature | Claude Code | Kiro | Codex |
|---------|-------------|------|-------|
| Guidelines | `rules/` | `steering/` | `AGENTS.md` |
| Inclusion | `alwaysApply` | `inclusion: always` | Always loaded |
| File matching | ❌ | ✅ `fileMatchPattern` | ❌ |
| Hooks | Root `hooks.json` | `.kiro/hooks/hooks.json` | Not supported |
| MCP | `config.json` | `.kiro/settings/mcp.json` | `config.toml` |
| Agents | Native delegation | Reference only | Reference only |
| Commands | Slash commands | Not supported | Not supported |

## Usage Examples

### Example 1: Bootstrap New Java Project

```bash
cd /path/to/ai-code
scripts/bootstrap-project.sh \
  --target ~/projects/my-java-app \
  --langs java \
  --tool kiro

cd ~/projects/my-java-app
# Open in Kiro
# Steering files load automatically
```

**Result:**
- 6 steering files copied
- Hooks configured for Java files
- MCP template ready for configuration
- Java-specific skills referenced

### Example 2: Multi-Language Project

```bash
scripts/bootstrap-project.sh \
  --target ~/projects/fullstack-app \
  --langs java,typescript,python \
  --tool kiro

# Opens with:
# - Java, TypeScript, Python workflows
# - Multi-language steering files
# - Language-specific test patterns
```

### Example 3: Use ai-code Repo Directly

```bash
git clone https://github.com/Zack-Zz/ai-code.git
cd ai-code
# Open in Kiro
# All steering files available immediately
```

## Customization Guide

### Adding Custom Steering Files

Create new `.md` files in `.kiro/steering/`:

```markdown
---
inclusion: always
---

# Project-Specific Guidelines

Your custom guidelines here...
```

Or with file matching:

```markdown
---
inclusion: fileMatch
fileMatchPattern: ".*\\.graphql$"
---

# GraphQL Guidelines

GraphQL-specific guidelines here...
```

### Adding Custom Hooks

Edit `.kiro/hooks/hooks.json`:

```json
{
  "id": "custom-hook",
  "name": "Custom Hook",
  "description": "What this hook does",
  "when": {
    "type": "fileEdited",
    "patterns": ["*.custom"]
  },
  "then": {
    "type": "askAgent",
    "prompt": "Your custom prompt"
  }
}
```

### Configuring MCP Servers

1. Open `.kiro/settings/mcp.json`
2. Add your credentials:
   ```json
   "env": {
     "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_actual_token"
   }
   ```
3. Enable the server:
   ```json
   "disabled": false
   ```
4. Restart Kiro

## Testing the Integration

### Manual Testing Checklist

- [ ] Bootstrap script runs without errors
- [ ] All 6 steering files are copied
- [ ] Hooks configuration is valid JSON
- [ ] MCP template has correct structure
- [ ] Documentation is accessible
- [ ] README updates are accurate

### Verification Commands

```bash
# Verify bootstrap script
bash scripts/bootstrap-project.sh --help

# Check Kiro directory structure
ls -la .kiro/steering/
ls -la .kiro/hooks/
ls -la .kiro/settings/

# Validate JSON files
cat .kiro/hooks/hooks.json | jq .
cat .kiro/settings/mcp.json | jq .

# Check steering file frontmatter
head -n 5 .kiro/steering/*.md
```

## Troubleshooting

### Issue: Steering files not loading

**Symptoms:** Guidelines not appearing in Kiro context

**Solutions:**
1. Check frontmatter syntax (must have `---` delimiters)
2. Verify `inclusion` field is set correctly
3. Ensure file is in `.kiro/steering/` directory
4. Restart Kiro

### Issue: Hooks not triggering

**Symptoms:** No automation when files are edited

**Solutions:**
1. Validate JSON syntax in `.kiro/hooks/hooks.json`
2. Check event type matches Kiro's supported events
3. Verify file patterns match your files
4. Check Kiro's hook logs

### Issue: MCP servers not working

**Symptoms:** MCP commands fail or not available

**Solutions:**
1. Replace all `YOUR_*_HERE` placeholders
2. Set `disabled: false` for servers you want
3. Verify API keys are valid
4. Check network connectivity
5. Restart Kiro after config changes

## Migration from Claude Code

If you're migrating from Claude Code to Kiro:

| Claude Code | Kiro Equivalent |
|-------------|-----------------|
| `rules/common/security.md` | `.kiro/steering/security-checklist.md` |
| `rules/common/coding-style.md` | `.kiro/steering/coding-standards.md` |
| `rules/common/testing.md` | `.kiro/steering/tdd-workflow.md` |
| `hooks/hooks.json` | `.kiro/hooks/hooks.json` |
| `config.json` (MCP) | `.kiro/settings/mcp.json` |

**Key Differences:**
- Change `alwaysApply: true` to `inclusion: always`
- Move hooks to `.kiro/hooks/` directory
- Move MCP config to `.kiro/settings/` directory
- Agent delegation → Reference guidelines

## Future Enhancements

Potential improvements for future versions:

1. **Language-Specific Steering Files**
   - Java-specific patterns and anti-patterns
   - Python-specific idioms and best practices
   - Go-specific concurrency patterns

2. **More Hook Examples**
   - Pre-commit validation hooks
   - Test coverage enforcement
   - Documentation generation

3. **CI Validation**
   - `scripts/ci/validate-kiro-steering.js`
   - `scripts/ci/validate-kiro-hooks.js`
   - Automated testing of Kiro configurations

4. **Integration with Kiro Features**
   - As Kiro evolves, adapt to new capabilities
   - Leverage Kiro-specific features
   - Optimize for Kiro's architecture

## Contributing

To improve Kiro support:

1. Fork the repository
2. Make changes to `.kiro/` directory
3. Test with `scripts/bootstrap-project.sh --tool kiro`
4. Update documentation
5. Submit pull request

**Guidelines:**
- Follow existing steering file format
- Keep hooks simple and focused
- Document all changes in `.kiro/CHANGELOG.md`
- Test on actual Kiro installation

## Resources

- **ai-code Repository**: https://github.com/Zack-Zz/ai-code
- **Kiro Documentation**: Check Kiro's official docs
- **MCP Protocol**: https://modelcontextprotocol.io/
- **Issues**: https://github.com/Zack-Zz/ai-code/issues

## License

MIT - Same as the ai-code repository

---

**Last Updated:** 2024-12
**Version:** 1.0.0
**Status:** Production Ready
