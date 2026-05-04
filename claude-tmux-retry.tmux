#!/usr/bin/env bash
# TPM loads <repo_name>.tmux by convention for each plugin.
# Keep this thin wrapper so repository name and plugin entry stay aligned.
CURRENT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$CURRENT_DIR/tmux-claude-quota-auto-continue.tmux"
