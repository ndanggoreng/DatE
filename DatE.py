import sys
import socket
import json
import os
import time

from version import APP_VERSION
from i18n import I18n
from activity_log import append_log, read_logs, clear_logs
from server import (
    app_data_dir,
    bundle_dir,
    ensure_data_files,
    HttpTransferServer,
    port_in_use,
    resolve_port,
    save_config_port,
    reset_server_stats,
    get_upload_folder,
)

from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLabel,
    QMessageBox,
    QFileDialog,
    QProgressBar,
    QSizePolicy,
    QFrame,
    QDialog,
    QTextEdit,
    QComboBox,
)

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QGuiApplication, QIcon, QPixmap, QFont


def resource_path(relative_path):
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, relative_path)


class SettingsDialog(QDialog):

    def __init__(self, parent):
        super().__init__(parent)
        self.parent_window = parent
        self.i18n = parent.i18n
        self._build_ui()
        self._reload_log()
        self._apply_texts()

    def _build_ui(self):
        self.setMinimumSize(460, 420)
        self.setStyleSheet("""
            QDialog { background: #0f172a; color: #e2e8f0; }
            QLabel { color: #e2e8f0; }
            QTextEdit {
                background: #1e293b; color: #e2e8f0;
                border: none; border-radius: 8px;
                font-family: Consolas, monospace; font-size: 11px;
            }
            QComboBox {
                background: #1e293b; color: white;
                border-radius: 8px; padding: 6px;
            }
            QPushButton {
                background: #2563eb; color: white; border: none;
                border-radius: 8px; padding: 8px 14px; font-weight: 600;
            }
            QPushButton:hover { background: #3b82f6; }
            QPushButton#secondary { background: #475569; }
        """)

        layout = QVBoxLayout(self)
        layout.setSpacing(10)

        self.title_label = QLabel()
        self.title_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        layout.addWidget(self.title_label)

        lang_row = QHBoxLayout()
        self.lang_label = QLabel()
        lang_row.addWidget(self.lang_label)
        self.lang_combo = QComboBox()
        self.lang_combo.addItem("Indonesia", "id")
        self.lang_combo.addItem("English", "en")
        idx = self.lang_combo.findData(self.i18n.lang)
        if idx >= 0:
            self.lang_combo.setCurrentIndex(idx)
        self.lang_combo.currentIndexChanged.connect(self._language_changed)
        lang_row.addWidget(self.lang_combo, 1)
        layout.addLayout(lang_row)

        self.log_label = QLabel()
        layout.addWidget(self.log_label)

        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Consolas", 10))
        layout.addWidget(self.log_view, 1)

        btn_row = QHBoxLayout()
        self.refresh_btn = QPushButton()
        self.refresh_btn.clicked.connect(self._reload_log)
        btn_row.addWidget(self.refresh_btn)
        self.clear_btn = QPushButton()
        self.clear_btn.setObjectName("secondary")
        self.clear_btn.clicked.connect(self._clear_log)
        btn_row.addWidget(self.clear_btn)
        btn_row.addStretch()
        self.close_btn = QPushButton("OK")
        self.close_btn.clicked.connect(self.accept)
        btn_row.addWidget(self.close_btn)
        layout.addLayout(btn_row)

    def _apply_texts(self):
        t = self.i18n.t
        self.setWindowTitle(t("settings_title"))
        self.title_label.setText(f"{t('settings_title')} — v{APP_VERSION}")
        self.lang_label.setText(t("language") + ":")
        self.log_label.setText(t("activity_log"))
        self.refresh_btn.setText(t("refresh"))
        self.clear_btn.setText(t("clear_log"))

    def _format_entries(self, entries):
        lines = []
        for e in reversed(entries):
            key = f"log_event_{e['event']}"
            label = self.i18n.t(key) if key in self.i18n._strings else e["event"]
            client = f" [{e['client']}]" if e.get("client") else ""
            detail = f" — {e['detail']}" if e.get("detail") else ""
            lines.append(f"{e['time']}  {label}{client}{detail}")
        return "\n".join(lines) if lines else self.i18n.t("no_log")

    def _reload_log(self):
        entries = read_logs(app_data_dir())
        self.log_view.setPlainText(self._format_entries(entries))

    def _clear_log(self):
        clear_logs(app_data_dir())
        self._reload_log()

    def _language_changed(self):
        lang = self.lang_combo.currentData()
        if lang and lang != self.i18n.lang:
            self.i18n.set_language(lang)
            self.parent_window.apply_language()
            self._apply_texts()
            self._reload_log()


class DataTransfer(QWidget):

    def __init__(self):
        super().__init__()

        self._http_server = None
        self.server_port = None
        self.url = ""
        self.i18n = I18n(bundle_dir(), app_data_dir())

        self._build_ui()
        self.apply_language()
        self.load_config()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_live_data)
        self.timer.start(250)

    def _build_ui(self):
        self.setFixedSize(380, 540)
        self.setStyleSheet("""
            QWidget {
                background: #0f172a;
                color: #f8fafc;
                font-family: Segoe UI;
            }
            QLabel { color: #e2e8f0; }
            QPushButton {
                background: #2563eb;
                border: none;
                border-radius: 10px;
                padding: 10px 14px;
                font-size: 13px;
                font-weight: 600;
                color: white;
                min-height: 40px;
            }
            QPushButton:hover { background: #3b82f6; }
            QPushButton#danger {
                background: #dc2626;
            }
            QPushButton#danger:hover { background: #ef4444; }
            QPushButton#settingsBtn {
                background: #334155;
                min-height: 32px;
                max-height: 32px;
                padding: 4px 10px;
                font-size: 12px;
            }
            QPushButton#settingsBtn:hover { background: #475569; }
            QPushButton#copyBtn {
                background: #475569;
                min-height: 32px;
                max-height: 32px;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton#copyBtn:hover { background: #64748b; }
            QFrame#urlBox {
                background: #1e293b;
                border-radius: 10px;
            }
            QLabel#urlText {
                color: #e2e8f0;
                font-size: 13px;
            }
            QProgressBar {
                border: none;
                border-radius: 6px;
                background: #1e293b;
                height: 14px;
                color: white;
            }
            QProgressBar::chunk {
                background: #10b981;
                border-radius: 6px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(10)
        layout.setContentsMargins(20, 14, 20, 14)

        top_bar = QHBoxLayout()
        top_bar.addStretch()
        self.settings_btn = QPushButton("Settings")
        self.settings_btn.setObjectName("settingsBtn")
        self.settings_btn.setFixedHeight(32)
        self.settings_btn.clicked.connect(self.open_settings)
        top_bar.addWidget(self.settings_btn)
        layout.addLayout(top_bar)

        icon_path = resource_path(os.path.join("assets", "app_icon.png"))
        if os.path.exists(icon_path):
            logo = QLabel()
            logo.setPixmap(
                QPixmap(icon_path).scaled(
                    40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation
                )
            )
            logo.setAlignment(Qt.AlignCenter)
            layout.addWidget(logo)

        self.title = QLabel()
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        layout.addWidget(self.title)

        self.subtitle = QLabel()
        self.subtitle.setAlignment(Qt.AlignCenter)
        self.subtitle.setStyleSheet("font-size: 12px; color: #94a3b8;")
        layout.addWidget(self.subtitle)

        self.status = QLabel()
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("font-size: 14px; font-weight: bold;")
        layout.addWidget(self.status)

        url_box = QFrame()
        url_box.setObjectName("urlBox")
        url_box.setFixedHeight(48)
        url_layout = QHBoxLayout(url_box)
        url_layout.setContentsMargins(12, 8, 8, 8)
        url_layout.setSpacing(8)

        self.ip_label = QLabel()
        self.ip_label.setObjectName("urlText")
        self.ip_label.setAlignment(Qt.AlignCenter)
        self.ip_label.setWordWrap(False)
        self.ip_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        url_layout.addWidget(self.ip_label, 1)

        self.copy_btn = QPushButton()
        self.copy_btn.setObjectName("copyBtn")
        self.copy_btn.setFixedWidth(64)
        self.copy_btn.clicked.connect(self.copy_address)
        url_layout.addWidget(self.copy_btn)

        layout.addWidget(url_box)

        self.folder_btn = QPushButton()
        self.folder_btn.clicked.connect(self.select_folder)
        layout.addWidget(self.folder_btn)

        self.folder_path = QLabel()
        self.folder_path.setWordWrap(True)
        self.folder_path.setAlignment(Qt.AlignCenter)
        self.folder_path.setStyleSheet("font-size: 11px; color: #94a3b8;")
        layout.addWidget(self.folder_path)

        row1 = QHBoxLayout()
        row1.setSpacing(8)
        self.start_btn = QPushButton()
        self.start_btn.clicked.connect(self.start_server)
        row1.addWidget(self.start_btn)
        self.stop_btn = QPushButton()
        self.stop_btn.setObjectName("danger")
        self.stop_btn.clicked.connect(self.stop_server)
        row1.addWidget(self.stop_btn)
        layout.addLayout(row1)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        self.progress.setFormat("%p%")
        layout.addWidget(self.progress)

        self.file_label = QLabel("")
        self.file_label.setAlignment(Qt.AlignCenter)
        self.file_label.setStyleSheet("font-size: 11px; color: #64748b;")
        layout.addWidget(self.file_label)

        stats = QHBoxLayout()
        self.device_label = QLabel()
        self.device_label.setStyleSheet("font-size: 12px;")
        self.upload_label = QLabel()
        self.upload_label.setStyleSheet("font-size: 12px;")
        stats.addWidget(self.device_label)
        stats.addStretch()
        stats.addWidget(self.upload_label)
        layout.addLayout(stats)

        self.version_label = QLabel(f"v{APP_VERSION}")
        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setStyleSheet("font-size: 11px; color: #64748b;")
        layout.addWidget(self.version_label)

        self.setLayout(layout)
        self._apply_app_icon()

    def apply_language(self):
        t = self.i18n.t
        self.setWindowTitle(f"{self.i18n.app_title()} — v{APP_VERSION}")
        self.settings_btn.setText(t("settings"))
        self.title.setText(t("app_name"))
        self.subtitle.setText(t("app_tagline"))
        self.copy_btn.setText(t("copy"))
        self.folder_btn.setText(t("pick_folder"))
        self.start_btn.setText(t("start_server"))
        self.stop_btn.setText(t("stop"))
        if self._http_server:
            self.status.setText(t("online"))
            self.status.setStyleSheet("font-size: 14px; color: #34d399; font-weight: bold;")
        else:
            self.status.setText(t("offline"))
            self.status.setStyleSheet("font-size: 14px; color: #f87171; font-weight: bold;")
            self._set_url_display("")
            if not self.folder_path.text().startswith(t("save_to")):
                self.folder_path.setText(t("no_folder"))
        self._update_stats_labels(0, 0)

    def _update_stats_labels(self, devices, files):
        self.device_label.setText(f"{self.i18n.t('devices')}: {devices}")
        self.upload_label.setText(f"{self.i18n.t('files')}: {files}")

    def _apply_app_icon(self):
        icon_path = resource_path(os.path.join("assets", "app_icon.png"))
        if not os.path.exists(icon_path):
            return
        icon = QIcon(icon_path)
        self.setWindowIcon(icon)
        app = QApplication.instance()
        if app:
            app.setWindowIcon(icon)

    def _config_path(self):
        return os.path.join(app_data_dir(), "config.json")

    def load_config(self):
        ensure_data_files(bundle_dir(), app_data_dir())
        if os.path.exists(self._config_path()):
            with open(self._config_path(), "r", encoding="utf-8") as f:
                config = json.load(f)
            folder = config.get("upload_folder", "").strip()
            if folder:
                self.folder_path.setText(folder)
            else:
                self.folder_path.setText(self.i18n.t("no_folder"))

    def get_local_ip(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip

    def _set_url_display(self, url):
        t = self.i18n.t
        if not url:
            self.ip_label.setText(t("url_placeholder"))
            self.ip_label.setToolTip("")
            return
        self.ip_label.setToolTip(url)
        fm = self.ip_label.fontMetrics()
        elided = fm.elidedText(url, Qt.ElideMiddle, 230)
        self.ip_label.setText(elided)

    def _folder_ready(self):
        folder = get_upload_folder(app_data_dir())
        if not folder or not os.path.isdir(folder):
            return False, ""
        return True, folder

    def start_server(self):
        if self._http_server:
            return

        ok, folder = self._folder_ready()
        if not ok:
            QMessageBox.warning(self, self.i18n.t("info"), self.i18n.t("folder_required"))
            return

        ensure_data_files(bundle_dir(), app_data_dir())
        port = resolve_port(app_data_dir())
        if port is None:
            QMessageBox.warning(self, self.i18n.t("info"), self.i18n.t("no_port"))
            return

        reset_server_stats(app_data_dir())
        self._http_server = HttpTransferServer(bundle_dir(), app_data_dir(), port)
        self._http_server.start_background()

        for _ in range(40):
            if port_in_use(port):
                break
            time.sleep(0.05)

        if not port_in_use(port):
            self._http_server.stop()
            self._http_server = None
            QMessageBox.warning(self, self.i18n.t("info"), self.i18n.t("server_failed"))
            return

        self.server_port = port
        save_config_port(app_data_dir(), port)
        ip = self.get_local_ip()
        self.url = f"http://{ip}:{port}"
        self.status.setText(self.i18n.t("online"))
        self.status.setStyleSheet("font-size: 14px; color: #34d399; font-weight: bold;")
        self._set_url_display(self.url)
        port_hint = f" (port {port})" if port != 8000 else ""
        self.folder_path.setText(f"{self.i18n.t('save_to')}: {folder}{port_hint}")

        append_log(
            app_data_dir(),
            "server_start",
            f"{self.url}{port_hint}",
            "",
        )

    def _set_offline(self):
        self.status.setText(self.i18n.t("offline"))
        self.status.setStyleSheet("font-size: 14px; color: #f87171; font-weight: bold;")
        self._set_url_display("")
        self.load_config()
        self.url = ""
        self.server_port = None
        self.progress.setValue(0)
        self.file_label.setText("")

    def stop_server(self):
        if self._http_server:
            append_log(app_data_dir(), "server_stop", "", "")
            self._http_server.stop()
            self._http_server = None
        self._set_offline()

    def copy_address(self):
        if not self.url:
            QMessageBox.information(
                self, self.i18n.t("info"), self.i18n.t("server_not_active")
            )
            return
        QGuiApplication.clipboard().setText(self.url)
        QMessageBox.information(
            self, self.i18n.t("success"), self.i18n.t("url_copied")
        )

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, self.i18n.t("select_folder_title")
        )
        if not folder:
            return
        config = {}
        if os.path.exists(self._config_path()):
            with open(self._config_path(), "r", encoding="utf-8") as f:
                config = json.load(f)
        config["upload_folder"] = folder
        with open(self._config_path(), "w", encoding="utf-8") as f:
            json.dump(config, f)
        self.folder_path.setText(folder)
        QMessageBox.information(
            self, self.i18n.t("success"), f"{self.i18n.t('folder_saved')}:\n{folder}"
        )

    def open_settings(self):
        dlg = SettingsDialog(self)
        dlg.exec()

    def update_live_data(self):
        if not self._http_server:
            return
        data_path = os.path.join(app_data_dir(), "server_data.json")
        if not os.path.exists(data_path):
            return
        try:
            with open(data_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._update_stats_labels(
                data.get("connected_devices", 0),
                data.get("uploaded_files", 0),
            )
            self.progress.setValue(data.get("upload_progress", 0))
            if data.get("uploading") and data.get("current_file"):
                self.file_label.setText(data["current_file"])
            elif not data.get("uploading"):
                self.file_label.setText("")
        except OSError:
            pass


app = QApplication(sys.argv)
window = DataTransfer()
window.show()
sys.exit(app.exec())
