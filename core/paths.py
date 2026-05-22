"""Path aplikasi: res/ (bundle), data/ (runtime), log/ (aktivitas)."""

import os
import shutil
import sys

_CORE_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_CORE_DIR)

_LEGACY_FILES = (
    "config.json",
    "server_data.json",
    "activity_log.json",
)


def res_dir():
    """Resource statis: web, locales, assets."""
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "res")
    return os.path.join(_PROJECT_ROOT, "res")


def _data_dir_path():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    path = os.path.join(_PROJECT_ROOT, "data")
    os.makedirs(path, exist_ok=True)
    return path


def _migrate_legacy_files(data_dir):
    """Pindahkan config/log lama dari root atau core/ ke data/."""
    sources = [_PROJECT_ROOT, _CORE_DIR]
    for name in _LEGACY_FILES:
        dest = os.path.join(data_dir, name)
        if os.path.exists(dest):
            continue
        for base in sources:
            src = os.path.join(base, name)
            if os.path.isfile(src):
                shutil.copy2(src, dest)
                break
    log_sub = os.path.join(data_dir, "log")
    os.makedirs(log_sub, exist_ok=True)
    new_log = os.path.join(log_sub, "activity_log.json")
    for src in (
        os.path.join(_PROJECT_ROOT, "activity_log.json"),
        os.path.join(_CORE_DIR, "activity_log.json"),
        os.path.join(data_dir, "activity_log.json"),
    ):
        if os.path.isfile(src) and not os.path.isfile(new_log):
            shutil.copy2(src, new_log)
            break


def app_data_dir():
    """Data runtime: config, status server, antrian kirim ke HP."""
    path = _data_dir_path()
    if not getattr(sys, "frozen", False):
        _migrate_legacy_files(path)
    return path


def log_dir():
    """Log aktivitas (di dalam data/)."""
    path = os.path.join(_data_dir_path(), "log")
    os.makedirs(path, exist_ok=True)
    return path


def outgoing_dir():
    """Antrian file dari PC ke perangkat client (HP)."""
    path = os.path.join(_data_dir_path(), "outgoing")
    os.makedirs(path, exist_ok=True)
    return path


def bundle_dir():
    """Alias untuk kompatibilitas modul lama."""
    return res_dir()
