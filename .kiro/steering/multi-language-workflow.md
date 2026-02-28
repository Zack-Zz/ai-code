---
inclusion: fileMatch
fileMatchPattern: "(pom\\.xml|build\\.gradle(\\.kts)?|.*\\.java|pyproject\\.toml|requirements(\\.txt)?|.*\\.py|go\\.mod|.*\\.go|Cargo\\.toml|.*\\.rs|package\\.json|tsconfig\\.json|.*\\.(js|jsx|ts|tsx))$"
---

# Multi-language Workflow

When files from mainstream stacks are in scope:

## Common

- Prefer test-first changes when feasible.
- Keep fixes small and verifiable; run local checks before larger refactors.
- Use project-native tooling first (respect lockfiles and existing scripts).

## Java

- Detect build tool from `pom.xml` or `build.gradle(.kts)`.
- Follow TDD: update tests before implementation when feasible.
- Typical commands:
  - Maven test: `mvn -q test`
  - Maven compile: `mvn -q -DskipTests compile`
  - Gradle test: `./gradlew test`
  - Gradle compile: `./gradlew compileJava`

## Python

- Follow TDD with `pytest` first.
- Typical commands:
  - Tests: `pytest -q`
  - Lint: `ruff check .` (if configured)
  - Type check: `mypy .` (if configured)
  - Security: `pip-audit` (if available)

## Go

- Keep code idiomatic and minimal; prefer table-driven tests.
- Typical commands:
  - Tests: `go test ./...`
  - Vet: `go vet ./...`
  - Format: `gofmt -w .` or `go fmt ./...`

## Rust

- Prefer `cargo` workflow and clippy checks.
- Typical commands:
  - Tests: `cargo test`
  - Lint: `cargo clippy --all-targets --all-features -- -D warnings`
  - Format: `cargo fmt`

## JavaScript / TypeScript

- Prefer project scripts when present (`npm run test`, `pnpm test`, etc.).
- Typical commands:
  - Tests: `npm test` or `pnpm test`
  - Lint: `npm run lint`
  - Type check: `npm run typecheck` or `tsc --noEmit`
  - Build: `npm run build`
