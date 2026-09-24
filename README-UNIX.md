# Nail POS — macOS & Linux

Self-contained POS app built with Python + pywebview.
Each platform build produces a native app with NO Python required on the target machine.

---

## macOS

**Requirements:** macOS 10.14+, Python 3.9+, Xcode Command Line Tools

```bash
# 1. Install Xcode CLI tools (if not already)
xcode-select --install

# 2. Run the build script
chmod +x BUILD-MAC.sh
./BUILD-MAC.sh
```

**Output:**
- `dist/NailPOS.app` — drag to Applications to install
- `dist/NailPOS-Mac.dmg` — shareable installer (double-click, drag to Applications)

**Data location:** `~/Library/Application Support/Nail POS/`

---

## Linux (Ubuntu / Debian / Fedora / Arch)

**Requirements:** Python 3.9+, webkit2gtk

```bash
# Run the build script (auto-detects your distro)
chmod +x BUILD-LINUX.sh
./BUILD-LINUX.sh
```

**Output:**
- `dist/NailPOS` — standalone binary, runs anywhere
- Desktop launcher added to your app menu automatically

**Data location:** `~/.local/share/Nail POS/`

---

## Running without building

If you just want to run the app directly without building an installer:

```bash
pip3 install pywebview

# macOS:
python3 app.py

# Linux (install webkit2gtk first):
sudo apt-get install python3-gi gir1.2-webkit2-4.0
python3 app.py
```

---

## Files

| File | Purpose |
|------|---------|
| `app.py` | Main app — HTTP server + pywebview window |
| `index.html` | POS frontend (all UI) |
| `checkin.html` | Customer kiosk page |
| `booking.html` | Booking page |
| `BUILD-MAC.sh` | One-click macOS build |
| `BUILD-LINUX.sh` | One-click Linux build |

---

## Customer Kiosk

While the app is running, open any browser on the same machine and go to:
`http://localhost:3000/checkin.html`

Or on another device on the same network, replace `localhost` with this machine's IP address.
