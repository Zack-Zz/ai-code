# CodeVow release notes — preview

## 1.0.2 — 2026-10-08 candidate

- Prepares GitHub marketplace distribution with schema 2 release bundles and separate plugin-only native installer ZIPs, including artifact.json.
- Preserves local-market download ZIPs and the existing submission source kits; schema 1 historical bundles remain explicitly verifiable.
- Adds local distribution plans for independent plugin releases and channel-specific market sources: Claude archive, ZCode ZIP URL/path, and Codex version directories pinned to a distribution commit.
- Separates draft preparation, human Publish and reviewed marketplace deployment. Plans bind release assets and the previous market snapshot; deployment preserves other plugins and immutable old version directories.
- Keeps the candidate in preview with all native transport, installation, upgrade and workflow behavior acceptance unverified. Existing dist and ai-code-local entry points remain available until the new native transports pass acceptance.
- Records no remote Release, marketplace deployment or host acceptance result in these notes. Dated 1.0.1 verification remains historical evidence for its own bytes.

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
