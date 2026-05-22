import json
import os
import threading
from datetime import datetime

MAX_ENTRIES = 300
_lock = threading.Lock()


def log_path(data_dir):
    return os.path.join(data_dir, "activity_log.json")


def read_logs(data_dir):
    path = log_path(data_dir)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get("entries", [])
    except (OSError, json.JSONDecodeError):
        return []


def append_log(data_dir, event, detail="", client=""):
    entry = {
        "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "event": event,
        "detail": detail,
        "client": client,
    }
    with _lock:
        logs = read_logs(data_dir)
        logs.append(entry)
        logs = logs[-MAX_ENTRIES:]
        path = log_path(data_dir)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"entries": logs}, f, ensure_ascii=False, indent=0)


def clear_logs(data_dir):
    with _lock:
        path = log_path(data_dir)
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
