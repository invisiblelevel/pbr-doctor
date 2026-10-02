"""
ui/report_panel.py — правая панель с деталями выбранной карты.

Работает с S["selected_idx"] — индексом в списке S["maps"].

Структура панели:
  1. Хедер: имя файла + тип
  2. Превью рабочей версии
  3. Вердикт (Severity + список проблем простым языком)
  4. Свёрнутый блок "Сырые метрики" (клик -> раскрывается)
  5. Список issues с кнопками Fix

Прогресс:
  При применении фикса показывается indeterminate-прогресс
  в нижней панели лога. Обновление прогресса идёт через
  поллинг из главного Flet-потока (безопасно для DirectML).

Все строки — через core.i18n.t().
"""

import flet as ft
import numpy as np
import asyncio

from core.state import MapType, MapEntry, map_label
from core.io import pil_to_b64
from core.analyzers import get_analyzer
from core.i18n import t

from ui.theme import (
    make_btn_compact, section_title, divider,
    FONT, FONT_MONO,
)
from ui.icons import img_icon
from ui.helpers import (log, show_progress, hide_progress)


SEV_COLORS = {
    "ok":   "#4caf50",
    "warn": "#ff9800",
    "fail": "#e53935",
}


# ═══════════════════════════════════════════════════════════
#  ГЛАВНАЯ ФУНКЦИЯ
# ═══════════════════════════════════════════════════════════

def build_report_panel(S: dict, page: ft.Page) -> ft.Control:
    """Правая панель с деталями выбранной карты."""
    T = S["theme"]

    inner = ft.Column(spacing=10, scroll=ft.ScrollMode.AUTO, expand=True)

    def render(S):
        inner.controls.clear()

        idx = S.get("selected_idx")
        if idx is None or idx < 0 or idx >= len(S["maps"]):
            inner.controls.append(_empty_state(T))
            return

        entry = S["maps"][idx]
        inner.controls.append(_header(T, entry))
        inner.controls.append(divider(T["input"]))
        inner.controls.append(_preview(T, entry))

        if entry.report is None:
            inner.controls.append(ft.Container(
                content=ft.Text(t("panel.need_analyze"),
                                color=T["fg3"], size=13, font_family=FONT),
                padding=10,
            ))
        else:
            inner.controls.append(_verdict(S, page, T, entry))

            if entry.map_type == MapType.ALBEDO:
                inner.controls.append(_profile_selector(S, page, T, entry))

            inner.controls.append(_raw_metrics_expander(T, entry.report))
            inner.controls.append(divider(T["input"]))
            inner.controls.append(_issues(S, page, T, entry))

            if entry.had_fixes or entry.fix_history:
                inner.controls.append(
                    _reset_fixes_button(S, page, T, entry)
                )

    panel = ft.Container(
        content=inner,
        width=420,
        bgcolor=T["panel"],
        border=ft.Border.all(1, T["input"]),
        border_radius=12,
        padding=12,
    )

    panel.render = lambda: render(S)
    render(S)
    return panel


def _empty_state(T) -> ft.Control:
    return ft.Container(
        content=ft.Column([
            img_icon("info", T["fg3"], 40),
            ft.Text(t("panel.empty"), color=T["fg3"],
                    size=13, font_family=FONT),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
        alignment=ft.Alignment.CENTER,
        padding=ft.Padding.symmetric(vertical=80),
    )


def _header(T, entry: MapEntry) -> ft.Control:
    return ft.Row([
        img_icon("image", T["accent"], 18),
        ft.Column([
            ft.Text(entry.filename, color=T["fg"], size=14,
                    font_family=FONT, weight=ft.FontWeight.W_600,
                    overflow=ft.TextOverflow.ELLIPSIS),
            ft.Text(map_label(entry.map_type), color=T["fg3"],
                    size=12, font_family=FONT),
        ], spacing=0, expand=True),
    ], spacing=10)


def _preview(T, entry: MapEntry) -> ft.Control:
    """Превью рабочей версии карты. Клик — открывает большую модалку."""
    cache_key = id(entry.working)
    cached = getattr(entry, "_preview_cache", None)

    if cached is not None and cached[0] == cache_key:
        b64 = cached[1]
    else:
        try:
            b64 = pil_to_b64(entry.working, max_size=380)
        except Exception:
            b64 = None
        try:
            entry._preview_cache = (cache_key, b64)
        except Exception:
            pass

    if b64 is None:
        return ft.Container()

    def on_preview_click(e):
        _open_full_preview(e.page, T, entry)

    return ft.Container(
        content=ft.Stack([
            ft.Image(src=f"data:image/png;base64,{b64}",
                     fit=ft.BoxFit.CONTAIN),
            # Подсказка «клик для увеличения» в углу
            ft.Container(
                content=ft.Row([
                    img_icon("eye", T["fg"], 12),
                    ft.Text("Увеличить", color=T["fg"], size=10,
                            font_family=FONT),
                ], spacing=4, tight=True,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor="#00000099",
                border_radius=6,
                padding=ft.Padding.symmetric(vertical=3, horizontal=8),
                right=6, bottom=6,
            ),
        ]),
        height=200,
        bgcolor=T["card"],
        border_radius=8,
        alignment=ft.Alignment.CENTER,
        on_click=on_preview_click,
        ink=True,
        tooltip="Клик — открыть на весь экран",
    )


def _open_full_preview(page: ft.Page, T, entry: MapEntry):
    """Модалка с большой картинкой + переключение before/after."""
    # Готовим большую версию превью (до 1400px по длинной стороне)
    try:
        b64_big = pil_to_b64(entry.working, max_size=1400)
    except Exception:
        return

    if b64_big is None:
        return

    # ─── Сборка содержимого модалки ───
    img_ctrl = ft.Image(
        src=f"data:image/png;base64,{b64_big}",
        fit=ft.BoxFit.CONTAIN,
    )

    img_container = ft.Container(
        content=img_ctrl,
        bgcolor=T["card"],
        border_radius=8,
        padding=8,
        alignment=ft.Alignment.CENTER,
        expand=True,
    )

    # ─── Кнопки: показать before / after ───
    btn_state = {"mode": "after"}   # "after" | "before"

    btn_toggle = ft.Container(
        content=ft.Row([
            img_icon("rotate-ccw", T["fg"], 14),
            ft.Text("Показать оригинал", color=T["fg"], size=12,
                    font_family=FONT, weight=ft.FontWeight.W_600),
        ], spacing=6, tight=True,
           vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=T["card"],
        border_radius=8,
        padding=ft.Padding.symmetric(vertical=8, horizontal=12),
        ink=True,
    )

    def on_toggle(e):
        if btn_state["mode"] == "after":
            btn_state["mode"] = "before"
            src = entry.original
            label = "Показать результат"
        else:
            btn_state["mode"] = "after"
            src = entry.working
            label = "Показать оригинал"

        try:
            b64 = pil_to_b64(src, max_size=1400)
        except Exception:
            return

        img_ctrl.src = f"data:image/png;base64,{b64}"
        btn_toggle.content.controls[1].value = label
        page.update()

    btn_toggle.on_click = on_toggle

    # Показываем toggle только если есть фиксы
    if entry.had_fixes or entry.fix_history:
        btn_toggle.visible = True
    else:
        btn_toggle.visible = False

    # ─── Кнопка закрытия ───
    btn_close = ft.Container(
        content=ft.Row([
            img_icon("x", T["fg"], 14),
            ft.Text("Закрыть", color=T["fg"], size=12,
                    font_family=FONT, weight=ft.FontWeight.W_600),
        ], spacing=6, tight=True,
           vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=T["card"],
        border_radius=8,
        padding=ft.Padding.symmetric(vertical=8, horizontal=12),
        ink=True,
    )

    # ─── Заголовок ───
    title_row = ft.Row([
        ft.Text(entry.filename, color=T["fg"], size=14,
                font_family=FONT, weight=ft.FontWeight.W_600,
                overflow=ft.TextOverflow.ELLIPSIS),
        ft.Text(f"  •  {entry.working.shape[1]}×{entry.working.shape[0]}",
                color=T["fg3"], size=12, font_family=FONT_MONO),
    ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    # ─── Собираем модалку ───
    dlg = ft.AlertDialog(
        modal=True,
        title=title_row,
        content=ft.Container(
            content=img_container,
            width=1400,
            height=820,
            padding=6,
        ),
        actions=[btn_toggle, btn_close],
        actions_alignment=ft.MainAxisAlignment.END,
        bgcolor=T["panel"],
    )

    def close(e=None):
        dlg.open = False
        page.update()

    btn_close.on_click = close
    dlg.on_dismiss = close

    if dlg not in page.overlay:
        page.overlay.append(dlg)
    dlg.open = True
    page.update()


# ═══════════════════════════════════════════════════════════
#  ВЕРДИКТ
# ═══════════════════════════════════════════════════════════

def _verdict(S, page, T, entry: MapEntry) -> ft.Control:
    report = entry.report
    if report is None:
        return ft.Container()

    sev = report.severity.value
    sev_color = SEV_COLORS.get(sev, T["fg3"])
    sev_label = t(f"panel.sev.{sev}")

    explanations = _explain_metrics(report)

    if not explanations:
        return ft.Container(
            content=ft.Row([
                ft.Container(width=4, height=34, bgcolor=sev_color,
                             border_radius=2),
                ft.Column([
                    ft.Text(sev_label, color=sev_color, size=16,
                            font_family=FONT,
                            weight=ft.FontWeight.W_700),
                    ft.Text(t("panel.all_passed"),
                            color=T["fg2"], size=13, font_family=FONT),
                ], spacing=1, expand=True),
            ], spacing=8),
            bgcolor=T["card"],
            padding=10,
            border_radius=8,
            border=ft.Border.all(1, T["input"]),
        )

    bullets = []
    for text, sev_level in explanations:
        bullet_color = SEV_COLORS.get(sev_level, T["fg2"])
        bullets.append(ft.Row([
            ft.Text("•", color=bullet_color, size=16,
                    font_family=FONT, width=14),
            ft.Text(text, color=T["fg"], size=14,
                    font_family=FONT, expand=True, no_wrap=False),
        ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.START))

    return ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Container(width=4, height=34, bgcolor=sev_color,
                             border_radius=2),
                ft.Column([
                    ft.Text(sev_label, color=sev_color, size=16,
                            font_family=FONT,
                            weight=ft.FontWeight.W_700),
                    ft.Text(t("panel.issues_found", n=len(report.issues)),
                            color=T["fg2"], size=13, font_family=FONT),
                ], spacing=1, expand=True),
            ], spacing=8),

            ft.Container(height=6),
            *bullets,
        ], spacing=6),
        bgcolor=T["card"],
        padding=10,
        border_radius=8,
        border=ft.Border.all(1, T["input"]),
    )


def _explain_metrics(report) -> list:
    out = []
    m = report.metrics or {}
    mtype = report.map_type

    COLOR_THRESH = 0.02

    # ─── NORMAL ───
    if mtype == "normal":
        mean_len = m.get("mean_length")
        bad_pct  = m.get("bad_length_pct")
        angle    = m.get("angle_deg")
        b_mean   = m.get("b_mean")
        b_std    = m.get("b_std")
        r_std    = m.get("r_std")
        g_std    = m.get("g_std")

        if mean_len is not None and mean_len < 0.9:
            out.append((t("verdict.normal.mean_len", v=mean_len), "fail"))
        if bad_pct is not None and bad_pct >= 5.0:
            out.append((t("verdict.normal.bad_pct_fail", v=bad_pct), "fail"))
        elif bad_pct is not None and bad_pct >= 1.0:
            out.append((t("verdict.normal.bad_pct_warn", v=bad_pct), "warn"))
        if angle is not None and angle >= 15.0:
            out.append((t("verdict.normal.angle_fail", v=angle), "fail"))
        elif angle is not None and angle >= 5.0:
            out.append((t("verdict.normal.angle_warn", v=angle), "warn"))
        if b_mean is not None and b_mean < 0.5 and (b_std or 0) < 0.05:
            if (r_std or 0) < 0.02 and (g_std or 0) < 0.02:
                out.append((t("verdict.normal.not_normal"), "fail"))
            else:
                out.append((
                    t("verdict.normal.broken_b", bm=b_mean, bs=b_std),
                    "fail"
                ))

    # ─── ROUGHNESS ───
    elif mtype == "roughness":
        mean        = m.get("mean")
        std         = m.get("std")
        span        = m.get("span_p1_p99")
        p1          = m.get("p1")
        p99         = m.get("p99")
        channel_std = m.get("channel_std", 0.0)

        if channel_std >= COLOR_THRESH:
            out.append((t("verdict.rough.color", v=channel_std), "fail"))
        if std is not None and std < 0.03:
            out.append((t("verdict.rough.dead", v=std), "fail"))
        elif std is not None and std < 0.06:
            out.append((t("verdict.rough.low_var", v=std), "warn"))
        elif span is not None and span < 0.50:
            out.append((t("verdict.rough.narrow", p1=p1, p99=p99), "warn"))
        if std is not None and std > 0.35:
            out.append((t("verdict.rough.noisy", v=std), "warn"))

    # ─── METALLIC ───
    elif mtype == "metallic":
        muddy_pct   = m.get("muddy_pct")
        zero_pct    = m.get("zero_pct")
        one_pct     = m.get("one_pct")
        channel_std = m.get("channel_std", 0.0)

        if channel_std >= COLOR_THRESH:
            out.append((t("verdict.metal.color", v=channel_std), "fail"))
        if muddy_pct is not None and muddy_pct >= 15.0:
            out.append((t("verdict.metal.muddy_fail", v=muddy_pct), "fail"))
        elif muddy_pct is not None and muddy_pct >= 5.0:
            out.append((t("verdict.metal.muddy_warn", v=muddy_pct), "warn"))
        if zero_pct is not None and zero_pct >= 99.5:
            out.append((t("verdict.metal.all_zero", v=zero_pct), "warn"))
        if one_pct is not None and one_pct >= 99.5:
            out.append((t("verdict.metal.all_one", v=one_pct), "warn"))

    # ─── AO ───
    elif mtype == "ao":
        mean        = m.get("mean")
        std         = m.get("std")
        span        = m.get("span_p1_p99")
        p1          = m.get("p1")
        p99         = m.get("p99")
        dark_pct    = m.get("dark_pct")
        channel_std = m.get("channel_std", 0.0)

        if channel_std >= COLOR_THRESH:
            out.append((t("verdict.ao.color", v=channel_std), "fail"))
        if std is not None and std < 0.03:
            out.append((t("verdict.ao.dead", v=std), "fail"))
        elif std is not None and std < 0.05:
            out.append((t("verdict.ao.low_var", v=std), "warn"))
        if mean is not None and mean < 0.15:
            if dark_pct:
                out.append((t("verdict.ao.dark", v=mean, dp=dark_pct), "fail"))
            else:
                out.append((t("verdict.ao.dark_short", v=mean), "fail"))
        if mean is not None and mean > 0.90:
            out.append((t("verdict.ao.light", v=mean), "warn"))
        if (std is not None and std >= 0.03
                and span is not None and span < 0.40):
            out.append((t("verdict.ao.narrow", p1=p1, p99=p99), "warn"))

    # ─── ALBEDO ───
    elif mtype == "albedo":
        profile = m.get("profile", "?")
        std_l = m.get("std_L")
        p1 = m.get("p1_L")
        p99 = m.get("p99_L")
        mean_s = m.get("mean_S")
        soapy_pct = m.get("soapy_pct")
        color_spread = m.get("color_spread")

        if soapy_pct is not None and soapy_pct >= 20.0:
            out.append((
                t("verdict.albedo.soapy", pct=soapy_pct),
                "warn"
            ))
        if p1 is not None and p1 < 10:
            out.append((
                t("verdict.albedo.dark", p1=p1, thr=10),
                "warn"
            ))
        if p99 is not None and p99 > 250:
            out.append((
                t("verdict.albedo.light", p99=p99, thr=250),
                "warn"
            ))
        if std_l is not None and std_l < 30.0:
            out.append((
                t("verdict.albedo.flat_contrast", std=std_l),
                "warn"
            ))
        elif std_l is not None and std_l > 80.0:
            out.append((
                t("verdict.albedo.hard_contrast", std=std_l),
                "warn"
            ))
        if mean_s is not None and mean_s < 0.15:
            out.append((
                t("verdict.albedo.flat_color", sat=mean_s),
                "warn"
            ))
        elif mean_s is not None and mean_s > 0.75:
            out.append((
                t("verdict.albedo.oversaturated", sat=mean_s),
                "warn"
            ))
        if color_spread is not None and color_spread > 15.0:
            out.append((
                t("verdict.albedo.color_cast", delta=color_spread),
                "warn"
            ))

    # ─── HEIGHT / EDGE / UNKNOWN ───
    elif mtype in ("height", "edge", "unknown"):
        label = map_label(mtype)

        mean        = m.get("mean")
        std         = m.get("std")
        span        = m.get("span_p1_p99")
        p1          = m.get("p1")
        p99         = m.get("p99")
        channel_std = m.get("channel_std", 0.0)
        muddy_pct   = m.get("muddy_pct")

        if mtype == "unknown":
            out.append((t("verdict.fb.unknown"), "warn"))

        if channel_std >= COLOR_THRESH:
            out.append((
                t("verdict.fb.color", v=channel_std, label=label),
                "fail"
            ))
        if std is not None and std < 0.02:
            out.append((t("verdict.fb.dead", v=std), "fail"))
        elif std is not None and std < 0.04:
            out.append((t("verdict.fb.low_var", v=std), "warn"))
        elif span is not None and span < 0.40:
            out.append((t("verdict.fb.narrow", p1=p1, p99=p99), "warn"))
        if std is not None and std > 0.40:
            out.append((t("verdict.fb.noisy", v=std), "warn"))
        if mean is not None and mean < 0.05:
            out.append((t("verdict.fb.dark", v=mean), "warn"))
        if mean is not None and mean > 0.95:
            out.append((t("verdict.fb.light", v=mean), "warn"))
        if mtype == "edge" and muddy_pct is not None and muddy_pct >= 10.0:
            out.append((t("verdict.fb.edge_muddy", v=muddy_pct), "warn"))

    elif mtype == "orm":
        pass

    return out


# ═══════════════════════════════════════════════════════════
#  СЫРЫЕ МЕТРИКИ
# ═══════════════════════════════════════════════════════════

def _profile_selector(S, page, T, entry: MapEntry) -> ft.Control:
    from core.albedo_profiles import sorted_profile_keys
    from core.analyzers import get_analyzer
    from core.i18n import t

    profile_keys = sorted_profile_keys()

    current = entry.albedo_profile or "stone"
    if current not in profile_keys:
        current = "stone"

    async def on_profile_change(e):
        new_key = e.control.value
        if new_key == entry.albedo_profile:
            return

        entry.albedo_profile = new_key
        entry.fix_history.clear()
        entry.had_fixes = False

        analyzer = get_analyzer(entry.map_type.value)
        if analyzer is not None:
            if hasattr(analyzer, "_profile_key"):
                analyzer._profile_key = new_key
            try:
                entry.report = await asyncio.to_thread(
                    analyzer.analyze,
                    entry.working,
                    new_key,
                    entry.filename,
                )
            except Exception as ex:
                log(S, f"✗ Переанализ не удался: {ex}", T["danger"])
                return

        log(S, t("panel.profile_changed",
                 profile=t(f"albedo.profile.{new_key}")), T["fg2"])

        try:
            panel = S.get("report_panel")
            if panel is not None and hasattr(panel, "render"):
                panel.render()
        except Exception:
            pass

        page.update()

    options = [
        ft.dropdown.Option(key=k, text=t(f"albedo.profile.{k}"))
        for k in profile_keys
    ]

    dd = ft.Dropdown(
        value=current,
        options=options,
        width=280,
        text_style=ft.TextStyle(font_family=FONT, color=T["fg"], size=12),
        border=ft.OutlineInputBorder(),
        bgcolor=T["input"],
        content_padding=ft.Padding.symmetric(vertical=4, horizontal=8),
    )
    dd.on_select = on_profile_change

    return ft.Container(
        content=ft.Column([
            ft.Text(t("panel.profile_label"),
                    color=T["fg3"], size=11, font_family=FONT,
                    weight=ft.FontWeight.W_600),
            dd,
        ], spacing=4),
        bgcolor=T["card"],
        padding=10,
        border_radius=8,
        border=ft.Border.all(1, T["input"]),
    )


def _raw_metrics_expander(T, report) -> ft.Control:
    rows = _build_raw_metric_rows(T, report)
    body = ft.Column(rows, spacing=3, tight=True, visible=False)

    chevron = img_icon("chevron-down", T["fg3"], 14)

    def toggle(e):
        body.visible = not body.visible
        chevron.icon = ("chevron-up" if body.visible else "chevron-down")
        e.page.update()

    header = ft.Container(
        content=ft.Row([
            chevron,
            ft.Text(t("panel.raw_metrics"), color=T["fg3"], size=13,
                    font_family=FONT, weight=ft.FontWeight.W_600),
        ], spacing=6),
        on_click=toggle,
        ink=True,
        padding=ft.Padding.symmetric(vertical=4, horizontal=2),
    )

    return ft.Container(
        content=ft.Column([header, body], spacing=4),
        bgcolor=T["panel"],
        padding=ft.Padding.symmetric(vertical=4, horizontal=8),
        border_radius=6,
    )


def _build_raw_metric_rows(T, report) -> list:
    rows = []
    for key, val in report.metrics.items():
        if isinstance(val, dict):
            continue

        if isinstance(val, float):
            v_str = f"{val:.4f}"
        elif isinstance(val, list):
            v_str = "[" + ", ".join(f"{x:.2f}" for x in val) + "]"
        else:
            v_str = str(val)

        rows.append(ft.Row([
            ft.Text(key, color=T["fg3"], size=12, font_family=FONT_MONO,
                    width=160),
            ft.Text(v_str, color=T["fg"], size=12, font_family=FONT_MONO,
                    expand=True),
        ], spacing=6))

    if not rows:
        rows.append(ft.Text(t("panel.no_data"), color=T["fg3"], size=12,
                            font_family=FONT))
    return rows


# ═══════════════════════════════════════════════════════════
#  ISSUES
# ═══════════════════════════════════════════════════════════

def _reset_fixes_button(S, page, T, entry: MapEntry) -> ft.Control:
    from core.analyzers import get_analyzer

    async def on_reset(e):
        entry.working = entry.original.copy()
        entry.fix_history.clear()
        entry.had_fixes = False

        analyzer = get_analyzer(entry.map_type.value)
        if analyzer is not None:
            if (entry.map_type == MapType.ALBEDO
                    and entry.albedo_profile
                    and hasattr(analyzer, "_profile_key")):
                analyzer._profile_key = entry.albedo_profile

            try:
                entry.report = await asyncio.to_thread(
                    analyzer.analyze,
                    entry.working,
                    entry.albedo_profile,
                    entry.filename,
                )
            except Exception:
                entry.report = None
        else:
            entry.report = None

        log(S, t("panel.fixes_reset_log", name=entry.filename), T["fg2"])

        try:
            panel = S.get("report_panel")
            if panel is not None and hasattr(panel, "render"):
                panel.render()
        except Exception:
            pass

        try:
            from ui.tab_analyze import rebuild_table
            tc = S.get("analyze_table_container")
            osm = S.get("analyze_on_select_map")
            if tc is not None:
                rebuild_table(S, page, tc, osm)
        except Exception:
            pass

        page.update()

    btn = make_btn_compact(
        t("panel.fixes_reset"),
        on_click=on_reset,
        color=T["danger"],
        icon="rotate-ccw",
        fg3=T["fg3"], input_bg=T["input"],
    )

    return ft.Container(
        content=ft.Row([
            ft.Container(expand=True),
            btn,
        ], spacing=6),
        padding=ft.Padding.symmetric(vertical=6),
    )


def _issues(S, page, T, entry: MapEntry) -> ft.Control:
    report = entry.report
    if not report or not report.issues:
        return ft.Container(
            content=ft.Row([
                img_icon("check", T["success"], 18),
                ft.Text(t("panel.no_issues"), color=T["success"],
                        size=14, font_family=FONT),
            ], spacing=6),
            padding=ft.Padding.symmetric(vertical=8),
        )

    cards = []
    for issue in report.issues:
        cards.append(_make_issue_card(S, page, T, entry, issue))

    return ft.Column([
        section_title(t("panel.issues_title", n=len(report.issues)),
                      T["fg3"]),
        *cards,
    ], spacing=8)


def _make_issue_card(S, page, T, entry: MapEntry, issue) -> ft.Control:
    sev_color = SEV_COLORS.get(issue.severity.value, T["fg2"])

    head = ft.Row([
        ft.Container(width=4, height=48, bgcolor=sev_color,
                     border_radius=2),
        ft.Column([
            ft.Text(issue.title, color=T["fg"], size=15,
                    font_family=FONT, weight=ft.FontWeight.W_600),
            ft.Text(issue.detail, color=T["fg2"], size=13,
                    font_family=FONT, no_wrap=False),
        ], spacing=3, expand=True),
    ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.START)

    bottom_slot = ft.Container()

    last_fix = None
    for rec in entry.fix_history:
        if rec.get("issue_code") == issue.code:
            last_fix = rec
            break

    if last_fix is not None:
        bottom_slot.content = _make_fix_result_row(
            S, page, T, entry, last_fix
        )
    elif issue.fix_id:
        fix_id = issue.fix_id

        async def on_fix_click(e, fid=fix_id, code=issue.code,
                               slot=bottom_slot):
            await _apply_fix_inline(S, page, T, entry, fid, code, slot)
            page.update()

        btn_fix = make_btn_compact(
            issue.fix_label or t("fix.generic"),
            on_click=on_fix_click,
            color=T["accent"],
            icon="wand-sparkles",
            fg3=T["fg3"], input_bg=T["input"],
        )
        bottom_slot.content = ft.Row([
            ft.Container(expand=True),
            btn_fix,
        ])
    else:
        bottom_slot.content = ft.Container()

    return ft.Container(
        content=ft.Column([head, bottom_slot], spacing=6),
        bgcolor=T["card"],
        padding=10,
        border_radius=8,
        border=ft.Border.all(1, T["input"]),
    )


def _make_fix_result_row(S, page, T, entry: MapEntry, rec: dict) -> ft.Control:
    before = rec.get("sev_before", "fail")
    after = rec.get("sev_after", "fail")

    order = {"ok": 0, "warn": 1, "fail": 2}
    b = order.get(before, 3)
    a = order.get(after, 3)

    from ui.dialogs_fix import _compute_metric_deltas

    mb = rec.get("prev_report").metrics if rec.get("prev_report") else {}
    ma = entry.report.metrics if entry.report else {}
    mtype = entry.map_type.value
    deltas = _compute_metric_deltas(mtype, mb, ma)
    improved = sum(1 for d in deltas if d["verdict"] == "better")
    worse = sum(1 for d in deltas if d["verdict"] == "worse")

    if a == 0 and b != 0:
        icon_name = "check"
        icon_color = T["success"]
        text = t("panel.fix_result.done")
    elif a < b:
        icon_name = "chevron-down"
        icon_color = T["warn"]
        text = t("panel.fix_result.better",
                 before=t("sev." + before), after=t("sev." + after))
    elif a == b and improved > 0 and worse == 0:
        icon_name = "chevron-down"
        icon_color = T["warn"]
        text = t("panel.fix_result.metrics_better", n=improved)
    elif a == b and worse > 0 and improved == 0:
        icon_name = "x"
        icon_color = T["danger"]
        text = t("panel.fix_result.metrics_worse", n=worse)
    elif a == b:
        icon_name = "info"
        icon_color = T["fg2"]
        text = t("panel.fix_result.unchanged")
    else:
        icon_name = "x"
        icon_color = T["danger"]
        text = t("panel.fix_result.worse")

    async def on_undo(e):
        _undo_fix(S, page, T, entry, rec)
        page.update()

    btn_undo = make_btn_compact(
        t("panel.fix_result.undo"),
        on_click=on_undo,
        color=T["reset"],
        icon="rotate-ccw",
        fg3=T["fg3"], input_bg=T["input"],
    )

    return ft.Row([
        img_icon(icon_name, icon_color, 16),
        ft.Text(text, color=icon_color, size=13,
                font_family=FONT, weight=ft.FontWeight.W_600),
        ft.Container(expand=True),
        btn_undo,
    ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER)


# ═══════════════════════════════════════════════════════════
#  ФИКСЫ (с диагностическими print)
# ═══════════════════════════════════════════════════════════

async def _apply_fix_inline(S, page, T, entry: MapEntry, fix_id: str,
                            issue_code: str,
                            bottom_slot: ft.Container):
    """
    Применяет фикс, показывает результат + модалку.
    Async — чтобы не блокировать Flet-поток.

    ВНИМАНИЕ: тут стоят диагностические print для отладки —
    убрать после того как поймём где именно виснет.
    """
    from ui.dialogs_fix import show_fix_result


    analyzer = get_analyzer(entry.map_type.value)
    if analyzer is None:
        log(S, t("panel.no_analyzer", mtype=entry.map_type.value),
            T["danger"])
        return

    report_before = entry.report
    sev_before = (report_before.severity.value
                  if report_before else "fail")
    issues_before = len(report_before.issues) if report_before else 0

    fix_label = fix_id
    if report_before:
        for iss in report_before.issues:
            if iss.fix_id == fix_id and iss.fix_label:
                fix_label = iss.fix_label
                break

    prev_working = entry.working.copy()
    prev_report = entry.report

    # ─── Показать прогресс ───
    await show_progress(S, page, fix_label)

    # ─── Callback прогресса: только пишет в S, БЕЗ page.update() ───
    from core.analyzers.base import set_progress_callback

    def _progress_cb(text, done=0, total=0):
        try:
            S["progress_text_value"] = text
            S["progress_done"] = done
            S["progress_total"] = total
        except Exception:
            pass

    set_progress_callback(_progress_cb)

    # ─── Поллинг из главного потока ───
    poll_state = {"running": True}

    async def _poll_progress():
        while poll_state["running"]:
            try:
                if S.get("progress_panel") is not None:
                    S["progress_panel"].visible = True
                if S.get("progress_text") is not None:
                    txt = S.get("progress_text_value")
                    if txt:
                        S["progress_text"].value = txt
                if S.get("progress_bar") is not None:
                    done = S.get("progress_done", 0)
                    total = S.get("progress_total", 0)
                    if total > 0:
                        S["progress_bar"].value = max(
                            0.0, min(1.0, done / total)
                        )
                    else:
                        S["progress_bar"].value = None
                page.update()
            except Exception:
                pass
            await asyncio.sleep(0.25)

    poll_task = asyncio.create_task(_poll_progress())

    # Профиль для albedo
    if (entry.map_type == MapType.ALBEDO
            and entry.albedo_profile
            and hasattr(analyzer, "_profile_key")):
        analyzer._profile_key = entry.albedo_profile

    # ─── Применение фикса в отдельном потоке ───
    try:
        fixed = await asyncio.to_thread(analyzer.fix,
                                         entry.working, fix_id)
    except Exception as ex:
        set_progress_callback(None)
        poll_state["running"] = False
        await asyncio.sleep(0.5)
        await hide_progress(S, page)
        log(S, t("panel.fix_fail", fix=fix_id, err=str(ex)), T["danger"])
        return
    finally:
        set_progress_callback(None)


    entry.working = fixed
    entry.had_fixes = True

    try:
        entry._seam_cache = None
    except Exception:
        pass

    # ─── Пересчёт отчёта тоже в потоке ───
    try:
        entry.report = await asyncio.to_thread(
            analyzer.analyze,
            entry.working,
            entry.albedo_profile,
            entry.filename,
        )
    except Exception as ex:
        poll_state["running"] = False
        await asyncio.sleep(0.5)
        await hide_progress(S, page)
        log(S, t("panel.refix_fail", err=str(ex)), T["danger"])
        return


    # ─── Останавливаем поллинг ───
    poll_state["running"] = False
    await asyncio.sleep(0.5)
    await hide_progress(S, page)

    sev_after = entry.report.severity.value
    issues_after = len(entry.report.issues)

    rec = {
        "issue_code": issue_code,
        "fix_id": fix_id,
        "fix_label": fix_label,
        "sev_before": sev_before,
        "sev_after": sev_after,
        "issues_before": issues_before,
        "issues_after": issues_after,
        "prev_working": prev_working,
        "prev_report": prev_report,
    }
    entry.fix_history.append(rec)

    log(S, t("panel.fix_log",
             name=entry.filename, fix=fix_label,
             before=t("sev." + sev_before),
             after=t("sev." + sev_after)),
        T["success"])

    bottom_slot.content = _make_fix_result_row(S, page, T, entry, rec)

    show_fix_result(
        page=page,
        T=T,
        filename=entry.filename,
        fix_label=fix_label,
        severity_before=sev_before,
        severity_after=sev_after,
        issues_before=issues_before,
        issues_after=issues_after,
        metrics_before=(prev_report.metrics if prev_report else {}),
        metrics_after=(entry.report.metrics if entry.report else {}),
        map_type=entry.map_type.value,
    )

    try:
        panel = S.get("report_panel")
        if panel is not None and hasattr(panel, "render"):
            panel.render()
    except Exception:
        pass



def _undo_fix(S, page, T, entry: MapEntry, rec: dict):
    prev_working = rec.get("prev_working")
    if prev_working is None:
        return

    entry.working = prev_working
    entry.report = rec.get("prev_report")

    try:
        entry._seam_cache = None
    except Exception:
        pass

    if rec in entry.fix_history:
        entry.fix_history.remove(rec)

    log(S, t("panel.undo_log", name=entry.filename,
             fix=rec.get("fix_label", "")),
        T["fg2"])

    try:
        panel = S.get("report_panel")
        if panel is not None and hasattr(panel, "render"):
            panel.render()
    except Exception:
        pass