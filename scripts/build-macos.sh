#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
vp run desktop-ui#build
pyinstaller client/pyinstaller/squeeze-pdf-macos.spec --noconfirm
hdiutil create -volname "squeeze-pdf" -srcfolder "dist/squeeze-pdf.app" -ov -format UDZO squeeze-pdf-macOS.dmg
echo "Built: dist/squeeze-pdf.app"
echo "Built: squeeze-pdf-macOS.dmg"
