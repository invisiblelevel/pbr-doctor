"""
core/deblur_model.py — обёртка над SCUNet (ONNX, фиксированный вход).

Модель: SCUNet-GAN-fixed.onnx
Путь: assets/models/SCUNet-GAN-fixed.onnx

Вход зафиксирован на [1, 3, 256, 256] — это нужно для DirectML,
который не поддерживает динамические размеры.

Провайдеры:
  1. DmlExecutionProvider — DirectML (NVIDIA / AMD / Intel через DX12).
  2. CPUExecutionProvider — fallback.
"""

import os
import numpy as np
import cv2


# ═══════════════════════════════════════════════════════════
#  КОНСТАНТЫ
# ═══════════════════════════════════════════════════════════

MODEL_FILENAME = "SCUNet-GAN-fixed.onnx"
MODEL_SUBPATH = os.path.join("assets", "models", MODEL_FILENAME)

# Фиксированный размер тайла — совпадает с формой модели
TILE_SIZE = 256
TILE_OVERLAP = 32

PROVIDERS_PRIORITY = [
    "DmlExecutionProvider",
    "CPUExecutionProvider",
]


# ═══════════════════════════════════════════════════════════
#  СИНГЛТОН
# ═══════════════════════════════════════════════════════════

_MODEL = {"session": None, "tried": False, "provider": None,
          "input_name": None, "output_name": None}


def get_nafnet_model(base_dir: str = None):
    """Ленивая загрузка модели SCUNet (fixed shape) через onnxruntime."""
    if _MODEL["tried"]:
        return _MODEL["session"]

    _MODEL["tried"] = True

    if base_dir is None:
        base_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

    model_path = os.path.join(base_dir, MODEL_SUBPATH)

    if not os.path.isfile(model_path):
        return None

    try:
        import onnxruntime as ort
    except ImportError:
        return None

    try:
        available = set(ort.get_available_providers())
        providers = [p for p in PROVIDERS_PRIORITY if p in available]
        if not providers:
            providers = ["CPUExecutionProvider"]


        sess_options = ort.SessionOptions()
        sess_options.graph_optimization_level = (
            ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        )
        sess_options.log_severity_level = 3

        session = ort.InferenceSession(
            model_path,
            sess_options=sess_options,
            providers=providers,
        )

        inp = session.get_inputs()[0]
        out = session.get_outputs()[0]

        _MODEL["session"] = session
        _MODEL["provider"] = session.get_providers()[0]
        _MODEL["input_name"] = inp.name
        _MODEL["output_name"] = out.name


        return session
    except Exception as ex:
        import traceback
        traceback.print_exc()
        _MODEL["session"] = None
        return None


def get_provider() -> str:
    return _MODEL.get("provider")


def is_gpu_active() -> bool:
    p = _MODEL.get("provider") or ""
    return "Dml" in p or "CUDA" in p or "Tensorrt" in p


# ═══════════════════════════════════════════════════════════
#  ИНФЕРЕНС ОДНОГО ТАЙЛА
# ═══════════════════════════════════════════════════════════

def _process_tile(session, tile_rgb_u8: np.ndarray) -> np.ndarray:
    """
    Прогон одного тайла. tile_rgb_u8 ДОЛЖЕН быть ровно 256x256x3.
    Если меньше — вызывающий код должен добить паддингом.
    """
    h, w = tile_rgb_u8.shape[:2]
    assert h == TILE_SIZE and w == TILE_SIZE, \
        f"tile должен быть {TILE_SIZE}x{TILE_SIZE}, а не {h}x{w}"

    blob = tile_rgb_u8.astype(np.float32) / 255.0
    blob = np.transpose(blob, (2, 0, 1))
    blob = np.expand_dims(blob, axis=0)

    input_name = _MODEL["input_name"]
    output_name = _MODEL["output_name"]

    out = session.run([output_name], {input_name: blob})[0]

    out = out[0]
    out = np.transpose(out, (1, 2, 0))
    out = np.clip(out, 0.0, 1.0)
    return (out * 255.0).astype(np.uint8)


# ═══════════════════════════════════════════════════════════
#  ПАДДИНГ ТАЙЛА ДО 256x256
# ═══════════════════════════════════════════════════════════

def _pad_tile_to_256(tile_rgb_u8: np.ndarray) -> np.ndarray:
    """Добивает тайл reflect-паддингом до 256x256."""
    h, w = tile_rgb_u8.shape[:2]
    pad_h = TILE_SIZE - h
    pad_w = TILE_SIZE - w
    if pad_h == 0 and pad_w == 0:
        return tile_rgb_u8
    return np.pad(
        tile_rgb_u8,
        ((0, pad_h), (0, pad_w), (0, 0)),
        mode="reflect",
    )


# ═══════════════════════════════════════════════════════════
#  ИНФЕРЕНС ВСЕЙ КАРТЫ
# ═══════════════════════════════════════════════════════════

def deblur_image(session, img_float: np.ndarray,
                  deficit_mask: np.ndarray = None) -> np.ndarray:
    """
    Прогон всей карты через SCUNet + смешка по маске.

    img_float: [H,W,3] float32 [0..1] в RGB.
    deficit_mask: [H,W] float32 [0..1] — где 1 = мыло, 0 = детали.
    """
    if session is None:
        return img_float

    H, W = img_float.shape[:2]
    img_u8 = np.clip(img_float * 255.0, 0, 255).astype(np.uint8)


    # ─── Маленькая карта (<= TILE_SIZE) — целиком с паддингом ───
    if H <= TILE_SIZE and W <= TILE_SIZE:
        padded = _pad_tile_to_256(img_u8)
        out_u8 = _process_tile(session, padded)[:H, :W]
        out = out_u8.astype(np.float32) / 255.0
    else:
        # ─── Тайлинг 256x256 с overlap ───
        out = np.zeros((H, W, 3), dtype=np.float32)
        weight = np.zeros((H, W, 1), dtype=np.float32)

        step = TILE_SIZE - TILE_OVERLAP

        # Оконная маска (треугольник)
        y_axis = np.linspace(-1, 1, TILE_SIZE, dtype=np.float32)
        tile_win = 1.0 - np.abs(y_axis)
        tile_win = np.clip(tile_win, 0.0, 1.0)
        win_2d = np.outer(tile_win, tile_win)[:, :, None]

        # Позиции тайлов. Последний тайл ставим так чтобы влез ровно 256.
        ys = list(range(0, max(1, H - TILE_OVERLAP), step))
        xs = list(range(0, max(1, W - TILE_OVERLAP), step))
        if ys[-1] + TILE_SIZE < H:
            ys.append(H - TILE_SIZE)
        if xs[-1] + TILE_SIZE < W:
            xs.append(W - TILE_SIZE)

        total_tiles = len(ys) * len(xs)

        done = 0
        for y0 in ys:
            for x0 in xs:
                y1 = y0 + TILE_SIZE
                x1 = x0 + TILE_SIZE

                # Защита на случай если карта меньше 256 по стороне
                if y0 < 0:
                    y0 = 0
                if x0 < 0:
                    x0 = 0
                if y1 > H:
                    y1 = H
                if x1 > W:
                    x1 = W

                tile = img_u8[y0:y1, x0:x1]
                th, tw = tile.shape[:2]

                # Добиваем до 256x256
                padded = _pad_tile_to_256(tile)
                out_padded = _process_tile(session, padded)
                out_tile = out_padded[:th, :tw].astype(np.float32) / 255.0

                w_tile = win_2d[:th, :tw]
                out[y0:y1, x0:x1] += out_tile * w_tile
                weight[y0:y1, x0:x1] += w_tile

                done += 1
                if done % 5 == 0 or done == total_tiles:
                    try:
                        from core.analyzers.base import (
                            emit_progress, get_progress_scale
                        )
                        lo, hi = get_progress_scale()
                        local = done / total_tiles
                        overall = lo + (hi - lo) * local
                        # Передаём и done/total, и общий процент — UI-поллинг
                        # возьмёт done/total для полоски
                        emit_progress(
                            f"Де-блюр: {done}/{total_tiles} тайлов",
                            done=int(overall * 1000),
                            total=1000,
                        )
                    except Exception:
                        pass

        weight = np.maximum(weight, 1e-6)
        out = out / weight


    # ─── Смешка по маске ───
    if deficit_mask is None:
        return np.clip(out, 0.0, 1.0).astype(np.float32)

    m = np.clip(deficit_mask, 0.0, 1.0)
    m = cv2.GaussianBlur(m, (0, 0), sigmaX=8.0)
    m = m[:, :, None]

    result = img_float * (1.0 - m) + out * m
    return np.clip(result, 0.0, 1.0).astype(np.float32)
    