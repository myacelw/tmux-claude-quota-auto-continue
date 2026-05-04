# tmux-claude-quota-auto-continue

这是一个 tmux 插件风格的监控器：默认以当前 session 为范围监控全部 pane，识别 Claude 限额提示，等待 reset 后自动在原 pane 发送 `continue`。

## 特性

- 默认监控当前 session 的全部 pane
- 支持快捷键 **开/关切换** 监控
- 状态栏指示：`CQ:ON / CQ:OFF`
- 识别关键词：`rate limit`、`quota exceeded`、`5 hour limit`、`five hours`、`reset at`、`resets`
- 可解析 reset 时间（如 `12:10am`），失败回退默认等待
- JSONL 日志记录 + 状态去重

## 文件结构

```text
.
├── config.example.toml
├── scripts/
│   └── tmux_claude_quota_auto_continue.py
└── plugins/
    └── tmux-claude-quota-auto-continue/
        ├── tmux-claude-quota-auto-continue.tmux
        └── scripts/toggle-monitor.sh
```

## 安装与使用

1. 复制配置：
```bash
cp config.example.toml config.toml
```

2. 在 `.tmux.conf` 里加载插件脚本：
```tmux
run-shell /path/to/repo/plugins/tmux-claude-quota-auto-continue/tmux-claude-quota-auto-continue.tmux
```

3. 重载 tmux 配置：
```bash
tmux source-file ~/.tmux.conf
```

4. 在任意 session 中按快捷键（默认 `Ctrl-q`）：
- 第一次按：启动监控（CQ:ON）
- 再按一次：关闭监控（CQ:OFF）

## 可配置项

- `@claude_quota_key`：快捷键（默认 `C-q`）
- `@claude_quota_status_off`：设为 `1` 可禁用状态栏指示注入
- `TMUX_CLAUDE_QUOTA_CONFIG`：配置文件路径（默认 `repo/config.toml`）
- `TMUX_CLAUDE_QUOTA_PID_DIR`：pid 文件目录（默认 `~/.cache/tmux-claude-quota`）

## 配置文件

见 `config.example.toml`：
- `poll_interval_seconds`
- `capture_lines`
- `default_wait_seconds`
- `wait_buffer_seconds`
- `log_file`
- `lock_file`
- `keywords`
