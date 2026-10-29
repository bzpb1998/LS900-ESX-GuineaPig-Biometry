$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv-v5\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    py -3.12 -m venv .venv-v5
    if ($LASTEXITCODE -ne 0) { throw "Python 3.12 environment creation failed" }
}

& $python -m pip install -r requirements-lock-windows-py312.txt
if ($LASTEXITCODE -ne 0) { throw "Dependency installation failed" }
& $python -m pip install -e . --no-deps --no-build-isolation
if ($LASTEXITCODE -ne 0) { throw "Project installation failed" }
& $python .\build_tools\create_icon.py
if ($LASTEXITCODE -ne 0) { throw "Icon generation failed" }
& $python -m PyInstaller --noconfirm --clean .\LS900-Biometry-Analyzer.spec
if ($LASTEXITCODE -ne 0) { throw "Executable build failed" }
& $python .\build_tools\package_release.py
if ($LASTEXITCODE -ne 0) { throw "Release packaging failed" }
