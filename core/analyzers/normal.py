"""
core/analyzers/normal.py — анализ и ремонт Normal Map.

Что проверяем:
  1. Это вообще нормаль? (B-канал доминирует? средний вектор похож на (0,0,1)?)
  2. Длина векторов ~ 1.0? (иначе карта битая)
  3. Запечён ли свет? (средний вектор сдвинут от (0,0,1) > порога)
  4. B-канал не вырожден? (плоский, тёмный — "сломанный Z")

Что фиксим:
  - unbake_light:   поворот средней нормали к (0,0,1)
  - restore_b:      B = sqrt(1 - R^2 - G^2)

Тексты issues — ключами локализации (title_key / detail_key / fix_label_key).
"""

import numpy as np

from core.analyzers.base import (
    BaseAnalyzer, Report, Issue, Severity,
)
from core.state import MapType
from core.i18n import t


# ═══════════════════════════════════════════════════════════
#  ПОРОГИ
# ═══════════════════════════════════════════════════════════

ANGLE_WARN_DEG   = 5.0
ANGLE_FAIL_DEG   = 15.0
LENGTH_WARN_PCT  = 1.0
LENGTH_FAIL_PCT  = 5.0
B_DARK_THRESHOLD = 0.5


# ═══════════════════════════════════════════════════════════
#  МАТЕМАТИКА
# ═══════════════════════════════════════════════════════════

def _decode_normal(img: np.ndarray) -> np.ndarray:
    """
    RGB [0..1] -> XYZ [-1..1]. X=R*2-1, Y=G*2-1, Z=B*2-1.
    Возвращает float32 [H,W,3].
    """
    return img * 2.0 - 1.0


def _mean_vector(n_xyz: np.ndarray) -> np.ndarray:
    """Средний вектор нормали по всей карте."""
    return n_xyz.reshape(-1, 3).mean(axis=0)


def _angle_to_up(mean_vec: np.ndarray) -> float:
    """Угол между средним вектором и (0,0,1) в градусах."""
    v = mean_vec / (np.linalg.norm(mean_vec) + 1e-8)
    up = np.array([0.0, 0.0, 1.0])
    cos = float(np.clip(np.dot(v, up), -1.0, 1.0))
    return float(np.degrees(np.arccos(cos)))


def _vector_lengths(n_xyz: np.ndarray) -> np.ndarray:
    """[H,W] длины векторов."""
    return np.linalg.norm(n_xyz, axis=2)


def _rotation_matrix_to_up(v: np.ndarray) -> np.ndarray:
    """
    Матрица поворота, переводящая v в (0,0,1). Формула Родрига.
    """
    v = v / (np.linalg.norm(v) + 1e-8)
    up = np.array([0.0, 0.0, 1.0])

    axis = np.cross(v, up)
    sin_a = np.linalg.norm(axis)
    cos_a = float(np.clip(np.dot(v, up), -1.0, 1.0))

    if sin_a < 1e-8:
        if cos_a > 0:
            return np.eye(3, dtype=np.float32)
        return np.diag([1.0, -1.0, -1.0]).astype(np.float32)

    axis = axis / sin_a
    K = np.array([
        [0,           -axis[2],    axis[1]],
        [axis[2],      0,         -axis[0]],
        [-axis[1],     axis[0],    0],
    ], dtype=np.float32)

    R = (np.eye(3, dtype=np.float32)
         + sin_a * K
         + (1 - cos_a) * (K @ K))
    return R.astype(np.float32)


# ═══════════════════════════════════════════════════════════
#  АНАЛИЗАТОР
# ═══════════════════════════════════════════════════════════

class NormalAnalyzer(BaseAnalyzer):

    MAP_TYPE = MapType.NORMAL.value

    def analyze(self, img: np.ndarray) -> Report:
        img = self.to_float01(img)
        n_xyz = _decode_normal(img)

        mean_vec = _mean_vector(n_xyz)
        angle = _angle_to_up(mean_vec)
        lengths = _vector_lengths(n_xyz)

        mean_len = float(lengths.mean())
        std_len  = float(lengths.std())

        bad_mask = (lengths < 0.9) | (lengths > 1.1)
        bad_pct  = float(bad_mask.mean() * 100.0)

        b_mean = float(img[:, :, 2].mean())
        b_std  = float(img[:, :, 2].std())

        r_std = float(img[:, :, 0].std())
        g_std = float(img[:, :, 1].std())
        rg_alive = (r_std > 0.02) or (g_std > 0.02)

        metrics = {
            "mean_vector":    mean_vec.tolist(),
            "angle":          angle,
            "mean_length":    mean_len,
            "std_length":     std_len,
            "bad_length_pct": bad_pct,
            "b_mean":         b_mean,
            "b_std":          b_std,
            "r_std":          r_std,
            "g_std":          g_std,
            # алиасы для шаблонов в i18n (которые используют {angle},
            # {bad_pct}, {mean_len}, {std_len})
            "angle_deg":      angle,
            "bad_pct":        bad_pct,
            "mean_len":       mean_len,
            "std_len":        std_len,
        }

        issues = []

        # ── 1. Это вообще нормаль? ──
        if b_mean < B_DARK_THRESHOLD and b_std < 0.05 and not rg_alive:
            issues.append(Issue(
                code="not_a_normal",
                severity=Severity.FAIL,
                title_key="normal.not_a_normal.title",
                detail_key="normal.not_a_normal.detail",
                fix_id=None,
                metrics={
                    "b_mean": b_mean,
                    "b_std":  b_std,
                    "r_std":  r_std,
                    "g_std":  g_std,
                },
            ))
            return Report(
                map_type=self.MAP_TYPE,
                severity=Severity.FAIL,
                issues=issues,
                metrics=metrics,
            )

        # ── 2. Битый B при живых R/G ──
        if rg_alive and mean_len < 0.85:
            issues.append(Issue(
                code="broken_b_channel",
                severity=Severity.FAIL,
                title_key="normal.broken_b.title",
                detail_key="normal.broken_b.detail",
                fix_id="restore_b",
                fix_label_key="fix.restore_b",
                metrics={
                    "mean_len": mean_len,
                    "b_mean":   b_mean,
                    "b_std":    b_std,
                },
            ))

        # ── 3. Запечённый свет ──
        if mean_len >= 0.85 and angle >= ANGLE_FAIL_DEG:
            issues.append(Issue(
                code="baked_light",
                severity=Severity.FAIL,
                title_key="normal.baked.title",
                detail_key="normal.baked.detail",
                fix_id="unbake_light",
                fix_label_key="fix.unbake_light",
                metrics={
                    "angle":       angle,
                    "mean_vector": mean_vec.tolist(),
                },
            ))
        elif mean_len >= 0.85 and angle >= ANGLE_WARN_DEG:
            issues.append(Issue(
                code="baked_light_mild",
                severity=Severity.WARN,
                title_key="normal.baked_mild.title",
                detail_key="normal.baked_mild.detail",
                fix_id="unbake_light",
                fix_label_key="fix.align_normal",
                metrics={"angle": angle},
            ))

        # ── 4. Длины векторов ──
        if bad_pct >= LENGTH_FAIL_PCT:
            issues.append(Issue(
                code="bad_vector_length",
                severity=Severity.FAIL,
                title_key="normal.bad_len.title",
                detail_key="normal.bad_len.detail",
                fix_id="restore_b",
                fix_label_key="fix.restore_b",
                metrics={
                    "bad_pct":   bad_pct,
                    "mean_len":  mean_len,
                    "std_len":   std_len,
                },
            ))
        elif bad_pct >= LENGTH_WARN_PCT:
            issues.append(Issue(
                code="bad_vector_length_mild",
                severity=Severity.WARN,
                title_key="normal.bad_len_mild.title",
                detail_key="normal.bad_len_mild.detail",
                fix_id="restore_b",
                fix_label_key="fix.restore_b",
                metrics={"bad_pct": bad_pct},
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
        if fix_id == "unbake_light":
            return self._fix_unbake_light(img)
        if fix_id == "restore_b":
            return self._fix_restore_b(img)
        raise ValueError(t("err.unknown_fix", fix_id=fix_id))

    def _fix_unbake_light(self, img: np.ndarray) -> np.ndarray:
        """Поворот всех нормалей так, чтобы средний вектор стал (0,0,1)."""
        n_xyz = _decode_normal(img)
        mean_vec = _mean_vector(n_xyz)
        R = _rotation_matrix_to_up(mean_vec)

        flat = n_xyz.reshape(-1, 3)
        rotated = flat @ R.T
        rotated = rotated.reshape(n_xyz.shape)

        out = (rotated + 1.0) * 0.5
        return np.clip(out, 0.0, 1.0).astype(np.float32)

    def _fix_restore_b(self, img: np.ndarray) -> np.ndarray:
        """B = sqrt(1 - X^2 - Y^2), X=R*2-1, Y=G*2-1."""
        out = img.copy()
        x = out[:, :, 0] * 2.0 - 1.0
        y = out[:, :, 1] * 2.0 - 1.0
        z_sq = 1.0 - x * x - y * y
        z = np.sqrt(np.clip(z_sq, 0.0, 1.0))
        out[:, :, 2] = (z + 1.0) * 0.5
        return np.clip(out, 0.0, 1.0).astype(np.float32)