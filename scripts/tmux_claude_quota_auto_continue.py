#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    print("Python 3.11+ is required (tomllib missing).", file=sys.stderr)
    raise


RESET_PATTERNS = [
    re.compile(r"reset(?:s)?\s+(?:at\s+)?([0-9]{1,2}:[0-9]{2}\s*(?:am|pm)?)", re.IGNORECASE),
    re.compile(r"reset(?:s)?\s+(?:at\s+)?([0-9]{1,2}\s*(?:am|pm))", re.IGNORECASE),
]


def now_utc_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def run_tmux(args: list[str]) -> str:
    proc = subprocess.run(["tmux", *args], text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(f"tmux {' '.join(args)} failed: {proc.stderr.strip()}")
    return proc.stdout


def load_config(path: Path) -> dict[str, Any]:
    with path.open("rb") as f:
        cfg = tomllib.load(f)
    return cfg


def append_log(path: Path, payload: dict[str, Any]) -> None:
    payload = {"ts": now_utc_iso(), **payload}
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, ensure_ascii=False) + "\n")


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def capture_pane(target: str, lines: int) -> str:
    return run_tmux(["capture-pane", "-p", "-t", target, "-S", f"-{lines}"])


def parse_reset_wait_seconds(text: str, buffer_seconds: int) -> int | None:
    now = dt.datetime.now()
    for pattern in RESET_PATTERNS:
        m = pattern.search(text)
        if not m:
            continue
        raw = m.group(1).strip().lower()
        for fmt in ["%I:%M%p", "%I:%M %p", "%I%p"]:
            try:
                t = dt.datetime.strptime(raw.replace(" ", ""), fmt.replace(" ", "")).time()
                candidate = now.replace(hour=t.hour, minute=t.minute, second=0, microsecond=0)
                if candidate <= now:
                    candidate += dt.timedelta(days=1)
                delta = int((candidate - now).total_seconds()) + buffer_seconds
                return max(delta, buffer_seconds)
            except ValueError:
                continue
    return None


def detect_limit(text: str, keywords: list[str]) -> tuple[bool, str]:
    lower = text.lower()
    for kw in keywords:
        if kw.lower() in lower:
            return True, f"matched_keyword:{kw}"
    return False, ""


def fingerprint(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def send_continue(target: str) -> None:
    run_tmux(["send-keys", "-t", target, "continue", "C-m"])


def main() -> int:
    parser = argparse.ArgumentParser(description="Auto continue Claude in tmux after quota reset")
    parser.add_argument("--target", default=os.environ.get("TMUX_PANE", ""), help="tmux target pane, e.g. session:0.0")
    parser.add_argument("--config", default="config.toml", help="TOML config path")
    args = parser.parse_args()

    if not args.target:
        print("--target is required (or run inside tmux with TMUX_PANE).", file=sys.stderr)
        return 2

    cfg = load_config(Path(args.config))
    poll_interval = int(cfg.get("poll_interval_seconds", 30))
    capture_lines = int(cfg.get("capture_lines", 200))
    default_wait = int(cfg.get("default_wait_seconds", 18060))
    wait_buffer = int(cfg.get("wait_buffer_seconds", 60))
    log_file = Path(cfg.get("log_file", "./quota-monitor.log.jsonl"))
    state_file = Path(cfg.get("lock_file", "./quota-monitor.state.json"))
    keywords = list(cfg.get("keywords", []))

    append_log(log_file, {"event": "monitor_started", "target": args.target})

    while True:
        pane_output = capture_pane(args.target, capture_lines)
        matched, reason = detect_limit(pane_output, keywords)
        if not matched:
            time.sleep(poll_interval)
            continue

        sig = fingerprint(reason + pane_output[-1000:])
        state = load_state(state_file)
        pane_state = state.get(args.target, {})
        if pane_state.get("last_sig") == sig:
            time.sleep(poll_interval)
            continue

        wait_seconds = parse_reset_wait_seconds(pane_output, wait_buffer) or default_wait
        append_log(
            log_file,
            {
                "event": "limit_detected",
                "target": args.target,
                "reason": reason,
                "wait_seconds": wait_seconds,
            },
        )

        state[args.target] = {"last_sig": sig, "detected_at": now_utc_iso(), "wait_seconds": wait_seconds}
        save_state(state_file, state)

        time.sleep(wait_seconds)
        send_continue(args.target)
        append_log(log_file, {"event": "continue_sent", "target": args.target, "command": "continue"})


if __name__ == "__main__":
    raise SystemExit(main())
