#!/usr/bin/env python3
"""Offline test (owner rule, 2026-11-10): the download-source change check skips a source tried less than KPC_WATCH_MIN_DAYS
(default 7) days ago, and writes download-sources.json only when something in it changed. Stubbed fetchers, temp files only."""
import json, os, pathlib, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))
import kpc_master_watch as W
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


calls = []
def head(u): calls.append(u); return 200, {'content-length': '100', 'etag': 'a'}
def getj(u): calls.append(u); return None


with tempfile.TemporaryDirectory() as t:
    sp = pathlib.Path(t) / 'download-sources.json'
    sp.write_text(json.dumps({'sources': {'s1': {'check': 'bot', 'kind': 'first-party', 'file': 'https://example.org/a.zip', 'areas': ['US-TN']}}}))
    W.watch(str(sp), head=head, getj=getj, date='2026-11-10', min_days=7)
    n1 = len(calls); m1 = sp.stat().st_mtime_ns
    check(n1 >= 1 and json.loads(sp.read_text())['sources']['s1'].get('fp_seen') == '2026-11-10', 'a never-checked source is checked and its fingerprint saved')
    o = W.watch(str(sp), head=head, getj=getj, date='2026-11-12', min_days=7)
    check(len(calls) == n1 and o.get('recent') == 1, 'a source checked 2 days ago is not asked again (no request)')
    check(sp.stat().st_mtime_ns == m1, 'nothing changed: the file is not rewritten')
    W.watch(str(sp), head=head, getj=getj, date='2026-11-18', min_days=7)
    check(len(calls) > n1, 'a source last checked 8 days ago is checked again')
    # the CLI passes KPC_WATCH_MIN_DAYS (default 7) to the watch
    src = (HERE / '.github/scripts/kpc_master_cli.py').read_text()
    check("min_days=float(os.environ.get('KPC_WATCH_MIN_DAYS') or 7)" in src, 'kpc_master_cli.py watch: KPC_WATCH_MIN_DAYS, default 7 days')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
