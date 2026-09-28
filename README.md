# PBR Doctor

**Диагностика и ремонт PBR-карт после AI-генерации** · **Diagnose and repair AI-generated PBR maps** · **AI 生成的 PBR 贴图诊断与修复**

[🇷🇺 Русский](#русский) · [🇬🇧 English](#english) · [🇨🇳 中文](#中文)

---

## Русский

PBR Doctor — отдельная программа для проверки и починки PBR-карт, которые сгенерировали нейросети (Meshy, Tripo, Luma, Stable Diffusion, генераторы в Photoshop и др.).

Загружаешь карты → получаешь отчёт, что не так → фиксишь в один клик → сохраняешь результат в 8-bit или 16-bit. Отдельная вкладка **Seamless** для приведения карт к бесшовному тайлингу.

### Что умеет

- **Загрузка карт** — перетащил файлы, тип определился автоматически (по имени и по содержимому)
- **Анализ** — светофор OK / Warning / Fail, детальные метрики, понятный вердикт на человеческом языке
- **Фиксы в один клик** — растяжка диапазона, grayscale, восстановление B-канала, бинаризация, инверсия AO, вычитание запечённого света
- **Undo** — откат любого фикса
- **ORM** — per-channel анализ (R=AO, G=Roughness, B=Metallic) с фиксом «починить всё»
- **Seamless** — три алгоритма: mirror-blend, frequency-separation, hi-pass (GIMP)
- **16-bit** — полноценная поддержка загрузки и сохранения
- **Три языка** — русский, английский, китайский (упрощённый), с авто-определением системного

### Поддерживаемые типы карт

| Тип | Что проверяет |
|---|---|
| Normal | запечённый свет, длины векторов, вырожденный B-канал |
| Roughness | мёртвая карта, узкий диапазон, шум, цветность |
| Metallic | градиенты в серой зоне, всё в 0 / всё в 1 |
| Ambient Occlusion | мёртвая, слишком тёмная / светлая, пережатый диапазон |
| ORM | per-channel анализ (AO + Roughness + Metallic) |
| Height / Displacement | базовые проверки grayscale и диапазона |
| Edge / Outline | бинарность, шум |
| Albedo / BaseColor | распознаётся, но не проверяется |

### Установка

Скачай `PBR Doctor Setup.exe` из раздела [Releases](../../releases), запусти, установи. Python и зависимости не нужны — всё вшито в инсталлер.

Поддерживается Windows 10 / 11 (64-bit).

### Сборка из исходников

```bash
pip install -r requirements.txt
python -m PyInstaller "PBR Doctor.spec" --noconfirm --clean
Инсталлер (требуется Inno Setup 6):

bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
Стек
Python 3.14 · Flet 1.0 · NumPy · Pillow · OpenCV · PyInstaller · Inno Setup

Лицензия
MIT — см. LICENSE

Автор
INV.LVL · @invisiblelevel

English
PBR Doctor is a standalone tool for diagnosing and repairing PBR maps produced by AI generators (Meshy, Tripo, Luma, Stable Diffusion, Photoshop generators, etc.).

Load maps → get a report on what's wrong → fix in one click → save as 8-bit or 16-bit. A dedicated Seamless tab brings maps to tileable form.

Features
Load maps — drop files, type is auto-detected (by name and by content)

Analysis — traffic-light verdict OK / Warning / Fail, raw metrics, plain-language explanation

One-click fixes — stretch range, make grayscale, restore B channel, binarize, invert AO, remove baked light

Undo — roll back any fix

ORM — per-channel analysis (R=AO, G=Roughness, B=Metallic) with "Fix All"

Seamless — three algorithms: mirror-blend, frequency-separation, hi-pass (GIMP)

16-bit — full load and save support

Three languages — Russian, English, Chinese (Simplified), with system auto-detection

Supported map types
Type	What is checked
Normal	baked light, vector lengths, degenerate B channel
Roughness	dead map, narrow range, noise, color channels
Metallic	mid-zone gradients, all-zero / all-one
Ambient Occlusion	dead, too dark / too light, narrow range
ORM	per-channel analysis (AO + Roughness + Metallic)
Height / Displacement	basic grayscale and range checks
Edge / Outline	binarity, noise
Albedo / BaseColor	detected but not analyzed
Install
Download PBR Doctor Setup.exe from Releases, run, install. No Python or dependencies needed — everything is bundled.

Windows 10 / 11 (64-bit) supported.

Build from source
bash
pip install -r requirements.txt
python -m PyInstaller "PBR Doctor.spec" --noconfirm --clean
Installer (requires Inno Setup 6):

bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
Stack
Python 3.14 · Flet 1.0 · NumPy · Pillow · OpenCV · PyInstaller · Inno Setup

License
MIT — see LICENSE

Author
INV.LVL · @invisiblelevel

中文
PBR Doctor 是一款独立的 PBR 贴图诊断与修复工具，专为 AI 生成的贴图而设计（适用于 Meshy、Tripo、Luma、Stable Diffusion、Photoshop 生成器等）。

加载贴图 → 获取问题报告 → 一键修复 → 保存为 8-bit 或 16-bit。独立的 无缝（Seamless） 标签页可将贴图处理为无缝平铺。

功能
加载贴图 — 拖入文件，类型自动识别（按文件名和内容）

分析 — 交通灯判定 OK / 警告 / 失败，原始指标，通俗解释

一键修复 — 拉伸范围、转为灰度、恢复 B 通道、二值化、AO 反相、去除烘焙光照

撤销 — 回退任意修复

ORM — 分通道分析（R=AO，G=粗糙度，B=金属度），支持"全部修复"

无缝 — 三种算法：镜像混合、频率分离、高通（GIMP）

16-bit — 完整的加载与保存支持

三种语言 — 俄语、英语、简体中文，支持系统自动检测

支持的贴图类型
类型	检查内容
法线（Normal）	烘焙光照、向量长度、B 通道退化
粗糙度（Roughness）	死图、范围过窄、噪声、彩色通道
金属度（Metallic）	中间区域渐变、全 0 / 全 1
环境光遮蔽（AO）	死图、过暗 / 过亮、范围过窄
ORM	分通道分析（AO + 粗糙度 + 金属度）
高度 / 置换（Height）	灰度与范围基础检查
边缘 / 描边（Edge）	二值性、噪声
反照率 / 基础色（Albedo）	可识别，但不做分析
安装
从 Releases 下载 PBR Doctor Setup.exe，运行并安装。无需 Python 或任何依赖 — 全部已打包。

支持 Windows 10 / 11（64 位）。

从源码构建
bash
pip install -r requirements.txt
python -m PyInstaller "PBR Doctor.spec" --noconfirm --clean
安装包（需先安装 Inno Setup 6）：

bash
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" installer.iss
技术栈
Python 3.14 · Flet 1.0 · NumPy · Pillow · OpenCV · PyInstaller · Inno Setup

许可证
MIT — 见 LICENSE

作者
INV.LVL · @invisiblelevel