# Changelog

All notable changes to PBR Doctor will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] — 2025-09-29

Major feature release: Albedo analyzer, full localization, ORM, Seamless tab, and a reworked fix dialog with human-readable metrics.

### Added

#### Analyzers
- **Albedo / BaseColor analyzer** — 7 checks:
  - Soapiness (loss of local detail)
  - Underexposure / overexposure (per texture profile)
  - Flat / extreme contrast
  - Flat / oversaturated colors
  - Color cast between R/G/B channels
- **50 texture profiles** for Albedo (metal, wood, stone, fabric, fauna, synthetic, special) with auto-detection by filename
- **Texture profile dropdown** in the right panel — manual override of auto-detection
- **ORM analyzer** — per-channel (R=AO, G=Roughness, B=Metallic) with "Fix All ORM" button
- **Fallback analyzer** for Height / Edge / Unknown map types

#### Seamless tab
- **Three seamless algorithms**:
  - Mirror-blend (shift + mirror blend)
  - Frequency-separation (low-pass blend, high-pass kept)
  - Hi-pass (GIMP tile-seamless port)
- **Before/After preview** for each map
- **Apply to selected / Apply to all** with per-map checkboxes
- **Automatic hide of the right panel** on the Seamless tab for full width

#### Localization
- **Three languages**: English, Russian, Chinese (Simplified)
- **System language auto-detection** on startup
- **Language switcher** in the header (dropdown: RU / EN / ZH)
- **All UI, issues, fixes, dialogs, and metrics** translated

#### Fixes
- **Auto-correct for Albedo** — CLAHE + auto-levels + contrast stretch + saturation, profile-aware (port of Albedolizer's `fallback_correct`)
- **Remove soapiness** — SCUNet-GAN (ONNX) two-pass with deficit mask + multi-scale detail boost
- **+15% / +30% saturation**, **−15% saturation**
- **White balance** (gray world)
- **Reduce contrast**
- **Remove color cast** (LAB)
- **Reset all fixes** button — one-click rollback of all fixes on a map

#### UI / UX
- **Human-readable metrics** in the fix result dialog:
  - Before/After table with norms in parentheses
  - Colored arrows (better / worse / unchanged)
  - Percent signs where applicable
  - Metric deltas count in the headline ("Improved (2 metrics better)")
- **Delete maps from the list** — trash icon in each row
- **Manual map type override** — dropdown in the map list
- **Smart fix result headline** — takes into account metric deltas, not just severity

### Changed

- **Right panel hidden on Seamless tab** — full width for the seamless workflow
- **Window size** — 1320×840 (was 1400×880)
- **Right panel width** — expanded for better readability
- **Font sizes** in the right panel increased for clarity
- **Seamless header** — single row, shorter button labels
- **`MapEntry`** — added `albedo_profile` field
- **`albedo_profiles.py`** — added `sorted_profile_keys()` for alphabetically sorted dropdown
- **Analyzer profile sync** — profile is now passed from `analyze` to `fix` (fixes the auto-correct bug where the fix was working with the default profile)

### Fixed

- **Normal analyzer** — `broken_b_channel` criterion changed to `mean_len < 0.85` (was `b_std < 0.05`, which caused a false-positive loop)
- **Normal analyzer** — `baked_light` only checked when `mean_len >= 0.85` (angle is unreliable for degenerate maps)
- **Fix dialog** — takes into account metric deltas, not just severity (shows "Improved (2 metrics)" instead of "No change" when severity stays the same)
- **`auto_correct` for Albedo** — was running with the default "stone" profile regardless of the actual map type (now uses the detected or user-selected profile)
- **`remove_soap`** — completely reworked: was doing nothing useful with the old multi-scale algorithm; now uses SCUNet-GAN with a deficit mask
- **Locale detection** — uses `ctypes.windll.kernel32.GetUserDefaultUILanguage()` for more reliable detection on Windows
- **Fix history** — cleared when changing map type or texture profile (fixes from a different type are invalid)
- **Seamless** — `detect_seam` no longer triggers on grayscale maps with slightly different edge pixels

### Technical

- **New module**: `core/albedo_profiles.py` — 50 texture profiles + auto-detection
- **New module**: `core/deblur_model.py` — SCUNet-GAN ONNX singleton with tiled inference
- **New module**: `core/i18n.py` — full localization system (RU / EN / ZH)
- **New module**: `core/seamless.py` — three seamless algorithms + `detect_seam`
- **New module**: `core/analyzers/orm.py` — per-channel ORM analyzer
- **New module**: `core/analyzers/fallback.py` — height / edge / unknown
- **New module**: `core/analyzers/albedo.py` — albedo analyzer + 10 fixes
- **New module**: `ui/tab_seamless.py` — Seamless tab
- **Model bundled**: `assets/models/SCUNet-GAN.onnx` (~91 MB, compressed to ~30 MB in installer)
- **Refactor**: `Issue` now stores localization keys (`title_key`, `detail_key`, `fix_label_key`) instead of raw strings
- **Refactor**: `Report` metrics are now the single source of truth for the fix result dialog
- **Refactor**: `analyze()` for Albedo accepts `profile_key` and `filename` arguments

### Removed

- **Empty right panel on Seamless tab** — now hidden for full-width layout
- **`ai_edge_litert` dependency** — was used for a NAFNet TFLite test that didn't pan out; SCUNet works through OpenCV dnn
- **NAFNet models** (2025may ONNX, fp16 TFLite, GoPro-width64 ONNX) — replaced by SCUNet-GAN

---

## [1.0.0] — 2025-08-15

Initial public release.

### Added

- **Load maps** via Add files (FilePicker)
- **Auto-detection** of map type by name and by content (normal, roughness, metallic, AO, height, edge, albedo, unknown)
- **Normal analyzer** — baked light, broken vector lengths, "not a normal map" checks
- **Roughness analyzer** — dead map, narrow range, noise, grayscale check
- **Metallic analyzer** — mid-zone gradients, all-zero / all-one
- **AO analyzer** — dead, too dark / too light, narrow range
- **One-click fixes** with inline buttons and a result dialog
- **Undo** — rollback of the last fix
- **Save results** — 8-bit or 16-bit PNG, only-fixed or all maps
- **Info dialog** — Help / About / Support with crypto wallets
- **Log panel** at the bottom — collapsible
- **Dark theme**

### Technical

- Python 3.14, Flet 1.0, NumPy, Pillow, OpenCV
- `S["maps"]` — list of `MapEntry` objects (no type collisions)
- Analyzer registry with `get_analyzer(map_type)`
- PyInstaller + Inno Setup build pipeline

---

## Legend

- **Added** — new features
- **Changed** — changes in existing functionality
- **Deprecated** — soon-to-be removed features
- **Removed** — removed features
- **Fixed** — bug fixes
- **Security** — security fixes
- **Technical** — internal refactors, new modules, build changes

---

[1.1.0]: ../../compare/v1.0.0...v1.1.0
[1.0.0]: ../../releases/tag/v1.0.0