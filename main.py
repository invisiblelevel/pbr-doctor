"""
main.py — точка входа PBR Doctor.

Собирает окно, вкладки, лог-панель, Info-кнопку, переключатель языка.
Работает со списком карт (S["maps"]) и индексом выбранной (S["selected_idx"]).

Язык: авто-детект при старте, переключение через дропдаун в хедере.
При смене языка пересобираются: хедер, обе вкладки, правая панель,
Info-диалог.
"""

import os
import sys
import flet as ft

from core.state import new_state
from core.i18n import t, set_lang, get_system_lang, SUPPORTED
from ui.theme import (THEME_DARK, apply_lang_font, FONT, FONT_MONO, divider)
from ui.icons import img_icon
from ui.tab_analyze import build_analyze_tab
from ui.tab_seamless import build_seamless_tab
from ui.report_panel import build_report_panel
from ui.info_dialog import create_info_dialog
from core.i18n import t


# ═══════════════════════════════════════════════════════════
#  ГЛАВНАЯ
# ═══════════════════════════════════════════════════════════

def main(page: ft.Page):
    page.title = "PBR Doctor 1.1.1-beta"
    page.window.width = 1320
    page.window.height = 840
    page.window.min_width = 1100
    page.window.min_height = 700
    # Путь к иконке: и в dev-режиме, и в собранном exe.
    # В exe PyInstaller распаковывает данные в sys._MEIPASS.
    if getattr(sys, "frozen", False):
        # Мы в собранном PyInstaller exe
        _base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    else:
        _base = os.path.dirname(os.path.abspath(__file__))
    _icon_path = os.path.join(_base, "icon.ico")
    if os.path.isfile(_icon_path):
        page.window.icon = _icon_path
    page.padding = 0
    page.spacing = 0

    # ─── состояние ───
    S = new_state()
    S["theme"] = THEME_DARK
    S.update(THEME_DARK)
    S["page"] = page
    S["base_dir"] = os.path.dirname(os.path.abspath(__file__))

     # ─── регистрация шрифта для китайского ───
    page.fonts = {
        "NotoSansSC": "fonts/NotoSansSC-Regular.ttf",
    }

    # ─── язык (авто-детект) ───
    S["lang"] = get_system_lang()
    set_lang(S["lang"])
    apply_lang_font(S["lang"])

    # ─── тема страницы ───
    page.theme_mode = ft.ThemeMode.DARK
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary=S["theme"]["accent"],
            surface=S["theme"]["panel"],
            on_surface=S["theme"]["fg"],
        ),
    )

    # ─── общий контейнер ───
    body = ft.Row(spacing=0, expand=True)

    # ═══════════════════════════════════════════════════════
    #  ПРАВАЯ ПАНЕЛЬ
    # ═══════════════════════════════════════════════════════

    report_panel = build_report_panel(S, page)
    S["report_panel"] = report_panel

    def on_select_map(S, idx):
        report_panel.render()
        page.update()

    # ═══════════════════════════════════════════════════════
    #  ЛЕВАЯ ЧАСТЬ — ВКЛАДКИ
    # ═══════════════════════════════════════════════════════

    analyze_tab = build_analyze_tab(S, page, on_select_map=on_select_map)
    seamless_tab = build_seamless_tab(S, page)

    tabs_holder = {"ctrl": None}

    def on_tab_change(e):
        idx = e.control.selected_index
        if idx == 1:
            right.visible = False
            left.width = None
            left.expand = True
            if hasattr(seamless_tab, "rebuild"):
                seamless_tab.rebuild()
        else:
            right.visible = True
            left.width = 780
            left.expand = False
        page.update()

    def build_tabs() -> ft.Control:
        tabs = ft.Tabs(
            length=2,
            selected_index=0,
            animation_duration=200,
            expand=True,
            content=ft.Column([
                ft.TabBar(
                    tabs=[
                        ft.Tab(label=t("tab_analyze.title")),
                        ft.Tab(label=t("tab_seamless.title")),
                    ],
                ),
                ft.TabBarView(
                    controls=[analyze_tab, seamless_tab],
                    expand=True,
                ),
            ], expand=True, spacing=0),
        )
        tabs.on_change = on_tab_change
        tabs_holder["ctrl"] = tabs
        return tabs

    tabs = build_tabs()

    left = ft.Container(
        content=tabs,
        width=780,
        padding=16,
        bgcolor=S["theme"]["bg"],
    )

    right = ft.Container(
        content=report_panel,
        expand=True,
        padding=ft.Padding.only(right=16, top=16, bottom=16, left=8),
        bgcolor=S["theme"]["bg"],
    )

    body.controls.append(left)
    body.controls.append(right)

    # ═══════════════════════════════════════════════════════
    #  ПРОГРЕСС-ПЛАШКА (под хедером, над вкладками)
    # ═══════════════════════════════════════════════════════

    progress_bar = ft.ProgressBar(
        value=None,
        color=S["theme"]["accent"],
        bgcolor=S["theme"]["input"],
        bar_height=4,
    )
    progress_text = ft.Text("", color=S["theme"]["fg2"], size=12,
                             font_family=FONT)

    progress_panel = ft.Container(
        content=ft.Column([
            progress_text,
            progress_bar,
        ], spacing=6),
        padding=ft.Padding.symmetric(vertical=8, horizontal=16),
        bgcolor=S["theme"]["card"],
        border=ft.Border.only(
            bottom=ft.BorderSide(1, S["theme"]["input"])
        ),
        visible=False,
    )

    S["progress_bar"] = progress_bar
    S["progress_text"] = progress_text
    S["progress_panel"] = progress_panel

    # ═══════════════════════════════════════════════════════
    #  ЛОГ-ПАНЕЛЬ
    # ═══════════════════════════════════════════════════════

    log_column = ft.Column(spacing=2, scroll=ft.ScrollMode.AUTO,
                            expand=True, auto_scroll=True)
    S["log_column_bottom"] = log_column

    log_preview = ft.Text("", color=S["theme"]["fg2"], size=12,
                           font_family=FONT, expand=True,
                           overflow=ft.TextOverflow.ELLIPSIS)
    S["log_collapsed_preview"] = log_preview

    log_expanded = {"value": False}

    log_arrow = ft.Container(
        content=img_icon("chevron-up", S["theme"]["fg3"], 14),
        padding=4,
    )

    log_label = ft.Text(t("app.log"), color=S["theme"]["fg3"], size=11,
                        font_family=FONT, weight=ft.FontWeight.W_600)

    log_header = ft.Container(
        content=ft.Row([
            img_icon("clipboard-list", S["theme"]["fg3"], 14),
            log_label,
            ft.Container(width=10),
            log_preview,
            log_arrow,
        ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        padding=ft.Padding.symmetric(vertical=6, horizontal=14),
        bgcolor=S["theme"]["panel"],
        on_click=None,
        ink=True,
    )

    log_body = ft.Container(
        content=ft.Column([
            log_column,
        ], spacing=4, expand=True),
        padding=ft.Padding.symmetric(vertical=6, horizontal=14),
        bgcolor=S["theme"]["panel"],
        height=0,
        visible=True,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
    )

    log_panel = ft.Container(
        content=ft.Column([
            log_header,
            log_body,
        ], spacing=0, tight=True),
        bgcolor=S["theme"]["panel"],
    )

    def toggle_log(e):
        log_expanded["value"] = not log_expanded["value"]
        if log_expanded["value"]:
            log_body.height = 180
            log_preview.visible = False
            log_arrow.content = img_icon("chevron-down",
                                          S["theme"]["fg3"], 14)
        else:
            log_body.height = 0
            log_preview.visible = True
            log_arrow.content = img_icon("chevron-up",
                                          S["theme"]["fg3"], 14)
        page.update()

    log_header.on_click = toggle_log

    # ═══════════════════════════════════════════════════════
    #  INFO-ДИАЛОГ (пересоздаётся при смене языка)
    # ═══════════════════════════════════════════════════════

    info_state = {"dlg": None}

    def rebuild_info_dialog():
        old = info_state.get("dlg")
        if old is not None and old in page.overlay:
            page.overlay.remove(old)
        new_dlg = create_info_dialog(page, S, S["base_dir"])
        page.overlay.append(new_dlg)
        info_state["dlg"] = new_dlg

    rebuild_info_dialog()

    def open_info(e=None):
        dlg = info_state.get("dlg")
        if dlg is not None:
            dlg.open = True
            page.update()


    # ═══════════════════════════════════════════════════════
    #  ЯЗЫК
    # ═══════════════════════════════════════════════════════

    def on_lang_change(e):
        new_lang = e.control.value
        if new_lang not in SUPPORTED:
            return
        if new_lang == S.get("lang"):
            return

        S["lang"] = new_lang
        set_lang(new_lang)
        apply_lang_font(new_lang)

        # 1) Перестроить вкладки
        if hasattr(analyze_tab, "rebuild"):
            analyze_tab.rebuild()
        if hasattr(seamless_tab, "rebuild"):
            seamless_tab.rebuild()

        # 2) Перестроить правую панель
        try:
            report_panel.render()
        except Exception:
            pass

        # 3) Пересобрать хедер (кнопки + лейбл дропдауна)
        rebuild_header()
        print("=== LANG CHANGE ===")
        print("app.info =", t("app.info"))
        print("tab_analyze.title =", t("tab_analyze.title"))
        print("S['lang'] =", S["lang"])

        # 4) Пересобрать строку вкладок
        rebuild_tabbar()

        # 5) Пересоздать Info-диалог
        rebuild_info_dialog()

        # 6) Обновить надпись Log
        log_label.value = t("app.log")

        page.update()

    lang_dd = ft.Dropdown(
        value=S["lang"],
        options=[
            ft.dropdown.Option(key="ru", text="RU"),
            ft.dropdown.Option(key="en", text="EN"),
            ft.dropdown.Option(key="zh", text="中文"),
        ],
        width=90,
        text_style=ft.TextStyle(font_family=FONT,
                                color=S["theme"]["fg"], size=12),
        border=ft.OutlineInputBorder(),
        bgcolor=S["theme"]["input"],
        content_padding=ft.Padding.symmetric(vertical=4, horizontal=8),
    )
    lang_dd.on_select = on_lang_change

    # ═══════════════════════════════════════════════════════
    #  ХЕДЕР — пересобираемый
    # ═══════════════════════════════════════════════════════

    header_holder = {"ctrl": None}

    def build_header_content() -> ft.Row:
        btn_info = ft.Container(
            content=ft.Row([
                img_icon("info", S["theme"]["fg"], 16),
                ft.Text(t("app.info"), color=S["theme"]["fg"], size=12,
                        font_family=FONT, weight=ft.FontWeight.W_600),
            ], spacing=6, tight=True,
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=S["theme"]["card"],
            border_radius=8,
            padding=ft.Padding.symmetric(vertical=8, horizontal=12),
            ink=True,
            on_click=open_info,
        )

        return ft.Row([
            img_icon("search-check", S["theme"]["accent"], 22),
            ft.Text(t("app.title"), color=S["theme"]["fg"], size=16,
                    font_family=FONT, weight=ft.FontWeight.W_600),
            ft.Text("1.1.1-beta", color=S["theme"]["fg3"], size=11,
                    font_family=FONT),
            ft.Container(expand=True),
            ft.Text(t("app.tagline"),
                    color=S["theme"]["fg3"], size=11, font_family=FONT),
            ft.Container(width=12),
            lang_dd,
            btn_info,
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def rebuild_header():
        h = header_holder.get("ctrl")
        if h is None:
            return
        h.content = build_header_content()

    header = ft.Container(
        content=build_header_content(),
        bgcolor=S["theme"]["panel"],
        padding=ft.Padding.symmetric(vertical=10, horizontal=16),
        border=ft.Border.only(
            bottom=ft.BorderSide(1, S["theme"]["input"])
        ),
    )
    header_holder["ctrl"] = header

    # ═══════════════════════════════════════════════════════
    #  TABBAR — пересобираемый
    # ═══════════════════════════════════════════════════════

    def rebuild_tabbar():
        """Пересобирает только labels вкладок (Analyze / Seamless)."""
        tabs_ctrl = tabs_holder.get("ctrl")
        if tabs_ctrl is None:
            return
        try:
            tabbar = tabs_ctrl.content.controls[0]   # ft.TabBar
            tabbar.tabs[0].label = t("tab_analyze.title")
            tabbar.tabs[1].label = t("tab_seamless.title")
        except Exception:
            pass

    # ═══════════════════════════════════════════════════════
    #  СБОРКА
    # ═══════════════════════════════════════════════════════

    page.add(ft.Column([
        header,
        progress_panel,
        ft.Container(content=body, expand=True),
        log_panel,
    ], spacing=0, expand=True))

    from ui.helpers import log as log_fn
    log_fn(S, t("log.ready"), S["theme"]["fg2"])
    log_fn(S, t("log.hint_add"), S["theme"]["fg3"])

    page.update()


if __name__ == "__main__":
    ft.run(main, assets_dir="assets")