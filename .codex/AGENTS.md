# ai-code for Codex (CLI + GUI)

This supplements the root `AGENTS.md` with Codex-specific guidance for both CLI and Codex GUI.

## Model Recommendations

| Task Type | Recommended Model |
|-----------|------------------|
| Routine coding, tests, formatting | gpt-5.3-codex |
| Complex features, architecture | gpt-5.3-codex |
| Debugging, refactoring | gpt-5.3-codex |
| Security review | gpt-5.3-codex |

## Skills Discovery

Skills are auto-loaded from `.agents/skills/`. Each skill contains:
- `SKILL.md` — Detailed instructions and workflow
- `agents/openai.yaml` — Codex interface metadata

Available skills:
- tdd-workflow — Test-driven development with 80%+ coverage
- security-review — Comprehensive security checklist
- coding-standards — Universal coding standards
- frontend-patterns — React/Next.js patterns
- backend-patterns — API design, database, caching
- e2e-testing — Playwright E2E tests
- eval-harness — Eval-driven development
- strategic-compact — Context management
- api-design — REST API design patterns
- verification-loop — Build, test, lint, typecheck, security

## Java + Python Defaults

When the repository contains Java or Python code, prioritize these workflows:

### Java (Maven / Gradle)

1. Detect build tool from `pom.xml` or `build.gradle*`.
2. Before implementation, write/update tests first (TDD).
3. Run:
   - Maven: `mvn -q test`
   - Gradle: `./gradlew test`
4. For build issues:
   - Maven: `mvn -q -DskipTests compile`
   - Gradle: `./gradlew compileJava`
5. Security/dependency checks:
   - Maven: `mvn -q org.owasp:dependency-check-maven:check` (if plugin available)
   - Gradle: `./gradlew dependencyCheckAnalyze` (if plugin available)

### Python (pytest)

1. Detect environment from `pyproject.toml`, `requirements*.txt`, or `poetry.lock`.
2. Before implementation, write/update tests first (TDD).
3. Run:
   - `pytest -q`
   - `ruff check .` (if configured)
   - `mypy .` (if configured)
4. Security/dependency checks:
   - `pip-audit` (if available)

## MCP Servers

Configure in `~/.codex/config.toml` under `[mcp_servers]`. See `.codex/config.toml` for reference configuration with GitHub, Context7, Memory, and Sequential Thinking servers.

## Key Differences from Claude Code

| Feature | Claude Code | Codex (CLI/GUI) |
|---------|------------|------------------|
| Hooks | 8+ event types | Not yet supported |
| Context file | CLAUDE.md + AGENTS.md | AGENTS.md only |
| Skills | Skills loaded via plugin | `.agents/skills/` directory |
| Commands | `/slash` commands | Instruction-based |
| Agents | Subagent Task tool | Single agent model |
| Security | Hook-based enforcement | Instruction + sandbox |
| MCP | Full support | Command-based only |

## Security Without Hooks

Since Codex lacks hooks, security enforcement is instruction-based:
1. Always validate inputs at system boundaries
2. Never hardcode secrets — use environment variables
3. Run `npm audit` / `pip audit` before committing
4. Review `git diff` before every push
5. Use `sandbox_mode = "workspace-write"` in config
