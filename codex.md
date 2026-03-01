# Codex GUI Project Guide (Polyglot)

Use this file as the default session brief for Codex GUI in this repository.

## Scope

- Primary stacks: TypeScript/JavaScript, Java, Python, Go, Rust
- Follow TDD: tests first, then implementation
- Target minimum test coverage: 80%
- Security-first: validate inputs, avoid hardcoded secrets

## Startup Checklist

1. Inspect project structure and detect language/toolchain (`package.json`, `pom.xml`, `build.gradle*`, `pyproject.toml`, `go.mod`, `Cargo.toml`).
2. Propose a short plan before major multi-file changes.
3. Add or update tests before implementation.
4. Run stack-appropriate validation commands.
5. Summarize changes, risks, and verification results.

## TypeScript / JavaScript Workflow

- Detect package manager from lock files.
- Recommended commands:
  - Tests: `npm test` / `pnpm test` / `yarn test` / `bun test`
  - Lint: `npm run lint` (if configured)
  - Types: `npm run typecheck` or `tsc --noEmit` (if configured)
  - Build: `npm run build` (if configured)
- Prefer:
  - strict TypeScript settings
  - immutable updates and pure utility functions
  - schema validation at API boundaries

## Java Workflow

- Detect build tool:
  - Maven if `pom.xml` exists
  - Gradle if `build.gradle` or `build.gradle.kts` exists
- Recommended commands:
  - Maven test: `mvn -q test`
  - Maven compile: `mvn -q -DskipTests compile`
  - Gradle test: `./gradlew test`
  - Gradle compile: `./gradlew compileJava`

## Python Workflow

- Detect environment from `pyproject.toml` or `requirements*.txt`
- Recommended commands:
  - Tests: `pytest -q`
  - Lint: `ruff check .` (if configured)
  - Types: `mypy .` (if configured)
  - Security: `pip-audit` (if available)

## Go Workflow

- Detect module from `go.mod`
- Recommended commands:
  - Tests: `go test ./...`
  - Lint: `golangci-lint run` (if configured)
  - Build: `go build ./...`

## Rust Workflow

- Detect crate/workspace from `Cargo.toml`
- Recommended commands:
  - Tests: `cargo test`
  - Lint: `cargo clippy --all-targets --all-features -D warnings` (if configured)
  - Build: `cargo build`
  - Format: `cargo fmt --check`

## Done Criteria

- Tests added/updated and passing
- No critical security issues introduced
- Changes are minimal, readable, and explainable
- Output includes exact files changed and commands executed
