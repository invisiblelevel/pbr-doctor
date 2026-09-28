"""
ui/info_dialog.py — Info-диалог PBR Doctor.

4 таба: Help / About / Support + кнопка Manual (закомменчена пока).

Все строки — через core.i18n.t().
"""

import os
import webbrowser
import flet as ft

from core.wallets import (WALLETS, get_support_title, get_support_text)
from core.i18n import t
from ui.icons import img_icon
from ui.theme import divider
from ui.helpers import log

FONT = "Segoe UI"
FONT_MONO = "Consolas"
ON_ACCENT = "#ffffff"


# ═══════════════════════════════════════════════════════════
#  INFO-ДИАЛОГ
# ═══════════════════════════════════════════════════════════

def create_info_dialog(page: ft.Page, S: dict,
                       base_dir: str = ".") -> ft.AlertDialog:
    """
    Возвращает готовый AlertDialog с табами: Help / About / Support.
    Кнопка Manual закомменчена — включим, когда будет manual.html.
    """
    th = S["theme"]

    # ═══════════════════════════════════════════════════════
    #  HELP
    # ═══════════════════════════════════════════════════════

    help_content = ft.Container(
        content=ft.Column(
            [ft.Text(t("info.help_text"), color=th["fg"], size=12,
                     font_family=FONT_MONO, selectable=True, expand=True)],
            scroll=ft.ScrollMode.AUTO, expand=True,
            horizontal_alignment=ft.CrossAxisAlignment.STRETCH,
        ),
        padding=ft.Padding.only(left=16, top=16, bottom=16, right=28),
        visible=True, expand=True,
    )

    # ═══════════════════════════════════════════════════════
    #  ABOUT
    # ═══════════════════════════════════════════════════════

    about_rows = [
        (t("info.about.version"), "1.0.0"),
        (t("info.about.build"),   "2026-09-27"),
        (t("info.about.author"),  "INV.LVL"),
        (t("info.about.license"), "Free / Open Source"),
    ]
    about_col = [
        ft.Text(t("app.title"), size=24, weight=ft.FontWeight.BOLD,
                color=th["accent"], font_family=FONT),
        ft.Container(height=16),
    ]
    for label, val in about_rows:
        about_col.append(ft.Row([
            ft.Text(f"{label}:", color=th["fg3"], size=12,
                    font_family=FONT, width=100),
            ft.Text(val, color=th["fg"], size=12,
                    font_family=FONT_MONO, weight=ft.FontWeight.W_600),
        ]))
    about_col.extend([
        ft.Container(height=20),
        ft.Text(t("info.about.desc"), color=th["fg2"], size=11,
                font_family=FONT),
    ])
    about_content = ft.Container(
        content=ft.Column(about_col, spacing=6),
        padding=20, visible=False,
    )

    # ═══════════════════════════════════════════════════════
    #  SUPPORT
    # ═══════════════════════════════════════════════════════

    copy_feedback = ft.Text("", color=th["success"], size=11,
                            font_family=FONT)

    clipboard = ft.Clipboard()
    if clipboard not in page.services:
        page.services.append(clipboard)

    def copy_address(addr):
        async def _do(e):
            try:
                await clipboard.set(addr)
                copy_feedback.value = t("info.support.copied")
            except Exception as ex:
                copy_feedback.value = f"✗ {ex}"
            page.update()
        return _do

    wallet_cards = []
    for w in WALLETS:
        card = ft.Container(
            content=ft.Row([
                ft.Text(w["label"], color=th["accent"], size=12,
                        font_family=FONT, width=130,
                        weight=ft.FontWeight.W_600),
                ft.Text(w["address"], color=th["fg"], size=11,
                        font_family=FONT_MONO, selectable=True,
                        expand=True),
                ft.Container(
                    content=img_icon("copy", th["fg"], 14),
                    bgcolor=th["input"], border_radius=6,
                    padding=ft.Padding.symmetric(vertical=6, horizontal=10),
                    ink=True, on_click=copy_address(w["address"]),
                ),
            ], spacing=8,
               vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=th["card"], border_radius=8, padding=10,
        )
        wallet_cards.append(card)

    support_content = ft.Container(
        content=ft.Column([
            img_icon("heart", th["save"], 42),
            ft.Text(get_support_title(), size=18,
                    weight=ft.FontWeight.BOLD, color=th["fg"],
                    font_family=FONT, text_align=ft.TextAlign.CENTER),
            ft.Container(height=8),
            ft.Text(get_support_text(), color=th["fg2"], size=11,
                    font_family=FONT, text_align=ft.TextAlign.CENTER),
            ft.Container(height=16),
            *wallet_cards,
            ft.Container(height=8),
            copy_feedback,
        ], spacing=6, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
        padding=20, visible=False,
    )

    # ═══════════════════════════════════════════════════════
    #  TAB SWITCHER
    # ═══════════════════════════════════════════════════════

    tab_btns = {}

    def set_info_tab(name):
        help_content.visible = (name == "help")
        about_content.visible = (name == "about")
        support_content.visible = (name == "support")
        for k, b in tab_btns.items():
            b.content.color = ON_ACCENT if k == name else th["fg2"]
            b.bgcolor = th["accent"] if k == name else th["card"]
        page.update()

    def make_tab(key, label):
        b = ft.Container(
            content=ft.Text(label, color=th["fg2"], size=12,
                            font_family=FONT, weight=ft.FontWeight.W_600),
            bgcolor=th["card"], border_radius=8,
            padding=ft.Padding.symmetric(vertical=8, horizontal=14),
            ink=True, on_click=lambda e, k=key: set_info_tab(k),
        )
        tab_btns[key] = b
        return b

    # ═══════════════════════════════════════════════════════
    #  MANUAL — закомменчено до момента, когда будет manual.html
    # ═══════════════════════════════════════════════════════

    # def open_manual(e=None):
    #     manual_path = os.path.join(base_dir, "manual.html")
    #     if os.path.exists(manual_path):
    #         webbrowser.open(f"file:///{manual_path.replace(os.sep, '/')}")
    #         log(S, t("info.manual.opened"), th["fg2"])
    #     else:
    #         log(S, t("info.manual.not_found", path=manual_path), th["warn"])
    #     page.update()

    # manual_btn = ft.Container(
    #     content=ft.Row([
    #         img_icon("book-open", ON_ACCENT, 14),
    #         ft.Text(t("info.tab.manual"), color=ON_ACCENT, size=12,
    #                 font_family=FONT, weight=ft.FontWeight.W_600),
    #     ], spacing=6, tight=True,
    #        vertical_alignment=ft.CrossAxisAlignment.CENTER),
    #     bgcolor=th["accent"], border_radius=8,
    #     padding=ft.Padding.symmetric(vertical=8, horizontal=14),
    #     ink=True, on_click=open_manual,
    # )

    # ═══════════════════════════════════════════════════════
    #  CLOSE
    # ═══════════════════════════════════════════════════════

    def close_info(e=None):
        dlg.open = False
        page.update()

    close_btn = ft.Container(
        content=img_icon("x", th["fg"], 14),
        bgcolor=th["card"], border_radius=8,
        padding=ft.Padding.symmetric(vertical=6, horizontal=12),
        ink=True, on_click=close_info,
    )

    # ═══════════════════════════════════════════════════════
    #  СБОРКА
    # ═══════════════════════════════════════════════════════

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Row([
            make_tab("help",    t("info.tab.help")),
            make_tab("about",   t("info.tab.about")),
            make_tab("support", t("info.tab.support")),
            ft.Container(expand=True),
            close_btn,
        ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        content=ft.Container(
            content=ft.Column([help_content, about_content, support_content],
                              spacing=0),
            width=600, height=420,
        ),
        bgcolor=th["panel"],
    )
    set_info_tab("help")
    return dlg