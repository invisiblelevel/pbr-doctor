"""
core/analyzers/ao.py — анализ и ремонт Ambient Occlusion.

Что проверяем:
  1. Grayscale? (R=G=B)
  2. Живая ли? (std > порога)
  3. Не вся ли тёмная? (mean слишком низкий)
  4. Не вся ли светлая? (mean слишком высокий, AO бесполезно)
  5. Пережатый диапазон?

Что фиксим:
  - to_grayscale:    цветная -> grayscale
  - normalize_range: растяжка по перцентилям
  - invert:          инверсия полярности

Тексты issues — ключами локализации.
"""

import numpy as np
from core.analyzers.base import BaseAnalyzer, Report, Issue, Severity
from core.state import MapType
from core.i18n import t


# ═══════════════════════════════════════════════════════════
#  ПОРОГИ
# ═══════════════════════════════════════════════════════════

COLOR_CHANNEL_THRESH = 0.02
DEAD_STD_THRESH      = 0.03
LOW_STD_THRESH       = 0.05
DARK_MEAN_THRESH     = 0.15
LIGHT_MEAN_THRESH    = 0.90
NARROW_RANGE_THRESH  = 0.40


# ═══════════════════════════════════════════════════════════
#  АНАЛИЗАТОР
# ═══════════════════════════════════════════════════════════

class AOAnalyzer(BaseAnalyzer):

    MAP_TYPE = MapType.AO.value

    def analyze(self, img: np.ndarray) -> Report:
        img = self.to_float01(img)

        # ─── цветность ───
        rgb_stack = np.stack([img[:, :, 0], img[:, :, 1], img[:, :, 2]],
                             axis=0)
        channel_std = float(rgb_stack.std(axis=0).mean())
        is_grayscale = channel_std < COLOR_CHANNEL_THRESH

        # ─── яркость ───
        lum = self.grayscale(img)

        mean = float(lum.mean())
        std  = float(lum.std())
        p1   = float(np.percentile(lum, 1))
        p99  = float(np.percentile(lum, 99))
        vmin = float(lum.min())
        vmax = float(lum.max())
        span = p99 - p1

        dark_pct = float((lum < 0.2).mean() * 100.0)

        metrics = {
            "mean":         mean,
            "std":          std,
            "min":          vmin,
            "max":          vmax,
            "p1":           p1,
            "p99":          p99,
            "span_p1_p99":  span,
            "span":         span,
            "dark_pct":     dark_pct,
            "channel_std":  channel_std,
        }

        issues = []

        # ── 1. Не grayscale ──
        if not is_grayscale:
            issues.append(Issue(
                code="not_grayscale",
                severity=Severity.FAIL,
                title_key="ao.not_grayscale.title",
                detail_key="ao.not_grayscale.detail",
                fix_id="to_grayscale",
                fix_label_key="fix.to_grayscale",
                metrics={"channel_std": channel_std},
            ))

        # ── 2. Мёртвая карта ──
        if std < DEAD_STD_THRESH:
            issues.append(Issue(
                code="dead_ao",
                severity=Severity.FAIL,
                title_key="ao.dead.title",
                detail_key="ao.dead.detail",
                fix_id="normalize_range",
                fix_label_key="fix.normalize_range",
                metrics={
                    "std":  std,
                    "mean": mean,
                },
            ))
        elif std < LOW_STD_THRESH:
            issues.append(Issue(
                code="low_variation",
                severity=Severity.WARN,
                title_key="ao.low_var.title",
                detail_key="ao.low_var.detail",
                fix_id="normalize_range",
                fix_label_key="fix.normalize_range",
                metrics={"std": std},
            ))

        # ── 3. Слишком тёмная ──
        if mean < DARK_MEAN_THRESH:
            issues.append(Issue(
                code="too_dark",
                severity=Severity.FAIL,
                title_key="ao.too_dark.title",
                detail_key="ao.too_dark.detail",
                fix_id="invert",
                fix_label_key="fix.invert",
                metrics={
                    "mean":     mean,
                    "dark_pct": dark_pct,
                },
            ))

        # ── 4. Слишком светлая ──
        # AO с открытой сценой — норма. Диапазон полный, std в норме,
        # фиксить тут нечего. Оставляем warn без fix.
        if mean > LIGHT_MEAN_THRESH and dark_pct < 5.0:
            issues.append(Issue(
                code="too_light",
                severity=Severity.WARN,
                title_key="ao.too_light.title",
                detail_key="ao.too_light.detail",
                fix_id=None,
                metrics={"mean": mean},
            ))

        # ── 5. Пережатый диапазон ──
        if std >= DEAD_STD_THRESH and span < NARROW_RANGE_THRESH:
            issues.append(Issue(
                code="narrow_range",
                severity=Severity.WARN,
                title_key="ao.narrow.title",
                detail_key="ao.narrow.detail",
                fix_id="normalize_range",
                fix_label_key="fix.normalize_range",
                metrics={
                    "span": span,
                    "p1":   p1,
                    "p99":  p99,
                },
            ))

        severity = (Severity.FAIL if any(i.severity == Severity.FAIL
                                          for i in issues)
                    else Severity.WARN if issues
                    else Severity.OK)

        return Report(
            map_type=self.MAP_TYPE,
            severity=severity,
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
        if fix_id == "invert":
            return self._fix_invert(img)
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

    def _fix_invert(self, img: np.ndarray) -> np.ndarray:
        lum = self.grayscale(img)
        inv = 1.0 - lum
        return np.stack([inv, inv, inv], axis=-1).astype(np.float32)