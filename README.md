# Dat E — Data Transfer Local

<p align="center">
  <strong>Transfer file antar perangkat dalam jaringan WiFi lokal yang sama — tanpa internet.</strong>
</p>

<p align="center">
  <em>Transfer files between devices on the same local WiFi — no internet required.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.2.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/platform-Windows-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

---

## Tentang aplikasi / About

**Dat E (Data Transfer Local)** adalah aplikasi desktop ringan untuk Windows yang menjalankan server file lokal. Perangkat lain (HP, tablet, laptop) cukup membuka browser dan mengunggah file ke PC Anda — cocok untuk berbagi dokumen, foto, atau video dalam satu jaringan WiFi (rumah, kantor, sekolah).

**Dat E (Data Transfer Local)** is a lightweight Windows desktop app that runs a local file server. Other devices (phones, tablets, laptops) open a browser and upload files to your PC — ideal for sharing documents, photos, or videos on the same WiFi network.

### Kegunaan utama / Main use cases

- Transfer file dari HP ke PC tanpa kabel USB
- Berbagi file cepat di jaringan lokal
- Tidak membutuhkan koneksi internet
- Antarmuka sederhana untuk pengguna non-teknis

---

## Fitur / Features

| Fitur | Deskripsi |
|-------|-----------|
| **Server lokal** | Jalankan server HTTP dari aplikasi desktop |
| **Web client** | Klien berbasis browser — tidak perlu instal di HP |
| **Pilih folder simpan** | Tentukan lokasi file yang diterima |
| **Progress real-time** | Progress upload & jumlah perangkat terhubung |
| **Port otomatis** | Mencari port kosong jika port default (8000) sibuk |
| **Log aktivitas** | Riwayat koneksi client & transfer file di Settings |
| **Multi-bahasa (i18n)** | Indonesia & English — mudah ditambah bahasa baru |
| **Build EXE** | Dapat di-build menjadi `DatE.exe` (PyInstaller) |

---

## Cara kerja / How it works

```
┌─────────────────┐         WiFi lokal          ┌─────────────────┐
│   PC (Dat E)    │ ◄────────────────────────── │  HP / Browser   │
│  DatE.exe       │    http://192.168.x.x:port  │  Web client     │
│  + folder simpan│ ──────────────────────────► │  Upload file    │
└─────────────────┘         file tersimpan      └─────────────────┘
```

1. Buka **Dat E** di PC Windows
2. Pilih **folder simpan** file
3. Klik **Mulai Server** — URL akan muncul
4. Di HP (WiFi **sama**), buka URL di browser
5. Pilih file → **Kirim File**
6. File tersimpan di folder yang dipilih di PC

---

## Persyaratan / Requirements

### Menjalankan dari source (developer)

- Windows 10/11
- Python 3.10 atau lebih baru
- [PySide6](https://pypi.org/project/PySide6/) (Qt untuk antarmuka desktop)

### Menjalankan EXE (pengguna akhir)

- Windows 10/11
- Tidak perlu instal Python

---

## Instalasi / Installation

### 1. Clone repository

```bash
git clone https://github.com/ndanggoreng/DateT.git
cd DateT
```

### 2. Buat virtual environment (disarankan)

```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install dependensi

```bash
pip install PySide6 pyinstaller
```

> Server HTTP menggunakan modul bawaan Python (`http.server`) — tidak memerlukan FastAPI/uvicorn.

---

## Menjalankan aplikasi / Running the app

### Mode development

```bash
python DatE.py
```

### Build menjadi EXE

```powershell
# Disarankan: build + trim Qt + ZIP release (< 25 MB)
.\build_release.ps1
```

Atau manual:

```bash
pyinstaller dekstop.spec --noconfirm
py trim_build.py
```

Hasil build:

```
dist/DatE/DatE.exe
release/DatE-v1.2.0-windows.zip   # siap upload ke GitHub Releases
```

> **Catatan ukuran:** PyInstaller menyertakan banyak library Qt. Script `trim_build.py` menghapus modul yang tidak dipakai (QML, PDF, OpenGL software, terjemahan Qt) agar ZIP release **≤ 25 MB**. Kompresi ZIP memakai 7-Zip (`-mx=9`) jika terinstal.

Jalankan `DatE.exe` dari folder `dist/DatE/`.

---

## Panduan penggunaan / Usage guide

### Aplikasi desktop (PC)

| Langkah | Aksi |
|--------|------|
| 1 | Klik **Pilih Folder Simpan** |
| 2 | Klik **Mulai Server** |
| 3 | Klik **Salin** di dalam kotak URL (jika perlu) |
| 4 | Buka URL tersebut di browser perangkat lain |
| 5 | Klik **Stop** untuk menghentikan server |

### Web client (HP / perangkat lain)

1. Pastikan terhubung ke **WiFi yang sama** dengan PC
2. Buka URL yang ditampilkan di aplikasi (contoh: `http://192.168.1.10:8000`)
3. Pilih file — nama file akan ditampilkan
4. Klik **Kirim File**

### Settings

- **Log aktivitas** — riwayat koneksi & transfer
- **Bahasa** — Indonesia / English
- Log & konfigurasi disimpan di folder yang sama dengan `DatE.exe`

---

## Konfigurasi / Configuration

File konfigurasi dibuat otomatis di folder aplikasi:

| File | Fungsi |
|------|--------|
| `config.json` | Folder simpan, port server, bahasa |
| `server_data.json` | Status server (progress, jumlah file) |
| `activity_log.json` | Log koneksi & transfer |

Contoh `config.json`:

```json
{
  "upload_folder": "D:\\Uploads",
  "server_port": 8000,
  "language": "id"
}
```

| Field | Keterangan |
|-------|------------|
| `upload_folder` | Path folder penyimpanan file upload |
| `server_port` | Port preferensi (default: 8000). Jika sibuk, port lain dipilih otomatis |
| `language` | `id` (Indonesia) atau `en` (English) |

---

## Struktur proyek / Project structure

```
DateT/
├── DatE.py              # Aplikasi desktop (PySide6)
├── server.py            # HTTP server (stdlib)
├── activity_log.py      # Log aktivitas
├── i18n.py              # Sistem multi-bahasa
├── version.py           # Versi aplikasi
├── dekstop.spec         # Konfigurasi PyInstaller
├── locales/
│   ├── id.json          # Terjemahan Indonesia
│   └── en.json          # Terjemahan English
├── web/
│   ├── index.html       # Halaman upload (client)
│   ├── style.css
│   └── app.js
├── assets/
│   ├── app_icon.png
│   └── app_icon.ico
└── README.md
```

---

## Menambah bahasa baru / Adding a new language

1. Salin `locales/en.json` → `locales/xx.json` (misalnya `de.json` untuk Jerman)
2. Terjemahkan semua string di file tersebut
3. Tambahkan kode bahasa di `i18n.py`:

```python
SUPPORTED = ("id", "en", "de")
```

4. Tambahkan opsi di dialog Settings (`DatE.py` → `SettingsDialog`)

Kontribusi terjemahan sangat diterima.

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| HP tidak bisa buka URL | Pastikan PC dan HP di WiFi yang sama; izinkan **Windows Firewall** untuk `DatE.exe` |
| Server gagal start | Port 8000 mungkin dipakai aplikasi lain — Dat E akan coba port lain otomatis |
| File tidak tersimpan | Pilih folder simpan **sebelum** mulai server; pastikan path folder valid |
| Upload gagal di browser | Refresh halaman; coba browser lain (Chrome/Safari) |

---

## Tech stack

- **Desktop UI:** PySide6 (Qt)
- **Server:** Python `http.server` + `socketserver` (ringan, tanpa dependensi web berat)
- **Web client:** HTML, CSS, JavaScript (vanilla)
- **Packaging:** PyInstaller
- **i18n:** JSON locale files

---

## Berkontribusi / Contributing

Kontribusi dipersilakan.

1. Fork repository
2. Buat branch fitur (`git checkout -b feature/nama-fitur`)
3. Commit perubahan (`git commit -m 'Add: deskripsi fitur'`)
4. Push ke branch (`git push origin feature/nama-fitur`)
5. Buka Pull Request

Ide kontribusi: terjemahan bahasa baru, perbaikan UI, dukungan macOS/Linux, dark/light theme, QR code untuk URL server.

---

## Lisensi / License

Proyek ini menggunakan lisensi **MIT** — bebas digunakan, dimodifikasi, dan didistribusikan. Lihat file [LICENSE](LICENSE) untuk detail.

---

## Pengembang / Author

Dibuat sebagai proyek open source untuk memudahkan transfer file lokal.

Jika proyek ini membantu Anda, pertimbangkan untuk memberi **star** di GitHub.

---

<p align="center">
  <strong>Dat E</strong> — Data Transfer Local · v1.2.0
</p>
