$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    py -3 -m venv .venv
}

& $python -m pip install -r requirements-build.txt
& $python .\build_tools\create_icon.py
& $python -m PyInstaller --noconfirm --clean .\LS900-Biometry-Analyzer.spec

$releaseDir = Join-Path $PSScriptRoot "release"
New-Item -ItemType Directory -Force -Path $releaseDir | Out-Null
$archive = Join-Path $releaseDir "LS900-ESX-GuineaPig-Biometry-v0.1.0-windows-x64.zip"
Compress-Archive -Path ".\dist\LS900 Biometry Analyzer\*" -DestinationPath $archive -Force
$hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $archive).Hash
Set-Content -LiteralPath "$archive.sha256.txt" -Value "$hash  $(Split-Path -Leaf $archive)" -Encoding ascii

Write-Output "Windows application: $PSScriptRoot\dist\LS900 Biometry Analyzer\LS900 Biometry Analyzer.exe"
Write-Output "Release archive: $archive"
Write-Output "SHA256: $hash"
