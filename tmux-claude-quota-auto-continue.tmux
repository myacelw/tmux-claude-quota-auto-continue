#!/usr/bin/env bash
set -euo pipefail

CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

key="$(tmux show-option -gqv @claude_quota_key)"
if [[ -z "$key" ]]; then
  key="q"
fi

status_off="$(tmux show-option -gqv @claude_quota_status_off)"
if [[ "$status_off" != "1" ]]; then
  current_status="$(tmux show-option -gqv status-right)"
  marker='#{?@claude_quota_enabled,#[fg=green]CQ:ON#[default],#[fg=colour244]CQ:OFF#[default]}'
  if [[ "$current_status" != *"CQ:ON"* && "$current_status" != *"CQ:OFF"* ]]; then
    tmux set-option -g status-right "$current_status #[default]| $marker"
  fi
fi

no_prefix="$(tmux show-option -gqv @claude_quota_no_prefix)"
if [[ "$no_prefix" == "1" ]]; then
  tmux bind-key -n "$key" run-shell -b "$CURRENT_DIR/scripts/toggle-monitor.sh '$CURRENT_DIR'"
else
  tmux bind-key "$key" run-shell -b "$CURRENT_DIR/scripts/toggle-monitor.sh '$CURRENT_DIR'"
fi
