"""core/analyzers — по одному анализатору на каждый тип карты."""

from core.analyzers.normal import NormalAnalyzer
from core.analyzers.roughness import RoughnessAnalyzer
from core.analyzers.metallic import MetallicAnalyzer
from core.analyzers.ao import AOAnalyzer
from core.analyzers.orm import ORMAnalyzer
from core.analyzers.fallback import FallbackAnalyzer

REGISTRY = {
    "normal":    NormalAnalyzer,
    "roughness": RoughnessAnalyzer,
    "metallic":  MetallicAnalyzer,
    "ao":        AOAnalyzer,
    "orm":       ORMAnalyzer,
    "height":    FallbackAnalyzer,
    "edge":      FallbackAnalyzer,
    "unknown":   FallbackAnalyzer,
}


def get_analyzer(map_type: str):
    """Возвращает инстанс анализатора для типа карты, или None."""
    cls = REGISTRY.get(map_type)
    if cls is None:
        return None

    # FallbackAnalyzer требует явного типа, остальные — нет.
    if cls is FallbackAnalyzer:
        return cls(map_type)
    return cls()