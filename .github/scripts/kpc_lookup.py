#!/usr/bin/env python3
"""KPC SHARED LOOK-UP BOT (chat 10, Oct 29 2026; HQ 12:00 PM, Brandon 11:59 AM GO: 'think more people need a look up bot').
Chat sessions see only part of the web, so any chat writes a small REQUEST file and a GitHub runner (open internet, a real
headless browser) answers it. Each request is its OWN job (kpc-lookup.yml, a matrix, up to 4 at once), so a big request never
blocks a small one. No timers: a request runs when its file is pushed (or by hand).

REQUEST  .claude/lookup/requests/<chat>-<id>.json, e.g.
  {"chat": 11, "kind": "page", "urls": ["https://app.fw.ky.gov/..."], "screenshot": true, "report": "is the area closed?"}
  kind  page        read each page in a real browser: title, visible text (first 15,000 characters), links, optional screenshot
        map-check   the same + always a screenshot (for checkers who must SEE an agency map)
        layer-probe ArcGIS layers: does it answer, geometry, name field, record count, licence, dates (chat 9's probe)
        parcel      which features of a layer hold a point: {"layer": url, "points": [[lat, lon], ...], "fields": "*"}
        probe       a whole chat-9 probe config (layers / searches / pointq / pinhunt / ...), run by kpc_adds_probe.py
ANSWER   .claude/lookup/answers/<chat>-<id>.json (+ <chat>-<id>-<n>.png) and ONE line under '## OPEN' in .claude/inbox/
         chat-<chat>.md: '- FROM LOOK-UP BOT (<date>): <id> answered: <short> -> <answer file>'.
MANNERS  kpc_manners.py (KPC-Data): robots.txt obeyed (exemptions: ArcGIS REST, ridb.recreation.gov/api, developer.nps.gov/api),
         2 s per host, three strikes = leave the host alone. Never fails loudly (exit 0). Answers kept small.
  python3 kpc_lookup.py run <request path>     answer one request
  python3 kpc_lookup.py post <request path>    add its inbox line (run after a git pull, inside the save loop)
  python3 kpc_lookup.py todo                   print requests that have no answer yet (JSON list) for the matrix"""
import json, os, pathlib, re, sys, time, urllib.parse

ROOT = pathlib.Path(os.environ.get('LOOKUP_ROOT') or '.claude/lookup')
REQ, ANS = ROOT / 'requests', ROOT / 'answers'
INBOX = pathlib.Path('.claude/inbox')
TEXT_MAX, LINKS_MAX, URLS_MAX = 15000, 150, 25
sys.path.insert(0, os.environ.get('MANNERS_DIR') or '../kpcdata/.github/scripts')
sys.path.insert(0, '.github/scripts')
try:
    from kpc_manners import Manners, page_text, links_in
    M = Manners('shared look-up bot')
except Exception:  # noqa: BLE001  (no manners module = no network work at all: fail closed, say so)
    M = None


def notice(m): print('::notice title=Look-up bot::' + str(m).replace('\n', ' ')[:900], flush=True)


def ans_path(req): return ANS / (pathlib.Path(req).stem + '.json')


def todo():
    out = []
    for p in sorted(REQ.glob('*.json')) if REQ.exists() else []:
        if not ans_path(p).exists(): out.append(str(p))
    print(json.dumps(out[:20]))


_BR = None
def browser():
    global _BR
    if _BR is None:
        try:
            from playwright.sync_api import sync_playwright
            pw = sync_playwright().start(); b = pw.chromium.launch()
            _BR = b.new_context(viewport={'width': 1280, 'height': 900}, user_agent=M.ua if M else 'KPC look-up bot')
        except Exception as e:  # noqa: BLE001
            _BR = False; notice(f'no browser ({type(e).__name__}): plain reads only')
    return _BR


PDF_PAGES = 3


def pdf_answer(r, body, shot_path):
    """chat 3 (Oct 29 3:50 PM): a PDF comes back as text + pages 1-3 rendered to PNG (so a checker can SEE the boundary). Poppler
    (pdftotext / pdftoppm), about 1600 px on the long side."""
    import subprocess, tempfile
    r['kind'] = 'pdf'; r['bytes'] = len(body)
    with tempfile.TemporaryDirectory() as td:
        f = pathlib.Path(td) / 'in.pdf'; f.write_bytes(body)
        try:
            info = subprocess.run(['pdfinfo', str(f)], capture_output=True, text=True, timeout=60).stdout
            m = re.search(r'^Pages:\s+(\d+)', info, re.M); r['pages'] = int(m.group(1)) if m else None
            r['text'] = subprocess.run(['pdftotext', '-f', '1', '-l', str(PDF_PAGES), '-layout', str(f), '-'], capture_output=True, text=True, timeout=120).stdout[:TEXT_MAX]
            if shot_path:
                base = str(shot_path)[:-4]
                subprocess.run(['pdftoppm', '-f', '1', '-l', str(PDF_PAGES), '-png', '-scale-to', '1600', str(f), base + '-p'], capture_output=True, timeout=300)
                shots = sorted(str(q) for q in pathlib.Path(base).parent.glob(pathlib.Path(base).name + '-p*.png'))
                r['screenshots'] = shots; r['screenshot'] = shots[0] if shots else None
        except Exception as e:  # noqa: BLE001
            r['pdf_error'] = f'{type(e).__name__}: {str(e)[:120]}'
    return r


def read_page(u, shot_path=None):
    r = {'url': u}
    if not M: r['status'] = 'no manners module: not read'; return r
    h = M.host(u)
    if M.dead.get(h, 0) > time.time(): r['status'] = 'host left alone (strikes)'; return r
    if not M.robots_ok(u): r['status'] = 'robots.txt says no'; return r
    w = M.gap - (time.time() - M.last.get(h, 0))
    if w > 0: time.sleep(w)
    M.last[h] = time.time()
    if re.search(r'\.pdf(?:$|[?#])|/download(?:$|[?#])', u, re.I):   # a PDF (or a /download link): read the bytes, render pages
        st, hd, body, final = M.get(u, accept='application/pdf,*/*')
        r['status'] = st; r['final_url'] = final; r['read_by'] = 'plain read'
        if body[:5] == b'%PDF-' or 'pdf' in str(hd.get('content-type', '')).lower(): return pdf_answer(r, body, shot_path)
        if isinstance(st, int) and st < 400 and body: r['text'] = page_text(body.decode('utf-8', 'replace'))[:TEXT_MAX]; return r
    ctx = browser()
    if ctx:
        try:
            pg = ctx.new_page()
            resp = pg.goto(u, wait_until='domcontentloaded', timeout=60000)
            try: pg.wait_for_load_state('networkidle', timeout=20000)
            except Exception: pass  # noqa: BLE001
            r['status'] = resp.status if resp else 'no response'
            r['final_url'] = pg.url; r['title'] = (pg.title() or '')[:200]
            txt = pg.inner_text('body') if pg.query_selector('body') else ''
            r['text'] = '\n'.join(' '.join(l.split()) for l in txt.split('\n') if l.strip())[:TEXT_MAX]
            r['links'] = [{'url': a, 'text': t[:100]} for a, t in pg.eval_on_selector_all('a[href]', 'els => els.map(e => [e.href, e.innerText])')
                          if a.startswith('http')][:LINKS_MAX]
            if shot_path:
                pg.screenshot(path=str(shot_path), full_page=False); r['screenshot'] = str(shot_path)
            pg.close(); r['read_by'] = 'headless browser'
            return r
        except Exception as e:  # noqa: BLE001
            r['browser_error'] = f'{type(e).__name__}: {str(e)[:120]}'
    st, hd, body, final = M.get(u)
    r['status'] = st; r['final_url'] = final; r['read_by'] = 'plain read'
    if isinstance(st, int) and st < 400 and body:
        html = body.decode('utf-8', 'replace')
        m = re.search(r'<title[^>]*>(.*?)</title>', html, re.I | re.S); r['title'] = ' '.join((m.group(1) if m else '').split())[:200]
        r['text'] = page_text(html)[:TEXT_MAX]
        r['links'] = [{'url': a, 'text': t} for a, t in links_in(html, final)][:LINKS_MAX]
    return r


def arc(u, params):
    st, hd, body, final = M.get(u + ('&' if '?' in u else '?') + urllib.parse.urlencode({**params, 'f': 'json'}), accept='application/json')
    if not (isinstance(st, int) and st < 400): raise RuntimeError(f'no answer ({st})')
    j = json.loads(body.decode('utf-8', 'replace'))
    if isinstance(j, dict) and j.get('error'): raise RuntimeError(str(j['error'])[:140])
    return j


OWNER_RX = r'^(?:own(?:er)?(?:_?name)?\d?|owner1|ownername|own_nm|deeded_?owner|grantee|taxpayer(?:_?name)?|mail(?:ing)?_?name|ownernme1?)$|owner'
PARCEL_RX = r'^(?:parcel(?:_?id|_?no|_?num(?:ber)?)?|pin|apn|parid|par_id|pidn?|parcelnumb|map_?par(?:cel)?|tax_?id|account(?:_?no)?)$|parcel'


def do_parcel(q):
    lay = q['layer'].rstrip('/'); out = []
    for la, lo in (q.get('points') or [])[:50]:
        try:
            j = arc(lay + '/query', {'geometry': f'{lo},{la}', 'geometryType': 'esriGeometryPoint', 'inSR': 4326, 'spatialRel': 'esriSpatialRelIntersects',
                                     'outFields': q.get('fields') or '*', 'returnGeometry': 'false'})
            feats = [f.get('attributes') or {} for f in (j.get('features') or [])][:10]
            pick = lambda a, rx: next((str(v) for k, v in a.items() if v not in (None, '') and re.search(rx, k, re.I)), None)
            out.append({'point': [la, lo], 'owner': [pick(a, OWNER_RX) for a in feats], 'parcel_id': [pick(a, PARCEL_RX) for a in feats],
                        'features': feats})   # P-3 (HQ 6:20 PM): owner + parcel id per point, the full record kept beside them
        except Exception as e: out.append({'point': [la, lo], 'error': str(e)[:140]})  # noqa: BLE001
    return out


def run(req):
    q = json.load(open(req))
    rid = pathlib.Path(req).stem; kind = q.get('kind') or 'page'
    ANS.mkdir(parents=True, exist_ok=True)
    out = {'request': str(req), 'id': rid, 'chat': q.get('chat'), 'kind': kind, 'report': q.get('report') or '', 'asked': q,
           'answered': time.strftime('%Y-%m-%d %H:%MZ', time.gmtime()), 'results': []}
    t0 = time.time()
    try:
        if kind in ('page', 'map-check'):
            for i, u in enumerate((q.get('urls') or [])[:URLS_MAX]):
                shot = ANS / f'{rid}-{i + 1}.png' if (kind == 'map-check' or q.get('screenshot')) else None
                out['results'].append(read_page(u, shot))
        elif kind == 'layer-probe':
            import kpc_adds_probe as P
            for x in (q.get('layers') or [])[:URLS_MAX]:
                x = x if isinstance(x, dict) else {'url': x}
                try: out['results'].append(P.layer({'st': x.get('st', ''), 'kind': x.get('kind', ''), **x}))
                except Exception as e: out['results'].append({'url': x.get('url'), 'error': str(e)[:140]})  # noqa: BLE001
        elif kind == 'parcel':
            out['results'] = do_parcel(q)
        elif kind == 'probe':
            import kpc_adds_probe as P
            tmp = pathlib.Path('/tmp') / f'{rid}.json'; tmp.write_text(json.dumps(q.get('probe') or q))
            P.CAND = tmp; P.OUT = tmp.with_name(tmp.stem + '-tested.json'); P.main()
            out['results'] = json.load(open(P.OUT)) if P.OUT.exists() else {'error': 'the probe wrote nothing'}
        else: out['error'] = f'unknown kind {kind} (page, map-check, layer-probe, parcel, probe)'
    except Exception as e: out['error'] = f'{type(e).__name__}: {str(e)[:200]}'  # noqa: BLE001
    out['seconds'] = round(time.time() - t0)
    if M: out['manners'] = M.stat
    res = out['results'] if isinstance(out['results'], list) else [out['results']]
    ok = sum(1 for r in res if isinstance(r, dict) and not r.get('error') and (not isinstance(r.get('status'), (int, str)) or (isinstance(r.get('status'), int) and r['status'] < 400)))
    out['short'] = out.get('error') or f"{len(res)} result(s), {ok} read OK" + (f", {sum(1 for r in res if isinstance(r, dict) and r.get('screenshot'))} screenshot(s)" if kind in ('page', 'map-check') else '')
    ans_path(req).write_text(json.dumps(out, indent=1, ensure_ascii=False)[:3_000_000] + '\n')
    notice(f'{rid}: {out["short"]} in {out["seconds"]} s')


def post(req):
    a = ans_path(req)
    if not a.exists(): return
    out = json.load(open(a)); chat = out.get('chat') or pathlib.Path(req).stem.split('-')[0]
    ib = INBOX / f'chat-{chat}.md'
    if not ib.exists(): notice(f'no inbox for chat {chat}: answer kept at {a}'); return
    line = f"- FROM LOOK-UP BOT ({out['answered'][:10]}): {out['id']} answered: {out.get('short', '')} -> {a}"
    x = ib.read_text(encoding='utf-8')
    if f"{out['id']} answered:" in x: return
    m = re.search(r'^## OPEN[^\n]*\n', x, re.M)
    x = (x[:m.end()] + line + '\n' + x[m.end():]) if m else (line + '\n' + x)
    ib.write_text(x, encoding='utf-8')


if __name__ == '__main__':
    a = sys.argv[1:] or ['todo']
    try:
        if a[0] == 'todo': todo()
        elif a[0] == 'run': run(a[1])
        elif a[0] == 'post': post(a[1])
    except Exception as e:  # noqa: BLE001
        notice(f'stopped ({type(e).__name__}: {str(e)[:200]})')
    sys.exit(0)
