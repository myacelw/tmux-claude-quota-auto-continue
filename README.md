# tmux-claude-quota-auto-continue

tmux 插件：监控 Claude/Codex 限额文本，重置后自动在原 pane 发送 `continue`。

## TPM 安装方式（tmux-plugins 风格）

TPM 约定会优先加载与仓库同名的入口脚本。当前仓库名为 `claude-tmux-retry`，因此提供了 `claude-tmux-retry.tmux` 作为入口包装器。

在 `~/.tmux.conf` 中添加：

```tmux
set -g @plugin 'myacelw/claude-tmux-retry'
run '~/.tmux/plugins/tpm/tpm'
```

然后在 tmux 中按 `prefix + I` 安装。

仓库地址：`https://github.com/myacelw/claude-tmux-retry`

## 本地手动加载

```tmux
run-shell /path/to/repo/tmux-claude-quota-auto-continue.tmux
```

## 使用

- 默认快捷键：`prefix + q`
- 第一次按下：启动（`CQ:ON`）
- 再按一次：关闭（`CQ:OFF`）
- 若你确实想用无前缀按键，可设置：`set -g @claude_quota_no_prefix 1`

## 配置

仓库已提供默认 `config.toml`，可直接使用。
如需重置为模板：

```bash
cp config.example.toml config.toml
```

支持：
- 正则 `message_patterns`（建议 `(?P<reset_time>...)`）
- 解析不到 reset 时间时跳过，不发送 continue
- 发送前再次确认 pane 仍为限额状态

### 状态栏标记不显示排查

1. 先确认已 reload：`tmux source-file ~/.tmux.conf`。
2. 确认没关闭注入：`@claude_quota_status_off` 不应为 `1`。
3. 如果你在插件加载后又重写了 `status-right`，需要把插件放到配置最后，或手动保留 `CQ:ON/CQ:OFF` 片段。
