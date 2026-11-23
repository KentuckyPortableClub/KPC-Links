#!/usr/bin/env python3
"""Official-links bot, 23 Nov 2026 (rule sheet L; owner 7:41 AM: "Finish the bot so I can do the webpage look up"). In the run
mode 'reader' the bot takes the page reader's SURE own-page finds from KPC-Data's park facts into data/parkinfo-web.json, with no
web request at all: for a park with no POTA link, and in place of a POTA link the facts call dead or only the agency's front page.
An unsure find is never taken; a person's value is never changed; a find no longer sure is taken out. Invented parks.
Prints PASS / FAIL, ends ALL PASS or SOME FAILED."""
import gzip, json, os, pathlib, socket, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


H = 'https://parks.zz.invented.gov'
PARKINFO = {   # [name, website, type, ...]
    'US-9603': ['Heron Marsh State Park', '', 'State Park'],
    'US-9604': ['Red Notch State Park', H + '/parks/old/red-notch.html', 'State Park'],
    'US-9608': ['Lone Pine State Park', H, 'State Park'],
    'US-9609': ['Fox Den State Park', '', 'State Park'],
    'US-9612': ['Elm Hollow State Park', H + '/parks/elm-hollow', 'State Park'],
    'US-9613': ['Pike Bend State Park', '', 'State Park'],
    'US-9614': ['Wren Hill State Park', '', 'State Park'],
}
FOUND = {
    'US-9603': {'level': 'sure', 'url': H + '/parks/heron-marsh', 'for': 'no link', 'how': 'sister'},
    'US-9604': {'level': 'sure', 'url': H + '/parks/red-notch-sp', 'for': 'dead link', 'how': 'up'},
    'US-9608': {'level': 'sure', 'url': H + '/parks/lone-pine', 'for': 'agency home only', 'how': 'home'},
    'US-9609': {'level': 'unsure', 'url': H + '/parks/fox-den', 'for': 'no link', 'how': 'sister'},
    'US-9612': {'level': 'sure', 'url': H + '/parks/elm-hollow-2', 'for': 'no link', 'how': 'kept'},   # POTA has a live link: never covered
    'US-9613': {'level': 'sure', 'url': H + '/parks/pike-bend', 'for': 'no link', 'how': 'sister'},    # a person's value is kept
    'US-9614': {'level': 'no', 'url': '', 'for': 'no link', 'how': ''},                               # was sure before: taken out
}
WEB = {'about': 'test', 'parks': {
    'US-9613': {'web': 'https://www.zz.invented.gov/pike-bend-by-hand'},
    'US-9614': {'web': H + '/parks/wren-hill', 'web_by': 'bot: page reader, agency site (parks.zz.invented.gov)', 'web_read': '2026-11-20'},
}}

with tempfile.TemporaryDirectory() as d:
    t = pathlib.Path(d)
    (t / '.github/scripts').mkdir(parents=True)
    for f in ('kpc_link_harvest.py', 'kpc_net_guard.py', 'kpc_save.py', 'kpc_scrub.py'):
        src = ROOT / '.github/scripts' / f
        (t / '.github/scripts' / f).write_bytes(src.read_bytes())
    for f in (ROOT / '.github/scripts').glob('kpc_host_rules*.py'):
        (t / '.github/scripts' / f.name).write_bytes(f.read_bytes())
    if (ROOT / '.github/host-rules.json').is_file():
        (t / '.github').joinpath('host-rules.json').write_bytes((ROOT / '.github/host-rules.json').read_bytes())
    (t / 'data/parkinfo').mkdir(parents=True)
    (t / 'data/parkinfo/US-ZZ.json').write_text(json.dumps({'parks': {r: v + ['', '', 47.0, -101.0, 0, 0, 1] for r, v in PARKINFO.items()}}))
    (t / 'data/parkinfo-web.json').write_text(json.dumps(WEB))
    facts = {'parks': {r: {'area': 'US-ZZ', 'page': {'kind': 'html' if f['level'] == 'sure' else 'none', 'found': f}} for r, f in FOUND.items()}}
    (t / 'pf.json.gz').write_bytes(gzip.compress(json.dumps(facts).encode()))
    env = dict(os.environ, ONLY='reader', PARK_FACTS=str(t / 'pf.json.gz'), MINUTES='2', NPS_API_KEY='', RIDB_API_KEY='')
    # no web request may happen: a socket that is opened fails the run
    guard = t / 'sitecustomize.py'
    guard.write_text('import socket\n'
                     'def _no(*a, **k): raise SystemExit("a network request was made")\n'
                     'socket.socket.connect = _no\nsocket.create_connection = _no\n')
    env['PYTHONPATH'] = str(t)
    r = subprocess.run([sys.executable, '.github/scripts/kpc_link_harvest.py'], cwd=t, env=env, capture_output=True, text=True, timeout=120)
    check('the reader mode runs with no web request', r.returncode == 0 and 'network request' not in r.stdout + r.stderr
          and 'stopped' not in r.stdout)
    if r.returncode or 'stopped' in r.stdout:
        print(r.stdout[-1500:], r.stderr[-1500:])
    out = json.loads((t / 'data/parkinfo-web.json').read_text())['parks']
    g = lambda ref, k='web': (out.get(ref) or {}).get(k)
    check('no POTA link: the sure find is the park\'s page, tagged as the page reader\'s', g('US-9603') == FOUND['US-9603']['url']
          and g('US-9603', 'web_by') == 'bot: page reader, agency site (parks.zz.invented.gov)')
    check('a dead POTA link: the sure find stands in for it', g('US-9604') == FOUND['US-9604']['url'])
    check("only the agency's front page: the sure find stands in for it", g('US-9608') == FOUND['US-9608']['url'])
    check('an unsure find is never taken', 'US-9609' not in out)
    check('a park whose POTA link works is never covered', 'US-9612' not in out)
    check("a person's own value is never changed", g('US-9613') == 'https://www.zz.invented.gov/pike-bend-by-hand' and not g('US-9613', 'web_by'))
    check('a page-reader value the finder no longer calls sure is taken out', 'US-9614' not in out)
    check('the run says what it took', 'page reader' in r.stdout)
    # the reader on the PC reads a 'bot: page reader' value in place of POTA's link (KPC-Data kpc_park_pages.choose_link)
    check('the tag starts the way the reader looks for it', g('US-9604', 'web_by').startswith('bot: page reader'))

wf = (ROOT / '.github/workflows/kpc-official-links.yml').read_text()
check('the workflow has the reader mode and no new timer', "only == 'reader'" in wf and wf.count('cron:') == 1 and "'23 10 9 * *'" in wf)
check('in the reader mode the map finder and the link check do not run (they make requests)',
      "inputs.only != 'reader' }}" in wf and "always() && inputs.only != 'reader'" in wf)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
