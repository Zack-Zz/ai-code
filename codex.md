# Codex GUI Project Guide (Java + Python)

Use this file as the default session brief for Codex GUI in this repository.

## Scope

- Primary languages: Java and Python
- Follow TDD: tests first, then implementation
- Target minimum test coverage: 80%
- Security-first: validate inputs, avoid hardcoded secrets

## Startup Checklist

1. Inspect project structure and detect language/toolchain (`pom.xml`, `build.gradle*`, `pyproject.toml`, `requirements*.txt`).
2. Propose a short plan before major multi-file changes.
3. Add or update tests before implementation.
4. Run language-appropriate validation commands.
5. Summarize changes, risks, and verification results.

## Java Workflow

- Detect build tool:
  - Maven if `pom.xml` exists
  - Gradle if `build.gradle` or `build.gradle.kts` exists
- Recommended commands:
  - Maven test: `mvn -q test`
  - Maven compile: `mvn -q -DskipTests compile`
  - Gradle test: `./gradlew test`
  - Gradle compile: `./gradlew compileJava`
- Prefer:
  - Constructor injection
  - Immutable DTOs/value objects
  - Bean Validation for boundary input checks

## Python Workflow

- Detect environment from `pyproject.toml` or `requirements*.txt`
- Recommended commands:
  - Tests: `pytest -q`
  - Lint: `ruff check .` (if configured)
  - Types: `mypy .` (if configured)
  - Security: `pip-audit` (if available)
- Prefer:
  - Type hints on public functions
  - Dataclasses / Pydantic models for validated data boundaries
  - Pure functions and immutable transformations where possible

## Done Criteria

- Tests added/updated and passing
- No critical security issues introduced
- Changes are minimal, readable, and explainable
- Output includes exact files changed and commands executed
