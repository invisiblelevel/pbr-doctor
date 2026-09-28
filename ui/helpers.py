"""
ui/helpers.py — лог, статистика, прогресс-бары.

Работает с любым dict-like S (словарём состояния из core/state.py).
Не импортирует core — не создаёт циклических зависимостей.
"""

import asyncio
import flet as ft

FONT = "Segoe UI"
FONT_MONO = "Consolas"


# ═══════════════════════════════════════════════════════════
#  ЛОГ
# ═══════════════════════════════════════════════════════════

def log(S: dict, text: str, color: str = None, fg2: str = "#9aa0a6"):
    """Добавляет строку в лог и обновляет ListView."""
    S["log_lines"].append((text, color or fg2))
    if len(S["log_lines"]) > 200:
        S["log_lines"].pop(0)
    refresh_log(S)


def refresh_log(S: dict):
    """Перерисовывает весь лог из S['log_lines']."""
    lc = S.get("log_column_bottom")
    if lc is None:
        return
    lc.controls.clear()
    for txt, col in S["log_lines"]:
        lc.controls.append(
            ft.Text(txt, color=col, size=13, font_family=FONT_MONO,
                    selectable=True, expand=True)
        )
    # Обновляем свёрнутый preview, если есть
    prev = S.get("log_collapsed_preview")
    if prev is not None:
        if S["log_lines"]:
            last_txt, last_col = S["log_lines"][-1]
            prev.value = last_txt
            prev.color = last_col
        else:
            prev.value = ""


def clear_log(S: dict):
    """Очищает лог."""
    S["log_lines"].clear()
    refresh_log(S)


# ═══════════════════════════════════════════════════════════
#  СТАТИСТИКА
# ═══════════════════════════════════════════════════════════

def add_stat(S: dict, label: str, value: str,
             color: str = None, fg2: str = "#9aa0a6",
             fg3: str = "#5f6368"):
    """Добавляет строку в панель статистики."""
    col = color or fg2
    S["stats_lines"].append((label, value, col))
    col_ctrl = S.get("stats_column")
    if col_ctrl is None:
        return
    col_ctrl.controls.append(
        ft.Row([
            ft.Text(label, color=fg3, size=13, font_family=FONT, width=95),
            ft.Text(value, color=col, size=13, font_family=FONT_MONO,
                    weight=ft.FontWeight.W_600),
        ], spacing=8)
    )


def clear_stats(S: dict):
    """Очищает панель статистики."""
    S["stats_lines"].clear()
    col_ctrl = S.get("stats_column")
    if col_ctrl is not None:
        col_ctrl.controls.clear()


# ═══════════════════════════════════════════════════════════
#  ПРОГРЕСС-БАРЫ (async)
# ═══════════════════════════════════════════════════════════

async def show_progress(S: dict, page: ft.Page, text: str = "Обработка...",
                        fg2: str = "#9aa0a6"):
    """Показать indeterminate прогресс-плашку с текстом."""
    panel = S.get("progress_panel")
    bar = S.get("progress_bar")
    lbl = S.get("progress_text")

    if panel:
        panel.visible = True
    if bar:
        bar.visible = True
        bar.value = None
    if lbl:
        lbl.value = text
        lbl.visible = True

    page.update()
    await asyncio.sleep(0.05)
    page.update()


async def hide_progress(S: dict, page: ft.Page):
    """Спрятать прогресс-плашку."""
    panel = S.get("progress_panel")
    if panel:
        panel.visible = False
    page.update()
    await asyncio.sleep(0.02)


def show_indeterminate(S: dict, page: ft.Page, text: str = "Обработка..."):
    """То же, что show_progress, но без await — для sync-контекста."""
    panel = S.get("progress_panel")
    bar = S.get("progress_bar")
    lbl = S.get("progress_text")

    if panel:
        panel.visible = True
    if bar:
        bar.visible = True
        bar.value = None
    if lbl:
        lbl.value = text
        lbl.visible = True

    try:
        page.update()
    except Exception:
        pass


def update_progress(S: dict, page: ft.Page,
                    done: int, total: int = 0, text: str = None):
    """Обновляет текст прогресс-плашки. Полоска всегда бегает."""
    panel = S.get("progress_panel")
    bar = S.get("progress_bar")
    lbl = S.get("progress_text")

    if panel:
        panel.visible = True
    if bar:
        bar.visible = True
        bar.value = None
    if lbl:
        lbl.visible = True
        if text is not None:
            lbl.value = text
        elif total > 0:
            lbl.value = f"{done} / {total}"

    try:
        page.update()
    except Exception:
        pass


def downscale_for_preview(arr, max_size: int = 512):
    """Уменьшает numpy-массив [H,W,3] float32 [0..1] до max_size."""
    import numpy as np
    import cv2

    h, w = arr.shape[:2]
    if max(h, w) <= max_size:
        return arr.astype(np.float32)

    scale = max_size / float(max(h, w))
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))

    resized = cv2.resize(arr.astype(np.float32), (new_w, new_h),
                         interpolation=cv2.INTER_AREA)
    return resized