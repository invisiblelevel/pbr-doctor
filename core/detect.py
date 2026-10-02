"""
core/detect.py — определяет тип PBR-карты.

Двухуровнево:
  1. По имени файла (суффиксы: _normal, _n, _roughness, ...).
  2. По содержимому (гистограммы, каналы, статистика).

Возвращает (MapType, confidence, detected_by).

ВАЖНО: albedo всегда форсится по имени. AI-генераторы часто дают albedo
с "неправильным" содержимым (шумное, не цветное), но имя файла надёжное.
"""

import os
import re
import numpy as np
from core.state import MapType


# ═══════════════════════════════════════════════════════════
#  ПРАВИЛА ПО ИМЕНИ
# ═══════════════════════════════════════════════════════════

# Порядок важен — более специфичные суффиксы раньше.
# ALBEDO — самый первый, потому что часто имя файла содержит
# "albedo" вместе с другими словами (например wall_metal_albedo.png),
# и без приоритета его перебивает метал/нормаль.
NAME_RULES = [
    # ═══ ALBEDO — приоритет ВЫШЕ всех ═══
    (r"(^|[_\-\s])albedo([_\-\s]|$)",       MapType.ALBEDO),
    (r"(^|[_\-\s])alb([_\-\s]|$)",          MapType.ALBEDO),
    (r"(^|[_\-\s])basecolor([_\-\s]|$)",    MapType.ALBEDO),
    (r"(^|[_\-\s])base_color([_\-\s]|$)",   MapType.ALBEDO),
    (r"(^|[_\-\s])base([_\-\s]|$)",         MapType.ALBEDO),
    (r"(^|[_\-\s])diffuse([_\-\s]|$)",      MapType.ALBEDO),
    (r"(^|[_\-\s])diff([_\-\s]|$)",         MapType.ALBEDO),
    (r"(^|[_\-\s])colour([_\-\s]|$)",       MapType.ALBEDO),
    (r"(^|[_\-\s])texture([_\-\s]|$)",      MapType.ALBEDO),
    (r"(^|[_\-\s])tex([_\-\s]|$)",          MapType.ALBEDO),
    (r"(^|[_\-\s])bc([_\-\s]|$)",           MapType.ALBEDO),

    # ═══ ORM — до других, чтобы не спутать ═══
    (r"(^|[_\-\s])orm([_\-\s]|$)",          MapType.ORM),
    (r"(^|[_\-\s])rma([_\-\s]|$)",          MapType.ORM),
    (r"(^|[_\-\s])mra([_\-\s]|$)",          MapType.ORM),
    (r"(^|[_\-\s])arm([_\-\s]|$)",          MapType.ORM),
    (r"(^|[_\-\s])mre([_\-\s]|$)",          MapType.ORM),

    # ═══ EDGE / OUTLINE ═══
    (r"(^|[_\-\s])edge([_\-\s]|$)",         MapType.EDGE),
    (r"(^|[_\-\s])outline([_\-\s]|$)",      MapType.EDGE),
    (r"(^|[_\-\s])contour([_\-\s]|$)",      MapType.EDGE),
    (r"(^|[_\-\s])outl([_\-\s]|$)",         MapType.EDGE),

    # ═══ NORMAL ═══
    (r"(^|[_\-\s])normal([_\-\s]|$)",       MapType.NORMAL),
    (r"(^|[_\-\s])norm([_\-\s]|$)",         MapType.NORMAL),
    (r"(^|[_\-\s])nrm([_\-\s]|$)",          MapType.NORMAL),
    (r"(^|[_\-\s])n([_\-\s]|$)",            MapType.NORMAL),

    # ═══ ROUGHNESS ═══
    (r"(^|[_\-\s])roughness([_\-\s]|$)",    MapType.ROUGHNESS),
    (r"(^|[_\-\s])rough([_\-\s]|$)",        MapType.ROUGHNESS),
    (r"(^|[_\-\s])rgh([_\-\s]|$)",          MapType.ROUGHNESS),

    # ═══ METALLIC ═══
    (r"(^|[_\-\s])metallic([_\-\s]|$)",     MapType.METALLIC),
    (r"(^|[_\-\s])metal([_\-\s]|$)",        MapType.METALLIC),
    (r"(^|[_\-\s])mtl([_\-\s]|$)",          MapType.METALLIC),

    # ═══ AO ═══
    (r"(^|[_\-\s])ao([_\-\s]|$)",           MapType.AO),
    (r"(^|[_\-\s])occlusion([_\-\s]|$)",    MapType.AO),
    (r"(^|[_\-\s])ambient([_\-\s]|$)",      MapType.AO),

    # ═══ HEIGHT ═══
    (r"(^|[_\-\s])height([_\-\s]|$)",       MapType.HEIGHT),
    (r"(^|[_\-\s])disp([_\-\s]|$)",         MapType.HEIGHT),
    (r"(^|[_\-\s])bump([_\-\s]|$)",         MapType.HEIGHT),

    # ═══ Однобуквенные — в самом конце, чтоб не мешали ═══
    (r"(^|[_\-\s])r([_\-\s]|$)",            MapType.ROUGHNESS),
    (r"(^|[_\-\s])m([_\-\s]|$)",            MapType.METALLIC),
    (r"(^|[_\-\s])h([_\-\s]|$)",            MapType.HEIGHT),
]


def detect_by_name(filename: str) -> tuple:
    """
    Возвращает (MapType, confidence) или (UNKNOWN, 0.0).
    """
    stem = os.path.splitext(os.path.basename(filename))[0].lower()
    stem = re.sub(r"[^a-z0-9_\- ]", "", stem)

    for pattern, mtype in NAME_RULES:
        if re.search(pattern, stem):
            return mtype, 0.95
    return MapType.UNKNOWN, 0.0


# ═══════════════════════════════════════════════════════════
#  ПРАВИЛА ПО СОДЕРЖИМОМУ
# ═══════════════════════════════════════════════════════════

def detect_by_content(img: np.ndarray) -> tuple:
    """
    img: float32 [H,W,3] в [0..1].
    Возвращает (MapType, confidence).

    Логика:
      - Normal: B-канал доминирует, средняя длина вектора ≈ 1
      - Edge: почти бинарная, есть и чёрное, и белое
      - Metallic: почти бинарная, одно преобладает
      - AO: grayscale, тёмное, с плавными вариациями
      - Roughness: grayscale, широкое распределение
      - Albedo: цветное, высокая дисперсия между каналами
      - Height: grayscale fallback
    """
    if img.ndim != 3 or img.shape[2] < 3:
        return MapType.UNKNOWN, 0.0

    r, g, b = img[:, :, 0], img[:, :, 1], img[:, :, 2]

    # ─── Цветность ───
    rgb_stack = np.stack([r, g, b], axis=0)
    channel_std = float(rgb_stack.std(axis=0).mean())
    is_grayscale = channel_std < 0.02

    # ─── Нормаль? ───
    xyz = img * 2.0 - 1.0
    lengths = np.linalg.norm(xyz, axis=2)
    mean_len = float(lengths.mean())
    std_len = float(lengths.std())
    b_mean = float(b.mean())
    b_std = float(b.std())

    if (0.85 < mean_len < 1.15
            and std_len < 0.25
            and b_mean > 0.5
            and b_std > 0.03):
        conf = float(1.0 - min(abs(mean_len - 1.0) * 3, 0.4))
        return MapType.NORMAL, conf

    # ─── Grayscale-карты ───
    if is_grayscale:
        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
        mean = float(lum.mean())
        std = float(lum.std())

        low  = float((lum < 0.15).mean())
        high = float((lum > 0.85).mean())
        mid  = float(((lum > 0.15) & (lum < 0.85)).mean())

        # Edge / Outline
        if (low + high) > 0.90 and mid < 0.10:
            if low > 0.02 and high > 0.02:
                return MapType.EDGE, 0.75

        # Metallic
        if (low + high) > 0.75 and mid < 0.25:
            return MapType.METALLIC, 0.85

        # AO
        if mean < 0.6 and std < 0.2:
            return MapType.AO, 0.7

        # Roughness
        if std > 0.05:
            return MapType.ROUGHNESS, 0.6

        # Height
        return MapType.HEIGHT, 0.5

    # ─── Цветное → Albedo ───
    return MapType.ALBEDO, 0.8


# ═══════════════════════════════════════════════════════════
#  ОБЪЕДИНЁННЫЙ ДЕТЕКТ
# ═══════════════════════════════════════════════════════════

def detect(filename: str, img: np.ndarray) -> tuple:
    """
    Возвращает (MapType, confidence, detected_by).
    detected_by: 'name' | 'content' | 'name+content' | 'fallback'

    ALBEDO и ORM форсятся по имени — их содержимое слишком легко
    спутать с другими типами (металл, шум, edge).
    """
    name_type, name_conf = detect_by_name(filename)
    content_type, content_conf = detect_by_content(img)

    # ─── ALBEDO: всегда верим имени ───
    if name_type == MapType.ALBEDO:
        return MapType.ALBEDO, max(name_conf, 0.9), "name"

    # ─── ORM: тоже форсим по имени ───
    if name_type == MapType.ORM:
        return MapType.ORM, max(name_conf, 0.9), "name"

    if name_type != MapType.UNKNOWN and name_type == content_type:
        return name_type, max(name_conf, content_conf), "name+content"

    if name_type != MapType.UNKNOWN and content_type == MapType.UNKNOWN:
        return name_type, name_conf, "name"

    if name_type == MapType.UNKNOWN and content_type != MapType.UNKNOWN:
        return content_type, content_conf, "content"

    if name_type != MapType.UNKNOWN and content_type != MapType.UNKNOWN:
        if content_conf > name_conf:
            return content_type, content_conf * 0.8, "content"
        return name_type, name_conf * 0.8, "name"

    return MapType.UNKNOWN, 0.0, "fallback"