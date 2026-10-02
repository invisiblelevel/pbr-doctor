# PBR Doctor

**Diagnose and repair AI-generated PBR maps** · **Диагностика и ремонт PBR-карт после AI-генерации** · **AI 生成的 PBR 贴图诊断与修复**

[![Version](https://img.shields.io/badge/version-1.1.1--beta-blue.svg)](../../releases)
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

### What's new in 1.1.1-beta

- **DirectML GPU backend** — soapiness removal (SCUNet-GAN) now runs on **any DirectX 12 GPU**: NVIDIA, AMD, Intel. **No CUDA, no cuDNN, no TensorRT installation required.** CPU fallback if DirectML is unavailable
- **~2× faster soapiness fix** — the second model pass was removed; quality is unaffected, inference time is halved
- **Full-screen preview** — click any map thumbnail to inspect it at full resolution, with a Before / After toggle
- **Real progress bar** — determinate percentage and a live tile counter instead of an indeterminate spinner
- **Fixed UI freeze on 8K maps** — analysis and fixes now run on a background thread; the interface stays responsive
- **Smarter map detection** — Albedo and ORM are now classified by filename priority, so AI-generated albedo maps are no longer misdetected as Metallic or Edge
- **Cleaner output** — diagnostic logging removed from the console

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

### GPU acceleration

Soapiness removal runs SCUNet-GAN through **DirectML**, a universal GPU backend that works on any DirectX 12 graphics adapter. No proprietary SDKs required.

If DirectML is unavailable, inference falls back to CPU automatically — the app always works, GPU is just faster.

### Install

Download **PBR Doctor Setup v1.1.1-beta.exe** from [Releases](../../releases), run, install (choose English / Russian / Chinese). No Python or dependencies needed — everything is bundled.

Windows 10 version 1903 or newer / Windows 11 (64-bit).

### Build from source

Install dependencies:

    pip install -r requirements.txt

Build the exe:

    python -m PyInstaller pbr_doctor.spec --noconfirm --clean

Build the installer (requires [Inno Setup 7](https://jrsoftware.org/isdl.php)):

    "C:\Program Files\Inno Setup 7\ISCC.exe" installer.iss

### Stack

Python 3.14 · Flet 1.0 · NumPy · Pillow · OpenCV · onnxruntime-directml · SCUNet-GAN (ONNX) · PyInstaller · Inno Setup

### License

MIT — see [LICENSE](LICENSE).

### Author

INV.LVL · [@invisiblelevel](https://github.com/invisiblelevel)

---

## Русский

PBR Doctor — отдельная программа для проверки и починки PBR-карт, которые сгенерировали нейросети (Meshy, Tripo, Luma, Stable Diffusion, генераторы в Photoshop и другие).

Загружаешь карты → получаешь отчёт, что не так → фиксишь в один клик → сохраняешь результат в 8-bit или 16-bit. Отдельная вкладка **Seamless** для приведения карт к бесшовному тайлингу.

### Что нового в 1.1.1-beta

- **GPU через DirectML** — удаление мыла (SCUNet-GAN) теперь работает на **любой видеокарте с DirectX 12**: NVIDIA, AMD, Intel. **Не нужно ставить CUDA, cuDNN или TensorRT.** Если DirectML недоступен — автоматический откат на CPU
- **Фикс мыла в ~2 раза быстрее** — убран второй проход модели, качество не пострадало, время вдвое меньше
- **Полноэкранное превью** — клик по миниатюре открывает карту на весь экран с переключением «до / после»
- **Настоящий прогресс-бар** — процент и счётчик обработанных тайлов вместо бесконечной крутилки
- **Пофикшено зависание интерфейса на 8K** — анализ и фиксы работают в фоновом потоке, окно остаётся живым
- **Умнее детект карт** — Albedo и ORM теперь определяются по приоритету имени файла, поэтому AI-альбедо больше не улетает в Metallic или Edge
- **Чистая консоль** — диагностические логи убраны

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

### Ускорение на GPU

Удаление мыла работает через **DirectML** — универсальный GPU-бэкенд, который поддерживает **любую видеокарту с DirectX 12**. Проприетарные SDK ставить не нужно.

Если DirectML недоступен, инференс автоматически откатывается на CPU — программа работает всегда, GPU просто быстрее.

### Установка

Скачай **PBR Doctor Setup v1.1.1-beta.exe** из раздела [Releases](../../releases), запусти, установи (выбери язык: русский / английский / китайский). Python и зависимости не нужны — всё вшито в инсталлер.

Поддерживается Windows 10 (версия 1903+) / Windows 11 (64-bit).

### Сборка из исходников

Установить зависимости:

    pip install -r requirements.txt

Собрать exe:

    python -m PyInstaller pbr_doctor.spec --noconfirm --clean

Собрать инсталлер (требуется [Inno Setup 7](https://jrsoftware.org/isdl.php)):

    "C:\Program Files\Inno Setup 7\ISCC.exe" installer.iss

### Стек

Python 3.14 · Flet 1.0 · NumPy · Pillow · OpenCV · onnxruntime-directml · SCUNet-GAN (ONNX) · PyInstaller · Inno Setup

### Лицензия

MIT — см. [LICENSE](LICENSE).

### Автор

INV.LVL · [@invisiblelevel](https://github.com/invisiblelevel)

---

## 中文

PBR Doctor 是一款独立的 PBR 贴图诊断与修复工具，专为 AI 生成的贴图而设计（适用于 Meshy、Tripo、Luma、Stable Diffusion、Photoshop 生成器等）。

加载贴图 → 获取问题报告 → 一键修复 → 保存为 8-bit 或 16-bit。独立的 **无缝（Seamless）** 标签页可将贴图处理为无缝平铺。

### 1.1.1-beta 新功能

- **DirectML GPU 后端** — 模糊修复（SCUNet-GAN）现在可在 **任何支持 DirectX 12 的显卡**上运行：NVIDIA、AMD、Intel。**无需安装 CUDA、cuDNN 或 TensorRT。** 若 DirectML 不可用，将自动回退到 CPU
- **模糊修复速度提升约 2 倍** — 移除了第二次模型推理，画质不变，耗时减半
- **全屏预览** — 点击缩略图可全屏查看贴图，并支持「前 / 后」切换
- **真正的进度条** — 显示百分比和处理进度，不再是无限循环的转圈
- **修复 8K 贴图的界面冻结问题** — 分析与修复在后台线程运行，界面保持响应
- **更智能的贴图识别** — Albedo 和 ORM 现在按文件名优先级识别，AI 生成的反照率贴图不再被误判为金属度或边缘
- **控制台输出更干净** — 移除了调试日志

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

### GPU 加速

模糊修复通过 **DirectML** 运行 —— 一个通用 GPU 后端，支持任何 DirectX 12 显卡。无需安装专有 SDK。

若 DirectML 不可用，将自动回退到 CPU —— 程序始终可用，GPU 只是更快。

### 安装

从 [Releases](../../releases) 下载 **PBR Doctor Setup v1.1.1-beta.exe**，运行并安装（可选英语 / 俄语 / 中文）。无需 Python 或任何依赖 — 全部已打包。

支持 Windows 10（1903 或更新版本）/ Windows 11（64 位）。

### 从源码构建

安装依赖：

    pip install -r requirements.txt

构建 exe：

    python -m PyInstaller pbr_doctor.spec --noconfirm --clean

构建安装包（需先安装 [Inno Setup 7](https://jrsoftware.org/isdl.php)）：

    "C:\Program Files\Inno Setup 7\ISCC.exe" installer.iss

### 技术栈

Python 3.14 · Flet 1.0 · NumPy · Pillow · OpenCV · onnxruntime-directml · SCUNet-GAN (ONNX) · PyInstaller · Inno Setup

### 许可证

MIT — 见 [LICENSE](LICENSE)。

### 作者

INV.LVL · [@invisiblelevel](https://github.com/invisiblelevel)