## Dat E v1.3.1 — Data Transfer Local

Patch release: perbaikan transfer file **besar (>2 GB)** dan notifikasi web client.

### Download

| File | Keterangan |
|------|------------|
| `DatE-v1.3.1-windows.zip` | Aplikasi Windows (~24 MB) — folder `DatE/` berisi `DatE.exe` |
| Source code | Klik "Source code (zip)" di bawah jika tidak pakai asset ZIP |

### Perbaikan v1.3.1

- Upload/download file besar via **streaming chunk** — tidak lagi membaca seluruh file ke memory
- EXE tidak freeze / Not Responding saat transfer file >2 GB
- Progress upload lebih ringan (throttle update status ke disk)
- Web client: alert offline tidak berulang; unduh dari PC stabil (tanpa spam notifikasi)

### Cara pakai

Sama seperti v1.3.0 — lihat [README.md](https://github.com/ndanggoreng/DatE/blob/main/README.md).

### Persyaratan

- Windows 10/11
- PC dan perangkat lain di **jaringan WiFi yang sama**
- Izinkan Windows Firewall untuk `DatE.exe` (jaringan privat)

---

**Full changelog:** [CHANGELOG.md](https://github.com/ndanggoreng/DatE/blob/main/CHANGELOG.md)
