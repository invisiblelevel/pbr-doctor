"""
core/i18n.py — локализация PBR Doctor.

Три языка: ru / en / zh (упрощённый, zh-Hans).
"""

from __future__ import annotations

import locale
import os
import sys


SUPPORTED = ("ru", "en", "zh")
DEFAULT_LANG = "en"

_CURRENT = {"lang": None}


def set_lang(lang: str):
    if lang not in SUPPORTED:
        lang = DEFAULT_LANG
    _CURRENT["lang"] = lang


def get_lang() -> str:
    if _CURRENT["lang"] is None:
        _CURRENT["lang"] = get_system_lang()
    return _CURRENT["lang"]


def get_system_lang() -> str:
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

    if sys.platform == "win32":
        try:
            import ctypes
            windll = ctypes.windll.kernel32
            lang_id = windll.GetUserDefaultUILanguage()
            primary = lang_id & 0xFF
            if primary == 0x19:
                return "ru"
            if primary == 0x04:
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


def t(key: str, lang: str = None, **kw) -> str:
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
            return s
    return s


TEXTS = {

    "ru": {

        "app.title":       "PBR Doctor",
        "app.subtitle":    "Диагностика и ремонт PBR-карт",
        "app.tagline":     "Анализ и ремонт PBR-карт",
        "app.log":         "Лог",
        "app.info":        "Инфо",
        "app.lang":        "Язык",

        "log.ready":       "PBR Doctor 1.1.0 готов к работе",
        "log.hint_add":    "Нажми Add files, чтобы загрузить карты",

        "map.albedo":      "Albedo / BaseColor",
        "map.normal":      "Normal",
        "map.roughness":   "Roughness",
        "map.metallic":    "Metallic",
        "map.ao":          "Ambient Occlusion",
        "map.orm":         "ORM (R=AO G=Rough B=Metal)",
        "map.height":      "Height / Displacement",
        "map.edge":        "Edge / Outline",
        "map.unknown":     "Unknown",

        "detected.name":         "по имени",
        "detected.content":      "по содержимому",
        "detected.name+content": "имя + содержимое",
        "detected.fallback":     "не определено",
        "detected.manual":       "вручную",

        "sev.ok":   "OK",
        "sev.warn": "Warning",
        "sev.fail": "Fail",

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

        "err.unknown_fix":        "Неизвестный фикс: {fix_id}",
        "err.fix_not_implemented":"Фикс '{fix_id}' не реализован",
        "err.open_file":          "Не удалось открыть файл: {path}",
        "err.open_reason":        "Причина: {reason}",
        "err.open_hint":          "Проверь: длину пути (>260 символов?), права доступа, свободное место на диске, целостность файла.",
        "err.seamless_mode":      "Неизвестный режим seamless: {mode}",
        "err.orm_bad_fix_id":     "Неверный fix_id для ORM: {fix_id}",
        "err.orm_forbidden_fix":  "Фикс '{op}' запрещён для ORM — он ломает каналы.",
        "err.orm_unknown_channel":"Неизвестный канал: {channel}",

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
        "tab_analyze.log.deleted":     "✗ {name}: удалено из списка",
        "tab_analyze.delete_tooltip":  "Удалить из списка",

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
        "panel.fix_result.metrics_better": "Лучше ({n} метрик)",
        "panel.fix_result.metrics_worse":  "Хуже ({n} метрик)",
        "panel.profile_label":   "Профиль текстуры",
        "panel.profile_changed": "Профиль изменён на «{profile}»",
        "panel.fixes_reset":     "Сбросить все фиксы",
        "panel.fixes_reset_log": "↺ {name}: все фиксы сброшены",

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

        "dlg_fix.headline.done":       "Отлично! Проблема устранена",
        "dlg_fix.headline.better":     "Стало лучше ({b} → {a} issues)",
        "dlg_fix.headline.partial":    "Стало лучше (частично): {b} → {a} issues",
        "dlg_fix.headline.worse_iss":  "Стало хуже: {b} → {a} issues",
        "dlg_fix.headline.unchanged":  "Без изменений",
        "dlg_fix.headline.worse":      "Стало хуже",
        "dlg_fix.headline.metrics_better": "Стало лучше ({n} метрик улучшилось)",
        "dlg_fix.headline.metrics_worse":  "Стало хуже ({n} метрик ухудшилось)",
        "dlg_fix.headline.mixed":          "Смешанный результат ({good} лучше, {bad} хуже)",
        "dlg_fix.row_metrics":             "Показатели:",
        "dlg_fix.fix_line":            "Фикс: {label}",
        "dlg_fix.row_status":          "Статус (issues):",
        "dlg_fix.row_issues":          "Issues:",
        "dlg_fix.ok":                  "OK",

        "metric.std_l":        "Контраст деталей",
        "metric.soapy_pct":    "Мыльные зоны",
        "metric.p1_l":         "Яркость теней",
        "metric.p99_l":        "Засветы",
        "metric.mean_s":       "Насыщенность цвета",
        "metric.color_spread": "Перекос в оттенок",
        "metric.mean_length":  "Длина векторов",
        "metric.bad_pct":      "Битые длины",
        "metric.angle":        "Угол наклона",
        "metric.std":          "Разброс яркости",
        "metric.span":         "Диапазон яркости",
        "metric.muddy_pct":    "Серая зона",
        "metric.mean":         "Средняя яркость",

        "metric.std_l.norm":        "(норма > 30)",
        "metric.soapy_pct.norm":    "(норма < 20%)",
        "metric.p1_l.norm":         "(норма ≥ 10)",
        "metric.p99_l.norm":        "(норма ≤ 250)",
        "metric.mean_s.norm":       "(норма 0.15–0.75)",
        "metric.color_spread.norm": "(норма ≤ 15)",
        "metric.mean_length.norm":  "(норма ≈ 1.0)",
        "metric.bad_pct.norm":      "(норма < 5%)",
        "metric.angle.norm":        "(норма < 5°)",
        "metric.std.norm":          "(норма > 0.06)",
        "metric.span.norm":         "(норма > 0.4)",
        "metric.muddy_pct.norm":    "(норма < 5%)",
        "metric.mean.norm":         "",

        "info.tab.help":    "Помощь",
        "info.tab.about":   "О программе",
        "info.tab.support": "Поддержать",
        "info.help_text": (
            "PBR Doctor — диагностика и ремонт PBR-карт.\n\n"
            "КАК РАБОТАТЬ:\n"
            "1. Нажми Add files и загрузи карты.\n"
            "2. Нажми Analyze All — прога проверит каждую карту.\n"
            "3. Кликни по карте слева — справа метрики и issues.\n"
            "4. Жми Fix. Появится диалог с результатом.\n"
            "5. Undo откатит последний фикс.\n"
            "6. Save fixed — сохрани результат (8 / 16-bit).\n\n"
            "СОВЕТ: normal и height сохраняй в 16-bit."
        ),
        "info.about.version": "Версия",
        "info.about.build":   "Сборка",
        "info.about.author":  "Автор",
        "info.about.license": "Лицензия",
        "info.about.desc": (
            "Отдельная программа из семейства Albedolizer.\n"
            "Диагностика и ремонт PBR-карт после AI-генерации."
        ),
        "info.support.copied": "✓ Адрес скопирован в буфер",
        "wallets.support_title": "Поддержать разработку",
        "wallets.support_text":  "Бро, если зашло, закинь дяде на папиросы.",

        # ─── ALBEDO ───
        "albedo.default_profile_warn":
            "Профиль текстуры не распознан по имени файла — "
            "использую «{profile}».",
        "albedo.profile_line": "Профиль: {profile}",

        "albedo.soapy.title":  "Мыльные зоны ({pct:.0f}%)",
        "albedo.soapy.detail": (
            "{pct:.0f}% пикселей выглядят «мыльно» — локальная "
            "детализация сильно ниже медианы."
        ),
        "albedo.dark.title":  "Недосвет (p1={p1:.0f}, порог {thr})",
        "albedo.dark.detail": (
            "Тёмные зоны уходят ниже порога профиля «{profile}» "
            "(p1={p1:.0f}, норма ≥ {thr})."
        ),
        "albedo.light.title":  "Пересвет (p99={p99:.0f}, порог {thr})",
        "albedo.light.detail": (
            "Светлые зоны выходят за порог профиля «{profile}» "
            "(p99={p99:.0f}, норма ≤ {thr})."
        ),
        "albedo.flat_contrast.title":  "Плоский контраст (std={std:.1f})",
        "albedo.flat_contrast.detail": (
            "Разброс яркости L-канала низкий (std={std:.1f})."
        ),
        "albedo.hard_contrast.title":  "Зашкаливающий контраст (std={std:.1f})",
        "albedo.hard_contrast.detail": (
            "Разброс яркости L-канала очень высокий (std={std:.1f})."
        ),
        "albedo.flat_color.title":  "Плоская насыщенность (S={sat:.3f})",
        "albedo.flat_color.detail": (
            "Средняя насыщенность HSV всего {sat:.3f}."
        ),
        "albedo.oversaturated.title":  "Перенасыщенность (S={sat:.3f})",
        "albedo.oversaturated.detail": (
            "Средняя насыщенность HSV {sat:.3f} — цвета «кислотные»."
        ),
        "albedo.color_cast.title":  "Цветовой сдвиг (Δ={delta:.0f})",
        "albedo.color_cast.detail": (
            "Разброс среднего цвета между каналами R/G/B = {delta:.0f} "
            "(норма ≤ 15)."
        ),

        "albedo.profile.metal":          "Металл",
        "albedo.profile.rust":           "Ржавчина",
        "albedo.profile.oxidized_metal": "Окисленный металл",
        "albedo.profile.patina":         "Патина",
        "albedo.profile.brass":          "Латунь",
        "albedo.profile.aluminum":       "Алюминий",
        "albedo.profile.copper":         "Медь",
        "albedo.profile.wood":           "Дерево",
        "albedo.profile.leaves":         "Листва",
        "albedo.profile.moss":           "Мох",
        "albedo.profile.organic":        "Органика",
        "albedo.profile.grass":          "Трава",
        "albedo.profile.bark":           "Кора",
        "albedo.profile.tile":           "Плитка",
        "albedo.profile.gravel":         "Гравий",
        "albedo.profile.coal":           "Уголь",
        "albedo.profile.roof_tiles":     "Черепица",
        "albedo.profile.stone":          "Камень",
        "albedo.profile.concrete":       "Бетон",
        "albedo.profile.brick":          "Кирпич",
        "albedo.profile.ground":         "Земля",
        "albedo.profile.asphalt":        "Асфальт",
        "albedo.profile.marble":         "Мрамор",
        "albedo.profile.sand":           "Песок",
        "albedo.profile.clay":           "Глина",
        "albedo.profile.granite":        "Гранит",
        "albedo.profile.stucco":         "Штукатурка",
        "albedo.profile.gemstone":       "Самоцвет",
        "albedo.profile.plastic":        "Пластик",
        "albedo.profile.rubber":         "Резина",
        "albedo.profile.glass":          "Стекло",
        "albedo.profile.ceramic":        "Керамика",
        "albedo.profile.painted_metal":  "Крашеный металл",
        "albedo.profile.carbon":         "Карбон",
        "albedo.profile.cardboard":      "Картон",
        "albedo.profile.water":          "Вода",
        "albedo.profile.mud":            "Грязь",
        "albedo.profile.snow":           "Снег",
        "albedo.profile.ice":            "Лёд",
        "albedo.profile.cotton":         "Хлопок",
        "albedo.profile.wool":           "Шерсть",
        "albedo.profile.silk":           "Шёлк",
        "albedo.profile.denim":          "Джинса",
        "albedo.profile.carpet":         "Ковёр",
        "albedo.profile.velvet":         "Бархат",
        "albedo.profile.leather":        "Кожа",
        "albedo.profile.fur":            "Мех",
        "albedo.profile.skin":           "Кожа (тело)",
        "albedo.profile.scales":         "Чешуя",
        "albedo.profile.bone":           "Кость",

        "fix.auto_correct":    "Авто-коррекция",
        "fix.clahe_only":      "Только CLAHE",
        "fix.auto_levels_only":"Только авто-уровни",
        "fix.remove_soap":     "Убрать мыльность",
        "fix.saturate_15":     "+15% насыщенности",
        "fix.saturate_30":     "+30% насыщенности",
        "fix.desaturate_15":   "−15% насыщенности",
        "fix.white_balance":   "Баланс белого",
        "fix.decontrast":      "Снизить контраст",
        "fix.remove_color_cast":"Убрать цветовой сдвиг",

        "verdict.albedo.soapy":
            "{pct:.0f}% пикселей выглядят «мыльно» — детализация ниже нормы.",
        "verdict.albedo.dark":
            "Тёмные зоны ниже порога (p1={p1:.0f}, порог {thr}).",
        "verdict.albedo.light":
            "Светлые зоны выше порога (p99={p99:.0f}, порог {thr}).",
        "verdict.albedo.flat_contrast":
            "Плоский контраст (std={std:.1f}). Детали слабо читаются.",
        "verdict.albedo.hard_contrast":
            "Зашкаливающий контраст (std={std:.1f}).",
        "verdict.albedo.flat_color":
            "Бледные цвета (S={sat:.3f}).",
        "verdict.albedo.oversaturated":
            "Перенасыщенные цвета (S={sat:.3f}).",
        "verdict.albedo.color_cast":
            "Цветовой сдвиг (Δ={delta:.0f}). Вся карта ушла в один оттенок.",
    },

    "en": {

        "app.title":       "PBR Doctor",
        "app.subtitle":    "Diagnose and repair PBR maps",
        "app.tagline":     "Analyze & repair PBR maps",
        "app.log":         "Log",
        "app.info":        "Info",
        "app.lang":        "Language",

        "log.ready":       "PBR Doctor 1.1.0 is ready",
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
        "err.open_hint":          "Check: path length, permissions, disk space, file integrity.",
        "err.seamless_mode":      "Unknown seamless mode: {mode}",
        "err.orm_bad_fix_id":     "Bad fix_id for ORM: {fix_id}",
        "err.orm_forbidden_fix":  "Fix '{op}' is forbidden for ORM.",
        "err.orm_unknown_channel":"Unknown channel: {channel}",

        "normal.not_a_normal.title":  "This doesn't look like a normal map",
        "normal.not_a_normal.detail": (
            "B channel averages {b_mean:.2f}, std={b_std:.3f}. "
            "R/G barely vary (r_std={r_std:.3f}, g_std={g_std:.3f})."
        ),
        "normal.broken_b.title":  "B channel is degenerate (flat)",
        "normal.broken_b.detail": (
            "Mean vector length {mean_len:.3f}. B channel: "
            "mean={b_mean:.3f}, std={b_std:.3f}."
        ),
        "normal.baked.title":  "Baked light (shift {angle:.1f}°)",
        "normal.baked.detail": (
            "Mean normal vector is tilted from (0,0,1) by {angle:.1f}°."
        ),
        "normal.baked_mild.title":  "Slight mean-normal shift ({angle:.1f}°)",
        "normal.baked_mild.detail": (
            "Mean vector is tilted by {angle:.1f}°."
        ),
        "normal.bad_len.title":  "Broken vector lengths ({bad_pct:.1f}% of pixels)",
        "normal.bad_len.detail": (
            "{bad_pct:.1f}% of pixels have length outside [0.9, 1.1]."
        ),
        "normal.bad_len_mild.title":  "Minor length deviations ({bad_pct:.1f}%)",
        "normal.bad_len_mild.detail": (
            "{bad_pct:.1f}% of pixels outside [0.9, 1.1]."
        ),

        "rough.not_grayscale.title":  "Roughness is not grayscale",
        "rough.not_grayscale.detail": (
            "R/G/B channels differ (std={channel_std:.3f})."
        ),
        "rough.dead.title":  "Dead map (std={std:.3f})",
        "rough.dead.detail": (
            "Value spread is almost zero. {mid_pct:.1f}% pixels in mid zone."
        ),
        "rough.low_var.title":  "Low variation (std={std:.3f})",
        "rough.low_var.detail": "Spread is below normal.",
        "rough.narrow.title":  "Narrow range (span={span:.2f})",
        "rough.narrow.detail": (
            "Values only span [{p1:.2f}, {p99:.2f}] out of [0, 1]."
        ),
        "rough.noisy.title":  "Too noisy (std={std:.3f})",
        "rough.noisy.detail": "Spread is off the charts.",

        "metal.not_grayscale.title":  "Metallic is not grayscale",
        "metal.not_grayscale.detail": (
            "R/G/B channels differ (std={channel_std:.3f})."
        ),
        "metal.muddy.title":  "Gradients in the mid zone ({muddy_pct:.1f}%)",
        "metal.muddy.detail": (
            "{muddy_pct:.1f}% of pixels in range {low}..{high}."
        ),
        "metal.muddy_mild.title":  "Some gradients ({muddy_pct:.1f}%)",
        "metal.muddy_mild.detail": (
            "{muddy_pct:.1f}% of pixels in the mid zone."
        ),
        "metal.all_zero.title":  "No metal (all zeros)",
        "metal.all_zero.detail": "{zero_pct:.1f}% of pixels = 0.",
        "metal.all_one.title":  "All metal (all ones)",
        "metal.all_one.detail": "{one_pct:.1f}% of pixels = 1.",

        "ao.not_grayscale.title":  "AO is not grayscale",
        "ao.not_grayscale.detail": (
            "R/G/B channels differ (std={channel_std:.3f})."
        ),
        "ao.dead.title":  "Dead map (std={std:.3f})",
        "ao.dead.detail": "Spread is almost zero.",
        "ao.low_var.title":  "Low variation (std={std:.3f})",
        "ao.low_var.detail": "Spread is below normal.",
        "ao.too_dark.title":  "AO is too dark (mean={mean:.2f})",
        "ao.too_dark.detail": (
            "Mean brightness {mean:.2f} ({dark_pct:.1f}% pixels dark)."
        ),
        "ao.too_light.title":  "AO is almost invisible (mean={mean:.2f})",
        "ao.too_light.detail": "Mean brightness {mean:.2f}.",
        "ao.narrow.title":  "Narrow range (span={span:.2f})",
        "ao.narrow.detail": (
            "Values only span [{p1:.2f}, {p99:.2f}] out of [0, 1]."
        ),

        "orm.bad_shape.title":  "[ORM] Map is not RGB",
        "orm.bad_shape.detail": "ORM must be RGB.",
        "orm.grayscale.title":  "[ORM] Map is grayscale",
        "orm.grayscale.detail": "All channels identical.",
        "orm.metal_muddy.title":  "[B] Metallic: not binary",
        "orm.metal_muddy.detail": "{mid_pct:.0f}% pixels in mid zone.",
        "orm.fix_all.title":  "[ORM] Fix everything",
        "orm.fix_all.detail": "Apply best fix to every channel.",
        "orm.channel.R": "AO",
        "orm.channel.G": "Roughness",
        "orm.channel.B": "Metallic",
        "orm.wrap.R": "[R] AO: {text}",
        "orm.wrap.G": "[G] Roughness: {text}",
        "orm.wrap.B": "[B] Metallic: {text}",

        "fb.bad_shape.title":  "{label}: map is not RGB",
        "fb.bad_shape.detail": "Expected RGB array.",
        "fb.unknown.title":  "Map type undetected",
        "fb.unknown.detail": (
            "Auto-detect couldn't identify the map. It {kind}."
        ),
        "fb.unknown.kind_gray":  "looks grayscale",
        "fb.unknown.kind_color": "looks like a color map",
        "fb.dead_unknown.title":  "Map barely varies",
        "fb.dead_unknown.detail": "std {std:.3f}.",
        "fb.not_grayscale.title":  "{label} is not grayscale",
        "fb.not_grayscale.detail": (
            "R/G/B channels differ (std={channel_std:.3f})."
        ),
        "fb.dead.title":  "{label}: dead map (std={std:.3f})",
        "fb.dead.detail": "Spread is almost zero.",
        "fb.low_var.title":  "{label}: low variation (std={std:.3f})",
        "fb.low_var.detail": "Spread is below normal.",
        "fb.narrow.title":  "{label}: narrow range (span={span:.2f})",
        "fb.narrow.detail": (
            "Values only span [{p1:.2f}, {p99:.2f}] out of [0, 1]."
        ),
        "fb.too_dark.title":  "{label}: too dark (mean={mean:.2f})",
        "fb.too_dark.detail": "Mean brightness {mean:.2f}.",
        "fb.too_light.title":  "{label}: too light (mean={mean:.2f})",
        "fb.too_light.detail": "Mean brightness {mean:.2f}.",
        "fb.noisy.title":  "{label}: too noisy (std={std:.3f})",
        "fb.noisy.detail": "Spread is off the charts.",
        "fb.edge_not_binary.title":  "Edge is not binary ({muddy_pct:.1f}% in mid zone)",
        "fb.edge_not_binary.detail": (
            "{muddy_pct:.1f}% of pixels in range {low}..{high}."
        ),
        "fb.label.height":  "Height",
        "fb.label.edge":    "Edge",
        "fb.label.unknown": "Unknown",

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
        "tab_analyze.log.no_maps":   "Nothing to analyze.",
        "tab_analyze.log.loading":   "Loading {n} files...",
        "tab_analyze.log.loaded":    "Loaded: {done}/{total}",
        "tab_analyze.log.analyzing": "Analyzing...",
        "tab_analyze.log.analyzed":  "Analyzed: {done}/{total}",
        "tab_analyze.log.not_a_file":  "Not a file: {path}",
        "tab_analyze.log.not_an_image":"Not an image: {name}",
        "tab_analyze.log.open_fail":   "Failed to open {name}: {err}",
        "tab_analyze.log.no_analyzer": "{name}: analyzer for {mtype} not ready",
        "tab_analyze.log.analyze_fail":"{name}: analysis failed: {err}",
        "tab_analyze.log.type_changed":"{name}: type changed to {type}",
        "tab_analyze.log.no_maps_to_save": "No maps to save",
        "tab_analyze.log.nothing_to_save": "Nothing to save",
        "tab_analyze.log.saved_one":   "{name}  ({bit}-bit)",
        "tab_analyze.log.save_fail":   "Could not save {name}: {err}",
        "tab_analyze.log.saved_total": "Saved: {saved}/{total} → {folder}",
        "tab_analyze.save.title":       "Save maps",
        "tab_analyze.save.what":        "What to save:",
        "tab_analyze.save.only_fixed":  "Only maps with fixes ({n})",
        "tab_analyze.save.bitness":     "Bit depth:",
        "tab_analyze.save.bit8":        "8-bit",
        "tab_analyze.save.bit16":       "16-bit",
        "tab_analyze.save.summary":     "Total: {total}  •  With fixes: {fixed}",
        "tab_analyze.save.cancel":      "Cancel",
        "tab_analyze.save.confirm":     "Save",
        "tab_analyze.save.pick_folder": "Where to save?",
        "tab_analyze.log.deleted":     "✗ {name}: removed from list",
        "tab_analyze.delete_tooltip":  "Remove from list",

        "tab_seamless.title":        "Seamless",
        "tab_seamless.mode_label":   "Mode:",
        "tab_seamless.btn_one":      "To selected",
        "tab_seamless.btn_all":      "To all",
        "tab_seamless.btn_save":     "Save",
        "tab_seamless.empty.list":   "Load maps on Analyze tab",
        "tab_seamless.empty.preview":"Pick a map on the left",
        "tab_seamless.before":       "BEFORE",
        "tab_seamless.after":        "AFTER",
        "tab_seamless.mode_line":    "Mode: {mode}",
        "tab_seamless.seam_ok":      "ok",
        "tab_seamless.seam_bad":     "seam {diff:.3f}",
        "tab_seamless.seam_info":    "Before: LR={lr:.3f}  TB={tb:.3f}  max={mx:.3f}",
        "tab_seamless.mode.mirror_blend.label": "Mirror-blend",
        "tab_seamless.mode.mirror_blend.desc":  "Shift + mirror blend.",
        "tab_seamless.mode.freq_sep.label":     "Freq-separation",
        "tab_seamless.mode.freq_sep.desc":      "Frequency separation.",
        "tab_seamless.mode.hipass.label":       "Hi-pass (GIMP)",
        "tab_seamless.mode.hipass.desc":        "GIMP tile-seamless.",
        "tab_seamless.log.mode_changed": "{mode}",
        "tab_seamless.log.nothing_selected": "Nothing selected",
        "tab_seamless.log.no_preview_map":   "No map selected",
        "tab_seamless.log.applying":     "Seamless ({mode}) for {n} maps...",
        "tab_seamless.log.applied_one":  "{name}: seamless → seam {diff:.3f}",
        "tab_seamless.log.applied":      "Seamless applied: {ok}/{total}",
        "tab_seamless.log.no_seamless":  "No maps with seamless",
        "tab_seamless.log.saved":        "Saved: {saved}/{total} → {folder}",
        "tab_seamless.log.saved_one":    "{name}",
        "tab_seamless.log.save_fail":    "{name}: {err}",
        "tab_seamless.log.pick_folder":  "Where to save seamless maps?",

        "panel.empty":           "Pick a map on the left",
        "panel.need_analyze":    "Click Analyze All",
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
        "panel.refix_fail":      "✗ Re-analysis failed: {err}",
        "panel.no_analyzer":     "✗ No analyzer for {mtype}",
        "panel.undo_log":        "↶ {name}: undo '{fix}'",
        "panel.fix_result.metrics_better": "Better ({n} metrics)",
        "panel.fix_result.metrics_worse":  "Worse ({n} metrics)",
        "panel.profile_label":   "Texture profile",
        "panel.profile_changed": "Profile changed to \"{profile}\"",
        "panel.fixes_reset":     "Reset all fixes",
        "panel.fixes_reset_log": "↺ {name}: all fixes reset",

        "verdict.normal.mean_len":
            "Vector lengths below normal ({v:.2f} instead of 1.0).",
        "verdict.normal.bad_pct_fail":
            "{v:.1f}% pixels have wrong vector length.",
        "verdict.normal.bad_pct_warn":
            "Minor length deviations: {v:.1f}% pixels.",
        "verdict.normal.angle_fail":
            "Mean vector tilted from (0,0,1) by {v:.1f}°.",
        "verdict.normal.angle_warn":
            "Slight mean-normal shift of {v:.1f}°.",
        "verdict.normal.not_normal":
            "This isn't a normal map.",
        "verdict.normal.broken_b":
            "B channel degenerate: mean={bm:.2f}, std={bs:.2f}.",

        "verdict.rough.color":
            "Map is colored, should be grayscale (spread {v:.3f}).",
        "verdict.rough.dead":
            "Map is dead (std {v:.3f}).",
        "verdict.rough.low_var":
            "Low variation (std {v:.3f}).",
        "verdict.rough.narrow":
            "Narrow range: [{p1:.2f}..{p99:.2f}].",
        "verdict.rough.noisy":
            "Too noisy (std {v:.3f}).",

        "verdict.metal.color":
            "Map is colored, should be grayscale (spread {v:.3f}).",
        "verdict.metal.muddy_fail":
            "{v:.0f}% pixels in mid zone.",
        "verdict.metal.muddy_warn":
            "{v:.0f}% pixels in mid zone.",
        "verdict.metal.all_zero":
            "{v:.1f}% pixels = 0.",
        "verdict.metal.all_one":
            "{v:.1f}% pixels = 1.",

        "verdict.ao.color":
            "Map is colored, should be grayscale.",
        "verdict.ao.dead":
            "Map is dead (std {v:.3f}).",
        "verdict.ao.low_var":
            "Low variation (std {v:.3f}).",
        "verdict.ao.dark":
            "Too dark (mean {v:.2f}, {dp:.1f}% dark).",
        "verdict.ao.dark_short":
            "Too dark (mean {v:.2f}).",
        "verdict.ao.light":
            "AO almost invisible (mean {v:.2f}).",
        "verdict.ao.narrow":
            "Narrow range: [{p1:.2f}..{p99:.2f}].",

        "verdict.fb.unknown":
            "Map type undetected.",
        "verdict.fb.color":
            "Map is colored, {label} should be grayscale.",
        "verdict.fb.dead":
            "Map is dead (std {v:.3f}).",
        "verdict.fb.low_var":
            "Low variation (std {v:.3f}).",
        "verdict.fb.narrow":
            "Narrow range: [{p1:.2f}..{p99:.2f}].",
        "verdict.fb.noisy":
            "Too noisy (std {v:.3f}).",
        "verdict.fb.dark":
            "Too dark (mean {v:.2f}).",
        "verdict.fb.light":
            "Too light (mean {v:.2f}).",
        "verdict.fb.edge_muddy":
            "{v:.0f}% pixels in mid zone.",

        "dlg_fix.headline.done":       "Issue resolved",
        "dlg_fix.headline.better":     "Improved ({b} → {a} issues)",
        "dlg_fix.headline.partial":    "Partially improved: {b} → {a}",
        "dlg_fix.headline.worse_iss":  "Got worse: {b} → {a}",
        "dlg_fix.headline.unchanged":  "No change",
        "dlg_fix.headline.worse":      "Got worse",
        "dlg_fix.headline.metrics_better": "Improved ({n} metrics better)",
        "dlg_fix.headline.metrics_worse":  "Worse ({n} metrics worse)",
        "dlg_fix.headline.mixed":          "Mixed result",
        "dlg_fix.row_metrics":             "Metrics:",
        "dlg_fix.fix_line":            "Fix: {label}",
        "dlg_fix.row_status":          "Status:",
        "dlg_fix.row_issues":          "Issues:",
        "dlg_fix.ok":                  "OK",

        "metric.std_l":        "Detail contrast",
        "metric.soapy_pct":    "Soapy zones",
        "metric.p1_l":         "Shadow brightness",
        "metric.p99_l":        "Highlights",
        "metric.mean_s":       "Color saturation",
        "metric.color_spread": "Color cast",
        "metric.mean_length":  "Vector length",
        "metric.bad_pct":      "Broken lengths",
        "metric.angle":        "Tilt angle",
        "metric.std":          "Brightness spread",
        "metric.span":         "Brightness range",
        "metric.muddy_pct":    "Mid zone",
        "metric.mean":         "Average brightness",

        "metric.std_l.norm":        "(normal > 30)",
        "metric.soapy_pct.norm":    "(normal < 20%)",
        "metric.p1_l.norm":         "(normal ≥ 10)",
        "metric.p99_l.norm":        "(normal ≤ 250)",
        "metric.mean_s.norm":       "(normal 0.15–0.75)",
        "metric.color_spread.norm": "(normal ≤ 15)",
        "metric.mean_length.norm":  "(normal ≈ 1.0)",
        "metric.bad_pct.norm":      "(normal < 5%)",
        "metric.angle.norm":        "(normal < 5°)",
        "metric.std.norm":          "(normal > 0.06)",
        "metric.span.norm":         "(normal > 0.4)",
        "metric.muddy_pct.norm":    "(normal < 5%)",
        "metric.mean.norm":         "",

        "info.tab.help":    "Help",
        "info.tab.about":   "About",
        "info.tab.support": "Support",
        "info.help_text": (
            "PBR Doctor — diagnose and repair PBR maps.\n\n"
            "HOW TO USE:\n"
            "1. Add files and load maps.\n"
            "2. Analyze All.\n"
            "3. Click a map to see details.\n"
            "4. Fix.\n"
            "5. Undo rolls back.\n"
            "6. Save fixed (8 / 16-bit).\n\n"
            "TIP: normal and height — always 16-bit."
        ),
        "info.about.version": "Version",
        "info.about.build":   "Build",
        "info.about.author":  "Author",
        "info.about.license": "License",
        "info.about.desc": (
            "A standalone app from the Albedolizer family."
        ),
        "info.support.copied": "✓ Address copied",
        "wallets.support_title": "Support development",
        "wallets.support_text":  "Bro, if this helped, toss the dev a coin.",

        # ─── ALBEDO ───
        "albedo.default_profile_warn":
            "Texture profile not detected — using \"{profile}\".",
        "albedo.profile_line": "Profile: {profile}",

        "albedo.soapy.title":  "Soapy zones ({pct:.0f}%)",
        "albedo.soapy.detail": (
            "{pct:.0f}% of pixels look soapy."
        ),
        "albedo.dark.title":  "Underexposed (p1={p1:.0f}, threshold {thr})",
        "albedo.dark.detail": (
            "Dark zones below threshold (p1={p1:.0f}, normal ≥ {thr})."
        ),
        "albedo.light.title":  "Overexposed (p99={p99:.0f}, threshold {thr})",
        "albedo.light.detail": (
            "Bright zones exceed threshold (p99={p99:.0f}, normal ≤ {thr})."
        ),
        "albedo.flat_contrast.title":  "Flat contrast (std={std:.1f})",
        "albedo.flat_contrast.detail": (
            "Luminance spread is low (std={std:.1f})."
        ),
        "albedo.hard_contrast.title":  "Extreme contrast (std={std:.1f})",
        "albedo.hard_contrast.detail": (
            "Luminance spread is very high (std={std:.1f})."
        ),
        "albedo.flat_color.title":  "Flat saturation (S={sat:.3f})",
        "albedo.flat_color.detail": (
            "Mean HSV saturation is only {sat:.3f}."
        ),
        "albedo.oversaturated.title":  "Oversaturated (S={sat:.3f})",
        "albedo.oversaturated.detail": (
            "Mean HSV saturation {sat:.3f}."
        ),
        "albedo.color_cast.title":  "Color cast (Δ={delta:.0f})",
        "albedo.color_cast.detail": (
            "Mean R/G/B spread is {delta:.0f} (normal ≤ 15)."
        ),

        "albedo.profile.metal":          "Metal",
        "albedo.profile.rust":           "Rust",
        "albedo.profile.oxidized_metal": "Oxidized metal",
        "albedo.profile.patina":         "Patina",
        "albedo.profile.brass":          "Brass",
        "albedo.profile.aluminum":       "Aluminum",
        "albedo.profile.copper":         "Copper",
        "albedo.profile.wood":           "Wood",
        "albedo.profile.leaves":         "Leaves",
        "albedo.profile.moss":           "Moss",
        "albedo.profile.organic":        "Organic",
        "albedo.profile.grass":          "Grass",
        "albedo.profile.bark":           "Bark",
        "albedo.profile.tile":           "Tile",
        "albedo.profile.gravel":         "Gravel",
        "albedo.profile.coal":           "Coal",
        "albedo.profile.roof_tiles":     "Roof tiles",
        "albedo.profile.stone":          "Stone",
        "albedo.profile.concrete":       "Concrete",
        "albedo.profile.brick":          "Brick",
        "albedo.profile.ground":         "Ground",
        "albedo.profile.asphalt":        "Asphalt",
        "albedo.profile.marble":         "Marble",
        "albedo.profile.sand":           "Sand",
        "albedo.profile.clay":           "Clay",
        "albedo.profile.granite":        "Granite",
        "albedo.profile.stucco":         "Stucco",
        "albedo.profile.gemstone":       "Gemstone",
        "albedo.profile.plastic":        "Plastic",
        "albedo.profile.rubber":         "Rubber",
        "albedo.profile.glass":          "Glass",
        "albedo.profile.ceramic":        "Ceramic",
        "albedo.profile.painted_metal":  "Painted metal",
        "albedo.profile.carbon":         "Carbon",
        "albedo.profile.cardboard":      "Cardboard",
        "albedo.profile.water":          "Water",
        "albedo.profile.mud":            "Mud",
        "albedo.profile.snow":           "Snow",
        "albedo.profile.ice":            "Ice",
        "albedo.profile.cotton":         "Cotton",
        "albedo.profile.wool":           "Wool",
        "albedo.profile.silk":           "Silk",
        "albedo.profile.denim":          "Denim",
        "albedo.profile.carpet":         "Carpet",
        "albedo.profile.velvet":         "Velvet",
        "albedo.profile.leather":        "Leather",
        "albedo.profile.fur":            "Fur",
        "albedo.profile.skin":           "Skin",
        "albedo.profile.scales":         "Scales",
        "albedo.profile.bone":           "Bone",

        "fix.auto_correct":    "Auto-correct",
        "fix.clahe_only":      "CLAHE only",
        "fix.auto_levels_only":"Auto-levels only",
        "fix.remove_soap":     "Remove soapiness",
        "fix.saturate_15":     "+15% saturation",
        "fix.saturate_30":     "+30% saturation",
        "fix.desaturate_15":   "−15% saturation",
        "fix.white_balance":   "White balance",
        "fix.decontrast":      "Reduce contrast",
        "fix.remove_color_cast":"Remove color cast",

        "verdict.albedo.soapy":
            "{pct:.0f}% of pixels look soapy.",
        "verdict.albedo.dark":
            "Dark zones below threshold (p1={p1:.0f}).",
        "verdict.albedo.light":
            "Bright zones above threshold (p99={p99:.0f}).",
        "verdict.albedo.flat_contrast":
            "Flat contrast (std={std:.1f}).",
        "verdict.albedo.hard_contrast":
            "Extreme contrast (std={std:.1f}).",
        "verdict.albedo.flat_color":
            "Washed-out colors (S={sat:.3f}).",
        "verdict.albedo.oversaturated":
            "Oversaturated colors (S={sat:.3f}).",
        "verdict.albedo.color_cast":
            "Color cast (Δ={delta:.0f}).",
    },

    "zh": {

        "app.title":       "PBR Doctor",
        "app.subtitle":    "PBR 贴图诊断与修复",
        "app.tagline":     "PBR 贴图分析与修复",
        "app.log":         "日志",
        "app.info":        "关于",
        "app.lang":        "语言",

        "log.ready":       "PBR Doctor 1.1.0 已就绪",
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
        "err.open_hint":          "请检查路径、权限、磁盘空间、文件完整性。",
        "err.seamless_mode":      "未知无缝模式：{mode}",
        "err.orm_bad_fix_id":     "ORM fix_id 无效：{fix_id}",
        "err.orm_forbidden_fix":  "修复 '{op}' 不适用于 ORM。",
        "err.orm_unknown_channel":"未知通道：{channel}",

        "normal.not_a_normal.title":  "这不像法线贴图",
        "normal.not_a_normal.detail": (
            "B 通道平均 {b_mean:.2f}，std={b_std:.3f}。"
        ),
        "normal.broken_b.title":  "B 通道退化（平坦）",
        "normal.broken_b.detail": (
            "平均向量长度 {mean_len:.3f}。"
        ),
        "normal.baked.title":  "烘焙光照（偏移 {angle:.1f}°）",
        "normal.baked.detail": "平均法线偏离 (0,0,1) 达 {angle:.1f}°。",
        "normal.baked_mild.title":  "平均法线轻微偏移（{angle:.1f}°）",
        "normal.baked_mild.detail": "平均向量偏移 {angle:.1f}°。",
        "normal.bad_len.title":  "向量长度异常（{bad_pct:.1f}% 像素）",
        "normal.bad_len.detail": "{bad_pct:.1f}% 的像素超出 [0.9, 1.1]。",
        "normal.bad_len_mild.title":  "轻微长度偏差（{bad_pct:.1f}%）",
        "normal.bad_len_mild.detail": "{bad_pct:.1f}% 的像素超出 [0.9, 1.1]。",

        "rough.not_grayscale.title":  "粗糙度不是灰度图",
        "rough.not_grayscale.detail": "R/G/B 通道不一致（std={channel_std:.3f}）。",
        "rough.dead.title":  "死图（std={std:.3f}）",
        "rough.dead.detail": "{mid_pct:.1f}% 的像素位于中间区域。",
        "rough.low_var.title":  "变化过少（std={std:.3f}）",
        "rough.low_var.detail": "分布低于正常水平。",
        "rough.narrow.title":  "范围被压缩（span={span:.2f}）",
        "rough.narrow.detail": "数值仅分布在 [{p1:.2f}, {p99:.2f}]。",
        "rough.noisy.title":  "噪声过多（std={std:.3f}）",
        "rough.noisy.detail": "分布异常。",

        "metal.not_grayscale.title":  "金属度不是灰度图",
        "metal.not_grayscale.detail": "R/G/B 通道不一致。",
        "metal.muddy.title":  "中间区域有渐变（{muddy_pct:.1f}%）",
        "metal.muddy.detail": "{muddy_pct:.1f}% 的像素位于 {low}..{high} 区间。",
        "metal.muddy_mild.title":  "少量渐变（{muddy_pct:.1f}%）",
        "metal.muddy_mild.detail": "{muddy_pct:.1f}% 的像素位于中间区域。",
        "metal.all_zero.title":  "没有金属（全为 0）",
        "metal.all_zero.detail": "{zero_pct:.1f}% 的像素 = 0。",
        "metal.all_one.title":  "全是金属（全为 1）",
        "metal.all_one.detail": "{one_pct:.1f}% 的像素 = 1。",

        "ao.not_grayscale.title":  "AO 不是灰度图",
        "ao.not_grayscale.detail": "R/G/B 通道不一致。",
        "ao.dead.title":  "死图（std={std:.3f}）",
        "ao.dead.detail": "分布几乎为零。",
        "ao.low_var.title":  "变化过少（std={std:.3f}）",
        "ao.low_var.detail": "分布低于正常。",
        "ao.too_dark.title":  "AO 过暗（mean={mean:.2f}）",
        "ao.too_dark.detail": "平均亮度 {mean:.2f}。",
        "ao.too_light.title":  "AO 几乎不可见（mean={mean:.2f}）",
        "ao.too_light.detail": "平均亮度 {mean:.2f}。",
        "ao.narrow.title":  "范围被压缩（span={span:.2f}）",
        "ao.narrow.detail": "数值仅分布在 [{p1:.2f}, {p99:.2f}]。",

        "orm.bad_shape.title":  "[ORM] 贴图不是 RGB",
        "orm.bad_shape.detail": "ORM 必须为三通道 RGB。",
        "orm.grayscale.title":  "[ORM] 贴图是灰度图",
        "orm.grayscale.detail": "三个通道完全相同。",
        "orm.metal_muddy.title":  "[B] 金属度：非二值",
        "orm.metal_muddy.detail": "{mid_pct:.0f}% 的像素位于中间区域。",
        "orm.fix_all.title":  "[ORM] 全部修复",
        "orm.fix_all.detail": "对所有存在问题的通道应用最佳修复。",
        "orm.channel.R": "AO",
        "orm.channel.G": "粗糙度",
        "orm.channel.B": "金属度",
        "orm.wrap.R": "[R] AO: {text}",
        "orm.wrap.G": "[G] 粗糙度: {text}",
        "orm.wrap.B": "[B] 金属度: {text}",

        "fb.bad_shape.title":  "{label}：贴图不是 RGB",
        "fb.bad_shape.detail": "需要 RGB 数组。",
        "fb.unknown.title":  "贴图类型未识别",
        "fb.unknown.detail": "自动检测无法识别贴图。",
        "fb.unknown.kind_gray":  "看起来是灰度图",
        "fb.unknown.kind_color": "看起来是彩色图",
        "fb.dead_unknown.title":  "贴图几乎没有变化",
        "fb.dead_unknown.detail": "std {std:.3f}。",
        "fb.not_grayscale.title":  "{label} 不是灰度图",
        "fb.not_grayscale.detail": "R/G/B 通道不一致。",
        "fb.dead.title":  "{label}：死图（std={std:.3f}）",
        "fb.dead.detail": "分布几乎为零。",
        "fb.low_var.title":  "{label}：变化过少（std={std:.3f}）",
        "fb.low_var.detail": "分布低于正常。",
        "fb.narrow.title":  "{label}：范围被压缩（span={span:.2f}）",
        "fb.narrow.detail": "数值仅分布在 [{p1:.2f}, {p99:.2f}]。",
        "fb.too_dark.title":  "{label}：过暗（mean={mean:.2f}）",
        "fb.too_dark.detail": "平均亮度 {mean:.2f}。",
        "fb.too_light.title":  "{label}：过亮（mean={mean:.2f}）",
        "fb.too_light.detail": "平均亮度 {mean:.2f}。",
        "fb.noisy.title":  "{label}：噪声过多（std={std:.3f}）",
        "fb.noisy.detail": "分布异常。",
        "fb.edge_not_binary.title":  "边缘不是二值（{muddy_pct:.1f}%）",
        "fb.edge_not_binary.detail": "{muddy_pct:.1f}% 的像素位于中间区域。",
        "fb.label.height":  "高度",
        "fb.label.edge":    "边缘",
        "fb.label.unknown": "未知",

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
        "tab_analyze.log.no_maps":   "没有可分析的内容。",
        "tab_analyze.log.loading":   "正在加载 {n} 个文件...",
        "tab_analyze.log.loaded":    "已加载：{done}/{total}",
        "tab_analyze.log.analyzing": "分析中...",
        "tab_analyze.log.analyzed":  "已分析：{done}/{total}",
        "tab_analyze.log.not_a_file":  "不是文件：{path}",
        "tab_analyze.log.not_an_image":"不是图片：{name}",
        "tab_analyze.log.open_fail":   "打开 {name} 失败：{err}",
        "tab_analyze.log.no_analyzer": "{name}：{mtype} 分析器未就绪",
        "tab_analyze.log.analyze_fail":"{name}：分析失败：{err}",
        "tab_analyze.log.type_changed":"{name}：类型改为 {type}",
        "tab_analyze.log.no_maps_to_save": "没有可保存的贴图",
        "tab_analyze.log.nothing_to_save": "没有可保存的内容",
        "tab_analyze.log.saved_one":   "{name}（{bit}-bit）",
        "tab_analyze.log.save_fail":   "未保存 {name}：{err}",
        "tab_analyze.log.saved_total": "已保存：{saved}/{total} → {folder}",
        "tab_analyze.save.title":       "保存贴图",
        "tab_analyze.save.what":        "保存内容：",
        "tab_analyze.save.only_fixed":  "仅已修复（{n}）",
        "tab_analyze.save.bitness":     "位深：",
        "tab_analyze.save.bit8":        "8-bit",
        "tab_analyze.save.bit16":       "16-bit",
        "tab_analyze.save.summary":     "共 {total} 张  •  已修复 {fixed} 张",
        "tab_analyze.save.cancel":      "取消",
        "tab_analyze.save.confirm":     "保存",
        "tab_analyze.save.pick_folder": "保存到哪个文件夹？",
        "tab_analyze.log.deleted":     "✗ {name}：已从列表移除",
        "tab_analyze.delete_tooltip":  "从列表移除",

        "tab_seamless.title":        "无缝",
        "tab_seamless.mode_label":   "模式：",
        "tab_seamless.btn_one":      "应用到所选",
        "tab_seamless.btn_all":      "应用到全部",
        "tab_seamless.btn_save":     "保存",
        "tab_seamless.empty.list":   "请在 Analyze 标签页加载贴图",
        "tab_seamless.empty.preview":"请在左侧选择贴图",
        "tab_seamless.before":       "处理前",
        "tab_seamless.after":        "处理后",
        "tab_seamless.mode_line":    "模式：{mode}",
        "tab_seamless.seam_ok":      "正常",
        "tab_seamless.seam_bad":     "接缝 {diff:.3f}",
        "tab_seamless.seam_info":    "处理前：LR={lr:.3f}  TB={tb:.3f}",
        "tab_seamless.mode.mirror_blend.label": "镜像混合",
        "tab_seamless.mode.mirror_blend.desc":  "位移 + 镜像混合。",
        "tab_seamless.mode.freq_sep.label":     "频率分离",
        "tab_seamless.mode.freq_sep.desc":      "频率分离。",
        "tab_seamless.mode.hipass.label":       "高通（GIMP）",
        "tab_seamless.mode.hipass.desc":        "GIMP 无缝平铺。",
        "tab_seamless.log.mode_changed": "{mode}",
        "tab_seamless.log.nothing_selected": "未选择任何内容",
        "tab_seamless.log.no_preview_map":   "未选择用于预览的贴图",
        "tab_seamless.log.applying":     "正在对 {n} 张贴图应用无缝...",
        "tab_seamless.log.applied_one":  "{name}：无缝 → 接缝 {diff:.3f}",
        "tab_seamless.log.applied":      "无缝应用完成：{ok}/{total}",
        "tab_seamless.log.no_seamless":  "没有应用过无缝的贴图",
        "tab_seamless.log.saved":        "已保存：{saved}/{total} → {folder}",
        "tab_seamless.log.saved_one":    "{name}",
        "tab_seamless.log.save_fail":    "{name}：{err}",
        "tab_seamless.log.pick_folder":  "无缝贴图保存到哪个文件夹？",

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
        "panel.fix_result.metrics_better": "改善（{n} 项指标）",
        "panel.fix_result.metrics_worse":  "变差（{n} 项指标）",
        "panel.profile_label":   "材质配置",
        "panel.profile_changed": "配置已更改为「{profile}」",
        "panel.fixes_reset":     "重置所有修复",
        "panel.fixes_reset_log": "↺ {name}：已重置所有修复",

        "verdict.normal.mean_len":
            "向量长度低于正常（平均 {v:.2f}，应为 1.0）。",
        "verdict.normal.bad_pct_fail":
            "{v:.1f}% 的像素向量长度异常。",
        "verdict.normal.bad_pct_warn":
            "向量长度轻微偏差：{v:.1f}%。",
        "verdict.normal.angle_fail":
            "平均向量偏离 (0,0,1) 达 {v:.1f}°。",
        "verdict.normal.angle_warn":
            "平均法线轻微偏移 {v:.1f}°。",
        "verdict.normal.not_normal":
            "这不是法线贴图。",
        "verdict.normal.broken_b":
            "B 通道退化：mean={bm:.2f}，std={bs:.2f}。",

        "verdict.rough.color":
            "贴图为彩色，应为灰度（通道差 {v:.3f}）。",
        "verdict.rough.dead":
            "贴图已死（std {v:.3f}）。",
        "verdict.rough.low_var":
            "变化过少（std {v:.3f}）。",
        "verdict.rough.narrow":
            "范围被压缩：[{p1:.2f}..{p99:.2f}]。",
        "verdict.rough.noisy":
            "噪声过多（std {v:.3f}）。",

        "verdict.metal.color":
            "贴图为彩色，应为灰度。",
        "verdict.metal.muddy_fail":
            "{v:.0f}% 的像素位于中间区域。",
        "verdict.metal.muddy_warn":
            "{v:.0f}% 的像素位于中间区域。",
        "verdict.metal.all_zero":
            "{v:.1f}% 的像素 = 0。",
        "verdict.metal.all_one":
            "{v:.1f}% 的像素 = 1。",

        "verdict.ao.color":
            "贴图为彩色，应为灰度。",
        "verdict.ao.dead":
            "贴图已死（std {v:.3f}）。",
        "verdict.ao.low_var":
            "变化过少（std {v:.3f}）。",
        "verdict.ao.dark":
            "过暗（mean {v:.2f}）。",
        "verdict.ao.dark_short":
            "过暗（mean {v:.2f}）。",
        "verdict.ao.light":
            "AO 几乎不可见（mean {v:.2f}）。",
        "verdict.ao.narrow":
            "范围被压缩：[{p1:.2f}..{p99:.2f}]。",

        "verdict.fb.unknown":
            "贴图类型未识别。",
        "verdict.fb.color":
            "贴图为彩色，{label} 应为灰度。",
        "verdict.fb.dead":
            "贴图已死（std {v:.3f}）。",
        "verdict.fb.low_var":
            "变化过少（std {v:.3f}）。",
        "verdict.fb.narrow":
            "范围被压缩：[{p1:.2f}..{p99:.2f}]。",
        "verdict.fb.noisy":
            "噪声过多（std {v:.3f}）。",
        "verdict.fb.dark":
            "过暗（mean {v:.2f}）。",
        "verdict.fb.light":
            "过亮（mean {v:.2f}）。",
        "verdict.fb.edge_muddy":
            "{v:.0f}% 的像素位于中间区域。",

        "dlg_fix.headline.done":       "问题已解决",
        "dlg_fix.headline.better":     "已改善（{b} → {a}）",
        "dlg_fix.headline.partial":    "部分改善：{b} → {a}",
        "dlg_fix.headline.worse_iss":  "变差了：{b} → {a}",
        "dlg_fix.headline.unchanged":  "无变化",
        "dlg_fix.headline.worse":      "变差了",
        "dlg_fix.headline.metrics_better": "已改善（{n} 项指标）",
        "dlg_fix.headline.metrics_worse":  "变差（{n} 项指标）",
        "dlg_fix.headline.mixed":          "结果参半",
        "dlg_fix.row_metrics":             "指标：",
        "dlg_fix.fix_line":            "修复：{label}",
        "dlg_fix.row_status":          "状态：",
        "dlg_fix.row_issues":          "问题：",
        "dlg_fix.ok":                  "OK",

        "metric.std_l":        "细节对比度",
        "metric.soapy_pct":    "模糊区域",
        "metric.p1_l":         "暗部亮度",
        "metric.p99_l":        "高光",
        "metric.mean_s":       "颜色饱和度",
        "metric.color_spread": "色偏",
        "metric.mean_length":  "向量长度",
        "metric.bad_pct":      "异常长度",
        "metric.angle":        "倾斜角度",
        "metric.std":          "亮度分布",
        "metric.span":         "亮度范围",
        "metric.muddy_pct":    "中间区",
        "metric.mean":         "平均亮度",

        "metric.std_l.norm":        "（正常 > 30）",
        "metric.soapy_pct.norm":    "（正常 < 20%）",
        "metric.p1_l.norm":         "（正常 ≥ 10）",
        "metric.p99_l.norm":        "（正常 ≤ 250）",
        "metric.mean_s.norm":       "（正常 0.15–0.75）",
        "metric.color_spread.norm": "（正常 ≤ 15）",
        "metric.mean_length.norm":  "（正常 ≈ 1.0）",
        "metric.bad_pct.norm":      "（正常 < 5%）",
        "metric.angle.norm":        "（正常 < 5°）",
        "metric.std.norm":          "（正常 > 0.06）",
        "metric.span.norm":         "（正常 > 0.4）",
        "metric.muddy_pct.norm":    "（正常 < 5%）",
        "metric.mean.norm":         "",

        "info.tab.help":    "帮助",
        "info.tab.about":   "关于",
        "info.tab.support": "支持",
        "info.help_text": (
            "PBR Doctor — PBR 贴图诊断与修复。\n\n"
            "使用方法：\n"
            "1. 点击 Add files 加载贴图。\n"
            "2. 点击 Analyze All。\n"
            "3. 点击左侧贴图查看详情。\n"
            "4. 点击修复。\n"
            "5. 撤销可回退。\n"
            "6. Save fixed 保存（8 / 16-bit）。\n\n"
            "提示：法线和高度请始终保存为 16-bit。"
        ),
        "info.about.version": "版本",
        "info.about.build":   "构建",
        "info.about.author":  "作者",
        "info.about.license": "许可",
        "info.about.desc": (
            "Albedolizer 系列的独立程序。"
        ),
        "info.support.copied": "✓ 地址已复制",
        "wallets.support_title": "支持开发",
        "wallets.support_text":  "如果这个工具帮到了你，请作者喝杯咖啡。",

        # ─── ALBEDO ───
        "albedo.default_profile_warn":
            "未能从文件名识别材质配置 — 使用 \"{profile}\"。",
        "albedo.profile_line": "配置：{profile}",

        "albedo.soapy.title":  "模糊区域（{pct:.0f}%）",
        "albedo.soapy.detail": "{pct:.0f}% 的像素看起来模糊。",
        "albedo.dark.title":  "欠曝（p1={p1:.0f}，阈值 {thr}）",
        "albedo.dark.detail": "暗部低于阈值（p1={p1:.0f}）。",
        "albedo.light.title":  "过曝（p99={p99:.0f}，阈值 {thr}）",
        "albedo.light.detail": "亮部超出阈值（p99={p99:.0f}）。",
        "albedo.flat_contrast.title":  "对比度偏低（std={std:.1f}）",
        "albedo.flat_contrast.detail": "亮度分布较窄（std={std:.1f}）。",
        "albedo.hard_contrast.title":  "对比度过高（std={std:.1f}）",
        "albedo.hard_contrast.detail": "亮度分布过宽（std={std:.1f}）。",
        "albedo.flat_color.title":  "饱和度偏低（S={sat:.3f}）",
        "albedo.flat_color.detail": "HSV 平均饱和度仅 {sat:.3f}。",
        "albedo.oversaturated.title":  "过饱和（S={sat:.3f}）",
        "albedo.oversaturated.detail": "HSV 平均饱和度 {sat:.3f}。",
        "albedo.color_cast.title":  "偏色（Δ={delta:.0f}）",
        "albedo.color_cast.detail": "R/G/B 通道平均色差为 {delta:.0f}。",

        "albedo.profile.metal":          "金属",
        "albedo.profile.rust":           "锈",
        "albedo.profile.oxidized_metal": "氧化金属",
        "albedo.profile.patina":         "铜绿",
        "albedo.profile.brass":          "黄铜",
        "albedo.profile.aluminum":       "铝",
        "albedo.profile.copper":         "铜",
        "albedo.profile.wood":           "木材",
        "albedo.profile.leaves":         "树叶",
        "albedo.profile.moss":           "苔藓",
        "albedo.profile.organic":        "有机",
        "albedo.profile.grass":          "草",
        "albedo.profile.bark":           "树皮",
        "albedo.profile.tile":           "瓷砖",
        "albedo.profile.gravel":         "砾石",
        "albedo.profile.coal":           "煤",
        "albedo.profile.roof_tiles":     "屋顶瓦",
        "albedo.profile.stone":          "石头",
        "albedo.profile.concrete":       "混凝土",
        "albedo.profile.brick":          "砖",
        "albedo.profile.ground":         "地面",
        "albedo.profile.asphalt":        "沥青",
        "albedo.profile.marble":         "大理石",
        "albedo.profile.sand":           "沙子",
        "albedo.profile.clay":           "粘土",
        "albedo.profile.granite":        "花岗岩",
        "albedo.profile.stucco":         "灰泥",
        "albedo.profile.gemstone":       "宝石",
        "albedo.profile.plastic":        "塑料",
        "albedo.profile.rubber":         "橡胶",
        "albedo.profile.glass":          "玻璃",
        "albedo.profile.ceramic":        "陶瓷",
        "albedo.profile.painted_metal":  "涂漆金属",
        "albedo.profile.carbon":         "碳纤维",
        "albedo.profile.cardboard":      "纸板",
        "albedo.profile.water":          "水",
        "albedo.profile.mud":            "泥",
        "albedo.profile.snow":           "雪",
        "albedo.profile.ice":            "冰",
        "albedo.profile.cotton":         "棉",
        "albedo.profile.wool":           "羊毛",
        "albedo.profile.silk":           "丝绸",
        "albedo.profile.denim":          "牛仔布",
        "albedo.profile.carpet":         "地毯",
        "albedo.profile.velvet":         "天鹅绒",
        "albedo.profile.leather":        "皮革",
        "albedo.profile.fur":            "毛皮",
        "albedo.profile.skin":           "皮肤",
        "albedo.profile.scales":         "鳞片",
        "albedo.profile.bone":           "骨头",

        "fix.auto_correct":    "自动校正",
        "fix.clahe_only":      "仅 CLAHE",
        "fix.auto_levels_only":"仅自动色阶",
        "fix.remove_soap":     "去除模糊",
        "fix.saturate_15":     "+15% 饱和度",
        "fix.saturate_30":     "+30% 饱和度",
        "fix.desaturate_15":   "−15% 饱和度",
        "fix.white_balance":   "白平衡",
        "fix.decontrast":      "降低对比",
        "fix.remove_color_cast":"去除色偏",

        "verdict.albedo.soapy":
            "{pct:.0f}% 的像素看起来模糊。",
        "verdict.albedo.dark":
            "暗部低于阈值（p1={p1:.0f}）。",
        "verdict.albedo.light":
            "亮部超出阈值（p99={p99:.0f}）。",
        "verdict.albedo.flat_contrast":
            "对比度偏低（std={std:.1f}）。",
        "verdict.albedo.hard_contrast":
            "对比度过高（std={std:.1f}）。",
        "verdict.albedo.flat_color":
            "颜色偏淡（S={sat:.3f}）。",
        "verdict.albedo.oversaturated":
            "颜色过饱和（S={sat:.3f}）。",
        "verdict.albedo.color_cast":
            "偏色（Δ={delta:.0f}）。",
    },
}