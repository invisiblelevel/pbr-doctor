"""
core/seamless.py — три алгоритма приведения карт к бесшовному тайлингу.

Режимы:
  1. mirror_blend  — сдвиг + зеркальный blend. Простой, предсказуемый.
                     Хорош для albedo / roughness / ao / metallic.
  2. freq_sep      — frequency separation: низкие частоты blend,
                     высокие копируются. Не размывает детали.
                     Хорош для normal / height.
  3. hipass        — GIMP tile-seamless порт. Даёт наложение, но иногда
                     спасает на специфичных текстурах.

Все функции принимают и возвращают np.ndarray float32 [H,W,3] в [0..1].
Для normal-карт после каждого метода нормализуем длины векторов.
"""

import numpy as np
import cv2
from core.i18n import t


# ═══════════════════════════════════════════════════════════
#  ДЕТЕКТ ШВА
# ═══════════════════════════════════════════════════════════

def detect_seam(img: np.ndarray) -> dict:
    """
    Считает разницу между противоположными краями карты.

    Возвращает:
        {
          "lr_diff": float,       # средняя разница левого/правого края
          "tb_diff": float,       # средняя разница верхнего/нижнего края
          "max_diff": float,      # максимум из lr/tb
          "has_seam": bool,       # max_diff > порог
        }
    """
    if img.ndim != 3:
        return {"lr_diff": 0.0, "tb_diff": 0.0,
                "max_diff": 0.0, "has_seam": False}

    # Левый/правый край
    left = img[:, 0, :]
    right = img[:, -1, :]
    lr_diff = float(np.abs(left - right).mean())

    # Верхний/нижний край
    top = img[0, :, :]
    bottom = img[-1, :, :]
    tb_diff = float(np.abs(top - bottom).mean())

    max_diff = max(lr_diff, tb_diff)
    has_seam = max_diff > 0.05

    return {
        "lr_diff": lr_diff,
        "tb_diff": tb_diff,
        "max_diff": max_diff,
        "has_seam": has_seam,
    }


# ═══════════════════════════════════════════════════════════
#  ГЛАВНЫЙ ВХОД
# ═══════════════════════════════════════════════════════════

def make_seamless(img: np.ndarray, mode: str = "mirror_blend",
                  is_normal: bool = False) -> np.ndarray:
    """
    Применяет выбранный режим бесшовности.

    mode: "mirror_blend" | "freq_sep" | "hipass"
    is_normal: если True — после обработки нормализуем длины векторов.
    """
    if img.ndim != 3 or img.shape[2] < 3:
        return img

    img = img.astype(np.float32)

    if mode == "mirror_blend":
        out = _make_seamless_mirror(img)
    elif mode == "freq_sep":
        out = _make_seamless_freqsep(img)
    elif mode == "hipass":
        out = _make_seamless_hipass(img)
    else:
        raise ValueError(t("err.seamless_mode", mode=mode))

    if is_normal:
        out = _normalize_normal(out)

    return np.clip(out, 0.0, 1.0).astype(np.float32)


# ═══════════════════════════════════════════════════════════
#  РЕЖИМ 1 — MIRROR-BLEND
# ═══════════════════════════════════════════════════════════

def _make_seamless_mirror(img: np.ndarray, band: int = 64) -> np.ndarray:
    """
    Сдвигаем на пол-размера (шов в центре), потом в полосе шириной
    `band` вокруг центра смешиваем с зеркальной копией.

    Вне полосы — просто сдвинутая карта. Внутри — плавный переход
    между shifted и mirror.
    """
    h, w = img.shape[:2]
    half_h, half_w = h // 2, w // 2

    # Сдвиг: шов теперь в центре
    shifted = np.roll(np.roll(img, half_h, axis=0), half_w, axis=1)

    # Зеркальная копия сдвинутой (по обеим осям)
    mirror = shifted[::-1, ::-1, :]

    # Расстояние от центра по каждой оси (в пикселях)
    yy = np.arange(h, dtype=np.float32)
    xx = np.arange(w, dtype=np.float32)
    dy = np.abs(yy - h / 2.0)
    dx = np.abs(xx - w / 2.0)

    # Нормализованное расстояние внутри полосы band
    wy = np.clip(dy / band, 0.0, 1.0)
    wx = np.clip(dx / band, 0.0, 1.0)

    # 2D-вес: 0 в центре полосы, 1 за её пределами
    weight = np.maximum(wy[:, None], wx[None, :])
    weight = weight[:, :, None]  # (h,w,1)

    # В полосе — смешиваем shifted и mirror, вне — просто shifted
    blended = shifted * (1.0 - weight * 0.5) + mirror * (weight * 0.5)

    return np.clip(blended, 0.0, 1.0).astype(np.float32)


# ═══════════════════════════════════════════════════════════
#  РЕЖИМ 2 — FREQUENCY SEPARATION
# ═══════════════════════════════════════════════════════════

def _make_seamless_freqsep(img: np.ndarray,
                            blur_sigma: float = 8.0) -> np.ndarray:
    """
    Раскладываем на low + high.
    Low сглаживаем через mirror-blend, high — оставляем как есть.
    Складываем. Детали не размываются.
    """
    h, w = img.shape[:2]
    half_h, half_w = h // 2, w // 2

    # Разложение
    low = cv2.GaussianBlur(img, (0, 0), blur_sigma)
    high = img - low

    # Сдвигаем low на пол-размера
    shifted_low = np.roll(np.roll(low, half_h, axis=0), half_w, axis=1)

    # Зеркалим
    mirror_low = shifted_low[::-1, ::-1, :]

    # Плавный blend в полосе вокруг центра
    band = max(32, min(h, w) // 8)
    yy = np.arange(h, dtype=np.float32)
    xx = np.arange(w, dtype=np.float32)
    dy = np.abs(yy - h / 2.0)
    dx = np.abs(xx - w / 2.0)
    wy = np.clip(dy / band, 0.0, 1.0)
    wx = np.clip(dx / band, 0.0, 1.0)
    weight = np.maximum(wy[:, None], wx[None, :])[:, :, None]

    blended_low = (shifted_low * (1.0 - weight * 0.5)
                   + mirror_low * (weight * 0.5))

    # Складываем обратно: сглаженные низкие + детальные высокие
    out = blended_low + high
    return np.clip(out, 0.0, 1.0).astype(np.float32)


# ═══════════════════════════════════════════════════════════
#  РЕЖИМ 3 — HIPASS (GIMP tile-seamless порт)
# ═══════════════════════════════════════════════════════════

def _make_seamless_hipass(img: np.ndarray,
                           hipass: bool = True,
                           radius: float = 20.0) -> np.ndarray:
    """
    GIMP tile-seamless. Сдвиг + диагональная весовая маска.
    Даёт наложение, но иногда работает там, где mirror/freq-sep не тянут.
    """
    arr = img.astype(np.float32)

    if hipass:
        arr = _hipass_filter_np(arr, radius=radius)

    h, w = arr.shape[:2]
    xx = np.arange(w, dtype=np.float32)
    yy = np.arange(h, dtype=np.float32)

    wx = 1.0 - np.abs(2.0 * xx / w - 1.0)
    wy = 1.0 - np.abs(2.0 * yy / h - 1.0)
    weight = np.outer(wy, wx)[:, :, None]

    half_h, half_w = h // 2, w // 2
    shifted = np.roll(np.roll(arr, half_h, axis=0), half_w, axis=1)

    mixed = arr * weight + shifted * (1.0 - weight)
    return np.clip(mixed, 0.0, 1.0).astype(np.float32)


def _hipass_filter_np(arr: np.ndarray, radius: float = 20.0) -> np.ndarray:
    """Hi-pass pre-filter. Вход/выход float [0..1]."""
    arr255 = arr * 255.0
    blurred = cv2.GaussianBlur(arr255, (0, 0), radius)
    hp = arr255 - blurred + 128.0
    return np.clip(hp / 255.0, 0.0, 1.0).astype(np.float32)


# ═══════════════════════════════════════════════════════════
#  NORMAL — нормализация длин векторов
# ═══════════════════════════════════════════════════════════

def _normalize_normal(img: np.ndarray) -> np.ndarray:
    """XYZ → нормируем каждый вектор к длине 1 → обратно RGB."""
    xyz = img * 2.0 - 1.0
    lengths = np.linalg.norm(xyz, axis=2, keepdims=True)
    lengths = np.maximum(lengths, 1e-6)
    xyz_n = xyz / lengths
    out = (xyz_n + 1.0) * 0.5
    return np.clip(out, 0.0, 1.0).astype(np.float32)