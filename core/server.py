"""HTTP server ringan (stdlib) untuk transfer file."""

import http.server
import json
import os
import re
import shutil
import socket
import socketserver
import sys
import threading
from urllib.parse import unquote

from log.activity_log import append_log, read_logs
from .i18n import get_language, load_locale_file
from .paths import app_data_dir, outgoing_dir, res_dir
from .version import APP_NAME, APP_TAGLINE, APP_VERSION

DEFAULT_PORT = 8000


def ensure_data_files(bundle, data):
    os.makedirs(data, exist_ok=True)
    defaults = {
        "config.json": {
            "upload_folder": "",
            "server_port": DEFAULT_PORT,
            "language": "id",
        },
        "server_data.json": {
            "connected_devices": 0,
            "uploaded_files": 0,
            "upload_progress": 0,
            "uploading": False,
            "current_file": "",
        },
    }
    for name, default in defaults.items():
        dest = os.path.join(data, name)
        if os.path.exists(dest):
            continue
        src = os.path.join(bundle, name)
        if os.path.exists(src):
            shutil.copy2(src, dest)
        else:
            with open(dest, "w", encoding="utf-8") as f:
                json.dump(default, f)


def read_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)


def list_outgoing_files():
    folder = outgoing_dir()
    items = []
    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            items.append({
                "name": name,
                "size": os.path.getsize(path),
            })
    items.sort(key=lambda x: x["name"].lower())
    return items


def clear_outgoing_files():
    """Kosongkan antrian kirim PC→HP (saat server dihentikan)."""
    folder = outgoing_dir()
    for name in os.listdir(folder):
        path = os.path.join(folder, name)
        if os.path.isfile(path):
            try:
                os.remove(path)
            except OSError:
                pass


def safe_outgoing_path(filename):
    name = os.path.basename(filename.replace("\\", "/"))
    if not name or name in (".", ".."):
        return None
    folder = os.path.realpath(outgoing_dir())
    path = os.path.realpath(os.path.join(folder, name))
    if not path.startswith(folder + os.sep) and path != folder:
        return None
    if not os.path.isfile(path):
        return None
    return path


def get_upload_folder(data_dir):
    config_path = os.path.join(data_dir, "config.json")
    config = read_json(config_path)
    folder = (config.get("upload_folder") or "").strip()
    if not folder:
        folder = os.path.join(data_dir, "uploads")
    os.makedirs(folder, exist_ok=True)
    return folder


def find_free_port(start=DEFAULT_PORT, attempts=50):
    for port in range(start, start + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("0.0.0.0", port))
                return port
            except OSError:
                continue
    return None


def port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.3)
        return s.connect_ex(("127.0.0.1", port)) == 0


def get_config_port(data_dir):
    config_path = os.path.join(data_dir, "config.json")
    try:
        config = read_json(config_path)
        return int(config.get("server_port", DEFAULT_PORT))
    except (ValueError, TypeError, OSError):
        return DEFAULT_PORT


def save_config_port(data_dir, port):
    config_path = os.path.join(data_dir, "config.json")
    config = {}
    if os.path.exists(config_path):
        config = read_json(config_path)
    config["server_port"] = port
    write_json(config_path, config)


def _strip_part_tail(data):
    while data.endswith(b"\r\n"):
        data = data[:-2]
    while data.endswith(b"\n"):
        data = data[:-1]
    return data


def parse_multipart(body, content_type):
    match = re.search(r'boundary=(?:"([^"]+)"|([^\s;]+))', content_type, re.I)
    if not match:
        return None, None
    boundary = (match.group(1) or match.group(2)).encode()
    delimiter = b"--" + boundary
    parts = body.split(delimiter)
    for part in parts:
        if b"filename=" not in part and b"filename*=" not in part:
            continue
        header_block = part
        data = b""
        for sep in (b"\r\n\r\n", b"\n\n"):
            idx = part.find(sep)
            if idx != -1:
                header_block = part[:idx]
                data = part[idx + len(sep) :]
                break
        if not data:
            continue
        data = _strip_part_tail(data)
        headers = header_block.decode("utf-8", errors="ignore")
        name_match = re.search(r'filename="([^"]*)"', headers)
        if name_match:
            filename = name_match.group(1)
        else:
            utf_match = re.search(r"filename\*=UTF-8''(.+)", headers, re.I)
            if utf_match:
                filename = unquote(utf_match.group(1))
            else:
                continue
        if filename:
            return os.path.basename(filename.replace("\\", "/")), data
    return None, None


def unique_path(folder, filename):
    base, ext = os.path.splitext(filename)
    path = os.path.join(folder, filename)
    if not os.path.exists(path):
        return path
    n = 1
    while True:
        candidate = os.path.join(folder, f"{base}_{n}{ext}")
        if not os.path.exists(candidate):
            return candidate
        n += 1


class TransferHandler(http.server.BaseHTTPRequestHandler):
    bundle_dir = ""
    data_dir = ""
    server_data_path = ""
    config_path = ""
    _data_lock = threading.Lock()

    def log_message(self, format, *args):
        pass

    def _send_json(self, data, code=200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_file(self, path, content_type):
        with open(path, "rb") as f:
            body = f.read()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _update_status(self, **kwargs):
        with self._data_lock:
            payload = read_json(self.server_data_path)
            payload.update(kwargs)
            write_json(self.server_data_path, payload)

    def _read_upload_body(self, filename_header):
        length = int(self.headers.get("Content-Length", 0))
        if filename_header:
            filename = os.path.basename(unquote(filename_header))
            return filename, self.rfile.read(length)

        content_type = self.headers.get("Content-Type", "")
        body = self.rfile.read(length)
        if "multipart/form-data" in content_type:
            return parse_multipart(body, content_type)
        return None, None

    def _client_ip(self):
        return self.client_address[0] if self.client_address else ""

    def _save_upload(self, filename, file_data):
        upload_folder = get_upload_folder(self.data_dir)
        if not file_data:
            return None, "File kosong"

        file_path = unique_path(upload_folder, filename)
        safe_name = os.path.basename(file_path)
        client = self._client_ip()
        append_log(
            "upload_start",
            f"{safe_name} ({len(file_data)} bytes)",
            client,
        )

        self._update_status(
            uploading=True,
            upload_progress=0,
            current_file=safe_name,
        )

        total = len(file_data)
        chunk = 256 * 1024
        uploaded = 0
        try:
            with open(file_path, "wb") as f:
                for i in range(0, total, chunk):
                    part = file_data[i : i + chunk]
                    f.write(part)
                    uploaded += len(part)
                    percent = int((uploaded / total) * 100) if total else 100
                    self._update_status(upload_progress=percent)
        except OSError as e:
            append_log("upload_fail", str(e), client)
            self._update_status(uploading=False, current_file="", upload_progress=0)
            return None, str(e)

        with self._data_lock:
            payload = read_json(self.server_data_path)
            payload["uploaded_files"] = payload.get("uploaded_files", 0) + 1
            payload["upload_progress"] = 100
            payload["uploading"] = False
            payload["current_file"] = ""
            write_json(self.server_data_path, payload)

        append_log("upload_ok", os.path.basename(file_path), client)
        return file_path, None

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, X-Filename")
        self.end_headers()

    def do_GET(self):
        path = unquote(self.path.split("?", 1)[0])

        if path == "/api/info":
            lang = get_language(self.data_dir, self.bundle_dir)
            loc = load_locale_file(self.bundle_dir, lang)
            self._send_json({
                "name": loc.get("app_name", APP_NAME),
                "tagline": loc.get("app_tagline", APP_TAGLINE),
                "version": APP_VERSION,
                "language": lang,
            })
            return

        if path == "/api/i18n":
            lang = get_language(self.data_dir, self.bundle_dir)
            loc = load_locale_file(self.bundle_dir, lang)
            strings = {k: loc[k] for k in loc if k.startswith("web_")}
            self._send_json({"language": lang, "strings": strings})
            return

        if path == "/api/logs":
            self._send_json({"entries": read_logs()})
            return

        if path == "/api/outgoing":
            files = list_outgoing_files()
            self._send_json({
                "files": [
                    {
                        "name": f["name"],
                        "size": f["size"],
                        "url": f"/download/{f['name']}",
                    }
                    for f in files
                ]
            })
            return

        if path.startswith("/download/"):
            rel = unquote(path[10:])
            file_path = safe_outgoing_path(rel)
            if not file_path:
                self.send_error(404)
                return
            client = self._client_ip()
            append_log("download_start", os.path.basename(file_path), client)
            try:
                with open(file_path, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header(
                    "Content-Type", "application/octet-stream"
                )
                self.send_header(
                    "Content-Disposition",
                    f'attachment; filename="{os.path.basename(file_path)}"',
                )
                self.send_header("Content-Length", str(len(body)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(body)
                append_log("download_ok", os.path.basename(file_path), client)
            except OSError as e:
                append_log("download_fail", str(e), client)
                self.send_error(500)
            return

        if path == "/api/status":
            with self._data_lock:
                payload = read_json(self.server_data_path)
            payload["server_running"] = True
            self._send_json(payload)
            return

        if path == "/":
            client = self._client_ip()
            append_log("client_connect", self.path, client)
            with self._data_lock:
                payload = read_json(self.server_data_path)
                payload["connected_devices"] = payload.get("connected_devices", 0) + 1
                write_json(self.server_data_path, payload)
            index = os.path.join(self.bundle_dir, "web", "index.html")
            self._send_file(index, "text/html; charset=utf-8")
            return

        if path.startswith("/web/"):
            rel = path[5:]
            file_path = os.path.join(self.bundle_dir, "web", rel)
            if os.path.isfile(file_path):
                if rel.endswith(".css"):
                    ctype = "text/css; charset=utf-8"
                elif rel.endswith(".js"):
                    ctype = "application/javascript; charset=utf-8"
                else:
                    ctype = "text/html; charset=utf-8"
                self._send_file(file_path, ctype)
                return

        if path.startswith("/locales/"):
            rel = path[9:]
            file_path = os.path.join(self.bundle_dir, "locales", rel)
            if os.path.isfile(file_path) and rel.endswith(".json"):
                self._send_file(file_path, "application/json; charset=utf-8")
                return

        if path.startswith("/assets/"):
            rel = path[8:]
            file_path = os.path.join(self.bundle_dir, "assets", rel)
            if os.path.isfile(file_path):
                ctype = "image/png" if rel.endswith(".png") else "application/octet-stream"
                self._send_file(file_path, ctype)
                return

        self.send_error(404)

    def do_POST(self):
        if self.path.split("?", 1)[0] != "/upload":
            self.send_error(404)
            return

        filename_header = self.headers.get("X-Filename", "")
        filename, file_data = self._read_upload_body(filename_header)

        if not filename or file_data is None:
            append_log(
                "upload_fail",
                "file not readable",
                self._client_ip(),
            )
            self._send_json({"message": "Upload gagal: file tidak terbaca"}, 400)
            return

        saved_path, err = self._save_upload(filename, file_data)
        if err:
            self._send_json({"message": f"Upload gagal: {err}"}, 500)
            return

        self._send_json({
            "message": "Upload Success",
            "saved_to": saved_path,
            "filename": os.path.basename(saved_path),
        })


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def queue_outgoing_file(source_path):
    """Salin file ke antrian kirim (PC → HP)."""
    name = os.path.basename(source_path)
    dest = unique_path(outgoing_dir(), name)
    shutil.copy2(source_path, dest)
    append_log("share_queued", os.path.basename(dest), "")
    return dest


class HttpTransferServer:
    def __init__(self, bundle, data, port):
        self.bundle = bundle
        self.data = data
        self.port = port
        self.httpd = None
        self._thread = None

    @classmethod
    def prepare_handler(cls, bundle, data):
        ensure_data_files(bundle, data)
        TransferHandler.bundle_dir = bundle  # res/
        TransferHandler.data_dir = data
        TransferHandler.config_path = os.path.join(data, "config.json")
        TransferHandler.server_data_path = os.path.join(data, "server_data.json")
        get_upload_folder(data)
        return TransferHandler

    def start_background(self):
        handler = self.prepare_handler(self.bundle, self.data)
        self.httpd = ThreadedHTTPServer(("0.0.0.0", self.port), handler)
        self._thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
            self.httpd = None
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=3)
        self._thread = None


def reset_server_stats(data_dir):
    path = os.path.join(data_dir, "server_data.json")
    write_json(
        path,
        {
            "connected_devices": 0,
            "uploaded_files": 0,
            "upload_progress": 0,
            "uploading": False,
            "current_file": "",
        },
    )


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    ip = s.getsockname()[0]
    s.close()
    return ip


def resolve_port(data_dir):
    preferred = get_config_port(data_dir)
    if not port_in_use(preferred):
        return preferred
    free = find_free_port(preferred + 1)
    if free is None:
        free = find_free_port(1024)
    return free
