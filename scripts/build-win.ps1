# Build squeeze-pdf for Windows (run on Windows with PowerShell).
# Requires: activated Python venv with pip install -e ".[dev]", Node.js, vp CLI.
# Target machines need WebView2 Runtime for pywebview.
Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

vp run desktop-ui#build
pyinstaller client/pyinstaller/squeeze-pdf-win.spec --noconfirm

$iscc = "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe"
if (Test-Path $iscc) {
  & $iscc "scripts/installer.iss"
  Write-Host "Built: squeeze-pdf-Windows-Setup.exe"
} else {
  Write-Host "Built: dist/squeeze-pdf/squeeze-pdf.exe (install Inno Setup 6 for installer)"
}
