"""
core/io.py — сохранение/загрузка изображений, конвертация, форматирование.

PBR Doctor edition: без зависимостей от pbr_generator/image_processor/realism.
Только PIL, numpy, cv2.
"""

import io
import base64
import os
import numpy as np
import cv2
from PIL import Image

from core.i18n import t


# ═══════════════════════════════════════════════════════════
#  ПРЕВЬЮ → PIL
# ═══════════════════════════════════════════════════════════

def to_preview_pil(data, max_size: int = 900) -> Image.Image:
    """numpy [0..1] / uint8 / PIL → PIL RGB/L (thumbnail)."""
    if isinstance(data, Image.Image):
        p = data.copy()
    else:
        arr = np.asarray(data)
        if arr.dtype != np.uint8:
            arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
        if arr.ndim == 2:
            p = Image.fromarray(arr, mode="L")
        elif arr.ndim == 3 and arr.shape[2] == 1:
            p = Image.fromarray(arr[:, :, 0], mode="L")
        elif arr.ndim == 3 and arr.shape[2] >= 3:
            p = Image.fromarray(arr[:, :, :3], mode="RGB")
        else:
            raise ValueError(f"Не могу сделать превью из формы {arr.shape}")

    if p.mode not in ("RGB", "L"):
        p = p.convert("RGB")
    p.thumbnail((max_size, max_size), Image.LANCZOS)
    return p


# ═══════════════════════════════════════════════════════════
#  СОХРАНЕНИЕ PNG
# ═══════════════════════════════════════════════════════════

def save_16bit_or_8bit(pil_img: Image.Image, path: str, bit_depth: int = 16):
    """Сохраняет PIL в PNG с выбранной битностью. bit_depth: 8 или 16."""
    if bit_depth == 16:
        arr = np.array(pil_img.convert("RGB"))
        arr16 = arr.astype(np.uint16) * 257
        bgr = cv2.cvtColor(arr16, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(path), bgr)
    else:
        pil_img.save(str(path))


def save_array_png(arr: np.ndarray, path: str):
    """float32 [0..1] или uint8 → PNG 8-bit."""
    if arr.dtype != np.uint8:
        arr = np.clip(arr * 255.0, 0, 255).astype(np.uint8)
    if arr.ndim == 2:
        Image.fromarray(arr, mode="L").save(path)
    else:
        Image.fromarray(arr[:, :, :3], mode="RGB").save(path)


def save_array_png_16(arr: np.ndarray, path: str):
    """
    float32 [0..1] или uint8 → PNG 16-bit.
    16-bit даёт плавные градиенты там, где 8-bit даёт бандинг —
    критично для normal и height.
    """
    if arr.dtype == np.uint8:
        arr_f = arr.astype(np.float32) / 255.0
    else:
        arr_f = np.clip(arr.astype(np.float32), 0.0, 1.0)

    # 0..1 → 0..65535
    arr16 = np.clip(arr_f * 65535.0, 0, 65535).astype(np.uint16)

    if arr16.ndim == 2:
        # grayscale 16-bit
        Image.fromarray(arr16, mode="I;16").save(path)
    else:
        # RGB 16-bit — через cv2 (PIL не умеет RGB 16-bit PNG)
        rgb16 = arr16[:, :, :3]
        bgr16 = cv2.cvtColor(rgb16, cv2.COLOR_RGB2BGR)
        cv2.imwrite(str(path), bgr16)


def save_array_png_any(arr: np.ndarray, path: str, bit_depth: int = 8):
    """Обёртка: 8 или 16 бит."""
    if bit_depth == 16:
        save_array_png_16(arr, path)
    else:
        save_array_png(arr, path)


# ═══════════════════════════════════════════════════════════
#  ПРЕВЬЮ → BASE64
# ═══════════════════════════════════════════════════════════

def pil_to_b64(data, max_size: int = 900) -> str:
    """PIL или numpy → base64 PNG."""
    p = to_preview_pil(data, max_size=max_size)
    buf = io.BytesIO()
    p.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode()


# ═══════════════════════════════════════════════════════════
#  РАЗМЕР
# ═══════════════════════════════════════════════════════════

def fmt_size(b: int) -> str:
    """Байты → человекочитаемо."""
    if b < 1024:
        return f"{b} B"
    if b < 1024 * 1024:
        return f"{b / 1024:.1f} KB"
    if b < 1024 * 1024 * 1024:
        return f"{b / 1024 / 1024:.2f} MB"
    return f"{b / 1024 / 1024 / 1024:.2f} GB"


# ═══════════════════════════════════════════════════════════
#  ЯРКОСТЬ
# ═══════════════════════════════════════════════════════════

def get_luminance(pil: Image.Image) -> np.ndarray:
    """PIL → массив яркости (Rec. 709)."""
    arr = np.array(pil.convert("RGB")).astype(np.float32)
    return (0.2126 * arr[:, :, 0]
            + 0.7152 * arr[:, :, 1]
            + 0.0722 * arr[:, :, 2])


# ═══════════════════════════════════════════════════════════
#  БЕЗОПАСНОЕ ОТКРЫТИЕ
# ═══════════════════════════════════════════════════════════

def safe_open_rgb(path: str) -> Image.Image:
    """Открывает картинку и конвертит в RGB."""
    try:
        img = Image.open(path)
        img.load()
        return img.convert("RGB")
    except OSError as ex:
        raise OSError(
            t("err.open_file", path=path) + "\n"
            + t("err.open_reason", reason=str(ex)) + "\n"
            + t("err.open_hint")
        ) from ex


def safe_open_gray(path: str) -> Image.Image:
    """Открывает картинку в grayscale."""
    try:
        img = Image.open(path)
        img.load()
        return img.convert("L")
    except OSError as ex:
        raise OSError(
            t("err.open_file", path=path) + "\n"
            + t("err.open_reason", reason=str(ex)) + "\n"
            + t("err.open_hint")
        ) from ex


def load_rgb_float(path: str) -> np.ndarray:
    """
    Открывает файл и возвращает numpy float32 [H,W,3] в [0..1].

    Поддерживает 8-bit и 16-bit PNG/TIFF. Для 16-bit делит на 65535,
    для 8-bit — на 255. Grayscale дублируется в 3 канала.

    NaN/Inf чистим — AI-генераторы иногда выдают мусор.
    """
    try:
        pil = Image.open(path)
        pil.load()
    except OSError as ex:
        raise OSError(
            t("err.open_file", path=path) + "\n"
            + t("err.open_reason", reason=str(ex)) + "\n"
            + t("err.open_hint")
        ) from ex

    arr = np.array(pil)

    # ─── Определяем битность по dtype ───
    if arr.dtype == np.uint16:
        divisor = 65535.0
    elif arr.dtype == np.uint8:
        divisor = 255.0
    elif arr.dtype == np.int32:
        # PIL иногда отдаёт int32 для 16-bit — приводим
        arr = arr.astype(np.uint16)
        divisor = 65535.0
    else:
        # Что-то экзотическое — приводим к float через PIL
        arr = np.array(pil.convert("RGB"))
        divisor = 255.0

    # ─── Grayscale → RGB (дублируем канал) ───
    if arr.ndim == 2:
        arr = np.stack([arr, arr, arr], axis=-1)
    elif arr.ndim == 3 and arr.shape[2] == 1:
        arr = np.repeat(arr, 3, axis=2)
    elif arr.ndim == 3 and arr.shape[2] == 4:
        # RGBA — отбрасываем альфу
        arr = arr[:, :, :3]
    elif arr.ndim == 3 and arr.shape[2] > 3:
        arr = arr[:, :, :3]

    arr = arr.astype(np.float32) / divisor

    if not np.isfinite(arr).all():
        arr = np.nan_to_num(arr, nan=0.0, posinf=1.0, neginf=0.0)
    return np.clip(arr, 0.0, 1.0).astype(np.float32)


def get_file_size(path: str) -> int:
    """Размер файла в байтах, 0 если нет."""
    try:
        return os.path.getsize(path)
    except OSError:
        return 0