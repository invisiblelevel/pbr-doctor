"""
core/analyzers/metallic.py — анализ и ремонт Metallic Map.

Что проверяем:
  1. Grayscale? (R=G=B)
  2. Бинарная? (пиксели в 0.1..0.9 — градиенты, плохо)
  3. Не вся ли в 0? (нет металла вообще)
  4. Не вся ли в 1? (вся модель металлическая — странно)

Что фиксим:
  - to_grayscale:   цветная -> grayscale
  - binarize_otsu:  авто-порог по Otsu
  - binarize_hard:  жёсткий порог 0.5

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
MUDDY_LOW            = 0.10
MUDDY_HIGH           = 0.90
MUDDY_FAIL_PCT       = 15.0
MUDDY_WARN_PCT       = 5.0
DEAD_ALL_ZERO_PCT    = 99.5
DEAD_ALL_ONE_PCT     = 99.5


# ═══════════════════════════════════════════════════════════
#  АНАЛИЗАТОР
# ═══════════════════════════════════════════════════════════

class MetallicAnalyzer(BaseAnalyzer):

    MAP_TYPE = MapType.METALLIC.value

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

        # ─── распределение по зонам ───
        is_zero  = lum < MUDDY_LOW
        is_one   = lum > MUDDY_HIGH
        is_muddy = (~is_zero) & (~is_one)

        zero_pct  = float(is_zero.mean() * 100.0)
        one_pct   = float(is_one.mean() * 100.0)
        muddy_pct = float(is_muddy.mean() * 100.0)

        metrics = {
            "mean":        mean,
            "std":         std,
            "zero_pct":    zero_pct,
            "one_pct":     one_pct,
            "muddy_pct":   muddy_pct,
            "channel_std": channel_std,
        }

        issues = []

        # ── 1. Не grayscale ──
        if not is_grayscale:
            issues.append(Issue(
                code="not_grayscale",
                severity=Severity.FAIL,
                title_key="metal.not_grayscale.title",
                detail_key="metal.not_grayscale.detail",
                fix_id="to_grayscale",
                fix_label_key="fix.to_grayscale",
                metrics={"channel_std": channel_std},
            ))

        # ── 2. Градиенты в серой зоне ──
        if muddy_pct >= MUDDY_FAIL_PCT:
            issues.append(Issue(
                code="muddy_metallic",
                severity=Severity.FAIL,
                title_key="metal.muddy.title",
                detail_key="metal.muddy.detail",
                fix_id="binarize_otsu",
                fix_label_key="fix.binarize_otsu",
                metrics={
                    "muddy_pct": muddy_pct,
                    "low":       str(MUDDY_LOW),
                    "high":      str(MUDDY_HIGH),
                },
            ))
        elif muddy_pct >= MUDDY_WARN_PCT:
            issues.append(Issue(
                code="muddy_metallic_mild",
                severity=Severity.WARN,
                title_key="metal.muddy_mild.title",
                detail_key="metal.muddy_mild.detail",
                fix_id="binarize_otsu",
                fix_label_key="fix.binarize_otsu",
                metrics={"muddy_pct": muddy_pct},
            ))

        # ── 3. Всё в нуле ──
        if zero_pct >= DEAD_ALL_ZERO_PCT:
            issues.append(Issue(
                code="all_dielectric",
                severity=Severity.WARN,
                title_key="metal.all_zero.title",
                detail_key="metal.all_zero.detail",
                fix_id=None,
                metrics={"zero_pct": zero_pct},
            ))

        # ── 4. Всё в единице ──
        if one_pct >= DEAD_ALL_ONE_PCT:
            issues.append(Issue(
                code="all_metal",
                severity=Severity.WARN,
                title_key="metal.all_one.title",
                detail_key="metal.all_one.detail",
                fix_id=None,
                metrics={"one_pct": one_pct},
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
        if fix_id == "binarize_otsu":
            return self._fix_binarize_otsu(img)
        if fix_id == "binarize_hard":
            return self._fix_binarize_hard(img)
        raise ValueError(t("err.unknown_fix", fix_id=fix_id))

    def _fix_to_grayscale(self, img: np.ndarray) -> np.ndarray:
        lum = self.grayscale(img)
        return np.stack([lum, lum, lum], axis=-1).astype(np.float32)

    def _fix_binarize_otsu(self, img: np.ndarray) -> np.ndarray:
        """Порог по методу Otsu — авто-разделение двух пиков гистограммы."""
        import cv2
        lum = self.grayscale(img)
        lum8 = np.clip(lum * 255.0, 0, 255).astype(np.uint8)
        threshold, _ = cv2.threshold(lum8, 0, 255,
                                      cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        binary = (lum8 >= threshold).astype(np.float32)
        return np.stack([binary, binary, binary],
                        axis=-1).astype(np.float32)

    def _fix_binarize_hard(self, img: np.ndarray) -> np.ndarray:
        """Жёсткий порог 0.5."""
        lum = self.grayscale(img)
        binary = (lum >= 0.5).astype(np.float32)
        return np.stack([binary, binary, binary],
                        axis=-1).astype(np.float32)