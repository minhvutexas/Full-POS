/**
 * Nail POS — Local Server
 * Pure Node.js, zero dependencies.
 * Run: node server.js
 */
const http = require('http');
const fs   = require('fs');
const path = require('path');
const os   = require('os');

const PORT      = 3000;
const DATA_FILE = path.join(__dirname, 'data.json');
const DIR       = __dirname;

// Ensure data.json exists
if (!fs.existsSync(DATA_FILE)) fs.writeFileSync(DATA_FILE, '{}');

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.js':   'application/javascript',
  '.css':  'text/css',
  '.json': 'application/json',
  '.png':  'image/png',
  '.ico':  'image/x-icon',
  '.svg':  'image/svg+xml',
};

function getLocalIP() {
  const nets = os.networkInterfaces();
  for (const name of Object.keys(nets)) {
    for (const net of nets[name]) {
      if (net.family === 'IPv4' && !net.internal) return net.address;
    }
  }
  return 'localhost';
}

function readData() {
  try { return JSON.parse(fs.readFileSync(DATA_FILE, 'utf8')); } catch { return {}; }
}

function writeData(data) {
  fs.writeFileSync(DATA_FILE, JSON.stringify(data));
}

const server = http.createServer((req, res) => {
  // CORS — allow any origin so the booking form on external websites can POST here
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  if (req.method === 'OPTIONS') { res.writeHead(204); res.end(); return; }

  const url = req.url.split('?')[0];

  // ── GET /api/db  — full data sync ─────────────────────────
  if (url === '/api/db' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(fs.existsSync(DATA_FILE) ? fs.readFileSync(DATA_FILE, 'utf8') : '{}');
    return;
  }

  // ── POST /api/db  — full data sync ─────────────────────────
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
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end('{"error":"Invalid JSON"}');
      }
    });
    return;
  }

  // ── GET /api/services  — public: booking form fetches these ─
  if (url === '/api/services' && req.method === 'GET') {
    const data = readData();
    const services = data['npos_services'] ? JSON.parse(data['npos_services']) : [];
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(services));
    return;
  }

  // ── GET /api/settings  — public: salon name for booking form ─
  if (url === '/api/settings' && req.method === 'GET') {
    const data = readData();
    const settings = data['npos_settings'] ? JSON.parse(data['npos_settings']) : {};
    // Only expose safe fields
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ salonName: settings.salonName || 'Nail Salon' }));
    return;
  }

  // ── POST /api/bookings  — booking form submits here ─────────
  if (url === '/api/bookings' && req.method === 'POST') {
    let body = '';
    req.on('data', c => body += c);
    req.on('end', () => {
      try {
        const booking = JSON.parse(body);
        const data = readData();
        const pending = data['npos_web_bookings'] ? JSON.parse(data['npos_web_bookings']) : [];
        booking.id    = Date.now() + Math.floor(Math.random() * 1000);
        booking.receivedAt = new Date().toISOString();
        booking.status = 'pending';
        pending.push(booking);
        data['npos_web_bookings'] = JSON.stringify(pending);
        writeData(data);
        console.log(`[Booking] New booking from ${booking.name} on ${booking.date} at ${booking.time}`);
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ ok: true, id: booking.id }));
      } catch (e) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end('{"error":"Invalid booking data"}');
      }
    });
    return;
  }

  // ── GET /api/bookings  — POS fetches pending web bookings ───
  if (url === '/api/bookings' && req.method === 'GET') {
    const data = readData();
    const pending = data['npos_web_bookings'] ? JSON.parse(data['npos_web_bookings']) : [];
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(pending));
    return;
  }

  // ── DELETE /api/bookings/:id  — after POS imports/dismisses ─
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

  // ── Serve static files ────────────────────────────────────
  const filePath = path.join(DIR, url === '/' ? 'index.html' : url);
  fs.readFile(filePath, (err, fileData) => {
    if (err) {
      res.writeHead(404, { 'Content-Type': 'text/plain' });
      res.end('404 Not Found');
      return;
    }
    const ext = path.extname(filePath);
    res.writeHead(200, { 'Content-Type': MIME[ext] || 'text/plain' });
    res.end(fileData);
  });
});

server.listen(PORT, '0.0.0.0', () => {
  const ip = getLocalIP();
  console.log('');
  console.log('╔════════════════════════════════════════════════════════╗');
  console.log('║              💅  Nail POS  is  Running                 ║');
  console.log('╠════════════════════════════════════════════════════════╣');
  console.log(`║  This computer                                         ║`);
  console.log(`║    POS:         http://localhost:${PORT}                  ║`);
  console.log(`║    Kiosk:       http://localhost:${PORT}/checkin.html     ║`);
  console.log(`║    Booking page: http://localhost:${PORT}/booking.html    ║`);
  console.log(`║                                                        ║`);
  console.log(`║  Other devices (same WiFi)                             ║`);
  console.log(`║    POS:         http://${ip}:${PORT}                  ║`);
  console.log(`║    Kiosk:       http://${ip}:${PORT}/checkin.html     ║`);
  console.log(`║                                                        ║`);
  console.log(`║  For website booking (needs Cloudflare Tunnel):        ║`);
  console.log(`║    Run start-tunnel.bat and paste the tunnel URL       ║`);
  console.log(`║    into your website's booking widget src.             ║`);
  console.log('╠════════════════════════════════════════════════════════╣');
  console.log('║  Press Ctrl+C to stop                                  ║');
  console.log('╚════════════════════════════════════════════════════════╝');
  console.log('');
});
