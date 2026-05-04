# tmux-claude-quota-auto-continue

在同一个 tmux pane 中监控 Claude CLI 输出，当检测到 5 小时配额/限额提示后自动等待并发送 `continue`。

## 功能

- 监控指定 pane 的最近输出（`tmux capture-pane`）
- 识别限额关键字（`rate limit`、`quota exceeded`、`5 hour limit`、`five hours`、`reset at` 等）
- 自动解析 reset 时间（支持简单时间文本），解析失败时按默认等待时长
- 到点后在同一 pane 执行：`continue` + 回车
- 防重复触发（基于 pane + 事件指纹）
- 结构化日志（JSONL）

## 目录结构

```text
.
├── README.md
├── config.example.toml
├── scripts/
│   └── tmux_claude_quota_auto_continue.py
└── LICENSE
```

## 依赖

- Python 3.10+
- tmux（脚本通过 `tmux` CLI 调用，无需额外 Python 包）

## 快速开始

1. 在 tmux 里启动 Claude：

```bash
tmux new-session -d -s claude_session
tmux send-keys -t claude_session "claude" C-m
```

2. 复制配置并按需调整：

```bash
cp config.example.toml config.toml
```

3. 启动监控（默认目标：当前 pane）：

```bash
python3 scripts/tmux_claude_quota_auto_continue.py --config config.toml
```

或显式指定目标 pane：

```bash
python3 scripts/tmux_claude_quota_auto_continue.py --target claude_session:0.0 --config config.toml
```

## 配置说明

`config.example.toml` 支持：

- `poll_interval_seconds`：轮询间隔（默认 30）
- `capture_lines`：每次捕获的历史行数（默认 200）
- `default_wait_seconds`：无法解析 reset 时间时等待时长（默认 5h+60s）
- `wait_buffer_seconds`：解析出 reset 时间后的附加 buffer
- `log_file`：日志输出路径（JSONL）
- `lock_file`：去重状态文件路径
- `keywords`：限额关键词列表（可扩展）

## 日志样例

```json
{"ts":"2026-05-04T12:00:00Z","event":"limit_detected","target":"claude_session:0.0","wait_seconds":18210,"reason":"matched_keyword:5 hour limit"}
{"ts":"2026-05-04T17:03:30Z","event":"continue_sent","target":"claude_session:0.0","command":"continue"}
```

## 可扩展建议

- 多 pane 并行：以多个 `--target` 启动，或扩展为线程/async 管理器
- 通知集成：在 `continue_sent`/`limit_detected` 事件处挂接 Slack/Webhook
- TUI 面板：展示各 pane 的检测状态和下一次发送时间
