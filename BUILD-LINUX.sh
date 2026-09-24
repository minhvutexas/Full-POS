#!/bin/bash
# ============================================
#  Nail POS - Build for Linux
# ============================================
set -e
cd "$(dirname "$0")"

echo ""
echo "============================================"
echo "  Nail POS - Linux Build"
echo "============================================"
echo ""

# Detect distro
if command -v apt-get &> /dev/null; then
    DISTRO="debian"
elif command -v dnf &> /dev/null; then
    DISTRO="fedora"
elif command -v pacman &> /dev/null; then
    DISTRO="arch"
else
    DISTRO="unknown"
fi

# ── Step 1: System dependencies ──
echo "[1/3] Installing system dependencies..."
if [ "$DISTRO" = "debian" ]; then
    sudo apt-get update -qq
    sudo apt-get install -y \
        python3-pip python3-gi python3-gi-cairo \
        gir1.2-gtk-3.0 gir1.2-webkit2-4.0 \
        libgtk-3-dev libwebkit2gtk-4.0-dev \
        python3-dev gcc
elif [ "$DISTRO" = "fedora" ]; then
    sudo dnf install -y \
        python3-pip python3-gobject \
        webkit2gtk4.0-devel gtk3-devel \
        python3-devel gcc
elif [ "$DISTRO" = "arch" ]; then
    sudo pacman -Sy --noconfirm \
        python-pip python-gobject \
        webkit2gtk gtk3
else
    echo "   Unknown distro — please install webkit2gtk and GTK3 manually."
fi

# ── Step 2: Python dependencies ──
echo ""
echo "[2/3] Installing Python dependencies..."
pip3 install --upgrade pywebview pyinstaller

# Clean previous build
rm -rf build dist

# Build standalone binary
echo ""
echo "[3/3] Building NailPOS binary..."
python3 -m PyInstaller \
  --onefile \
  --name "NailPOS" \
  --add-data "index.html:." \
  --add-data "checkin.html:." \
  --add-data "booking.html:." \
  --collect-all webview \
  --hidden-import "webview.platforms.gtk" \
  app.py

# Create .desktop launcher
INSTALL_DIR="$HOME/.local/share/NailPOS"
mkdir -p "$INSTALL_DIR"
cp dist/NailPOS "$INSTALL_DIR/"

# Try to create a PNG icon from the ico
if command -v convert &> /dev/null && [ -f "icon.ico" ]; then
    convert icon.ico -resize 256x256 "$INSTALL_DIR/icon.png" 2>/dev/null || true
fi

mkdir -p "$HOME/.local/share/applications"
cat > "$HOME/.local/share/applications/NailPOS.desktop" << DESKTOP
[Desktop Entry]
Version=1.0
Type=Application
Name=Nail POS
Comment=Nail Salon Point of Sale
Exec=$INSTALL_DIR/NailPOS
Icon=$INSTALL_DIR/icon.png
Terminal=false
Categories=Office;Finance;
DESKTOP

echo ""
echo "============================================"
echo "  SUCCESS!"
echo "============================================"
echo ""
echo "  Binary:   dist/NailPOS"
echo "  Launcher: ~/.local/share/applications/NailPOS.desktop"
echo ""
echo "  Run now:  ./dist/NailPOS"
echo "  Or find 'Nail POS' in your app menu."
echo ""

# Ask to run now
read -p "Launch Nail POS now? [y/N] " answer
[ "$answer" = "y" ] || [ "$answer" = "Y" ] && ./dist/NailPOS &
