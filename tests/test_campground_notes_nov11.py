#!/usr/bin/env python3
"""Nov 11 (data-quality review): kpc_campground_notes.py
  * a sheet without the review columns (a form question renamed, 'Publish to web' off so Google sends a web page, the wrong link) gave
    zero reviews and the run SAVED that: every published review vanished. Now it exits 1, says what is missing, and writes nothing.
  * the net guard is installed before the first request (it sat below the sheet download).
  * a sheet with no 'park number' column crashed on 'parkno.near'.
The script is run in a temp folder against a tiny web server on 127.0.0.1 (the net guard allows only that kind of host in this test)."""
import http.server, json, os, pathlib, subprocess, sys, tempfile, threading

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCR = ROOT / '.github' / 'scripts' / 'kpc_campground_notes.py'
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


src = SCR.read_text(encoding='utf-8')
check(src.index('kpc_net_guard.install()') < src.index('get(URL)'), 'the net guard is installed before the first request (file order)')

BODY = {'csv': b''}


class H(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.send_header('Content-Type', 'text/csv'); self.end_headers(); self.wfile.write(BODY['csv'])
    def log_message(self, *a): pass


srv = http.server.HTTPServer(('127.0.0.1', 0), H)
threading.Thread(target=srv.serve_forever, daemon=True).start()
URL = f'http://127.0.0.1:{srv.server_port}/sheet.csv'


def run(csv_text, old_notes=None):
    d = pathlib.Path(tempfile.mkdtemp(prefix='kpc-cgn-'))
    (d / 'kpc-campgrounds.json').write_text(json.dumps({'parks': [{'pota': 'US-0001', 'campgrounds': [{'id': 'pine', 'name': 'Pine Camp'}], 'lodging': []}]}))
    if old_notes is not None: (d / 'kpc-campground-notes.json').write_text(json.dumps(old_notes))
    BODY['csv'] = csv_text.encode()
    env = dict(os.environ, CAMPGROUND_SHEET_CSV=URL, PYTHONPATH=os.pathsep.join([str(SCR.parent)] + [x for x in [os.environ.get('PYTHONPATH')] if x]))   # keeps a net spy on the path
    r = subprocess.run([sys.executable, '-B', str(SCR)], cwd=d, env=env, capture_output=True, text=True, timeout=120)
    out = None
    try: out = json.loads((d / 'kpc-campground-notes.json').read_text())
    except Exception: pass
    return r, out


OLD = {'updated': '2026-11-10', 'notes': [{'id': 'x1', 'call': 'W1AW', 'text': 'A published review', 'place': 'pine'}]}
GOOD = ('Timestamp,Call sign,What are you reviewing,Campground or cabin,Rating,Your review,Approved\n'
        '11/10/2026 10:00:00,W1AW,Campground,US-0001 · Pine Camp,5,Lovely quiet loop,YES\n')

r, out = run(GOOD, OLD)
check(r.returncode == 0 and out and len(out['notes']) == 1 and out['notes'][0]['call'] == 'W1AW' and out['notes'][0]['place'] == 'pine' and out['notes'][0]['text'] == 'Lovely quiet loop',
      f"a good sheet is published as before (rc {r.returncode}; {r.stderr[-200:]})")
check(out['notes'][0].get('near') is None, 'a sheet with no park-number column does not crash on parkno.near')

renamed = GOOD.replace('Call sign', 'Your callsign').replace('Campground or cabin', 'Place')
renamed_csv = 'Timestamp,Your callsign,What are you reviewing,Camp spot,Stars,Comments,Approved\n11/10/2026 10:00:00,W1AW,Campground,Pine,5,Lovely,YES\n'
r, out = run(renamed_csv, OLD)
check(r.returncode == 1 and '::error title=Campground reviews::' in r.stdout and 'Call sign' in r.stdout, f'form question renamed: exit 1 with a plain error ({r.returncode})')
check(out == OLD, 'form question renamed: the published reviews are untouched')

r, out = run('<!DOCTYPE html><html><body>Sign in to Google</body></html>\n', OLD)
check(r.returncode == 1 and out == OLD, 'Google sent a web page instead of the CSV: exit 1, nothing changed')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
