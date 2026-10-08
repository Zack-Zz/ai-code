# CodeVow release notes — preview

## 1.0.1 — 2026-10-08

- Accepts Claude Code, Codex and ZCode in task host-run evidence and evaluation input contracts while preserving conservative results for unverified runs.
- Prepares A23/A24/A25 package fixtures for every host declared by this plugin; A23/A24 exercise the selected package's file staging, update, removal and recovery tools.
- Extends A25 to verify every declared host package, source metadata and all common resources, including licenses and shared reviewer content where applicable.
- Keeps A25 compatible with legacy manifests that omit generated_agents, using the standalone builder's default reviewer composition while preserving complete-body and source-drift checks.
- Rebuilds the three host distributions and repository marketplace entries from the current source at version 1.0.1.
- Keeps native installation, skill invocation, model behavior and reviewer enforcement unverified. File staging and package parity are separate from real-host acceptance.

## 1.0.0 — initial preview

- Starts CodeVow at 1.0.0 after the maintainer confirmed the new plugin had not been installed.
- Provides declarative packages for Claude Code, Codex and ZCode from the same six skill sources.
- Adds publisher-derived native metadata, a PNG listing icon with an SVG alternative and portable package guides.
- Preserves collaboration policies, workspace-bound task records, evidence checks and owned-file protection.
- Adds native repository marketplace entry points for self-hosted preview distribution.
- All native host acceptance remains unverified; package checks and script tests do not establish runtime acceptance.

The release version, source identity and package hashes are supplied by the release builder.
