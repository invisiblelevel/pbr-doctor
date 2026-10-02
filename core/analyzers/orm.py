"""
core/analyzers/orm.py — анализатор ORM (Occlusion-Roughness-Metallic).

ORM — упакованная карта:
  R = Ambient Occlusion
  G = Roughness
  B = Metallic

Стратегия:
  - Внутри гоняем каждый канал через логику соответствующего анализатора
    (AO / Roughness / Metallic), но без фиксов — только для сбора issues.
  - Issues получают префикс [R] / [G] / [B] через title_wrap_key
    и fix_id вида "ch:R:normalize_range".
  - Фикс применяется ТОЛЬКО к своему каналу, остальные не трогаются.
  - Общие grayscale-фиксы (to_grayscale) для ORM ЗАПРЕЩЕНЫ — они
    убивают семантику каналов.

Fix All ORM: fix_id = "ch:all:fix_all"

Тексты issues — ключами локализации.
"""

import numpy as np

from core.analyzers.base import (
    BaseAnalyzer, Issue, Report, Severity,
)
from core.analyzers.ao import AOAnalyzer
from core.analyzers.roughness import RoughnessAnalyzer
from core.analyzers.metallic import MetallicAnalyzer
from core.i18n import t


# ═══════════════════════════════════════════════════════════
#  ВСПОМОГАТЕЛЬНОЕ
# ═══════════════════════════════════════════════════════════

CHANNEL_INDEX = {"R": 0, "G": 1, "B": 2}

# обёртки для title — "[R] AO: {text}"
TITLE_WRAP_KEY = {
    "R": "orm.wrap.R",
    "G": "orm.wrap.G",
    "B": "orm.wrap.B",
}

ALLOWED_FIXES = {
    "normalize_range", "invert",
    "compress",
    "binarize_otsu", "binarize_hard",
    "fix_all",
}

FORBIDDEN_FIXES = {"to_grayscale"}


# ═══════════════════════════════════════════════════════════
#  ORM ANALYZER
# ═══════════════════════════════════════════════════════════

class ORMAnalyzer(BaseAnalyzer):
    MAP_TYPE = "orm"

    def __init__(self):
        self._ao = AOAnalyzer()
        self._rough = RoughnessAnalyzer()
        self._metal = MetallicAnalyzer()

    # ─────────────────────────────────────────────────────
    #  АНАЛИЗ
    # ─────────────────────────────────────────────────────

    def analyze(self, img: np.ndarray,
                profile_key: str = None,
                filename: str = None) -> Report:
        img = self.to_float01(img)
        img = self.downsample_for_analysis(img, max_size=2048)
        if img.ndim != 3 or img.shape[2] < 3:
            return Report(
                map_type=self.MAP_TYPE,
                severity=Severity.FAIL,
                issues=[Issue(
                    code="orm_bad_shape",
                    severity=Severity.FAIL,
                    title_key="orm.bad_shape.title",
                    detail_key="orm.bad_shape.detail",
                    fix_id=None,
                )],
                metrics={"shape": list(img.shape)},
            )

        r = img[:, :, 0]
        g = img[:, :, 1]
        b = img[:, :, 2]

        issues = []
        metrics = {}

        # ─── Валидация: не grayscale ли это? ───
        rgb_stack = np.stack([r, g, b], axis=0)
        channel_std = float(rgb_stack.std(axis=0).mean())
        is_grayscale = channel_std < 0.02
        metrics["channel_std"] = channel_std
        metrics["is_grayscale"] = is_grayscale

        if is_grayscale:
            issues.append(Issue(
                code="orm_grayscale",
                severity=Severity.FAIL,
                title_key="orm.grayscale.title",
                detail_key="orm.grayscale.detail",
                fix_id=None,
            ))

        # ─── AO (R-канал) ───
        ao_img = self._as_rgb(r)
        ao_report = self._ao.analyze(ao_img)
        metrics["R_ao"] = ao_report.metrics
        for iss in ao_report.issues:
            issues.append(self._wrap_issue(iss, "R"))

        # ─── Roughness (G-канал) ───
        rough_img = self._as_rgb(g)
        rough_report = self._rough.analyze(rough_img)
        metrics["G_rough"] = rough_report.metrics
        for iss in rough_report.issues:
            issues.append(self._wrap_issue(iss, "G"))

        # ─── Metallic (B-канал) ───
        metal_img = self._as_rgb(b)
        metal_report = self._metal.analyze(metal_img)
        metrics["B_metal"] = metal_report.metrics
        for iss in metal_report.issues:
            issues.append(self._wrap_issue(iss, "B"))

        # ─── Валидация: B-канал бинарный? ───
        b_low  = float((b < 0.15).mean())
        b_high = float((b > 0.85).mean())
        b_mid  = float(((b >= 0.15) & (b <= 0.85)).mean())
        metrics["B_low_pct"]  = b_low
        metrics["B_high_pct"] = b_high
        metrics["B_mid_pct"]  = b_mid

        if b_mid > 0.5:
            issues.append(Issue(
                code="orm_metal_muddy",
                severity=Severity.WARN,
                title_key="orm.metal_muddy.title",
                detail_key="orm.metal_muddy.detail",
                fix_id="ch:B:binarize_otsu",
                fix_label_key="fix.binarize_otsu",
                metrics={"mid_pct": b_mid * 100.0},
            ))

        # ─── Сводная severity ───
        sev = Severity.OK
        for iss in issues:
            if iss.severity == Severity.FAIL:
                sev = Severity.FAIL
                break
            if iss.severity == Severity.WARN:
                sev = Severity.WARN

        # ─── Fix All (если есть что фиксить) ───
        if any(i.fix_id for i in issues):
            issues.insert(0, Issue(
                code="orm_fix_all",
                severity=sev if sev != Severity.OK else Severity.WARN,
                title_key="orm.fix_all.title",
                detail_key="orm.fix_all.detail",
                fix_id="ch:all:fix_all",
                fix_label_key="fix.fix_all_orm",
            ))

        return Report(
            map_type=self.MAP_TYPE,
            severity=sev,
            issues=issues,
            metrics=metrics,
        )

    # ─────────────────────────────────────────────────────
    #  ФИКСЫ
    # ─────────────────────────────────────────────────────

    def fix(self, img: np.ndarray, fix_id: str) -> np.ndarray:
        """
        fix_id формата:
          "ch:R:normalize_range"
          "ch:G:compress"
          "ch:B:binarize_otsu"
          "ch:all:fix_all"
        """
        img = self.to_float01(img).copy()
        if img.ndim != 3 or img.shape[2] < 3:
            return img

        parts = fix_id.split(":")
        if len(parts) != 3 or parts[0] != "ch":
            raise ValueError(t("err.orm_bad_fix_id", fix_id=fix_id))

        _, channel, op = parts

        if op in FORBIDDEN_FIXES:
            raise ValueError(t("err.orm_forbidden_fix", op=op))

        if channel == "all":
            return self._fix_all(img)

        if channel not in CHANNEL_INDEX:
            raise ValueError(t("err.orm_unknown_channel", channel=channel))

        return self._fix_channel(img, channel, op)

    # ─────────────────────────────────────────────────────
    #  ВНУТРЕННЕЕ
    # ─────────────────────────────────────────────────────

    def _fix_all(self, img: np.ndarray) -> np.ndarray:
        """Применяет лучший фикс к каждому каналу, где есть issues."""
        from core.analyzers.base import emit_progress

        out = img.copy()
        for ch in ("R", "G", "B"):
            emit_progress(f"ORM: канал [{ch}]...")
            ch_img = self._as_rgb(out[:, :, CHANNEL_INDEX[ch]])
            report = self._analyze_channel(ch, ch_img)
            if not report.issues:
                continue
            for iss in report.issues:
                if iss.fix_id:
                    op = iss.fix_id
                    if op.startswith(f"ch:{ch}:"):
                        op = op.split(":")[2]
                    try:
                        out = self._fix_channel(out, ch, op)
                    except Exception:
                        pass
                    break
        emit_progress("ORM: готово")
        return out

    def _fix_channel(self, img: np.ndarray, channel: str,
                     op: str) -> np.ndarray:
        """Применяет операцию op к одному каналу."""
        idx = CHANNEL_INDEX[channel]
        ch = img[:, :, idx]

        if channel == "R":
            analyzer = self._ao
        elif channel == "G":
            analyzer = self._rough
        else:
            analyzer = self._metal

        ch_rgb = self._as_rgb(ch)
        fixed_rgb = analyzer.fix(ch_rgb, op)
        fixed_ch = fixed_rgb[:, :, 0]

        out = img.copy()
        out[:, :, idx] = fixed_ch
        return out

    def _analyze_channel(self, channel: str,
                         ch_rgb: np.ndarray) -> Report:
        if channel == "R":
            return self._ao.analyze(ch_rgb)
        if channel == "G":
            return self._rough.analyze(ch_rgb)
        return self._metal.analyze(ch_rgb)

    @staticmethod
    def _as_rgb(channel: np.ndarray) -> np.ndarray:
        """[H,W] -> [H,W,3] (дублируем канал)."""
        return np.stack([channel, channel, channel], axis=2)

    @staticmethod
    def _wrap_issue(iss: Issue, channel: str) -> Issue:
        """
        Оборачивает issue канала: добавляет префикс [R]/[G]/[B]
        через title_wrap_key и переписывает fix_id с каналом.
        """
        new_fix_id = None
        if iss.fix_id:
            new_fix_id = f"ch:{channel}:{iss.fix_id}"

        return Issue(
            code=f"{channel}_{iss.code}",
            severity=iss.severity,
            title_key=iss.title_key,
            detail_key=iss.detail_key,
            fix_label_key=iss.fix_label_key,
            title_wrap_key=TITLE_WRAP_KEY[channel],
            fix_id=new_fix_id,
            metrics=dict(iss.metrics),
        )