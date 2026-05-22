import json
import os
import threading
from datetime import datetime

from core.paths import log_dir

MAX_ENTRIES = 300
_lock = threading.Lock()


def log_path():
    return os.path.join(log_dir(), "activity_log.json")


def read_logs():
    path = log_path()
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("entries", [])
    except (OSError, json.JSONDecodeError):
        return []


def append_log(event, detail="", client=""):
    entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": event,
        "detail": detail,
        "client": client,
    }
    with _lock:
        logs = read_logs()
        logs.append(entry)
        logs = logs[-MAX_ENTRIES:]
        path = log_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"entries": logs}, f, ensure_ascii=False, indent=0)


def clear_logs():
    with _lock:
        path = log_path()
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"entries": []}, f)


def format_logs_text(entries, empty_msg="No activity yet."):
    if not entries:
        return empty_msg
    lines = []
    for e in entries:
        client = f" [{e['client']}]" if e.get("client") else ""
        detail = f" — {e['detail']}" if e.get("detail") else ""
        lines.append(f"{e['time']}  {e['event']}{client}{detail}")
    return "\n".join(reversed(lines))
