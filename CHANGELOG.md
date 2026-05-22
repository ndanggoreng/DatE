# Changelog

Semua perubahan penting pada proyek Dat E didokumentasikan di file ini.

Format berdasarkan [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [1.3.0] - 2026-05-23

### Added
- Transfer **PC → HP**: tombol **Kirim ke HP** di desktop + tab **Unduh dari PC** di web client
- Endpoint `/api/outgoing` dan `/download/<nama>` untuk unduhan dari browser
- Deteksi server offline di web client (polling, banner, alert saat pilih/unduh file)
- Struktur proyek dirapikan: `core/`, `log/`, `res/`, `data/`, `sys/`
- Launcher `DatE.py` di root; modul utama `core/app.py`
- Migrasi otomatis config/log lama ke folder `data/`

### Changed
- Tombol **Pilih Folder Simpan** dan **Kirim ke HP** dalam layout grid (desktop)
- Tombol **Salin** URL menjadi teks tanpa background (tetap bisa diklik)
- Antrian file PC→HP dikosongkan saat server di-stop (tidak menumpuk di client)
- Script build dipindah ke `sys/build_release.ps1` dan `sys/trim_build.py`
- Resource web/locale/asset dipindah ke `res/`

### Fixed
- Path resource salah setelah refactor folder (`locales`, `web`, `assets` tidak ditemukan)
- Daftar file dari PC tetap tampil di browser setelah server dimatikan
- Upload/unduh tanpa server aktif — pengguna mendapat peringatan jelas

## [1.2.0] - 2026-05-22

### Added
- Script `trim_build.py` & `build_release.ps1` — release ZIP di bawah 25 MB
- Log aktivitas server & client di Settings
- Multi-bahasa (Indonesia & English) — siap untuk kontribusi terjemahan
- Build output `DatE.exe` (PyInstaller)
- Endpoint `/api/info`, `/api/i18n`, `/api/logs`
- Tampilan nama file setelah dipilih di web client
- Tombol Salin URL di dalam kotak URL
- Tombol Settings di kanan atas

### Changed
- Server HTTP ringan (stdlib) — ukuran build lebih kecil tanpa FastAPI/uvicorn
- UI desktop & web disederhanakan
- Nama aplikasi diseragamkan: **Dat E (Data Transfer Local)**
- Port otomatis jika 8000 sedang digunakan
- Upload file via `X-Filename` header (lebih stabil di mobile)

### Fixed
- File upload tidak tersimpan setelah build EXE
- Tombol START/STOP teks hilang di UI desktop
- Sinkronisasi progress bar & connected devices dengan client

## [1.0.0] - 2026-05-22

### Added
- Rilis awal — transfer file lokal via WiFi
- Aplikasi desktop PySide6
- Web client untuk upload dari browser
- Pilih folder simpan, salin URL server

[1.3.0]: https://github.com/ndanggoreng/DatE/releases/tag/v1.3.0
[1.2.0]: https://github.com/ndanggoreng/DatE/releases/tag/v1.2.0
[1.0.0]: https://github.com/ndanggoreng/DatE/releases/tag/v1.0.0
