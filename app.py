"""
Nail POS — Desktop Application (Python + pywebview)
Bundles the HTTP server and opens a native window.
Data is stored in AppData so it survives re-installs.
"""

import sys, os, threading, time, json, socket, sqlite3, shutil
import urllib.request, urllib.parse, urllib.error, base64
import smtplib
from email.mime.text import MIMEText
from socketserver import ThreadingMixIn
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class ThreadingHTTPServer(ThreadingMixIn, HTTPServer):
    daemon_threads = True

# ── Paths ──────────────────────────────────────────────────────────────────────
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS          # PyInstaller temp dir (read-only bundled files)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Writable user data lives in AppData
DATA_DIR  = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'Nail POS')
os.makedirs(DATA_DIR, exist_ok=True)
DATA_FILE = os.path.join(DATA_DIR, 'data.json')
GC_DB     = os.path.join(DATA_DIR, 'giftcards.db')

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'w') as f: f.write('{}')

# Auto-create giftcards.db schema if it doesn't exist
def init_gc_db():
    conn = sqlite3.connect(GC_DB)
    conn.execute('''CREATE TABLE IF NOT EXISTS gift_cards (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gc_code TEXT UNIQUE NOT NULL,
        msr_id TEXT UNIQUE,
        cust_mobile TEXT,
        balance REAL NOT NULL DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'ACTIVE',
        created_at TEXT
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        gc_code TEXT NOT NULL,
        type TEXT NOT NULL,
        amount REAL NOT NULL,
        balance_before REAL NOT NULL,
        balance_after REAL NOT NULL,
        ticket_no TEXT,
        note TEXT,
        created_at TEXT
    )''')
    conn.commit()
    conn.close()

init_gc_db()

PORT = 3000

# ── Mime types ─────────────────────────────────────────────────────────────────
MIME = {
    '.html': 'text/html; charset=utf-8',
    '.js':   'application/javascript',
    '.css':  'text/css',
    '.json': 'application/json',
    '.png':  'image/png',
    '.ico':  'image/x-icon',
    '.svg':  'image/svg+xml',
}

_data_lock = threading.Lock()

def read_data():
    try:
        with _data_lock, open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}

def write_data(data):
    with _data_lock, open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f)

def gc_conn():
    if os.path.isfile(GC_DB):
        conn = sqlite3.connect(GC_DB)
        conn.row_factory = sqlite3.Row
        return conn
    return None

def get_settings():
    data = read_data()
    try:
        return json.loads(data.get('npos_settings', '{}'))
    except:
        return {}

def send_sms_one(sid, token, from_number, to, body):
    """Send one SMS via the Twilio REST API. Returns (ok, error_message)."""
    url = f'https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json'
    payload = urllib.parse.urlencode({'To': to, 'From': from_number, 'Body': body}).encode()
    req = urllib.request.Request(url, data=payload, method='POST')
    auth = base64.b64encode(f'{sid}:{token}'.encode()).decode()
    req.add_header('Authorization', f'Basic {auth}')
    req.add_header('Content-Type', 'application/x-www-form-urlencoded')
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp.read()
        return True, None
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode()).get('message', str(e))
        except:
            err = str(e)
        return False, err
    except Exception as e:
        return False, str(e)

def send_email_one(host, port, user, pw, from_email, from_name, to, subject, body):
    """Send one email via SMTP (STARTTLS). Returns (ok, error_message)."""
    try:
        msg = MIMEText(body, 'plain', 'utf-8')
        msg['Subject'] = subject
        msg['From'] = f'{from_name} <{from_email}>' if from_name else from_email
        msg['To'] = to
        with smtplib.SMTP(host, int(port), timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.ehlo()
            if user:
                server.login(user, pw)
            server.sendmail(from_email, [to], msg.as_string())
        return True, None
    except Exception as e:
        return False, str(e)

# ─── PAX POSLINK helpers ──────────────────────────────────────────────────────
def _lrc(data: bytes) -> int:
    v = 0
    for b in data:
        v ^= b
    return v

def _build_packet(cmd: str, fields: list) -> bytes:
    STX, ETX, FS = 0x02, 0x03, 0x1C
    body = cmd.encode() + bytes([FS])
    for i, f in enumerate(fields):
        body += str(f).encode()
        if i < len(fields) - 1:
            body += bytes([FS])
    packet = bytes([STX]) + body + bytes([ETX])
    return packet + bytes([_lrc(packet)])

def _parse_response(data: bytes) -> dict:
    """Parse POSLINK response packet into a dict."""
    STX, ETX = 0x02, 0x03
    if not data or data[0] != STX:
        return {'approved': False, 'message': 'Invalid response from terminal'}
    etx_pos = data.rfind(ETX)
    if etx_pos < 0:
        return {'approved': False, 'message': 'Malformed response'}
    payload = data[1:etx_pos].decode('ascii', errors='replace')
    parts = payload.split('\x1c')
    if len(parts) < 4:
        return {'approved': False, 'message': payload}
    resp_code = parts[2] if len(parts) > 2 else ''
    resp_msg  = parts[3] if len(parts) > 3 else ''
    auth_code = parts[4] if len(parts) > 4 else ''
    trans_id  = parts[6] if len(parts) > 6 else ''
    card_type = parts[11] if len(parts) > 11 else ''
    acct_last4 = ''
    if len(parts) > 13:
        acct = parts[13]
        acct_last4 = acct[-4:] if len(acct) >= 4 else acct
    approved  = resp_code.strip() == '000000'
    return {
        'approved':   approved,
        'code':       resp_code.strip(),
        'message':    resp_msg.strip(),
        'auth_code':  auth_code.strip(),
        'trans_id':   trans_id.strip(),
        'card_type':  card_type.strip(),
        'last4':      acct_last4,
    }

def _send_packet(ip: str, port: int, packet: bytes, timeout: int = 60) -> bytes:
    import socket as _sock
    s = _sock.socket(_sock.AF_INET, _sock.SOCK_STREAM)
    s.settimeout(timeout)
    s.connect((ip, port))
    s.sendall(packet)
    chunks = []
    while True:
        try:
            chunk = s.recv(4096)
            if not chunk:
                break
            chunks.append(chunk)
            if 0x03 in chunk:   # ETX received — response complete
                break
        except _sock.timeout:
            break
    s.close()
    return b''.join(chunks)

def poslink_sale(ip: str, port: int, amount_cents: int, tip_cents: int, ref: str) -> dict:
    """Send Credit Sale (T00) to PAX terminal."""
    fields = ['1.28', '01', str(amount_cents), str(tip_cents), '0', '0', ref, '']
    packet = _build_packet('T00', fields)
    raw = _send_packet(ip, port, packet, timeout=90)
    return _parse_response(raw)

def poslink_void(ip: str, port: int, ref: str) -> dict:
    """Send Void (T02) to PAX terminal."""
    fields = ['1.28', '17', '0', '0', '0', '0', ref, '']
    packet = _build_packet('T00', fields)
    raw = _send_packet(ip, port, packet, timeout=30)
    return _parse_response(raw)

# ── HTTP Handler (same as server.py but uses DATA_DIR paths) ──────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args): pass

    def send_cors(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def send_json(self, code, obj):
        body = json.dumps(obj).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_cors()
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def read_body(self):
        return self.rfile.read(int(self.headers.get('Content-Length', 0)))

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_cors()
        self.end_headers()

    def do_GET(self):
        parsed = urlparse(self.path)
        path   = parsed.path
        qs     = parse_qs(parsed.query)

        if path == '/api/giftcard':
            code = qs.get('code', [''])[0].strip()
            conn = gc_conn()
            if not conn:
                self.send_json(503, {'error': 'Gift card database not found'}); return
            cur = conn.cursor()
            cur.execute("SELECT gc_code,msr_id,cust_mobile,balance,status FROM gift_cards WHERE gc_code=? OR msr_id=?", (code, code))
            row = cur.fetchone(); conn.close()
            self.send_json(200, dict(row)) if row else self.send_json(404, {'error': 'Card not found'})
            return

        if path == '/api/giftcards':
            conn = gc_conn()
            if not conn:
                self.send_json(503, {'error': 'Gift card database not found'}); return
            cur = conn.cursor()
            cur.execute("SELECT gc_code,msr_id,cust_mobile,balance,status FROM gift_cards ORDER BY CASE status WHEN 'ACTIVE' THEN 0 WHEN 'PARTIALUSED' THEN 1 ELSE 2 END, gc_code")
            rows = [dict(r) for r in cur.fetchall()]; conn.close()
            self.send_json(200, rows); return

        if path == '/api/db':
            try:
                with _data_lock, open(DATA_FILE, 'rb') as f: body = f.read()
            except:
                body = b'{}'
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.send_cors()
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body); return

        if path == '/api/services':
            data = read_data()
            try: services = json.loads(data.get('npos_services', '[]'))
            except: services = []
            self.send_json(200, services); return

        if path == '/api/settings':
            data = read_data()
            try: settings = json.loads(data.get('npos_settings', '{}'))
            except: settings = {}
            self.send_json(200, {'salonName': settings.get('salonName', 'Nail Salon')}); return

        if path == '/api/bookings':
            data = read_data()
            try: pending = json.loads(data.get('npos_web_bookings', '[]'))
            except: pending = []
            self.send_json(200, pending); return

        # Static files from bundled resources
        if path == '/': path = '/index.html'
        file_path = os.path.join(BASE_DIR, path.lstrip('/'))
        if os.path.isfile(file_path):
            ext   = os.path.splitext(file_path)[1]
            ctype = MIME.get(ext, 'application/octet-stream')
            with open(file_path, 'rb') as f: body = f.read()
            self.send_response(200)
            self.send_header('Content-Type', ctype)
            self.send_cors()
            self.send_header('Content-Length', str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(404)
            self.end_headers()
            self.wfile.write(b'404 Not Found')

    def do_POST(self):
        import datetime, random
        path = urlparse(self.path).path

        if path == '/api/giftcard/new':
            try:
                body = json.loads(self.read_body())
                gc_code = body.get('gc_code', '').strip()
                msr_id  = body.get('msr_id', '').strip()
                mobile  = body.get('cust_mobile', '').strip()
                balance = float(body.get('balance', 0))
                if not gc_code:
                    conn_tmp = gc_conn()
                    cur_tmp  = conn_tmp.cursor() if conn_tmp else None
                    for _ in range(20):
                        a, b, c = random.randint(10,99), random.randint(1000,9999), random.randint(1000,9999)
                        candidate = f'{a}-{b}-{c}'
                        if cur_tmp:
                            cur_tmp.execute('SELECT 1 FROM gift_cards WHERE gc_code=?', (candidate,))
                            if cur_tmp.fetchone(): continue
                        gc_code = candidate; break
                    if conn_tmp: conn_tmp.close()
                if balance < 0:
                    self.send_json(400, {'error': 'Balance cannot be negative'}); return
                conn = gc_conn()
                if not conn:
                    self.send_json(503, {'error': 'Gift card database not found'}); return
                cur = conn.cursor()
                cur.execute("SELECT id FROM gift_cards WHERE gc_code=?", (gc_code,))
                if cur.fetchone():
                    conn.close(); self.send_json(400, {'error': f'Card {gc_code} already exists'}); return
                if msr_id:
                    cur.execute("SELECT id FROM gift_cards WHERE msr_id=?", (msr_id,))
                    if cur.fetchone():
                        conn.close(); self.send_json(400, {'error': f'MSR ID {msr_id} already exists'}); return
                now    = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                status = 'ACTIVE' if balance > 0 else 'USED'
                cur.execute("INSERT INTO gift_cards(gc_code,msr_id,cust_mobile,balance,status,created_at) VALUES(?,?,?,?,?,?)",
                            (gc_code, msr_id or None, mobile or None, balance, status, now))
                cur.execute("INSERT INTO transactions(gc_code,type,amount,balance_before,balance_after,ticket_no,note,created_at) VALUES(?,?,?,?,?,?,?,?)",
                            (gc_code,'NEW',balance,0,balance,'','New card',now))
                conn.commit(); conn.close()
                self.send_json(200, {'ok': True, 'gc_code': gc_code, 'balance': balance, 'status': status})
            except Exception as e:
                self.send_json(400, {'error': str(e)})
            return

        if path == '/api/giftcard/charge':
            try:
                import datetime
                body   = json.loads(self.read_body())
                code   = body.get('code','').strip()
                amount = float(body.get('amount', 0))
                ticket = body.get('ticket_no', '')
                conn   = gc_conn()
                if not conn: self.send_json(503, {'error': 'Gift card database not found'}); return
                cur = conn.cursor()
                cur.execute("SELECT id,gc_code,balance,status FROM gift_cards WHERE gc_code=? OR msr_id=?", (code, code))
                row = cur.fetchone()
                if not row: conn.close(); self.send_json(404, {'error': 'Card not found'}); return
                if row['status'] == 'USED': conn.close(); self.send_json(400, {'error': 'Card is fully used'}); return
                bal_before = row['balance']
                if amount > bal_before: conn.close(); self.send_json(400, {'error': f'Insufficient balance (${bal_before:.2f})'}); return
                bal_after  = round(bal_before - amount, 2)
                new_status = 'USED' if bal_after == 0 else 'PARTIALUSED'
                now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cur.execute("UPDATE gift_cards SET balance=?,status=? WHERE id=?", (bal_after, new_status, row['id']))
                cur.execute("INSERT INTO transactions(gc_code,type,amount,balance_before,balance_after,ticket_no,note,created_at) VALUES(?,?,?,?,?,?,?,?)",
                            (row['gc_code'],'CHARGE',amount,bal_before,bal_after,ticket,'POS charge',now))
                conn.commit(); conn.close()
                self.send_json(200, {'ok': True, 'gc_code': row['gc_code'], 'balance_before': bal_before, 'balance_after': bal_after, 'charged': amount})
            except Exception as e:
                self.send_json(400, {'error': str(e)})
            return

        if path == '/api/giftcard/refill':
            try:
                import datetime
                body   = json.loads(self.read_body())
                code   = body.get('code','').strip()
                amount = float(body.get('amount', 0))
                if amount <= 0: self.send_json(400, {'error': 'Amount must be positive'}); return
                conn = gc_conn()
                if not conn: self.send_json(503, {'error': 'Gift card database not found'}); return
                cur = conn.cursor()
                cur.execute("SELECT id,gc_code,balance FROM gift_cards WHERE gc_code=? OR msr_id=?", (code, code))
                row = cur.fetchone()
                if not row: conn.close(); self.send_json(404, {'error': 'Card not found'}); return
                bal_before = row['balance']
                bal_after  = round(bal_before + amount, 2)
                now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                cur.execute("UPDATE gift_cards SET balance=?,status='ACTIVE' WHERE id=?", (bal_after, row['id']))
                cur.execute("INSERT INTO transactions(gc_code,type,amount,balance_before,balance_after,ticket_no,note,created_at) VALUES(?,?,?,?,?,?,?,?)",
                            (row['gc_code'],'REFILL',amount,bal_before,bal_after,'','POS refill',now))
                conn.commit(); conn.close()
                self.send_json(200, {'ok': True, 'gc_code': row['gc_code'], 'balance_before': bal_before, 'balance_after': bal_after})
            except Exception as e:
                self.send_json(400, {'error': str(e)})
            return

        if path == '/api/db':
            # Merged (not replaced) so server-owned keys the browser never
            # tracks (e.g. npos_web_bookings, managed via /api/bookings)
            # survive a save instead of being wiped out.
            try:
                incoming = json.loads(self.read_body())
                existing = read_data()
                existing.update(incoming)
                write_data(existing)
                self.send_json(200, {'ok': True})
            except:
                self.send_json(400, {'error': 'Invalid JSON'})
            return

        if path == '/api/bookings':
            try:
                import datetime, random
                booking = json.loads(self.read_body())
                data    = read_data()
                try: pending = json.loads(data.get('npos_web_bookings', '[]'))
                except: pending = []
                booking['id']         = int(time.time() * 1000) + random.randint(0, 999)
                booking['receivedAt'] = datetime.datetime.utcnow().isoformat() + 'Z'
                booking['status']     = 'pending'
                pending.append(booking)
                data['npos_web_bookings'] = json.dumps(pending)
                write_data(data)
                self.send_json(200, {'ok': True, 'id': booking['id']})
            except Exception as e:
                self.send_json(400, {'error': str(e)})
            return

        if path == '/api/giftcard/delete':
            try:
                body = json.loads(self.read_body())
                code = body.get('code', '').strip()
                conn = gc_conn()
                if not conn:
                    self.send_json(503, {'error': 'DB not found'}); return
                conn.execute("DELETE FROM gift_cards WHERE gc_code=?", (code,))
                conn.execute("DELETE FROM transactions WHERE gc_code=?", (code,))
                conn.commit(); conn.close()
                self.send_json(200, {'ok': True})
            except Exception as e:
                self.send_json(400, {'error': str(e)})
            return

        # POST /api/terminal/ping — check if PAX terminal is reachable
        if path == '/api/terminal/ping':
            try:
                import socket as _sock
                body = json.loads(self.read_body())
                ip   = body.get('ip', '').strip()
                port = int(body.get('port', 10009))
                if not ip:
                    self.send_json(400, {'error': 'IP required'}); return
                s = _sock.socket(_sock.AF_INET, _sock.SOCK_STREAM)
                s.settimeout(3)
                result = s.connect_ex((ip, port))
                s.close()
                if result == 0:
                    self.send_json(200, {'ok': True, 'message': f'Terminal reachable at {ip}:{port}'})
                else:
                    self.send_json(200, {'ok': False, 'message': f'Cannot reach terminal at {ip}:{port}. Check IP and that terminal is on.'})
            except Exception as e:
                self.send_json(200, {'ok': False, 'message': str(e)})
            return

        # POST /api/terminal/sale — send credit sale to PAX via POSLINK
        if path == '/api/terminal/sale':
            try:
                body   = json.loads(self.read_body())
                ip     = body.get('ip', '').strip()
                port   = int(body.get('port', 10009))
                amount = int(round(float(body.get('amount', 0)) * 100))
                tip    = int(round(float(body.get('tip', 0)) * 100))
                ref    = str(body.get('ref', '001')).zfill(6)
                if not ip:
                    self.send_json(400, {'error': 'Terminal IP not set. Go to Settings → Terminal.'}); return
                if amount <= 0:
                    self.send_json(400, {'error': 'Amount must be greater than 0'}); return
                result = poslink_sale(ip, port, amount, tip, ref)
                self.send_json(200, result)
            except Exception as e:
                self.send_json(500, {'error': str(e)})
            return

        # POST /api/terminal/void — void last transaction
        if path == '/api/terminal/void':
            try:
                body = json.loads(self.read_body())
                ip   = body.get('ip', '').strip()
                port = int(body.get('port', 10009))
                ref  = str(body.get('ref', '001')).zfill(6)
                if not ip:
                    self.send_json(400, {'error': 'Terminal IP not set'}); return
                result = poslink_void(ip, port, ref)
                self.send_json(200, result)
            except Exception as e:
                self.send_json(500, {'error': str(e)})
            return

        # POST /api/sms/send  {to:[phone,...], body}
        if path == '/api/sms/send':
            try:
                body = json.loads(self.read_body())
                to_list = body.get('to', [])
                text = (body.get('body') or '').strip()
                if not to_list or not text:
                    self.send_json(400, {'error': 'Missing recipients or message body'}); return
                s = get_settings()
                sid, token, frm = s.get('smsAccountSid', ''), s.get('smsAuthToken', ''), s.get('smsFromNumber', '')
                if not (sid and token and frm):
                    self.send_json(400, {'error': 'SMS provider not configured yet — add your Twilio credentials in Settings → Messaging.'}); return
                sent, failed = [], []
                for to in to_list:
                    ok, err = send_sms_one(sid, token, frm, to, text)
                    (sent if ok else failed).append(to if ok else {'to': to, 'error': err})
                self.send_json(200, {'ok': True, 'sent': len(sent), 'failed': failed})
            except Exception as e:
                self.send_json(400, {'error': str(e)})
            return

        # POST /api/email/send  {to:[email,...], subject, body}
        if path == '/api/email/send':
            try:
                body = json.loads(self.read_body())
                to_list = body.get('to', [])
                subject = (body.get('subject') or '').strip() or '(no subject)'
                text = (body.get('body') or '').strip()
                if not to_list or not text:
                    self.send_json(400, {'error': 'Missing recipients or message body'}); return
                s = get_settings()
                host, port, user, pw, from_email = s.get('smtpHost', ''), s.get('smtpPort', 587), s.get('smtpUser', ''), s.get('smtpPass', ''), s.get('smtpFromEmail', '')
                if not (host and from_email):
                    self.send_json(400, {'error': 'Email provider not configured yet — add your SMTP details in Settings → Messaging.'}); return
                from_name = s.get('salonName', '')
                sent, failed = [], []
                for to in to_list:
                    ok, err = send_email_one(host, port, user, pw, from_email, from_name, to, subject, text)
                    (sent if ok else failed).append(to if ok else {'to': to, 'error': err})
                self.send_json(200, {'ok': True, 'sent': len(sent), 'failed': failed})
            except Exception as e:
                self.send_json(400, {'error': str(e)})
            return

        self.send_json(404, {'error': 'Not found'})

    def do_DELETE(self):
        path = urlparse(self.path).path
        if path.startswith('/api/bookings/'):
            try:
                bid  = int(path.replace('/api/bookings/', ''))
                data = read_data()
                try: pending = json.loads(data.get('npos_web_bookings', '[]'))
                except: pending = []
                pending = [b for b in pending if b.get('id') != bid]
                data['npos_web_bookings'] = json.dumps(pending)
                write_data(data)
                self.send_json(200, {'ok': True})
            except:
                self.send_json(400, {'error': 'Bad id'})
            return
        self.send_json(404, {'error': 'Not found'})


# ── Start server in background ────────────────────────────────────────────────
# Bind on the main thread first so we know for certain the socket is listening
# before the window opens (a fixed sleep() before this was flaky on slower
# first-run machines, e.g. macOS scanning an unsigned binary via Gatekeeper).
try:
    httpd = ThreadingHTTPServer(('127.0.0.1', PORT), Handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
except OSError:
    # Port already in use — most likely another instance of this app is
    # already running and serving it; fall through and point the window at it.
    pass

# ── Open native window ────────────────────────────────────────────────────────
import webview

webview.create_window(
    'Nail POS',
    f'http://127.0.0.1:{PORT}',
    width=1400,
    height=900,
    min_size=(900, 600),
)
webview.start()
