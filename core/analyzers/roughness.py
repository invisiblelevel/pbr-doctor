"""
core/analyzers/roughness.py — анализ и ремонт Roughness Map.

Что проверяем:
  1. Grayscale ли карта? (R=G=B)
  2. Живая ли? (std > порога)
  3. Полный ли диапазон? (min близко к 0, max близко к 1)
  4. Не пережата ли? (не вся в узком диапазоне)
  5. Не шумная ли? (std не зашкаливает)

Что фиксим:
  - to_grayscale:    цветная -> grayscale
  - normalize_range: растяжка диапазона на [0, 1]
  - compress:        слишком контрастная -> мягче

Тексты issues — ключами локализации.
"""

import numpy as np
from core.analyzers.base import BaseAnalyzer, Report, Issue, Severity
from core.state import MapType
from core.i18n import t


# ═══════════════════════════════════════════════════════════
#  ПОРОГИ
# ═══════════════════════════════════════════════════════════

DEAD_STD_THRESH       = 0.03
LOW_STD_THRESH        = 0.06
HIGH_STD_THRESH       = 0.35
NARROW_RANGE_THRESH   = 0.50
COLOR_CHANNEL_THRESH  = 0.02


# ═══════════════════════════════════════════════════════════
#  АНАЛИЗАТОР
# ═══════════════════════════════════════════════════════════

class RoughnessAnalyzer(BaseAnalyzer):

    MAP_TYPE = MapType.ROUGHNESS.value

    def analyze(self, img: np.ndarray) -> Report:
        img = self.to_float01(img)

        # ─── цветность ───
        rgb_stack = np.stack([img[:, :, 0], img[:, :, 1], img[:, :, 2]],
                             axis=0)
        channel_std = float(rgb_stack.std(axis=0).mean())
        is_grayscale = channel_std < COLOR_CHANNEL_THRESH

        # ─── яркость ───
        lum = self.grayscale(img)

        mean   = float(lum.mean())
        std    = float(lum.std())
        p1     = float(np.percentile(lum, 1))
        p99    = float(np.percentile(lum, 99))
        p5     = float(np.percentile(lum, 5))
        p95    = float(np.percentile(lum, 95))
        vmin   = float(lum.min())
        vmax   = float(lum.max())
        span   = p99 - p1

        mid_pct = float(((lum > 0.45) & (lum < 0.55)).mean() * 100.0)

        metrics = {
            "mean":         mean,
            "std":          std,
            "min":          vmin,
            "max":          vmax,
            "p1":           p1,
            "p99":          p99,
            "p5":           p5,
            "p95":          p95,
            "span_p1_p99":  span,
            "span":         span,
            "mid_pct":      mid_pct,
            "channel_std":  channel_std,
        }

        issues = []

        # ── 1. Не grayscale ──
        if not is_grayscale:
            issues.append(Issue(
                code="not_grayscale",
                severity=Severity.FAIL,
                title_key="rough.not_grayscale.title",
                detail_key="rough.not_grayscale.detail",
                fix_id="to_grayscale",
                fix_label_key="fix.to_grayscale",
                metrics={"channel_std": channel_std},
            ))

        # ── 2. Мёртвая карта ──
        if std < DEAD_STD_THRESH:
            issues.append(Issue(
                code="dead_roughness",
                severity=Severity.FAIL,
                title_key="rough.dead.title",
                detail_key="rough.dead.detail",
                fix_id="normalize_range",
                fix_label_key="fix.normalize_range",
                metrics={
                    "std":     std,
                    "mean":    mean,
                    "p1":      p1,
                    "p99":     p99,
                    "mid_pct": mid_pct,
                },
            ))
        elif std < LOW_STD_THRESH:
            issues.append(Issue(
                code="low_variation",
                severity=Severity.WARN,
                title_key="rough.low_var.title",
                detail_key="rough.low_var.detail",
                fix_id="normalize_range",
                fix_label_key="fix.normalize_range",
                metrics={"std": std},
            ))

        # ── 3. Узкий диапазон ──
        elif span < NARROW_RANGE_THRESH:
            issues.append(Issue(
                code="narrow_range",
                severity=Severity.WARN,
                title_key="rough.narrow.title",
                detail_key="rough.narrow.detail",
                fix_id="normalize_range",
                fix_label_key="fix.normalize_range",
                metrics={
                    "span": span,
                    "p1":   p1,
                    "p99":  p99,
                },
            ))

        # ── 4. Шумная карта ──
        if std > HIGH_STD_THRESH:
            issues.append(Issue(
                code="too_noisy",
                severity=Severity.WARN,
                title_key="rough.noisy.title",
                detail_key="rough.noisy.detail",
                fix_id="compress",
                fix_label_key="fix.compress",
                metrics={"std": std},
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
        if fix_id == "compress":
            return self._fix_compress(img)
        raise ValueError(t("err.unknown_fix", fix_id=fix_id))

    def _fix_to_grayscale(self, img: np.ndarray) -> np.ndarray:
        lum = self.grayscale(img)
        out = np.stack([lum, lum, lum], axis=-1)
        return out.astype(np.float32)

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