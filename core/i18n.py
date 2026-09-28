"""
core/i18n.py — локализация PBR Doctor.

Три языка: ru / en / zh (упрощённый, zh-Hans).

Ключи плоские, точки как разделители, префикс = модуль:
    "map.normal"              — название типа карты
    "fix.normalize_range"     — подпись кнопки фикса
    "ao.dead.title"           — заголовок issue
    "ao.dead.detail"          — детали issue (с {подстановками})
    "tab_analyze.btn_add"     — UI вкладки Analyze
    "verdict.normal.baked"    — вердикт в правой панели

t() читает S["lang"] если не передан явно.
Если ключа нет — fallback на EN, потом на сам ключ.
"""

from __future__ import annotations

import locale
import os
import sys


# ═══════════════════════════════════════════════════════════
#  ЯЗЫКИ
# ═══════════════════════════════════════════════════════════

SUPPORTED = ("ru", "en", "zh")
DEFAULT_LANG = "en"

# Глобальный «текущий язык». Устанавливается в main.py,
# но t() умеет работать и без S — просто берёт DEFAULT_LANG.
_CURRENT = {"lang": None}


def set_lang(lang: str):
    """Установить текущий язык. 'ru' | 'en' | 'zh'."""
    if lang not in SUPPORTED:
        lang = DEFAULT_LANG
    _CURRENT["lang"] = lang


def get_lang() -> str:
    """Текущий язык. Если не установлен — определяем по системе."""
    if _CURRENT["lang"] is None:
        _CURRENT["lang"] = get_system_lang()
    return _CURRENT["lang"]


def get_system_lang() -> str:
    """
    Авто-детект языка системы.
    ru*  → ru
    en*  → en
    zh*  → zh
    иначе → en
    """
    candidates = []
    try:
        loc = locale.getlocale()[0] or ""
        candidates.append(loc.lower())
    except Exception:
        pass
    for env in ("LANG", "LC_ALL", "LC_MESSAGES", "LANGUAGE"):
        v = os.environ.get(env)
        if v:
            candidates.append(v.lower())

    # Windows-специфика
    if sys.platform == "win32":
        try:
            import ctypes
            windll = ctypes.windll.kernel32
            lang_id = windll.GetUserDefaultUILanguage()
            # 0x0419 = ru-RU, 0x0409 = en-US, 0x0804 = zh-CN (Hans)
            primary = lang_id & 0xFF
            if primary == 0x19:
                return "ru"
            if primary == 0x04:
                # 0x04 — китайский; суб-язык: 0x01=Hans, 0x02=Hant.
                # 0x0804 = zh-CN → Hans. 0x0404 = zh-TW → Hant (мы всё равно даём Hans).
                return "zh"
        except Exception:
            pass

    for c in candidates:
        if c.startswith("ru"):
            return "ru"
        if c.startswith("en"):
            return "en"
        if c.startswith("zh"):
            return "zh"

    return DEFAULT_LANG


# ═══════════════════════════════════════════════════════════
#  t() — перевод
# ═══════════════════════════════════════════════════════════

def t(key: str, lang: str = None, **kw) -> str:
    """
    Перевод по ключу. Поддерживает .format(**kw).

    Если ключа нет в текущем языке — fallback на EN.
    Если и там нет — вернёт сам ключ (чтобы не падало).
    """
    if lang is None:
        lang = get_lang()
    if lang not in TEXTS:
        lang = DEFAULT_LANG

    s = TEXTS[lang].get(key)
    if s is None:
        s = TEXTS[DEFAULT_LANG].get(key)
    if s is None:
        return key

    if kw:
        try:
            return s.format(**kw)
        except (KeyError, IndexError, ValueError):
            # Шаблон кривой или не хватает подстановок — отдаём как есть
            return s
    return s


# ═══════════════════════════════════════════════════════════
#  ТЕКСТЫ
# ═══════════════════════════════════════════════════════════

TEXTS = {

    # ═══════════════════════════════════════════════════════
    #  РУССКИЙ
    # ═══════════════════════════════════════════════════════
    "ru": {

        # ─── Приложение / хедер ───
        "app.title":       "PBR Doctor",
        "app.subtitle":    "Диагностика и ремонт PBR-карт",
        "app.tagline":     "Анализ и ремонт PBR-карт",
        "app.log":         "Лог",
        "app.info":        "Инфо",
        "app.lang":        "Язык",

        # ─── Стартовые сообщения в логе ───
        "log.ready":       "PBR Doctor 1.0.0 готов к работе",
        "log.hint_add":    "Нажми Add files, чтобы загрузить карты",

        # ─── Типы карт ───
        "map.albedo":      "Albedo / BaseColor",
        "map.normal":      "Normal",
        "map.roughness":   "Roughness",
        "map.metallic":    "Metallic",
        "map.ao":          "Ambient Occlusion",
        "map.orm":         "ORM (R=AO G=Rough B=Metal)",
        "map.height":      "Height / Displacement",
        "map.edge":        "Edge / Outline",
        "map.unknown":     "Unknown",

        # ─── Как определён тип ───
        "detected.name":         "по имени",
        "detected.content":      "по содержимому",
        "detected.name+content": "имя + содержимое",
        "detected.fallback":     "не определено",
        "detected.manual":       "вручную",

        # ─── Severity ───
        "sev.ok":   "OK",
        "sev.warn": "Warning",
        "sev.fail": "Fail",

        # ─── Подписи кнопок фиксов (общие) ───
        "fix.to_grayscale":    "Сделать grayscale",
        "fix.normalize_range": "Растянуть диапазон",
        "fix.compress":        "Сгладить",
        "fix.invert":          "Инвертировать",
        "fix.binarize_otsu":   "Бинаризовать (Otsu)",
        "fix.binarize_hard":   "Бинаризовать (порог 0.5)",
        "fix.restore_b":       "Восстановить B-канал",
        "fix.unbake_light":    "Вычесть запечённый свет",
        "fix.align_normal":    "Выровнять среднюю нормаль",
        "fix.fix_all_orm":     "Починить всё (ORM)",
        "fix.generic":         "Починить",

        # ─── Служебные ошибки ───
        "err.unknown_fix":        "Неизвестный фикс: {fix_id}",
        "err.fix_not_implemented":"Фикс '{fix_id}' не реализован",
        "err.open_file":          "Не удалось открыть файл: {path}",
        "err.open_reason":        "Причина: {reason}",
        "err.open_hint":          "Проверь: длину пути (>260 символов?), права доступа, свободное место на диске, целостность файла.",
        "err.seamless_mode":      "Неизвестный режим seamless: {mode}",
        "err.orm_bad_fix_id":     "Неверный fix_id для ORM: {fix_id}",
        "err.orm_forbidden_fix":  "Фикс '{op}' запрещён для ORM — он ломает каналы.",
        "err.orm_unknown_channel":"Неизвестный канал: {channel}",

        # ═══════════════════════════════════════════════════
        #  NORMAL
        # ═══════════════════════════════════════════════════
        "normal.not_a_normal.title":  "Это не похоже на normal map",
        "normal.not_a_normal.detail": (
            "B-канал в среднем {b_mean:.2f} (должен быть >0.5), "
            "std={b_std:.3f}. R/G тоже почти не варьируются "
            "(r_std={r_std:.3f}, g_std={g_std:.3f}). "
            "Похоже на grayscale-карту или albedo. "
            "Проверь, что загружен правильный файл."
        ),

        "normal.broken_b.title":  "B-канал вырожден (плоский)",
        "normal.broken_b.detail": (
            "Средняя длина вектора {mean_len:.3f} (должна быть ≈1.0). "
            "B-канал: mean={b_mean:.3f}, std={b_std:.3f}. "
            "Скорее всего Z потерян при генерации. "
            "Восстановим B из R и G: B = sqrt(1 - X² - Y²)."
        ),

        "normal.baked.title":  "Запечён свет (сдвиг {angle:.1f}°)",
        "normal.baked.detail": (
            "Средний вектор нормали отклонён от (0,0,1) на {angle:.1f}°. "
            "Это значит, что в карту запечён направленный свет — "
            "рендер будет кривым. Можно вычесть поворотом."
        ),

        "normal.baked_mild.title":  "Небольшой сдвиг средней нормали ({angle:.1f}°)",
        "normal.baked_mild.detail": (
            "Средний вектор отклонён на {angle:.1f}°. "
            "Может быть нормой для рельефных поверхностей, "
            "но если это плоский тайл — стоит проверить."
        ),

        "normal.bad_len.title":  "Битые длины векторов ({bad_pct:.1f}% пикселей)",
        "normal.bad_len.detail": (
            "{bad_pct:.1f}% пикселей имеют длину вне [0.9, 1.1]. "
            "Средняя длина {mean_len:.3f}, std {std_len:.3f}. "
            "Карта повреждена при генерации или сжатии. "
            "Восстановим B-канал из R и G."
        ),

        "normal.bad_len_mild.title":  "Лёгкие отклонения длин ({bad_pct:.1f}%)",
        "normal.bad_len_mild.detail": (
            "{bad_pct:.1f}% пикселей вне [0.9, 1.1]. "
            "Обычно нормально для сжатых PNG, но проверь."
        ),

        # ═══════════════════════════════════════════════════
        #  ROUGHNESS
        # ═══════════════════════════════════════════════════
        "rough.not_grayscale.title":  "Roughness не grayscale",
        "rough.not_grayscale.detail": (
            "Каналы R/G/B различаются (std={channel_std:.3f}). "
            "Roughness должна быть одноканальной. "
            "Скорее всего генератор сунул в неё цвет."
        ),

        "rough.dead.title":  "Мёртвая карта (std={std:.3f})",
        "rough.dead.detail": (
            "Разброс значений почти нулевой — вся карта "
            "в диапазоне ~[{p1:.2f}, {p99:.2f}] вокруг {mean:.2f}. "
            "{mid_pct:.1f}% пикселей в серой зоне. "
            "Рендер будет плоским. Нужна нормализация или замена карты."
        ),

        "rough.low_var.title":  "Мало вариаций (std={std:.3f})",
        "rough.low_var.detail": (
            "Разброс ниже нормы. Если сцена шершавая равномерно — ок, "
            "иначе стоит подтянуть."
        ),

        "rough.narrow.title":  "Пережатый диапазон (span={span:.2f})",
        "rough.narrow.detail": (
            "Значения занимают только [{p1:.2f}, {p99:.2f}] из [0, 1]. "
            "Рендер теряет контраст шероховатости."
        ),

        "rough.noisy.title":  "Слишком шумная (std={std:.3f})",
        "rough.noisy.detail": (
            "Разброс зашкаливает. Похоже на несглаженный шум "
            "от AI-генерации. Рендер будет звенеть."
        ),

        # ═══════════════════════════════════════════════════
        #  METALLIC
        # ═══════════════════════════════════════════════════
        "metal.not_grayscale.title":  "Metallic не grayscale",
        "metal.not_grayscale.detail": (
            "Каналы R/G/B различаются (std={channel_std:.3f}). "
            "Metallic должна быть одноканальной. "
            "Скорее всего генератор сунул туда цвет."
        ),

        "metal.muddy.title":  "Градиенты в серой зоне ({muddy_pct:.1f}%)",
        "metal.muddy.detail": (
            "{muddy_pct:.1f}% пикселей в диапазоне {low}..{high}. "
            "Металличность должна быть бинарной (0 или 1). "
            "Рендер будет кривым — непонятно, где металл, где диэлектрик."
        ),

        "metal.muddy_mild.title":  "Немного градиентов ({muddy_pct:.1f}%)",
        "metal.muddy_mild.detail": (
            "{muddy_pct:.1f}% пикселей в серой зоне. "
            "Если это грань металл/диэлектрик — может быть нормой "
            "(антиалиасинг), иначе стоит бинаризовать."
        ),

        "metal.all_zero.title":  "Нет металла (всё в 0)",
        "metal.all_zero.detail": (
            "{zero_pct:.1f}% пикселей = 0. Вся карта — диэлектрик. "
            "Если материал не должен содержать металл — это норм. "
            "Если должен — генератор не справился."
        ),

        "metal.all_one.title":  "Всё металл (всё в 1)",
        "metal.all_one.detail": (
            "{one_pct:.1f}% пикселей = 1. Вся модель металлическая. "
            "Если так и задумано — ок, но чаще это ошибка генератора."
        ),

        # ═══════════════════════════════════════════════════
        #  AO
        # ═══════════════════════════════════════════════════
        "ao.not_grayscale.title":  "AO не grayscale",
        "ao.not_grayscale.detail": (
            "Каналы R/G/B различаются (std={channel_std:.3f}). "
            "AO должна быть одноканальной. "
            "Скорее всего генератор сунул в неё цвет от альбедо."
        ),

        "ao.dead.title":  "Мёртвая карта (std={std:.3f})",
        "ao.dead.detail": (
            "Разброс почти нулевой — вся карта в узком диапазоне "
            "вокруг {mean:.2f}. AO бесполезно. "
            "Возможно, генератор просто залил карту серым."
        ),

        "ao.low_var.title":  "Мало вариаций (std={std:.3f})",
        "ao.low_var.detail": (
            "Разброс ниже нормы. Если геометрия плоская — ок, "
            "иначе стоит подтянуть контраст."
        ),

        "ao.too_dark.title":  "AO слишком тёмное (mean={mean:.2f})",
        "ao.too_dark.detail": (
            "Средняя яркость {mean:.2f} — почти всё затенено "
            "({dark_pct:.1f}% пикселей тёмные). "
            "Скорее всего перепутана полярность (белое = тень, чёрное = свет) "
            "или генератор перестарался с тенью."
        ),

        "ao.too_light.title":  "AO почти невидимо (mean={mean:.2f})",
        "ao.too_light.detail": (
            "Средняя яркость {mean:.2f} — почти нет теней. "
            "Если сцена открытая — ок, но обычно AO должно "
            "хоть немного затенять щели."
        ),

        "ao.narrow.title":  "Пережатый диапазон (span={span:.2f})",
        "ao.narrow.detail": (
            "Значения занимают только [{p1:.2f}, {p99:.2f}] из [0, 1]. "
            "Контраст AO слабый."
        ),

        # ═══════════════════════════════════════════════════
        #  ORM
        # ═══════════════════════════════════════════════════
        "orm.bad_shape.title":  "[ORM] Карта не RGB",
        "orm.bad_shape.detail": "ORM должна быть RGB-картой с тремя каналами.",

        "orm.grayscale.title":  "[ORM] Карта grayscale",
        "orm.grayscale.detail": (
            "Все три канала одинаковы. Это не ORM — "
            "проверь, не перепутан ли файл."
        ),

        "orm.metal_muddy.title":  "[B] Metallic: карта не бинарная",
        "orm.metal_muddy.detail": (
            "{mid_pct:.0f}% пикселей в серой зоне. "
            "Для металла ожидается 0 или 1."
        ),

        "orm.fix_all.title":  "[ORM] Починить всё",
        "orm.fix_all.detail": (
            "Применить лучшие фиксы ко всем каналам, "
            "где найдены проблемы."
        ),

        "orm.channel.R": "AO",
        "orm.channel.G": "Roughness",
        "orm.channel.B": "Metallic",

        "orm.wrap.R": "[R] AO: {text}",
        "orm.wrap.G": "[G] Roughness: {text}",
        "orm.wrap.B": "[B] Metallic: {text}",

        # ═══════════════════════════════════════════════════
        #  FALLBACK (height / edge / unknown)
        # ═══════════════════════════════════════════════════
        "fb.bad_shape.title":  "{label}: карта не RGB",
        "fb.bad_shape.detail": "Ожидается RGB-массив [H,W,3].",

        "fb.unknown.title":  "Тип карты не определён",
        "fb.unknown.detail": (
            "Авто-детект не смог опознать карту. Она {kind}. "
            "Проверь тип вручную в дропдауне слева — "
            "от этого зависит, какие проверки применять."
        ),
        "fb.unknown.kind_gray":  "похожа на grayscale-карту",
        "fb.unknown.kind_color": "похожа на цветную карту (возможно, albedo)",

        "fb.dead_unknown.title":  "Карта почти не варьируется",
        "fb.dead_unknown.detail": (
            "std {std:.3f} — разброс ниже нормы. "
            "Возможно, карта пустая или сжата в точку."
        ),

        "fb.not_grayscale.title":  "{label} не grayscale",
        "fb.not_grayscale.detail": (
            "Каналы R/G/B различаются (std={channel_std:.3f}). "
            "{label}-карта должна быть одноканальной."
        ),

        "fb.dead.title":  "{label}: мёртвая карта (std={std:.3f})",
        "fb.dead.detail": (
            "Разброс почти нулевой — вся карта в узком диапазоне "
            "вокруг {mean:.2f}. Рендер будет плоским."
        ),

        "fb.low_var.title":  "{label}: мало вариаций (std={std:.3f})",
        "fb.low_var.detail": (
            "Разброс ниже нормы. Если так и задумано — ок, "
            "иначе стоит растянуть."
        ),

        "fb.narrow.title":  "{label}: пережатый диапазон (span={span:.2f})",
        "fb.narrow.detail": (
            "Значения занимают только [{p1:.2f}, {p99:.2f}] из [0, 1]. "
            "Контраст слабый."
        ),

        "fb.too_dark.title":  "{label}: слишком тёмная (mean={mean:.2f})",
        "fb.too_dark.detail": "Средняя яркость {mean:.2f} — почти всё чёрное.",

        "fb.too_light.title":  "{label}: слишком светлая (mean={mean:.2f})",
        "fb.too_light.detail": "Средняя яркость {mean:.2f} — почти всё белое.",

        "fb.noisy.title":  "{label}: слишком шумная (std={std:.3f})",
        "fb.noisy.detail": (
            "Разброс зашкаливает. Похоже на несглаженный шум "
            "от AI-генерации."
        ),

        "fb.edge_not_binary.title":  "Edge не бинарный ({muddy_pct:.1f}% в серой зоне)",
        "fb.edge_not_binary.detail": (
            "{muddy_pct:.1f}% пикселей в диапазоне {low}..{high}. "
            "Edge-карты обычно 0 или 1. Размытые края могут "
            "выглядеть как грязь при рендере."
        ),

        "fb.label.height":  "Height",
        "fb.label.edge":    "Edge",
        "fb.label.unknown": "Unknown",

        # ═══════════════════════════════════════════════════
        #  ВКЛАДКА ANALYZE
        # ═══════════════════════════════════════════════════
        "tab_analyze.title":     "Анализ",
        "tab_analyze.btn_add":   "Добавить файлы",
        "tab_analyze.btn_analyze":"Анализировать все",
        "tab_analyze.btn_save":  "Сохранить исправленные",
        "tab_analyze.btn_clear": "Очистить",

        "tab_analyze.empty.title": "Нажми «Добавить файлы», чтобы загрузить карты",
        "tab_analyze.empty.hint":  "Normal / Roughness / Metallic / AO / ORM / Albedo",

        "tab_analyze.col.type":   "Тип",
        "tab_analyze.col.file":   "Файл",
        "tab_analyze.col.issues": "Проблемы",
        "tab_analyze.col.size":   "Размер",
        "tab_analyze.col.ok":     "OK",
        "tab_analyze.col.dash":   "—",

        "tab_analyze.dlg_pick":  "Выбери PBR-карты",

        "tab_analyze.log.no_maps":   "Нечего анализировать — сначала загрузи карты",
        "tab_analyze.log.loading":   "Загрузка {n} файлов...",
        "tab_analyze.log.loaded":    "Загружено: {done}/{total}",
        "tab_analyze.log.analyzing": "Анализ...",
        "tab_analyze.log.analyzed":  "Проанализировано: {done}/{total}",
        "tab_analyze.log.not_a_file":  "Не файл: {path}",
        "tab_analyze.log.not_an_image":"Не картинка: {name}",
        "tab_analyze.log.open_fail":   "Ошибка открытия {name}: {err}",
        "tab_analyze.log.no_analyzer": "{name}: анализатор для {mtype} ещё не готов",
        "tab_analyze.log.analyze_fail":"{name}: ошибка анализа: {err}",
        "tab_analyze.log.type_changed":"{name}: тип изменён на {type}",
        "tab_analyze.log.no_maps_to_save": "Нет карт для сохранения",
        "tab_analyze.log.nothing_to_save": "Нечего сохранять",
        "tab_analyze.log.saved_one":   "{name}  ({bit}-bit)",
        "tab_analyze.log.save_fail":   "Не сохранил {name}: {err}",
        "tab_analyze.log.saved_total": "Сохранено: {saved} из {total} → {folder}",

        "tab_analyze.save.title":       "Сохранить карты",
        "tab_analyze.save.what":        "Что сохранять:",
        "tab_analyze.save.only_fixed":  "Только карты с фиксами ({n})",
        "tab_analyze.save.bitness":     "Битность:",
        "tab_analyze.save.bit8":        "8-bit  (обычный PNG, меньше вес)",
        "tab_analyze.save.bit16":       "16-bit (плавные градиенты, для normal/height)",
        "tab_analyze.save.summary":     "Всего карт: {total}  •  С фиксами: {fixed}",
        "tab_analyze.save.cancel":      "Отмена",
        "tab_analyze.save.confirm":     "Сохранить",
        "tab_analyze.save.pick_folder": "Куда сохранить карты?",

        # ═══════════════════════════════════════════════════
        #  ВКЛАДКА SEAMLESS
        # ═══════════════════════════════════════════════════
        "tab_seamless.title":        "Бесшовность",
        "tab_seamless.mode_label":   "Режим:",
        "tab_seamless.btn_one":      "К выбранной",
        "tab_seamless.btn_all":      "Ко всем",
        "tab_seamless.btn_save":     "Сохранить",

        "tab_seamless.empty.list":   "Загрузи карты на вкладке Analyze",
        "tab_seamless.empty.preview":"Выбери карту слева",
        "tab_seamless.before":       "ДО",
        "tab_seamless.after":        "ПОСЛЕ (превью)",
        "tab_seamless.mode_line":    "Режим: {mode}",
        "tab_seamless.seam_ok":      "ок",
        "tab_seamless.seam_bad":     "шов {diff:.3f}",
        "tab_seamless.seam_info":    "До: LR={lr:.3f}  TB={tb:.3f}  max={mx:.3f}",

        "tab_seamless.mode.mirror_blend.label": "Mirror-blend",
        "tab_seamless.mode.mirror_blend.desc":  "Сдвиг + зеркальный blend. Простой, для albedo/roughness/ao.",
        "tab_seamless.mode.freq_sep.label":     "Freq-separation",
        "tab_seamless.mode.freq_sep.desc":      "Frequency separation. Не размывает детали, для normal/height.",
        "tab_seamless.mode.hipass.label":       "Hi-pass (GIMP)",
        "tab_seamless.mode.hipass.desc":        "GIMP tile-seamless. Может давать наложение.",

        "tab_seamless.log.mode_changed": "{mode}",
        "tab_seamless.log.nothing_selected": "Ничего не выбрано",
        "tab_seamless.log.no_preview_map":   "Не выбрана карта для превью",
        "tab_seamless.log.applying":     "Seamless ({mode}) для {n} карт...",
        "tab_seamless.log.applied_one":  "{name}: seamless → шов {diff:.3f}",
        "tab_seamless.log.applied":      "Seamless применён: {ok}/{total}",
        "tab_seamless.log.no_seamless":  "Нет карт с применённым seamless",
        "tab_seamless.log.saved":        "Сохранено: {saved}/{total} → {folder}",
        "tab_seamless.log.saved_one":    "{name}",
        "tab_seamless.log.save_fail":    "{name}: {err}",
        "tab_seamless.log.pick_folder":  "Куда сохранить бесшовные карты?",

        # ═══════════════════════════════════════════════════
        #  ПРАВАЯ ПАНЕЛЬ (report_panel)
        # ═══════════════════════════════════════════════════
        "panel.empty":           "Выбери карту слева",
        "panel.need_analyze":    "Нажми «Анализировать все», чтобы получить отчёт",

        "panel.sev.ok":   "ХОРОШО",
        "panel.sev.warn": "ЕСТЬ ЗАМЕЧАНИЯ",
        "panel.sev.fail": "ПЛОХО",

        "panel.all_passed":      "Все проверки пройдены",
        "panel.issues_found":    "Найдено проблем: {n}",
        "panel.raw_metrics":     "Сырые метрики",
        "panel.issues_title":    "ПРОБЛЕМЫ ({n})",
        "panel.no_issues":       "Проблем не обнаружено",
        "panel.no_data":         "(нет данных)",

        "panel.fix_result.done":         "Готово",
        "panel.fix_result.better":       "Стало лучше ({before} → {after})",
        "panel.fix_result.unchanged":    "Без изменений",
        "panel.fix_result.worse":        "Стало хуже",
        "panel.fix_result.undo":         "Undo",

        "panel.fix_log":         "✓ {name}: {fix} → {before} → {after}",
        "panel.fix_fail":        "✗ Ошибка фикса '{fix}': {err}",
        "panel.refix_fail":      "✗ Пересчёт после фикса упал: {err}",
        "panel.no_analyzer":     "✗ Нет анализатора для {mtype}",
        "panel.undo_log":        "↶ {name}: откат '{fix}'",

        # ─── Вердикт: тексты проблем (одна строка — одна проблема) ───
        "verdict.normal.mean_len":
            "Длины векторов меньше нормы (средняя {v:.2f} вместо 1.0). "
            "Карта повреждена при генерации или сжатии.",
        "verdict.normal.bad_pct_fail":
            "{v:.1f}% пикселей имеют неправильную длину вектора "
            "(норма — меньше 5%).",
        "verdict.normal.bad_pct_warn":
            "Лёгкие отклонения длин векторов: {v:.1f}% пикселей "
            "(норма — меньше 1%).",
        "verdict.normal.angle_fail":
            "Средний вектор сильно сдвинут от (0,0,1) на {v:.1f}° — "
            "в карту запечён свет.",
        "verdict.normal.angle_warn":
            "Небольшой сдвиг средней нормали на {v:.1f}°.",
        "verdict.normal.not_normal":
            "B-канал тёмный и плоский, R/G тоже не варьируются. "
            "Это вообще не normal map — проверь файл.",
        "verdict.normal.broken_b":
            "B-канал вырожден: mean={bm:.2f}, std={bs:.2f}. "
            "Z потерян, но R/G живые — можно восстановить B.",

        "verdict.rough.color":
            "Карта цветная, а roughness должна быть grayscale "
            "(разброс между каналами {v:.3f}).",
        "verdict.rough.dead":
            "Карта мёртвая — весь диапазон сжат в узкую полосу "
            "(std {v:.3f}, норма > 0.06).",
        "verdict.rough.low_var":
            "Мало вариаций (std {v:.3f}, норма > 0.06). "
            "Если сцена равномерно шершавая — ок, иначе стоит растянуть.",
        "verdict.rough.narrow":
            "Пережатый диапазон: значения занимают [{p1:.2f}..{p99:.2f}] "
            "вместо [0,1]. Рендер теряет контраст.",
        "verdict.rough.noisy":
            "Слишком шумная карта (std {v:.3f}). "
            "Похоже на несглаженный шум от AI.",

        "verdict.metal.color":
            "Карта цветная, а metallic должен быть grayscale "
            "(разброс между каналами {v:.3f}).",
        "verdict.metal.muddy_fail":
            "{v:.0f}% пикселей в серой зоне (0.1..0.9). "
            "Metallic должен быть бинарным: 0 или 1. "
            "Рендер не поймёт, где металл.",
        "verdict.metal.muddy_warn":
            "{v:.0f}% пикселей в серой зоне. "
            "Если это сглаживание границы металл/диэлектрик — ок, "
            "иначе стоит бинаризовать.",
        "verdict.metal.all_zero":
            "{v:.1f}% пикселей = 0. Вся карта — диэлектрик. "
            "Если металла не должно быть — ок.",
        "verdict.metal.all_one":
            "{v:.1f}% пикселей = 1. Вся модель металлическая. "
            "Если так задумано — ок.",

        "verdict.ao.color":
            "Карта цветная, а AO должен быть grayscale "
            "(разброс между каналами {v:.3f}).",
        "verdict.ao.dead":
            "Карта мёртвая — std {v:.3f} (норма > 0.03). "
            "AO ничего не затеняет.",
        "verdict.ao.low_var":
            "Мало вариаций (std {v:.3f}, норма > 0.05).",
        "verdict.ao.dark":
            "Слишком тёмное (mean {v:.2f}, {dp:.1f}% пикселей тёмные). "
            "Возможно, перепутана полярность или генератор перестарался с тенью.",
        "verdict.ao.dark_short":
            "Слишком тёмное (mean {v:.2f}). "
            "Возможно, перепутана полярность или генератор перестарался с тенью.",
        "verdict.ao.light":
            "AO почти невидимо (mean {v:.2f}). Почти нет теней.",
        "verdict.ao.narrow":
            "Пережатый диапазон: значения занимают [{p1:.2f}..{p99:.2f}] "
            "вместо [0,1]. Контраст AO слабый.",

        "verdict.fb.unknown":
            "Тип карты не определён. Проверь тип вручную в дропдауне "
            "слева — от этого зависят проверки.",
        "verdict.fb.color":
            "Карта цветная, а {label} должна быть grayscale "
            "(разброс между каналами {v:.3f}).",
        "verdict.fb.dead":
            "Карта мёртвая — std {v:.3f} (норма > 0.02).",
        "verdict.fb.low_var":
            "Мало вариаций (std {v:.3f}, норма > 0.04).",
        "verdict.fb.narrow":
            "Пережатый диапазон: значения занимают [{p1:.2f}..{p99:.2f}] "
            "вместо [0,1].",
        "verdict.fb.noisy":
            "Слишком шумная (std {v:.3f}). Похоже на несглаженный шум от AI.",
        "verdict.fb.dark":
            "Слишком тёмная (mean {v:.2f}).",
        "verdict.fb.light":
            "Слишком светлая (mean {v:.2f}).",
        "verdict.fb.edge_muddy":
            "{v:.0f}% пикселей в серой зоне — edge обычно бинарный (0 или 1).",

        # ═══════════════════════════════════════════════════
        #  ДИАЛОГ РЕЗУЛЬТАТА ФИКСА
        # ═══════════════════════════════════════════════════
        "dlg_fix.headline.done":       "Отлично! Проблема устранена",
        "dlg_fix.headline.better":     "Стало лучше ({b} → {a} issues)",
        "dlg_fix.headline.partial":    "Стало лучше (частично): {b} → {a} issues",
        "dlg_fix.headline.worse_iss":  "Стало хуже: {b} → {a} issues",
        "dlg_fix.headline.unchanged":  "Без изменений",
        "dlg_fix.headline.worse":      "Стало хуже",
        "dlg_fix.fix_line":            "Фикс: {label}",
        "dlg_fix.row_status":          "Статус (issues):",
        "dlg_fix.row_issues":          "Issues:",
        "dlg_fix.ok":                  "OK",

        # ═══════════════════════════════════════════════════
        #  INFO-ДИАЛОГ
        # ═══════════════════════════════════════════════════
        "info.tab.help":    "Помощь",
        "info.tab.about":   "О программе",
        "info.tab.support": "Поддержать",

        "info.help_text": (
            "PBR Doctor — диагностика и ремонт PBR-карт.\n\n"
            "КАК РАБОТАТЬ:\n"
            "1. Нажми Add files и загрузи карты (normal / roughness /\n"
            "   metallic / AO / albedo).\n"
            "2. Нажми Analyze All — прога проверит каждую карту\n"
            "   и покажет светофор: OK / Warning / Fail.\n"
            "3. Кликни по карте слева — справа появятся метрики\n"
            "   и список проблем с кнопками Fix.\n"
            "4. Жми Fix для каждой проблемы. Появится диалог\n"
            "   с результатом: стало лучше / без изменений / хуже.\n"
            "5. Кнопка Undo откатит последний фикс.\n"
            "6. Save fixed — сохрани результат (8-bit или 16-bit).\n\n"
            "ЧТО ПРОВЕРЯЕТСЯ:\n"
            "• Normal — запечённый свет, битые длины векторов.\n"
            "• Roughness — мёртвая карта, узкий диапазон, шум.\n"
            "• Metallic, AO, Seamless — в разработке.\n\n"
            "СОВЕТ:\n"
            "Для нормалей и height всегда сохраняй в 16-bit —\n"
            "8-bit даёт бандинг на градиентах.\n"
        ),

        "info.about.version": "Версия",
        "info.about.build":   "Сборка",
        "info.about.author":  "Автор",
        "info.about.license": "Лицензия",
        "info.about.desc": (
            "Отдельная программа из семейства Albedolizer.\n"
            "Диагностика и ремонт PBR-карт после AI-генерации.\n"
            "Работает с normal, roughness, metallic, AO, seamless."
        ),

        "info.support.copied": "✓ Адрес скопирован в буфер",

        # ═══════════════════════════════════════════════════
        #  SUPPORT (кошельки)
        # ═══════════════════════════════════════════════════
        "wallets.support_title": "Поддержать разработку",
        "wallets.support_text":  "Бро, если зашло, закинь дяде на папиросы.",
    },

    # ═══════════════════════════════════════════════════════
    #  ENGLISH
    # ═══════════════════════════════════════════════════════
    "en": {

        "app.title":       "PBR Doctor",
        "app.subtitle":    "Diagnose and repair PBR maps",
        "app.tagline":     "Analyze & repair PBR maps",
        "app.log":         "Log",
        "app.info":        "Info",
        "app.lang":        "Language",

        "log.ready":       "PBR Doctor 1.0.0 is ready",
        "log.hint_add":    "Click Add files to load maps",

        "map.albedo":      "Albedo / BaseColor",
        "map.normal":      "Normal",
        "map.roughness":   "Roughness",
        "map.metallic":    "Metallic",
        "map.ao":          "Ambient Occlusion",
        "map.orm":         "ORM (R=AO G=Rough B=Metal)",
        "map.height":      "Height / Displacement",
        "map.edge":        "Edge / Outline",
        "map.unknown":     "Unknown",

        "detected.name":         "by name",
        "detected.content":      "by content",
        "detected.name+content": "name + content",
        "detected.fallback":     "undetected",
        "detected.manual":       "manual",

        "sev.ok":   "OK",
        "sev.warn": "Warning",
        "sev.fail": "Fail",

        "fix.to_grayscale":    "Make grayscale",
        "fix.normalize_range": "Stretch range",
        "fix.compress":        "Smooth",
        "fix.invert":          "Invert",
        "fix.binarize_otsu":   "Binarize (Otsu)",
        "fix.binarize_hard":   "Binarize (threshold 0.5)",
        "fix.restore_b":       "Restore B channel",
        "fix.unbake_light":    "Remove baked light",
        "fix.align_normal":    "Align mean normal",
        "fix.fix_all_orm":     "Fix All (ORM)",
        "fix.generic":         "Fix",

        "err.unknown_fix":        "Unknown fix: {fix_id}",
        "err.fix_not_implemented":"Fix '{fix_id}' is not implemented",
        "err.open_file":          "Failed to open file: {path}",
        "err.open_reason":        "Reason: {reason}",
        "err.open_hint":          "Check: path length (>260 chars?), permissions, free disk space, file integrity.",
        "err.seamless_mode":      "Unknown seamless mode: {mode}",
        "err.orm_bad_fix_id":     "Bad fix_id for ORM: {fix_id}",
        "err.orm_forbidden_fix":  "Fix '{op}' is forbidden for ORM — it breaks channel semantics.",
        "err.orm_unknown_channel":"Unknown channel: {channel}",

        # NORMAL
        "normal.not_a_normal.title":  "This doesn't look like a normal map",
        "normal.not_a_normal.detail": (
            "B channel averages {b_mean:.2f} (should be >0.5), "
            "std={b_std:.3f}. R/G barely vary "
            "(r_std={r_std:.3f}, g_std={g_std:.3f}). "
            "Looks like a grayscale map or albedo. "
            "Check you loaded the right file."
        ),
        "normal.broken_b.title":  "B channel is degenerate (flat)",
        "normal.broken_b.detail": (
            "Mean vector length {mean_len:.3f} (should be ≈1.0). "
            "B channel: mean={b_mean:.3f}, std={b_std:.3f}. "
            "Z likely lost during generation. "
            "We'll restore B from R and G: B = sqrt(1 - X² - Y²)."
        ),
        "normal.baked.title":  "Baked light (shift {angle:.1f}°)",
        "normal.baked.detail": (
            "Mean normal vector is tilted from (0,0,1) by {angle:.1f}°. "
            "That means directional light was baked into the map — "
            "the render will be wrong. Can be removed by rotation."
        ),
        "normal.baked_mild.title":  "Slight mean-normal shift ({angle:.1f}°)",
        "normal.baked_mild.detail": (
            "Mean vector is tilted by {angle:.1f}°. "
            "Can be normal for relief surfaces, but if this is a flat "
            "tile — worth checking."
        ),
        "normal.bad_len.title":  "Broken vector lengths ({bad_pct:.1f}% of pixels)",
        "normal.bad_len.detail": (
            "{bad_pct:.1f}% of pixels have length outside [0.9, 1.1]. "
            "Mean length {mean_len:.3f}, std {std_len:.3f}. "
            "Map is damaged from generation or compression. "
            "We'll restore B from R and G."
        ),
        "normal.bad_len_mild.title":  "Minor length deviations ({bad_pct:.1f}%)",
        "normal.bad_len_mild.detail": (
            "{bad_pct:.1f}% of pixels outside [0.9, 1.1]. "
            "Usually normal for compressed PNGs, but check."
        ),

        # ROUGHNESS
        "rough.not_grayscale.title":  "Roughness is not grayscale",
        "rough.not_grayscale.detail": (
            "R/G/B channels differ (std={channel_std:.3f}). "
            "Roughness should be single-channel. "
            "The generator likely dumped color into it."
        ),
        "rough.dead.title":  "Dead map (std={std:.3f})",
        "rough.dead.detail": (
            "Value spread is almost zero — the whole map is in "
            "~[{p1:.2f}, {p99:.2f}] around {mean:.2f}. "
            "{mid_pct:.1f}% of pixels in the mid zone. "
            "Render will be flat. Needs normalization or replacement."
        ),
        "rough.low_var.title":  "Low variation (std={std:.3f})",
        "rough.low_var.detail": (
            "Spread is below normal. If the surface is uniformly rough — "
            "fine, otherwise stretch it."
        ),
        "rough.narrow.title":  "Narrow range (span={span:.2f})",
        "rough.narrow.detail": (
            "Values only span [{p1:.2f}, {p99:.2f}] out of [0, 1]. "
            "Render loses roughness contrast."
        ),
        "rough.noisy.title":  "Too noisy (std={std:.3f})",
        "rough.noisy.detail": (
            "Spread is off the charts. Looks like unsmoothed AI noise. "
            "Render will ring."
        ),

        # METALLIC
        "metal.not_grayscale.title":  "Metallic is not grayscale",
        "metal.not_grayscale.detail": (
            "R/G/B channels differ (std={channel_std:.3f}). "
            "Metallic should be single-channel. "
            "The generator likely dumped color into it."
        ),
        "metal.muddy.title":  "Gradients in the mid zone ({muddy_pct:.1f}%)",
        "metal.muddy.detail": (
            "{muddy_pct:.1f}% of pixels in range {low}..{high}. "
            "Metalness should be binary (0 or 1). "
            "Render will be wrong — can't tell metal from dielectric."
        ),
        "metal.muddy_mild.title":  "Some gradients ({muddy_pct:.1f}%)",
        "metal.muddy_mild.detail": (
            "{muddy_pct:.1f}% of pixels in the mid zone. "
            "If this is the metal/dielectric edge — can be normal "
            "(antialiasing), otherwise binarize."
        ),
        "metal.all_zero.title":  "No metal (all zeros)",
        "metal.all_zero.detail": (
            "{zero_pct:.1f}% of pixels = 0. The whole map is dielectric. "
            "If the material shouldn't contain metal — fine. "
            "If it should — the generator failed."
        ),
        "metal.all_one.title":  "All metal (all ones)",
        "metal.all_one.detail": (
            "{one_pct:.1f}% of pixels = 1. The whole model is metal. "
            "If that's intended — fine, but usually it's a generator error."
        ),

        # AO
        "ao.not_grayscale.title":  "AO is not grayscale",
        "ao.not_grayscale.detail": (
            "R/G/B channels differ (std={channel_std:.3f}). "
            "AO should be single-channel. "
            "The generator likely dumped albedo color into it."
        ),
        "ao.dead.title":  "Dead map (std={std:.3f})",
        "ao.dead.detail": (
            "Spread is almost zero — the whole map sits in a narrow band "
            "around {mean:.2f}. AO is useless. "
            "The generator may have just filled it with gray."
        ),
        "ao.low_var.title":  "Low variation (std={std:.3f})",
        "ao.low_var.detail": (
            "Spread is below normal. If geometry is flat — fine, "
            "otherwise push contrast."
        ),
        "ao.too_dark.title":  "AO is too dark (mean={mean:.2f})",
        "ao.too_dark.detail": (
            "Mean brightness {mean:.2f} — almost everything is shadowed "
            "({dark_pct:.1f}% of pixels are dark). "
            "Likely polarity is flipped (white = shadow, black = light) "
            "or the generator overdid the shadows."
        ),
        "ao.too_light.title":  "AO is almost invisible (mean={mean:.2f})",
        "ao.too_light.detail": (
            "Mean brightness {mean:.2f} — almost no shadows. "
            "If the scene is open — fine, but usually AO should shade "
            "crevices at least a bit."
        ),
        "ao.narrow.title":  "Narrow range (span={span:.2f})",
        "ao.narrow.detail": (
            "Values only span [{p1:.2f}, {p99:.2f}] out of [0, 1]. "
            "AO contrast is weak."
        ),

        # ORM
        "orm.bad_shape.title":  "[ORM] Map is not RGB",
        "orm.bad_shape.detail": "ORM must be an RGB map with three channels.",
        "orm.grayscale.title":  "[ORM] Map is grayscale",
        "orm.grayscale.detail": (
            "All three channels are identical. This isn't ORM — "
            "check the file."
        ),
        "orm.metal_muddy.title":  "[B] Metallic: not binary",
        "orm.metal_muddy.detail": (
            "{mid_pct:.0f}% of pixels in the mid zone. "
            "Metal expects 0 or 1."
        ),
        "orm.fix_all.title":  "[ORM] Fix everything",
        "orm.fix_all.detail": (
            "Apply the best fix to every channel where issues were found."
        ),
        "orm.channel.R": "AO",
        "orm.channel.G": "Roughness",
        "orm.channel.B": "Metallic",

        "orm.wrap.R": "[R] AO: {text}",
        "orm.wrap.G": "[G] Roughness: {text}",
        "orm.wrap.B": "[B] Metallic: {text}",

        # FALLBACK
        "fb.bad_shape.title":  "{label}: map is not RGB",
        "fb.bad_shape.detail": "Expected an RGB array [H,W,3].",
        "fb.unknown.title":  "Map type undetected",
        "fb.unknown.detail": (
            "Auto-detect couldn't identify the map. It {kind}. "
            "Pick the type manually in the dropdown on the left — "
            "checks depend on it."
        ),
        "fb.unknown.kind_gray":  "looks like a grayscale map",
        "fb.unknown.kind_color": "looks like a color map (possibly albedo)",
        "fb.dead_unknown.title":  "Map barely varies",
        "fb.dead_unknown.detail": (
            "std {std:.3f} — spread is below normal. "
            "The map may be empty or squashed to a point."
        ),
        "fb.not_grayscale.title":  "{label} is not grayscale",
        "fb.not_grayscale.detail": (
            "R/G/B channels differ (std={channel_std:.3f}). "
            "{label} map should be single-channel."
        ),
        "fb.dead.title":  "{label}: dead map (std={std:.3f})",
        "fb.dead.detail": (
            "Spread is almost zero — the whole map sits in a narrow band "
            "around {mean:.2f}. Render will be flat."
        ),
        "fb.low_var.title":  "{label}: low variation (std={std:.3f})",
        "fb.low_var.detail": (
            "Spread is below normal. If that's intended — fine, "
            "otherwise stretch it."
        ),
        "fb.narrow.title":  "{label}: narrow range (span={span:.2f})",
        "fb.narrow.detail": (
            "Values only span [{p1:.2f}, {p99:.2f}] out of [0, 1]. "
            "Contrast is weak."
        ),
        "fb.too_dark.title":  "{label}: too dark (mean={mean:.2f})",
        "fb.too_dark.detail": "Mean brightness {mean:.2f} — almost all black.",
        "fb.too_light.title":  "{label}: too light (mean={mean:.2f})",
        "fb.too_light.detail": "Mean brightness {mean:.2f} — almost all white.",
        "fb.noisy.title":  "{label}: too noisy (std={std:.3f})",
        "fb.noisy.detail": (
            "Spread is off the charts. Looks like unsmoothed AI noise."
        ),
        "fb.edge_not_binary.title":  "Edge is not binary ({muddy_pct:.1f}% in mid zone)",
        "fb.edge_not_binary.detail": (
            "{muddy_pct:.1f}% of pixels in range {low}..{high}. "
            "Edge maps are usually 0 or 1. Blurry edges may look "
            "like dirt in the render."
        ),
        "fb.label.height":  "Height",
        "fb.label.edge":    "Edge",
        "fb.label.unknown": "Unknown",

        # TAB ANALYZE
        "tab_analyze.title":     "Analyze",
        "tab_analyze.btn_add":   "Add files",
        "tab_analyze.btn_analyze":"Analyze All",
        "tab_analyze.btn_save":  "Save fixed",
        "tab_analyze.btn_clear": "Clear",
        "tab_analyze.empty.title": "Click Add files to load maps",
        "tab_analyze.empty.hint":  "Normal / Roughness / Metallic / AO / ORM / Albedo",
        "tab_analyze.col.type":   "Type",
        "tab_analyze.col.file":   "File",
        "tab_analyze.col.issues": "Issues",
        "tab_analyze.col.size":   "Size",
        "tab_analyze.col.ok":     "OK",
        "tab_analyze.col.dash":   "—",
        "tab_analyze.dlg_pick":  "Pick PBR maps",
        "tab_analyze.log.no_maps":   "Nothing to analyze — load maps first",
        "tab_analyze.log.loading":   "Loading {n} files...",
        "tab_analyze.log.loaded":    "Loaded: {done}/{total}",
        "tab_analyze.log.analyzing": "Analyzing...",
        "tab_analyze.log.analyzed":  "Analyzed: {done}/{total}",
        "tab_analyze.log.not_a_file":  "Not a file: {path}",
        "tab_analyze.log.not_an_image":"Not an image: {name}",
        "tab_analyze.log.open_fail":   "Failed to open {name}: {err}",
        "tab_analyze.log.no_analyzer": "{name}: analyzer for {mtype} is not ready",
        "tab_analyze.log.analyze_fail":"{name}: analysis failed: {err}",
        "tab_analyze.log.type_changed":"{name}: type changed to {type}",
        "tab_analyze.log.no_maps_to_save": "No maps to save",
        "tab_analyze.log.nothing_to_save": "Nothing to save",
        "tab_analyze.log.saved_one":   "{name}  ({bit}-bit)",
        "tab_analyze.log.save_fail":   "Could not save {name}: {err}",
        "tab_analyze.log.saved_total": "Saved: {saved} of {total} → {folder}",
        "tab_analyze.save.title":       "Save maps",
        "tab_analyze.save.what":        "What to save:",
        "tab_analyze.save.only_fixed":  "Only maps with fixes ({n})",
        "tab_analyze.save.bitness":     "Bit depth:",
        "tab_analyze.save.bit8":        "8-bit  (regular PNG, smaller)",
        "tab_analyze.save.bit16":       "16-bit (smooth gradients, for normal/height)",
        "tab_analyze.save.summary":     "Total maps: {total}  •  With fixes: {fixed}",
        "tab_analyze.save.cancel":      "Cancel",
        "tab_analyze.save.confirm":     "Save",
        "tab_analyze.save.pick_folder": "Where to save the maps?",

        # TAB SEAMLESS
        "tab_seamless.title":        "Seamless",
        "tab_seamless.mode_label":   "Mode:",
        "tab_seamless.btn_one":      "To selected",
        "tab_seamless.btn_all":      "To all",
        "tab_seamless.btn_save":     "Save",
        "tab_seamless.empty.list":   "Load maps on the Analyze tab",
        "tab_seamless.empty.preview":"Pick a map on the left",
        "tab_seamless.before":       "BEFORE",
        "tab_seamless.after":        "AFTER (preview)",
        "tab_seamless.mode_line":    "Mode: {mode}",
        "tab_seamless.seam_ok":      "ok",
        "tab_seamless.seam_bad":     "seam {diff:.3f}",
        "tab_seamless.seam_info":    "Before: LR={lr:.3f}  TB={tb:.3f}  max={mx:.3f}",
        "tab_seamless.mode.mirror_blend.label": "Mirror-blend",
        "tab_seamless.mode.mirror_blend.desc":  "Shift + mirror blend. Simple, for albedo/roughness/ao.",
        "tab_seamless.mode.freq_sep.label":     "Freq-separation",
        "tab_seamless.mode.freq_sep.desc":      "Frequency separation. Keeps detail, for normal/height.",
        "tab_seamless.mode.hipass.label":       "Hi-pass (GIMP)",
        "tab_seamless.mode.hipass.desc":        "GIMP tile-seamless. May produce overlap.",
        "tab_seamless.log.mode_changed": "{mode}",
        "tab_seamless.log.nothing_selected": "Nothing selected",
        "tab_seamless.log.no_preview_map":   "No map selected for preview",
        "tab_seamless.log.applying":     "Seamless ({mode}) for {n} maps...",
        "tab_seamless.log.applied_one":  "{name}: seamless → seam {diff:.3f}",
        "tab_seamless.log.applied":      "Seamless applied: {ok}/{total}",
        "tab_seamless.log.no_seamless":  "No maps with applied seamless",
        "tab_seamless.log.saved":        "Saved: {saved}/{total} → {folder}",
        "tab_seamless.log.saved_one":    "{name}",
        "tab_seamless.log.save_fail":    "{name}: {err}",
        "tab_seamless.log.pick_folder":  "Where to save seamless maps?",

        # REPORT PANEL
        "panel.empty":           "Pick a map on the left",
        "panel.need_analyze":    "Click Analyze All to get a report",
        "panel.sev.ok":   "GOOD",
        "panel.sev.warn": "HAS WARNINGS",
        "panel.sev.fail": "BAD",
        "panel.all_passed":      "All checks passed",
        "panel.issues_found":    "Issues found: {n}",
        "panel.raw_metrics":     "Raw metrics",
        "panel.issues_title":    "ISSUES ({n})",
        "panel.no_issues":       "No issues found",
        "panel.no_data":         "(no data)",
        "panel.fix_result.done":         "Done",
        "panel.fix_result.better":       "Improved ({before} → {after})",
        "panel.fix_result.unchanged":    "No change",
        "panel.fix_result.worse":        "Got worse",
        "panel.fix_result.undo":         "Undo",
        "panel.fix_log":         "✓ {name}: {fix} → {before} → {after}",
        "panel.fix_fail":        "✗ Fix '{fix}' failed: {err}",
        "panel.refix_fail":      "✗ Re-analysis after fix failed: {err}",
        "panel.no_analyzer":     "✗ No analyzer for {mtype}",
        "panel.undo_log":        "↶ {name}: undo '{fix}'",

        # VERDICT
        "verdict.normal.mean_len":
            "Vector lengths are below normal (average {v:.2f} instead of 1.0). "
            "The map is damaged from generation or compression.",
        "verdict.normal.bad_pct_fail":
            "{v:.1f}% of pixels have wrong vector length (normal — under 5%).",
        "verdict.normal.bad_pct_warn":
            "Minor vector-length deviations: {v:.1f}% of pixels (normal — under 1%).",
        "verdict.normal.angle_fail":
            "Mean vector is heavily tilted from (0,0,1) by {v:.1f}° — "
            "light was baked into the map.",
        "verdict.normal.angle_warn":
            "Slight mean-normal shift of {v:.1f}°.",
        "verdict.normal.not_normal":
            "B channel is dark and flat, R/G barely vary. "
            "This isn't a normal map at all — check the file.",
        "verdict.normal.broken_b":
            "B channel is degenerate: mean={bm:.2f}, std={bs:.2f}. "
            "Z is lost but R/G are alive — B can be restored.",

        "verdict.rough.color":
            "Map is colored, but roughness should be grayscale "
            "(channel spread {v:.3f}).",
        "verdict.rough.dead":
            "Map is dead — the whole range is squashed into a narrow band "
            "(std {v:.3f}, normal > 0.06).",
        "verdict.rough.low_var":
            "Low variation (std {v:.3f}, normal > 0.06). "
            "If the surface is uniformly rough — fine, otherwise stretch it.",
        "verdict.rough.narrow":
            "Narrow range: values span [{p1:.2f}..{p99:.2f}] "
            "instead of [0,1]. Render loses contrast.",
        "verdict.rough.noisy":
            "Map is too noisy (std {v:.3f}). Looks like unsmoothed AI noise.",

        "verdict.metal.color":
            "Map is colored, but metallic should be grayscale "
            "(channel spread {v:.3f}).",
        "verdict.metal.muddy_fail":
            "{v:.0f}% of pixels in the mid zone (0.1..0.9). "
            "Metallic must be binary: 0 or 1. "
            "Render won't know where metal is.",
        "verdict.metal.muddy_warn":
            "{v:.0f}% of pixels in the mid zone. "
            "If this is the metal/dielectric edge — fine, "
            "otherwise binarize.",
        "verdict.metal.all_zero":
            "{v:.1f}% of pixels = 0. The whole map is dielectric. "
            "Fine if no metal is intended.",
        "verdict.metal.all_one":
            "{v:.1f}% of pixels = 1. The whole model is metal. "
            "Fine if that's intended.",

        "verdict.ao.color":
            "Map is colored, but AO should be grayscale "
            "(channel spread {v:.3f}).",
        "verdict.ao.dead":
            "Map is dead — std {v:.3f} (normal > 0.03). "
            "AO doesn't shade anything.",
        "verdict.ao.low_var":
            "Low variation (std {v:.3f}, normal > 0.05).",
        "verdict.ao.dark":
            "Too dark (mean {v:.2f}, {dp:.1f}% of pixels dark). "
            "Polarity may be flipped or the generator overdid shadows.",
        "verdict.ao.dark_short":
            "Too dark (mean {v:.2f}). "
            "Polarity may be flipped or the generator overdid shadows.",
        "verdict.ao.light":
            "AO is almost invisible (mean {v:.2f}). Almost no shadows.",
        "verdict.ao.narrow":
            "Narrow range: values span [{p1:.2f}..{p99:.2f}] "
            "instead of [0,1]. AO contrast is weak.",

        "verdict.fb.unknown":
            "Map type undetected. Pick it manually in the dropdown "
            "on the left — checks depend on it.",
        "verdict.fb.color":
            "Map is colored, but {label} should be grayscale "
            "(channel spread {v:.3f}).",
        "verdict.fb.dead":
            "Map is dead — std {v:.3f} (normal > 0.02).",
        "verdict.fb.low_var":
            "Low variation (std {v:.3f}, normal > 0.04).",
        "verdict.fb.narrow":
            "Narrow range: values span [{p1:.2f}..{p99:.2f}] instead of [0,1].",
        "verdict.fb.noisy":
            "Too noisy (std {v:.3f}). Looks like unsmoothed AI noise.",
        "verdict.fb.dark":
            "Too dark (mean {v:.2f}).",
        "verdict.fb.light":
            "Too light (mean {v:.2f}).",
        "verdict.fb.edge_muddy":
            "{v:.0f}% of pixels in the mid zone — edge is usually binary (0 or 1).",

        # FIX DIALOG
        "dlg_fix.headline.done":       "Great! Issue resolved",
        "dlg_fix.headline.better":     "Improved ({b} → {a} issues)",
        "dlg_fix.headline.partial":    "Partially improved: {b} → {a} issues",
        "dlg_fix.headline.worse_iss":  "Got worse: {b} → {a} issues",
        "dlg_fix.headline.unchanged":  "No change",
        "dlg_fix.headline.worse":      "Got worse",
        "dlg_fix.fix_line":            "Fix: {label}",
        "dlg_fix.row_status":          "Status (issues):",
        "dlg_fix.row_issues":          "Issues:",
        "dlg_fix.ok":                  "OK",

        # INFO
        "info.tab.help":    "Help",
        "info.tab.about":   "About",
        "info.tab.support": "Support",
        "info.help_text": (
            "PBR Doctor — diagnose and repair PBR maps.\n\n"
            "HOW TO USE:\n"
            "1. Click Add files and load maps (normal / roughness /\n"
            "   metallic / AO / albedo).\n"
            "2. Click Analyze All — the app checks every map and\n"
            "   shows a traffic light: OK / Warning / Fail.\n"
            "3. Click a map on the left — details, metrics and issues\n"
            "   with Fix buttons appear on the right.\n"
            "4. Hit Fix on each issue. A dialog shows the result:\n"
            "   improved / no change / worse.\n"
            "5. Undo rolls back the last fix.\n"
            "6. Save fixed — export the result (8-bit or 16-bit).\n\n"
            "WHAT IS CHECKED:\n"
            "• Normal — baked light, broken vector lengths.\n"
            "• Roughness — dead map, narrow range, noise.\n"
            "• Metallic, AO, Seamless — work in progress.\n\n"
            "TIP:\n"
            "Always save normal and height at 16-bit —\n"
            "8-bit produces banding on gradients.\n"
        ),
        "info.about.version": "Version",
        "info.about.build":   "Build",
        "info.about.author":  "Author",
        "info.about.license": "License",
        "info.about.desc": (
            "A standalone app from the Albedolizer family.\n"
            "Diagnose and repair PBR maps after AI generation.\n"
            "Works with normal, roughness, metallic, AO, seamless."
        ),
        "info.support.copied": "✓ Address copied to clipboard",

        "wallets.support_title": "Support development",
        "wallets.support_text":  "Bro, if this helped, toss the dev a coin.",
    },

    # ═══════════════════════════════════════════════════════
    #  CHINESE (Simplified, zh-Hans)
    # ═══════════════════════════════════════════════════════
    "zh": {

        "app.title":       "PBR Doctor",
        "app.subtitle":    "PBR 贴图诊断与修复",
        "app.tagline":     "PBR 贴图分析与修复",
        "app.log":         "日志",
        "app.info":        "关于",
        "app.lang":        "语言",

        "log.ready":       "PBR Doctor 1.0.0 已就绪",
        "log.hint_add":    "点击 Add files 加载贴图",

        "map.albedo":      "反照率 / 基础色",
        "map.normal":      "法线贴图",
        "map.roughness":   "粗糙度",
        "map.metallic":    "金属度",
        "map.ao":          "环境光遮蔽",
        "map.orm":         "ORM（R=AO G=粗糙 B=金属）",
        "map.height":      "高度 / 置换",
        "map.edge":        "边缘 / 描边",
        "map.unknown":     "未知",

        "detected.name":         "按文件名",
        "detected.content":      "按内容",
        "detected.name+content": "文件名 + 内容",
        "detected.fallback":     "未识别",
        "detected.manual":       "手动",

        "sev.ok":   "正常",
        "sev.warn": "警告",
        "sev.fail": "失败",

        "fix.to_grayscale":    "转为灰度",
        "fix.normalize_range": "拉伸范围",
        "fix.compress":        "平滑",
        "fix.invert":          "反相",
        "fix.binarize_otsu":   "二值化（Otsu）",
        "fix.binarize_hard":   "二值化（阈值 0.5）",
        "fix.restore_b":       "恢复 B 通道",
        "fix.unbake_light":    "去除烘焙光照",
        "fix.align_normal":    "对齐平均法线",
        "fix.fix_all_orm":     "全部修复（ORM）",
        "fix.generic":         "修复",

        "err.unknown_fix":        "未知修复：{fix_id}",
        "err.fix_not_implemented":"修复 '{fix_id}' 未实现",
        "err.open_file":          "无法打开文件：{path}",
        "err.open_reason":        "原因：{reason}",
        "err.open_hint":          "请检查：路径长度（>260 字符？）、权限、磁盘空间、文件完整性。",
        "err.seamless_mode":      "未知无缝模式：{mode}",
        "err.orm_bad_fix_id":     "ORM 的 fix_id 无效：{fix_id}",
        "err.orm_forbidden_fix":  "修复 '{op}' 不适用于 ORM — 会破坏通道语义。",
        "err.orm_unknown_channel":"未知通道：{channel}",

        # NORMAL
        "normal.not_a_normal.title":  "这不像法线贴图",
        "normal.not_a_normal.detail": (
            "B 通道平均 {b_mean:.2f}（应大于 0.5），std={b_std:.3f}。"
            "R/G 也几乎没有变化（r_std={r_std:.3f}，g_std={g_std:.3f}）。"
            "看起来是灰度图或反照率贴图。请检查是否加载了正确的文件。"
        ),
        "normal.broken_b.title":  "B 通道退化（平坦）",
        "normal.broken_b.detail": (
            "平均向量长度 {mean_len:.3f}（应约为 1.0）。"
            "B 通道：mean={b_mean:.3f}，std={b_std:.3f}。"
            "生成时可能丢失了 Z。可从 R、G 恢复 B：B = sqrt(1 - X² - Y²)。"
        ),
        "normal.baked.title":  "烘焙光照（偏移 {angle:.1f}°）",
        "normal.baked.detail": (
            "平均法线偏离 (0,0,1) 达 {angle:.1f}°。"
            "说明贴图中烘焙了方向光 — 渲染会出错。可通过旋转去除。"
        ),
        "normal.baked_mild.title":  "平均法线轻微偏移（{angle:.1f}°）",
        "normal.baked_mild.detail": (
            "平均向量偏移 {angle:.1f}°。对凹凸表面属正常，"
            "但若是平铺贴图，值得检查。"
        ),
        "normal.bad_len.title":  "向量长度异常（{bad_pct:.1f}% 像素）",
        "normal.bad_len.detail": (
            "{bad_pct:.1f}% 的像素长度超出 [0.9, 1.1]。"
            "平均长度 {mean_len:.3f}，std {std_len:.3f}。"
            "贴图在生成或压缩时损坏。将从 R、G 恢复 B 通道。"
        ),
        "normal.bad_len_mild.title":  "轻微长度偏差（{bad_pct:.1f}%）",
        "normal.bad_len_mild.detail": (
            "{bad_pct:.1f}% 的像素超出 [0.9, 1.1]。"
            "对压缩过的 PNG 通常正常，但仍建议检查。"
        ),

        # ROUGHNESS
        "rough.not_grayscale.title":  "粗糙度不是灰度图",
        "rough.not_grayscale.detail": (
            "R/G/B 通道不一致（std={channel_std:.3f}）。"
            "粗糙度应为单通道。生成器可能把颜色填了进去。"
        ),
        "rough.dead.title":  "死图（std={std:.3f}）",
        "rough.dead.detail": (
            "数值分布几乎为零 — 整张图集中在 ~[{p1:.2f}, {p99:.2f}] 附近，"
            "均值 {mean:.2f}。{mid_pct:.1f}% 的像素位于中间区域。"
            "渲染会显得平坦。需要归一化或替换贴图。"
        ),
        "rough.low_var.title":  "变化过少（std={std:.3f}）",
        "rough.low_var.detail": (
            "分布低于正常水平。若表面均匀粗糙则无妨，否则应拉伸。"
        ),
        "rough.narrow.title":  "范围被压缩（span={span:.2f}）",
        "rough.narrow.detail": (
            "数值仅分布在 [{p1:.2f}, {p99:.2f}]，未覆盖 [0, 1]。"
            "渲染会丢失粗糙度对比。"
        ),
        "rough.noisy.title":  "噪声过多（std={std:.3f}）",
        "rough.noisy.detail": (
            "分布异常。看起来是 AI 生成后未平滑的噪声，渲染会出现噪点。"
        ),

        # METALLIC
        "metal.not_grayscale.title":  "金属度不是灰度图",
        "metal.not_grayscale.detail": (
            "R/G/B 通道不一致（std={channel_std:.3f}）。"
            "金属度应为单通道。生成器可能填入了颜色。"
        ),
        "metal.muddy.title":  "中间区域有渐变（{muddy_pct:.1f}%）",
        "metal.muddy.detail": (
            "{muddy_pct:.1f}% 的像素位于 {low}..{high} 区间。"
            "金属度应为二值（0 或 1）。渲染会出错 — 无法区分金属和电介质。"
        ),
        "metal.muddy_mild.title":  "少量渐变（{muddy_pct:.1f}%）",
        "metal.muddy_mild.detail": (
            "{muddy_pct:.1f}% 的像素位于中间区域。"
            "若是金属/电介质的过渡边缘（抗锯齿）则属正常，否则应二值化。"
        ),
        "metal.all_zero.title":  "没有金属（全为 0）",
        "metal.all_zero.detail": (
            "{zero_pct:.1f}% 的像素 = 0。整张图都是电介质。"
            "若材质不应含金属则正常；若应含，则生成器失败了。"
        ),
        "metal.all_one.title":  "全是金属（全为 1）",
        "metal.all_one.detail": (
            "{one_pct:.1f}% 的像素 = 1。整个模型都是金属。"
            "若确为如此则正常，但通常是生成器出错。"
        ),

        # AO
        "ao.not_grayscale.title":  "AO 不是灰度图",
        "ao.not_grayscale.detail": (
            "R/G/B 通道不一致（std={channel_std:.3f}）。"
            "AO 应为单通道。生成器可能把反照率的颜色填了进去。"
        ),
        "ao.dead.title":  "死图（std={std:.3f}）",
        "ao.dead.detail": (
            "分布几乎为零 — 整张图集中在 {mean:.2f} 附近的窄带中。"
            "AO 没有作用。生成器可能只是填了灰。"
        ),
        "ao.low_var.title":  "变化过少（std={std:.3f}）",
        "ao.low_var.detail": (
            "分布低于正常。若几何平坦则无妨，否则应提升对比。"
        ),
        "ao.too_dark.title":  "AO 过暗（mean={mean:.2f}）",
        "ao.too_dark.detail": (
            "平均亮度 {mean:.2f} — 几乎全被遮蔽（{dark_pct:.1f}% 的像素偏暗）。"
            "可能极性颠倒（白色=阴影，黑色=光照），或生成器阴影过重。"
        ),
        "ao.too_light.title":  "AO 几乎不可见（mean={mean:.2f}）",
        "ao.too_light.detail": (
            "平均亮度 {mean:.2f} — 几乎没有阴影。"
            "若场景开阔则无妨，但通常 AO 至少应轻微遮蔽缝隙。"
        ),
        "ao.narrow.title":  "范围被压缩（span={span:.2f}）",
        "ao.narrow.detail": (
            "数值仅分布在 [{p1:.2f}, {p99:.2f}]，未覆盖 [0, 1]。"
            "AO 对比过弱。"
        ),

        # ORM
        "orm.bad_shape.title":  "[ORM] 贴图不是 RGB",
        "orm.bad_shape.detail": "ORM 必须为三通道 RGB 贴图。",
        "orm.grayscale.title":  "[ORM] 贴图是灰度图",
        "orm.grayscale.detail": "三个通道完全相同。这不是 ORM — 请检查文件。",
        "orm.metal_muddy.title":  "[B] 金属度：非二值",
        "orm.metal_muddy.detail": (
            "{mid_pct:.0f}% 的像素位于中间区域。金属度应为 0 或 1。"
        ),
        "orm.fix_all.title":  "[ORM] 全部修复",
        "orm.fix_all.detail": "对所有存在问题的通道应用最佳修复。",
        "orm.channel.R": "AO",
        "orm.channel.G": "粗糙度",
        "orm.channel.B": "金属度",

        "orm.wrap.R": "[R] AO: {text}",
        "orm.wrap.G": "[G] 粗糙度: {text}",
        "orm.wrap.B": "[B] 金属度: {text}",

        # FALLBACK
        "fb.bad_shape.title":  "{label}：贴图不是 RGB",
        "fb.bad_shape.detail": "需要 RGB 数组 [H,W,3]。",
        "fb.unknown.title":  "贴图类型未识别",
        "fb.unknown.detail": (
            "自动检测无法识别贴图。它{kind}。"
            "请在左侧下拉菜单中手动选择类型 — 检查项取决于它。"
        ),
        "fb.unknown.kind_gray":  "看起来是灰度图",
        "fb.unknown.kind_color": "看起来是彩色图（可能是反照率）",
        "fb.dead_unknown.title":  "贴图几乎没有变化",
        "fb.dead_unknown.detail": (
            "std {std:.3f} — 分布低于正常。贴图可能为空或压缩到一点。"
        ),
        "fb.not_grayscale.title":  "{label} 不是灰度图",
        "fb.not_grayscale.detail": (
            "R/G/B 通道不一致（std={channel_std:.3f}）。"
            "{label} 贴图应为单通道。"
        ),
        "fb.dead.title":  "{label}：死图（std={std:.3f}）",
        "fb.dead.detail": (
            "分布几乎为零 — 整张图集中在 {mean:.2f} 附近的窄带中。渲染会平坦。"
        ),
        "fb.low_var.title":  "{label}：变化过少（std={std:.3f}）",
        "fb.low_var.detail": "分布低于正常。若非有意，应拉伸。",
        "fb.narrow.title":  "{label}：范围被压缩（span={span:.2f}）",
        "fb.narrow.detail": (
            "数值仅分布在 [{p1:.2f}, {p99:.2f}]，未覆盖 [0, 1]。对比过弱。"
        ),
        "fb.too_dark.title":  "{label}：过暗（mean={mean:.2f}）",
        "fb.too_dark.detail": "平均亮度 {mean:.2f} — 几乎全黑。",
        "fb.too_light.title":  "{label}：过亮（mean={mean:.2f}）",
        "fb.too_light.detail": "平均亮度 {mean:.2f} — 几乎全白。",
        "fb.noisy.title":  "{label}：噪声过多（std={std:.3f}）",
        "fb.noisy.detail": "分布异常。看起来是 AI 生成后未平滑的噪声。",
        "fb.edge_not_binary.title":  "边缘不是二值（{muddy_pct:.1f}% 在中间区域）",
        "fb.edge_not_binary.detail": (
            "{muddy_pct:.1f}% 的像素位于 {low}..{high} 区间。"
            "边缘贴图通常为 0 或 1。模糊的边缘在渲染中会像脏点。"
        ),
        "fb.label.height":  "高度",
        "fb.label.edge":    "边缘",
        "fb.label.unknown": "未知",

        # TAB ANALYZE
        "tab_analyze.title":     "分析",
        "tab_analyze.btn_add":   "添加文件",
        "tab_analyze.btn_analyze":"全部分析",
        "tab_analyze.btn_save":  "保存已修复",
        "tab_analyze.btn_clear": "清空",
        "tab_analyze.empty.title": "点击 Add files 加载贴图",
        "tab_analyze.empty.hint":  "法线 / 粗糙度 / 金属度 / AO / ORM / 反照率",
        "tab_analyze.col.type":   "类型",
        "tab_analyze.col.file":   "文件",
        "tab_analyze.col.issues": "问题",
        "tab_analyze.col.size":   "大小",
        "tab_analyze.col.ok":     "OK",
        "tab_analyze.col.dash":   "—",
        "tab_analyze.dlg_pick":  "选择 PBR 贴图",
        "tab_analyze.log.no_maps":   "没有可分析的内容 — 请先加载贴图",
        "tab_analyze.log.loading":   "正在加载 {n} 个文件...",
        "tab_analyze.log.loaded":    "已加载：{done}/{total}",
        "tab_analyze.log.analyzing": "分析中...",
        "tab_analyze.log.analyzed":  "已分析：{done}/{total}",
        "tab_analyze.log.not_a_file":  "不是文件：{path}",
        "tab_analyze.log.not_an_image":"不是图片：{name}",
        "tab_analyze.log.open_fail":   "打开 {name} 失败：{err}",
        "tab_analyze.log.no_analyzer": "{name}：{mtype} 的分析器尚未就绪",
        "tab_analyze.log.analyze_fail":"{name}：分析失败：{err}",
        "tab_analyze.log.type_changed":"{name}：类型已改为 {type}",
        "tab_analyze.log.no_maps_to_save": "没有可保存的贴图",
        "tab_analyze.log.nothing_to_save": "没有可保存的内容",
        "tab_analyze.log.saved_one":   "{name}  （{bit}-bit）",
        "tab_analyze.log.save_fail":   "未保存 {name}：{err}",
        "tab_analyze.log.saved_total": "已保存：{saved}/{total} → {folder}",
        "tab_analyze.save.title":       "保存贴图",
        "tab_analyze.save.what":        "保存内容：",
        "tab_analyze.save.only_fixed":  "仅已修复的贴图（{n}）",
        "tab_analyze.save.bitness":     "位深：",
        "tab_analyze.save.bit8":        "8-bit（普通 PNG，体积更小）",
        "tab_analyze.save.bit16":       "16-bit（渐变平滑，适合法线/高度）",
        "tab_analyze.save.summary":     "共 {total} 张贴图  •  已修复 {fixed} 张",
        "tab_analyze.save.cancel":      "取消",
        "tab_analyze.save.confirm":     "保存",
        "tab_analyze.save.pick_folder": "保存到哪个文件夹？",

        # TAB SEAMLESS
        "tab_seamless.title":        "无缝",
        "tab_seamless.mode_label":   "模式：",
        "tab_seamless.btn_one":      "应用到所选",
        "tab_seamless.btn_all":      "应用到全部",
        "tab_seamless.btn_save":     "保存",
        "tab_seamless.empty.list":   "请在 Analyze 标签页加载贴图",
        "tab_seamless.empty.preview":"请在左侧选择贴图",
        "tab_seamless.before":       "处理前",
        "tab_seamless.after":        "处理后（预览）",
        "tab_seamless.mode_line":    "模式：{mode}",
        "tab_seamless.seam_ok":      "正常",
        "tab_seamless.seam_bad":     "接缝 {diff:.3f}",
        "tab_seamless.seam_info":    "处理前：LR={lr:.3f}  TB={tb:.3f}  最大={mx:.3f}",
        "tab_seamless.mode.mirror_blend.label": "镜像混合",
        "tab_seamless.mode.mirror_blend.desc":  "位移 + 镜像混合。简单，适用于反照率/粗糙度/AO。",
        "tab_seamless.mode.freq_sep.label":     "频率分离",
        "tab_seamless.mode.freq_sep.desc":      "频率分离。不模糊细节，适用于法线/高度。",
        "tab_seamless.mode.hipass.label":       "高通（GIMP）",
        "tab_seamless.mode.hipass.desc":        "GIMP 无缝平铺。可能出现叠加。",
        "tab_seamless.log.mode_changed": "{mode}",
        "tab_seamless.log.nothing_selected": "未选择任何内容",
        "tab_seamless.log.no_preview_map":   "未选择用于预览的贴图",
        "tab_seamless.log.applying":     "正在对 {n} 张贴图应用无缝（{mode}）...",
        "tab_seamless.log.applied_one":  "{name}：无缝 → 接缝 {diff:.3f}",
        "tab_seamless.log.applied":      "无缝应用完成：{ok}/{total}",
        "tab_seamless.log.no_seamless":  "没有应用过无缝的贴图",
        "tab_seamless.log.saved":        "已保存：{saved}/{total} → {folder}",
        "tab_seamless.log.saved_one":    "{name}",
        "tab_seamless.log.save_fail":    "{name}：{err}",
        "tab_seamless.log.pick_folder":  "无缝贴图保存到哪个文件夹？",

        # REPORT PANEL
        "panel.empty":           "请在左侧选择贴图",
        "panel.need_analyze":    "点击 Analyze All 获取报告",
        "panel.sev.ok":   "良好",
        "panel.sev.warn": "有警告",
        "panel.sev.fail": "有问题",
        "panel.all_passed":      "所有检查通过",
        "panel.issues_found":    "发现问题：{n}",
        "panel.raw_metrics":     "原始指标",
        "panel.issues_title":    "问题（{n}）",
        "panel.no_issues":       "未发现问题",
        "panel.no_data":         "（无数据）",
        "panel.fix_result.done":         "完成",
        "panel.fix_result.better":       "已改善（{before} → {after}）",
        "panel.fix_result.unchanged":    "无变化",
        "panel.fix_result.worse":        "变差了",
        "panel.fix_result.undo":         "撤销",
        "panel.fix_log":         "✓ {name}：{fix} → {before} → {after}",
        "panel.fix_fail":        "✗ 修复 '{fix}' 失败：{err}",
        "panel.refix_fail":      "✗ 修复后重新分析失败：{err}",
        "panel.no_analyzer":     "✗ 没有 {mtype} 的分析器",
        "panel.undo_log":        "↶ {name}：撤销 '{fix}'",

        # VERDICT
        "verdict.normal.mean_len":
            "向量长度低于正常（平均 {v:.2f}，应为 1.0）。"
            "贴图在生成或压缩时损坏。",
        "verdict.normal.bad_pct_fail":
            "{v:.1f}% 的像素向量长度异常（正常应低于 5%）。",
        "verdict.normal.bad_pct_warn":
            "向量长度轻微偏差：{v:.1f}% 的像素（正常应低于 1%）。",
        "verdict.normal.angle_fail":
            "平均向量偏离 (0,0,1) 达 {v:.1f}° — 贴图中烘焙了光照。",
        "verdict.normal.angle_warn":
            "平均法线轻微偏移 {v:.1f}°。",
        "verdict.normal.not_normal":
            "B 通道暗且平坦，R/G 几乎没有变化。这不是法线贴图 — 请检查文件。",
        "verdict.normal.broken_b":
            "B 通道退化：mean={bm:.2f}，std={bs:.2f}。"
            "Z 丢失但 R/G 正常 — 可恢复 B。",
        "verdict.rough.color":
            "贴图为彩色，但粗糙度应为灰度（通道差 {v:.3f}）。",
        "verdict.rough.dead":
            "贴图已死 — 整个范围压缩到窄带（std {v:.3f}，正常 > 0.06）。",
        "verdict.rough.low_var":
            "变化过少（std {v:.3f}，正常 > 0.06）。"
            "若表面均匀粗糙则无妨，否则应拉伸。",
        "verdict.rough.narrow":
            "范围被压缩：数值分布在 [{p1:.2f}..{p99:.2f}]，未覆盖 [0,1]。渲染会丢失对比。",
        "verdict.rough.noisy":
            "贴图噪声过多（std {v:.3f}）。看起来是 AI 生成后未平滑的噪声。",
        "verdict.metal.color":
            "贴图为彩色，但金属度应为灰度（通道差 {v:.3f}）。",
        "verdict.metal.muddy_fail":
            "{v:.0f}% 的像素位于中间区域（0.1..0.9）。"
            "金属度必须为二值：0 或 1。渲染无法判断金属位置。",
        "verdict.metal.muddy_warn":
            "{v:.0f}% 的像素位于中间区域。"
            "若是金属/电介质过渡边缘则属正常，否则应二值化。",
        "verdict.metal.all_zero":
            "{v:.1f}% 的像素 = 0。整张图都是电介质。若不应含金属则无妨。",
        "verdict.metal.all_one":
            "{v:.1f}% 的像素 = 1。整个模型都是金属。若确为如此则无妨。",
        "verdict.ao.color":
            "贴图为彩色，但 AO 应为灰度（通道差 {v:.3f}）。",
        "verdict.ao.dead":
            "贴图已死 — std {v:.3f}（正常 > 0.03）。AO 没有遮蔽任何东西。",
        "verdict.ao.low_var":
            "变化过少（std {v:.3f}，正常 > 0.05）。",
        "verdict.ao.dark":
            "过暗（mean {v:.2f}，{dp:.1f}% 的像素偏暗）。"
            "可能极性颠倒，或生成器阴影过重。",
        "verdict.ao.dark_short":
            "过暗（mean {v:.2f}）。可能极性颠倒，或生成器阴影过重。",
        "verdict.ao.light":
            "AO 几乎不可见（mean {v:.2f}）。几乎没有阴影。",
        "verdict.ao.narrow":
            "范围被压缩：数值分布在 [{p1:.2f}..{p99:.2f}]，未覆盖 [0,1]。AO 对比过弱。",
        "verdict.fb.unknown":
            "贴图类型未识别。请在左侧下拉菜单中手动选择 — 检查项取决于它。",
        "verdict.fb.color":
            "贴图为彩色，但 {label} 应为灰度（通道差 {v:.3f}）。",
        "verdict.fb.dead":
            "贴图已死 — std {v:.3f}（正常 > 0.02）。",
        "verdict.fb.low_var":
            "变化过少（std {v:.3f}，正常 > 0.04）。",
        "verdict.fb.narrow":
            "范围被压缩：数值分布在 [{p1:.2f}..{p99:.2f}]，未覆盖 [0,1]。",
        "verdict.fb.noisy":
            "噪声过多（std {v:.3f}）。看起来是 AI 生成后未平滑的噪声。",
        "verdict.fb.dark":
            "过暗（mean {v:.2f}）。",
        "verdict.fb.light":
            "过亮（mean {v:.2f}）。",
        "verdict.fb.edge_muddy":
            "{v:.0f}% 的像素位于中间区域 — 边缘通常为二值（0 或 1）。",

        # FIX DIALOG
        "dlg_fix.headline.done":       "很好！问题已解决",
        "dlg_fix.headline.better":     "已改善（{b} → {a} 个问题）",
        "dlg_fix.headline.partial":    "部分改善：{b} → {a} 个问题",
        "dlg_fix.headline.worse_iss":  "变差了：{b} → {a} 个问题",
        "dlg_fix.headline.unchanged":  "无变化",
        "dlg_fix.headline.worse":      "变差了",
        "dlg_fix.fix_line":            "修复：{label}",
        "dlg_fix.row_status":          "状态（问题）：",
        "dlg_fix.row_issues":          "问题：",
        "dlg_fix.ok":                  "OK",

        # INFO
        "info.tab.help":    "帮助",
        "info.tab.about":   "关于",
        "info.tab.support": "支持",
        "info.help_text": (
            "PBR Doctor — PBR 贴图诊断与修复。\n\n"
            "使用方法：\n"
            "1. 点击 Add files 加载贴图（法线 / 粗糙度 /\n"
            "   金属度 / AO / 反照率）。\n"
            "2. 点击 Analyze All — 程序会检查每张贴图，\n"
            "   并以交通灯显示：正常 / 警告 / 失败。\n"
            "3. 点击左侧贴图 — 右侧显示指标和带修复按钮的问题列表。\n"
            "4. 对每个问题点击修复。对话框会显示结果：\n"
            "   改善 / 无变化 / 变差。\n"
            "5. 撤销按钮可回退上一次修复。\n"
            "6. Save fixed — 导出结果（8-bit 或 16-bit）。\n\n"
            "检查内容：\n"
            "• 法线 — 烘焙光照、向量长度异常。\n"
            "• 粗糙度 — 死图、范围过窄、噪声。\n"
            "• 金属度、AO、无缝 — 开发中。\n\n"
            "提示：\n"
            "法线和高度贴图请始终保存为 16-bit —\n"
            "8-bit 在渐变上会出现色阶断层。\n"
        ),
        "info.about.version": "版本",
        "info.about.build":   "构建",
        "info.about.author":  "作者",
        "info.about.license": "许可",
        "info.about.desc": (
            "Albedolizer 系列的独立程序。\n"
            "用于 AI 生成后的 PBR 贴图诊断与修复。\n"
            "支持法线、粗糙度、金属度、AO、无缝。"
        ),
        "info.support.copied": "✓ 地址已复制到剪贴板",

        "wallets.support_title": "支持开发",
        "wallets.support_text":  "如果这个工具帮到了你，请作者喝杯咖啡。",
    },
}