# V5 reproducibility and environment

## Scope

Software v0.2.1 uses the locked V5 model `guinea-lenstar-v5.0.0-animal-grouped-2026-10-16`.
SHA-256: `80BDF7AC628A3F27F2CAE2CBD8D7D88B458FF6E248840AA406D09FFCAAE6100B`.
The model is checked on load. No fitting, online learning or reference-table lookup occurs during inference. V4 stays in `inference.py` for the unchanged lens implementation and historical comparison; public `analysis.analyze_esx` invokes V5 retinal inference with the locked lens parameters. Desktop and CLI use the same `batch.py` service.

## Conda entry point

From a source checkout:

```powershell
conda env create -f environment.yml
conda activate ls900-biometry-v5
python -m pip install -e . --no-deps --no-build-isolation
ls900-biometry --version
ls900-biometry --input "D:\data\raw" --output "D:\results\measurements.xlsx"
ls900-desktop
```

The Conda descriptor pins Python 3.12.10 to match the GitHub Windows build. Local development and regression used an isolated Python 3.12.14 Windows x64 venv. The downloaded GitHub executable was tested separately. No Conda solve was executed on this machine. Platform-specific binary dependencies must be verified separately. `environment.yml` is an environment specification, not a hash-locked cross-platform solver result. Pip editable installation also needs setuptools 80.9.0; install it before `--no-build-isolation` if absent.

## Exact Windows release dependency versions

```powershell
py -3.12 -m venv .venv-v5
.\.venv-v5\Scripts\python.exe -m pip install -r requirements-lock-windows-py312.txt
.\.venv-v5\Scripts\python.exe -m pip install -e . --no-deps --no-build-isolation
```

The lock file pins resolved dependency versions, not wheel hashes. GitHub builds use Python 3.12.10 x64; local checks also used 3.12.14. RELEASE_MANIFEST.json records the actual interpreter used for each package. This does not guarantee byte-identical executables, future package availability or numerical identity on untested platforms. Install `requirements-test.txt` to include the legacy Flask compatibility tests, then run:

```powershell
python -m unittest discover -s tests -v
python build_tools/audit_public_tree.py
python build_tools/create_icon.py
python -m PyInstaller --noconfirm --clean LS900-Biometry-Analyzer.spec
python build_tools/package_release.py
```

The native application itself does not require Flask, Waitress, a web browser, WebView2, a running Conda installation or a local web server. Its Qt libraries are bundled. Official Qt license texts are included in licenses/Qt, so packaging does not need to download them. Users of the completed ZIP do not need network access for analysis. See THIRD_PARTY_NOTICES.md for licensing and corresponding Qt source.

## Public synthetic installation check

```powershell
python examples/generate_synthetic.py --output "D:\scratch\synthetic.esx"
ls900-biometry --input "D:\scratch\synthetic.esx" --output "D:\scratch\synthetic_result.xlsx"
```

This generated file is not an animal record and does not validate biological accuracy or reproduce the study's training data. A malformed XML test, duplicate-file handling, missing-eye test, lens gate, model hash, manual-retinal-cursor independence and native-window controls are covered by automated tests.

For headless execution of the packaged EXE, use `"LS900 Biometry Analyzer.exe" --batch --input ... --output ...` (PowerShell uses `&` before a quoted executable path). Wait for process completion. CLI refuses to overwrite existing output. All user-facing numeric values remain ordinary Excel numbers; differences in cell display rounding are not algorithm changes.

## Study and data limits

Retrospective V5 performance, denominators and remaining failures are documented in V5_EXPERIMENTAL.md. Current evidence concerns manual EyeSuite-equivalent measurement agreement, not independent anatomical truth. Publication of code and parameters enables inference reproduction; complete training reproduction requires access to the underlying training signals and manual reference labels. Those private records are not distributed here. Raw ESX, reference screenshots/workbooks, patient data, vendor installers and protected manuals must never be added to this repository or release ZIP.
