#!/usr/bin/env bash
set -euo pipefail

# Bootstrap a target project with ai-code settings and selected skills.
#
# Usage:
#   scripts/bootstrap-project.sh --target /path/to/project --langs java,python
#   scripts/bootstrap-project.sh --target /path/to/project --langs js --tool kiro --force
#   scripts/bootstrap-project.sh --target /path/to/project --langs java --tool all

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR=""
LANGS_RAW=""
FORCE_OVERWRITE="false"
TOOL_MODE="auto"
APPLY_CODEX="false"
APPLY_KIRO="false"
APPLY_CLAUDE="false"
HAS_JAVA="false"
MANIFEST_PATH=""

print_help() {
  cat <<'EOF'
Bootstrap project settings from ai-code.

Required:
  --target <dir>       Target project directory
  --langs <list>       Comma-separated languages (java,js,python,go,rust)

Optional:
  --tool <mode>        auto|codex|kiro|claude|both|all (default: auto)
  --force              Overwrite existing files
  --help               Show this help

Examples:
  scripts/bootstrap-project.sh --target ~/work/my-java-app --langs java
  scripts/bootstrap-project.sh --target ~/work/poly-app --langs java,python,js
  scripts/bootstrap-project.sh --target ~/work/new-service --langs java --tool kiro
  scripts/bootstrap-project.sh --target ~/work/team-project --langs java --tool all
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --target)
      TARGET_DIR="${2:-}"
      shift 2
      ;;
    --langs)
      LANGS_RAW="${2:-}"
      shift 2
      ;;
    --tool)
      TOOL_MODE="${2:-}"
      shift 2
      ;;
    --force)
      FORCE_OVERWRITE="true"
      shift
      ;;
    --help|-h)
      print_help
      exit 0
      ;;
    *)
      echo "Unknown argument: $1" >&2
      print_help
      exit 1
      ;;
  esac
done

if [[ -z "$TARGET_DIR" || -z "$LANGS_RAW" ]]; then
  echo "Error: --target and --langs are required." >&2
  print_help
  exit 1
fi

TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"

if [[ ! -d "$TARGET_DIR" ]]; then
  echo "Error: target directory does not exist: $TARGET_DIR" >&2
  exit 1
fi

TOOL_MODE="$(echo "$TOOL_MODE" | tr '[:upper:]' '[:lower:]' | xargs)"
case "$TOOL_MODE" in
  auto)
    if [[ -d "$TARGET_DIR/.codex" || -f "$TARGET_DIR/codex.md" ]]; then
      APPLY_CODEX="true"
    fi
    if [[ -d "$TARGET_DIR/.kiro" ]]; then
      APPLY_KIRO="true"
    fi
    if [[ -d "$TARGET_DIR/.claude" || -f "$TARGET_DIR/CLAUDE.md" ]]; then
      APPLY_CLAUDE="true"
    fi
    if [[ "$APPLY_CODEX" != "true" && "$APPLY_KIRO" != "true" && "$APPLY_CLAUDE" != "true" ]]; then
      APPLY_CODEX="true"
      APPLY_KIRO="true"
      APPLY_CLAUDE="true"
    fi
    ;;
  codex)
    APPLY_CODEX="true"
    ;;
  kiro)
    APPLY_KIRO="true"
    ;;
  claude)
    APPLY_CLAUDE="true"
    ;;
  both)
    APPLY_CODEX="true"
    APPLY_KIRO="true"
    ;;
  all)
    APPLY_CODEX="true"
    APPLY_KIRO="true"
    APPLY_CLAUDE="true"
    ;;
  *)
    echo "Error: invalid --tool '$TOOL_MODE'. Use auto|codex|kiro|claude|both|all." >&2
    exit 1
    ;;
esac

copy_file() {
  local src="$1"
  local dst="$2"

  mkdir -p "$(dirname "$dst")"
  if [[ -e "$dst" && "$FORCE_OVERWRITE" != "true" ]]; then
    echo "skip file (exists): $dst"
    return 0
  fi
  cp "$src" "$dst"
  echo "copied file: $dst"
}

write_manifest() {
  local manifest_dir="$TARGET_DIR/.ai-code"
  MANIFEST_PATH="$manifest_dir/bootstrap.json"
  mkdir -p "$manifest_dir"

  local git_rev="unknown"
  if git -C "$ROOT_DIR" rev-parse --short HEAD >/dev/null 2>&1; then
    git_rev="$(git -C "$ROOT_DIR" rev-parse --short HEAD)"
  fi

  cat > "$MANIFEST_PATH" <<EOF
{
  "version": 1,
  "tool": "$TOOL_MODE",
  "langs": "$LANGS_RAW",
  "force": "$FORCE_OVERWRITE",
  "source_repo": "$ROOT_DIR",
  "source_git_revision": "$git_rev",
  "updated_at_utc": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
}
EOF
  echo "wrote manifest: $MANIFEST_PATH"
}

copy_dir() {
  local src="$1"
  local dst="$2"

  if [[ ! -d "$src" ]]; then
    echo "warn: directory not found, skipping: $src"
    return 0
  fi
  mkdir -p "$(dirname "$dst")"
  if [[ -e "$dst" && "$FORCE_OVERWRITE" != "true" ]]; then
    echo "skip directory (exists): $dst"
    return 0
  fi
  rm -rf "$dst"
  cp -R "$src" "$dst"
  echo "copied directory: $dst"
}

copy_skill() {
  local skill="$1"
  local dst="$TARGET_DIR/.agents/skills/$skill"
  local src="$ROOT_DIR/skills/$skill"

  if [[ ! -d "$src" ]]; then
    echo "warn: skill not found, skipping: $skill"
    return 0
  fi

  mkdir -p "$TARGET_DIR/.agents/skills"
  if [[ -e "$dst" && "$FORCE_OVERWRITE" != "true" ]]; then
    echo "skip skill (exists): $dst"
    return 0
  fi
  rm -rf "$dst"
  cp -R "$src" "$dst"
  echo "copied skill: $skill"
}

COMMON_SKILLS=(
  coding-standards
  tdd-workflow
  security-review
  verification-loop
  backend-patterns
  api-design
  strategic-compact
)

JAVA_SKILLS=(
  java-coding-standards
  springboot-patterns
  springboot-security
  springboot-tdd
  springboot-verification
  jpa-patterns
)

JS_SKILLS=(
  frontend-patterns
  e2e-testing
)

PYTHON_SKILLS=(
  python-patterns
  python-testing
)

GO_SKILLS=(
  golang-patterns
  golang-testing
)

RUST_SKILLS=(
  # No rust-specific skill currently in this repo.
)

declare -a SELECTED_SKILLS=()

add_skill_unique() {
  local skill="$1"
  for existing in "${SELECTED_SKILLS[@]:-}"; do
    if [[ "$existing" == "$skill" ]]; then
      return 0
    fi
  done
  SELECTED_SKILLS+=("$skill")
}

for s in "${COMMON_SKILLS[@]}"; do
  add_skill_unique "$s"
done

IFS=',' read -r -a langs <<< "$LANGS_RAW"
for lang_raw in "${langs[@]}"; do
  lang="$(echo "$lang_raw" | tr '[:upper:]' '[:lower:]' | xargs)"
  case "$lang" in
    java)
      HAS_JAVA="true"
      for s in "${JAVA_SKILLS[@]}"; do add_skill_unique "$s"; done
      ;;
    js|javascript|ts|typescript|frontend)
      for s in "${JS_SKILLS[@]}"; do add_skill_unique "$s"; done
      ;;
    python|py)
      for s in "${PYTHON_SKILLS[@]}"; do add_skill_unique "$s"; done
      ;;
    go|golang)
      for s in "${GO_SKILLS[@]}"; do add_skill_unique "$s"; done
      ;;
    rust)
      for s in "${RUST_SKILLS[@]}"; do add_skill_unique "$s"; done
      ;;
    *)
      echo "warn: unknown language '$lang' - skipping language-specific skills"
      ;;
  esac
done

echo "Target: $TARGET_DIR"
echo "Languages: $LANGS_RAW"
echo "Tool mode: $TOOL_MODE"
echo "Apply Codex: $APPLY_CODEX"
echo "Apply Kiro: $APPLY_KIRO"
echo "Apply Claude: $APPLY_CLAUDE"
echo "Force overwrite: $FORCE_OVERWRITE"
echo

# Shared baseline
copy_file "$ROOT_DIR/AGENTS.md" "$TARGET_DIR/AGENTS.md"

# Codex files
if [[ "$APPLY_CODEX" == "true" ]]; then
  copy_file "$ROOT_DIR/codex.md" "$TARGET_DIR/codex.md"
  copy_file "$ROOT_DIR/.codex/AGENTS.md" "$TARGET_DIR/.codex/AGENTS.md"
  copy_file "$ROOT_DIR/.codex/config.toml" "$TARGET_DIR/.codex/config.toml"
fi

# Kiro files
if [[ "$APPLY_KIRO" == "true" ]]; then
  # Core steering files
  copy_file "$ROOT_DIR/.kiro/steering/ai-code-core.md" "$TARGET_DIR/.kiro/steering/ai-code-core.md"
  copy_file "$ROOT_DIR/.kiro/steering/multi-language-workflow.md" "$TARGET_DIR/.kiro/steering/multi-language-workflow.md"
  copy_file "$ROOT_DIR/.kiro/steering/agents-overview.md" "$TARGET_DIR/.kiro/steering/agents-overview.md"
  copy_file "$ROOT_DIR/.kiro/steering/security-checklist.md" "$TARGET_DIR/.kiro/steering/security-checklist.md"
  copy_file "$ROOT_DIR/.kiro/steering/tdd-workflow.md" "$TARGET_DIR/.kiro/steering/tdd-workflow.md"
  copy_file "$ROOT_DIR/.kiro/steering/coding-standards.md" "$TARGET_DIR/.kiro/steering/coding-standards.md"
  
  # Hooks configuration
  copy_file "$ROOT_DIR/.kiro/hooks/hooks.json" "$TARGET_DIR/.kiro/hooks/hooks.json"
  
  # MCP configuration template
  copy_file "$ROOT_DIR/.kiro/settings/mcp.json" "$TARGET_DIR/.kiro/settings/mcp.json"
  
  # Documentation
  copy_file "$ROOT_DIR/.kiro/README.md" "$TARGET_DIR/.kiro/README.md"
  copy_file "$ROOT_DIR/.kiro/QUICK_START.md" "$TARGET_DIR/.kiro/QUICK_START.md"
  copy_file "$ROOT_DIR/.kiro/CHANGELOG.md" "$TARGET_DIR/.kiro/CHANGELOG.md"
fi

# Claude files
if [[ "$APPLY_CLAUDE" == "true" ]]; then
  copy_file "$ROOT_DIR/CLAUDE.md" "$TARGET_DIR/CLAUDE.md"
  copy_file "$ROOT_DIR/.claude/package-manager.json" "$TARGET_DIR/.claude/package-manager.json"
  copy_dir "$ROOT_DIR/agents" "$TARGET_DIR/agents"
  copy_dir "$ROOT_DIR/commands" "$TARGET_DIR/commands"
  copy_dir "$ROOT_DIR/rules" "$TARGET_DIR/rules"
  copy_dir "$ROOT_DIR/hooks" "$TARGET_DIR/hooks"
  copy_dir "$ROOT_DIR/scripts/hooks" "$TARGET_DIR/scripts/hooks"
  copy_dir "$ROOT_DIR/scripts/lib" "$TARGET_DIR/scripts/lib"
fi

# Copy selected skills
for skill in "${SELECTED_SKILLS[@]}"; do
  copy_skill "$skill"
done

# Java workflow checklist
if [[ "$HAS_JAVA" == "true" ]]; then
  copy_file "$ROOT_DIR/templates/JAVA_WORKFLOW.md" "$TARGET_DIR/JAVA_WORKFLOW.md"
fi

write_manifest

echo
echo "Bootstrap complete."
echo "Next steps:"
if [[ "$APPLY_CODEX" == "true" ]]; then
  echo "- Codex: open the target project in Codex GUI."
  echo "- Codex: start with 'Read /codex.md and follow the workflow defaults.'"
  echo "- Codex: optionally copy .codex/config.toml to ~/.codex/config.toml for global MCP/model defaults."
fi
if [[ "$APPLY_KIRO" == "true" ]]; then
  echo "- Kiro: open the target project; steering files from .kiro/steering load automatically."
  echo "- Kiro: review .kiro/settings/mcp.json and replace YOUR_*_HERE placeholders with actual API keys."
  echo "- Kiro: hooks are configured in .kiro/hooks/hooks.json (fileEdited, promptSubmit, agentStop)."
fi
if [[ "$APPLY_CLAUDE" == "true" ]]; then
  echo "- Claude Code: review CLAUDE.md and merge hooks/hooks.json into your Claude settings as needed."
fi
