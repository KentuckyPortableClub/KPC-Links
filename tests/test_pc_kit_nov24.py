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

# Batch 16 (grade of #380, 25 Nov: the PC's website copy of MN / NY was a test-built key): originals is only READ, and checked
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    K.LINKS, K.ORIG, K.LAST = t / 'links', t / 'originals', t / 'last-test'
    (K.LINKS / 'data' / 'us-key').mkdir(parents=True); K.ORIG.mkdir()
    os.symlink(ROOT / '.github', K.LINKS / '.github')
    kf = K.LINKS / 'data' / 'us-key' / 'US-ZZ.json'
    web = json.dumps({'parks': {'K-1': park(['zz1'], 0.2)}}); web_sha = __import__('hashlib').sha256(web.encode()).hexdigest()
    (K.ORIG / kf.name).write_text(web); kf.write_text(web)
    def fake_build(st, rep, attrs):   # writes a new far join, which the join check then holds (an in-place rewrite)
        kf.write_text(json.dumps({'parks': {'K-1': park(['zz1'], 0.2), 'K-2': park(['zz2'], 40.0)}}))
        return 0, '::notice title=US key ZZ::match checks: 1 confirmed'
    real_build, real_say = K.run_build, K.say
    K.run_build, K.say = fake_build, (lambda *a: None)
    snap = lambda: sorted((p.name, p.read_bytes()) for p in K.ORIG.iterdir())
    o0 = snap()
    out = K.run_state('ZZ', t, '', {})
    check('run_state (no kit list, an older kit): originals is read as before, the far join held', any('1 join(s) held' in l for l in out))
    check('run_state never writes into originals (no copy, no fingerprint list, no marker)', snap() == o0)
    K.run_build = lambda st, rep, attrs: (None, 'stop after the restore step')
    K.run_state('ZZ', t, '', {})
    check("the next run starts again from the website copy (links\\ put back from originals)", kf.read_text() == web)
    # the kit lists the website's sha256: a bad originals copy stops the state; the kit's own copy is used when it matches
    (K.LINKS / K.KITWEB_NAME).mkdir()
    (K.LINKS / K.KITWEB_NAME / 'sha256.json').write_text(json.dumps({'files': {'US-ZZ.json': web_sha}}))
    check('a good originals copy is trusted', K.web_copy(kf) == K.ORIG / kf.name and K.web_copy_problem(kf) == '')
    bad = json.dumps({'parks': {'K-9': park(['zz9'], 0.1)}}); (K.ORIG / kf.name).write_text(bad); o1 = snap()
    kf.write_text(bad)
    K.run_build = lambda st, rep, attrs: (_ for _ in ()).throw(AssertionError('must not build'))
    out = K.run_state('ZZ', t, '', {})
    check(f'a bad originals copy: the state is NOT BUILT, with one plain line ({out[0][:70]}...)',
          len(out) == 1 and 'NOT BUILT' in out[0] and "is not the website's key" in out[0] and 'US-ZZ.json' in out[0])
    check('a bad originals copy is left as it is (never fixed or overwritten by the test)', snap() == o1 and kf.read_text() == bad)
    (K.LINKS / K.KITWEB_NAME / kf.name).write_text(web)
    K.run_build = lambda st, rep, attrs: (None, 'stop after the restore step')
    out = K.run_state('ZZ', t, '', {})
    check("the kit's own website copy (sha matches) is used, and links\\ starts from it", K.web_copy(kf) == K.LINKS / K.KITWEB_NAME / kf.name and kf.read_text() == web)
    check('originals is still untouched', snap() == o1)
    # batch 16 item 4: ANY of the listed website copies wrong = the whole test stops before building (main(), first step)
    (K.LINKS / K.KITWEB_NAME / 'sha256.json').write_text(json.dumps({'files': {'US-ZZ.json': web_sha, 'US-YY.json': 'f' * 64}}))
    check('one wrong (or missing) website copy of the 66 is found before anything is built', K.website_copies_check() == ['US-YY.json'])
    (K.LINKS / K.KITWEB_NAME / 'sha256.json').write_text(json.dumps({'files': {'US-ZZ.json': web_sha}}))
    check('all listed copies good = nothing to stop', K.website_copies_check() == [])
    msrc = (ROOT / 'tools' / 'pc-keys' / 'kpc_test_keys.py').read_text(encoding='utf-8')
    mm = msrc[msrc.index('def main(argv):'):]
    check('main() checks every website copy first and stops with nothing built',
          mm.index('website_copies_check()') < mm.index('store_attrs()') < mm.index('run_state(') and 'Nothing was built.' in mm)
    K.run_build, K.say = real_build, real_say
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
