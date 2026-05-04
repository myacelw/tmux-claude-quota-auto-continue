# tmux-claude-quota-auto-continue

这是一个 tmux 插件风格监控器：默认监控当前 session 全部 pane，检测 Claude/Codex 限额文本并在重置后自动发送 `continue`。

## 关键更新（正则匹配）

- 限额识别从“关键词”升级为“**可配置正则**（`message_patterns`）”。
- 支持匹配类似：`You've hit your limit · resets 12:10am (Asia/Shanghai)`。
- 推荐在正则中提供命名分组 `(?P<reset_time>...)`，脚本会优先用该分组解析重置时间。
- 若未解析出 reset 时间：跳过本次，不发送 `continue`。
- 到达等待时间后会再次检查 pane 是否仍为限额提示，若已退出/有其他操作则跳过发送。

## 安装

在 `.tmux.conf` 中：

```tmux
run-shell /path/to/repo/plugins/tmux-claude-quota-auto-continue/tmux-claude-quota-auto-continue.tmux
```

重载：

```bash
tmux source-file ~/.tmux.conf
```

## 使用

- 默认快捷键：`Ctrl-q`
- 第一次按下：启动（`CQ:ON`）
- 再按一次：关闭（`CQ:OFF`）

## 配置

复制模板：

```bash
cp config.example.toml config.toml
```

主要配置：
- `poll_interval_seconds`
- `capture_lines`
- `wait_buffer_seconds`
- `message_patterns`（正则列表，建议包含 `reset_time` 命名分组）

状态栏/快捷键：
- `@claude_quota_key`：改快捷键
- `@claude_quota_status_off=1`：关闭状态栏指示注入
