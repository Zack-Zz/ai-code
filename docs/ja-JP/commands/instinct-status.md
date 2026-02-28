---
name: instinct-status
description: すべての学習済みインスティンクトと信頼度レベルを表示
command: true
---

# インスティンクトステータスコマンド

**Tool Scope:** `claude` / `codex` / `kiro`


すべての学習済みインスティンクトを信頼度スコアとともに、ドメインごとにグループ化して表示します。

## 実装

プラグインルートパスを使用してインスティンクトCLIを実行します:

```bash
python3 "${AI_CODE_PLUGIN_ROOT}/skills/continuous-learning-v2/scripts/instinct-cli.py" status
```

または、`AI_CODE_PLUGIN_ROOT` が設定されていない場合（手動インストール）の場合は:

```bash
python3 $AI_CODE_HOME/skills/continuous-learning-v2/scripts/instinct-cli.py status
```

## 使用方法

```
/instinct-status
/instinct-status --domain code-style
/instinct-status --low-confidence
```

## 実行内容

1. `$AI_CODE_HOME/homunculus/instincts/personal/` からすべてのインスティンクトファイルを読み込む
2. `$AI_CODE_HOME/homunculus/instincts/inherited/` から継承されたインスティンクトを読み込む
3. ドメインごとにグループ化し、信頼度バーとともに表示

## 出力形式

```
📊 Instinct Status
==================

## Code Style (4 instincts)

### prefer-functional-style
Trigger: when writing new functions
Action: Use functional patterns over classes
Confidence: ████████░░ 80%
Source: session-observation | Last updated: 2025-01-22

### use-path-aliases
Trigger: when importing modules
Action: Use @/ path aliases instead of relative imports
Confidence: ██████░░░░ 60%
Source: repo-analysis (github.com/acme/webapp)

## Testing (2 instincts)

### test-first-workflow
Trigger: when adding new functionality
Action: Write test first, then implementation
Confidence: █████████░ 90%
Source: session-observation

## Workflow (3 instincts)

### grep-before-edit
Trigger: when modifying code
Action: Search with Grep, confirm with Read, then Edit
Confidence: ███████░░░ 70%
Source: session-observation

---
Total: 9 instincts (4 personal, 5 inherited)
Observer: Running (last analysis: 5 min ago)
```

## フラグ

- `--domain <name>`: ドメインでフィルタリング（code-style、testing、gitなど）
- `--low-confidence`: 信頼度 < 0.5のインスティンクトのみを表示
- `--high-confidence`: 信頼度 >= 0.7のインスティンクトのみを表示
- `--source <type>`: ソースでフィルタリング（session-observation、repo-analysis、inherited）
- `--json`: プログラムで使用するためにJSON形式で出力
