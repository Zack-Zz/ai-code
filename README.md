**Language:** [English](README.md) | [简体中文](README.zh-CN.md)

# ai-code

[![Stars](https://img.shields.io/github/stars/Zack-Zz/ai-code?style=flat)](https://github.com/Zack-Zz/ai-code/stargazers)
[![Forks](https://img.shields.io/github/forks/Zack-Zz/ai-code?style=flat)](https://github.com/Zack-Zz/ai-code/network/members)
[![Contributors](https://img.shields.io/github/contributors/Zack-Zz/ai-code?style=flat)](https://github.com/Zack-Zz/ai-code/graphs/contributors)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
![Shell](https://img.shields.io/badge/-Shell-4EAA25?logo=gnu-bash&logoColor=white)
![TypeScript](https://img.shields.io/badge/-TypeScript-3178C6?logo=typescript&logoColor=white)
![Python](https://img.shields.io/badge/-Python-3776AB?logo=python&logoColor=white)
![Go](https://img.shields.io/badge/-Go-00ADD8?logo=go&logoColor=white)
![Java](https://img.shields.io/badge/-Java-ED8B00?logo=openjdk&logoColor=white)
![Markdown](https://img.shields.io/badge/-Markdown-000000?logo=markdown&logoColor=white)

<div align="center">

**🌐 Language / 语言**

[**English**](README.md) | [简体中文](README.zh-CN.md)

</div>

---

**A practical multi-assistant configuration toolkit for ChatGPT, Codex, Claude, and other mainstream AI coding tools.**

Production-ready agents, skills, hooks, commands, rules, and MCP configurations evolved over 10+ months of intensive daily use building real products.

---

## Project Goal

`ai-code` is a fork-oriented toolkit designed for cross-assistant workflows instead of a single-vendor setup.

- ChatGPT / Codex: project-level `AGENTS.md`, `.codex/config.toml`, `.codex/codex.md`
- Claude Code: plugin/rules/hooks compatible assets
- Cursor/OpenCode: compatible configs and command sets
- Polyglot workflows: TypeScript/JavaScript, Java, Python, Go, and Rust

---

## Usage Overview

- Choose your assistant stack first: Codex/ChatGPT, Claude Code, or Cursor/OpenCode.
- Keep project-level instructions in `AGENTS.md`, and add language-specific workflow notes when needed.
- Start from `.codex/codex.md` for a polyglot Codex workflow and run tests before implementation.
- Use only the directories you need (`agents/`, `skills/`, `rules/`, `commands/`) to keep setup minimal.

### Component Compatibility Matrix (Claude / Codex / Kiro)

Status legend:
- Native: directly loaded/executed by the assistant
- Reference: usable as guidance, but not natively executed
- No: not consumed by that assistant

| Component | Primary purpose | Claude Code | Codex | Kiro |
|-----------|-----------------|-------------|-------|------|
| `commands/` | Slash command workflows (`/tdd`, `/plan`, etc.) | Native | No | No |
| `rules/` | Always-follow coding/security/testing rules | Native | No | No (use `.kiro/steering/`) |
| `skills/*/SKILL.md` | Reusable workflow knowledge | Native | Native (via project `.agents/skills/`) | Reference |
| `skills/*/agents/openai.yaml` | Skill metadata for Codex auto-recognition | No | Native | No |
| `agents/` | Specialized subagent role instructions | Native | Reference | Reference |
| `hooks/` + `scripts/hooks/` | Event-triggered automation | Native | No (Codex CLI lacks hooks) | No (uses `.kiro/hooks/hooks.json`) |
| `.codex/*` | Codex config and session guide | Reference | Native | Reference |
| `.kiro/steering/*` + `.kiro/hooks/*` + `.kiro/settings/mcp.json` | Kiro steering/hook/MCP integration | Reference | Reference | Native |
| `mcp-configs/` | MCP template set (mainly for Claude-style config) | Native/Reference | Reference (Codex uses `.codex/config.toml`) | Reference (Kiro uses `.kiro/settings/mcp.json`) |

### Bootstrap Mapping (`scripts/bootstrap-project.sh`)

| `--tool` mode | Copied for this assistant |
|---------------|---------------------------|
| `claude` | `CLAUDE.md`, `agents/`, `commands/`, `rules/`, `hooks/`, hook runtime scripts |
| `codex` | `.codex/codex.md`, `.codex/AGENTS.md`, optional `.codex/config.toml`, selected skills |
| `kiro` | `.kiro/steering/*`, `.kiro/hooks/hooks.json`, `.kiro/settings/mcp.json`, selected skills (reference use) |
| `both` | Codex + Kiro assets |
| `all` | Codex + Kiro + Claude assets |

When `--langs` includes `go`, bootstrap also copies tool-agnostic Go enforcement templates:
`Makefile`, `.golangci.yml`, and `.github/workflows/go-ci.yml` (without affecting non-Go languages).

### Unified Runtime Config (Codex + Claude)

For hook/session scripts, you can use one set of environment variables across assistants:

```bash
export AI_CODE_TOOL=codex      # codex | claude
export AI_CODE_HOME=/path/to/assistant-home
```

- `AI_CODE_HOME` has highest priority.
- If `AI_CODE_HOME` is unset and `AI_CODE_TOOL=codex`, default path is `~/.codex`.
- Otherwise default path is `~/.claude`.
- Hook scripts also support `--tool` and `--home` flags for one-off runs.

---

## 🚀 Quick Start

### One-Command Bootstrap (New Project)

```bash
scripts/bootstrap-project.sh --target /path/to/your-project --langs js
scripts/bootstrap-project.sh --target /path/to/your-project --langs java,python,go
# Optional tool mode: --tool auto|codex|kiro|claude|both|all
# both = codex + kiro, all = codex + kiro + claude
# Optional project-level codex config copy:
# scripts/bootstrap-project.sh --target /path/to/your-project --langs js --tool codex --copy-codex-config
# Re-sync latest ai-code updates using target manifest:
# scripts/sync-project.sh --target /path/to/your-project
# Sync global Codex config (recommended):
# scripts/sync-codex-global-config.sh
```

### Option 1: Codex / ChatGPT Stack (Recommended)

```bash
git clone https://github.com/Zack-Zz/ai-code.git
cd ai-code
scripts/sync-codex-global-config.sh
```

Then open the repo in Codex GUI and start with:
`Read /.codex/codex.md and follow the polyglot workflow defaults.`

### Option 2: Claude Code Stack

```bash
git clone https://github.com/Zack-Zz/ai-code.git
cd ai-code
./install.sh typescript python golang
# or bootstrap a target project directly:
# scripts/bootstrap-project.sh --target /path/to/project --langs java --tool claude
```

### Option 3: Cursor / OpenCode Stack

- Cursor: use `.cursor/` with `./install.sh --target cursor ...`
- OpenCode: run from repo root and load `.opencode/` config

### Option 4: Kiro GUI Stack

```bash
git clone https://github.com/Zack-Zz/ai-code.git
cd ai-code

# Bootstrap a new project with Kiro support
scripts/bootstrap-project.sh --target /path/to/your-project --langs java,python --tool kiro

# Or use this repo directly
# Open the folder in Kiro - steering files load automatically
```

**What gets installed:**
- 6 steering files in `.kiro/steering/` (core principles, security, TDD, coding standards)
- Hooks configuration in `.kiro/hooks/hooks.json` (auto-format, security checks)
- MCP template in `.kiro/settings/mcp.json` (filesystem, GitHub, PostgreSQL, search)

**Next steps:**
1. Open project in Kiro - steering files load automatically
2. Configure MCP servers in `.kiro/settings/mcp.json` (replace `YOUR_*_HERE` with API keys)
3. Review hooks in `.kiro/hooks/hooks.json` (fileEdited, promptSubmit, agentStop)

See [`.kiro/README.md`](.kiro/README.md) for detailed Kiro configuration guide.

---

## 🌐 Cross-Platform Support

This toolkit fully supports **Windows, macOS, and Linux**. All hooks and scripts have been rewritten in Node.js for maximum compatibility.

### Package Manager Detection

For Claude Code workflows, package-manager detection follows this priority:

1. **Environment variable**: `AI_CODE_PACKAGE_MANAGER` (`CLAUDE_PACKAGE_MANAGER` also supported for backward compatibility)
2. **Project config**: `.claude/package-manager.json`
3. **package.json**: `packageManager` field
4. **Lock file**: Detection from package-lock.json, yarn.lock, pnpm-lock.yaml, or bun.lockb
5. **Global config**: `$AI_CODE_HOME/package-manager.json`
6. **Fallback**: `npm`

To set your preferred package manager:

```bash
# Via environment variable
export AI_CODE_PACKAGE_MANAGER=pnpm

# Via global config
node scripts/setup-package-manager.js --global pnpm

# Via project config
node scripts/setup-package-manager.js --project bun

# Detect current setting
node scripts/setup-package-manager.js --detect
```

Or use the `/setup-pm` command in Claude Code.

---

## 📦 What's Inside

This repo is a **multi-assistant toolkit** that includes Claude Code plugin assets, Codex configs, and Kiro steering files.

```
ai-code/
|-- .claude-plugin/   # Plugin and marketplace manifests
|   |-- plugin.json         # Plugin metadata and component paths
|   |-- marketplace.json    # Marketplace catalog for /plugin marketplace add
|
|-- agents/           # Specialized subagents for delegation
|   |-- planner.md           # Feature implementation planning
|   |-- architect.md         # System design decisions
|   |-- tdd-guide.md         # Test-driven development
|   |-- code-reviewer.md     # Quality and security review
|   |-- security-reviewer.md # Vulnerability analysis
|   |-- build-error-resolver.md
|   |-- e2e-runner.md        # Playwright E2E testing
|   |-- refactor-cleaner.md  # Dead code cleanup
|   |-- doc-updater.md       # Documentation sync
|   |-- go-reviewer.md       # Go code review
|   |-- go-build-resolver.md # Go build error resolution
|   |-- python-reviewer.md   # Python code review (NEW)
|   |-- database-reviewer.md # Database/Supabase review (NEW)
|
|-- skills/           # Workflow definitions and domain knowledge
|   |-- coding-standards/           # Language best practices
|   |-- clickhouse-io/              # ClickHouse analytics, queries, data engineering
|   |-- backend-patterns/           # API, database, caching patterns
|   |-- frontend-patterns/          # React, Next.js patterns
|   |-- continuous-learning/        # Auto-extract patterns from sessions (Usage Guide)
|   |-- continuous-learning-v2/     # Instinct-based learning with confidence scoring
|   |-- iterative-retrieval/        # Progressive context refinement for subagents
|   |-- strategic-compact/          # Manual compaction suggestions (Usage Guide)
|   |-- tdd-workflow/               # TDD methodology
|   |-- security-review/            # Security checklist
|   |-- eval-harness/               # Verification loop evaluation (Usage Guide)
|   |-- verification-loop/          # Continuous verification (Usage Guide)
|   |-- golang-patterns/            # Go idioms and best practices
|   |-- golang-testing/             # Go testing patterns, TDD, benchmarks
|   |-- cpp-coding-standards/         # C++ coding standards from C++ Core Guidelines (NEW)
|   |-- cpp-testing/                # C++ testing with GoogleTest, CMake/CTest (NEW)
|   |-- django-patterns/            # Django patterns, models, views (NEW)
|   |-- django-security/            # Django security best practices (NEW)
|   |-- django-tdd/                 # Django TDD workflow (NEW)
|   |-- django-verification/        # Django verification loops (NEW)
|   |-- python-patterns/            # Python idioms and best practices (NEW)
|   |-- python-testing/             # Python testing with pytest (NEW)
|   |-- springboot-patterns/        # Java Spring Boot patterns (NEW)
|   |-- springboot-security/        # Spring Boot security (NEW)
|   |-- springboot-tdd/             # Spring Boot TDD (NEW)
|   |-- springboot-verification/    # Spring Boot verification (NEW)
|   |-- configure-ai-code/              # Interactive installation wizard (NEW)
|   |-- security-scan/              # AgentShield security auditor integration (NEW)
|   |-- java-coding-standards/     # Java coding standards (NEW)
|   |-- jpa-patterns/              # JPA/Hibernate patterns (NEW)
|   |-- postgres-patterns/         # PostgreSQL optimization patterns (NEW)
|   |-- nutrient-document-processing/ # Document processing with Nutrient API (NEW)
|   |-- project-guidelines-example/   # Template for project-specific skills
|   |-- database-migrations/         # Migration patterns (Prisma, Drizzle, Django, Go) (NEW)
|   |-- api-design/                  # REST API design, pagination, error responses (NEW)
|   |-- deployment-patterns/         # CI/CD, Docker, health checks, rollbacks (NEW)
|   |-- docker-patterns/            # Docker Compose, networking, volumes, container security (NEW)
|   |-- e2e-testing/                 # Playwright E2E patterns and Page Object Model (NEW)
|   |-- content-hash-cache-pattern/  # SHA-256 content hash caching for file processing (NEW)
|   |-- cost-aware-llm-pipeline/     # LLM cost optimization, model routing, budget tracking (NEW)
|   |-- regex-vs-llm-structured-text/ # Decision framework: regex vs LLM for text parsing (NEW)
|   |-- swift-actor-persistence/     # Thread-safe Swift data persistence with actors (NEW)
|   |-- swift-protocol-di-testing/   # Protocol-based DI for testable Swift code (NEW)
|   |-- search-first/               # Research-before-coding workflow (NEW)
|   |-- skill-stocktake/            # Audit skills and commands for quality (NEW)
|   |-- liquid-glass-design/         # iOS 26 Liquid Glass design system (NEW)
|   |-- foundation-models-on-device/ # Apple on-device LLM with FoundationModels (NEW)
|   |-- swift-concurrency-6-2/       # Swift 6.2 Approachable Concurrency (NEW)
|
|-- commands/         # Slash commands for quick execution
|   |-- tdd.md              # /tdd - Test-driven development
|   |-- plan.md             # /plan - Implementation planning
|   |-- e2e.md              # /e2e - E2E test generation
|   |-- code-review.md      # /code-review - Quality review
|   |-- build-fix.md        # /build-fix - Fix build errors
|   |-- refactor-clean.md   # /refactor-clean - Dead code removal
|   |-- learn.md            # /learn - Extract patterns mid-session (Usage Guide)
|   |-- learn-eval.md       # /learn-eval - Extract, evaluate, and save patterns (NEW)
|   |-- checkpoint.md       # /checkpoint - Save verification state (Usage Guide)
|   |-- verify.md           # /verify - Run verification loop (Usage Guide)
|   |-- setup-pm.md         # /setup-pm - Configure package manager
|   |-- go-review.md        # /go-review - Go code review (NEW)
|   |-- go-test.md          # /go-test - Go TDD workflow (NEW)
|   |-- go-build.md         # /go-build - Fix Go build errors (NEW)
|   |-- skill-create.md     # /skill-create - Generate skills from git history (NEW)
|   |-- instinct-status.md  # /instinct-status - View learned instincts (NEW)
|   |-- instinct-import.md  # /instinct-import - Import instincts (NEW)
|   |-- instinct-export.md  # /instinct-export - Export instincts (NEW)
|   |-- evolve.md           # /evolve - Cluster instincts into skills
|   |-- pm2.md              # /pm2 - PM2 service lifecycle management (NEW)
|   |-- multi-plan.md       # /multi-plan - Multi-agent task decomposition (NEW)
|   |-- multi-execute.md    # /multi-execute - Orchestrated multi-agent workflows (NEW)
|   |-- multi-backend.md    # /multi-backend - Backend multi-service orchestration (NEW)
|   |-- multi-frontend.md   # /multi-frontend - Frontend multi-service orchestration (NEW)
|   |-- multi-workflow.md   # /multi-workflow - General multi-service workflows (NEW)
|   |-- orchestrate.md      # /orchestrate - Multi-agent coordination
|   |-- sessions.md         # /sessions - Session history management
|   |-- eval.md             # /eval - Evaluate against criteria
|   |-- test-coverage.md    # /test-coverage - Test coverage analysis
|   |-- update-docs.md      # /update-docs - Update documentation
|   |-- update-codemaps.md  # /update-codemaps - Update codemaps
|   |-- python-review.md    # /python-review - Python code review (NEW)
|
|-- rules/            # Always-follow guidelines (copy to $AI_CODE_HOME/rules/)
|   |-- README.md            # Structure overview and installation guide
|   |-- common/              # Language-agnostic principles
|   |   |-- coding-style.md    # Immutability, file organization
|   |   |-- git-workflow.md    # Commit format, PR process
|   |   |-- testing.md         # TDD, 80% coverage requirement
|   |   |-- performance.md     # Model selection, context management
|   |   |-- patterns.md        # Design patterns, skeleton projects
|   |   |-- hooks.md           # Hook architecture, TodoWrite
|   |   |-- agents.md          # When to delegate to subagents
|   |   |-- security.md        # Mandatory security checks
|   |-- typescript/          # TypeScript/JavaScript specific
|   |-- python/              # Python specific
|   |-- golang/              # Go specific
|
|-- hooks/            # Trigger-based automations
|   |-- README.md                 # Hook documentation, recipes, and customization guide
|   |-- hooks.json                # All hooks config (PreToolUse, PostToolUse, Stop, etc.)
|   |-- memory-persistence/       # Session lifecycle hooks (Usage Guide)
|   |-- strategic-compact/        # Compaction suggestions (Usage Guide)
|
|-- scripts/          # Cross-platform Node.js scripts (NEW)
|   |-- lib/                     # Shared utilities
|   |   |-- utils.js             # Cross-platform file/path/system utilities
|   |   |-- package-manager.js   # Package manager detection and selection
|   |-- hooks/                   # Hook implementations
|   |   |-- session-start.js     # Load context on session start
|   |   |-- session-end.js       # Save state on session end
|   |   |-- pre-compact.js       # Pre-compaction state saving
|   |   |-- suggest-compact.js   # Strategic compaction suggestions
|   |   |-- evaluate-session.js  # Extract patterns from sessions
|   |-- setup-package-manager.js # Interactive PM setup
|
|-- tests/            # Test suite (NEW)
|   |-- lib/                     # Library tests
|   |-- hooks/                   # Hook tests
|   |-- run-all.js               # Run all tests
|
|-- contexts/         # Dynamic system prompt injection contexts (Usage Guide)
|   |-- dev.md              # Development mode context
|   |-- review.md           # Code review mode context
|   |-- research.md         # Research/exploration mode context
|
|-- examples/         # Example configurations and sessions
|   |-- CLAUDE.md             # Example project-level config
|   |-- user-CLAUDE.md        # Example user-level config
|   |-- saas-nextjs-CLAUDE.md   # Real-world SaaS (Next.js + Supabase + Stripe)
|   |-- go-microservice-CLAUDE.md # Real-world Go microservice (gRPC + PostgreSQL)
|   |-- django-api-CLAUDE.md      # Real-world Django REST API (DRF + Celery)
|   |-- rust-api-CLAUDE.md        # Real-world Rust API (Axum + SQLx + PostgreSQL) (NEW)
|
|-- mcp-configs/      # MCP server configurations
|   |-- mcp-servers.json    # GitHub, Supabase, Vercel, Railway, etc.
|
|-- marketplace.json  # Self-hosted marketplace config (for /plugin marketplace add)
```

---

## 🛠️ Ecosystem Tools

### Skill Creator

Two ways to generate Claude Code skills from your repository:

#### Option A: Local Analysis (Built-in)

Use the `/skill-create` command for local analysis without external services:

```bash
/skill-create                    # Analyze current repo
/skill-create --instincts        # Also generate instincts for continuous-learning
```

This analyzes your git history locally and generates SKILL.md files.

#### Option B: GitHub App (Advanced)

For advanced features (10k+ commits, auto-PRs, team sharing):

[Install GitHub App](https://github.com/apps/skill-creator) | [github.com/Zack-Zz/ai-code](https://github.com/Zack-Zz/ai-code)

```bash
# Comment on any issue:
/skill-creator analyze

# Or auto-triggers on push to default branch
```

Both options create:
- **SKILL.md files** - Ready-to-use skills for Claude Code
- **Instinct collections** - For continuous-learning-v2
- **Pattern extraction** - Learns from your commit history

### AgentShield — Security Auditor

> Security scanning companion tool for Claude Code workflows.

Scan your Claude Code configuration for vulnerabilities, misconfigurations, and injection risks.

```bash
# Quick scan (no install needed)
npx ecc-agentshield scan

# Auto-fix safe issues
npx ecc-agentshield scan --fix

# Deep analysis with three Opus 4.6 agents
npx ecc-agentshield scan --opus --stream

# Generate secure config from scratch
npx ecc-agentshield init
```

**What it scans:** CLAUDE.md, settings.json, MCP configs, hooks, agent definitions, and skills across 5 categories — secrets detection (14 patterns), permission auditing, hook injection analysis, MCP server risk profiling, and agent config review.

**The `--opus` flag** runs three Claude Opus 4.6 agents in a red-team/blue-team/auditor pipeline. The attacker finds exploit chains, the defender evaluates protections, and the auditor synthesizes both into a prioritized risk assessment. Adversarial reasoning, not just pattern matching.

**Output formats:** Terminal (color-graded A-F), JSON (CI pipelines), Markdown, HTML. Exit code 2 on critical findings for build gates.

Use `/security-scan` in Claude Code to run it, or add to CI with the [GitHub Action](https://github.com/affaan-m/agentshield).

[GitHub](https://github.com/affaan-m/agentshield) | [npm](https://www.npmjs.com/package/ecc-agentshield)

### 🧠 Continuous Learning v2

The instinct-based learning system automatically learns your patterns:

```bash
/instinct-status        # Show learned instincts with confidence
/instinct-import <file> # Import instincts from others
/instinct-export        # Export your instincts for sharing
/evolve                 # Cluster related instincts into skills
```

See `skills/continuous-learning-v2/` for full documentation.

---

## 📋 Requirements

### Claude Code CLI Version

**Minimum version: v2.1.0 or later**

This plugin requires Claude Code CLI v2.1.0+ due to changes in how the plugin system handles hooks.

Check your version:
```bash
claude --version
```

### Important: Hooks Auto-Loading Behavior

> ⚠️ **For Contributors:** Do NOT add a `"hooks"` field to `.claude-plugin/plugin.json`. This is enforced by a regression test.

Claude Code v2.1+ **automatically loads** `hooks/hooks.json` from any installed plugin by convention. Explicitly declaring it in `plugin.json` causes a duplicate detection error:

```
Duplicate hooks file detected: ./hooks/hooks.json resolves to already-loaded file
```

**History:** This has caused repeated fix/revert cycles in this repo ([#29](https://github.com/Zack-Zz/ai-code/issues/29), [#52](https://github.com/Zack-Zz/ai-code/issues/52), [#103](https://github.com/Zack-Zz/ai-code/issues/103)). The behavior changed between Claude Code versions, leading to confusion. We now have a regression test to prevent this from being reintroduced.

---

## 📥 Installation

### Option 1: Install as Plugin (Recommended)

The easiest way to use this repo - install as a Claude Code plugin:

```bash
# Add this repo as a marketplace
/plugin marketplace add Zack-Zz/ai-code

# Install the plugin
/plugin install ai-code@ai-code
```

Or add directly to your `$AI_CODE_HOME/settings.json`:

```json
{
  "extraKnownMarketplaces": {
    "ai-code": {
      "source": {
        "source": "github",
        "repo": "Zack-Zz/ai-code"
      }
    }
  },
  "enabledPlugins": {
    "ai-code@ai-code": true
  }
}
```

This gives you instant access to all commands, agents, skills, and hooks.

> **Note:** The Claude Code plugin system does not support distributing `rules` via plugins ([upstream limitation](https://code.claude.com/docs/en/plugins-reference)). You need to install rules manually:
>
> ```bash
> # Clone the repo first
> git clone https://github.com/Zack-Zz/ai-code.git
>
> # Option A: User-level rules (applies to all projects)
> mkdir -p $AI_CODE_HOME/rules
> cp -r ai-code/rules/common/* $AI_CODE_HOME/rules/
> cp -r ai-code/rules/typescript/* $AI_CODE_HOME/rules/   # pick your stack
> cp -r ai-code/rules/python/* $AI_CODE_HOME/rules/
> cp -r ai-code/rules/golang/* $AI_CODE_HOME/rules/
>
> # Option B: Project-level rules (applies to current project only)
> mkdir -p .claude/rules
> cp -r ai-code/rules/common/* .claude/rules/
> cp -r ai-code/rules/typescript/* .claude/rules/     # pick your stack
> ```

---

### 🔧 Option 2: Manual Installation

If you prefer manual control over what's installed:

```bash
# Clone the repo
git clone https://github.com/Zack-Zz/ai-code.git

# Copy agents to your Claude config
cp ai-code/agents/*.md $AI_CODE_HOME/agents/

# Copy rules (common + language-specific)
cp -r ai-code/rules/common/* $AI_CODE_HOME/rules/
cp -r ai-code/rules/typescript/* $AI_CODE_HOME/rules/   # pick your stack
cp -r ai-code/rules/python/* $AI_CODE_HOME/rules/
cp -r ai-code/rules/golang/* $AI_CODE_HOME/rules/

# Copy commands
cp ai-code/commands/*.md $AI_CODE_HOME/commands/

# Copy skills
cp -r ai-code/skills/* $AI_CODE_HOME/skills/
```

#### Add hooks to settings.json

Copy the hooks from `hooks/hooks.json` to your `$AI_CODE_HOME/settings.json`.

#### Configure MCPs

Copy desired MCP servers from `mcp-configs/mcp-servers.json` to your `$AI_CODE_HOME/config.json`.

**Important:** Replace `YOUR_*_HERE` placeholders with your actual API keys.

---

## 🎯 Key Concepts

### Agents

Subagents handle delegated tasks with limited scope. Example:

```markdown
---
name: code-reviewer
description: Reviews code for quality, security, and maintainability
tools: ["Read", "Grep", "Glob", "Bash"]
model: opus
---

You are a senior code reviewer...
```

### Skills

Skills are workflow definitions invoked by commands or agents:

```markdown
# TDD Workflow

1. Define interfaces first
2. Write failing tests (RED)
3. Implement minimal code (GREEN)
4. Refactor (IMPROVE)
5. Verify 80%+ coverage
```

### Hooks

Hooks fire on tool events. Example - warn about console.log:

```json
{
  "matcher": "tool == \"Edit\" && tool_input.file_path matches \"\\\\.(ts|tsx|js|jsx)$\"",
  "hooks": [{
    "type": "command",
    "command": "#!/bin/bash\ngrep -n 'console\\.log' \"$file_path\" && echo '[Hook] Remove console.log' >&2"
  }]
}
```

### Rules

Rules are always-follow guidelines, organized into `common/` (language-agnostic) + language-specific directories:

```
rules/
  common/          # Universal principles (always install)
  typescript/      # TS/JS specific patterns and tools
  python/          # Python specific patterns and tools
  golang/          # Go specific patterns and tools
```

See [`rules/README.md`](rules/README.md) for installation and structure details.

---

## 🗺️ Which Agent Should I Use?

Not sure where to start? Use this quick reference:

| I want to... | Use this command | Agent used |
|--------------|-----------------|------------|
| Plan a new feature | `/ai-code:plan "Add auth"` | planner |
| Design system architecture | `/ai-code:plan` + architect agent | architect |
| Write code with tests first | `/tdd` | tdd-guide |
| Review code I just wrote | `/code-review` | code-reviewer |
| Fix a failing build | `/build-fix` | build-error-resolver |
| Run end-to-end tests | `/e2e` | e2e-runner |
| Find security vulnerabilities | `/security-scan` | security-reviewer |
| Remove dead code | `/refactor-clean` | refactor-cleaner |
| Update documentation | `/update-docs` | doc-updater |
| Review Go code | `/go-review` | go-reviewer |
| Review Python code | `/python-review` | python-reviewer |
| Audit database queries | *(auto-delegated)* | database-reviewer |

### Common Workflows

**Starting a new feature:**
```
/ai-code:plan "Add user authentication with OAuth"
                                              → planner creates implementation blueprint
/tdd                                          → tdd-guide enforces write-tests-first
/code-review                                  → code-reviewer checks your work
```

**Fixing a bug:**
```
/tdd                                          → tdd-guide: write a failing test that reproduces it
                                              → implement the fix, verify test passes
/code-review                                  → code-reviewer: catch regressions
```

**Preparing for production:**
```
/security-scan                                → security-reviewer: OWASP Top 10 audit
/e2e                                          → e2e-runner: critical user flow tests
/test-coverage                                → verify 80%+ coverage
```

---

## ❓ FAQ

<details>
<summary><b>How do I check which agents/commands are installed?</b></summary>

```bash
/plugin list ai-code@ai-code
```

This shows all available agents, commands, and skills from the plugin.
</details>

<details>
<summary><b>My hooks aren't working / I see "Duplicate hooks file" errors</b></summary>

This is the most common issue. **Do NOT add a `"hooks"` field to `.claude-plugin/plugin.json`.** Claude Code v2.1+ automatically loads `hooks/hooks.json` from installed plugins. Explicitly declaring it causes duplicate detection errors. See [#29](https://github.com/Zack-Zz/ai-code/issues/29), [#52](https://github.com/Zack-Zz/ai-code/issues/52), [#103](https://github.com/Zack-Zz/ai-code/issues/103).
</details>

<details>
<summary><b>My context window is shrinking / Claude is running out of context</b></summary>

Too many MCP servers eat your context. Each MCP tool description consumes tokens from your 200k window, potentially reducing it to ~70k.

**Fix:** Disable unused MCPs per project:
```json
// In your project's .claude/settings.json
{
  "disabledMcpServers": ["supabase", "railway", "vercel"]
}
```

Keep under 10 MCPs enabled and under 80 tools active.
</details>

<details>
<summary><b>Can I use only some components (e.g., just agents)?</b></summary>

Yes. Use Option 2 (manual installation) and copy only what you need:

```bash
# Just agents
cp ai-code/agents/*.md $AI_CODE_HOME/agents/

# Just rules
cp -r ai-code/rules/common/* $AI_CODE_HOME/rules/
```

Each component is fully independent.
</details>

<details>
<summary><b>Does this work with Cursor / OpenCode / Codex?</b></summary>

Yes. ai-code is cross-platform:
- **Cursor**: Pre-translated configs in `.cursor/`. See [Cursor IDE Support](#cursor-ide-support).
- **OpenCode**: Full plugin support in `.opencode/`. See [OpenCode Support](#-opencode-support).
- **Codex**: First-class support with adapter drift guards and SessionStart fallback. See PR [#257](https://github.com/Zack-Zz/ai-code/pull/257).
- **Claude Code**: Native — this is the primary target.
</details>

<details>
<summary><b>How do I contribute a new skill or agent?</b></summary>

See [CONTRIBUTING.md](CONTRIBUTING.md). The short version:
1. Fork the repo
2. Create your skill in `skills/your-skill-name/SKILL.md` (with YAML frontmatter)
3. Or create an agent in `agents/your-agent.md`
4. Submit a PR with a clear description of what it does and when to use it
</details>

---

## 🧪 Running Tests

The plugin includes a comprehensive test suite:

```bash
# Run all tests
node tests/run-all.js

# Run individual test files
node tests/lib/utils.test.js
node tests/lib/package-manager.test.js
node tests/hooks/hooks.test.js
```

---

## 🤝 Contributing

**Contributions are welcome and encouraged.**

This repo is meant to be a community resource. If you have:
- Useful agents or skills
- Clever hooks
- Better MCP configurations
- Improved rules

Please contribute! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### Ideas for Contributions

- Language-specific skills (Rust, C#, Swift, Kotlin) — Go, Python, Java already included
- Framework-specific configs (Rails, Laravel, FastAPI, NestJS) — Django, Spring Boot already included
- DevOps agents (Kubernetes, Terraform, AWS, Docker)
- Testing strategies (different frameworks, visual regression)
- Domain-specific knowledge (ML, data engineering, mobile)

---

## Cursor IDE Support

ai-code provides **full Cursor IDE support** with hooks, rules, agents, skills, commands, and MCP configs adapted for Cursor's native format.

### Quick Start (Cursor)

```bash
# Install for your language(s)
./install.sh --target cursor typescript
./install.sh --target cursor python golang swift
```

### What's Included

| Component | Count | Details |
|-----------|-------|---------|
| Hook Events | 15 | sessionStart, beforeShellExecution, afterFileEdit, beforeMCPExecution, beforeSubmitPrompt, and 10 more |
| Hook Scripts | 16 | Thin Node.js scripts delegating to `scripts/hooks/` via shared adapter |
| Rules | 29 | 9 common (alwaysApply) + 20 language-specific (TypeScript, Python, Go, Swift) |
| Agents | Shared | Via AGENTS.md at root (read by Cursor natively) |
| Skills | Shared | Via AGENTS.md at root |
| Commands | Shared | `.cursor/commands/` if installed |
| MCP Config | Shared | `.cursor/mcp.json` if installed |

### Hook Architecture (DRY Adapter Pattern)

Cursor has **more hook events than Claude Code** (20 vs 8). The `.cursor/hooks/adapter.js` module transforms Cursor's stdin JSON to Claude Code's format, allowing existing `scripts/hooks/*.js` to be reused without duplication.

```
Cursor stdin JSON → adapter.js → transforms → scripts/hooks/*.js
                                              (shared with Claude Code)
```

Key hooks:
- **beforeShellExecution** — Blocks dev servers outside tmux (exit 2), git push review
- **afterFileEdit** — Auto-format + TypeScript check + console.log warning
- **beforeSubmitPrompt** — Detects secrets (sk-, ghp_, AKIA patterns) in prompts
- **beforeTabFileRead** — Blocks Tab from reading .env, .key, .pem files (exit 2)
- **beforeMCPExecution / afterMCPExecution** — MCP audit logging

### Rules Format

Cursor rules use YAML frontmatter with `description`, `globs`, and `alwaysApply`:

```yaml
---
description: "TypeScript coding style extending common rules"
globs: ["**/*.ts", "**/*.tsx", "**/*.js", "**/*.jsx"]
alwaysApply: false
---
```

---

## Kiro IDE Support

ai-code provides **comprehensive Kiro support** with steering files, hooks, and MCP configurations adapted for Kiro's native format.

### Quick Start (Kiro)

```bash
# Bootstrap a new project with Kiro support
scripts/bootstrap-project.sh --target /path/to/your-project --langs java,python --tool kiro

# Or use this repo directly in Kiro
# Open the folder in Kiro - steering files load automatically
```

### What's Included

| Component | Count | Details |
|-----------|-------|---------|
| Steering Files | 6 | Core principles, security, TDD, coding standards, multi-language workflow |
| Hooks | 4 | fileEdited (format, console warn), promptSubmit (security), agentStop (summary) |
| MCP Template | 4 servers | filesystem, GitHub, PostgreSQL, brave-search (disabled by default) |
| Agent Guidelines | 13 | Reference to specialized agent workflows (planner, tdd-guide, security-reviewer, etc.) |

### Steering Files

Kiro steering files provide context and guidelines automatically:

#### Always Included
- `ai-code-core.md` - Core behavior and quality principles
- `agents-overview.md` - Reference to 13 specialized agent guidelines
- `security-checklist.md` - Security requirements and common vulnerabilities
- `coding-standards.md` - Immutability, file organization, error handling

#### Conditionally Included (fileMatch)
- `tdd-workflow.md` - Loaded when working with test files (`*.test.*`, `*.spec.*`)
- `multi-language-workflow.md` - Loaded when working with source files (`*.java`, `*.py`, `*.go`, `*.ts`, etc.)

### Steering File Format

Kiro steering files use YAML frontmatter with `inclusion` setting:

```yaml
---
inclusion: always
---

# Your Steering Content

Guidelines here...
```

Or use `fileMatch` for conditional inclusion:

```yaml
---
inclusion: fileMatch
fileMatchPattern: ".*\\.tsx?$"
---

# TypeScript-Specific Guidelines

TypeScript guidelines here...
```

### Hooks Configuration

Hooks in `.kiro/hooks/hooks.json` provide event-based automations:

```json
{
  "id": "file-edited-format",
  "name": "Auto-format on file edit",
  "when": {
    "type": "fileEdited",
    "patterns": ["*.ts", "*.tsx", "*.js", "*.jsx"]
  },
  "then": {
    "type": "askAgent",
    "prompt": "Check if formatting is needed and apply the project's formatter."
  }
}
```

**Available Hook Events:**
- `fileEdited` - When a file is saved
- `fileCreated` - When a new file is created
- `fileDeleted` - When a file is deleted
- `promptSubmit` - When a message is sent to Kiro
- `agentStop` - When Kiro finishes processing
- `userTriggered` - Manual trigger by user

### MCP Configuration

MCP servers in `.kiro/settings/mcp.json` provide additional capabilities:

```json
{
  "mcpServers": {
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "YOUR_GITHUB_TOKEN_HERE"
      },
      "disabled": true
    }
  }
}
```

**Setup Steps:**
1. Replace `YOUR_*_HERE` placeholders with actual API keys
2. Set `disabled: false` for servers you want to enable
3. Adjust file paths and connection strings as needed

### Differences from Claude Code

| Feature | Claude Code | Kiro |
|---------|-------------|------|
| Guidelines | `rules/` directory | `steering/` directory |
| Inclusion | `alwaysApply` field | `inclusion: always` |
| File matching | Not supported | `inclusion: fileMatch` |
| Hooks | `hooks.json` in root | `.kiro/hooks/hooks.json` |
| MCP | `config.json` | `.kiro/settings/mcp.json` |
| Agents | Native delegation | Reference guidelines only |

### Agent Guidelines Reference

While Kiro doesn't have native agent delegation, you can reference agent guidelines:

- `agents/planner.md` - Implementation planning for complex features
- `agents/tdd-guide.md` - Test-driven development methodology
- `agents/code-reviewer.md` - Code quality and maintainability
- `agents/security-reviewer.md` - Vulnerability detection and security audits
- And 9 more specialized agents

See [`.kiro/README.md`](.kiro/README.md) for detailed configuration guide.

---

## Codex Support (CLI + GUI)

ai-code provides **first-class Codex support** with a reference configuration, Codex-specific AGENTS.md supplement, and a single-source skills catalog.

### Quick Start (Codex CLI)

```bash
# Copy the reference config to your home directory
scripts/sync-codex-global-config.sh

# Run Codex in the repo — AGENTS.md is auto-detected
codex
```

### Quick Start (Codex GUI, Polyglot)

```bash
# 1) Configure Codex once
scripts/sync-codex-global-config.sh

# 2) Open this repository in Codex GUI
# 3) Start your first prompt with:
#    "Read /.codex/codex.md and follow polyglot workflow defaults."
```

`.codex/codex.md` provides a practical polyglot operating guide for Codex GUI sessions in this repo.

### What's Included

| Component | Count | Details |
|-----------|-------|---------|
| Config | 1 | `.codex/config.toml` — model, permissions, MCP servers, persistent instructions |
| AGENTS.md | 2 | Root (universal) + `.codex/AGENTS.md` (Codex-specific supplement) |
| Session Guide | 1 | `.codex/codex.md` — Codex GUI startup guide with polyglot defaults |
| Skills | 50 | `skills/` — SKILL.md + agents/openai.yaml per skill |
| MCP Servers | 4 | GitHub, Context7, Memory, Sequential Thinking (command-based) |
| Profiles | 4 | `strict` (read-only), `polyglot` (recommended), `java-python` (compat), `yolo` (full auto-approve) |

### Skills

Skills are maintained in `skills/` and include Codex metadata (`agents/openai.yaml`):

| Skill | Description |
|-------|-------------|
| tdd-workflow | Test-driven development with 80%+ coverage |
| security-review | Comprehensive security checklist |
| coding-standards | Universal coding standards |
| frontend-patterns | React/Next.js patterns |
| backend-patterns | API design, database, caching |
| e2e-testing | Playwright E2E tests |
| eval-harness | Eval-driven development |
| strategic-compact | Context management |
| api-design | REST API design patterns |
| verification-loop | Build, test, lint, typecheck, security |

### Key Limitation

Codex CLI does **not yet support hooks** ([GitHub Issue #2109](https://github.com/openai/codex/issues/2109), 430+ upvotes). Security enforcement is instruction-based via `persistent_instructions` in config.toml and the sandbox permission system.

---

## 🔌 OpenCode Support

ai-code provides **full OpenCode support** including plugins and hooks.

### Quick Start

```bash
# Install OpenCode
npm install -g opencode

# Run in the repository root
opencode
```

The configuration is automatically detected from `.opencode/opencode.json`.

### Feature Parity

| Feature | Claude Code | OpenCode | Status |
|---------|-------------|----------|--------|
| Agents | ✅ 13 agents | ✅ 12 agents | **Claude Code leads** |
| Commands | ✅ 33 commands | ✅ 24 commands | **Claude Code leads** |
| Skills | ✅ 50+ skills | ✅ 37 skills | **Claude Code leads** |
| Hooks | ✅ 8 event types | ✅ 11 events | **OpenCode has more!** |
| Rules | ✅ 29 rules | ✅ 13 instructions | **Claude Code leads** |
| MCP Servers | ✅ 14 servers | ✅ Full | **Full parity** |
| Custom Tools | ✅ Via hooks | ✅ 6 native tools | **OpenCode is better** |

### Hook Support via Plugins

OpenCode's plugin system is MORE sophisticated than Claude Code with 20+ event types:

| Claude Code Hook | OpenCode Plugin Event |
|-----------------|----------------------|
| PreToolUse | `tool.execute.before` |
| PostToolUse | `tool.execute.after` |
| Stop | `session.idle` |
| SessionStart | `session.created` |
| SessionEnd | `session.deleted` |

**Additional OpenCode events**: `file.edited`, `file.watcher.updated`, `message.updated`, `lsp.client.diagnostics`, `tui.toast.show`, and more.

### Available Commands (32)

| Command | Description |
|---------|-------------|
| `/plan` | Create implementation plan |
| `/tdd` | Enforce TDD workflow |
| `/code-review` | Review code changes |
| `/build-fix` | Fix build errors |
| `/e2e` | Generate E2E tests |
| `/refactor-clean` | Remove dead code |
| `/orchestrate` | Multi-agent workflow |
| `/learn` | Extract patterns from session |
| `/checkpoint` | Save verification state |
| `/verify` | Run verification loop |
| `/eval` | Evaluate against criteria |
| `/update-docs` | Update documentation |
| `/update-codemaps` | Update codemaps |
| `/test-coverage` | Analyze coverage |
| `/go-review` | Go code review |
| `/go-test` | Go TDD workflow |
| `/go-build` | Fix Go build errors |
| `/python-review` | Python code review (PEP 8, type hints, security) |
| `/multi-plan` | Multi-model collaborative planning |
| `/multi-execute` | Multi-model collaborative execution |
| `/multi-backend` | Backend-focused multi-model workflow |
| `/multi-frontend` | Frontend-focused multi-model workflow |
| `/multi-workflow` | Full multi-model development workflow |
| `/pm2` | Auto-generate PM2 service commands |
| `/sessions` | Manage session history |
| `/skill-create` | Generate skills from git |
| `/instinct-status` | View learned instincts |
| `/instinct-import` | Import instincts |
| `/instinct-export` | Export instincts |
| `/evolve` | Cluster instincts into skills |
| `/learn-eval` | Extract and evaluate patterns before saving |
| `/setup-pm` | Configure package manager |

### Plugin Installation

**Option 1: Use directly**
```bash
cd ai-code
opencode
```

**Option 2: Install as npm package**
```bash
npm install ai-code-universal
```

Then add to your `opencode.json`:
```json
{
  "plugin": ["ai-code-universal"]
}
```

### Documentation

- **Migration Guide**: `.opencode/MIGRATION.md`
- **OpenCode Plugin README**: `.opencode/README.md`
- **Consolidated Rules**: `.opencode/instructions/INSTRUCTIONS.md`
- **LLM Documentation**: `llms.txt` (complete OpenCode docs for LLMs)

---

## Cross-Tool Feature Parity

ai-code is the **first plugin to maximize every major AI coding tool**. Here's how each harness compares:

| Feature | Claude Code | Cursor IDE | Codex CLI | OpenCode |
|---------|------------|------------|-----------|----------|
| **Agents** | 13 | Shared (AGENTS.md) | Shared (AGENTS.md) | 12 |
| **Commands** | 33 | Shared | Instruction-based | 24 |
| **Skills** | 50+ | Shared | 10 (native format) | 37 |
| **Hook Events** | 8 types | 15 types | None yet | 11 types |
| **Hook Scripts** | 9 scripts | 16 scripts (DRY adapter) | N/A | Plugin hooks |
| **Rules** | 29 (common + lang) | 29 (YAML frontmatter) | Instruction-based | 13 instructions |
| **Custom Tools** | Via hooks | Via hooks | N/A | 6 native tools |
| **MCP Servers** | 14 | Shared (mcp.json) | 4 (command-based) | Full |
| **Config Format** | settings.json | hooks.json + rules/ | config.toml | opencode.json |
| **Context File** | CLAUDE.md + AGENTS.md | AGENTS.md | AGENTS.md | AGENTS.md |
| **Secret Detection** | Hook-based | beforeSubmitPrompt hook | Sandbox-based | Hook-based |
| **Auto-Format** | PostToolUse hook | afterFileEdit hook | N/A | file.edited hook |
| **Version** | Plugin | Plugin | Reference config | 1.6.0 |

**Key architectural decisions:**
- **AGENTS.md** at root is the universal cross-tool file (read by all 4 tools)
- **DRY adapter pattern** lets Cursor reuse Claude Code's hook scripts without duplication
- **Skills format** (SKILL.md with YAML frontmatter) works across Claude Code, Codex, and OpenCode
- Codex's lack of hooks is compensated by `persistent_instructions` and sandbox permissions

---

## 📖 Background

This repository is maintained as a practical, fork-friendly configuration baseline.
Use it as a starting point and adapt components to your own projects.

---

## Token Optimization

Claude Code usage can be expensive if you don't manage token consumption. These settings significantly reduce costs without sacrificing quality.

### Recommended Settings

Add to `$AI_CODE_HOME/settings.json`:

```json
{
  "model": "sonnet",
  "env": {
    "MAX_THINKING_TOKENS": "10000",
    "AI_CODE_AUTOCOMPACT_PCT_OVERRIDE": "50"
  }
}
```

| Setting | Default | Recommended | Impact |
|---------|---------|-------------|--------|
| `model` | opus | **sonnet** | ~60% cost reduction; handles 80%+ of coding tasks |
| `MAX_THINKING_TOKENS` | 31,999 | **10,000** | ~70% reduction in hidden thinking cost per request |
| `AI_CODE_AUTOCOMPACT_PCT_OVERRIDE` | 95 | **50** | Compacts earlier — better quality in long sessions |

Switch to Opus only when you need deep architectural reasoning:
```
/model opus
```

### Daily Workflow Commands

| Command | When to Use |
|---------|-------------|
| `/model sonnet` | Default for most tasks |
| `/model opus` | Complex architecture, debugging, deep reasoning |
| `/clear` | Between unrelated tasks (free, instant reset) |
| `/compact` | At logical task breakpoints (research done, milestone complete) |
| `/cost` | Monitor token spending during session |

### Strategic Compaction

The `strategic-compact` skill (included in this plugin) suggests `/compact` at logical breakpoints instead of relying on auto-compaction at 95% context. See `skills/strategic-compact/SKILL.md` for the full decision guide.

**When to compact:**
- After research/exploration, before implementation
- After completing a milestone, before starting the next
- After debugging, before continuing feature work
- After a failed approach, before trying a new one

**When NOT to compact:**
- Mid-implementation (you'll lose variable names, file paths, partial state)

### Context Window Management

**Critical:** Don't enable all MCPs at once. Each MCP tool description consumes tokens from your 200k window, potentially reducing it to ~70k.

- Keep under 10 MCPs enabled per project
- Keep under 80 tools active
- Use `disabledMcpServers` in project config to disable unused ones

### Agent Teams Cost Warning

Agent Teams spawns multiple context windows. Each teammate consumes tokens independently. Only use for tasks where parallelism provides clear value (multi-module work, parallel reviews). For simple sequential tasks, subagents are more token-efficient.

---

## ⚠️ Important Notes

### Token Optimization

Hitting daily limits? See the **[Token Optimization Guide](docs/token-optimization.md)** for recommended settings and workflow tips.

Quick wins:

```json
// $AI_CODE_HOME/settings.json
{
  "model": "sonnet",
  "env": {
    "MAX_THINKING_TOKENS": "10000",
    "AI_CODE_AUTOCOMPACT_PCT_OVERRIDE": "50",
    "AI_CODE_SUBAGENT_MODEL": "haiku"
  }
}
```

Use `/clear` between unrelated tasks, `/compact` at logical breakpoints, and `/cost` to monitor spending.

### Customization

These configs work for my workflow. You should:
1. Start with what resonates
2. Modify for your stack
3. Remove what you don't use
4. Add your own patterns

---

## 🔗 Links

- **Local Usage Guide:** [docs/USAGE.md](docs/USAGE.md)
- **Fork Repository:** [Zack-Zz/ai-code](https://github.com/Zack-Zz/ai-code)
- **Skills Directory:** awesome-agent-skills (community-maintained directory of agent skills)

---

## 📄 License

MIT - Use freely, modify as needed, contribute back if you can.

---

**Use what fits your workflow, and keep iterating based on your project needs.**
