"""
ui/dialogs_fix.py — всплывающее окно с результатом фикса.

Все строки — через core.i18n.t().
"""

import flet as ft
from ui.theme import FONT, FONT_MONO, make_btn_compact
from ui.icons import img_icon
from core.i18n import t


SEV_COLORS = {
    "ok":   "#4caf50",
    "warn": "#ff9800",
    "fail": "#e53935",
}


def show_fix_result(page: ft.Page, T: dict, filename: str,
                    fix_label: str,
                    severity_before: str,
                    severity_after: str,
                    issues_before: int,
                    issues_after: int):
    """
    Показывает модалку с результатом фикса.

    severity_before / severity_after: 'ok' | 'warn' | 'fail'
    issues_before / issues_after: количество issues до и после
    """

    # ─── определяем статус результата ───
    order = {"ok": 0, "warn": 1, "fail": 2}
    b = order.get(severity_before, 3)
    a = order.get(severity_after, 3)

    issues_delta = issues_before - issues_after

    if a < b:
        if a == 0:
            icon_name = "check"
            icon_color = T["success"]
            headline = t("dlg_fix.headline.done")
        else:
            icon_name = "chevron-down"
            icon_color = T["warn"]
            headline = t("dlg_fix.headline.better",
                         b=issues_before, a=issues_after)
    elif a == b:
        if issues_delta > 0:
            icon_name = "chevron-down"
            icon_color = T["warn"]
            headline = t("dlg_fix.headline.partial",
                         b=issues_before, a=issues_after)
        elif issues_delta < 0:
            icon_name = "x"
            icon_color = T["danger"]
            headline = t("dlg_fix.headline.worse_iss",
                         b=issues_before, a=issues_after)
        else:
            icon_name = "info"
            icon_color = T["fg2"]
            headline = t("dlg_fix.headline.unchanged")
    else:
        icon_name = "x"
        icon_color = T["danger"]
        headline = t("dlg_fix.headline.worse")

    # ─── строки со «до -> после» ───
    def _row(label, before, after):
        return ft.Row([
            ft.Text(label, color=T["fg3"], size=12, font_family=FONT,
                    width=110),
            ft.Text(before,
                    color=SEV_COLORS.get(severity_before, T["fg2"]),
                    size=12, font_family=FONT_MONO,
                    weight=ft.FontWeight.W_600, width=90),
            ft.Text("→", color=T["fg3"], size=12, font_family=FONT),
            ft.Text(after,
                    color=SEV_COLORS.get(severity_after, T["fg2"]),
                    size=12, font_family=FONT_MONO,
                    weight=ft.FontWeight.W_600, width=90),
        ], spacing=8)

    sev_b_txt = f"{t('sev.' + severity_before)} ({issues_before})"
    sev_a_txt = f"{t('sev.' + severity_after)} ({issues_after})"

    body = ft.Column([
        ft.Row([
            img_icon(icon_name, icon_color, 24),
            ft.Text(headline, color=T["fg"], size=14, font_family=FONT,
                    weight=ft.FontWeight.W_600),
        ], spacing=10),

        ft.Container(height=4),

        ft.Text(filename, color=T["fg2"], size=12, font_family=FONT_MONO,
                overflow=ft.TextOverflow.ELLIPSIS),
        ft.Text(t("dlg_fix.fix_line", label=fix_label),
                color=T["fg3"], size=11, font_family=FONT),

        ft.Container(height=8),
        ft.Divider(color=T["input"], height=1),
        ft.Container(height=8),

        _row(t("dlg_fix.row_status"), sev_b_txt, sev_a_txt),
        _row(t("dlg_fix.row_issues"),
             str(issues_before), str(issues_after)),
    ], spacing=4, tight=True)

    # ─── диалог ───
    dlg = ft.AlertDialog(
        modal=True,
        title=None,
        content=ft.Container(content=body, width=420, padding=6),
        actions=[],
        actions_alignment=ft.MainAxisAlignment.END,
        bgcolor=T["panel"],
    )

    def close(e):
        dlg.open = False
        page.update()

    btn_ok = make_btn_compact(
        t("dlg_fix.ok"), on_click=close,
        color=T["accent"], icon="check",
        fg3=T["fg3"], input_bg=T["input"],
    )
    dlg.actions = [btn_ok]
    dlg.on_dismiss = close

    if dlg not in page.overlay:
        page.overlay.append(dlg)
    dlg.open = True
    page.update()