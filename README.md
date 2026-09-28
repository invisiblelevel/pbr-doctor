# PBR Doctor 1.0.0

Диагностика и ремонт PBR-карт после AI-генерации.

## Что это

Отдельная программа для проверки и починки PBR-карт, которые
сгенерировали нейросети (Meshy, Tripo, Luma, Stable Diffusion и др.).

- Загружаешь карты → получаешь отчёт → фиксишь в один клик
- Сохраняешь результат в 8-bit или 16-bit
- Отдельная вкладка Seamless для приведения к бесшовному тайлингу

## Поддерживаемые типы карт

- Normal
- Roughness
- Metallic
- Ambient Occlusion (AO)
- ORM (Occlusion-Roughness-Metallic)
- Height / Displacement
- Edge / Outline
- Albedo / BaseColor

## Языки интерфейса

Русский / English / 中文 (简体)

## Установка

Скачай `PBR Doctor Setup.exe` из релизов, запусти, установи.
Python и зависимости не нужны — всё вшито.

## Сборка из исходников

```bash
pip install -r requirements.txt
python -m PyInstaller "PBR Doctor.spec" --noconfirm --clean