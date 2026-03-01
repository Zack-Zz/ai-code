#!/usr/bin/env bash
set -euo pipefail

# Sync an existing project with the latest ai-code bootstrap assets.
# If --langs/--tool are omitted, values are loaded from target .ai-code/bootstrap.json.
#
# Usage:
#   scripts/sync-project.sh --target /path/to/project
#   scripts/sync-project.sh --target /path/to/project --langs js --tool codex

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_DIR=""
LANGS_RAW=""
TOOL_MODE=""
FORCE_OVERWRITE="true"

print_help() {
  cat <<'EOF'
Sync project settings from ai-code using the latest local repo state.

Required:
  --target <dir>       Target project directory

Optional:
  --langs <list>       Comma-separated languages (overrides manifest)
  --tool <mode>        auto|codex|kiro|claude|both|all (overrides manifest)
  --force              Force overwrite (default: true)
  --help               Show this help

Examples:
  scripts/sync-project.sh --target ~/work/my-project
  scripts/sync-project.sh --target ~/work/my-project --langs js --tool codex
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

if [[ -z "$TARGET_DIR" ]]; then
  echo "Error: --target is required." >&2
  print_help
  exit 1
fi

TARGET_DIR="$(cd "$TARGET_DIR" && pwd)"
if [[ ! -d "$TARGET_DIR" ]]; then
  echo "Error: target directory does not exist: $TARGET_DIR" >&2
  exit 1
fi

MANIFEST_PATH="$TARGET_DIR/.ai-code/bootstrap.json"

if [[ -z "$LANGS_RAW" || -z "$TOOL_MODE" ]]; then
  if [[ ! -f "$MANIFEST_PATH" ]]; then
    echo "Error: missing $MANIFEST_PATH. Provide --langs and --tool explicitly." >&2
    exit 1
  fi
fi

if [[ -z "$LANGS_RAW" ]]; then
  LANGS_RAW="$(node -e "const fs=require('fs');const p=process.argv[1];const d=JSON.parse(fs.readFileSync(p,'utf8'));if(!d.langs)process.exit(2);process.stdout.write(String(d.langs));" "$MANIFEST_PATH" || true)"
  if [[ -z "$LANGS_RAW" ]]; then
    echo "Error: could not read 'langs' from $MANIFEST_PATH. Provide --langs." >&2
    exit 1
  fi
fi

if [[ -z "$TOOL_MODE" ]]; then
  TOOL_MODE="$(node -e "const fs=require('fs');const p=process.argv[1];const d=JSON.parse(fs.readFileSync(p,'utf8'));if(!d.tool)process.exit(2);process.stdout.write(String(d.tool));" "$MANIFEST_PATH" || true)"
  if [[ -z "$TOOL_MODE" ]]; then
    echo "Error: could not read 'tool' from $MANIFEST_PATH. Provide --tool." >&2
    exit 1
  fi
fi

echo "Sync target: $TARGET_DIR"
echo "Sync langs: $LANGS_RAW"
echo "Sync tool: $TOOL_MODE"
echo "Force overwrite: $FORCE_OVERWRITE"
echo

"$ROOT_DIR/scripts/bootstrap-project.sh" \
  --target "$TARGET_DIR" \
  --langs "$LANGS_RAW" \
  --tool "$TOOL_MODE" \
  --force
