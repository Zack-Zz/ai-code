---
inclusion: always
---

# Agents Overview for Kiro

This workspace includes 13 specialized agents for different development tasks. While Kiro doesn't have a native agent delegation system like Claude Code, you can reference these agent guidelines when working on specific tasks.

## Available Agent Guidelines

### Planning & Architecture
- **planner** - Implementation planning for complex features
- **architect** - System design and scalability decisions

### Development & Testing
- **tdd-guide** - Test-driven development methodology
- **code-reviewer** - Code quality and maintainability checks
- **security-reviewer** - Vulnerability detection and security audits

### Build & Errors
- **build-error-resolver** - Fix build and type errors
- **go-build-resolver** - Go-specific build error resolution

### Testing
- **e2e-runner** - End-to-end Playwright testing

### Maintenance
- **refactor-cleaner** - Dead code cleanup
- **doc-updater** - Documentation synchronization

### Language-Specific
- **go-reviewer** - Go code review
- **python-reviewer** - Python code review
- **database-reviewer** - PostgreSQL/Supabase optimization

## How to Use in Kiro

When working on a specific task, mentally apply the relevant agent's guidelines:

1. **For new features**: Follow planner → tdd-guide → code-reviewer workflow
2. **For bug fixes**: Use tdd-guide (write failing test first) → code-reviewer
3. **For refactoring**: Use architect → refactor-cleaner → code-reviewer
4. **For security**: Always apply security-reviewer guidelines before commits

## Core Principles

1. **Test-Driven** - Write tests before implementation (80%+ coverage required)
2. **Security-First** - Never compromise on security; validate all inputs
3. **Immutability** - Always create new objects, never mutate existing ones
4. **Plan Before Execute** - Plan complex features before writing code

See the full AGENTS.md file in the repository root for detailed guidelines.
