---
inclusion: fileMatch
fileMatchPattern: "(pom\\.xml|build\\.gradle(\\.kts)?|.*\\.java|pyproject\\.toml|requirements(\\.txt)?|.*\\.py)$"
---

# Java and Python Workflow

When Java or Python files are in scope:

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

