# Changelog

## 0.2.1 — 2026-10-30

- Record the actual build interpreter in RELEASE_MANIFEST.json instead of a local hard-coded version.
- Pin GitHub's build interpreter to 3.12.10 and align the Conda descriptor; document local 3.12.14 checks separately.
- Keep the identical locked V5 model and numerical results; no training changes.

## 0.2.0 — 2026-10-29

- Native Windows Qt desktop window with no browser or local HTTP server.
- Default locked V5 inference shared by the Python API, CLI and desktop.
- Original SVG logo, progress/cancellation, help, citation and direct Excel save.
- Pinned Windows dependencies, Conda environment descriptor and reproducibility guide.
- Correct model-version notes and defensive lens-gate enforcement in the compact Excel exporter.
- Retained V4 implementation and previous release; no raw research data distributed.

## V5 experimental research branch — 2026-10-16

- Animal-grouped retinal ranker, wider waveform context and normalized raw-scan median.
- Explicit review when a backup retinal selector is unavailable.
- Frozen V5 parameters, opt-in local Excel CLI, numerical fitting primitives and synthetic integrity tests.
- Retrospective evaluation documents both improvements and remaining failures; default V4 application is retained.
- Research data/file exclusions strengthened; no raw ESX or manual references are included.

## 0.1.0 — 2026-10-06

- First public research release.
- Added local multi-file ESX upload and timestamped Excel export.
- Embedded the locked V4 guinea-pig biometry model.
- Added hidden Windows launcher, browser opening and system-tray exit.
- Added compact two-sheet output with OD/OS AL, CCT, AD, LT and RT.
