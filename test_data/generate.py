"""
test_data/generate.py — генерит тестовые PBR-карты для проверки анализаторов.

Запуск:
    python test_data/generate.py

Кладёт PNG в test_data/:
    normal_clean.png      — чистая (средняя нормаль ≈ (0,0,1))
    normal_baked.png      — запечён свет (сдвиг 20°)
    normal_broken_b.png   — битый B-канал (B=0.5 плоский)
    not_normal.png        — вообще не нормаль (серый шум)
    roughness_dead.png    — мёртвая roughness (всё в 0.5)
    roughness_color.png   — цветная roughness (ошибка)
    metallic_muddy.png    — muddy металлик (градиенты)
    metallic_clean.png    — чистая бинарная металличность
    ao_clean.png          — нормальное AO
    ao_inverted.png       — перевёрнутое AO
    test_orm.png          — ORM (R=AO, G=Rough, B=Metal)
"""

import os
import numpy as np
from PIL import Image


OUT_DIR = os.path.dirname(os.path.abspath(__file__))


def encode_normal(xyz: np.ndarray) -> np.ndarray:
    """XYZ [-1..1] → RGB [0..255] uint8."""
    rgb = (xyz + 1.0) * 0.5
    return np.clip(rgb * 255.0, 0, 255).astype(np.uint8)


def encode_rgb01(rgb: np.ndarray) -> np.ndarray:
    """RGB [0..1] → uint8 [0..255]."""
    return np.clip(rgb * 255.0, 0, 255).astype(np.uint8)


# ═══════════════════════════════════════════════════════════
#  NORMAL
# ═══════════════════════════════════════════════════════════

def make_clean(size: int = 512) -> np.ndarray:
    """Плоская нормаль с лёгким шумом — средний вектор ≈ (0,0,1)."""
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    nx = 0.15 * np.sin(xx / 40.0)
    ny = 0.15 * np.sin(yy / 40.0)
    nz = np.sqrt(np.clip(1.0 - nx * nx - ny * ny, 0.0, 1.0))
    return np.stack([nx, ny, nz], axis=-1)


def make_baked(size: int = 512, angle_deg: float = 20.0) -> np.ndarray:
    """То же, что clean, но повёрнуто на angle_deg вокруг оси X."""
    base = make_clean(size)
    a = np.radians(angle_deg)
    ca, sa = np.cos(a), np.sin(a)
    x = base[..., 0]
    y = base[..., 1]
    z = base[..., 2]
    return np.stack([x, y * ca - z * sa, y * sa + z * ca], axis=-1)


def make_broken_b(size: int = 512) -> np.ndarray:
    """Нормаль, но B-канал выставлен в 0.5 (плоский)."""
    base = make_clean(size)
    out = base.copy()
    out[..., 2] = 0.0
    return out


def make_not_normal(size: int = 512) -> np.ndarray:
    """Серый шум — анализатор должен сказать 'это не нормаль'."""
    rng = np.random.default_rng(42)
    g = rng.normal(0.5, 0.05, (size, size)).astype(np.float32)
    g = np.clip(g, 0, 1)
    return np.stack([g, g, g], axis=-1)


# ═══════════════════════════════════════════════════════════
#  ROUGHNESS
# ═══════════════════════════════════════════════════════════

def make_dead_roughness(size: int = 512) -> np.ndarray:
    """Плоская карта — вся в районе 0.5. Мёртвая."""
    rng = np.random.default_rng(1)
    g = 0.5 + rng.normal(0, 0.005, (size, size)).astype(np.float32)
    g = np.clip(g, 0, 1)
    return np.stack([g, g, g], axis=-1)


def make_colorful_roughness(size: int = 512) -> np.ndarray:
    """Цветная карта — генератор сунул цвет в roughness."""
    rng = np.random.default_rng(2)
    r = 0.4 + rng.random((size, size)).astype(np.float32) * 0.3
    g = 0.5 + rng.random((size, size)).astype(np.float32) * 0.3
    b = 0.6 + rng.random((size, size)).astype(np.float32) * 0.3
    return np.stack([r, g, b], axis=-1)


# ═══════════════════════════════════════════════════════════
#  METALLIC
# ═══════════════════════════════════════════════════════════

def make_muddy_metallic(size: int = 512) -> np.ndarray:
    """Металлик с градиентами — половина карты в серой зоне."""
    rng = np.random.default_rng(3)
    g = np.zeros((size, size), dtype=np.float32)
    grad = np.linspace(0.2, 0.8, size, dtype=np.float32)
    g[:, size // 2:] = grad[None, :size - size // 2]
    g += rng.normal(0, 0.02, (size, size)).astype(np.float32)
    g = np.clip(g, 0, 1)
    return np.stack([g, g, g], axis=-1)


def make_clean_metallic(size: int = 512) -> np.ndarray:
    """Чистая бинарная металличность — пятна металла на диэлектрике."""
    rng = np.random.default_rng(4)
    g = np.zeros((size, size), dtype=np.float32)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    for _ in range(5):
        cx = rng.integers(50, size - 50)
        cy = rng.integers(50, size - 50)
        r = rng.integers(30, 100)
        mask = ((xx - cx) ** 2 + (yy - cy) ** 2) < r * r
        g[mask] = 1.0
    return np.stack([g, g, g], axis=-1)


# ═══════════════════════════════════════════════════════════
#  AO
# ═══════════════════════════════════════════════════════════

def make_clean_ao(size: int = 512) -> np.ndarray:
    """Нормальное AO — тёмные области в углах/щелях, светлое в центре."""
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    cx, cy = size / 2, size / 2
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (size / 2)
    g = np.clip(1.0 - dist * 0.7, 0.1, 1.0)
    g[100:130, 50:size - 50] = 0.15
    g[350:380, 50:size - 50] = 0.15
    return np.stack([g, g, g], axis=-1)


def make_inverted_ao(size: int = 512) -> np.ndarray:
    """Перевёрнутое AO — белое = тень (ошибка полярности)."""
    normal = make_clean_ao(size)
    inv = 1.0 - normal
    return inv


# ═══════════════════════════════════════════════════════════
#  ORM (R=AO, G=Roughness, B=Metallic)
# ═══════════════════════════════════════════════════════════

def make_orm(size: int = 512) -> np.ndarray:
    """
    ORM-карта:
      R = AO (радиальный градиент, тёмное по краям)
      G = Roughness (широкий диапазон + шум)
      B = Metallic (бинарное, пятна металла)
    """
    rng = np.random.default_rng(7)
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    cx, cy = size / 2, size / 2

    # R — AO: радиальное затемнение к краям + лёгкий шум
    dist = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / (size / 2)
    r = np.clip(1.0 - dist * 0.7, 0.15, 1.0)
    r += rng.normal(0, 0.02, (size, size)).astype(np.float32)
    r = np.clip(r, 0, 1)

    # G — Roughness: широкий диапазон + синус-рябь + шум
    g = 0.3 + 0.6 * rng.random((size, size)).astype(np.float32)
    g += 0.1 * np.sin(xx / 30.0) * np.cos(yy / 30.0)
    g = np.clip(g, 0, 1)

    # B — Metallic: бинарное, пятна
    b = np.zeros((size, size), dtype=np.float32)
    for _ in range(4):
        px = rng.integers(60, size - 60)
        py = rng.integers(60, size - 60)
        rad = rng.integers(40, 110)
        mask = ((xx - px) ** 2 + (yy - py) ** 2) < rad * rad
        b[mask] = 1.0

    return np.stack([r, g, b], axis=-1)


# ═══════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════

def main():
    # (имя, массив, энкодер)
    cases = [
        ("normal_clean.png",      make_clean(),              encode_normal),
        ("normal_baked.png",      make_baked(),              encode_normal),
        ("normal_broken_b.png",   make_broken_b(),           encode_normal),
        ("not_normal.png",        make_not_normal(),         encode_rgb01),
        ("roughness_dead.png",    make_dead_roughness(),     encode_rgb01),
        ("roughness_color.png",   make_colorful_roughness(), encode_rgb01),
        ("metallic_muddy.png",    make_muddy_metallic(),     encode_rgb01),
        ("metallic_clean.png",    make_clean_metallic(),     encode_rgb01),
        ("ao_clean.png",          make_clean_ao(),           encode_rgb01),
        ("ao_inverted.png",       make_inverted_ao(),        encode_rgb01),
        ("test_orm.png",          make_orm(),                encode_rgb01),
    ]
    for name, data, encoder in cases:
        rgb = encoder(data)
        path = os.path.join(OUT_DIR, name)
        Image.fromarray(rgb, mode="RGB").save(path)
        print(f"  saved: {path}")

    print(f"\nDone. {len(cases)} файлов в test_data/")


if __name__ == "__main__":
    main()