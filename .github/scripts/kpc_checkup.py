#!/usr/bin/env python3
"""KPC CHECK-UP parts (chat 5, Oct 26 2026; Brandon GO 11:50 AM: 'grow the daily bot-health check into a nightly check-up').

Each part is run as its own workflow step and writes checkup-out/<part>.json:
  {"part": ..., "date": ..., "problems": [{"key", "chat", "msg"}], "notes": [{"chat", "msg"}], "ok": [...]}
kpc_bot_health.py then puts every part into ONE issue body, grouped by chat. A 'problem' is a real fault that
someone must fix (a NEW one is the only thing that emails Brandon); a 'note' is for the report only.

  guard   DAILY.  Public-list guard: every page that is NOT on kpc-gate.js's PUBLIC list must load the gate and carry
                  noindex (members only, hidden from Google); every PUBLIC page must exist, load the gate and NOT carry
                  noindex (except 404 and the beta rooms, which have their own password).
  refs    SUNDAY. Reference check for every US state + Canadian province: park numbers in our data files (answer
                  keys, access points, 2-fer spots, state camps, trails) that POTA no longer lists (retired), and key
                  rows whose park name no longer matches POTA's (renamed). Kentucky's own ref-check bot stays as is.
  links   SUNDAY. Data link check: the official map-server addresses our bots read (state-gis, access, trails,
                  camps, trails-hand, land-owner layers) must still answer; holiday pictures must exist; plus a summary
                  of chat 2's monthly map-link results in parkinfo-web.json (not re-fetched). A server that fails is
                  only a PROBLEM when it also failed the Sunday before (servers have bad days).

Read-only: it never changes the files it checks. Never fails (exit 0).
"""
import datetime as dt
import glob
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.request

OUT = pathlib.Path('checkup-out')
TODAY = dt.date.today().isoformat()
UA = {'User-Agent': 'Mozilla/5.0 (compatible; KPC check-up; kentuckyportableclub.github.io)', 'Accept': '*/*'}


def load(p, d=None):
    try:
        return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
    except Exception:  # noqa: BLE001
        return d


def write(part, problems, notes, ok):
    OUT.mkdir(exist_ok=True)
    (OUT / f'{part}.json').write_text(json.dumps({'part': part, 'date': TODAY, 'problems': problems, 'notes': notes,
                                                  'ok': ok}, indent=1, ensure_ascii=False), encoding='utf-8')
    print(f'::notice title=Check-up {part}::{len(problems)} problem(s), {len(notes)} note(s)', flush=True)


# ---------------------------------------------------------------- guard (daily)
def public_list():
    g = pathlib.Path('kpc-gate.js').read_text(encoding='utf-8')
    m = re.search(r'var PUBLIC = \[(.*?)\];', g, re.S)
    return set(re.findall(r"'([\w.-]+\.html)'", m.group(1))) if m else set()


def guard():
    problems, notes = [], []
    pub = public_list()
    if not pub:
        write('guard', [{'key': 'guard:no-public-list', 'chat': 1, 'msg': 'kpc-gate.js: could not read the PUBLIC list'}], [], [])
        return
    pages = sorted(p.name for p in pathlib.Path('.').glob('*.html'))
    n_pub = n_priv = 0
    for p in pages:
        t = pathlib.Path(p).read_text(encoding='utf-8', errors='replace')
        head = t[:t.find('</head>')] if '</head>' in t else t[:30000]
        gate = re.search(r'<script[^>]+src="kpc-gate\.js', head) is not None
        noindex = re.search(r'<meta[^>]+name=["\']robots["\'][^>]*noindex', head, re.I) is not None
        own_lock = 'data-lock=' in t and 'kpc-vip.js' in t        # beta rooms: their own password on top
        if not gate:
            problems.append({'key': f'guard:nogate:{p}', 'chat': 1,
                             'msg': f'{p}: does not load kpc-gate.js in its head, so ' + ('guests are not handled' if p in pub else 'it is OPEN to the public')})
        if p in pub:
            n_pub += 1
            if noindex and p != '404.html' and not own_lock:
                problems.append({'key': f'guard:pubnoindex:{p}', 'chat': 1,
                                 'msg': f'{p}: on the PUBLIC list but tells Google not to index it (noindex)'})
        else:
            n_priv += 1
            if not noindex and not re.search(r'HOLD\.html$', p):
                problems.append({'key': f'guard:privindex:{p}', 'chat': 1,
                                 'msg': f'{p}: members-only page with no noindex, so Google may list it (add <meta name="robots" content="noindex,nofollow">)'})
    for p in sorted(pub):
        if not pathlib.Path(p).is_file():
            problems.append({'key': f'guard:pubmissing:{p}', 'chat': 1, 'msg': f'{p}: on the PUBLIC list but the page does not exist'})
    for p in pages:
        if re.search(r'HOLD\.html$', p):
            notes.append({'chat': 1, 'msg': f'{p}: a HOLD page (members only, no noindex on purpose until it goes public)'})
    write('guard', problems, notes, [f'{n_pub} public pages and {n_priv} members-only pages checked'])


# ---------------------------------------------------------------- refs (Sunday)
def norm(s):
    return re.sub(r'[^a-z0-9]', '', str(s).lower())


def refs():
    cur = {}
    for r in (load('locations.json', []) or []) + ((load('data/canada.json', {}) or {}).get('rows') or []):
        if isinstance(r, list) and len(r) > 2 and r[0] == 'POTA':
            cur[r[1]] = r[2]
    if len(cur) < 10000:
        write('refs', [], [{'chat': 2, 'msg': f'Reference check skipped: only {len(cur)} US + Canada parks in locations.json / data/canada.json'}], [])
        return
    gone, renamed = {}, {}

    def chk(src, st, ref, name=None):
        if not re.match(r'^(US|CA)-\d{4,5}$', str(ref)):
            return
        if ref not in cur:
            gone.setdefault(st, {}).setdefault(ref, set()).add(src)
        elif name and norm(name) != norm(cur[ref]):
            renamed.setdefault(st, {})[ref] = (name, cur[ref])

    for f in glob.glob('data/us-key/US-*.json') + glob.glob('data/ca-key/CA-*.json'):
        st = pathlib.Path(f).stem
        for ref, e in ((load(f, {}) or {}).get('parks') or {}).items():
            chk('answer key', st, ref, (e or {}).get('n'))
    for f in glob.glob('data/access/*.json'):
        st = pathlib.Path(f).stem
        for ref in ((load(f, {}) or {}).get('parks') or {}):
            chk('access points', st, ref)
    for f in glob.glob('data/fers/*.json'):
        st = pathlib.Path(f).stem
        for s in ((load(f, {}) or {}).get('spots') or []):
            for ref in (s or {}).get('refs') or []:
                chk('2-fer spots', st, ref)
    for f in glob.glob('data/campstate*/*.json'):
        st = pathlib.Path(f).stem
        if not re.match(r'^(US|CA)-[A-Z]{2}$', st):
            continue
        for row in json.dumps(load(f, {})).split('"'):
            if re.fullmatch(r'(US|CA)-\d{4,5}', row):
                chk('state camps', st, row)
    for f in glob.glob('data/trails/*.json'):
        ref = pathlib.Path(f).stem
        if re.fullmatch(r'(US|CA)-\d{4,5}', ref):
            chk('trail lines', 'trails', ref)
    problems, notes = [], []
    for st in sorted(gone):
        items = sorted(gone[st].items())
        txt = ', '.join(f"{r} ({'/'.join(sorted(s))})" for r, s in items[:12]) + (f' +{len(items) - 12} more' if len(items) > 12 else '')
        problems.append({'key': f'refs:gone:{st}:' + ','.join(r for r, _ in items), 'chat': 2,
                         'msg': f'{st}: {len(items)} park number(s) POTA no longer lists, still in our data: {txt}'})
    for st in sorted(renamed):
        items = sorted(renamed[st].items())
        txt = '; '.join(f'{r} ours "{a}" / POTA "{b}"' for r, (a, b) in items[:6]) + (f' +{len(items) - 6} more' if len(items) > 6 else '')
        notes.append({'chat': 2, 'msg': f'{st}: {len(items)} name(s) differ from POTA (renamed or spelled differently): {txt}'})
    write('refs', problems, notes, [f'{len(cur)} current US + Canada parks compared with the answer keys, access points, 2-fer spots, state camps and trails'])


# ---------------------------------------------------------------- links (Sunday)
def answer(url):
    """'ok' or what went wrong. ArcGIS REST addresses are asked for their description (?f=json)."""
    rest = '/rest/services' in url.lower()
    u = url.split('?')[0] + '?f=json' if rest else url
    try:
        req = urllib.request.Request(u, headers=UA)
        with urllib.request.urlopen(req, timeout=40) as r:
            body = r.read(5000000 if rest else 4096).decode('utf-8', 'replace')
            if rest:
                try:
                    j = json.loads(body)
                except ValueError:
                    return 'not a map-server answer'
                if isinstance(j, dict) and j.get('error'):
                    return 'server error: ' + str((j['error'] or {}).get('message') or j['error'])[:60]
            return 'ok' if r.status < 400 else f'HTTP {r.status}'
    except urllib.error.HTTPError as e:
        return f'HTTP {e.code}'
    except Exception as e:  # noqa: BLE001
        return 'no answer (' + str(e)[:50] + ')'


def links():
    t0, limit = time.time(), float(os.environ.get('LINK_MINUTES') or 20) * 60
    owners = {'data/state-gis.json': 2, 'data/access-layers.json': 2, 'data/trails-layers.json': 2,
              'data/campstate-layers.json': 2, 'data/trails-hand.json': 2, 'data/land-owner.json': 2}
    urls = {}
    for f, chat in owners.items():
        s = json.dumps(load(f, {}) or {})
        for u in set(re.findall(r'https?://[^"\s\\]+', s)):
            if '{' in u or '}' in u:
                continue          # a pattern like .../{slug}.php
            if '/rest/services' in u.lower() or f.endswith('land-owner.json'):
                urls.setdefault(u.rstrip('/'), (f, chat))
    problems, notes, ok = [], [], []
    bad, n, cache = [], 0, {}
    for u, (f, chat) in sorted(urls.items()):
        if time.time() - t0 > limit:
            notes.append({'chat': 5, 'msg': f'Link check stopped at its time limit after {n} of {len(urls)} addresses'})
            break
        host = re.sub(r'^https?://', '', u).split('/')[0]
        if cache.get(host, 0) >= 3:      # a host that is down: don't knock on it 40 more times
            res = 'host not answering'
        else:
            res = answer(u)
            if res.startswith('no answer'):
                cache[host] = cache.get(host, 0) + 1
            time.sleep(0.8)
        n += 1
        if res != 'ok':
            bad.append((f, chat, u, res))
    for f, chat, u, res in bad:
        problems.append({'key': f'links:{u}', 'chat': chat, 'twice': True, 'msg': f'{pathlib.Path(f).name}: {u} → {res}'})
    ok.append(f'{n - len(bad)} of {n} map-server / data addresses answered')
    # holiday pictures
    for h in ((load('data/holidays.json', {}) or {}).get('holidays') or []):
        for k, chat in (('img', 1), ('post_img', 5)):
            p = h.get(k)
            if p and not pathlib.Path(p).is_file():
                problems.append({'key': f'links:holiday:{p}', 'chat': chat, 'msg': f"data/holidays.json {h.get('id')}: picture {p} is missing"})
    # chat 2's own monthly map-link check (summary only; not re-fetched here)
    pw = (load('data/parkinfo-web.json', {}) or {}).get('parks') or {}
    chk = [(r, k, v) for r, e in pw.items() for k, v in ((e or {}).get('map_check') or {}).items() if k != 'date']
    nb = [x for x in chk if x[2] != 'ok']
    if chk:
        notes.append({'chat': 2, 'msg': f'parkinfo-web.json map links (from the monthly map-link check): {len(chk) - len(nb)} load, {len(nb)} do not'
                      + (': ' + '; '.join(f'{r} {k} {v}' for r, k, v in nb[:8]) if nb else '')})
    write('links', problems, notes, ok)


if __name__ == '__main__':
    try:
        {'guard': guard, 'refs': refs, 'links': links}[sys.argv[1]]()
    except Exception as e:  # noqa: BLE001
        print(f'::notice title=Check-up::{sys.argv[1:]} stopped early: {type(e).__name__}: {e}', flush=True)
    sys.exit(0)
