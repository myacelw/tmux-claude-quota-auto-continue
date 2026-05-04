# tmux-claude-quota-auto-continue

A tmux plugin that monitors Claude/Codex quota-limit messages and automatically sends `continue` in the same pane after reset.

## Install via TPM

Add this to `~/.tmux.conf`:

```tmux
set -g @plugin 'myacelw/tmux-claude-quota-auto-continue'
run '~/.tmux/plugins/tpm/tpm'
```

Then press `prefix + I` inside tmux to install.

## Manual local load

```tmux
run-shell /path/to/repo/tmux-claude-quota-auto-continue.tmux
```

## Usage

- Default hotkey: `prefix + Q` (uppercase `Q`). You can customize it with:
  `set -g @claude_quota_key Q`
- First press: enable monitor (`CQ:ON`)
- Press again: disable monitor (`CQ:OFF`)
- If you really want no-prefix binding, set:
  `set -g @claude_quota_no_prefix 1`

## Configuration

A default `config.toml` is included and ready to use.
To reset from template:

```bash
cp config.example.toml config.toml
```

Supported behavior:
- Regex `message_patterns` (recommended to include `(?P<reset_time>...)`)
- If reset time cannot be parsed, event is skipped and no `continue` is sent
- Re-check pane state before sending `continue`
- If `log_file` / `lock_file` are relative paths, they are resolved relative to `config.toml`; default log file is `quota-monitor.log.jsonl`
