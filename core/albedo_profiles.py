"""
core/albedo_profiles.py — профили текстур для AlbedoAnalyzer.

Профили взяты из Albedolizer. dark/light — пороги L-канала в LAB (0..255).
dark — насколько тёмные зоны могут быть (ниже — «недосвет»).
light — насколько светлые зоны могут быть (выше — «пересвет»).

Авто-детект профиля по имени файла:
  metal_albedo.png     → metal
  brick_diffuse.png    → brick
  wood_basecolor.png   → wood
  ...
Если ничего не нашли — DEFAULT_PROFILE = "stone".

Переводы названий профилей живут в core/i18n.py по ключам:
  "albedo.profile.metal", "albedo.profile.brick", ...
"""

DEFAULT_PROFILE = "stone"

# ═══════════════════════════════════════════════════════════
#  ПРОФИЛИ
# ═══════════════════════════════════════════════════════════

TEXTURE_PROFILES = {
    # METAL
    "metal":          {"dark": 140, "light": 255},
    "rust":           {"dark": 20,  "light": 235},
    "oxidized_metal": {"dark": 30,  "light": 240},
    "patina":         {"dark": 25,  "light": 235},
    "brass":          {"dark": 120, "light": 250},
    "aluminum":       {"dark": 130, "light": 250},
    "copper":         {"dark": 120, "light": 250},
    # NATURE
    "wood":           {"dark": 25,  "light": 240},
    "leaves":         {"dark": 20,  "light": 245},
    "moss":           {"dark": 10,  "light": 230},
    "organic":        {"dark": 15,  "light": 235},
    "grass":          {"dark": 20,  "light": 240},
    "bark":           {"dark": 20,  "light": 230},
    # MINERAL
    "tile":           {"dark": 30,  "light": 245},
    "gravel":         {"dark": 20,  "light": 220},
    "coal":           {"dark": 10,  "light": 150},
    "roof_tiles":     {"dark": 25,  "light": 230},
    "stone":          {"dark": 25,  "light": 235},
    "concrete":       {"dark": 30,  "light": 240},
    "brick":          {"dark": 25,  "light": 235},
    "ground":         {"dark": 20,  "light": 235},
    "asphalt":        {"dark": 15,  "light": 200},
    "marble":         {"dark": 35,  "light": 250},
    "sand":           {"dark": 40,  "light": 245},
    "clay":           {"dark": 30,  "light": 230},
    "granite":        {"dark": 25,  "light": 230},
    "stucco":         {"dark": 40,  "light": 250},
    "gemstone":       {"dark": 30,  "light": 250},
    # SYNTHETIC
    "plastic":        {"dark": 30,  "light": 245},
    "rubber":         {"dark": 20,  "light": 200},
    "glass":          {"dark": 50,  "light": 250},
    "ceramic":        {"dark": 35,  "light": 245},
    "painted_metal":  {"dark": 25,  "light": 240},
    "carbon":         {"dark": 15,  "light": 200},
    "cardboard":      {"dark": 45,  "light": 245},
    # SPECIAL
    "water":          {"dark": 40,  "light": 250},
    "mud":            {"dark": 20,  "light": 220},
    "snow":           {"dark": 80,  "light": 255},
    "ice":            {"dark": 60,  "light": 250},
    # FABRIC
    "cotton":         {"dark": 30,  "light": 245},
    "wool":           {"dark": 25,  "light": 240},
    "silk":           {"dark": 40,  "light": 250},
    "denim":          {"dark": 25,  "light": 200},
    "carpet":         {"dark": 30,  "light": 235},
    "velvet":         {"dark": 20,  "light": 210},
    # FAUNA
    "leather":        {"dark": 25,  "light": 235},
    "fur":            {"dark": 20,  "light": 245},
    "skin":           {"dark": 30,  "light": 240},
    "scales":         {"dark": 25,  "light": 245},
    "bone":           {"dark": 60,  "light": 245},
}


# ═══════════════════════════════════════════════════════════
#  АВТО-ДЕТЕКТ ПО ИМЕНИ ФАЙЛА
# ═══════════════════════════════════════════════════════════

# Порядок важен — более специфичные ключи раньше
# (oxidized_metal раньше metal, painted_metal раньше metal)
_DETECT_ORDER = [
    "oxidized_metal", "painted_metal", "roof_tiles",
    "rust", "patina", "brass", "aluminum", "copper", "metal",
    "leaves", "moss", "organic", "grass", "bark", "wood",
    "gravel", "coal", "tile", "asphalt", "marble", "sand",
    "clay", "granite", "stucco", "gemstone",
    "stone", "concrete", "brick", "ground",
    "rubber", "glass", "ceramic", "carbon", "cardboard",
    "plastic",
    "water", "mud", "snow", "ice",
    "cotton", "wool", "silk", "denim", "carpet", "velvet",
    "leather", "fur", "scales", "bone", "skin",
]


def detect_profile(filename: str) -> str:
    """
    Авто-детект профиля по имени файла.
    Возвращает ключ профиля или DEFAULT_PROFILE если не нашёл.
    """
    import os
    stem = os.path.splitext(os.path.basename(filename))[0].lower()

    for key in _DETECT_ORDER:
        if key in stem:
            return key

    return DEFAULT_PROFILE


def get_profile(key: str) -> dict:
    """Возвращает профиль по ключу. Если нет — дефолтный."""
    return TEXTURE_PROFILES.get(key, TEXTURE_PROFILES[DEFAULT_PROFILE])


def sorted_profile_keys() -> list:
    """
    Возвращает список ключей профилей в алфавитном порядке
    ОТОБРАЖАЕМЫХ имён (на текущем языке).

    Используется для дропдауна выбора профиля в UI.
    """
    from core.i18n import t

    keys = list(TEXTURE_PROFILES.keys())

    def _display_name(key: str) -> str:
        label = t(f"albedo.profile.{key}")
        # Если ключа нет в i18n — вернётся сам ключ, тогда сортируем по нему
        return label.lower()

    keys.sort(key=_display_name)
    return keys