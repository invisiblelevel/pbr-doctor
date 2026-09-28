"""
core/detect.py — определяет тип PBR-карты.

Двухуровнево:
  1. По имени файла (суффиксы: _normal, _n, _roughness, ...).
  2. По содержимому (гистограммы, каналы, статистика).

Возвращает (MapType, confidence, detected_by).
"""

import os
import re
import numpy as np
from core.state import MapType


# ═══════════════════════════════════════════════════════════
#  ПРАВИЛА ПО ИМЕНИ
# ═══════════════════════════════════════════════════════════

# Порядок важен — более специфичные суффиксы раньше
NAME_RULES = [
    # ORM — самым первым, иначе путается с albedo
    (r"(^|[_\-\s])orm([_\-\s]|$)",        MapType.ORM),
    (r"(^|[_\-\s])rma([_\-\s]|$)",        MapType.ORM),
    (r"(^|[_\-\s])mra([_\-\s]|$)",        MapType.ORM),
    (r"(^|[_\-\s])arm([_\-\s]|$)",        MapType.ORM),
    (r"(^|[_\-\s])mre([_\-\s]|$)",        MapType.ORM),
    (r"(^|[_\-\s])occlusionroughnessmetal([_\-\s]|$)", MapType.ORM),
    # Edge / Outline
    (r"(^|[_\-\s])edge([_\-\s]|$)",       MapType.EDGE),
    (r"(^|[_\-\s])outline([_\-\s]|$)",    MapType.EDGE),
    (r"(^|[_\-\s])contour([_\-\s]|$)",    MapType.EDGE),
    (r"(^|[_\-\s])mask([_\-\s]|$)",       MapType.EDGE),
    (r"(^|[_\-\s])outl([_\-\s]|$)",       MapType.EDGE),
    # (регекс, MapType)
    (r"(^|[_\-\s])normal([_\-\s]|$)",     MapType.NORMAL),
    (r"(^|[_\-\s])norm([_\-\s]|$)",       MapType.NORMAL),
    (r"(^|[_\-\s])nrm([_\-\s]|$)",        MapType.NORMAL),
    (r"(^|[_\-\s])n([_\-\s]|$)",          MapType.NORMAL),
    (r"(^|[_\-\s])roughness([_\-\s]|$)",  MapType.ROUGHNESS),
    (r"(^|[_\-\s])rough([_\-\s]|$)",      MapType.ROUGHNESS),
    (r"(^|[_\-\s])rgh([_\-\s]|$)",        MapType.ROUGHNESS),
    (r"(^|[_\-\s])r([_\-\s]|$)",          MapType.ROUGHNESS),
    (r"(^|[_\-\s])metallic([_\-\s]|$)",   MapType.METALLIC),
    (r"(^|[_\-\s])metal([_\-\s]|$)",      MapType.METALLIC),
    (r"(^|[_\-\s])mtl([_\-\s]|$)",        MapType.METALLIC),
    (r"(^|[_\-\s])m([_\-\s]|$)",          MapType.METALLIC),
    (r"(^|[_\-\s])ao([_\-\s]|$)",         MapType.AO),
    (r"(^|[_\-\s])occlusion([_\-\s]|$)",  MapType.AO),
    (r"(^|[_\-\s])ambient([_\-\s]|$)",    MapType.AO),
    (r"(^|[_\-\s])height([_\-\s]|$)",     MapType.HEIGHT),
    (r"(^|[_\-\s])disp([_\-\s]|$)",       MapType.HEIGHT),
    (r"(^|[_\-\s])bump([_\-\s]|$)",       MapType.HEIGHT),
    (r"(^|[_\-\s])h([_\-\s]|$)",          MapType.HEIGHT),
    (r"(^|[_\-\s])albedo([_\-\s]|$)",     MapType.ALBEDO),
    (r"(^|[_\-\s])basecolor([_\-\s]|$)",  MapType.ALBEDO),
    (r"(^|[_\-\s])base_color([_\-\s]|$)", MapType.ALBEDO),
    (r"(^|[_\-\s])diffuse([_\-\s]|$)",    MapType.ALBEDO),
    (r"(^|[_\-\s])color([_\-\s]|$)",      MapType.ALBEDO),
    (r"(^|[_\-\s])col([_\-\s]|$)",        MapType.ALBEDO),
    (r"(^|[_\-\s])diff([_\-\s]|$)",       MapType.ALBEDO),
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
      - Metallic: почти бинарная гистограмма (два пика)
      - Roughness: grayscale, широкое распределение, не бинарное
      - AO: grayscale, тёмное, с плавными вариациями
      - Albedo: цветное, высокая дисперсия между каналами
      - Height: grayscale, любое
    """
    if img.ndim != 3 or img.shape[2] < 3:
        # grayscale подали как 1 канал — редкий случай
        return MapType.UNKNOWN, 0.0

    r, g, b = img[:, :, 0], img[:, :, 1], img[:, :, 2]

    # ─── Цветность: насколько каналы отличаются ───
    rgb_stack = np.stack([r, g, b], axis=0)
    channel_std = float(rgb_stack.std(axis=0).mean())  # разброс между каналами
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
        # Похоже на нормаль. Уверенность выше если mean_len ближе к 1.
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

        # Edge / Outline: бинарная, почти всё в 0 или 1
        if (low + high) > 0.90 and mid < 0.10:
            # Дополнительная проверка: edge обычно ИМЕЕТ и чёрное, и белое
            if low > 0.02 and high > 0.02:
                return MapType.EDGE, 0.75

        # Metallic: почти бинарная, но НЕ edge (одно преобладает)
        if (low + high) > 0.75 and mid < 0.25:
            return MapType.METALLIC, 0.85

        # AO: тёмное, среднее < 0.6, плавное
        if mean < 0.6 and std < 0.2:
            return MapType.AO, 0.7

        # Roughness: grayscale, широкое распределение
        if std > 0.05:
            return MapType.ROUGHNESS, 0.6

        # Height: остаётся как fallback
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
    """
    name_type, name_conf = detect_by_name(filename)
    content_type, content_conf = detect_by_content(img)

    # ORM форсим по имени: содержимое легко спутать с albedo
    if name_type == MapType.ORM:
        return MapType.ORM, max(name_conf, 0.9), "name"

    if name_type != MapType.UNKNOWN and name_type == content_type:
        return name_type, max(name_conf, content_conf), "name+content"

    if name_type != MapType.UNKNOWN and content_type == MapType.UNKNOWN:
        return name_type, name_conf, "name"

    if name_type == MapType.UNKNOWN and content_type != MapType.UNKNOWN:
        return content_type, content_conf, "content"

    if name_type != MapType.UNKNOWN and content_type != MapType.UNKNOWN:
        # Конфликт: имя говорит одно, содержимое другое.
        # Верим содержимому, но снижаем уверенность.
        if content_conf > name_conf:
            return content_type, content_conf * 0.8, "content"
        return name_type, name_conf * 0.8, "name"

    # Ничего не поняли — fallback
    return MapType.UNKNOWN, 0.0, "fallback"