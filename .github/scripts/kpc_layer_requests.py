#!/usr/bin/env python3
"""kpc_layer_requests.py: checks .github/layer-requests-new.json, the list of new and partial official layers (KPC owner, 2026-11-21).

Each row names the bot that will provide the layer (keeper = a keeper fetch request; intake = the layer intake bot; hand = a
person downloads it from the official page; fix = already on the box, needs a merge or a status fix; none = already wired) and
stays OFF until the licence allows our use and robots.txt allows the path. This script fetches nothing and starts nothing.

Rules (each one a check):
  - 'on' only for a keeper or intake row with licence_ok true, a licence line, a terms address, and robots.txt read as allowed
    with a date. robots.txt answering 403, unreadable or a parse error counts as no.
  - a keeper or intake row never points at a saved-copies-only or never-contact host (kpc_net_guard: services*.arcgis.com,
    apps.fs.usda.gov, ncnhde.natureserve.org, and KPC_SAVED_ONLY_HOSTS), and never at WDPA / Protected Planet.
  - a hand row is links only (an official page, no fetch address); a fix row names the file already on the box.
  - ids are unique; no park number appears anywhere in the file (counts only).

  python3 .github/scripts/kpc_layer_requests.py [--file F]        # check; exit 1 on any problem
  python3 .github/scripts/kpc_layer_requests.py --intake ID       # the intake bot's sidecar for one row, only when the row is on
  python3 .github/scripts/kpc_layer_requests.py --selftest
"""
import argparse, collections, copy, json, os, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent
FILE = HERE.parent / 'layer-requests-new.json'
TARGETS = {'keeper', 'intake', 'hand', 'fix', 'none'}
STATUSES = {'off', 'on', 'hold', 'hand', 'done'}
WDPA = re.compile(r'wdpa|protected[ _-]?planet|unep-?wcmc', re.I)
PARK_REF = re.compile(r'\b(?:US|CA|[A-Z]{1,3})-\d{4,5}\b')
ROBOTS_OK = 'allowed'


def _host_rule(url):
    """'' when a bot may contact the url's host, else why not (kpc_net_guard's own rule, so the two never drift)."""
    sys.path.insert(0, str(HERE))
    import kpc_net_guard as G
    ok, why = G.host_ok(url)
    return '' if ok else why


def problems(doc):
    out = []
    rows = doc.get('rows') if isinstance(doc, dict) else None
    if not isinstance(rows, list):
        return ['the file has no rows list']
    seen = set()
    text = json.dumps(doc, ensure_ascii=False)
    for m in sorted(set(PARK_REF.findall(text))):
        out.append(f'a park number is named ({m}): counts only')
    for r in rows:
        i = r.get('id') or '?'
        if i in seen:
            out.append(f'{i}: id used twice')
        seen.add(i)
        t, st = r.get('target'), r.get('status')
        if t not in TARGETS:
            out.append(f'{i}: target {t!r} is not one of {sorted(TARGETS)}')
        if st not in STATUSES:
            out.append(f'{i}: status {st!r} is not one of {sorted(STATUSES)}')
        urls = [u for u in (r.get('service'), (r.get('intake') or {}).get('source_url')) if u]
        if any(WDPA.search(str(u)) for u in urls + [r.get('page') or '']) or WDPA.search(str(r.get('agency') or '')):
            out.append(f'{i}: WDPA / Protected Planet is never a source')
        if t in ('keeper', 'intake'):
            for u in urls:
                why = _host_rule(u)
                if why:
                    out.append(f'{i}: a live fetch may not point there ({why})')
            if not urls:
                out.append(f'{i}: a {t} row needs the service or file address')
        if st == 'on':
            rb = r.get('robots') or {}
            if t not in ('keeper', 'intake'):
                out.append(f'{i}: only a keeper or intake row can be on')
            if not (r.get('licence_ok') is True and r.get('licence') and r.get('terms_url')):
                out.append(f'{i}: on, but the licence is not read and allowed (licence, licence_ok, terms_url)')
            if rb.get('result') != ROBOTS_OK or not rb.get('date'):
                out.append(f'{i}: on, but robots.txt is not read as allowed with a date (403, unreadable or a parse error = no)')
        if st in ('off', 'hold') and not r.get('why_off'):
            out.append(f'{i}: off with no one-line reason (why_off)')
        if t == 'hand':
            if r.get('service'):
                out.append(f'{i}: a hand row is links only (no fetch address)')
            if st != 'hand':
                out.append(f'{i}: a hand row has status hand')
        if t == 'fix' and not r.get('on_box'):
            out.append(f'{i}: a fix row names the file already on the box (on_box)')
    return out


def intake_sidecar(doc, rid):
    """The layer intake bot's sidecar for one row (area, layer, source_url, license, expected, name_fields), or a refusal."""
    for r in doc.get('rows') or []:
        if r.get('id') == rid:
            if r.get('target') != 'intake' or r.get('status') != 'on':
                return None, f'{rid}: not an intake row that is on (status {r.get("status")}): nothing to hand the intake bot'
            bad = [p for p in problems({'rows': [r]})]
            if bad:
                return None, '; '.join(bad)
            return dict(r['intake']), ''
    return None, f'{rid}: no such row'


def summary(doc):
    c = collections.Counter((r.get('target'), r.get('status')) for r in doc.get('rows') or [])
    return ', '.join(f'{t}/{s} {n}' for (t, s), n in sorted(c.items()))


def selftest():
    print('kpc_layer_requests SELF-TEST')
    bad = []

    def ok(what, cond):
        print(f'  {"ok  " if cond else "FAIL"} {what}')
        if not cond:
            bad.append(what)
    base = {'rows': [{'id': 'W-ZZ|a', 'area': 'W-ZZ', 'target': 'intake', 'status': 'off', 'why_off': 'robots.txt not read',
                      'service': 'https://data.invented.example/wfs', 'licence': 'Invented Open Licence', 'licence_ok': True,
                      'terms_url': 'https://data.invented.example/licence', 'robots': {'result': 'not read', 'date': ''},
                      'intake': {'area': 'W-ZZ', 'layer': 'zz-a', 'source_url': 'https://data.invented.example/wfs', 'license': 'open',
                                 'expected': None, 'name_fields': []}}]}
    ok('an off row with a reason passes', problems(base) == [])
    on = copy.deepcopy(base); on['rows'][0]['status'] = 'on'
    ok('on without robots read as allowed is refused', any('robots.txt' in p for p in problems(on)))
    on['rows'][0]['robots'] = {'result': '403', 'date': '2026-11-21'}
    ok('robots.txt answering 403 counts as no', any('robots.txt' in p for p in problems(on)))
    on['rows'][0]['robots'] = {'result': 'allowed', 'date': '2026-11-21'}
    ok('on with licence and robots allowed passes', problems(on) == [])
    nl = copy.deepcopy(on); nl['rows'][0]['licence_ok'] = False
    ok('on with an unclear licence is refused', any('licence' in p for p in problems(nl)))
    sv = copy.deepcopy(base); sv['rows'][0]['service'] = 'https://services3.arcgis.com/abc/arcgis/rest/services/x/FeatureServer/0'
    ok('a saved-copies-only host is never a live fetch', any('may not point' in p for p in problems(sv)))
    fs = copy.deepcopy(base); fs['rows'][0]['service'] = 'https://apps.fs.usda.gov/arcx/rest/services/x/MapServer/0'
    ok('apps.fs.usda.gov is never a live fetch', any('may not point' in p for p in problems(fs)))
    nc = copy.deepcopy(base); nc['rows'][0]['service'] = 'https://ncnhde.natureserve.org/x'
    ok('ncnhde.natureserve.org is never contacted', any('may not point' in p for p in problems(nc)))
    wd = copy.deepcopy(base); wd['rows'][0]['service'] = 'https://www.protectedplanet.net/en/thematic-areas/wdpa'
    ok('WDPA is never a source', any('WDPA' in p for p in problems(wd)))
    pr = copy.deepcopy(base); pr['rows'][0]['notes'] = 'park US-9001 is missing'
    ok('a park number in the file is refused', any('park number' in p for p in problems(pr)))
    hd = {'rows': [{'id': 'W-ZZ|h', 'target': 'hand', 'status': 'hand', 'page': 'https://agency.invented.example/',
                    'service': 'https://agency.invented.example/x.zip'}]}
    ok('a hand row is links only', any('links only' in p for p in problems(hd)))
    fx = {'rows': [{'id': 'W-ZZ|f', 'target': 'fix', 'status': 'done'}]}
    ok('a fix row names the file on the box', any('on_box' in p for p in problems(fx)))
    nr = copy.deepcopy(base); nr['rows'][0]['why_off'] = ''
    ok('an off row needs its one-line reason', any('why_off' in p for p in problems(nr)))
    ok('the intake sidecar is refused while the row is off', intake_sidecar(base, 'W-ZZ|a')[0] is None)
    ok('the intake sidecar comes out when the row is on and passes', intake_sidecar(on, 'W-ZZ|a')[0]['layer'] == 'zz-a')
    shipped = json.load(open(FILE, encoding='utf-8'))
    ok('the shipped file passes every rule', problems(shipped) == [])
    ok('nothing in the shipped file is switched on', all(r.get('status') != 'on' for r in shipped['rows']))
    print('SELF-TEST PASSED' if not bad else f'SELF-TEST FAILED: {len(bad)}')
    return 0 if not bad else 1


def main(argv=None):
    ap = argparse.ArgumentParser(description='Check the new-layer request list (fetches nothing).')
    ap.add_argument('--file', default=str(FILE))
    ap.add_argument('--intake', default='')
    ap.add_argument('--selftest', action='store_true')
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()
    doc = json.load(open(a.file, encoding='utf-8'))
    if a.intake:
        side, why = intake_sidecar(doc, a.intake)
        if side is None:
            print(why)
            return 1
        print(json.dumps(side, ensure_ascii=False))
        return 0
    bad = problems(doc)
    print(f'{len(doc.get("rows") or [])} rows: {summary(doc)}')
    for p in bad:
        print('  PROBLEM ' + p)
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
