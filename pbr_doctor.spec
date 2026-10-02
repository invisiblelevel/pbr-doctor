# -*- mode: python ; coding: utf-8 -*-

from PyInstaller.utils.hooks import collect_all, collect_dynamic_libs


# ═══════════════════════════════════════════════════════════
#  Сбор данных для Flet, cv2, onnxruntime
# ═══════════════════════════════════════════════════════════

datas = []
binaries = []
hiddenimports = []

# Пакеты, содержимое которых надо целиком затащить в exe
for pkg in ("flet", "flet_desktop", "cv2", "onnxruntime"):
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


# ═══════════════════════════════════════════════════════════
#  Исключаем CUDA / TensorRT библиотеки onnxruntime-gpu
#  (нам нужен только DirectML + CPU)
# ═══════════════════════════════════════════════════════════

# Эти dll'ки — часть onnxruntime-gpu, не DirectML.
# Если их оставить — exe потолстеет на ~150 МБ без пользы.
_CUDA_BINS = [
    "onnxruntime_providers_cuda",
    "onnxruntime_providers_tensorrt",
    "onnxruntime_providers_shared",   # ← нужен только GPU-провайдерам
    "cublas",
    "cudnn",
    "cudart",
    "cufft",
    "curand",
    "cusolver",
    "cusparse",
    "nvrtc",
    "nvjpeg",
    "nvinfer",
    "nvonnxparser",
    "nvToolsExt",
    "cudnn64",
    "cublasLt64",
    "cublas64",
    "cudart64",
    "cufft64",
    "curand64",
    "cusolver64",
    "cusparse64",
    "nvrtc64",
    "nvjpeg64",
    "nvinfer",
    "nvonnxparser",
]

def _is_cuda_bin(name: str) -> bool:
    low = name.lower()
    return any(x in low for x in _CUDA_BINS)


# ─── Прочие исключения ───
_EXCLUDE_BINS = ["opencv_videoio_ffmpeg"]


def _should_exclude(name: str) -> bool:
    low = name.lower()
    if any(p in low for p in _EXCLUDE_BINS):
        return True
    if _is_cuda_bin(low):
        return True
    return False


# ═══════════════════════════════════════════════════════════
#  Analysis
# ═══════════════════════════════════════════════════════════

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
        # ML-фреймворки — не используем
        "torch", "torchvision", "torchaudio",
        "tensorflow", "keras",
        "sklearn", "scipy", "pandas", "matplotlib",
        # Окружения разработки
        "IPython", "jupyter", "notebook",
        # GUI-фреймворки — Flet самодостаточен
        "tkinter", "PyQt5", "PyQt6", "PySide2", "PySide6", "wx",
        # Тесты
        "test", "unittest", "pydoc", "doctest",
        # flet-dropzone — не используем
        "flet_dropzone",
    ],
    noarchive=False,
    optimize=0,
)

# ─── Чистим бинарники от CUDA / ffmpeg ───
a.binaries = [x for x in a.binaries if not _should_exclude(x[0])]
a.datas = [x for x in a.datas if not _should_exclude(x[0])]


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
    upx=False,
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
    upx=False,
    upx_exclude=[],
    name="PBR Doctor",
)