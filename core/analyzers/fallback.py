"""
core/analyzers/fallback.py — базовый анализатор для типов, у которых
нет специализированной логики: HEIGHT, EDGE, UNKNOWN.

Стратегия:
  - HEIGHT — базовые проверки (grayscale, мёртвая, диапазон, шум).
  - EDGE   — то же + проверка на бинарность (edge почти всегда 0/1).
  - UNKNOWN — только предупреждения, БЕЗ фиксов (не знаем, что за карта).

Фиксы (только для height / edge):
  - to_grayscale:    цветная -> grayscale
  - normalize_range: растяжка диапазона по перцентилям
  - compress:        слишком шумная -> сгладить
  - binarize_otsu:   для edge — бинаризация

Тексты issues — ключами локализации. Лейбл типа (Height / Edge /
Unknown) подставляется как {label} и берётся из t("fb.label.<mtype>").
"""

import numpy as np
from core.analyzers.base import BaseAnalyzer, Report, Issue, Severity
from core.state import MapType
from core.i18n import t


# ═══════════════════════════════════════════════════════════
#  ПОРОГИ
# ═══════════════════════════════════════════════════════════

COLOR_CHANNEL_THRESH = 0.02
DEAD_STD_THRESH      = 0.02
LOW_STD_THRESH       = 0.04
HIGH_STD_THRESH      = 0.40
NARROW_RANGE_THRESH  = 0.40
DARK_MEAN_THRESH     = 0.05
LIGHT_MEAN_THRESH    = 0.95
MUDDY_LOW            = 0.15
MUDDY_HIGH           = 0.85
MUDDY_WARN_PCT       = 10.0


# ═══════════════════════════════════════════════════════════
#  ЧЕЛОВЕЧЕСКИЕ НАЗВАНИЯ ПО ТИПАМ — теперь через i18n
# ═══════════════════════════════════════════════════════════

def _type_label(mtype: str) -> str:
    """Height / Edge / Unknown — переведённые."""
    key = f"fb.label.{mtype}"
    v = t(key)
    # если ключа нет — t() вернёт сам ключ, подстрахуемся
    if v.startswith("fb.label."):
        return mtype.capitalize()
    return v


# ═══════════════════════════════════════════════════════════
#  АНАЛИЗАТОР
# ═══════════════════════════════════════════════════════════

class FallbackAnalyzer(BaseAnalyzer):
    """
    Универсальный анализатор для height / edge / unknown.
    Ключ в REGISTRY определяет, с каким MAP_TYPE он работает.
    """

    MAP_TYPE = MapType.UNKNOWN.value

    def __init__(self, map_type: str = "unknown"):
        self.MAP_TYPE = map_type
        self._label = _type_label(map_type)

    # ─────────────────────────────────────────────────────
    #  АНАЛИЗ
    # ─────────────────────────────────────────────────────

    def analyze(self, img: np.ndarray) -> Report:
        img = self.to_float01(img)

        mtype = self.MAP_TYPE
        label = self._label

        # ─── Морфология ───
        if img.ndim != 3 or img.shape[2] < 3:
            return Report(
                map_type=mtype,
                severity=Severity.FAIL,
                issues=[Issue(
                    code="bad_shape",
                    severity=Severity.FAIL,
                    title_key="fb.bad_shape.title",
                    detail_key="fb.bad_shape.detail",
                    fix_id=None,
                    metrics={"label": label},
                )],
                metrics={"shape": list(img.shape)},
            )

        # ─── Цветность ───
        rgb_stack = np.stack([img[:, :, 0], img[:, :, 1], img[:, :, 2]],
                             axis=0)
        channel_std = float(rgb_stack.std(axis=0).mean())
        is_grayscale = channel_std < COLOR_CHANNEL_THRESH

        # ─── Яркость ───
        lum = self.grayscale(img)
        mean = float(lum.mean())
        std  = float(lum.std())
        p1   = float(np.percentile(lum, 1))
        p99  = float(np.percentile(lum, 99))
        vmin = float(lum.min())
        vmax = float(lum.max())
        span = p99 - p1

        metrics = {
            "mean":         mean,
            "std":          std,
            "min":          vmin,
            "max":          vmax,
            "p1":           p1,
            "p99":          p99,
            "span_p1_p99":  span,
            "span":         span,
            "channel_std":  channel_std,
            "map_type":     mtype,
        }

        issues = []

        # ═══════════════════════════════════════════════════
        #  UNKNOWN — только предупреждения, без фиксов
        # ═══════════════════════════════════════════════════

        if mtype == "unknown":
            if is_grayscale:
                kind = t("fb.unknown.kind_gray")
            else:
                kind = t("fb.unknown.kind_color")

            issues.append(Issue(
                code="unknown_type",
                severity=Severity.WARN,
                title_key="fb.unknown.title",
                detail_key="fb.unknown.detail",
                fix_id=None,
                metrics={
                    "channel_std": channel_std,
                    "kind":        kind,
                },
            ))

            if std < DEAD_STD_THRESH:
                issues.append(Issue(
                    code="dead_unknown",
                    severity=Severity.WARN,
                    title_key="fb.dead_unknown.title",
                    detail_key="fb.dead_unknown.detail",
                    fix_id=None,
                    metrics={"std": std},
                ))

            sev = Severity.WARN if issues else Severity.OK
            return Report(
                map_type=mtype,
                severity=sev,
                issues=issues,
                metrics=metrics,
            )

        # ═══════════════════════════════════════════════════
        #  HEIGHT / EDGE — с фиксами
        # ═══════════════════════════════════════════════════

        # ── 1. Не grayscale ──
        if not is_grayscale:
            issues.append(Issue(
                code="not_grayscale",
                severity=Severity.FAIL,
                title_key="fb.not_grayscale.title",
                detail_key="fb.not_grayscale.detail",
                fix_id="to_grayscale",
                fix_label_key="fix.to_grayscale",
                metrics={
                    "channel_std": channel_std,
                    "label":       label,
                },
            ))

        # ── 2. Мёртвая карта ──
        if std < DEAD_STD_THRESH:
            issues.append(Issue(
                code="dead",
                severity=Severity.FAIL,
                title_key="fb.dead.title",
                detail_key="fb.dead.detail",
                fix_id="normalize_range",
                fix_label_key="fix.normalize_range",
                metrics={
                    "std":   std,
                    "mean":  mean,
                    "label": label,
                },
            ))
        elif std < LOW_STD_THRESH:
            issues.append(Issue(
                code="low_variation",
                severity=Severity.WARN,
                title_key="fb.low_var.title",
                detail_key="fb.low_var.detail",
                fix_id="normalize_range",
                fix_label_key="fix.normalize_range",
                metrics={
                    "std":   std,
                    "label": label,
                },
            ))

        # ── 3. Пережатый диапазон ──
        elif span < NARROW_RANGE_THRESH:
            issues.append(Issue(
                code="narrow_range",
                severity=Severity.WARN,
                title_key="fb.narrow.title",
                detail_key="fb.narrow.detail",
                fix_id="normalize_range",
                fix_label_key="fix.normalize_range",
                metrics={
                    "span":  span,
                    "p1":    p1,
                    "p99":   p99,
                    "label": label,
                },
            ))

        # ── 4. Всё в край ──
        if mean < DARK_MEAN_THRESH:
            issues.append(Issue(
                code="too_dark",
                severity=Severity.WARN,
                title_key="fb.too_dark.title",
                detail_key="fb.too_dark.detail",
                fix_id="normalize_range",
                fix_label_key="fix.normalize_range",
                metrics={
                    "mean":  mean,
                    "label": label,
                },
            ))
        elif mean > LIGHT_MEAN_THRESH:
            issues.append(Issue(
                code="too_light",
                severity=Severity.WARN,
                title_key="fb.too_light.title",
                detail_key="fb.too_light.detail",
                fix_id="normalize_range",
                fix_label_key="fix.normalize_range",
                metrics={
                    "mean":  mean,
                    "label": label,
                },
            ))

        # ── 5. Слишком шумная ──
        # Для edge-карт это не имеет смысла: бинарные карты всегда
        # имеют std ~0.5, это норма, а не шум.
        if std > HIGH_STD_THRESH and mtype != "edge":
            issues.append(Issue(
                code="too_noisy",
                severity=Severity.WARN,
                title_key="fb.noisy.title",
                detail_key="fb.noisy.detail",
                fix_id="compress",
                fix_label_key="fix.compress",
                metrics={
                    "std":   std,
                    "label": label,
                },
            ))

        # ── 6. EDGE: проверка бинарности ──
        if mtype == "edge":
            is_zero  = lum < MUDDY_LOW
            is_one   = lum > MUDDY_HIGH
            is_muddy = (~is_zero) & (~is_one)
            muddy_pct = float(is_muddy.mean() * 100.0)
            metrics["muddy_pct"] = muddy_pct

            if muddy_pct >= MUDDY_WARN_PCT:
                issues.append(Issue(
                    code="edge_not_binary",
                    severity=Severity.WARN,
                    title_key="fb.edge_not_binary.title",
                    detail_key="fb.edge_not_binary.detail",
                    fix_id="binarize_otsu",
                    fix_label_key="fix.binarize_otsu",
                    metrics={
                        "muddy_pct": muddy_pct,
                        "low":       str(MUDDY_LOW),
                        "high":      str(MUDDY_HIGH),
                    },
                ))

        # ── Severity ──
        sev = Severity.OK
        for iss in issues:
            if iss.severity == Severity.FAIL:
                sev = Severity.FAIL
                break
            if iss.severity == Severity.WARN:
                sev = Severity.WARN

        return Report(
            map_type=mtype,
            severity=sev,
            issues=issues,
            metrics=metrics,
        )

    # ═══════════════════════════════════════════════════════
    #  ФИКСЫ
    # ═══════════════════════════════════════════════════════

    def fix(self, img: np.ndarray, fix_id: str) -> np.ndarray:
        img = self.to_float01(img)
        if fix_id == "to_grayscale":
            return self._fix_to_grayscale(img)
        if fix_id == "normalize_range":
            return self._fix_normalize_range(img)
        if fix_id == "compress":
            return self._fix_compress(img)
        if fix_id == "binarize_otsu":
            return self._fix_binarize_otsu(img)
        raise ValueError(t("err.unknown_fix", fix_id=fix_id))

    def _fix_to_grayscale(self, img: np.ndarray) -> np.ndarray:
        lum = self.grayscale(img)
        return np.stack([lum, lum, lum], axis=-1).astype(np.float32)

    def _fix_normalize_range(self, img: np.ndarray) -> np.ndarray:
        lum = self.grayscale(img)
        p1 = float(np.percentile(lum, 1))
        p99 = float(np.percentile(lum, 99))
        if p99 - p1 < 1e-6:
            return img
        norm = (lum - p1) / (p99 - p1)
        norm = np.clip(norm, 0.0, 1.0)
        return np.stack([norm, norm, norm], axis=-1).astype(np.float32)

    def _fix_compress(self, img: np.ndarray) -> np.ndarray:
        lum = self.grayscale(img)
        mean = float(lum.mean())
        compressed = mean + (lum - mean) * 0.6
        compressed = np.clip(compressed, 0.0, 1.0)
        return np.stack([compressed, compressed, compressed],
                        axis=-1).astype(np.float32)

    def _fix_binarize_otsu(self, img: np.ndarray) -> np.ndarray:
        import cv2
        lum = self.grayscale(img)
        lum8 = np.clip(lum * 255.0, 0, 255).astype(np.uint8)
        threshold, _ = cv2.threshold(lum8, 0, 255,
                                      cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        binary = (lum8 >= threshold).astype(np.float32)
        return np.stack([binary, binary, binary],
                        axis=-1).astype(np.float32)