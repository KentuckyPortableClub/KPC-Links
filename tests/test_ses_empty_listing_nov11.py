#!/usr/bin/env python3
"""Nov 11 (data-quality review): kpc_ses.py saved 'ARRL ok (0)' and an empty station list when the ARRL page came back with no listing in
it (page changed, block page, empty answer), so every special event station vanished from the Events page. With stations on file the
old ones now stay and the status says why. A real failure already kept them. Offline: arrl() is a stub, nothing is fetched."""
import contextlib, datetime as dt, io, json, os, pathlib, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import kpc_ses as S   # noqa: E402

ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


TODAY = S.TODAY
soon = (TODAY + dt.timedelta(days=10)).isoformat()
gone = (TODAY - dt.timedelta(days=3)).isoformat()
ST = [{'title': 'Alpha', 'start': soon, 'end': soon, 'call': 'W1AA'}, {'title': 'Old', 'start': gone, 'end': gone, 'call': 'W1BB'}]


def go(arrl, old):
    d = pathlib.Path(tempfile.mkdtemp(prefix='kpc-ses-')); os.chdir(d)
    if old is not None: (d / 'kpc-special-events.json').write_text(json.dumps(old))
    S.arrl = arrl
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): rc = S.main()
    return rc, json.loads((d / 'kpc-special-events.json').read_text()), buf.getvalue()


rc, out, log = go(lambda: [], {'stations': ST, 'yearly': [], 'status': {}})
check([x['title'] for x in out['stations']] == ['Alpha'], 'an empty listing keeps the stations still to come (and drops the one that ended)')
check('returned no stations' in out['status']['ARRL'] and 'kept 1' in out['status']['ARRL'], f"the status says so ({out['status']['ARRL']})")
check('::notice title=Special events::ARRL returned no stations' in log, 'and the log says so')

rc, out, log = go(lambda: [], None)
check(out['stations'] == [] and out['status']['ARRL'] == 'ok (0)', 'nothing on file and nothing listed: ok (0), as before')

new = [{'title': 'Beta', 'start': soon, 'end': soon, 'call': 'W1CC'}]
rc, out, log = go(lambda: new, {'stations': ST, 'yearly': [], 'status': {}})
check([x['title'] for x in out['stations']] == ['Beta'] and out['status']['ARRL'] == 'ok (1)', 'a real listing replaces the old one')


def boom(): raise RuntimeError('503')
rc, out, log = go(boom, {'stations': ST, 'yearly': [], 'status': {}})
check([x['title'] for x in out['stations']] == ['Alpha'] and out['status']['ARRL'].startswith('failed, kept 1'), 'a failed read still keeps the old stations')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
