"""
ui/tab_seamless.py — вкладка Seamless.

Фича: привести карты к бесшовному тайлингу.
  - Список загруженных карт с чекбоксами
  - Дропдаун режима (mirror_blend / freq_sep / hipass)
  - Превью до/после для выбранной карты (на уменьшенной копии)
  - Кнопки: "Применить к выбранной", "Применить ко всем", "Сохранить"

Локализация: метод .rebuild() полностью пересобирает содержимое
вкладки на текущем языке.

Прогресс:
  - detect_seam кешируется в entry._seam_cache.
  - Превью считается на уменьшенной копии (fast).
  - apply / save обновляют progress_bar per-map.

Все строки — через core.i18n.t().
"""

import os
import numpy as np
import flet as ft

from core.state import MapType, MapEntry, map_label
from core.io import pil_to_b64, save_array_png_any
from core.seamless import make_seamless, detect_seam
from core.i18n import t

from ui.theme import (
    make_btn, make_btn_tiny, divider,
    FONT, FONT_MONO,
)
from ui.icons import img_icon
from ui.helpers import (log, show_progress, hide_progress,
                        update_progress, downscale_for_preview)


# Ключи локализации: (id, label_key)
MODES = [
    ("mirror_blend", "tab_seamless.mode.mirror_blend.label"),
    ("freq_sep",     "tab_seamless.mode.freq_sep.label"),
    ("hipass",       "tab_seamless.mode.hipass.label"),
]


# ═══════════════════════════════════════════════════════════
#  КЕШ DETECT_SEAM
# ═══════════════════════════════════════════════════════════

def _get_seam(entry: MapEntry) -> dict:
    """
    Возвращает результат detect_seam(entry.working).
    Кеширует в entry._seam_cache — чтобы не гонять на каждый рендер.
    """
    cache = getattr(entry, "_seam_cache", None)
    if cache is None:
        cache = detect_seam(entry.working)
        try:
            entry._seam_cache = cache
        except Exception:
            pass
    return cache


def _invalidate_seam(entry: MapEntry):
    """Сбрасывает кеш seam — вызывать после изменения entry.working."""
    try:
        entry._seam_cache = None
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════
#  ГЛАВНАЯ ФУНКЦИЯ
# ═══════════════════════════════════════════════════════════

def build_seamless_tab(S: dict, page: ft.Page) -> ft.Control:
    """
    Возвращает Column с вкладкой Seamless.
    У результата есть метод .rebuild() — пересобирает весь UI
    на текущем языке.
    """
    T = S["theme"]

    # ─── Состояние вкладки ───
    if "seamless_checks" not in S:
        S["seamless_checks"] = {}
    if "seamless_mode" not in S:
        S["seamless_mode"] = "mirror_blend"
    if "seamless_selected" not in S:
        S["seamless_selected"] = None

    # ─── Dir picker — один раз на всю вкладку ───
    dir_picker = ft.FilePicker()
    page.services.append(dir_picker)

    # ─── Постоянные контейнеры ───
    list_col = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO, expand=True)
    preview_col = ft.Column(spacing=8, expand=True)

    # ─── Кеш превью ───
    # { (idx, mode) : b64_after }
    preview_cache = {}

    # ─── Перестройки внутренние ───

    def rebuild_list():
        list_col.controls.clear()
        if not S["maps"]:
            list_col.controls.append(_empty_state(T))
            return
        for idx, entry in enumerate(S["maps"]):
            list_col.controls.append(
                _make_map_row(S, page, idx, entry,
                              rebuild_list, rebuild_preview)
            )

    def rebuild_preview():
        preview_col.controls.clear()
        idx = S.get("seamless_selected")
        if idx is None or idx < 0 or idx >= len(S["maps"]):
            preview_col.controls.append(_empty_preview(T))
            return
        entry = S["maps"][idx]
        preview_col.controls.append(
            _preview_block(S, T, entry, idx, preview_cache)
        )

    def rebuild_inner():
        rebuild_list()
        rebuild_preview()
        try:
            if list_col.page is not None:
                list_col.page.update()
        except Exception:
            pass

    # ─── Async-хендлеры ───

    async def on_apply_all(_):
        selected = [i for i, v in S["seamless_checks"].items() if v]
        if not selected:
            log(S, t("tab_seamless.log.nothing_selected"), "#ff9800")
            return
        await _apply_to_selected(S, page, selected, rebuild_inner,
                                 preview_cache)
        preview_cache.clear()

    async def on_apply_one(_):
        idx = S.get("seamless_selected")
        if idx is None:
            log(S, t("tab_seamless.log.no_preview_map"), "#ff9800")
            return
        await _apply_to_selected(S, page, [idx], rebuild_inner,
                                 preview_cache)
        preview_cache.clear()

    async def on_save(_):
        await _save_seamless(S, page, dir_picker)

    # ─── Построение хедера ───

    def on_mode_change(e):
        S["seamless_mode"] = e.control.value
        log(S, t("tab_seamless.log.mode_changed",
                 mode=t(f"tab_seamless.mode.{e.control.value}.label")),
            T["fg2"])
        rebuild_preview()
        page.update()

    def build_header() -> ft.Control:
        mode_dd = ft.Dropdown(
            value=S["seamless_mode"],
            options=[ft.dropdown.Option(key=k, text=t(label_key))
                     for k, label_key in MODES],
            width=170,
            text_style=ft.TextStyle(font_family=FONT,
                                    color=T["fg"], size=12),
            border=ft.OutlineInputBorder(),
            bgcolor=T["input"],
            content_padding=ft.Padding.symmetric(vertical=4, horizontal=8),
        )
        mode_dd.on_select = on_mode_change

        btn_apply_one = make_btn_tiny(
            t("tab_seamless.btn_one"),
            on_click=on_apply_one,
            color=T["accent"], icon=None,
            fg=T["fg"], fg3=T["fg3"], input_bg=T["input"],
        )
        btn_apply_all = make_btn_tiny(
            t("tab_seamless.btn_all"),
            on_click=on_apply_all,
            color=T["success"], icon=None,
            fg=T["fg"], fg3=T["fg3"], input_bg=T["input"],
        )
        btn_save = make_btn_tiny(
            t("tab_seamless.btn_save"),
            on_click=on_save,
            color=T["save"], icon="save",
            fg=T["fg"], fg3=T["fg3"], input_bg=T["input"],
        )

        return ft.Row([
            img_icon("grid-3x3", T["accent"], 20),
            ft.Text(t("tab_seamless.title"), color=T["fg"], size=16,
                    font_family=FONT, weight=ft.FontWeight.W_600),
            ft.Container(expand=True),
            ft.Text(t("tab_seamless.mode_label"), color=T["fg2"],
                    size=12, font_family=FONT),
            mode_dd,
            btn_apply_one,
            btn_apply_all,
            btn_save,
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    # ─── Сам Column вкладки ───

    result = ft.Column([], expand=True, spacing=8)

    def rebuild():
        rebuild_list()
        rebuild_preview()

        result.controls.clear()
        result.controls.append(build_header())
        result.controls.append(divider(T["input"]))
        result.controls.append(ft.Row([
            ft.Container(
                content=list_col,
                width=300,
                bgcolor=T["panel"],
                border=ft.Border.all(1, T["input"]),
                border_radius=12,
                padding=8,
            ),
            ft.Container(
                content=preview_col,
                expand=True,
                bgcolor=T["panel"],
                border=ft.Border.all(1, T["input"]),
                border_radius=12,
                padding=12,
            ),
        ], expand=True, spacing=8))

        try:
            if result.page is not None:
                result.page.update()
        except Exception:
            pass

    result.rebuild = rebuild
    result.list_col = list_col
    result.preview_col = preview_col

    rebuild()
    return result


# ═══════════════════════════════════════════════════════════
#  СПИСОК КАРТ
# ═══════════════════════════════════════════════════════════

def _empty_state(T):
    return ft.Container(
        content=ft.Column([
            img_icon("grid-3x3", T["fg3"], 48),
            ft.Text(t("tab_seamless.empty.list"),
                    color=T["fg2"], size=13, font_family=FONT),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
        alignment=ft.Alignment.CENTER,
        padding=ft.Padding.symmetric(vertical=60),
    )


def _make_map_row(S, page, idx, entry: MapEntry,
                  rebuild_list, rebuild_preview):
    T = S["theme"]

    checked = S["seamless_checks"].get(idx, True)

    def on_check(e):
        S["seamless_checks"][idx] = e.control.value
        page.update()

    def on_click(e):
        S["seamless_selected"] = idx
        rebuild_preview()
        page.update()

    chk = ft.Checkbox(value=checked, on_change=on_check,
                      fill_color=T["input"], check_color=T["accent"])

    seam = _get_seam(entry)
    seam_color = T["danger"] if seam["has_seam"] else T["success"]
    if seam["has_seam"]:
        seam_label = t("tab_seamless.seam_bad", diff=seam["max_diff"])
    else:
        seam_label = t("tab_seamless.seam_ok")

    is_selected = (S.get("seamless_selected") == idx)

    return ft.Container(
        content=ft.Row([
            chk,
            ft.Column([
                ft.Text(entry.filename, color=T["fg"], size=14,
                        font_family=FONT,
                        overflow=ft.TextOverflow.ELLIPSIS),
                ft.Text(map_label(entry.map_type), color=T["fg3"],
                        size=11, font_family=FONT),
            ], spacing=0, expand=True),
            ft.Text(seam_label, color=seam_color, size=12,
                    font_family=FONT_MONO),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=6,
        border_radius=6,
        bgcolor=T["card"] if is_selected else "transparent",
        on_click=on_click,
        ink=True,
    )


# ═══════════════════════════════════════════════════════════
#  ПРЕВЬЮ ДО/ПОСЛЕ (на уменьшенной копии)
# ═══════════════════════════════════════════════════════════

def _empty_preview(T):
    return ft.Container(
        content=ft.Column([
            img_icon("image", T["fg3"], 40),
            ft.Text(t("tab_seamless.empty.preview"),
                    color=T["fg3"], size=12, font_family=FONT),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
        alignment=ft.Alignment.CENTER,
        padding=ft.Padding.symmetric(vertical=80),
    )


def _preview_block(S, T, entry: MapEntry, idx: int, cache: dict):
    """
    Два превью рядом: до и после.
    make_seamless считается на уменьшенной копии (512px) — быстро.
    """
    mode = S.get("seamless_mode", "mirror_blend")

    # ─── BEFORE — уменьшаем ───
    try:
        small_before = downscale_for_preview(entry.working, max_size=512)
        before_b64 = pil_to_b64(small_before, max_size=280)
    except Exception:
        before_b64 = None

    # ─── AFTER — из кеша или считаем ───
    cache_key = (idx, mode)
    after_b64 = cache.get(cache_key)

    if after_b64 is None:
        try:
            small_before2 = downscale_for_preview(entry.working, max_size=512)
            is_normal = (entry.map_type == MapType.NORMAL)
            after_small = make_seamless(small_before2, mode=mode,
                                        is_normal=is_normal)
            after_b64 = pil_to_b64(after_small, max_size=280)
            cache[cache_key] = after_b64
        except Exception:
            after_b64 = None

    def _img(b64, label, color):
        if b64 is None:
            return ft.Container(
                content=ft.Text("—", color=T["fg3"], size=12),
                height=260, alignment=ft.Alignment.CENTER,
            )
        return ft.Column([
            ft.Text(label, color=color, size=13, font_family=FONT,
                    weight=ft.FontWeight.W_600),
            ft.Container(
                content=ft.Image(src=f"data:image/png;base64,{b64}",
                                 fit=ft.BoxFit.CONTAIN),
                height=260, bgcolor=T["card"],
                border_radius=8, alignment=ft.Alignment.CENTER,
            ),
        ], spacing=4, expand=True)

    seam = _get_seam(entry)
    seam_info = ft.Text(
        t("tab_seamless.seam_info",
          lr=seam["lr_diff"], tb=seam["tb_diff"], mx=seam["max_diff"]),
        color=T["fg2"], size=13, font_family=FONT_MONO,
    )

    return ft.Column([
        ft.Text(entry.filename, color=T["fg"], size=15,
                font_family=FONT, weight=ft.FontWeight.W_600),
        ft.Text(t("tab_seamless.mode_line",
                  mode=t(f"tab_seamless.mode.{mode}.label")),
                color=T["fg3"], size=13, font_family=FONT),
        seam_info,
        ft.Container(height=6),
        ft.Row([
            _img(before_b64, t("tab_seamless.before"), T["fg2"]),
            _img(after_b64, t("tab_seamless.after"), T["accent"]),
        ], spacing=10, expand=True),
    ], spacing=4)


# ═══════════════════════════════════════════════════════════
#  ПРИМЕНИТЬ (с прогрессом)
# ═══════════════════════════════════════════════════════════

async def _apply_to_selected(S, page, indices, rebuild_all, preview_cache):
    T = S["theme"]
    mode = S.get("seamless_mode", "mirror_blend")

    total = len(indices)
    await show_progress(
        S, page,
        t("tab_seamless.log.applying",
          mode=t(f"tab_seamless.mode.{mode}.label"), n=total)
    )

    ok = 0
    for i, idx in enumerate(indices):
        if idx < 0 or idx >= len(S["maps"]):
            continue
        entry = S["maps"][idx]

        update_progress(
            S, page, i, total,
            f"{i + 1} / {total}: {entry.filename}"
        )

        try:
            is_normal = (entry.map_type == MapType.NORMAL)
            fixed = make_seamless(entry.working, mode=mode,
                                   is_normal=is_normal)
        except Exception as ex:
            log(S, f"✗ {entry.filename}: {ex}", "#e53935")
            continue

        entry.fix_history.append({
            "issue_code": "seamless",
            "fix_id": f"seamless:{mode}",
            "fix_label": t(f"tab_seamless.mode.{mode}.label"),
            "sev_before": "warn",
            "sev_after": "ok",
            "issues_before": 0,
            "issues_after": 0,
            "prev_working": entry.working.copy(),
            "prev_report": entry.report,
        })
        entry.working = fixed
        entry.had_fixes = True

        # сброс кеша seam — карта изменилась
        _invalidate_seam(entry)

        from core.analyzers import get_analyzer
        analyzer = get_analyzer(entry.map_type.value)
        if analyzer:
            try:
                entry.report = analyzer.analyze(entry.working)
            except Exception:
                pass

        seam_after = _get_seam(entry)
        log(S, t("tab_seamless.log.applied_one",
                 name=entry.filename, diff=seam_after["max_diff"]),
            "#4caf50")
        ok += 1

    update_progress(S, page, total, total)
    await hide_progress(S, page)
    log(S, t("tab_seamless.log.applied", ok=ok, total=total), T["fg2"])

    if preview_cache is not None:
        preview_cache.clear()

    rebuild_all()


# ═══════════════════════════════════════════════════════════
#  СОХРАНЕНИЕ (с прогрессом)
# ═══════════════════════════════════════════════════════════

async def _save_seamless(S, page, dir_picker):
    """Сохраняет все карты, к которым применялся seamless."""
    T = S["theme"]

    selected = [e for e in S["maps"]
                if any(r.get("issue_code") == "seamless"
                       for r in e.fix_history)]

    if not selected:
        log(S, t("tab_seamless.log.no_seamless"), "#ff9800")
        return

    folder = await dir_picker.get_directory_path(
        dialog_title=t("tab_seamless.log.pick_folder"),
    )
    if not folder:
        return

    total = len(selected)
    await show_progress(S, page, t("tab_seamless.btn_save") + "...")

    saved = 0
    for i, entry in enumerate(selected):
        update_progress(
            S, page, i, total,
            f"{i + 1} / {total}: {entry.filename}"
        )

        base, _ = os.path.splitext(entry.filename)
        out_name = f"{base}_seamless.png"
        out_path = os.path.join(folder, out_name)
        try:
            save_array_png_any(entry.working, out_path, bit_depth=8)
            log(S, "💾 " + t("tab_seamless.log.saved_one", name=out_name),
                "#4caf50")
            saved += 1
        except Exception as ex:
            log(S, t("tab_seamless.log.save_fail",
                     name=out_name, err=str(ex)), "#e53935")

    update_progress(S, page, total, total)
    await hide_progress(S, page)
    log(S, t("tab_seamless.log.saved",
             saved=saved, total=total, folder=folder), T["fg2"])
    page.update()