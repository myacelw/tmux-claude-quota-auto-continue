#!/usr/bin/env bash
set -euo pipefail

CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$CURRENT_DIR/../.." && pwd)"

key="$(tmux show-option -gqv @claude_quota_key)"
if [[ -z "$key" ]]; then
  key="C-q"
fi

# 默认在状态栏右侧追加开关指示，可通过 @claude_quota_status_off 关闭
status_off="$(tmux show-option -gqv @claude_quota_status_off)"
if [[ "$status_off" != "1" ]]; then
  current_status="$(tmux show-option -gqv status-right)"
  marker='#{?@claude_quota_enabled,#[fg=green]CQ:ON#[default],#[fg=colour244]CQ:OFF#[default]}'
  if [[ "$current_status" != *"CQ:ON"* ]]; then
    tmux set-option -g status-right "$current_status #[default]| $marker"
  fi
fi

tmux bind-key "$key" run-shell -b "$CURRENT_DIR/scripts/toggle-monitor.sh '$REPO_ROOT'"
