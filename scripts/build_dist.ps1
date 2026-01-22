Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Build both api_server and scanner_listener using the combined spec
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

# Clean previous outputs
if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path dist)  { Remove-Item -Recurse -Force dist }

# Prefer venv's PyInstaller if available
$pi = Join-Path $Root ".venv\Scripts\pyinstaller.exe"
if (-not (Test-Path $pi)) { $pi = "pyinstaller" }

& $pi --noconfirm api_server.spec

Write-Host ""
Write-Host "Build complete. Outputs:" -ForegroundColor Cyan
Get-ChildItem dist -Recurse | Select-Object FullName

Write-Host "API binary:      dist/api_server/api_server"
Write-Host "Scanner binary:  dist/scanner_listener/scanner_listener"
