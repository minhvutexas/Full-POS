/**
 * Nail POS — Electron Entry Point
 * Starts the built-in HTTP server, then opens a native window.
 * Data is stored in the user's AppData folder so it persists across updates.
 */
const { app, BrowserWindow, shell, Menu } = require('electron');
const path = require('path');
const http = require('http');
const fs   = require('fs');
const os   = require('os');

const PORT = 3000;

// ── Data file lives in AppData, not the install folder ───────────────────────
// e.g. C:\Users\You\AppData\Roaming\Nail POS\data.json
let DATA_FILE;

function initDataFile() {
  const userDataDir = app.getPath('userData');
  if (!fs.existsSync(userDataDir)) fs.mkdirSync(userDataDir, { recursive: true });
  DATA_FILE = path.join(userDataDir, 'data.json');
  if (!fs.existsSync(DATA_FILE)) fs.writeFileSync(DATA_FILE, '{}');
}

// ── Embedded HTTP server (same logic as server.js) ───────────────────────────
const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js':   'application/javascript',
  '.css':  'text/css',
  '.json': 'application/json',
  '.png':  'image/png',
  '.ico':  'image/x-icon',
  '.svg':  'image/svg+xml',
};

// app.getAppPath() returns the correct root in both dev and asar-packaged builds
// (Electron transparently patches fs to read from .asar archives)
let DIR = __dirname; // overridden in whenReady once app is ready

function readData()       { try { return JSON.parse(fs.readFileSync(DATA_FILE, 'utf8')); } catch { return {}; } }
function writeData(data)  { fs.writeFileSync(DATA_FILE, JSON.stringify(data)); }

function startServer() {
  const server = http.createServer((req, res) => {
    res.setHeader('Access-Control-Allow-Origin', '*');
    res.setHeader('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS');
    res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
    if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }

    const url = req.url.split('?')[0];

    if (url === '/api/db' && req.method === 'GET') {
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(fs.readFileSync(DATA_FILE, 'utf8'));
      return;
    }
    if (url === '/api/db' && req.method === 'POST') {
      let body = '';
      req.on('data', c => body += c);
      req.on('end', () => {
        try {
          JSON.parse(body);
          fs.writeFileSync(DATA_FILE, body);
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end('{"ok":true}');
        } catch {
          res.writeHead(400); res.end('{"error":"Invalid JSON"}');
        }
      });
      return;
    }
    if (url === '/api/services' && req.method === 'GET') {
      const data = readData();
      const services = data['npos_services'] ? JSON.parse(data['npos_services']) : [];
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(services));
      return;
    }
    if (url === '/api/settings' && req.method === 'GET') {
      const data = readData();
      const settings = data['npos_settings'] ? JSON.parse(data['npos_settings']) : {};
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({ salonName: settings.salonName || 'Nail Salon' }));
      return;
    }
    if (url === '/api/bookings' && req.method === 'POST') {
      let body = '';
      req.on('data', c => body += c);
      req.on('end', () => {
        try {
          const booking = JSON.parse(body);
          const data = readData();
          const pending = data['npos_web_bookings'] ? JSON.parse(data['npos_web_bookings']) : [];
          booking.id = Date.now() + Math.floor(Math.random() * 1000);
          booking.receivedAt = new Date().toISOString();
          booking.status = 'pending';
          pending.push(booking);
          data['npos_web_bookings'] = JSON.stringify(pending);
          writeData(data);
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ ok: true, id: booking.id }));
        } catch {
          res.writeHead(400); res.end('{"error":"Invalid booking data"}');
        }
      });
      return;
    }
    if (url === '/api/bookings' && req.method === 'GET') {
      const data = readData();
      const pending = data['npos_web_bookings'] ? JSON.parse(data['npos_web_bookings']) : [];
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(pending));
      return;
    }
    if (url.startsWith('/api/bookings/') && req.method === 'DELETE') {
      const id = parseInt(url.replace('/api/bookings/', ''));
      const data = readData();
      let pending = data['npos_web_bookings'] ? JSON.parse(data['npos_web_bookings']) : [];
      pending = pending.filter(b => b.id !== id);
      data['npos_web_bookings'] = JSON.stringify(pending);
      writeData(data);
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end('{"ok":true}');
      return;
    }

    // Static files
    const filePath = path.join(DIR, url === '/' ? 'index.html' : url);
    fs.readFile(filePath, (err, fileData) => {
      if (err) { res.writeHead(404); res.end('404 Not Found'); return; }
      const ext = path.extname(filePath);
      res.writeHead(200, { 'Content-Type': MIME[ext] || 'text/plain' });
      res.end(fileData);
    });
  });

  server.listen(PORT, '127.0.0.1', () => {
    console.log(`Nail POS server running on http://localhost:${PORT}`);
  });
}

// ── Window ────────────────────────────────────────────────────────────────────
let win;

function createWindow() {
  win = new BrowserWindow({
    width: 1400,
    height: 900,
    minWidth: 900,
    minHeight: 600,
    title: 'Nail POS',
    backgroundColor: '#1a1a2e',
    webPreferences: {
      nodeIntegration: false,
      contextIsolation: true,
    },
    show: false, // wait until ready to show
  });

  // Remove the default menu bar (keeps the app clean)
  Menu.setApplicationMenu(null);

  // Load the POS
  win.loadURL(`http://localhost:${PORT}`);

  win.once('ready-to-show', () => win.show());

  win.on('closed', () => { win = null; });

  // Open external links in the default browser, not in the app
  win.webContents.setWindowOpenHandler(({ url }) => {
    shell.openExternal(url);
    return { action: 'deny' };
  });
}

// ── App lifecycle ─────────────────────────────────────────────────────────────
app.whenReady().then(() => {
  DIR = app.getAppPath(); // correct for both dev and packaged .asar
  initDataFile();
  startServer();

  // Small delay to let the server bind before loading the URL
  setTimeout(createWindow, 300);

  app.on('activate', () => { if (!win) createWindow(); });
});

app.on('window-all-closed', () => {
  app.quit();
});
