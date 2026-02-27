# Java Workflow Checklist (ai-code)

This checklist turns ai-code principles into executable daily commands for Java projects.

## 1) Detect Build Tool

- Use Maven when `pom.xml` exists.
- Use Gradle when `build.gradle` or `build.gradle.kts` exists.

## 2) Daily Development Loop

Run after each meaningful change.

### Maven

```bash
mvn -q test
mvn -q -DskipTests compile
```

### Gradle

```bash
./gradlew test
./gradlew compileJava
```

## 3) Pre-Commit Verification

Run before every commit.

### Maven

```bash
mvn -q test
mvn -q verify
# Optional if dependency-check plugin is configured:
mvn -q org.owasp:dependency-check-maven:check
```

### Gradle

```bash
./gradlew test
./gradlew build
# Optional if dependency-check plugin is configured:
./gradlew dependencyCheckAnalyze
```

## 4) TDD Cadence

1. Write/update test first (RED).
2. Implement minimal code to pass (GREEN).
3. Refactor while tests remain green (REFACTOR).

## 5) Security and Quality Guardrails

- Validate all external input at boundaries.
- Do not hardcode secrets; use environment variables.
- Prefer immutable DTOs and constructor injection.
- Review `git diff` before push.
