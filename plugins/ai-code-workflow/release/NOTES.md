# CodeVow release notes / CodeVow 发布说明

[English](#english) | [简体中文](#中文)

Current distribution uses the `ai-code` public main marketplace. Shared local
builds and Release download packages use `ai-code-local`; CodeVow's standalone
build helper uses `ai-code-workflow-local`. See the
[installation guide](https://github.com/Zack-Zz/ai-code/blob/main/docs/installation.md).
The entries below retain their dated release context, including earlier migration plans.

## 1.0.3

### English

- Add intent routing at workflow entry and direct skill entry points. Load rules when the current phase needs them, and check authorization before moving from analysis into development.
- Clarify collaborative and continuous modes, including which plans require confirmation and how existing user authorization carries forward.
- Shorten the Codex entry prompt to fit the native listing limit.
- Add repository tooling to preview and apply version and bilingual release-note updates while invalidating stale acceptance bindings and preserving private evidence and published history.
- Provide one GitHub build/publish entry with fixed plugin and operation choices. Publishing derives the canonical tag, verifies uploaded bytes and the Release page, and automatically synchronizes the stable marketplace; previews remain Release-only.
- Report host acceptance separately from technical publication readiness. Preserve immutable versions and support verified retries after partial publication or marketplace failures.
- Real Claude Code, Codex and ZCode installation, upgrade and runtime behavior for these bytes remain unverified; repository tests and package checks do not establish host acceptance.

### 中文

- 补齐工作流入口和技能直接入口的意图路由，按当前阶段读取规则，并在从分析转入开发前检查用户授权。
- 明确 collaborative 与 continuous 模式，说明哪些方案需要确认，以及已有用户授权如何继续生效。
- 缩短 Codex 入口提示，满足原生发布清单的长度限制。
- 增加仓库发版准备工具，预览并应用版本和中英说明，明确使旧验收绑定失效，同时保留私有材料和已发布历史。
- 统一 GitHub 构建/发布入口，仅选择插件和操作；发布时自动派生规范标签、核对上传字节与 Release 页面，并自动同步正式市场，预览版只公开 Release。
- 将宿主实测与技术发布就绪分别报告，保持公开版本不可变，支持发布或市场更新部分失败后的核验重试。
- 本版本在 Claude Code、Codex 与 ZCode 的真实安装、升级和运行行为仍未验证；仓库测试和包检查不能代表宿主验收通过。

## 1.0.2 — 2026-10-08 candidate

- Prepares GitHub marketplace distribution with schema 2 release bundles and separate plugin-only native installer ZIPs, including artifact.json.
- Provides local-market download ZIPs and separate submission source kits.
- Adds local distribution plans for independent plugin releases and channel-specific market sources: Claude archive, ZCode ZIP URL/path, and Codex version directories pinned to a distribution commit.
- Separates draft preparation, human Publish and reviewed marketplace deployment. Plans bind release assets and the previous market snapshot; deployment preserves other plugins and immutable old version directories.
- Keeps the candidate in preview with all native transport, installation, upgrade and workflow behavior acceptance unverified. Existing dist and ai-code-local entry points remain available until the new native transports pass acceptance.
- Records no remote Release, marketplace deployment or host acceptance result in these notes. Dated 1.0.1 verification remains historical evidence for its own bytes.

## 1.0.1 — 2026-10-08

- Accepts Claude Code, Codex and ZCode in task host-run evidence and evaluation input contracts while preserving conservative results for unverified runs.
- Prepares A23/A24/A25 package fixtures for every host declared by this plugin; A23/A24 exercise the selected package's file staging, update, removal and recovery tools.
- Extends A25 to verify every declared host package, source metadata and all common resources, including licenses and shared reviewer content where applicable.
- A25 compares complete reviewer bodies and checks source drift.
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
