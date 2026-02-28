# Kiro Quick Start Guide

## 🚀 Setup (2 minutes)

### Option 1: Bootstrap New Project
```bash
cd /path/to/ai-code
scripts/bootstrap-project.sh --target /path/to/your-project --langs java,python --tool kiro
cd /path/to/your-project
# Open in Kiro
```

### Option 2: Use ai-code Repo Directly
```bash
git clone https://github.com/Zack-Zz/ai-code.git
cd ai-code
# Open in Kiro
```

## 📁 What You Get

```
.kiro/
├── steering/              # Auto-loaded guidelines
│   ├── ai-code-core.md           ✓ Always loaded
│   ├── agents-overview.md        ✓ Always loaded
│   ├── security-checklist.md     ✓ Always loaded
│   ├── coding-standards.md       ✓ Always loaded
│   ├── tdd-workflow.md           ⚡ Loaded with test files
│   └── multi-language-workflow.md ⚡ Loaded with source files
├── hooks/
│   └── hooks.json                # Event automations
└── settings/
    └── mcp.json                  # MCP servers (needs config)
```

## ⚙️ Configure MCP (Optional)

**All MCP servers are disabled by default for security.**

1. Open `.kiro/settings/mcp.json`
2. For filesystem server:
   - Replace `/path/to/allowed/directory` with actual path
   - Set `disabled: false`
3. For other servers, replace `YOUR_*_HERE` with actual API keys:
   ```json
   "GITHUB_PERSONAL_ACCESS_TOKEN": "ghp_your_token_here"
   ```
4. Set `disabled: false` for servers you want to use
5. Save and restart Kiro

## 🎯 Core Principles (Always Active)

### 1. Test-Driven Development
- Write test FIRST (RED)
- Implement minimal code (GREEN)
- Refactor (IMPROVE)
- 80%+ coverage required

### 2. Security-First
- No hardcoded secrets
- Validate all inputs
- Parameterized queries only
- Sanitize HTML output

### 3. Immutability
```typescript
// ❌ BAD
user.age = 31;

// ✅ GOOD
const updatedUser = { ...user, age: 31 };
```

### 4. Code Quality
- Functions < 50 lines
- Files < 800 lines
- No deep nesting (> 4 levels)
- Proper error handling

## 🪝 Hooks (Automatic)

| Hook | Trigger | Action |
|------|---------|--------|
| Auto-format | File edited | Checks if formatting needed |
| Console warn | File edited | Warns about console.log |
| Security check | Prompt submit | Reminds security checklist on commit |
| Session summary | Agent stop | Summarizes session |

## 🤖 Agent Guidelines (Reference)

When working on tasks, mentally apply these workflows:

| Task | Apply Guidelines |
|------|------------------|
| New feature | planner → tdd-guide → code-reviewer |
| Bug fix | tdd-guide → code-reviewer |
| Refactoring | architect → refactor-cleaner → code-reviewer |
| Security | security-reviewer (before any commit) |

## 📚 Language Commands

### JavaScript/TypeScript
```bash
npm test                    # Run tests
npm run test:coverage      # Check coverage
npm run lint               # Lint code
```

### Python
```bash
pytest                     # Run tests
pytest --cov              # Check coverage
ruff check .              # Lint code
```

### Go
```bash
go test ./...             # Run tests
go test -cover ./...      # Check coverage
go vet ./...              # Lint code
```

### Java
```bash
mvn test                  # Run tests (Maven)
./gradlew test            # Run tests (Gradle)
```

## 🔍 Common Workflows

### Starting a New Feature
1. Read requirements
2. Plan implementation (see `agents/planner.md`)
3. Write failing test
4. Implement minimal code
5. Refactor
6. Review security checklist
7. Commit

### Fixing a Bug
1. Write test that reproduces bug (should FAIL)
2. Fix implementation
3. Verify test PASSES
4. Check for similar issues
5. Commit

### Before Committing
- [ ] All tests pass
- [ ] Coverage ≥ 80%
- [ ] No hardcoded secrets
- [ ] No console.log in production code
- [ ] Security checklist reviewed
- [ ] Code formatted

## 📖 Documentation

- **Full guide**: `.kiro/README.md`
- **Changelog**: `.kiro/CHANGELOG.md`
- **Agent details**: `agents/*.md` in repo root
- **Skills**: `skills/*/SKILL.md` in repo root

## 🆘 Troubleshooting

### Steering files not loading?
- Check frontmatter syntax (must have `---` delimiters)
- Verify `inclusion` field is set
- Ensure file is in `.kiro/steering/`

### Hooks not triggering?
- Verify JSON syntax in `.kiro/hooks/hooks.json`
- Check event type matches Kiro's supported events
- Ensure file patterns match your files

### MCP servers not working?
- Replace all `YOUR_*_HERE` placeholders
- Set `disabled: false`
- Restart Kiro after config changes

## 💡 Tips

1. **Start small** - Enable only the MCP servers you need
2. **Customize steering** - Add project-specific guidelines to `.kiro/steering/`
3. **Review hooks** - Adjust hook prompts to match your workflow
4. **Reference agents** - Check `agents/*.md` for detailed workflows
5. **Use skills** - Browse `skills/` for patterns and best practices

## 🔗 Resources

- **Repository**: https://github.com/Zack-Zz/ai-code
- **Issues**: https://github.com/Zack-Zz/ai-code/issues
- **MCP Protocol**: https://modelcontextprotocol.io/

---

**Ready to code!** Open your project in Kiro and start building with AI-powered guidance.
