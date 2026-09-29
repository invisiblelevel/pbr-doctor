# PBR Doctor

**Diagnose and repair AI-generated PBR maps** · **Диагностика и ремонт PBR-карт после AI-генерации** · **AI 生成的 PBR 贴图诊断与修复**

[![Version](https://img.shields.io/badge/version-1.1.0-blue.svg)](../../releases)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D6.svg)](#install)
[![Python](https://img.shields.io/badge/python-3.14-3776AB.svg)](https://www.python.org/)
[![Flet](https://img.shields.io/badge/flet-1.0-00A67E.svg)](https://flet.dev/)
[![Languages](https://img.shields.io/badge/languages-EN%20%7C%20RU%20%7C%20ZH-orange.svg)](#languages)

[🇬🇧 English](#english) · [🇷🇺 Русский](#русский) · [🇨🇳 中文](#中文)

---

## English

PBR Doctor is a standalone tool for diagnosing and repairing PBR maps produced by AI generators (Meshy, Tripo, Luma, Stable Diffusion, Photoshop generators, and others).

Load maps → get a report of what's wrong → fix in one click → save as 8-bit or 16-bit. A dedicated **Seamless** tab brings maps to tileable form.

### What's new in 1.1.0

- **Albedo / BaseColor analyzer** — 7 checks (soapiness, exposure, contrast, saturation, color cast) with 50 texture profiles (metal, wood, stone, fabric, ...) and **SCUNet-based soapiness fix**
- **ORM analyzer** — per-channel analysis (R=AO, G=Roughness, B=Metallic) with "Fix All"
- **Fallback analyzer** for Height / Edge / Unknown maps
- **Seamless tab** — three algorithms (mirror-blend, frequency-separation, hi-pass GIMP)
- **Full localization** — EN / RU / ZH with system auto-detection and switcher in the header
- **Human-readable metrics** in the fix dialog — before/after table with norms, arrows and percent signs
- **Reset all fixes** button — one-click rollback when Undo isn't enough
- **Delete maps** from the list via trash icon in each row
- **Texture profile dropdown** for Albedo maps — override auto-detection if the filename lies
- **Manual map type override** via dropdown in the map list

### Features

- **Load maps** — drop files, type is auto-detected (by name and by content)
- **Analysis** — traffic-light verdict OK / Warning / Fail, raw metrics, plain-language explanation
- **One-click fixes** — stretch range, make grayscale, restore B channel, binarize, invert AO, remove baked light, auto-correct albedo, remove soapiness
- **Undo** + **Reset all fixes** — roll back any fix or all fixes on a map
- **ORM** — per-channel analysis with "Fix All"
- **Seamless** — three algorithms with before/after preview
- **16-bit** — full load and save support
- **Three languages** — English, Russian, Chinese (Simplified), with system auto-detection

### Supported map types

| Type | What is checked |
|---|---|
| Normal | baked light, vector lengths, degenerate B channel |
| Roughness | dead map, narrow range, noise, color channels |
| Metallic | mid-zone gradients, all-zero / all-one |
| Ambient Occlusion | dead, too dark / too light, narrow range |
| **ORM** | per-channel analysis (AO + Roughness + Metallic) |
| **Albedo / BaseColor** | soapiness, exposure, contrast, saturation, color cast |
| Height / Displacement | basic grayscale and range checks |
| Edge / Outline | binarity, noise |

### Install

Download **PBR Doctor Setup.exe** from [Releases](../../releases), run, install. No Python or dependencies needed — everything is bundled.

Windows 10 / 11 (64-bit) supported.

### Build from source

Install dependencies: `pip install -r requirements.txt`

Build the exe: `python -m PyInstaller "PBR Doctor.spec" --noconfirm --clean`

Build the installer (requires [Inno Setup 6](https://jrsoftware.org/isdl.php)): `"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss`

### Stack

Python 3.14 · Flet 1.0 · NumPy · Pillow · OpenCV · SCUNet-GAN (ONNX) · PyInstaller · Inno Setup

### License

MIT — see [LICENSE](LICENSE).

### Author

INV.LVL · [@invisiblelevel](https://github.com/invisiblelevel)

---

## Русский

PBR Doctor — отдельная программа для проверки и починки PBR-карт, которые сгенерировали нейросети (Meshy, Tripo, Luma, Stable Diffusion, генераторы в Photoshop и другие).

Загружаешь карты → получаешь отчёт, что не так → фиксишь в один клик → сохраняешь результат в 8-bit или 16-bit. Отдельная вкладка **Seamless** для приведения карт к бесшовному тайлингу.

### Что нового в 1.1.0

- **Анализатор Albedo / BaseColor** — 7 проверок (мыльность, недосвет/пересвет, контраст, насыщенность, цветовой сдвиг) + **50 профилей текстур** (металл, дерево, камень, ткань, ...) + **фикс мыла через SCUNet**
- **Анализатор ORM** — per-channel (R=AO, G=Roughness, B=Metallic) с фиксом «починить всё»
- **Fallback-анализатор** для Height / Edge / Unknown карт
- **Вкладка Seamless** — три алгоритма (mirror-blend, frequency-separation, hi-pass GIMP)
- **Полная локализация** — EN / RU / ZH с авто-определением системы и переключателем в хедере
- **Человеческие метрики** в модалке фикса — таблица до/после с нормами, стрелками и процентами
- **Кнопка «Сбросить все фиксы»** — откат всех фиксов на карте одним кликом
- **Удаление карт** из списка через корзину в каждой строке
- **Дропдаун профиля текстуры** для Albedo — переопределение авто-детекта если имя файла врёт
- **Ручное переключение типа карты** через дропдаун в списке

### Что умеет

- **Загрузка карт** — перетащил файлы, тип определился автоматически (по имени и по содержимому)
- **Анализ** — светофор OK / Warning / Fail, детальные метрики, понятный вердикт на человеческом языке
- **Фиксы в один клик** — растяжка диапазона, grayscale, восстановление B-канала, бинаризация, инверсия AO, вычитание запечённого света, авто-коррекция альбедо, удаление мыла
- **Undo** + **Сброс всех фиксов** — откат любого фикса или всех фиксов на карте
- **ORM** — per-channel анализ с фиксом «починить всё»
- **Seamless** — три алгоритма с превью до/после
- **16-bit** — полноценная поддержка загрузки и сохранения
- **Три языка** — английский, русский, китайский (упрощённый), с авто-определением системного

### Поддерживаемые типы карт

| Тип | Что проверяет |
|---|---|
| Normal | запечённый свет, длины векторов, вырожденный B-канал |
| Roughness | мёртвая карта, узкий диапазон, шум, цветность |
| Metallic | градиенты в серой зоне, всё в 0 / всё в 1 |
| Ambient Occlusion | мёртвая, слишком тёмная / светлая, пережатый диапазон |
| **ORM** | per-channel анализ (AO + Roughness + Metallic) |
| **Albedo / BaseColor** | мыльность, недосвет/пересвет, контраст, насыщенность, цветовой сдвиг |
| Height / Displacement | базовые проверки grayscale и диапазона |
| Edge / Outline | бинарность, шум |

### Установка

Скачай **PBR Doctor Setup.exe** из раздела [Releases](../../releases), запусти, установи. Python и зависимости не нужны — всё вшито в инсталлер.

Поддерживается Windows 10 / 11 (64-bit).

### Сборка из исходников

Установить зависимости: `pip install -r requirements.txt`

Собрать exe: `python -m PyInstaller "PBR Doctor.spec" --noconfirm --clean`

Собрать инсталлер (требуется [Inno Setup 6](https://jrsoftware.org/isdl.php)): `"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss`

### Стек

Python 3.14 · Flet 1.0 · NumPy · Pillow · OpenCV · SCUNet-GAN (ONNX) · PyInstaller · Inno Setup

### Лицензия

MIT — см. [LICENSE](LICENSE).

### Автор

INV.LVL · [@invisiblelevel](https://github.com/invisiblelevel)

---

## 中文

PBR Doctor 是一款独立的 PBR 贴图诊断与修复工具，专为 AI 生成的贴图而设计（适用于 Meshy、Tripo、Luma、Stable Diffusion、Photoshop 生成器等）。

加载贴图 → 获取问题报告 → 一键修复 → 保存为 8-bit 或 16-bit。独立的 **无缝（Seamless）** 标签页可将贴图处理为无缝平铺。

### 1.1.0 新功能

- **反照率 / 基础色分析器** — 7 项检查（模糊度、曝光、对比度、饱和度、色偏）+ **50 种材质配置**（金属、木材、石材、织物等）+ **基于 SCUNet 的模糊修复**
- **ORM 分析器** — 分通道（R=AO，G=粗糙度，B=金属度），支持「全部修复」
- **回退分析器** — 针对 Height / Edge / Unknown 贴图
- **无缝（Seamless）标签页** — 三种算法（镜像混合、频率分离、高通 GIMP）
- **完整本地化** — 英语 / 俄语 / 中文，支持系统自动检测与顶栏切换
- **人性化指标** — 修复对话框显示前后对比表格，包含正常范围、箭头和百分比
- **「重置所有修复」按钮** — 一键回退某张贴图的所有修复
- **删除贴图** — 每行右侧垃圾桶图标可从列表移除
- **材质配置下拉菜单** — 用于反照率贴图，可覆盖按文件名的自动识别
- **手动切换贴图类型** — 列表中的下拉菜单

### 功能

- **加载贴图** — 拖入文件，类型自动识别（按文件名和内容）
- **分析** — 交通灯判定 OK / 警告 / 失败，原始指标，通俗解释
- **一键修复** — 拉伸范围、转为灰度、恢复 B 通道、二值化、AO 反相、去除烘焙光照、自动校正反照率、去除模糊
- **撤销** + **重置所有修复** — 回退单个或全部修复
- **ORM** — 分通道分析，支持「全部修复」
- **无缝** — 三种算法，前后预览
- **16-bit** — 完整的加载与保存支持
- **三种语言** — 英语、俄语、简体中文，支持系统自动检测

### 支持的贴图类型

| 类型 | 检查内容 |
|---|---|
| 法线（Normal） | 烘焙光照、向量长度、B 通道退化 |
| 粗糙度（Roughness） | 死图、范围过窄、噪声、彩色通道 |
| 金属度（Metallic） | 中间区域渐变、全 0 / 全 1 |
| 环境光遮蔽（AO） | 死图、过暗 / 过亮、范围过窄 |
| **ORM** | 分通道分析（AO + 粗糙度 + 金属度） |
| **反照率 / 基础色（Albedo）** | 模糊度、曝光、对比度、饱和度、色偏 |
| 高度 / 置换（Height） | 灰度与范围基础检查 |
| 边缘 / 描边（Edge） | 二值性、噪声 |

### 安装

从 [Releases](../../releases) 下载 **PBR Doctor Setup.exe**，运行并安装。无需 Python 或任何依赖 — 全部已打包。

支持 Windows 10 / 11（64 位）。

### 从源码构建

安装依赖：`pip install -r requirements.txt`

构建 exe：`python -m PyInstaller "PBR Doctor.spec" --noconfirm --clean`

构建安装包（需先安装 [Inno Setup 6](https://jrsoftware.org/isdl.php)）：`"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss`

### 技术栈

Python 3.14 · Flet 1.0 · NumPy · Pillow · OpenCV · SCUNet-GAN (ONNX) · PyInstaller · Inno Setup

### 许可证

MIT — 见 [LICENSE](LICENSE)。

### 作者

INV.LVL · [@invisiblelevel](https://github.com/invisiblelevel)