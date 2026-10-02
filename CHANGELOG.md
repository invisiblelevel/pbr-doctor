# Changelog

All notable changes to PBR Doctor will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.1-beta] — 2026-10-02

Performance and compatibility release: DirectML backend for GPU inference on any GPU (NVIDIA / AMD / Intel), faster soapiness fix, full-resolution preview, and cleanup of diagnostic output.

### Added

#### Preview
- **Full-screen map preview** — click the thumbnail in the right panel to open a 1400×820 modal with the full-resolution image
- **Before / After toggle** in the preview modal — flip between original and fixed version (only shown if fixes were applied)
- **"Enlarge" hint** overlaid on the thumbnail so users know it's clickable

### Changed

#### Deblur (Remove Soapiness)
- **Single-pass SCUNet inference** — the second model pass was removed. It contributed little quality-wise but doubled inference time. Soapiness fix is now ~2× faster
- **Fixed-shape model** — `SCUNet-GAN-fixed.onnx` with static input `[1, 3, 256, 256]` (required for DirectML, which does not support dynamic input shapes)
- **Old dynamic-shape model removed** — `SCUNet-GAN.onnx` is no longer needed and can be deleted

#### Execution Provider
- **DirectML instead of CUDA** — the model now runs through `onnxruntime-directml`, which works on **any GPU via DirectX 12**: NVIDIA, AMD, Intel. No CUDA Toolkit, cuDNN, or TensorRT installation required
- **CPU fallback** — if DirectML is unavailable, inference falls back to CPU automatically

#### Map Detection
- **Albedo always wins by filename** — if the filename contains `albedo`, `alb`, `basecolor`, `base_color`, `diffuse`, `diff`, `colour`, `texture`, `tex`, or `bc`, the map is classified as Albedo regardless of content. This fixes cases where AI-generated albedo maps were being misdetected as Metallic / Edge / Height
- **ORM always wins by filename** — same priority rule for `orm`, `rma`, `mra`, `arm`, `mre`

#### Progress Reporting
- **Determinate progress bar** — shows real percentage based on processed tiles, not an indeterminate spinner
- **Live tile counter** — text like "Deblur: 245/1369 tiles" updates every 250 ms
- **Main-thread polling** — UI updates happen from the main Flet thread via `asyncio.create_task` polling, avoiding DirectML / GIL deadlocks

#### UI / UX
- **Version** bumped to `1.1.1-beta` in window title, header, and About dialog
- **Build date** updated to `2026-10-02`

### Fixed

- **UI freeze on 8K maps** — `analyzer.fix()` and `analyzer.analyze()` now run through `asyncio.to_thread`, so the Flet event loop stays responsive during long operations
- **DirectML hang on dynamic-shape model** — fixed by re-exporting SCUNet with a static input shape. Previously `session.run()` would hang indefinitely on the first tile
- **Progress callback crash** — `page.update()` is no longer called from the background thread (unsafe in Flet); the callback now only writes to `S` and a main-thread poller applies the updates
- **Albedo misdetected as Metallic / Edge** — fixed by giving filename rules for Albedo priority over content-based detection

### Removed

- **Diagnostic `print()` calls** — `[fix]`, `[scunet]`, `[deblur]` debug output removed from the console
- **`SCUNet-GAN.onnx`** (dynamic-shape model) — replaced by `SCUNet-GAN-fixed.onnx`
- **`core/io_patch.py`** — obsolete monkey-patch, no longer imported
- **TensorRT and CUDA provider branches** — replaced by a single DirectML / CPU priority list

### Technical

- **Provider priority**: `DmlExecutionProvider` → `CPUExecutionProvider`
- **Model**: `SCUNet-GAN-fixed.onnx`, static input `[1, 3, 256, 256]`, tile size 256, overlap 32, reflect padding for edge tiles
- **Tile inference**: per-tile run with triangular window blending to avoid seams
- **Deblur fix**: single model pass + multi-scale detail boost (3 Gaussian scales) + soft clip + bilateral filter
- **`BaseAnalyzer.downsample_for_analysis()`** — analysis runs on a ≤2048 px copy of the map; fixes still operate on the full-resolution array
- **Preview cache** — thumbnail base64 cached by `id(entry.working)`, invalidated when a fix replaces the array

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
- **Fix dialog** — takes into account metric deltas, not just severity
- **`auto_correct` for Albedo** — was running with the default "stone" profile regardless of the actual map type
- **`remove_soap`** — completely reworked: was doing nothing useful with the old multi-scale algorithm; now uses SCUNet-GAN with a deficit mask
- **Locale detection** — uses `ctypes.windll.kernel32.GetUserDefaultUILanguage()` for more reliable detection on Windows
- **Fix history** — cleared when changing map type or texture profile
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
- **Model bundled**: `assets/models/SCUNet-GAN-fixed.onnx`
- **Refactor**: `Issue` now stores localization keys (`title_key`, `detail_key`, `fix_label_key`) instead of raw strings
- **Refactor**: `Report` metrics are now the single source of truth for the fix result dialog
- **Refactor**: `analyze()` for Albedo accepts `profile_key` and `filename` arguments

### Removed

- **Empty right panel on Seamless tab** — now hidden for full-width layout
- **`ai_edge_litert` dependency** — was used for a NAFNet TFLite test that didn't pan out; SCUNet works through OpenCV dnn
- **NAFNet models** — replaced by SCUNet-GAN

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

[1.1.1-beta]: ../../compare/v1.1.0...v1.1.1-beta
[1.1.0]: ../../compare/v1.0.0...v1.1.0
[1.0.0]: ../../releases/tag/v1.0.0