"""
core/analyzers/albedo.py — анализ и ремонт Albedo (BaseColor).

Что проверяем:
  1. Мыльность (soapiness) — AI-генераторы оставляют гладкие пятна
     там, где должна быть текстура.
  2. Недосвет / пересвет — тёмные/светлые зоны за порогами профиля.
  3. Плоский контраст — std(L) слишком низкий.
  4. Зашкаливающий контраст — std(L) слишком высокий.
  5. Плоская насыщенность — средний S в HSV слишком низкий.
  6. Перенасыщенность — средний S слишком высокий.
  7. Цветовой сдвиг — средний цвет между каналами R/G/B разъехался.

Профили текстур — в core/albedo_profiles.py (61 профиль).
Профиль определяется автоматически по имени файла.
Фолбэк — stone.

Фиксы:
  - auto_correct:     CLAHE + auto-levels по профилю + contrast stretch + sat
  - clahe_only:       только CLAHE
  - auto_levels_only: только auto-levels без CLAHE
  - remove_soap:      убрать мыльность (adaptive unsharp)
  - saturate_15/30:   поднять насыщенность
  - desaturate_15:    приглушить насыщенность
  - white_balance:    выровнять баланс белого (gray world)
  - decontrast:       снизить контраст
  - remove_color_cast:убрать паразитный оттенок в LAB
"""

import numpy as np
import cv2

from core.analyzers.base import BaseAnalyzer, Report, Issue, Severity
from core.state import MapType
from core.albedo_profiles import detect_profile, get_profile, DEFAULT_PROFILE
from core.i18n import t


# ═══════════════════════════════════════════════════════════
#  ПОРОГИ
# ═══════════════════════════════════════════════════════════

SOAP_WINDOW       = 15
SOAP_THRESHOLD    = 25.0
SOAP_WARN_PCT     = 20.0

FLAT_STD_THRESH   = 30.0
HARD_STD_THRESH   = 80.0

FLAT_SAT_THRESH   = 0.15
OVER_SAT_THRESH   = 0.75

COLOR_CAST_THRESH = 15.0

DARK_OFFSET       = 10
LIGHT_OFFSET      = 10


# ═══════════════════════════════════════════════════════════
#  АНАЛИЗАТОР
# ═══════════════════════════════════════════════════════════

class AlbedoAnalyzer(BaseAnalyzer):

    MAP_TYPE = MapType.ALBEDO.value

    def __init__(self):
        self._profile_key = DEFAULT_PROFILE

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
                    code="bad_shape",
                    severity=Severity.FAIL,
                    title_key="fb.bad_shape.title",
                    detail_key="fb.bad_shape.detail",
                    fix_id=None,
                    metrics={"label": "Albedo"},
                )],
                metrics={"shape": list(img.shape)},
            )

        # ─── Профиль ───
        if profile_key is None:
            if filename:
                profile_key = detect_profile(filename)
            else:
                profile_key = self._profile_key
        self._profile_key = profile_key
        profile = get_profile(profile_key)
        dark_t = profile["dark"]
        light_t = profile["light"]

        # ─── LAB ───
        arr_u8 = np.clip(img * 255.0, 0, 255).astype(np.uint8)
        lab = cv2.cvtColor(arr_u8, cv2.COLOR_RGB2LAB)
        L = lab[:, :, 0].astype(np.float32)

        # ─── HSV ───
        hsv = cv2.cvtColor(arr_u8, cv2.COLOR_RGB2HSV).astype(np.float32)
        S = hsv[:, :, 1]

        # ─── Метрики ───
        mean_l = float(L.mean())
        std_l = float(L.std())
        p1 = float(np.percentile(L, 1))
        p99 = float(np.percentile(L, 99))
        mean_s = float(S.mean() / 255.0)

        r_mean = float(arr_u8[:, :, 0].mean())
        g_mean = float(arr_u8[:, :, 1].mean())
        b_mean = float(arr_u8[:, :, 2].mean())
        color_spread = max(abs(r_mean - g_mean),
                            abs(g_mean - b_mean),
                            abs(r_mean - b_mean))

        # ─── Мыльность ───
        k = SOAP_WINDOW if SOAP_WINDOW % 2 == 1 else SOAP_WINDOW + 1
        mean_b = cv2.blur(L, (k, k))
        sq_mean = cv2.blur(L * L, (k, k))
        local_std = np.sqrt(np.maximum(sq_mean - mean_b * mean_b, 0))

        med_std = float(np.median(local_std)) + 1e-6
        ratio = local_std / med_std
        deficit = np.clip((1.2 - ratio) / 0.6, 0.0, 1.0)
        deficit = cv2.GaussianBlur(deficit, (0, 0),
                                    sigmaX=SOAP_WINDOW / 3.0)
        deficit = np.where(deficit < 0.20, 0.0, deficit)

        # Отсеиваем «пустые» зоны — там где local_std буквально ноль.
        # Это не мыльность, а отсутствие текстуры (нужен inpaint, не unsharp).
        empty_zone = local_std < 0.5
        deficit = np.where(empty_zone, 0.0, deficit)

        soapy_pct = float((deficit > 0.3).mean() * 100.0)

        metrics = {
            "profile": profile_key,
            "mean_L": mean_l,
            "std_L": std_l,
            "p1_L": p1,
            "p99_L": p99,
            "mean_S": mean_s,
            "r_mean": r_mean,
            "g_mean": g_mean,
            "b_mean": b_mean,
            "color_spread": color_spread,
            "soapy_pct": soapy_pct,
        }

        issues = []

        # ── 1. Мыльность ──
        if soapy_pct >= SOAP_WARN_PCT:
            issues.append(Issue(
                code="soapy",
                severity=Severity.WARN if soapy_pct < 40 else Severity.FAIL,
                title_key="albedo.soapy.title",
                detail_key="albedo.soapy.detail",
                fix_id="remove_soap",
                fix_label_key="fix.remove_soap",
                metrics={"pct": soapy_pct, "soapy_pct": soapy_pct},
            ))

        # ── 2. Недосвет ──
        dark_threshold = max(0, dark_t - DARK_OFFSET)
        if p1 < dark_threshold:
            issues.append(Issue(
                code="dark",
                severity=Severity.WARN,
                title_key="albedo.dark.title",
                detail_key="albedo.dark.detail",
                fix_id="auto_correct",
                fix_label_key="fix.auto_correct",
                metrics={"p1": p1, "thr": dark_threshold,
                         "profile": profile_key},
            ))

        # ── 3. Пересвет ──
        light_threshold = min(255, light_t + LIGHT_OFFSET)
        if p99 > light_threshold:
            issues.append(Issue(
                code="light",
                severity=Severity.WARN,
                title_key="albedo.light.title",
                detail_key="albedo.light.detail",
                fix_id="auto_correct",
                fix_label_key="fix.auto_correct",
                metrics={"p99": p99, "thr": light_threshold,
                         "profile": profile_key},
            ))

        # ── 4. Плоский / жёсткий контраст ──
        if std_l < FLAT_STD_THRESH:
            issues.append(Issue(
                code="flat_contrast",
                severity=Severity.WARN,
                title_key="albedo.flat_contrast.title",
                detail_key="albedo.flat_contrast.detail",
                fix_id="clahe_only",
                fix_label_key="fix.clahe_only",
                metrics={"std": std_l, "std_L": std_l},
            ))
        elif std_l > HARD_STD_THRESH:
            issues.append(Issue(
                code="hard_contrast",
                severity=Severity.WARN,
                title_key="albedo.hard_contrast.title",
                detail_key="albedo.hard_contrast.detail",
                fix_id="decontrast",
                fix_label_key="fix.decontrast",
                metrics={"std": std_l, "std_L": std_l},
            ))

        # ── 5. Насыщенность ──
        if mean_s < FLAT_SAT_THRESH:
            issues.append(Issue(
                code="flat_color",
                severity=Severity.WARN,
                title_key="albedo.flat_color.title",
                detail_key="albedo.flat_color.detail",
                fix_id="saturate_30",
                fix_label_key="fix.saturate_30",
                metrics={"sat": mean_s, "mean_S": mean_s},
            ))
        elif mean_s > OVER_SAT_THRESH:
            issues.append(Issue(
                code="oversaturated",
                severity=Severity.WARN,
                title_key="albedo.oversaturated.title",
                detail_key="albedo.oversaturated.detail",
                fix_id="desaturate_15",
                fix_label_key="fix.desaturate_15",
                metrics={"sat": mean_s, "mean_S": mean_s},
            ))

        # ── 6. Цветовой сдвиг ──
        if color_spread > COLOR_CAST_THRESH:
            issues.append(Issue(
                code="color_cast",
                severity=Severity.WARN,
                title_key="albedo.color_cast.title",
                detail_key="albedo.color_cast.detail",
                fix_id="white_balance",
                fix_label_key="fix.white_balance",
                metrics={"delta": color_spread,
                         "color_spread": color_spread},
            ))

        # ─── Severity ───
        sev = Severity.OK
        for iss in issues:
            if iss.severity == Severity.FAIL:
                sev = Severity.FAIL
                break
            if iss.severity == Severity.WARN:
                sev = Severity.WARN

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
        img = self.to_float01(img).copy()

        if fix_id == "auto_correct":
            return self._fix_auto_correct(img)
        if fix_id == "clahe_only":
            return self._fix_clahe(img, blend=0.5)
        if fix_id == "auto_levels_only":
            return self._fix_auto_levels(img)
        if fix_id == "remove_soap":
            return self._fix_remove_soap(img)
        if fix_id == "saturate_15":
            return self._fix_saturation(img, 1.15)
        if fix_id == "saturate_30":
            return self._fix_saturation(img, 1.30)
        if fix_id == "desaturate_15":
            return self._fix_saturation(img, 0.85)
        if fix_id == "white_balance":
            return self._fix_white_balance(img)
        if fix_id == "decontrast":
            return self._fix_decontrast(img)
        if fix_id == "remove_color_cast":
            return self._fix_remove_color_cast(img)

        raise ValueError(t("err.unknown_fix", fix_id=fix_id))

    # ─── AUTO CORRECT ───

    def _fix_auto_correct(self, img: np.ndarray) -> np.ndarray:
        profile = get_profile(self._profile_key)
        dark_t = profile["dark"]
        light_t = profile["light"]

        lab = cv2.cvtColor(
            np.clip(img * 255, 0, 255).astype(np.uint8),
            cv2.COLOR_RGB2LAB
        )
        L = lab[:, :, 0].astype(np.float32)

        p1 = float(np.percentile(L, 1))
        p99 = float(np.percentile(L, 99))
        std_L = float(np.std(L))

        if std_L < 15:
            clip_limit = 1.5
        elif std_L < 35:
            clip_limit = 2.0
        elif std_L < 55:
            clip_limit = 2.8
        else:
            clip_limit = 3.5

        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
        L_clahe = clahe.apply(L.astype(np.uint8)).astype(np.float32)

        need = 0.0
        if p1 < dark_t - 10:
            need += min(1.0, (dark_t - 10 - p1) / 50.0)
        if p99 > light_t + 10:
            need += min(1.0, (p99 - light_t - 10) / 50.0)
        need = min(1.0, need)

        blend = 0.4 + need * 0.3
        L_new = L_clahe * blend + L * (1.0 - blend)

        hard_dark = max(0, dark_t - 20)
        hard_light = min(255, light_t + 20)

        dark_excess = np.maximum(0, hard_dark - L_new)
        L_new = L_new + dark_excess * 0.6

        light_excess = np.maximum(0, L_new - hard_light)
        L_new = L_new - light_excess * 0.6

        new_range = (float(np.percentile(L_new, 99))
                     - float(np.percentile(L_new, 1)))
        target_range = hard_light - hard_dark

        if new_range < target_range * 0.55:
            np1 = float(np.percentile(L_new, 1))
            np99 = float(np.percentile(L_new, 99))
            if np99 - np1 > 1:
                L_norm = np.clip((L_new - np1) / (np99 - np1), 0, 1)
                L_curved = L_norm * L_norm * (3 - 2 * L_norm)
                L_mixed = 0.3 * L_curved + 0.7 * L_norm
                L_stretched = hard_dark + L_mixed * (hard_light - hard_dark)
                L_new = L_new * 0.7 + L_stretched * 0.3

        lab[:, :, 0] = np.clip(L_new, 0, 255).astype(np.uint8)
        rgb = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * 1.02, 0, 255)
        rgb = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)

        return (rgb.astype(np.float32) / 255.0).astype(np.float32)

    # ─── CLAHE ───

    def _fix_clahe(self, img: np.ndarray, blend: float = 0.5) -> np.ndarray:
        lab = cv2.cvtColor(
            np.clip(img * 255, 0, 255).astype(np.uint8),
            cv2.COLOR_RGB2LAB
        )
        L = lab[:, :, 0].astype(np.float32)
        std_L = float(np.std(L))

        if std_L < 15:
            clip_limit = 1.5
        elif std_L < 35:
            clip_limit = 2.0
        elif std_L < 55:
            clip_limit = 2.8
        else:
            clip_limit = 3.5

        clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8))
        L_clahe = clahe.apply(L.astype(np.uint8)).astype(np.float32)

        L_new = L_clahe * blend + L * (1.0 - blend)
        lab[:, :, 0] = np.clip(L_new, 0, 255).astype(np.uint8)
        rgb = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        return (rgb.astype(np.float32) / 255.0).astype(np.float32)

    # ─── AUTO LEVELS ───

    def _fix_auto_levels(self, img: np.ndarray) -> np.ndarray:
        profile = get_profile(self._profile_key)
        dark_t = profile["dark"]
        light_t = profile["light"]

        lab = cv2.cvtColor(
            np.clip(img * 255, 0, 255).astype(np.uint8),
            cv2.COLOR_RGB2LAB
        )
        L = lab[:, :, 0].astype(np.float32)

        p1 = float(np.percentile(L, 1))
        p99 = float(np.percentile(L, 99))

        hard_dark = max(0, dark_t - 20)
        hard_light = min(255, light_t + 20)

        if p99 - p1 > 1:
            L_norm = np.clip((L - p1) / (p99 - p1), 0, 1)
            L_new = hard_dark + L_norm * (hard_light - hard_dark)
        else:
            L_new = L

        lab[:, :, 0] = np.clip(L_new, 0, 255).astype(np.uint8)
        rgb = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        return (rgb.astype(np.float32) / 255.0).astype(np.float32)

    # ─── REMOVE SOAP ───

    def _fix_remove_soap(self, img: np.ndarray,
                          strength: float = 1.0) -> np.ndarray:
        """
        Комбо-фикс: SCUNet (1 проход) + мягкий multi-scale detail boost.

        Второй проход модели убран — он давал маленький вклад,
        но удваивал время. Оставлен один проход + математика.
        """
        from core.deblur_model import get_nafnet_model, deblur_image
        from core.analyzers.base import emit_progress

        net = get_nafnet_model()
        if net is None:
            return img

        # ─── LAB ───
        rgb_u8 = np.clip(img * 255, 0, 255).astype(np.uint8)
        lab = cv2.cvtColor(rgb_u8, cv2.COLOR_RGB2LAB).astype(np.float32)
        L = lab[:, :, 0]

        # ─── Маска deficit ───
        k = SOAP_WINDOW if SOAP_WINDOW % 2 == 1 else SOAP_WINDOW + 1
        mean_b = cv2.blur(L, (k, k))
        sq_mean = cv2.blur(L * L, (k, k))
        local_std = np.sqrt(np.maximum(sq_mean - mean_b * mean_b, 0))
        med_std = float(np.median(local_std)) + 1e-6

        ratio = local_std / med_std
        deficit = np.clip((1.2 - ratio) / 0.6, 0.0, 1.0)
        deficit = cv2.GaussianBlur(deficit, (0, 0),
                                    sigmaX=SOAP_WINDOW / 3.0)
        deficit = np.where(deficit < 0.15, 0.0, deficit)

        if deficit.max() < 0.05:
            return img

        s = float(np.clip(strength, 0.0, 2.0))

        # ═══════════════════════════════════════════════════
        #  ЕДИНСТВЕННЫЙ ПРОХОД МОДЕЛИ
        # ═══════════════════════════════════════════════════
        emit_progress("Де-блюр...")
        model_out1 = deblur_image(net, img, deficit_mask=None)

        m1 = np.clip(deficit * s, 0.0, 1.0)[:, :, None]
        pass1 = img * (1.0 - m1) + model_out1 * m1
        pass1 = np.clip(pass1, 0.0, 1.0).astype(np.float32)

        emit_progress("Detail boost...")

        # ═══════════════════════════════════════════════════
        #  Мягкий multi-scale detail boost
        # ═══════════════════════════════════════════════════
        lab2 = cv2.cvtColor(
            np.clip(pass1 * 255, 0, 255).astype(np.uint8),
            cv2.COLOR_RGB2LAB,
        ).astype(np.float32)
        L2 = lab2[:, :, 0]

        b1 = cv2.GaussianBlur(L2, (0, 0), sigmaX=8.0)
        b2 = cv2.GaussianBlur(L2, (0, 0), sigmaX=4.0)
        b3 = cv2.GaussianBlur(L2, (0, 0), sigmaX=2.0)

        d2 = b1 - b2
        d3 = b2 - b3
        d4 = L2 - b3

        amp = deficit * s
        d2_new = d2 * (1.0 + 0.8 * amp)
        d3_new = d3 * (1.0 + 1.4 * amp)
        d4_new = d4 * (1.0 + 0.3 * amp)

        L_new = b1 + d2_new + d3_new + d4_new

        local_mean = cv2.GaussianBlur(L_new, (0, 0), sigmaX=3.0)
        excess = L_new - local_mean
        CLIP = 10.0
        soft_excess = CLIP * np.tanh(excess / CLIP)
        L_new = local_mean + soft_excess
        L_new = np.clip(L_new, 0, 255)

        L_u8 = L_new.astype(np.uint8)
        L_clean = cv2.bilateralFilter(
            L_u8, d=5, sigmaColor=10, sigmaSpace=7
        ).astype(np.float32)

        L_final = L2 * (1 - deficit) + L_clean * deficit

        lab2[:, :, 0] = np.clip(L_final, 0, 255)
        lab2 = np.clip(lab2, 0, 255).astype(np.uint8)
        result = cv2.cvtColor(lab2, cv2.COLOR_LAB2RGB)
        return (result.astype(np.float32) / 255.0).astype(np.float32)

    # ─── SATURATION ───

    def _fix_saturation(self, img: np.ndarray,
                         strength: float) -> np.ndarray:
        if abs(strength - 1.0) < 1e-3:
            return img
        rgb = np.clip(img * 255, 0, 255).astype(np.uint8)
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV).astype(np.float32)
        hsv[:, :, 1] = np.clip(hsv[:, :, 1] * strength, 0, 255)
        rgb = cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2RGB)
        return (rgb.astype(np.float32) / 255.0).astype(np.float32)

    # ─── WHITE BALANCE ───

    def _fix_white_balance(self, img: np.ndarray) -> np.ndarray:
        r_mean = float(img[:, :, 0].mean()) + 1e-6
        g_mean = float(img[:, :, 1].mean()) + 1e-6
        b_mean = float(img[:, :, 2].mean()) + 1e-6
        gray = (r_mean + g_mean + b_mean) / 3.0

        out = img.copy()
        out[:, :, 0] *= gray / r_mean
        out[:, :, 1] *= gray / g_mean
        out[:, :, 2] *= gray / b_mean
        return np.clip(out, 0.0, 1.0).astype(np.float32)

    # ─── DECONTRAST ───

    def _fix_decontrast(self, img: np.ndarray,
                         strength: float = 0.6) -> np.ndarray:
        lab = cv2.cvtColor(
            np.clip(img * 255, 0, 255).astype(np.uint8),
            cv2.COLOR_RGB2LAB
        )
        L = lab[:, :, 0].astype(np.float32)
        mean = float(L.mean())
        L_new = mean + (L - mean) * strength
        lab[:, :, 0] = np.clip(L_new, 0, 255).astype(np.uint8)
        rgb = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
        return (rgb.astype(np.float32) / 255.0).astype(np.float32)

    # ─── REMOVE COLOR CAST ───

    def _fix_remove_color_cast(self, img: np.ndarray) -> np.ndarray:
        lab = cv2.cvtColor(
            np.clip(img * 255, 0, 255).astype(np.uint8),
            cv2.COLOR_RGB2LAB
        ).astype(np.float32)
        a = lab[:, :, 1]
        b = lab[:, :, 2]
        a_mean = float(a.mean())
        b_mean = float(b.mean())
        a_new = a - (a_mean - 128.0) * 0.8
        b_new = b - (b_mean - 128.0) * 0.8
        lab[:, :, 1] = np.clip(a_new, 0, 255)
        lab[:, :, 2] = np.clip(b_new, 0, 255)
        rgb = cv2.cvtColor(lab.astype(np.uint8), cv2.COLOR_LAB2RGB)
        return (rgb.astype(np.float32) / 255.0).astype(np.float32)