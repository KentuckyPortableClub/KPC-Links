#!/usr/bin/env python3
"""24 Nov 2026 (#378 grade): the PC key test's own steps, offline, on made-up keys. K1 not-built reasons (the real notice
strings), K4 (a file this PC built is never taken as a new website copy), the join check (a far join is held, a multi-state
park is measured to its nearest piece, a missing answer sheet is said). Prints PASS / FAIL, ends ALL PASS or SOME FAILED."""
import json, os, pathlib, shutil, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools' / 'pc-keys'))
import kpc_test_keys as K  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


def park(ids, km, n='Test Park'):
    return {'n': n, 'g': 'shape', 'm': [[i, n, 100, 'name'] for i in ids], 'c': [], 'bk': ['x', km]}


with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    K.LINKS, K.ORIG, K.LAST = t / 'links', t / 'originals', t / 'last-test'
    (K.LINKS / 'data' / 'us-key').mkdir(parents=True); K.ORIG.mkdir(); K.LAST.mkdir()
    os.symlink(ROOT / '.github', K.LINKS / '.github')
    kf = K.LINKS / 'data' / 'us-key' / 'US-ZZ.json'
    web = {'parks': {'K-1': park(['zz1'], 0.2), 'K-2': park(['zz2'], 40.0), 'K-3': park(['zz3'], 30.0)}}
    kf.write_text(json.dumps(web)); shutil.copy2(kf, K.ORIG / kf.name)

    # K1
    check('Canada gate (GATE FAIL in the title) = not built',
          K.not_built_reason('CANADA', '::notice title=Canada key GATE FAIL::3 provinces lost parks -- the old province files are kept'))
    check('golden cases stop = not built', K.not_built_reason('ZZ', '::notice title=US key STOPPED (golden cases)::NO keys were written'))
    check('FAILED = not built', K.not_built_reason('ZZ', '::notice title=US key ZZ::FAILED: something'))
    check('a key file still byte for byte the website copy = not built', K.not_built_reason('ZZ', 'normal log') != '')
    kf.write_text(json.dumps({'parks': dict(web['parks'], **{'K-9': park(['zz9'], 0.1)})}))
    check('a written key with a normal log = built', K.not_built_reason('ZZ', '::notice title=US key ZZ::match checks: 1 confirmed') == '')

    # K4
    K.remember_built('ZZ')
    check("this PC's own build output is fingerprinted", K.sha(kf) in K.built_files())
    before = (K.ORIG / kf.name).read_bytes()
    for f in K.keyfiles('ZZ'):   # the start of run_state: the kept copy must NOT become the built (or crashed) file
        o = K.ORIG / f.name
        if f.is_file() and (not o.is_file() or (f.read_bytes() != o.read_bytes() and K.sha(f) not in K.built_files())): shutil.copy2(f, o)
    check('a file this PC built is never taken as a new website copy', (K.ORIG / kf.name).read_bytes() == before)

    # join check: K-2 is 40 km off (held); K-3 is 30 km off here but has a piece 1 km away in another state file (kept)
    kf.write_text(json.dumps(web))
    (K.LINKS / 'data' / 'us-key' / 'US-YY.json').write_text(json.dumps({'parks': {'K-3': park(['yy3'], 1.0)}}))
    os.environ.pop('ANSWER_SHEET', None)
    lines = K.join_check_lines('ZZ')
    after = json.loads(kf.read_text())['parks']
    check('the far join is held (as on GitHub)', after['K-2'].get('g') == 'pin' and not after['K-2'].get('m'))
    check('a multi-state park is measured to its nearest piece (not held)', after['K-3'].get('m'))
    check('the near join stays', after['K-1'].get('m'))
    check('a missing answer sheet is said in the report line', 'NO answer sheet' in lines[0])
    (K.ORIG / kf.name).unlink()
    kf.write_text(json.dumps(web))
    check('a key file with no website copy is still checked, and said', 'no website copy' in K.join_check_lines('ZZ')[0])

# 25 Nov (grade K4-2): through run_state with a fake builder: a join-check hold rewrites the key; the next run must keep the website copy
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    K.LINKS, K.ORIG, K.LAST = t / 'links', t / 'originals', t / 'last-test'
    (K.LINKS / 'data' / 'us-key').mkdir(parents=True)
    os.symlink(ROOT / '.github', K.LINKS / '.github')
    kf = K.LINKS / 'data' / 'us-key' / 'US-ZZ.json'
    kf.write_text(json.dumps({'parks': {'K-1': park(['zz1'], 0.2)}})); web_bytes = kf.read_bytes()
    def fake_build(st, rep, attrs):   # writes a new far join, which the join check then holds (an in-place rewrite)
        kf.write_text(json.dumps({'parks': {'K-1': park(['zz1'], 0.2), 'K-2': park(['zz2'], 40.0)}}))
        return 0, '::notice title=US key ZZ::match checks: 1 confirmed'
    real_build, real_say = K.run_build, K.say
    K.run_build, K.say = fake_build, (lambda *a: None)
    out = K.run_state('ZZ', t, '', {})
    check('run_state: the join check held the far join', any('1 join(s) held' in l for l in out))
    check('run_state: the final (rewritten) key file is fingerprinted', K.sha(kf) in K.built_files())
    K.run_build = lambda st, rep, attrs: (None, 'stop after the restore step')
    K.run_state('ZZ', t, '', {})
    check("the next run keeps the website copy in originals (the PC's own key never replaces it)", (K.ORIG / kf.name).read_bytes() == web_bytes)
    # a test killed mid-build: the marker stays, so the next run does not trust links\
    kf.write_text(json.dumps({'parks': {'K-7': park(['zz7'], 0.1)}}))
    (K.ORIG / 'build-running-ZZ.txt').write_text('x')
    K.run_state('ZZ', t, '', {})
    check('a killed test (marker left) is never taken as a new website copy', (K.ORIG / kf.name).read_bytes() == web_bytes)
    check('the marker is cleared after the run', not (K.ORIG / 'build-running-ZZ.txt').is_file())
    for i in range(3): K.remember_built('ZZ')
    check('the fingerprint list keeps time order (newest last)', K._built_list()[-1] == K.sha(kf))
    K.run_build, K.say = real_build, real_say
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
