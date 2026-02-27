**言語:** [English](../../README.md) | [简体中文](../../README.zh-CN.md) | [繁體中文](../zh-TW/README.md) | [日本語](README.md)

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

**🌐 言語 / Language / 語言**

[**English**](../../README.md) | [简体中文](../../README.zh-CN.md) | [繁體中文](../zh-TW/README.md) | [日本語](README.md)

</div>

---

**ChatGPT、Codex、Claude など主流 AI 開発アシスタント向けのマルチプラットフォーム実用設定集。**

10ヶ月以上の集中的な日常使用により、実際のプロダクト構築の過程で進化した、本番環境対応のエージェント、スキル、フック、コマンド、ルール、MCP設定。

---

## プロジェクト方針

`ai-code` は単一ベンダー向けではなく、複数アシスタント連携を前提にした設定リポジトリです。

- ChatGPT/Codex：`AGENTS.md` + `.codex/config.toml` + `codex.md`
- Claude Code：プラグイン/ルール/フックのワークフロー
- Cursor/OpenCode：互換設定とコマンド体系
- Java/Python を優先し、他言語は拡張可能

---

## 使い方

- まず利用するアシスタントを選びます：Codex/ChatGPT、Claude Code、または Cursor/OpenCode。
- プロジェクト共通ルールは `AGENTS.md` に集約し、言語別の運用ルールを追加します。
- Java/Python プロジェクトは `codex.md` から開始し、実装前にテストを更新します。
- `agents/`、`skills/`、`rules/`、`commands/` は必要なものだけ選んで導入します。

### 統一ランタイム設定（Codex + Claude）

Hook/Session スクリプトは共通の環境変数をサポートします：

```bash
export AI_CODE_TOOL=codex      # codex | claude
export AI_CODE_HOME=/path/to/assistant-home
```

- `AI_CODE_HOME` が最優先です。
- `AI_CODE_HOME` 未設定かつ `AI_CODE_TOOL=codex` の場合、既定は `~/.codex` です。
- それ以外は既定で `~/.claude` を使用します。
- 単発実行では `--tool`、`--home` も利用できます。

---

## 🚀 クイックスタート

### パターン 1：Codex / ChatGPT（推奨）

```bash
git clone https://github.com/Zack-Zz/ai-code.git
cd ai-code
cp .codex/config.toml ~/.codex/config.toml
```

Codex GUI でリポジトリを開き、最初の指示として次を送ってください：
`/codex.md を読み、Java/Python ワークフローに従って実行してください`

### パターン 2：Claude Code

```bash
git clone https://github.com/Zack-Zz/ai-code.git
cd ai-code
./install.sh typescript python golang
```

### パターン 3：Cursor / OpenCode

- Cursor：`.cursor/` を使用し、必要なら `./install.sh --target cursor ...`
- OpenCode：リポジトリ直下で起動し `.opencode/` 設定を読み込む

### パターン 4：Kiro GUI

```bash
git clone https://github.com/Zack-Zz/ai-code.git
cd ai-code
```

- Kiro でこのディレクトリを開きます。
- Kiro は `.kiro/steering/` のステアリングファイルを自動で読み込みます。
- ルート `AGENTS.md` もグローバル指示として利用できます。

---

## 🌐 クロスプラットフォーム対応

このプラグインは **Windows、macOS、Linux** を完全にサポートしています。すべてのフックとスクリプトが Node.js で書き直され、最大の互換性を実現しています。

### パッケージマネージャー検出

プラグインは、以下の優先順位で、お好みのパッケージマネージャー（npm、pnpm、yarn、bun）を自動検出します：

1. **環境変数**: `CLAUDE_PACKAGE_MANAGER`
2. **プロジェクト設定**: `.claude/package-manager.json`
3. **package.json**: `packageManager` フィールド
4. **ロックファイル**: package-lock.json、yarn.lock、pnpm-lock.yaml、bun.lockb から検出
5. **グローバル設定**: `~/.claude/package-manager.json`
6. **フォールバック**: 最初に利用可能なパッケージマネージャー

お好みのパッケージマネージャーを設定するには：

```bash
# 環境変数経由
export CLAUDE_PACKAGE_MANAGER=pnpm

# グローバル設定経由
node scripts/setup-package-manager.js --global pnpm

# プロジェクト設定経由
node scripts/setup-package-manager.js --project bun

# 現在の設定を検出
node scripts/setup-package-manager.js --detect
```

または Claude Code で `/setup-pm` コマンドを使用。

---

## 📦 含まれるもの

このリポジトリは**Claude Codeプラグイン**です - 直接インストールするか、コンポーネントを手動でコピーできます。

```
ai-code/
|-- .claude-plugin/   # プラグインとマーケットプレイスマニフェスト
|   |-- plugin.json         # プラグインメタデータとコンポーネントパス
|   |-- marketplace.json    # /plugin marketplace add 用のマーケットプレイスカタログ
|
|-- agents/           # 委任用の専門サブエージェント
|   |-- planner.md           # 機能実装計画
|   |-- architect.md         # システム設計決定
|   |-- tdd-guide.md         # テスト駆動開発
|   |-- code-reviewer.md     # 品質とセキュリティレビュー
|   |-- security-reviewer.md # 脆弱性分析
|   |-- build-error-resolver.md
|   |-- e2e-runner.md        # Playwright E2E テスト
|   |-- refactor-cleaner.md  # デッドコード削除
|   |-- doc-updater.md       # ドキュメント同期
|   |-- go-reviewer.md       # Go コードレビュー
|   |-- go-build-resolver.md # Go ビルドエラー解決
|   |-- python-reviewer.md   # Python コードレビュー（新規）
|   |-- database-reviewer.md # データベース/Supabase レビュー（新規）
|
|-- skills/           # ワークフロー定義と領域知識
|   |-- coding-standards/           # 言語ベストプラクティス
|   |-- backend-patterns/           # API、データベース、キャッシュパターン
|   |-- frontend-patterns/          # React、Next.js パターン
|   |-- continuous-learning/        # セッションからパターンを自動抽出（利用ガイド）
|   |-- continuous-learning-v2/     # 信頼度スコア付き直感ベース学習
|   |-- iterative-retrieval/        # サブエージェント用の段階的コンテキスト精製
|   |-- strategic-compact/          # 手動圧縮提案（利用ガイド）
|   |-- tdd-workflow/               # TDD 方法論
|   |-- security-review/            # セキュリティチェックリスト
|   |-- eval-harness/               # 検証ループ評価（利用ガイド）
|   |-- verification-loop/          # 継続的検証（利用ガイド）
|   |-- golang-patterns/            # Go イディオムとベストプラクティス
|   |-- golang-testing/             # Go テストパターン、TDD、ベンチマーク
|   |-- cpp-testing/                # C++ テスト GoogleTest、CMake/CTest（新規）
|   |-- django-patterns/            # Django パターン、モデル、ビュー（新規）
|   |-- django-security/            # Django セキュリティベストプラクティス（新規）
|   |-- django-tdd/                 # Django TDD ワークフロー（新規）
|   |-- django-verification/        # Django 検証ループ（新規）
|   |-- python-patterns/            # Python イディオムとベストプラクティス（新規）
|   |-- python-testing/             # pytest を使った Python テスト（新規）
|   |-- springboot-patterns/        # Java Spring Boot パターン（新規）
|   |-- springboot-security/        # Spring Boot セキュリティ（新規）
|   |-- springboot-tdd/             # Spring Boot TDD（新規）
|   |-- springboot-verification/    # Spring Boot 検証（新規）
|   |-- configure-ai-code/              # インタラクティブインストールウィザード（新規）
|   |-- security-scan/              # AgentShield セキュリティ監査統合（新規）
|
|-- commands/         # スラッシュコマンド用クイック実行
|   |-- tdd.md              # /tdd - テスト駆動開発
|   |-- plan.md             # /plan - 実装計画
|   |-- e2e.md              # /e2e - E2E テスト生成
|   |-- code-review.md      # /code-review - 品質レビュー
|   |-- build-fix.md        # /build-fix - ビルドエラー修正
|   |-- refactor-clean.md   # /refactor-clean - デッドコード削除
|   |-- learn.md            # /learn - セッション中のパターン抽出（利用ガイド）
|   |-- checkpoint.md       # /checkpoint - 検証状態を保存（利用ガイド）
|   |-- verify.md           # /verify - 検証ループを実行（利用ガイド）
|   |-- setup-pm.md         # /setup-pm - パッケージマネージャーを設定
|   |-- go-review.md        # /go-review - Go コードレビュー（新規）
|   |-- go-test.md          # /go-test - Go TDD ワークフロー（新規）
|   |-- go-build.md         # /go-build - Go ビルドエラーを修正（新規）
|   |-- skill-create.md     # /skill-create - Git 履歴からスキルを生成（新規）
|   |-- instinct-status.md  # /instinct-status - 学習した直感を表示（新規）
|   |-- instinct-import.md  # /instinct-import - 直感をインポート（新規）
|   |-- instinct-export.md  # /instinct-export - 直感をエクスポート（新規）
|   |-- evolve.md           # /evolve - 直感をスキルにクラスタリング
|   |-- pm2.md              # /pm2 - PM2 サービスライフサイクル管理（新規）
|   |-- multi-plan.md       # /multi-plan - マルチエージェント タスク分解（新規）
|   |-- multi-execute.md    # /multi-execute - オーケストレーション マルチエージェント ワークフロー（新規）
|   |-- multi-backend.md    # /multi-backend - バックエンド マルチサービス オーケストレーション（新規）
|   |-- multi-frontend.md   # /multi-frontend - フロントエンド マルチサービス オーケストレーション（新規）
|   |-- multi-workflow.md   # /multi-workflow - 一般的なマルチサービス ワークフロー（新規）
|
|-- rules/            # 常に従うべきガイドライン（~/.claude/rules/ にコピー）
|   |-- README.md            # 構造概要とインストールガイド
|   |-- common/              # 言語非依存の原則
|   |   |-- coding-style.md    # イミュータビリティ、ファイル組織
|   |   |-- git-workflow.md    # コミットフォーマット、PR プロセス
|   |   |-- testing.md         # TDD、80% カバレッジ要件
|   |   |-- performance.md     # モデル選択、コンテキスト管理
|   |   |-- patterns.md        # デザインパターン、スケルトンプロジェクト
|   |   |-- hooks.md           # フック アーキテクチャ、TodoWrite
|   |   |-- agents.md          # サブエージェントへの委任時機
|   |   |-- security.md        # 必須セキュリティチェック
|   |-- typescript/          # TypeScript/JavaScript 固有
|   |-- python/              # Python 固有
|   |-- golang/              # Go 固有
|
|-- hooks/            # トリガーベースの自動化
|   |-- hooks.json                # すべてのフック設定（PreToolUse、PostToolUse、Stop など）
|   |-- memory-persistence/       # セッションライフサイクルフック（利用ガイド）
|   |-- strategic-compact/        # 圧縮提案（利用ガイド）
|
|-- scripts/          # クロスプラットフォーム Node.js スクリプト（新規）
|   |-- lib/                     # 共有ユーティリティ
|   |   |-- utils.js             # クロスプラットフォーム ファイル/パス/システムユーティリティ
|   |   |-- package-manager.js   # パッケージマネージャー検出と選択
|   |-- hooks/                   # フック実装
|   |   |-- session-start.js     # セッション開始時にコンテキストを読み込む
|   |   |-- session-end.js       # セッション終了時に状態を保存
|   |   |-- pre-compact.js       # 圧縮前の状態保存
|   |   |-- suggest-compact.js   # 戦略的圧縮提案
|   |   |-- evaluate-session.js  # セッションからパターンを抽出
|   |-- setup-package-manager.js # インタラクティブ PM セットアップ
|
|-- tests/            # テストスイート（新規）
|   |-- lib/                     # ライブラリテスト
|   |-- hooks/                   # フックテスト
|   |-- run-all.js               # すべてのテストを実行
|
|-- contexts/         # 動的システムプロンプト注入コンテキスト（利用ガイド）
|   |-- dev.md              # 開発モード コンテキスト
|   |-- review.md           # コードレビューモード コンテキスト
|   |-- research.md         # リサーチ/探索モード コンテキスト
|
|-- examples/         # 設定例とセッション
|   |-- CLAUDE.md           # プロジェクトレベル設定例
|   |-- user-CLAUDE.md      # ユーザーレベル設定例
|
|-- mcp-configs/      # MCP サーバー設定
|   |-- mcp-servers.json    # GitHub、Supabase、Vercel、Railway など
|
|-- marketplace.json  # 自己ホストマーケットプレイス設定（/plugin marketplace add 用）
```

---

## 🛠️ エコシステムツール

### スキル作成ツール

リポジトリから Claude Code スキルを生成する 2 つの方法：

#### オプション A：ローカル分析（ビルトイン）

外部サービスなしで、ローカル分析に `/skill-create` コマンドを使用：

```bash
/skill-create                    # 現在のリポジトリを分析
/skill-create --instincts        # 継続的学習用の直感も生成
```

これはローカルで Git 履歴を分析し、SKILL.md ファイルを生成します。

#### オプション B：GitHub アプリ（高度な機能）

高度な機能用（10k+ コミット、自動 PR、チーム共有）：

[GitHub アプリをインストール](https://github.com/apps/skill-creator) | [github.com/Zack-Zz/ai-code](https://github.com/Zack-Zz/ai-code)

```bash
# 任意の Issue にコメント：
/skill-creator analyze

# またはデフォルトブランチへのプッシュで自動トリガー
```

両オプションで生成されるもの：
- **SKILL.mdファイル** - Claude Codeですぐに使えるスキル
- **instinctコレクション** - continuous-learning-v2用
- **パターン抽出** - コミット履歴からの学習

### AgentShield — セキュリティ監査ツール

Claude Code 設定の脆弱性、誤設定、インジェクションリスクをスキャンします。

```bash
# クイックスキャン（インストール不要）
npx ecc-agentshield scan

# 安全な問題を自動修正
npx ecc-agentshield scan --fix

# Opus 4.6 による深い分析
npx ecc-agentshield scan --opus --stream

# ゼロから安全な設定を生成
npx ecc-agentshield init
```

CLAUDE.md、settings.json、MCP サーバー、フック、エージェント定義をチェックします。セキュリティグレード（A-F）と実行可能な結果を生成します。

Claude Codeで`/security-scan`を実行、または[GitHub Action](https://github.com/affaan-m/agentshield)でCIに追加できます。

[GitHub](https://github.com/affaan-m/agentshield) | [npm](https://www.npmjs.com/package/ecc-agentshield)

### 🧠 継続的学習 v2

instinctベースの学習システムがパターンを自動学習：

```bash
/instinct-status        # 信頼度付きで学習したinstinctを表示
/instinct-import <file> # 他者のinstinctをインポート
/instinct-export        # instinctをエクスポートして共有
/evolve                 # 関連するinstinctをスキルにクラスタリング
```

完全なドキュメントは`skills/continuous-learning-v2/`を参照してください。

---

## 📋 要件

### Claude Code CLI バージョン

**最小バージョン: v2.1.0 以上**

このプラグインは Claude Code CLI v2.1.0+ が必要です。プラグインシステムがフックを処理する方法が変更されたためです。

バージョンを確認：
```bash
claude --version
```

### 重要: フック自動読み込み動作

> ⚠️ **貢献者向け:** `.claude-plugin/plugin.json`に`"hooks"`フィールドを追加しないでください。これは回帰テストで強制されます。

Claude Code v2.1+は、インストール済みプラグインの`hooks/hooks.json`（規約）を自動読み込みします。`plugin.json`で明示的に宣言するとエラーが発生します：

```
Duplicate hooks file detected: ./hooks/hooks.json resolves to already-loaded file
```

**背景:** これは本リポジトリで複数の修正/リバート循環を引き起こしました（[#29](https://github.com/Zack-Zz/ai-code/issues/29), [#52](https://github.com/Zack-Zz/ai-code/issues/52), [#103](https://github.com/Zack-Zz/ai-code/issues/103)）。Claude Codeバージョン間で動作が変わったため混乱がありました。今後を防ぐため回帰テストがあります。

---

## 📥 インストール

### オプション1：プラグインとしてインストール（推奨）

このリポジトリを使用する最も簡単な方法 - Claude Codeプラグインとしてインストール：

```bash
# このリポジトリをマーケットプレイスとして追加
/plugin marketplace add Zack-Zz/ai-code

# プラグインをインストール
/plugin install ai-code@ai-code
```

または、`~/.claude/settings.json` に直接追加：

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

これで、すべてのコマンド、エージェント、スキル、フックにすぐにアクセスできます。

> **注:** Claude Codeプラグインシステムは`rules`をプラグイン経由で配布できません（[アップストリーム制限](https://code.claude.com/docs/en/plugins-reference)）。ルールは手動でインストールする必要があります：
>
> ```bash
> # まずリポジトリをクローン
> git clone https://github.com/Zack-Zz/ai-code.git
>
> # オプション A：ユーザーレベルルール（すべてのプロジェクトに適用）
> mkdir -p ~/.claude/rules
> cp -r ai-code/rules/common/* ~/.claude/rules/
> cp -r ai-code/rules/typescript/* ~/.claude/rules/   # スタックを選択
> cp -r ai-code/rules/python/* ~/.claude/rules/
> cp -r ai-code/rules/golang/* ~/.claude/rules/
>
> # オプション B：プロジェクトレベルルール（現在のプロジェクトのみ）
> mkdir -p .claude/rules
> cp -r ai-code/rules/common/* .claude/rules/
> cp -r ai-code/rules/typescript/* .claude/rules/     # スタックを選択
> ```

---

### 🔧 オプション2：手動インストール

インストール内容を手動で制御したい場合：

```bash
# リポジトリをクローン
git clone https://github.com/Zack-Zz/ai-code.git

# エージェントを Claude 設定にコピー
cp ai-code/agents/*.md ~/.claude/agents/

# ルール（共通 + 言語固有）をコピー
cp -r ai-code/rules/common/* ~/.claude/rules/
cp -r ai-code/rules/typescript/* ~/.claude/rules/   # スタックを選択
cp -r ai-code/rules/python/* ~/.claude/rules/
cp -r ai-code/rules/golang/* ~/.claude/rules/

# コマンドをコピー
cp ai-code/commands/*.md ~/.claude/commands/

# スキルをコピー
cp -r ai-code/skills/* ~/.claude/skills/
```

#### settings.json にフックを追加

`hooks/hooks.json` のフックを `~/.claude/settings.json` にコピーします。

#### MCP を設定

`mcp-configs/mcp-servers.json` から必要な MCP サーバーを `~/.claude.json` にコピーします。

**重要:** `YOUR_*_HERE`プレースホルダーを実際のAPIキーに置き換えてください。

---

## 🎯 主要概念

### エージェント

サブエージェントは限定的な範囲のタスクを処理します。例：

```markdown
---
name: code-reviewer
description: コードの品質、セキュリティ、保守性をレビュー
tools: ["Read", "Grep", "Glob", "Bash"]
model: opus
---

あなたは経験豊富なコードレビュアーです...

```

### スキル

スキルはコマンドまたはエージェントによって呼び出されるワークフロー定義：

```markdown
# TDD ワークフロー

1. インターフェースを最初に定義
2. テストを失敗させる (RED)
3. 最小限のコードを実装 (GREEN)
4. リファクタリング (IMPROVE)
5. 80%+ のカバレッジを確認
```

### フック

フックはツールイベントでトリガーされます。例 - console.log についての警告：

```json
{
  "matcher": "tool == \"Edit\" && tool_input.file_path matches \"\\\\.(ts|tsx|js|jsx)$\"",
  "hooks": [{
    "type": "command",
    "command": "#!/bin/bash\ngrep -n 'console\\.log' \"$file_path\" && echo '[Hook] Remove console.log' >&2"
  }]
}
```

### ルール

ルールは常に従うべきガイドラインで、`common/`（言語非依存）+ 言語固有ディレクトリに組織化：

```
rules/
  common/          # 普遍的な原則（常にインストール）
  typescript/      # TS/JS 固有パターンとツール
  python/          # Python 固有パターンとツール
  golang/          # Go 固有パターンとツール
```

インストールと構造の詳細は[`rules/README.md`](rules/README.md)を参照してください。

---

## 🧪 テストを実行

プラグインには包括的なテストスイートが含まれています：

```bash
# すべてのテストを実行
node tests/run-all.js

# 個別のテストファイルを実行
node tests/lib/utils.test.js
node tests/lib/package-manager.test.js
node tests/hooks/hooks.test.js
```

---

## 🤝 貢献

**貢献は大歓迎で、奨励されています。**

このリポジトリはコミュニティリソースを目指しています。以下のようなものがあれば：
- 有用なエージェントまたはスキル
- 巧妙なフック
- より良い MCP 設定
- 改善されたルール

ぜひ貢献してください！ガイドについては[CONTRIBUTING.md](CONTRIBUTING.md)を参照してください。

### 貢献アイデア

- 言語固有のスキル（Rust、C#、Swift、Kotlin） — Go、Python、Javaは既に含まれています
- フレームワーク固有の設定（Rails、Laravel、FastAPI、NestJS） — Django、Spring Bootは既に含まれています
- DevOpsエージェント（Kubernetes、Terraform、AWS、Docker）
- テスト戦略（異なるフレームワーク、ビジュアルリグレッション）
- 専門領域の知識（ML、データエンジニアリング、モバイル開発）

---

## Cursor IDE サポート

ai-code-universal は [Cursor IDE](https://cursor.com) の事前翻訳設定を含みます。`.cursor/` ディレクトリには、Cursor フォーマット向けに適応されたルール、エージェント、スキル、コマンド、MCP 設定が含まれています。

### クイックスタート (Cursor)

```bash
# パッケージをインストール
npm install ai-code-universal

# 言語をインストール
./install.sh --target cursor typescript
./install.sh --target cursor python golang
```

### 翻訳内容

| コンポーネント | Claude Code → Cursor | パリティ |
|-----------|---------------------|--------|
| Rules | YAML フロントマター追加、パスフラット化 | 完全 |
| Agents | モデル ID 展開、ツール → 読み取り専用フラグ | 完全 |
| Skills | 変更不要（同一の標準） | 同一 |
| Commands | パス参照更新、multi-* スタブ化 | 部分的 |
| MCP Config | 環境補間構文更新 | 完全 |
| Hooks | Cursor相当なし | 別の方法を参照 |

詳細は[.cursor/README.md](.cursor/README.md)および完全な移行ガイドは[.cursor/MIGRATION.md](.cursor/MIGRATION.md)を参照してください。

---

## 🔌 OpenCodeサポート

ai-codeは**フルOpenCodeサポート**をプラグインとフック含めて提供。

### クイックスタート

```bash
# OpenCode をインストール
npm install -g opencode

# リポジトリルートで実行
opencode
```

設定は`.opencode/opencode.json`から自動検出されます。

### 機能パリティ

| 機能 | Claude Code | OpenCode | ステータス |
|---------|-------------|----------|--------|
| Agents | ✅ 14 エージェント | ✅ 12 エージェント | **Claude Code がリード** |
| Commands | ✅ 30 コマンド | ✅ 24 コマンド | **Claude Code がリード** |
| Skills | ✅ 28 スキル | ✅ 16 スキル | **Claude Code がリード** |
| Hooks | ✅ 3 フェーズ | ✅ 20+ イベント | **OpenCode が多い！** |
| Rules | ✅ 8 ルール | ✅ 8 ルール | **完全パリティ** |
| MCP Servers | ✅ 完全 | ✅ 完全 | **完全パリティ** |
| Custom Tools | ✅ フック経由 | ✅ ネイティブサポート | **OpenCode がより良い** |

### プラグイン経由のフックサポート

OpenCodeのプラグインシステムはClaude Codeより高度で、20+イベントタイプ：

| Claude Code フック | OpenCode プラグインイベント |
|-----------------|----------------------|
| PreToolUse | `tool.execute.before` |
| PostToolUse | `tool.execute.after` |
| Stop | `session.idle` |
| SessionStart | `session.created` |
| SessionEnd | `session.deleted` |

**追加OpenCodeイベント**: `file.edited`, `file.watcher.updated`, `message.updated`, `lsp.client.diagnostics`, `tui.toast.show`など。

### 利用可能なコマンド（24）

| コマンド | 説明 |
|---------|-------------|
| `/plan` | 実装計画を作成 |
| `/tdd` | TDD ワークフロー実行 |
| `/code-review` | コード変更をレビュー |
| `/security` | セキュリティレビュー実行 |
| `/build-fix` | ビルドエラーを修正 |
| `/e2e` | E2E テストを生成 |
| `/refactor-clean` | デッドコードを削除 |
| `/orchestrate` | マルチエージェント ワークフロー |
| `/learn` | セッションからパターン抽出 |
| `/checkpoint` | 検証状態を保存 |
| `/verify` | 検証ループを実行 |
| `/eval` | 基準に対して評価 |
| `/update-docs` | ドキュメントを更新 |
| `/update-codemaps` | コードマップを更新 |
| `/test-coverage` | カバレッジを分析 |
| `/go-review` | Go コードレビュー |
| `/go-test` | Go TDD ワークフロー |
| `/go-build` | Go ビルドエラーを修正 |
| `/skill-create` | Git からスキル生成 |
| `/instinct-status` | 学習した直感を表示 |
| `/instinct-import` | 直感をインポート |
| `/instinct-export` | 直感をエクスポート |
| `/evolve` | 直感をスキルにクラスタリング |
| `/setup-pm` | パッケージマネージャーを設定 |

### プラグインインストール

**オプション1：直接使用**
```bash
cd ai-code
opencode
```

**オプション2：npmパッケージとしてインストール**
```bash
npm install ai-code-universal
```

その後`opencode.json`に追加：
```json
{
  "plugin": ["ai-code-universal"]
}
```

### ドキュメンテーション

- **移行ガイド**: `.opencode/MIGRATION.md`
- **OpenCode プラグイン README**: `.opencode/README.md`
- **統合ルール**: `.opencode/instructions/INSTRUCTIONS.md`
- **LLM ドキュメンテーション**: `llms.txt`（完全な OpenCode ドキュメント）

---

## 📖 背景

このリポジトリは、再利用しやすい実用設定ベースラインとして維持されています。
各プロジェクト要件に合わせて取捨選択し、継続的に改善してください。

---

## ⚠️ 重要な注記

### コンテキストウィンドウ管理

**重要:** すべてのMCPを一度に有効にしないでください。多くのツールを有効にすると、200kのコンテキストウィンドウが70kに縮小される可能性があります。

経験則：
- 20-30のMCPを設定
- プロジェクトごとに10未満を有効にしたままにしておく
- アクティブなツール80未満

プロジェクト設定で`disabledMcpServers`を使用して、未使用のツールを無効にします。

### カスタマイズ

これらの設定は私のワークフロー用です。あなたは以下を行うべきです：
1. 共感できる部分から始める
2. 技術スタックに合わせて修正
3. 使用しない部分を削除
4. 独自のパターンを追加

---

## 🔗 リンク

- **ローカル利用ガイド:** [USAGE.md](../USAGE.md)
- **Fork リポジトリ:** [Zack-Zz/ai-code](https://github.com/Zack-Zz/ai-code)
- **スキル ディレクトリ:** awesome-agent-skills（コミュニティ管理のエージェントスキル ディレクトリ）

---

## 📄 ライセンス

MIT - 自由に使用、必要に応じて修正、可能であれば貢献してください。

---

**プロジェクトの要件に合わせて取捨選択し、継続的に改善してください。**
