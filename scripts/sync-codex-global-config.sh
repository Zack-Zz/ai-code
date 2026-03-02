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
SKIP_VALIDATE="false"

print_help() {
  cat <<'EOF'
Sync ai-code Codex global config.

Optional:
  --home <dir>         Codex home directory (default: ~/.codex)
  --skip-validate      Skip Codex config validation
  --help               Show this help
EOF
}

validate_config() {
  local codex_home="$1"

  if [[ "$SKIP_VALIDATE" == "true" ]]; then
    return 0
  fi

  if ! command -v codex >/dev/null 2>&1; then
    echo "warn: 'codex' binary not found, skipping validation."
    return 0
  fi

  if ! CODEX_HOME="$codex_home" codex features list >/dev/null 2>&1; then
    echo "error: Codex config validation failed for: $codex_home/config.toml" >&2
    CODEX_HOME="$codex_home" codex features list 2>&1 | sed -n '1,120p' >&2 || true
    return 1
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --home)
      TARGET_HOME="${2:-}"
      shift 2
      ;;
    --skip-validate)
      SKIP_VALIDATE="true"
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

TARGET_HOME="${TARGET_HOME/#\~/$HOME}"
TARGET_FILE="$TARGET_HOME/config.toml"
SOURCE_FILE="$ROOT_DIR/.codex/config.toml"
BACKUP_FILE=""
HAD_TARGET="false"

if [[ ! -f "$SOURCE_FILE" ]]; then
  echo "Error: source config not found: $SOURCE_FILE" >&2
  exit 1
fi

mkdir -p "$TARGET_HOME"

# Validate source config in isolation before touching user config.
VALIDATE_HOME="$(mktemp -d)"
cp "$SOURCE_FILE" "$VALIDATE_HOME/config.toml"
if ! validate_config "$VALIDATE_HOME"; then
  rm -rf "$VALIDATE_HOME"
  exit 1
fi
rm -rf "$VALIDATE_HOME"

if [[ -f "$TARGET_FILE" ]]; then
  HAD_TARGET="true"
  BACKUP_FILE="$TARGET_FILE.bak.$(date +%Y%m%d%H%M%S)"
  cp "$TARGET_FILE" "$BACKUP_FILE"
  echo "Backed up existing config to: $BACKUP_FILE"
fi

cp "$SOURCE_FILE" "$TARGET_FILE"

if ! validate_config "$TARGET_HOME"; then
  echo "error: restoring previous config because validation failed after sync." >&2
  if [[ "$HAD_TARGET" == "true" && -n "$BACKUP_FILE" && -f "$BACKUP_FILE" ]]; then
    cp "$BACKUP_FILE" "$TARGET_FILE"
    echo "Restored from backup: $BACKUP_FILE"
  else
    rm -f "$TARGET_FILE"
    echo "Removed invalid generated config: $TARGET_FILE"
  fi
  exit 1
fi

echo "Synced global Codex config to: $TARGET_FILE"
