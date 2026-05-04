#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT="$1"
SESSION_NAME="$(tmux display-message -p '#S')"
CONFIG_PATH="${TMUX_CLAUDE_QUOTA_CONFIG:-$REPO_ROOT/config.toml}"
PID_DIR="${TMUX_CLAUDE_QUOTA_PID_DIR:-$HOME/.cache/tmux-claude-quota}"
PID_FILE="$PID_DIR/${SESSION_NAME}.pid"
mkdir -p "$PID_DIR"

stop_monitor() {
  if [[ -f "$PID_FILE" ]]; then
    old_pid="$(cat "$PID_FILE")"
    if kill -0 "$old_pid" 2>/dev/null; then
      kill "$old_pid" || true
    fi
    rm -f "$PID_FILE"
  fi
  tmux set-option -t "$SESSION_NAME" -q @claude_quota_enabled 0
  tmux display-message "quota monitor stopped for session: $SESSION_NAME"
}

start_monitor() {
  nohup python3 "$REPO_ROOT/scripts/tmux_claude_quota_auto_continue.py" --session "$SESSION_NAME" --config "$CONFIG_PATH" >/dev/null 2>&1 &
  echo $! > "$PID_FILE"
  tmux set-option -t "$SESSION_NAME" -q @claude_quota_enabled 1
  tmux display-message "quota monitor started for session: $SESSION_NAME"
}

if [[ -f "$PID_FILE" ]]; then
  old_pid="$(cat "$PID_FILE")"
  if kill -0 "$old_pid" 2>/dev/null; then
    stop_monitor
    exit 0
  fi
fi

start_monitor
