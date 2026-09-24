#!/bin/bash
# ============================================
#  Nail POS - Build for macOS
# ============================================
set -e
cd "$(dirname "$0")"

echo ""
echo "============================================"
echo "  Nail POS - macOS Build"
echo "============================================"
echo ""

# ── Step 1: Install dependencies ──
echo "[1/3] Installing Python dependencies..."
pip3 install --upgrade pywebview pyinstaller pyobjc-core pyobjc pyobjc-framework-Cocoa pyobjc-framework-WebKit

# ── Step 2: Convert icon (ico → icns) ──
echo ""
echo "[2/3] Building NailPOS.app..."

# Use sips to convert icon if icns doesn't exist
if [ ! -f "icon.icns" ]; then
    if [ -f "icon.ico" ]; then
        echo "   Converting icon.ico → icon.icns..."
        mkdir -p /tmp/NailPOS.iconset
        # Extract at multiple sizes using sips
        for size in 16 32 64 128 256 512; do
            sips -z $size $size icon.ico --out /tmp/NailPOS.iconset/icon_${size}x${size}.png 2>/dev/null || true
            double=$((size * 2))
            sips -z $double $double icon.ico --out /tmp/NailPOS.iconset/icon_${size}x${size}@2x.png 2>/dev/null || true
        done
        iconutil -c icns /tmp/NailPOS.iconset -o icon.icns 2>/dev/null || echo "   (icon conversion skipped)"
        rm -rf /tmp/NailPOS.iconset
    fi
fi

# Clean previous build
rm -rf build dist

# Build .app bundle
ICON_ARG=""
[ -f "icon.icns" ] && ICON_ARG="--icon icon.icns"

python3 -m PyInstaller \
  --windowed \
  --onefile \
  --name "NailPOS" \
  --add-data "index.html:." \
  --add-data "checkin.html:." \
  --add-data "booking.html:." \
  --collect-all webview \
  --hidden-import "webview.platforms.cocoa" \
  $ICON_ARG \
  app.py

echo ""
echo "[3/3] Creating DMG installer..."

if command -v hdiutil &> /dev/null; then
    mkdir -p dist/dmg
    cp -r "dist/NailPOS.app" dist/dmg/
    ln -s /Applications dist/dmg/Applications
    hdiutil create \
        -volname "Nail POS" \
        -srcfolder dist/dmg \
        -ov -format UDZO \
        "dist/NailPOS-Mac.dmg"
    rm -rf dist/dmg
    echo ""
    echo "============================================"
    echo "  SUCCESS!"
    echo "  Installer: dist/NailPOS-Mac.dmg"
    echo "  App:       dist/NailPOS.app"
    echo "============================================"
    echo ""
    echo "  To install: open NailPOS-Mac.dmg and drag"
    echo "  NailPOS to your Applications folder."
    open dist/
else
    echo ""
    echo "============================================"
    echo "  SUCCESS!"
    echo "  App: dist/NailPOS.app"
    echo "============================================"
    echo ""
    echo "  Copy NailPOS.app to your Applications folder."
    open dist/
fi
