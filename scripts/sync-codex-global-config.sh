#!/usr/bin/env bash
set -euo pipefail

# Sync ai-code Codex reference config into ~/.codex/config.toml (or custom home).
#
# Usage:
#   scripts/sync-codex-global-config.sh
#   scripts/sync-codex-global-config.sh --home /custom/codex-home

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TARGET_HOME="${HOME}/.codex"
TARGET_FILE=""

print_help() {
  cat <<'EOF'
Sync ai-code Codex global config.

Optional:
  --home <dir>         Codex home directory (default: ~/.codex)
  --help               Show this help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --home)
      TARGET_HOME="${2:-}"
      shift 2
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

TARGET_HOME="${TARGET_HOME/#\~/$HOME}"
TARGET_FILE="$TARGET_HOME/config.toml"
SOURCE_FILE="$ROOT_DIR/.codex/config.toml"

mkdir -p "$TARGET_HOME"

if [[ -f "$TARGET_FILE" ]]; then
  BACKUP_FILE="$TARGET_FILE.bak.$(date +%Y%m%d%H%M%S)"
  cp "$TARGET_FILE" "$BACKUP_FILE"
  echo "Backed up existing config to: $BACKUP_FILE"
fi

cp "$SOURCE_FILE" "$TARGET_FILE"
echo "Synced global Codex config to: $TARGET_FILE"
