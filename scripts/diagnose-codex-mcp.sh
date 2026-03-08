#!/usr/bin/env bash
set -euo pipefail

# Diagnose which Codex MCP server(s) cause slow startup or timeout.
#
# The script enables one MCP server at a time, disables all others, runs
# `codex exec`, and captures a per-server log + summary table.

CODEX_HOME_DIR="${HOME}/.codex"
WORKDIR="$(pwd)"
SERVERS_RAW=""
TIMEOUT_SEC="30"
PROMPT_TEXT="echo ok"
OUTPUT_DIR="${TMPDIR:-/tmp}/codex-mcp-diagnose-$(date +%Y%m%d%H%M%S)"

print_help() {
  cat <<'EOF'
Diagnose Codex MCP startup behavior.

Usage:
  scripts/diagnose-codex-mcp.sh [options]

Options:
  --home <dir>          Codex home directory (default: ~/.codex)
  --workdir <dir>       Work directory for codex exec (default: current dir)
  --servers <list>      Comma-separated MCP names (default: all from config.toml)
  --timeout-sec <n>     Per-MCP startup timeout override (default: 30)
  --prompt <text>       Prompt used for codex exec (default: "echo ok")
  --output <dir>        Output directory for logs/summary
  --help                Show this help

Example:
  scripts/diagnose-codex-mcp.sh \
    --servers github,context7,memory,sequential-thinking \
    --timeout-sec 30
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --home)
      CODEX_HOME_DIR="${2:-}"
      shift 2
      ;;
    --workdir)
      WORKDIR="${2:-}"
      shift 2
      ;;
    --servers)
      SERVERS_RAW="${2:-}"
      shift 2
      ;;
    --timeout-sec)
      TIMEOUT_SEC="${2:-}"
      shift 2
      ;;
    --prompt)
      PROMPT_TEXT="${2:-}"
      shift 2
      ;;
    --output)
      OUTPUT_DIR="${2:-}"
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

CODEX_HOME_DIR="${CODEX_HOME_DIR/#\~/$HOME}"
CONFIG_FILE="$CODEX_HOME_DIR/config.toml"

if ! command -v codex >/dev/null 2>&1; then
  echo "Error: 'codex' command not found in PATH." >&2
  exit 1
fi

if [[ ! -f "$CONFIG_FILE" ]]; then
  echo "Error: config not found: $CONFIG_FILE" >&2
  exit 1
fi

if [[ ! -d "$WORKDIR" ]]; then
  echo "Error: workdir not found: $WORKDIR" >&2
  exit 1
fi

if ! [[ "$TIMEOUT_SEC" =~ ^[0-9]+$ ]]; then
  echo "Error: --timeout-sec must be a positive integer." >&2
  exit 1
fi

CONFIG_SERVERS=()
while IFS= read -r line; do
  [[ -n "$line" ]] && CONFIG_SERVERS+=("$line")
done < <(sed -n 's/^\[mcp_servers\.\([^]]*\)\]$/\1/p' "$CONFIG_FILE")
if [[ ${#CONFIG_SERVERS[@]} -eq 0 ]]; then
  echo "Error: no MCP servers found in $CONFIG_FILE" >&2
  exit 1
fi

declare -a TARGET_SERVERS=()
if [[ -n "$SERVERS_RAW" ]]; then
  IFS=',' read -r -a raw_arr <<< "$SERVERS_RAW"
  for item in "${raw_arr[@]}"; do
    s="$(echo "$item" | xargs)"
    [[ -n "$s" ]] && TARGET_SERVERS+=("$s")
  done
else
  TARGET_SERVERS=("${CONFIG_SERVERS[@]}")
fi

if [[ ${#TARGET_SERVERS[@]} -eq 0 ]]; then
  echo "Error: no target servers to test." >&2
  exit 1
fi

mkdir -p "$OUTPUT_DIR"
SUMMARY_TSV="$OUTPUT_DIR/summary.tsv"
{
  echo -e "server\tstatus\texit_code\tduration_sec\tnote\tlog_file"
} > "$SUMMARY_TSV"

contains_server() {
  local needle="$1"
  for x in "${CONFIG_SERVERS[@]}"; do
    if [[ "$x" == "$needle" ]]; then
      return 0
    fi
  done
  return 1
}

echo "Codex MCP diagnose starting..."
echo "Config:  $CONFIG_FILE"
echo "Workdir: $WORKDIR"
echo "Output:  $OUTPUT_DIR"
echo "Servers: ${TARGET_SERVERS[*]}"
echo

for server in "${TARGET_SERVERS[@]}"; do
  if ! contains_server "$server"; then
    echo "warn: server '$server' not found in config, skipping."
    continue
  fi

  logfile="$OUTPUT_DIR/${server}.log"
  echo "==> Testing MCP: $server"

  cmd=(codex exec --skip-git-repo-check -C "$WORKDIR")
  for s in "${CONFIG_SERVERS[@]}"; do
    if [[ "$s" == "$server" ]]; then
      cmd+=(-c "mcp_servers.$s.enabled=true")
    else
      cmd+=(-c "mcp_servers.$s.enabled=false")
    fi
  done
  cmd+=(-c "mcp_servers.$server.startup_timeout_sec=$TIMEOUT_SEC")
  cmd+=("$PROMPT_TEXT")

  start_epoch="$(date +%s)"
  if CODEX_HOME="$CODEX_HOME_DIR" "${cmd[@]}" >"$logfile" 2>&1; then
    exit_code=0
  else
    exit_code=$?
  fi
  end_epoch="$(date +%s)"
  duration_sec=$((end_epoch - start_epoch))

  status="UNKNOWN"
  note="-"

  if rg -q "mcp: ${server} failed: MCP client for \`${server}\` timed out after" "$logfile"; then
    status="MCP_TIMEOUT"
    note="$(rg -n "mcp: ${server} failed: MCP client for \`${server}\` timed out after" "$logfile" | head -n 1 | cut -d: -f2-)"
  elif rg -q "mcp: ${server} failed:" "$logfile"; then
    status="MCP_FAILED"
    note="$(rg -n "mcp: ${server} failed:" "$logfile" | head -n 1 | cut -d: -f2-)"
  elif rg -q "mcp: ${server} starting" "$logfile"; then
    if rg -q "mcp startup: failed" "$logfile"; then
      status="STARTUP_FAILED"
      note="$(rg -n "mcp startup: failed" "$logfile" | head -n 1 | cut -d: -f2-)"
    else
      status="MCP_OK"
    fi
  fi

  if rg -q "Reconnecting|stream disconnected|Operation timed out|error sending request for url" "$logfile"; then
    if [[ "$note" == "-" ]]; then
      note="$(rg -n "Reconnecting|stream disconnected|Operation timed out|error sending request for url" "$logfile" | head -n 1 | cut -d: -f2-)"
    fi
    if [[ "$status" == "UNKNOWN" || "$status" == "MCP_OK" ]]; then
      status="NETWORK_UNSTABLE"
    fi
  fi

  echo -e "${server}\t${status}\t${exit_code}\t${duration_sec}\t${note}\t${logfile}" >> "$SUMMARY_TSV"
done

echo
echo "Summary:"
awk -F '\t' '
  NR==1 {
    printf "%-22s %-16s %-9s %-11s %s\n", "SERVER", "STATUS", "EXIT", "DURATION(s)", "LOG"
    next
  }
  {
    printf "%-22s %-16s %-9s %-11s %s\n", $1, $2, $3, $4, $6
  }
' "$SUMMARY_TSV"

echo
echo "Detailed TSV: $SUMMARY_TSV"
echo "Tip: rg -n \"mcp: .*failed|timed out|Reconnecting|stream disconnected\" \"$OUTPUT_DIR\"/*.log"
