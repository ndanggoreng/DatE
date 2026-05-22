# Changelog

Semua perubahan penting pada proyek Dat E didokumentasikan di file ini.

Format berdasarkan [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

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

[1.2.0]: https://github.com/ndanggoreng/DatE/releases/tag/v1.2.0
[1.0.0]: https://github.com/ndanggoreng/DatE/releases/tag/v1.0.0
