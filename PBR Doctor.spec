# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all


# ═══════════════════════════════════════════════════════════
#  Собираем данные для Flet и cv2
# ═══════════════════════════════════════════════════════════

datas = []
binaries = []
hiddenimports = []

for pkg in ("flet", "flet_desktop", "cv2"):
    try:
        d, b, h = collect_all(pkg)
        datas += d
        binaries += b
        hiddenimports += h
    except Exception as ex:
        print(f"[spec] collect_all({pkg}) failed: {ex}")

# ─── Наши ассеты ───
datas += [("assets", "assets")]
datas += [("icon.ico", ".")]


a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports + [
        "PIL._tkinter_finder",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "torch", "torchvision", "torchaudio",
        "tensorflow", "keras",
        "sklearn", "scipy", "pandas", "matplotlib",
        "IPython", "jupyter", "notebook",
        "tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6", "wx",
        "test", "unittest", "pydoc", "doctest",
    ],
    noarchive=False,
    optimize=0,
)

# ─── Режем лишние бинарники ───
_exclude_bins = ["opencv_videoio_ffmpeg"]
a.binaries = [x for x in a.binaries
              if not any(p in x[0].lower() for p in _exclude_bins)]
a.datas = [x for x in a.datas
           if not any(p in x[0].lower() for p in _exclude_bins)]


pyz = PYZ(a.pure)


exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PBR Doctor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,                    # ← UPX выключен!
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=["icon.ico"],
)


coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,                    # ← UPX выключен!
    upx_exclude=[],
    name="PBR Doctor",
)