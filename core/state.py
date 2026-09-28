"""
core/state.py — состояние PBR Doctor.

Единый dict S (как в Albedolizer), в котором живёт всё:
  - загруженные карты (список, без коллизий типов)
  - отчёты анализаторов
  - история фиксов (для Undo)
  - UI-контролы (лог, статистика, прогресс)

MAP_LABELS хранит КЛЮЧИ локализации (map.normal и т.п.).
Готовую строку получать через map_label(map_type).
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Optional
import numpy as np

from core.i18n import t, get_lang


# ═══════════════════════════════════════════════════════════
#  ТИПЫ КАРТ
# ═══════════════════════════════════════════════════════════

class MapType(str, Enum):
    ALBEDO    = "albedo"
    NORMAL    = "normal"
    ROUGHNESS = "roughness"
    METALLIC  = "metallic"
    AO        = "ao"
    ORM       = "orm"
    HEIGHT    = "height"
    EDGE      = "edge"
    UNKNOWN   = "unknown"


# Ключи локализации для типов карт.
# Готовую строку — через map_label().
MAP_LABELS = {
    MapType.ALBEDO:    "map.albedo",
    MapType.NORMAL:    "map.normal",
    MapType.ROUGHNESS: "map.roughness",
    MapType.METALLIC:  "map.metallic",
    MapType.AO:        "map.ao",
    MapType.ORM:       "map.orm",
    MapType.HEIGHT:    "map.height",
    MapType.EDGE:      "map.edge",
    MapType.UNKNOWN:   "map.unknown",
}


def map_label(mt) -> str:
    """
    Переведённое название типа карты.

    Принимает MapType или строку ("normal"). Если ключа нет — вернёт
    сам ключ (t() подстрахует) или строковое значение.
    """
    if isinstance(mt, MapType):
        key = MAP_LABELS.get(mt)
        if key is None:
            return mt.value
        return t(key)

    # Строкой пришло
    s = str(mt)
    for k, v in MAP_LABELS.items():
        if k.value == s:
            return t(v)
    return s


# ═══════════════════════════════════════════════════════════
#  ЗАПИСЬ О КАРТЕ
# ═══════════════════════════════════════════════════════════

@dataclass
class MapEntry:
    """Одна загруженная карта."""
    path: str                            # путь к файлу
    filename: str                        # имя файла
    map_type: MapType                    # определённый тип
    confidence: float                    # уверенность детекта 0..1
    detected_by: str                     # "name" | "content" | "manual"
    original: np.ndarray                 # float32 [H,W,3] в [0..1]
    working: np.ndarray                  # текущая версия
    report: Optional[object] = None      # Report после анализа
    size_bytes: int = 0                  # размер файла
    had_fixes: bool = False              # были ли фиксы
    fix_history: list = field(default_factory=list)


def new_state() -> dict:
    """Создаёт пустое состояние."""
    return {
        # ─── карты ───
        "maps": [],              # list[MapEntry]
        "selected_idx": None,    # int | None — индекс выбранной карты

        # ─── лог ───
        "log_lines": [],
        "log_column_bottom": None,
        "log_collapsed_preview": None,

        # ─── статистика ───
        "stats_lines": [],
        "stats_column": None,

        # ─── прогресс ───
        "progress_bar": None,
        "progress_text": None,

        # ─── тема ───
        "theme_mode": "dark",

        # ─── язык ───
        # Заполняется в main.py через get_system_lang().
        # None означает "ещё не установлен, i18n сам определит".
        "lang": None,

        # ─── ссылка на правую панель ───
        "report_panel": None,
    }