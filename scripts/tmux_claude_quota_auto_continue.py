#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit("Python 3.11+ is required.") from exc

RESET_PATTERNS = [
    re.compile(r"reset(?:s)?\s+(?:at\s+)?([0-9]{1,2}:[0-9]{2}\s*(?:am|pm)?)", re.IGNORECASE),
    re.compile(r"reset(?:s)?\s+(?:at\s+)?([0-9]{1,2}\s*(?:am|pm))", re.IGNORECASE),
]


def run_tmux(args: list[str]) -> str:
    proc = subprocess.run(["tmux", *args], text=True, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or f"tmux failed: {' '.join(args)}")
    return proc.stdout


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as f:
        return tomllib.load(f)


def write_log(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": now_iso(), **payload}, ensure_ascii=False) + "\n")


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


def list_session_panes(session_name: str) -> list[str]:
    out = run_tmux(["list-panes", "-t", session_name, "-a", "-F", "#{pane_id}"])
    return [line.strip() for line in out.splitlines() if line.strip()]


def capture_pane(pane: str, lines: int) -> str:
    return run_tmux(["capture-pane", "-p", "-t", pane, "-S", f"-{lines}"])


def detect_limit(text: str, keywords: list[str]) -> tuple[bool, str]:
    low = text.lower()
    for kw in keywords:
        if kw.lower() in low:
            return True, f"keyword:{kw}"
    return False, ""


def parse_wait_seconds(text: str, buffer_seconds: int) -> int | None:
    now = dt.datetime.now()
    for pattern in RESET_PATTERNS:
        match = pattern.search(text)
        if not match:
            continue
        raw = match.group(1).strip().lower().replace(" ", "")
        for fmt in ["%I:%M%p", "%I%p"]:
            try:
                parsed = dt.datetime.strptime(raw, fmt).time()
                cand = now.replace(hour=parsed.hour, minute=parsed.minute, second=0, microsecond=0)
                if cand <= now:
                    cand += dt.timedelta(days=1)
                return int((cand - now).total_seconds()) + buffer_seconds
            except ValueError:
                continue
    return None


def send_continue(pane: str) -> None:
    run_tmux(["send-keys", "-t", pane, "continue", "C-m"])


def fp(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", required=True, help="tmux session name")
    parser.add_argument("--config", default="config.toml")
    args = parser.parse_args()

    cfg = load_toml(Path(args.config))
    poll = int(cfg.get("poll_interval_seconds", 30))
    lines = int(cfg.get("capture_lines", 200))
    default_wait = int(cfg.get("default_wait_seconds", 18060))
    buffer_s = int(cfg.get("wait_buffer_seconds", 60))
    log_file = Path(cfg.get("log_file", "./quota-monitor.log.jsonl"))
    state_file = Path(cfg.get("lock_file", "./quota-monitor.state.json"))
    keywords = list(cfg.get("keywords", []))

    write_log(log_file, {"event": "monitor_started", "session": args.session})
    while True:
        panes = list_session_panes(args.session)
        state = load_state(state_file)
        for pane in panes:
            pane_output = capture_pane(pane, lines)
            ok, reason = detect_limit(pane_output, keywords)
            if not ok:
                continue
            sig = fp(reason + pane_output[-1000:])
            pane_state = state.get(pane, {})
            until = pane_state.get("wait_until", 0)
            if pane_state.get("last_sig") == sig and time.time() < until:
                continue

            wait_s = parse_wait_seconds(pane_output, buffer_s) or default_wait
            wait_until = int(time.time()) + wait_s
            state[pane] = {"last_sig": sig, "wait_until": wait_until}
            save_state(state_file, state)
            write_log(log_file, {"event": "limit_detected", "session": args.session, "pane": pane, "reason": reason, "wait_seconds": wait_s})

        state = load_state(state_file)
        now = int(time.time())
        changed = False
        for pane, pane_state in list(state.items()):
            if now < int(pane_state.get("wait_until", 0)):
                continue
            if pane_state.get("sent_for_sig") == pane_state.get("last_sig"):
                continue
            send_continue(pane)
            pane_state["sent_for_sig"] = pane_state.get("last_sig")
            state[pane] = pane_state
            changed = True
            write_log(log_file, {"event": "continue_sent", "session": args.session, "pane": pane})
        if changed:
            save_state(state_file, state)

        time.sleep(poll)


if __name__ == "__main__":
    raise SystemExit(main())
