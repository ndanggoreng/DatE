"""
Hapus file Qt/PySide6 yang tidak dipakai Dat E agar ukuran release < 25 MB (ZIP).
Jalankan setelah: pyinstaller dekstop.spec --noconfirm
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

DIST_ROOT = Path("dist/DatE")
INTERNAL = DIST_ROOT / "_internal"

# DLL yang tidak diperlukan (hanya pakai Qt Widgets)
REMOVE_DLLS = [
    "PySide6/opengl32sw.dll",
    "PySide6/Qt6Quick.dll",
    "PySide6/Qt6Qml.dll",
    "PySide6/Qt6QmlModels.dll",
    "PySide6/Qt6QmlMeta.dll",
    "PySide6/Qt6QmlWorkerScript.dll",
    "PySide6/Qt6Pdf.dll",
    "PySide6/Qt6OpenGL.dll",
    "PySide6/Qt6Network.dll",
    "PySide6/Qt6Svg.dll",
    "PySide6/Qt6VirtualKeyboard.dll",
    "PySide6/QtNetwork.pyd",
    "PySide6/QtOpenGL.pyd",
]

# Plugin yang dipertahankan (minimal Windows widgets)
PLUGIN_KEEP = {
    "platforms/qwindows.dll",
    "styles/qwindowsvistastyle.dll",
    "imageformats/qico.dll",
    "imageformats/qgif.dll",
    "imageformats/qjpeg.dll",
    "imageformats/qpng.dll",
}


def _rm(path: Path) -> float:
    if not path.exists():
        return 0.0
    size = sum(f.stat().st_size for f in path.rglob("*") if f.is_file()) if path.is_dir() else path.stat().st_size
    if path.is_dir():
        shutil.rmtree(path)
    else:
        path.unlink()
    return size / (1024 * 1024)


def trim() -> None:
    if not INTERNAL.is_dir():
        print(f"Folder tidak ditemukan: {INTERNAL}")
        print("Jalankan PyInstaller terlebih dahulu.")
        sys.exit(1)

    saved = 0.0

    trans = INTERNAL / "PySide6" / "translations"
    saved += _rm(trans)

    for rel in REMOVE_DLLS:
        saved += _rm(INTERNAL / rel)

    plugins = INTERNAL / "PySide6" / "plugins"
    if plugins.is_dir():
        for sub in plugins.iterdir():
            if sub.is_dir():
                for dll in sub.glob("*.dll"):
                    rel = f"{sub.name}/{dll.name}"
                    if rel not in PLUGIN_KEEP:
                        saved += _rm(dll)
            elif sub.suffix.lower() == ".dll":
                if sub.name not in {p.split("/")[-1] for p in PLUGIN_KEEP}:
                    saved += _rm(sub)

    total_mb = sum(f.stat().st_size for f in DIST_ROOT.rglob("*") if f.is_file()) / (1024 * 1024)
    print(f"Trim selesai. Perkiraan hemat: {saved:.1f} MB")
    print(f"Ukuran folder dist/DatE: {total_mb:.1f} MB")


if __name__ == "__main__":
    trim()
