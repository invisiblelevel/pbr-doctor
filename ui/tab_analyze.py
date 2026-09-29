"""
ui/tab_analyze.py — главная вкладка PBR Doctor.

Возможности:
  - Загрузка файлов через кнопку "Add files"
  - Авто-детект типа каждой карты (с возможностью переопределить)
  - Кнопка "Analyze All" -> анализ всех карт
  - Кнопка "Save fixed" -> сохранение результатов (8 / 16-bit)
  - Таблица результатов с светофором
  - Клик по строке -> детали в правой панели

Локализация: метод .rebuild() полностью пересобирает содержимое
вкладки на текущем языке.

Прогресс:
  - load_files / analyze_all / _do_save обновляют progress_bar
    через update_progress() — per-file.

Все строки — через core.i18n.t().
"""

import os
import flet as ft

from core.state import MapType, MapEntry, map_label
from core.io import (load_rgb_float, get_file_size, fmt_size,
                     save_array_png_any)
from core.detect import detect
from core.analyzers import get_analyzer
from core.i18n import t

from ui.theme import (
    make_btn, make_btn_compact, make_btn_tiny, divider,
    FONT, FONT_MONO,
)
from ui.icons import img_icon
from ui.helpers import (log, show_progress, hide_progress,
                        update_progress)


SEV_COLORS = {
    "ok":   "#4caf50",
    "warn": "#ff9800",
    "fail": "#e53935",
}


# ═══════════════════════════════════════════════════════════
#  ГЛАВНАЯ ФУНКЦИЯ
# ═══════════════════════════════════════════════════════════

def build_analyze_tab(S: dict, page: ft.Page,
                      on_select_map=None) -> ft.Control:
    """
    Возвращает Column с вкладкой Analyze.
    У результата есть метод .rebuild() — пересобирает весь UI
    (хедер, кнопки, таблицу) на текущем языке.
    """
    T = S["theme"]

    # ─── контейнер для таблицы (постоянный объект) ───
    table_container = ft.Column(
        spacing=0, scroll=ft.ScrollMode.AUTO, expand=True,
    )

    # ─── file picker'ы (создаём один раз) ───
    file_picker = ft.FilePicker()
    page.services.append(file_picker)

    dir_picker = ft.FilePicker()
    page.services.append(dir_picker)

    # ─── async-хендлеры ───

    async def open_picker(_):
        files = await file_picker.pick_files(
            allow_multiple=True,
            allowed_extensions=["png", "jpg", "jpeg", "tif", "tiff", "bmp"],
            dialog_title=t("tab_analyze.dlg_pick"),
        )
        if not files:
            return
        paths = [f.path for f in files]
        await load_files(S, page, paths, table_container, on_select_map)

    async def on_analyze_all(_):
        await analyze_all(S, page, table_container, on_select_map)

    async def on_save_fixed(_):
        await save_fixed_maps(S, page, dir_picker)

    async def on_clear(_):
        S["maps"].clear()
        S["selected_idx"] = None
        rebuild_table(S, page, table_container, on_select_map)
        if on_select_map:
            on_select_map(S, None)
        page.update()

    # ─── построение хедера (пересобирается при rebuild) ───

    def build_header() -> ft.Control:
        btn_add = make_btn_tiny(
            t("tab_analyze.btn_add"), on_click=open_picker,
            color=T["accent"], icon="folder-open",
            fg=T["fg"], fg3=T["fg3"], input_bg=T["input"],
        )
        btn_analyze = make_btn_tiny(
            t("tab_analyze.btn_analyze"), on_click=on_analyze_all,
            color=T["success"], icon="search-check",
            fg=T["fg"], fg3=T["fg3"], input_bg=T["input"],
        )
        btn_save = make_btn_tiny(
            t("tab_analyze.btn_save"), on_click=on_save_fixed,
            color=T["save"], icon="save",
            fg=T["fg"], fg3=T["fg3"], input_bg=T["input"],
        )
        btn_clear = make_btn_tiny(
            t("tab_analyze.btn_clear"), on_click=on_clear,
            color=T["reset"], icon="trash-2",
            fg=T["fg"], fg3=T["fg3"], input_bg=T["input"],
        )

        return ft.Row([
            img_icon("search-check", T["accent"], 20),
            ft.Text(t("tab_analyze.title"), color=T["fg"], size=16,
                    font_family=FONT, weight=ft.FontWeight.W_600),
            ft.Container(expand=True),
            btn_add,
            btn_analyze,
            btn_save,
            btn_clear,
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    # ─── сам Column вкладки ───

    result = ft.Column([], expand=True, spacing=8)

    def rebuild():
        rebuild_table(S, page, table_container, on_select_map)
        result.controls.clear()
        result.controls.append(build_header())
        result.controls.append(divider(T["input"]))
        result.controls.append(ft.Container(
            content=table_container,
            expand=True,
            bgcolor=T["panel"],
            border=ft.Border.all(1, T["input"]),
            border_radius=12,
            padding=8,
        ))
        try:
            if result.page is not None:
                result.page.update()
        except Exception:
            pass

    result.rebuild = rebuild
    result.table_container = table_container

    # Ссылки для перерисовки из других мест (report_panel)
    S["analyze_table_container"] = table_container
    S["analyze_on_select_map"] = on_select_map

    rebuild()
    return result


# ═══════════════════════════════════════════════════════════
#  ПУСТОЕ СОСТОЯНИЕ
# ═══════════════════════════════════════════════════════════

def _make_empty_state(T) -> ft.Control:
    return ft.Container(
        content=ft.Column([
            img_icon("folder-open", T["fg3"], 48),
            ft.Text(t("tab_analyze.empty.title"),
                    color=T["fg2"], size=15, font_family=FONT),
            ft.Text(t("tab_analyze.empty.hint"),
                    color=T["fg3"], size=12, font_family=FONT),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
        alignment=ft.Alignment.CENTER,
        padding=ft.Padding.symmetric(vertical=60),
    )


# ═══════════════════════════════════════════════════════════
#  ЗАГРУЗКА ФАЙЛОВ (с прогрессом)
# ═══════════════════════════════════════════════════════════

async def load_files(S, page, paths, table_container, on_select_map):
    """Загружает файлы, детектит типы, добавляет в S['maps']."""
    total = len(paths)
    await show_progress(S, page,
                        t("tab_analyze.log.loading", n=total))

    loaded = 0
    for i, p in enumerate(paths):
        update_progress(
            S, page, i, total,
            f"{i + 1} / {total}: {os.path.basename(p)}"
        )

        if not os.path.isfile(p):
            log(S, t("tab_analyze.log.not_a_file", path=p), "#e53935")
            continue

        ext = os.path.splitext(p)[1].lower()
        if ext not in (".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"):
            log(S, t("tab_analyze.log.not_an_image",
                     name=os.path.basename(p)), "#e53935")
            continue

        try:
            arr = load_rgb_float(p)
        except Exception as ex:
            log(S, t("tab_analyze.log.open_fail",
                     name=os.path.basename(p), err=str(ex)), "#e53935")
            continue

        fname = os.path.basename(p)
        mtype, conf, by = detect(fname, arr)

        # Профиль текстуры для albedo: авто-детект по имени файла.
        # Юзер потом может поменять в правой панели.
        albedo_profile = None
        if mtype == MapType.ALBEDO:
            from core.albedo_profiles import detect_profile
            albedo_profile = detect_profile(fname)

        entry = MapEntry(
            path=p,
            filename=fname,
            map_type=mtype,
            confidence=conf,
            detected_by=by,
            original=arr,
            working=arr.copy(),
            size_bytes=get_file_size(p),
            albedo_profile=albedo_profile,
        )

        S["maps"].append(entry)
        log(S, f"✓ {fname} → {map_label(mtype)} "
               f"({int(conf * 100)}%, {t(f'detected.{by}')})",
            "#4caf50" if conf > 0.7 else "#ff9800")
        loaded += 1

    update_progress(S, page, total, total)
    await hide_progress(S, page)
    log(S, t("tab_analyze.log.loaded", done=loaded, total=total),
        S["theme"]["fg2"])

    rebuild_table(S, page, table_container, on_select_map)
    page.update()


# ═══════════════════════════════════════════════════════════
#  АНАЛИЗ ВСЕХ (с прогрессом)
# ═══════════════════════════════════════════════════════════

async def analyze_all(S, page, table_container, on_select_map):
    """Пробегает по всем картам, запускает анализатор."""
    T = S["theme"]
    if not S["maps"]:
        log(S, t("tab_analyze.log.no_maps"), "#ff9800")
        return

    total = len(S["maps"])
    await show_progress(S, page, t("tab_analyze.log.analyzing"))

    done = 0
    for i, entry in enumerate(S["maps"]):
        update_progress(
            S, page, i, total,
            f"{i + 1} / {total}: {entry.filename}"
        )

        analyzer = get_analyzer(entry.map_type.value)
        if analyzer is None:
            log(S, t("tab_analyze.log.no_analyzer",
                     name=entry.filename, mtype=entry.map_type.value),
                T["fg3"])
            done += 1
            continue

        # Если это albedo — прокидываем сохранённый профиль в анализатор,
        # иначе фикс потом не будет знать под что чинить.
        try:
            if (entry.map_type == MapType.ALBEDO
                    and entry.albedo_profile):
                if hasattr(analyzer, "_profile_key"):
                    analyzer._profile_key = entry.albedo_profile
        except Exception:
            pass

        try:
            report = analyzer.analyze(entry.working)
        except Exception as ex:
            log(S, t("tab_analyze.log.analyze_fail",
                     name=entry.filename, err=str(ex)), "#e53935")
            done += 1
            continue

        entry.report = report

        sev = report.severity.value
        sev_color = SEV_COLORS.get(sev, T["fg2"])
        log(S, f"{_sev_mark(sev)} {entry.filename}: {t('sev.' + sev).upper()} "
               f"({len(report.issues)} {t('tab_analyze.col.issues').lower()})",
            sev_color)
        done += 1

    update_progress(S, page, total, total)
    await hide_progress(S, page)
    log(S, t("tab_analyze.log.analyzed", done=done, total=total), T["fg2"])

    rebuild_table(S, page, table_container, on_select_map)
    page.update()


def _sev_mark(sev: str) -> str:
    return {"ok": "●", "warn": "▲", "fail": "✖"}.get(sev, "○")


# ═══════════════════════════════════════════════════════════
#  СОХРАНЕНИЕ (с прогрессом)
# ═══════════════════════════════════════════════════════════

async def save_fixed_maps(S, page, dir_picker):
    """Диалог выбора параметров сохранения, потом папки, потом сохранение."""
    T = S["theme"]

    entries_with_fixes = [e for e in S["maps"] if e.had_fixes]
    total_maps = len(S["maps"])

    if total_maps == 0:
        log(S, t("tab_analyze.log.no_maps_to_save"), "#ff9800")
        return

    has_precision_maps = any(
        e.map_type in (MapType.NORMAL, MapType.HEIGHT)
        for e in S["maps"]
    )

    bit_state = {"value": 16 if has_precision_maps else 8}
    only_fixed = {"value": len(entries_with_fixes) > 0}
    has_any_fixes = len(entries_with_fixes) > 0

    def on_bit_change(e):
        bit_state["value"] = int(e.control.value)

    def on_scope_change(e):
        only_fixed["value"] = e.control.value

    label_style = ft.TextStyle(color=T["fg"], size=12, font_family=FONT)

    radio_group = ft.RadioGroup(
        value=str(bit_state["value"]),
        content=ft.Column([
            ft.Radio(value="8",
                     label=t("tab_analyze.save.bit8"),
                     label_style=label_style,
                     fill_color=T["accent"]),
            ft.Radio(value="16",
                     label=t("tab_analyze.save.bit16"),
                     label_style=label_style,
                     fill_color=T["accent"]),
        ], spacing=4),
        on_change=on_bit_change,
    )

    chk_only_fixed = ft.Checkbox(
        value=has_any_fixes,
        label=t("tab_analyze.save.only_fixed",
                n=len(entries_with_fixes)),
        label_style=label_style,
        check_color=T["accent"],
        fill_color=T["input"],
        on_change=on_scope_change,
        disabled=not has_any_fixes,
    )

    body = ft.Column([
        ft.Text(t("tab_analyze.save.what"), color=T["fg2"], size=11,
                font_family=FONT, weight=ft.FontWeight.BOLD),
        chk_only_fixed,

        ft.Container(height=8),
        ft.Text(t("tab_analyze.save.bitness"), color=T["fg2"], size=11,
                font_family=FONT, weight=ft.FontWeight.BOLD),
        radio_group,

        ft.Container(height=4),
        ft.Text(
            t("tab_analyze.save.summary",
              total=total_maps, fixed=len(entries_with_fixes)),
            color=T["fg3"], size=10, font_family=FONT_MONO,
        ),
    ], spacing=6, tight=True)

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text(t("tab_analyze.save.title"),
                      color=T["fg"], size=14,
                      font_family=FONT, weight=ft.FontWeight.W_600),
        content=ft.Container(content=body, width=420, padding=6),
        actions=[],
        actions_alignment=ft.MainAxisAlignment.END,
        bgcolor=T["panel"],
    )

    def close_dialog():
        dlg.open = False
        page.update()

    async def on_cancel(e):
        close_dialog()

    async def on_confirm(e):
        close_dialog()
        await _do_save(S, page, dir_picker,
                       bit_depth=bit_state["value"],
                       only_fixed=only_fixed["value"])

    btn_cancel = make_btn_compact(
        t("tab_analyze.save.cancel"), on_click=on_cancel,
        color=T["reset"], icon="x",
        fg3=T["fg3"], input_bg=T["input"],
    )
    btn_save = make_btn_compact(
        t("tab_analyze.save.confirm"), on_click=on_confirm,
        color=T["save"], icon="save",
        fg3=T["fg3"], input_bg=T["input"],
    )
    dlg.actions = [btn_cancel, btn_save]
    dlg.on_dismiss = lambda e: close_dialog()

    if dlg not in page.overlay:
        page.overlay.append(dlg)
    dlg.open = True
    page.update()


async def _do_save(S, page, dir_picker, bit_depth: int, only_fixed: bool):
    """Собственно сохранение с прогрессом."""
    folder = await dir_picker.get_directory_path(
        dialog_title=t("tab_analyze.save.pick_folder"),
    )
    if not folder:
        return

    if only_fixed:
        to_save = [e for e in S["maps"] if e.had_fixes]
    else:
        to_save = list(S["maps"])

    if not to_save:
        log(S, t("tab_analyze.log.nothing_to_save"), "#ff9800")
        return

    total = len(to_save)
    await show_progress(S, page, t("tab_analyze.btn_save") + "...")

    saved = 0
    for i, entry in enumerate(to_save):
        update_progress(
            S, page, i, total,
            f"{i + 1} / {total}: {entry.filename}"
        )

        base, _ = os.path.splitext(entry.filename)
        suffix = "_fixed" if entry.had_fixes else ""
        out_name = f"{base}{suffix}.png"
        out_path = os.path.join(folder, out_name)
        try:
            save_array_png_any(entry.working, out_path,
                               bit_depth=bit_depth)
            log(S, "💾 " + t("tab_analyze.log.saved_one",
                              name=out_name, bit=bit_depth),
                "#4caf50")
            saved += 1
        except Exception as ex:
            log(S, t("tab_analyze.log.save_fail",
                     name=out_name, err=str(ex)), "#e53935")

    update_progress(S, page, total, total)
    await hide_progress(S, page)
    log(S, t("tab_analyze.log.saved_total",
             saved=saved, total=total, folder=folder),
        S["theme"]["fg2"])
    page.update()


# ═══════════════════════════════════════════════════════════
#  ПЕРЕСТРОЙКА ТАБЛИЦЫ
# ═══════════════════════════════════════════════════════════

def rebuild_table(S, page, table_container, on_select_map):
    """Строит список строк-карт."""
    if table_container is None:
        return
    table_container.controls.clear()

    T = S["theme"]

    if not S["maps"]:
        table_container.controls.append(_make_empty_state(T))
        return

    table_container.controls.append(_make_table_header(T))

    for idx, entry in enumerate(S["maps"]):
        table_container.controls.append(
            _make_table_row(S, page, table_container, idx, entry,
                            on_select_map)
        )


def _make_table_header(T) -> ft.Control:
    def _h(txt, width=None, expand=False):
        return ft.Text(txt.upper(), color=T["fg3"], size=10,
                       font_family=FONT, weight=ft.FontWeight.BOLD,
                       width=width, expand=expand)

    return ft.Container(
        content=ft.Row([
            ft.Container(width=22),
            _h(t("tab_analyze.col.type"), width=160),
            _h(t("tab_analyze.col.file"), expand=True),
            _h(t("tab_analyze.col.issues"), width=80),
            _h(t("tab_analyze.col.size"), width=80),
            ft.Container(width=32),   # ← место под корзину
        ], spacing=10),
        bgcolor=T["card"],
        padding=ft.Padding.symmetric(vertical=8, horizontal=10),
        border_radius=ft.BorderRadius.only(top_left=8, top_right=8),
    )


def _make_table_row(S, page, table_container, idx, entry: MapEntry,
                    on_select_map) -> ft.Control:
    T = S["theme"]
    report = entry.report
    sev = report.severity.value if report else "unknown"
    sev_color = SEV_COLORS.get(sev, T["fg3"])

    dot = ft.Container(width=10, height=10, bgcolor=sev_color,
                       border_radius=5)

    type_dd = ft.Dropdown(
        value=entry.map_type.value,
        options=[ft.dropdown.Option(key=mt.value, text=map_label(mt))
                 for mt in MapType],
        width=160,
        text_style=ft.TextStyle(font_family=FONT, color=T["fg"], size=12),
        border=ft.OutlineInputBorder(),
        bgcolor=T["input"],
        content_padding=ft.Padding.symmetric(vertical=4, horizontal=8),
    )

    def on_type_change(e):
        new_val = e.control.value
        try:
            new_type = MapType(new_val)
        except ValueError:
            return
        if new_type == entry.map_type:
            return
        entry.map_type = new_type
        entry.detected_by = "manual"
        entry.confidence = 1.0
        entry.report = None
        entry.fix_history.clear()
        log(S, t("tab_analyze.log.type_changed",
                 name=entry.filename, type=map_label(new_type)), T["fg2"])
        page.update()

    type_dd.on_select = on_type_change

    fname_col = ft.Column([
        ft.Text(entry.filename, color=T["fg"], size=13,
                font_family=FONT, overflow=ft.TextOverflow.ELLIPSIS),
        ft.Text(f"{int(entry.confidence * 100)}% "
                f"{t('detected.' + entry.detected_by)}",
                color=T["fg3"], size=10, font_family=FONT),
    ], spacing=0, expand=True, alignment=ft.MainAxisAlignment.CENTER)

    if report:
        n_issues = len(report.issues)
        if n_issues == 0:
            issues_txt = ft.Text(t("tab_analyze.col.ok"),
                                 color=T["success"], size=12,
                                 font_family=FONT,
                                 weight=ft.FontWeight.W_600)
        else:
            issues_txt = ft.Text(str(n_issues), color=sev_color, size=12,
                                 font_family=FONT_MONO,
                                 weight=ft.FontWeight.W_600)
    else:
        issues_txt = ft.Text(t("tab_analyze.col.dash"),
                             color=T["fg3"], size=12, font_family=FONT)

    size_txt = ft.Text(fmt_size(entry.size_bytes), color=T["fg2"],
                       size=11, font_family=FONT_MONO)

    is_selected = (S.get("selected_idx") == idx)
    bg = T["card"] if is_selected else "transparent"

    def on_row_click(e):
        S["selected_idx"] = idx
        rebuild_table(S, page, table_container, on_select_map)
        if on_select_map:
            on_select_map(S, idx)
        page.update()

    def on_delete(e):
        # Остановить всплытие (чтобы клик по корзине
        # не выбирал строку)
        try:
            e.stop_propagation()
        except Exception:
            pass

        # Удаляем карту
        if 0 <= idx < len(S["maps"]):
            S["maps"].pop(idx)

        # Скорректировать selected_idx
        if S.get("selected_idx") is not None:
            if S["selected_idx"] == idx:
                S["selected_idx"] = None
            elif S["selected_idx"] > idx:
                S["selected_idx"] -= 1

        log(S, t("tab_analyze.log.deleted", name=entry.filename),
            T["fg2"])

        # Перерисовать таблицу
        rebuild_table(S, page, table_container, on_select_map)

        # Обновить правую панель
        if on_select_map:
            on_select_map(S, S.get("selected_idx"))

        page.update()

    btn_delete = ft.Container(
        content=img_icon("trash-2", T["fg3"], 14),
        padding=6,
        border_radius=6,
        ink=True,
        on_click=on_delete,
        tooltip=t("tab_analyze.delete_tooltip"),
    )

    return ft.Container(
        content=ft.Row([
            ft.Container(content=dot, width=22,
                         alignment=ft.Alignment.CENTER),
            type_dd,
            fname_col,
            ft.Container(content=issues_txt, width=80,
                         alignment=ft.Alignment.CENTER_LEFT),
            ft.Container(content=size_txt, width=80,
                         alignment=ft.Alignment.CENTER_LEFT),
            btn_delete,
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=bg,
        padding=ft.Padding.symmetric(vertical=6, horizontal=10),
        border_radius=6,
        on_click=on_row_click,
        ink=True,
    )