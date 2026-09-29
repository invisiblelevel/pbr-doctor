"""
ui/dialogs_fix.py — всплывающее окно с результатом фикса.

Умная модалка: показывает не только severity, но и ключевые метрики
до/после — чтобы было видно что фикс РЕАЛЬНО работает, даже если
severity не изменился.

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


# ═══════════════════════════════════════════════════════════
#  КЛЮЧЕВЫЕ МЕТРИКИ ПО ТИПАМ КАРТ
#  (имя ключа, человекочитаемый label-key, направление улучшения)
#  direction: +1 = «больше = лучше», -1 = «меньше = лучше»
# ═══════════════════════════════════════════════════════════

# (имя, label-key, direction, norm-key)
# direction: +1 = «больше лучше», -1 = «меньше лучше», None = без дельты
# norm-key: ключ i18n с описанием нормы (в скобках)

KEY_METRICS = {
    "albedo": [
        ("std_L",         "metric.std_l",       +1, "metric.std_l.norm"),
        ("soapy_pct",     "metric.soapy_pct",   -1, "metric.soapy_pct.norm"),
        ("p1_L",          "metric.p1_l",        +1, "metric.p1_l.norm"),
        ("p99_L",         "metric.p99_l",       -1, "metric.p99_l.norm"),
        ("mean_S",        "metric.mean_s",      +1, "metric.mean_s.norm"),
        ("color_spread",  "metric.color_spread",-1, "metric.color_spread.norm"),
    ],
    "normal": [
        ("mean_length",   "metric.mean_length", +1, "metric.mean_length.norm"),
        ("bad_length_pct","metric.bad_pct",     -1, "metric.bad_pct.norm"),
        ("angle_deg",     "metric.angle",       -1, "metric.angle.norm"),
    ],
    "roughness": [
        ("std",           "metric.std",         +1, "metric.std.norm"),
        ("span_p1_p99",   "metric.span",        +1, "metric.span.norm"),
    ],
    "metallic": [
        ("muddy_pct",     "metric.muddy_pct",   -1, "metric.muddy_pct.norm"),
    ],
    "ao": [
        ("std",           "metric.std",         +1, "metric.std.norm"),
        ("mean",          "metric.mean",        None, None),
    ],
    "height": [
        ("std",           "metric.std",         +1, "metric.std.norm"),
        ("span_p1_p99",   "metric.span",        +1, "metric.span.norm"),
    ],
    "edge": [
        ("std",           "metric.std",         +1, "metric.std.norm"),
    ],
    "unknown": [],
    "orm":     [],
}


# ═══════════════════════════════════════════════════════════
#  ГЛАВНАЯ ФУНКЦИЯ
# ═══════════════════════════════════════════════════════════

def show_fix_result(page: ft.Page, T: dict, filename: str,
                    fix_label: str,
                    severity_before: str,
                    severity_after: str,
                    issues_before: int,
                    issues_after: int,
                    metrics_before: dict = None,
                    metrics_after: dict = None,
                    map_type: str = None):
    """
    Показывает модалку с результатом фикса.

    severity_before / after: 'ok' | 'warn' | 'fail'
    issues_before / after:   количество issues до и после
    metrics_before / after:  сырые метрики (для таблицы до/после)
    map_type:                тип карты — чтобы выбрать ключевые метрики
    """

    order = {"ok": 0, "warn": 1, "fail": 2}
    b = order.get(severity_before, 3)
    a = order.get(severity_after, 3)

    issues_delta = issues_before - issues_after

    # ─── Считаем улучшения метрик ───
    metric_deltas = _compute_metric_deltas(
        map_type, metrics_before or {}, metrics_after or {}
    )
    improved_count = sum(1 for d in metric_deltas if d["verdict"] == "better")
    worse_count = sum(1 for d in metric_deltas if d["verdict"] == "worse")

    # ─── Определяем итоговый статус ───
    # 1) Severity улучшился
    # 2) Severity тот же, но issues убавилось
    # 3) Severity тот же, issues столько же, но метрики улучшились
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
    elif a == b and issues_delta > 0:
        icon_name = "chevron-down"
        icon_color = T["warn"]
        headline = t("dlg_fix.headline.partial",
                     b=issues_before, a=issues_after)
    elif a == b and issues_delta == 0:
        if improved_count > 0 and worse_count == 0:
            # Severity не изменилась, но метрики явно улучшились
            icon_name = "chevron-down"
            icon_color = T["warn"]
            headline = t("dlg_fix.headline.metrics_better",
                         n=improved_count)
        elif worse_count > 0 and improved_count == 0:
            icon_name = "x"
            icon_color = T["danger"]
            headline = t("dlg_fix.headline.metrics_worse",
                         n=worse_count)
        elif improved_count > 0 and worse_count > 0:
            icon_name = "info"
            icon_color = T["fg2"]
            headline = t("dlg_fix.headline.mixed",
                         good=improved_count, bad=worse_count)
        else:
            icon_name = "info"
            icon_color = T["fg2"]
            headline = t("dlg_fix.headline.unchanged")
    elif issues_delta < 0:
        icon_name = "x"
        icon_color = T["danger"]
        headline = t("dlg_fix.headline.worse_iss",
                     b=issues_before, a=issues_after)
    else:
        icon_name = "x"
        icon_color = T["danger"]
        headline = t("dlg_fix.headline.worse")

    # ─── Строки со «до -> после» ───

    def _row_plain(label, before, after):
        return ft.Row([
            ft.Text(label, color=T["fg3"], size=12, font_family=FONT,
                    width=150),
            ft.Text(before, color=T["fg2"], size=12, font_family=FONT_MONO,
                    weight=ft.FontWeight.W_600, width=90),
            ft.Text("→", color=T["fg3"], size=12, font_family=FONT),
            ft.Text(after, color=T["fg"], size=12, font_family=FONT_MONO,
                    weight=ft.FontWeight.W_600, width=90),
        ], spacing=8)

    def _row_metric(metric_name, label, before_val, after_val, verdict,
                    norm_key=None):
        # цвет дельты
        if verdict == "better":
            delta_color = T["success"]
            arrow = "▲" if after_val > before_val else "▼"
        elif verdict == "worse":
            delta_color = T["danger"]
            arrow = "▼" if after_val > before_val else "▲"
        else:
            delta_color = T["fg3"]
            arrow = "="

        # Определяем формат числа: если метрика в процентах — «%»,
        # если сотая доля (0..1) — 2 знака, иначе 1 знак.
        def _fmt(v):
            if v is None:
                return "—"
            if not isinstance(v, (int, float)):
                return str(v)
            if metric_name in ("soapy_pct", "bad_length_pct", "muddy_pct"):
                return f"{v:.1f}%"
            if metric_name in ("mean_S", "mean_length"):
                return f"{v:.3f}"
            return f"{v:.1f}"

        norm_txt = ""
        if norm_key:
            norm_txt = t(norm_key)
            if norm_txt == norm_key:
                norm_txt = ""

        return ft.Row([
            ft.Text(label, color=T["fg3"], size=12, font_family=FONT,
                    width=150),
            ft.Text(_fmt(before_val), color=T["fg2"], size=12,
                    font_family=FONT_MONO, width=90),
            ft.Text("→", color=T["fg3"], size=12, font_family=FONT),
            ft.Text(_fmt(after_val), color=T["fg"], size=12,
                    font_family=FONT_MONO,
                    weight=ft.FontWeight.W_600, width=90),
            ft.Text(arrow, color=delta_color, size=14,
                    font_family=FONT, width=20),
            ft.Text(norm_txt, color=T["fg3"], size=11,
                    font_family=FONT, expand=True),
        ], spacing=8)

    # ─── Собираем строки ───
    rows = []

    # Severity и issues
    sev_b_txt = f"{t('sev.' + severity_before)} ({issues_before})"
    sev_a_txt = f"{t('sev.' + severity_after)} ({issues_after})"
    rows.append(_row_plain(t("dlg_fix.row_status"), sev_b_txt, sev_a_txt))

    # Ключевые метрики
    if metric_deltas:
        rows.append(ft.Container(height=4))
        rows.append(ft.Text(t("dlg_fix.row_metrics"),
                            color=T["fg3"], size=11, font_family=FONT,
                            weight=ft.FontWeight.W_600))
        for d in metric_deltas:
            rows.append(_row_metric(
                d["name"], t(d["label_key"]),
                d["before"], d["after"], d["verdict"],
                d.get("norm_key"),
            ))

    body = ft.Column([
        ft.Row([
            img_icon(icon_name, icon_color, 24),
            ft.Text(headline, color=T["fg"], size=14, font_family=FONT,
                    weight=ft.FontWeight.W_600, expand=True,
                    no_wrap=False),
        ], spacing=10),

        ft.Container(height=4),

        ft.Text(filename, color=T["fg2"], size=12, font_family=FONT_MONO,
                overflow=ft.TextOverflow.ELLIPSIS),
        ft.Text(t("dlg_fix.fix_line", label=fix_label),
                color=T["fg3"], size=11, font_family=FONT),

        ft.Container(height=8),
        ft.Divider(color=T["input"], height=1),
        ft.Container(height=8),

        *rows,
    ], spacing=4, tight=True)

    # ─── диалог ───
    dlg = ft.AlertDialog(
        modal=True,
        title=None,
        content=ft.Container(content=body, width=620, padding=6),
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


# ═══════════════════════════════════════════════════════════
#  СРАВНЕНИЕ МЕТРИК
# ═══════════════════════════════════════════════════════════

def _compute_metric_deltas(map_type, before: dict, after: dict) -> list:
    """
    Возвращает список dict-ов:
      { "name": "std_L", "label_key": "metric.std_l",
        "norm_key": "metric.std_l.norm",
        "before": 10.2, "after": 32.2,
        "verdict": "better" | "worse" | "same" }
    """
    if not map_type:
        return []

    spec = KEY_METRICS.get(map_type, [])
    deltas = []

    for entry in spec:
        # Поддерживаем старый формат (3 элемента) и новый (4)
        if len(entry) == 3:
            key, label_key, direction = entry
            norm_key = None
        else:
            key, label_key, direction, norm_key = entry

        b_val = before.get(key)
        a_val = after.get(key)
        if b_val is None or a_val is None:
            continue
        if not isinstance(b_val, (int, float)):
            continue
        if not isinstance(a_val, (int, float)):
            continue

        diff = a_val - b_val
        eps = 1e-6
        rel = abs(diff) / (abs(b_val) + eps)

        if direction is None or rel < 0.02:
            verdict = "same"
        else:
            improved = (diff * direction) > 0
            verdict = "better" if improved else "worse"

        deltas.append({
            "name": key,
            "label_key": label_key,
            "norm_key": norm_key,
            "before": b_val,
            "after": a_val,
            "verdict": verdict,
        })

    return deltas