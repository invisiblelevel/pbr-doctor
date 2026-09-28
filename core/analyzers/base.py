"""
core/analyzers/base.py — база для всех анализаторов.

Каждый анализатор:
  1. Получает numpy-массив float32 [H,W,3] в [0..1].
  2. Возвращает Report с метриками и списком Issue.
  3. Умеет применять фиксы по fix_id.

Текст issues хранится в виде ключей локализации (title_key / detail_key /
fix_label_key). Готовые строки получаются через properties title / detail /
fix_label, которые зовут t() с подстановками из metrics.

Фиксы всегда возвращают новый массив (не мутируют вход).
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
import numpy as np

from core.i18n import t


# ═══════════════════════════════════════════════════════════
#  SEVERITY
# ═══════════════════════════════════════════════════════════

class Severity(str, Enum):
    OK   = "ok"
    WARN = "warn"
    FAIL = "fail"


SEVERITY_ORDER = {Severity.OK: 0, Severity.WARN: 1, Severity.FAIL: 2}


# ═══════════════════════════════════════════════════════════
#  ISSUE — одна найденная проблема
# ═══════════════════════════════════════════════════════════

@dataclass
class Issue:
    """
    Одна проблема.

    Тексты — ключами локализации. Подстановки ({std:.3f} и т.п.) берутся
    из metrics. Properties title / detail / fix_label возвращают уже
    переведённую строку на текущем языке.
    """

    code: str
    severity: Severity

    title_key: Optional[str] = None
    detail_key: Optional[str] = None
    fix_label_key: Optional[str] = None
    title_wrap_key: Optional[str] = None

    fix_id: Optional[str] = None
    metrics: dict = field(default_factory=dict)

    # ─── Обратная совместимость: старый код мог передать готовые строки ───
    _title_raw: Optional[str] = None
    _detail_raw: Optional[str] = None
    _fix_label_raw: Optional[str] = None

    def __post_init__(self):
        """
        Если передали старые title= / detail= / fix_label= через kwargs —
        dataclass их не знает, но мы можем их отловить и сохранить.
        Реализовано через properties ниже: тут просто проверяем, что
        хотя бы один ключ или raw есть.
        """
        if self.title_key is None and self._title_raw is None:
            # ничего страшного — просто пустая issue, но лучше предупредить
            pass

    # ─── Properties: отдают готовые строки на текущем языке ───

    @property
    def title(self) -> str:
        base = ""
        if self.title_key:
            base = t(self.title_key, **self.metrics)
        elif self._title_raw:
            base = self._title_raw

        if self.title_wrap_key:
            return t(self.title_wrap_key, text=base)
        return base

    @property
    def detail(self) -> str:
        if self.detail_key:
            return t(self.detail_key, **self.metrics)
        if self._detail_raw:
            return self._detail_raw
        return ""

    @property
    def fix_label(self) -> str:
        if self.fix_label_key:
            return t(self.fix_label_key)
        if self._fix_label_raw:
            return self._fix_label_raw
        return ""

    # ─── Старые имена для совместимости (сеттеры-заглушки) ───
    # Если где-то в проекте ещё остался код вида Issue(title="...") —
    # dataclass упадёт. Эти сеттеры не помогут при конструировании,
    # но если кто-то присваивает issue.title = "..." после создания —
    # сохранят в _title_raw.

    @title.setter
    def title(self, value: str):
        self._title_raw = value

    @detail.setter
    def detail(self, value: str):
        self._detail_raw = value

    @fix_label.setter
    def fix_label(self, value: str):
        self._fix_label_raw = value


# ═══════════════════════════════════════════════════════════
#  REPORT — результат анализа одной карты
# ═══════════════════════════════════════════════════════════

@dataclass
class Report:
    map_type: str
    severity: Severity
    issues: list = field(default_factory=list)
    metrics: dict = field(default_factory=dict)
    preview_before: Optional[np.ndarray] = None
    preview_after: Optional[np.ndarray] = None

    def worst_severity(self) -> Severity:
        if not self.issues:
            return Severity.OK
        return max((i.severity for i in self.issues),
                   key=lambda s: SEVERITY_ORDER[s])

    def has_fixable(self) -> bool:
        return any(i.fix_id for i in self.issues)


# ═══════════════════════════════════════════════════════════
#  BASE ANALYZER
# ═══════════════════════════════════════════════════════════

class BaseAnalyzer:
    """
    Наследники переопределяют:
      MAP_TYPE      — MapType.value
      analyze(img)  -> Report
      fix(img, fix_id) -> np.ndarray  (опционально)
    """

    MAP_TYPE: str = "unknown"

    def analyze(self, img: np.ndarray) -> Report:
        raise NotImplementedError

    def fix(self, img: np.ndarray, fix_id: str) -> np.ndarray:
        raise NotImplementedError(
            t("err.fix_not_implemented", fix_id=fix_id)
        )

    # ─── Утилиты для наследников ───

    @staticmethod
    def to_float01(img: np.ndarray) -> np.ndarray:
        """uint8 [0..255] -> float32 [0..1]; уже float — оставляем.
        NaN/Inf чистим — иначе все расчёты статистики ломаются."""
        if img.dtype == np.uint8:
            arr = img.astype(np.float32) / 255.0
        else:
            arr = img.astype(np.float32)

        if not np.isfinite(arr).all():
            arr = np.nan_to_num(arr, nan=0.0, posinf=1.0, neginf=0.0)
        return arr

    @staticmethod
    def to_uint8(img: np.ndarray) -> np.ndarray:
        """float [0..1] -> uint8 [0..255]."""
        return np.clip(img * 255.0, 0, 255).astype(np.uint8)

    @staticmethod
    def grayscale(img: np.ndarray) -> np.ndarray:
        """Rec.709 яркость из RGB float [0..1]. Возвращает [H,W] float."""
        return (0.2126 * img[:, :, 0]
                + 0.7152 * img[:, :, 1]
                + 0.0722 * img[:, :, 2])
                
# ═══════════════════════════════════════════════════════════
#  ГЛОБАЛЬНЫЙ CALLBACK ДЛЯ ПРОГРЕССА (используется ORM Fix All)
# ═══════════════════════════════════════════════════════════

_PROGRESS_CB = {"fn": None}


def set_progress_callback(fn):
    """Установить callback(text) для промежуточного прогресса."""
    _PROGRESS_CB["fn"] = fn


def emit_progress(text: str):
    """Толкнуть текст в callback, если он установлен."""
    fn = _PROGRESS_CB.get("fn")
    if fn:
        try:
            fn(text)
        except Exception:
            pass