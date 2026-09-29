"""
core/deblur_model.py — обёртка над SCUNet (ONNX).

Модель: SCUNet-GAN.onnx от deepghs/image_restoration
Размер: ~91 MB.
Путь: assets/models/SCUNet-GAN.onnx

SCUNet обучен на шумных данных (не только motion blur),
должен работать лучше на текстурах чем NAFNet.

Работает через OpenCV dnn.
Требует кратные 128 размеры входа — тайлинг по 256×256.
"""

import os
import numpy as np
import cv2


# ═══════════════════════════════════════════════════════════
#  КОНСТАНТЫ
# ═══════════════════════════════════════════════════════════

MODEL_FILENAME = "SCUNet-GAN.onnx"
MODEL_SUBPATH = os.path.join("assets", "models", MODEL_FILENAME)

# SCUNet требует кратные 128
TILE_SIZE = 256
TILE_OVERLAP = 32


# ═══════════════════════════════════════════════════════════
#  СИНГЛТОН
# ═══════════════════════════════════════════════════════════

_MODEL = {"net": None, "tried": False}


def get_nafnet_model(base_dir: str = None):
    """Ленивая загрузка модели (один раз)."""
    if _MODEL["tried"]:
        return _MODEL["net"]

    _MODEL["tried"] = True

    if base_dir is None:
        base_dir = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

    model_path = os.path.join(base_dir, MODEL_SUBPATH)

    if not os.path.isfile(model_path):
        print(f"[scunet] модель не найдена: {model_path}")
        return None

    try:
        net = cv2.dnn.readNetFromONNX(model_path)
        _MODEL["net"] = net
        print(f"[scunet] модель загружена: {model_path}")
        return net
    except Exception as ex:
        print(f"[scunet] ошибка загрузки модели: {ex}")
        _MODEL["net"] = None
        return None


# ═══════════════════════════════════════════════════════════
#  ИНФЕРЕНС ОДНОГО ТАЙЛА
# ═══════════════════════════════════════════════════════════

def _process_tile(net, tile_rgb_u8: np.ndarray) -> np.ndarray:
    """
    Прогон одного тайла.
    tile_rgb_u8: [h,w,3] uint8, RGB. Размер должен быть кратен 128.
    Возвращает [h,w,3] uint8 RGB.
    """
    h, w = tile_rgb_u8.shape[:2]

    blob = cv2.dnn.blobFromImage(
        tile_rgb_u8, 1.0 / 255.0, (w, h),
        (0, 0, 0), swapRB=False, crop=False,
    )
    net.setInput(blob)
    out = net.forward()  # [1, 3, h, w]

    out = out[0].transpose(1, 2, 0)
    out = np.clip(out, 0.0, 1.0)
    return (out * 255.0).astype(np.uint8)


# ═══════════════════════════════════════════════════════════
#  ИНФЕРЕНС ВСЕЙ КАРТЫ (тайлинг + маска)
# ═══════════════════════════════════════════════════════════

def deblur_image(net, img_float: np.ndarray,
                  deficit_mask: np.ndarray = None) -> np.ndarray:
    """
    Прогон всей карты через SCUNet + смешка по маске.

    img_float: [H,W,3] float32 [0..1] в RGB.
    deficit_mask: [H,W] float32 [0..1] — где 1 = мыло, 0 = детали.
    """
    if net is None:
        return img_float

    H, W = img_float.shape[:2]
    img_u8 = np.clip(img_float * 255.0, 0, 255).astype(np.uint8)

    # ─── Маленькая карта — целиком ───
    if H <= TILE_SIZE and W <= TILE_SIZE:
        # Паддинг до кратного 128
        pad_h = (128 - (H % 128)) % 128
        pad_w = (128 - (W % 128)) % 128
        if pad_h or pad_w:
            padded = np.pad(
                img_u8,
                ((0, pad_h), (0, pad_w), (0, 0)),
                mode="reflect",
            )
        else:
            padded = img_u8

        out_u8 = _process_tile(net, padded)[:H, :W]
        out = out_u8.astype(np.float32) / 255.0
    else:
        # ─── Тайлинг ───
        out = np.zeros((H, W, 3), dtype=np.float32)
        weight = np.zeros((H, W, 1), dtype=np.float32)

        step = TILE_SIZE - TILE_OVERLAP

        # Оконная маска (треугольник) для плавной сборки
        y_axis = np.linspace(-1, 1, TILE_SIZE, dtype=np.float32)
        tile_win = 1.0 - np.abs(y_axis)
        tile_win = np.clip(tile_win, 0.0, 1.0)
        win_2d = np.outer(tile_win, tile_win)[:, :, None]

        ys = list(range(0, max(1, H - TILE_OVERLAP), step))
        xs = list(range(0, max(1, W - TILE_OVERLAP), step))

        for y in ys:
            for x in xs:
                y0 = min(y, H - TILE_SIZE) if H > TILE_SIZE else 0
                x0 = min(x, W - TILE_SIZE) if W > TILE_SIZE else 0
                y0 = max(0, y0)
                x0 = max(0, x0)
                y1 = min(y0 + TILE_SIZE, H)
                x1 = min(x0 + TILE_SIZE, W)
                th = y1 - y0
                tw = x1 - x0

                if th < 8 or tw < 8:
                    continue

                tile = img_u8[y0:y1, x0:x1]

                # Паддинг до кратного 128
                pad_h = (128 - (th % 128)) % 128
                pad_w = (128 - (tw % 128)) % 128
                if pad_h or pad_w:
                    tile = np.pad(
                        tile,
                        ((0, pad_h), (0, pad_w), (0, 0)),
                        mode="reflect",
                    )

                out_tile = _process_tile(net, tile)
                out_tile = out_tile[:th, :tw].astype(np.float32) / 255.0

                w_tile = win_2d[:th, :tw]
                out[y0:y1, x0:x1] += out_tile * w_tile
                weight[y0:y1, x0:x1] += w_tile

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