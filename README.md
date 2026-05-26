# Dat E — Data Transfer Local

<p align="center">
  <strong>Transfer file antar perangkat dalam jaringan WiFi lokal yang sama — tanpa internet.</strong>
</p>

<p align="center">
  <em>Transfer files between devices on the same local WiFi — no internet required.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.3.1-blue" alt="Version">
  <img src="https://img.shields.io/badge/python-3.10%2B-blue" alt="Python">
  <img src="https://img.shields.io/badge/platform-Windows-lightgrey" alt="Platform">
  <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
</p>

---

## Tentang aplikasi / About

**Dat E (Data Transfer Local)** adalah aplikasi desktop ringan untuk Windows yang menjalankan server file lokal. Perangkat lain (HP, tablet, laptop) membuka browser untuk **mengirim file ke PC** atau **mengunduh file dari PC** — cocok untuk berbagi dokumen, foto, atau video dalam satu jaringan WiFi (rumah, kantor, sekolah).

**Dat E (Data Transfer Local)** is a lightweight Windows desktop app that runs a local file server. Other devices open a browser to **upload files to your PC** or **download files shared from your PC** — ideal for sharing on the same WiFi network.

### Kegunaan utama / Main use cases

- Transfer file dari HP ke PC tanpa kabel USB
- Kirim file dari PC ke HP (browser, tanpa instal di HP)
- Berbagi file cepat di jaringan lokal
- Tidak membutuhkan koneksi internet
- Antarmuka sederhana untuk pengguna non-teknis

---

## Fitur / Features

| Fitur | Deskripsi |
|-------|-----------|
| **Server lokal** | Jalankan server HTTP dari aplikasi desktop |
| **Web client** | Klien berbasis browser — kirim ke PC & unduh dari PC |
| **Kirim ke HP** | PC membagikan file lewat tab Unduh di browser |
| **Pilih folder simpan** | Tentukan lokasi file yang diterima dari HP |
| **Deteksi server offline** | Web client memperingatkan jika server belum aktif |
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
.\sys\build_release.ps1
```

Atau manual:

```bash
pyinstaller dekstop.spec --noconfirm
py sys/trim_build.py
```

Hasil build:

```
dist/DatE/DatE.exe
release/DatE-v1.3.1-windows.zip   # siap upload ke GitHub Releases
```

> **Catatan ukuran:** PyInstaller menyertakan banyak library Qt. Script `trim_build.py` menghapus modul yang tidak dipakai (QML, PDF, OpenGL software, terjemahan Qt) agar ZIP release **≤ 25 MB**. Kompresi ZIP memakai 7-Zip (`-mx=9`) jika terinstal.

Jalankan `DatE.exe` dari folder `dist/DatE/`.

---

## Panduan penggunaan / Usage guide

### Aplikasi desktop (PC)

| Langkah | Aksi |
|--------|------|
| 1 | Klik **Pilih Folder Simpan** (atau **Kirim ke HP** untuk share ke browser) |
| 2 | Klik **Mulai Server** |
| 3 | Klik teks **Salin** di kotak URL (jika perlu) |
| 4 | Buka URL tersebut di browser perangkat lain |
| 5 | Klik **Stop** untuk menghentikan server |

### Web client (HP / perangkat lain)

1. Pastikan terhubung ke **WiFi yang sama** dengan PC dan server PC sudah **Online**
2. Buka URL yang ditampilkan di aplikasi (contoh: `http://192.168.1.10:8000`)
3. **Kirim ke PC:** tab *Kirim ke PC* → pilih file → **Kirim File**
4. **Unduh dari PC:** tab *Unduh dari PC* → pilih file yang dikirim dari PC → unduh

> Jika server belum aktif, web client menampilkan peringatan dan daftar file dari PC dikosongkan.

### Settings

- **Log aktivitas** — riwayat koneksi & transfer
- **Bahasa** — Indonesia / English
- Log & konfigurasi: di folder `data/` (development) atau folder yang sama dengan `DatE.exe` (build EXE)

---

## Konfigurasi / Configuration

File konfigurasi dibuat otomatis di folder data aplikasi (`data/` saat dev, sebelah `DatE.exe` saat build):

| File | Fungsi |
|------|--------|
| `config.json` | Folder simpan, port server, bahasa |
| `server_data.json` | Status server (progress, jumlah file) |
| `log/activity_log.json` | Log koneksi & transfer |
| `outgoing/` | Antrian file PC → HP (dikosongkan saat server stop) |

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
├── DatE.py              # Launcher
├── core/
│   ├── app.py           # UI desktop (PySide6)
│   ├── server.py        # HTTP server (stdlib)
│   ├── i18n.py
│   └── version.py
├── log/
│   └── activity_log.py
├── res/
│   ├── locales/         # id.json, en.json
│   ├── web/             # index.html, app.js, style.css
│   └── assets/          # ikon aplikasi
├── data/                # config & runtime (gitignore)
├── sys/
│   ├── build_release.ps1
│   └── trim_build.py
└── dekstop.spec
```

---

## Menambah bahasa baru / Adding a new language

1. Salin `res/locales/en.json` → `res/locales/xx.json` (misalnya `de.json` untuk Jerman)
2. Terjemahkan semua string di file tersebut
3. Tambahkan kode bahasa di `i18n.py`:

```python
SUPPORTED = ("id", "en", "de")
```

4. Tambahkan opsi di dialog Settings (`core/app.py` → `SettingsDialog`)

Kontribusi terjemahan sangat diterima.

---

## Troubleshooting

| Masalah | Solusi |
|---------|--------|
| HP tidak bisa buka URL | Pastikan PC dan HP di WiFi yang sama; izinkan **Windows Firewall** untuk `DatE.exe` |
| Server gagal start | Port 8000 mungkin dipakai aplikasi lain — Dat E akan coba port lain otomatis |
| File tidak tersimpan | Pilih folder simpan **sebelum** mulai server; pastikan path folder valid |
| Upload gagal di browser | Pastikan server PC **Online**; refresh halaman; coba Chrome/Safari |
| File PC tidak muncul di HP | Klik **Kirim ke HP** di PC dulu; buka tab **Unduh dari PC** |
| Daftar file tidak hilang setelah stop | Refresh halaman — v1.3+ mengosongkan otomatis saat server mati |

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
  <strong>Dat E</strong> — Data Transfer Local · v1.3.1
</p>
