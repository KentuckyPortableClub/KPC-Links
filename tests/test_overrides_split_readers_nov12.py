#!/usr/bin/env python3
"""KPC-Links #151 readers fix (Nov 12 2026, KPC owner, 2026-11-12): every live reader and writer of data/us-key/overrides.json
follows the manifest to its parts (kpc_overrides), and none silently sees an EMPTY (or partial) set when the manifest or a part is
missing: it stops loudly. Fixture trees in a temp folder; offline, no network (sockets refused below; run with the network spy
too). Also: the workflows' save / skip lists name the parts, the save script honours a pattern in KPC_SAVE_SKIP and in its paths,
no 2-fer rule file changed, and no code reads the US overrides by file name outside the allowed places.

  python3 tests/test_overrides_split_readers_nov12.py
"""
import importlib, json, os, pathlib, re, shutil, socket, subprocess, sys, tempfile

def _no_net(*a, **k): raise RuntimeError('network refused in this test')
socket.socket.connect = _no_net; socket.create_connection = _no_net

ROOT = pathlib.Path(__file__).resolve().parent.parent
S = ROOT / '.github/scripts'
sys.path.insert(0, str(S))
import kpc_overrides as KO  # noqa: E402

bad = 0
def check(ok, msg):
    global bad; bad += not ok; print(('PASS ' if ok else 'FAIL ') + msg)

def raises(fn):
    try: fn(); return ''
    except Exception as e: return f'{type(e).__name__}: {e}'  # noqa: BLE001

# ---------------------------------------------------------------- fixture: a split US overrides set (small parts forced)
PARKS = {'US-0001': {'join': ['11'], 'why': 'person', 'decided_by': 'KPC owner'}, 'US-0002': {'no': ['22'], 'why': 'person no'},
         'US-0003': {'none': True, 'why': 'no outline'}, 'US-0004': {'join': ['44'], 'fp': {'44': ['Four Park', 10]}, 'decided_by': 'KPC owner'},
         'US-0005': {'alias': ['Five Lake'], 'why': 'person'}}
DOC = {'note': 'fixture', 'blocked_ids_about': 'x', 'blocked_ids': [{'ref': 'US-0005', 'id': '55', 'reason': 't', 'decided_by': 'KPC owner'}], 'parks': PARKS}


def tree(missing=None, single=False):
    t = pathlib.Path(tempfile.mkdtemp()); k = t / 'data/us-key'; k.mkdir(parents=True)
    for d in ('data/ca-key', 'data/world-key'): (t / d).mkdir(parents=True)
    (t / 'data/ca-key/overrides.json').write_text(json.dumps({'parks': {'CA-0001': {'join': ['c1']}}}))
    (t / 'data/world-key/overrides.json').write_text(json.dumps({'parks': {}}))
    if single:
        (k / 'overrides.json').write_text(json.dumps(DOC)); return t
    old = KO.FILL, KO.CAP
    KO.FILL = 120   # tiny parts so the fixture splits like the real file
    KO.CAP = 1_000_000
    try:
        files = KO.layout(k / 'overrides.json', dict(DOC))
        # force a split even though the fixture is small: lay it out as the real file is (parts + manifest)
        if len(files) == 1:
            own = {r: v for r, v in PARKS.items() if KO.has_no(v)}; rest = {r: v for r, v in PARKS.items() if r not in own}
            p1 = {r: rest[r] for r in list(rest)[:2]}; p2 = {r: rest[r] for r in list(rest)[2:]}
            man = {k2: v for k2, v in DOC.items() if k2 != 'parks'}
            man.update(parts=['overrides-parks-01.json', 'overrides-parks-02.json'],
                       parts_sha256={'overrides-parks-01.json': KO.canon_sha(p1), 'overrides-parks-02.json': KO.canon_sha(p2)}, parks=own)
            files = {'overrides.json': KO._dump(man).encode(), 'overrides-parks-01.json': KO._dump({'parks': p1}).encode(),
                     'overrides-parks-02.json': KO._dump({'parks': p2}).encode()}
    finally:
        KO.FILL, KO.CAP = old
    for n, b in files.items():
        if n != missing: (k / n).write_bytes(b)
    return t


T_OK, T_GONE, T_NOMAN = tree(), tree(missing='overrides-parks-02.json'), tree(missing='overrides.json')
man = json.loads((T_OK / 'data/us-key/overrides.json').read_text())
check(len(man['parts']) == 2 and set(man['parks']) == {'US-0002'}, 'fixture: a manifest (the park with a no) + two parts, like the real file')
check(KO.load(T_OK / 'data/us-key/overrides.json')['parks'] == PARKS, 'kpc_overrides.load puts the fixture back together exactly')

# ---------------------------------------------------------------- the module itself fails closed
U = lambda t: t / 'data/us-key/overrides.json'   # noqa: E731
e = raises(lambda: KO.load(U(T_GONE)))
check('overrides-parks-02.json' in e and 'missing' in e, f'a missing part = a loud error ({e[:90]})')
e = raises(lambda: KO.load(U(T_NOMAN), missing_ok=True))
check('missing' in e and 'part files are there' in e, f'a missing manifest with its parts still there = a loud error, even with missing_ok ({e[:90]})')
t = tree(); p = t / 'data/us-key/overrides-parks-01.json'; d = json.loads(p.read_text()); d['parks']['US-0001']['no'] = ['x']; p.write_text(json.dumps(d))
e = raises(lambda: KO.load(U(t)))
check("'no' list" in e or 'parts_sha256' in e, f"a part edited by hand (a 'no' added there) = a loud error until split is run ({e[:90]})")
t = tree(); p = t / 'data/us-key/overrides-parks-01.json'; d = json.loads(p.read_text()); d['parks']['US-0001']['why'] = 'hand edit'; p.write_text(json.dumps(d))
e = raises(lambda: KO.load(U(t)))
check('parts_sha256' in e and 'split' in e, f'a part edited by hand without the manifest = a loud error naming the fix ({e[:80]})')
check(KO.main(['x', 'split', str(U(t))]) == 0 and KO.load(U(t))['parks']['US-0001']['why'] == 'hand edit', '... and `kpc_overrides.py split` takes the hand edit in (the park keeps its new text)')
t = tree(); (t / 'data/us-key/overrides-parks-03.json').write_text('{"parks": {}}')
e = raises(lambda: KO.load(U(t)))
check('not named' in e, f'a part file the manifest does not name (a writer that bypassed save) = a loud error ({e[:80]})')
t = tree(); p = t / 'data/us-key/overrides-parks-02.json'; d = json.loads(p.read_text()); d['parks']['US-0001'] = {'join': ['dup']}; p.write_text(json.dumps(d))
check(bool(raises(lambda: KO.load(U(t)))), 'a ref in two files = a loud error')
check(KO.load(pathlib.Path(tempfile.mkdtemp()) / 'overrides.json', missing_ok=True) == {'parks': {}} and bool(raises(lambda: KO.load(pathlib.Path(tempfile.mkdtemp()) / 'overrides.json'))),
      'no override file at all: {} only when the caller says missing_ok (temp trees, a key with no overrides yet); else an error')

# ---------------------------------------------------------------- each Python reader on the fixtures
def in_dir(d, fn):
    here = os.getcwd(); os.chdir(d)
    try: return fn()
    finally: os.chdir(here)

import kpc_research_inbox as RI  # noqa: E402
_, OV, _ = RI.pins_and_overrides(T_OK, T_OK / 'nokpcdata')
check(all(r in OV for r in PARKS) and OV['US-0005'].get('_blocked') == ['55'] and 'CA-0001' in OV, 'kpc_research_inbox.pins_and_overrides: every US park (manifest + parts), blocked ids, Canada')
e = raises(lambda: RI.pins_and_overrides(T_GONE, T_GONE / 'x'))
check('overrides-parks-02.json' in e, f'kpc_research_inbox: a missing part stops it ({e[:70]})')

import kpc_key_postcheck as PK  # noqa: E402
N = {'US-0002': {'m': [['22', 'Bad piece', 5, 'x']], '_area': 'US-XX'}, 'US-0004': {'m': [], '_area': 'US-XX'}}
got = PK.override_check(N, 'us', cwd=str(T_OK))
check(any(x['park'] == 'US-0002' for x in got) and any(x['park'] == 'US-0004' for x in got),
      'kpc_key_postcheck.override_check: sees the manifest no (US-0002) and a part join (US-0004)')
check(bool(raises(lambda: PK.override_check(N, 'us', cwd=str(T_GONE)))), 'kpc_key_postcheck.override_check: a missing part stops it')

import kpc_key_dropped as KD  # noqa: E402
e_ok = raises(lambda: KD.rows_for('us', {}, {}, str(T_OK), {}, '', {}, ''))
e = raises(lambda: KD.rows_for('us', {}, {}, str(T_GONE), {}, '', {}, ''))
check('overrides-parks-02.json' in e and 'overrides-parks' not in e_ok, f'kpc_key_dropped.rows_for: reads the split set; a missing part stops it ({e[:70]})')
src = (S / 'kpc_key_dropped.py').read_text(encoding='utf-8')
check("kpc_overrides.load(os.path.join(kd, 'overrides.json')" in src, 'kpc_key_dropped reads overrides through kpc_overrides.load')

import kpc_join_check as J  # noqa: E402
okmap, _ = J.approvals(str(T_OK), 'us', {'ANSWER_SHEET': '/nonexistent'})
check({'US-0001', 'US-0004'} <= set(okmap) and 'US-0002' in J.NOS and 'US-0001' in J.SIGNED, 'kpc_join_check.approvals: part joins, signed joins and the manifest no all seen')
check(bool(raises(lambda: J.approvals(str(T_GONE), 'us', {'ANSWER_SHEET': '/nonexistent'}))), 'kpc_join_check.approvals: a missing part stops it (no silent un-signing)')

import kpc_problem_solver as PS  # noqa: E402
e = raises(lambda: PS.run({'PARKINFO': str(T_GONE / 'none'), 'GEO_CACHE': str(T_GONE / 'none')}, str(T_GONE)))
check('overrides-parks-02.json' in e, f'kpc_problem_solver.run: a missing part stops it ({e[:70]})')

import kpc_lost_finds as LF  # noqa: E402
e = in_dir(T_GONE, lambda: raises(LF.main))
check('overrides-parks-02.json' in e, f'kpc_lost_finds: a missing part stops it ({e[:70]})')
check("kpc_overrides.load('data/us-key/overrides.json'" in (S / 'kpc_lost_finds.py').read_text(encoding='utf-8'), 'kpc_lost_finds reads through kpc_overrides.load')

import kpc_precheck_whole as PW  # noqa: E402
import kpc_precheck as PCK  # noqa: E402
ov = in_dir(T_OK, PW.overrides)
check(set(PARKS) <= set(ov) and 'CA-0001' in ov and PCK.overrides is PW.overrides, 'kpc_precheck_whole: the pre-check reads US (manifest + parts) and Canada whole')
check(bool(in_dir(T_GONE, lambda: raises(PW.overrides))), 'kpc_precheck_whole: a missing part stops the pre-check')
r = subprocess.run([sys.executable, '-B', str(S / 'kpc_precheck_whole.py')], cwd=T_GONE, capture_output=True, text=True, timeout=120,
                   env=dict(os.environ, OUT=str(T_GONE / 'pc'), DATA=str(T_GONE / 'kpcdata')))
check(r.returncode == 1 and 'NOT complete' in r.stdout and json.loads((T_GONE / 'pc/counts.json').read_text())['status'] == 'red',
      'kpc_precheck_whole.py run: a missing part = exit 1, counts.json red (as kpc_precheck.py does on a crash)')
check(b'overrides-parks' not in (S / 'kpc_precheck.py').read_bytes() and 'kpc_precheck_whole.py' in (ROOT / '.github/workflows/kpc-key-postcheck.yml').read_text(encoding='utf-8')
      and 'scripts/kpc_precheck.py ' not in (ROOT / '.github/workflows/kpc-key-postcheck.yml').read_text(encoding='utf-8'),
      'kpc_precheck.py is unchanged (a 2-fer per-area code file); the key check workflow runs kpc_precheck_whole.py')

# the US key builder's load lines, run on the fixtures (the rest of kpc_us_key.py needs layers and the network: not run here)
ks = (S / 'kpc_us_key.py').read_text(encoding='utf-8')
a = ks.index('import kpc_overrides as _KOVR'); b = ks.index('\n', ks.index("OVR = _OVRDOC.get('parks', {})")) + 1
code = ks[a:b]
check(code.count('\n') == 2 and 'except' not in code, 'kpc_us_key.py: two lines (import + load), no except that could turn an error into an empty set')
g = {'OUT': T_OK / 'data/us-key'}; exec(code, g)
check(g['OVR'] == PARKS, 'kpc_us_key.py: OVR is the whole set (manifest + parts)')
check(bool(raises(lambda: exec(code, {'OUT': T_GONE / 'data/us-key'}))), 'kpc_us_key.py: a missing part stops the build (never OVR = {})')
g = {'OUT': pathlib.Path(tempfile.mkdtemp())}; exec(code, g)
check(g['OVR'] == {}, 'kpc_us_key.py: a temp tree with no overrides file at all still builds (as before)')

# BOT A (kpc_key_answers.py), the only writer: load + save through the module; a missing part stops it before any write
def bota(t):
    q = t / 'kpcdata/data/waiting/questions'; q.mkdir(parents=True, exist_ok=True)
    return subprocess.run([sys.executable, '-B', str(S / 'kpc_key_answers.py')], cwd=t, capture_output=True, text=True, timeout=120,
                          env=dict(os.environ, KEY_DIR=str(t / 'data/us-key'), DATA=str(t / 'kpcdata')))
before = {f.name: f.read_bytes() for f in (T_GONE / 'data/us-key').iterdir()}
r = bota(T_GONE)
check('::error' in r.stdout and 'NOT applied' in r.stdout and 'overrides-parks-02.json' in r.stdout + r.stderr and before == {f.name: f.read_bytes() for f in (T_GONE / 'data/us-key').iterdir()},
      "kpc_key_answers (BOT A): a missing part stops it with ::error (its own 'answers NOT applied' line) and nothing is written")
r = bota(T_OK)
check(r.returncode == 0 and KO.load(U(T_OK))['parks'] == PARKS, 'kpc_key_answers (BOT A): runs on the split set (no answers: nothing changes)')
ka = (S / 'kpc_key_answers.py').read_text(encoding='utf-8')
check('kpc_overrides.save(OVR, ovr)' in ka and 'save_json(OVR' not in ka and 'kpc_overrides.load(OVR' in ka, 'kpc_key_answers writes through kpc_overrides.save (parts kept under the cap)')
# a BOT A style write of a new 'no' on a park in a part moves it into the manifest and keeps every file under the cap
d = KO.load(U(T_OK)); d['parks']['US-0004'] = dict(d['parks']['US-0004'], no=['99']); KO.save(U(T_OK), d)
m2 = json.loads(U(T_OK).read_text())
check('US-0004' in m2['parks'] and KO.load(U(T_OK))['parks']['US-0004']['no'] == ['99'] and not KO.check(U(T_OK)),
      "a written 'no' lands in the manifest (where the 2-fer guard reads it); the set stays whole and placed right")

# 2-fers: the rule files are not edited and still see every 'no' from the manifest alone
import kpc_fers_guard as FG  # noqa: E402
check(FG.override_no(U(T_OK)) == {'US-0002': ({'22'}, {'22'}), 'US-0004': ({'99'}, {'99'})}, "kpc_fers_guard.override_no (unchanged) reads every 'no' from the manifest")
pl = (S / 'kpc_fers_postline.py').read_text(encoding='utf-8')
check("glob('overrides-parks-*.json')" in pl, 'kpc_fers_postline (not a rule file): the inputs time is the newest of the manifest and its parts')
check('parts_sha256' in m2 and m2['parts_sha256'] != man['parts_sha256'],
      "every save changes the manifest (parts_sha256), so kpc_fers_preline's commit time of overrides.json still dates any override change")

# ---------------------------------------------------------------- workflows (parsed YAML) and the save script
try:
    import yaml
except Exception:  # noqa: BLE001
    yaml = None
WF = ROOT / '.github/workflows'
def steps(name):
    y = yaml.safe_load((WF / name).read_text(encoding='utf-8'))
    return [s for j in (y.get('jobs') or {}).values() for s in (j.get('steps') or [])], y
if yaml:
    for name in ('kpc-us-key.yml', 'kpc-world-key.yml', 'kpc-boundary-check.yml', 'kpc-key-measure.yml', 'kpc-key-postcheck.yml'):
        st, y = steps(name)
        check(isinstance(y, dict) and (y.get('on') or y.get(True)) is not None and y.get('jobs'), f'{name}: parses, on + jobs present')
        runs = '\n'.join(str(s.get('run') or '') for s in st)
        for m in re.finditer(r'KPC_SAVE_SKIP="([^"]*)"', runs):
            names = m.group(1).split()
            if 'data/us-key/overrides.json' in names:
                check('data/us-key/overrides-parks-*.json' in names, f'{name}: a KPC_SAVE_SKIP list with overrides.json also skips data/us-key/overrides-parks-*.json')
        check(not re.search(r"json\.load\(open\('data/us-key/overrides\.json'\)\)", runs), f'{name}: no inline step reads data/us-key/overrides.json by name')
    st, _ = steps('kpc-us-key.yml')
    bota_step = next(s for s in st if 'BOT A' in str(s.get('name')))
    check("'data/us-key/overrides-parks-*.json'" in bota_step['run'] and 'data/us-key/overrides.json' in bota_step['run'],
          'kpc-us-key.yml BOT A save: names the manifest and the parts (quoted pattern: git adds new, changed and removed parts)')
    solver = next(s for s in st if s.get('id') == 'kept_green_solver')
    check("KO.load('data/us-key/overrides.json')" in solver['run'], 'kpc-us-key.yml problem-solver step (Quality ~line 572): reads through kpc_overrides.load')
    crons = [ln for f in WF.glob('*.yml') for ln in f.read_text(encoding='utf-8').splitlines() if re.match(r'\s*-?\s*cron:', ln)]
    base_crons = subprocess.run(['git', 'grep', '-h', '-E', r'^\s*-?\s*cron:', 'dedde63', '--', '.github/workflows/'], cwd=ROOT, capture_output=True, text=True)
    if base_crons.returncode in (0, 1) and base_crons.stdout:
        check(sorted(crons) == sorted(base_crons.stdout.splitlines()), 'no cron line added or changed')
else:
    print('SKIP workflow YAML: PyYAML not installed')

# save script: a pattern in KPC_SAVE_SKIP is skipped on copy-back; a quoted pattern in the paths is staged (adds and deletes)
sh = S / 'kpc_save_overwrite.sh'
w = pathlib.Path(tempfile.mkdtemp()); origin = w / 'origin.git'; wk = w / 'wk'
G = lambda *a, cwd=None: subprocess.run(['git', *a], cwd=cwd, capture_output=True, text=True)   # noqa: E731
G('init', '-q', '--bare', '-b', 'main', str(origin)); G('init', '-q', '-b', 'main', str(wk))
for k2, v in (('user.name', 't'), ('user.email', 't@example.invalid')): G('config', k2, v, cwd=wk)
(wk / 'data/us-key').mkdir(parents=True)
for n, body in (('overrides.json', '{"parts":["overrides-parks-01.json"]}'), ('overrides-parks-01.json', '{"parks":{"US-1":{}}}'), ('US-AL.json', '{"parks":{}}')):
    (wk / 'data/us-key' / n).write_text(body)
G('add', '-A', cwd=wk); G('commit', '-qm', 'base', cwd=wk); G('remote', 'add', 'origin', str(origin), cwd=wk); G('push', '-q', 'origin', 'main', cwd=wk)
(wk / 'data/us-key/overrides-parks-01.json').write_text('{"parks":{"US-1":{"stale":1}}}')   # a stale copy this run must NOT copy back
(wk / 'data/us-key/US-AL.json').write_text('{"parks":{"US-2":{}}}')                         # a generated file it must copy back
env = dict(os.environ, KPC_SAVE_SKIP='data/us-key/overrides.json data/us-key/overrides-parks-*.json', KPC_SAVE_TRIES='1', KPC_QUIET_HOURS='0', GIT_TERMINAL_PROMPT='0')
r = subprocess.run(['bash', str(sh), '--copy', 'test save', '-', '--', 'data/us-key'], cwd=wk, capture_output=True, text=True, env=env, timeout=120)
show = lambda p: G('--git-dir', str(origin), 'show', f'main:{p}').stdout   # noqa: E731
check(r.returncode == 0 and 'US-2' in show('data/us-key/US-AL.json') and 'stale' not in show('data/us-key/overrides-parks-01.json'),
      'kpc_save_overwrite.sh --copy: a part named by the KPC_SAVE_SKIP pattern is never copied back (hand-edited file kept); the key file is')
# BOT A style: no --copy, the redo writes a new part and removes none; the quoted pattern stages it
redo = "printf '{\"parks\":{\"US-3\":{}}}' > data/us-key/overrides-parks-02.json && printf '{\"parts\":[\"overrides-parks-01.json\",\"overrides-parks-02.json\"]}' > data/us-key/overrides.json"
r = subprocess.run(['bash', str(sh), 'bot a save', redo, '--', 'data/us-key/overrides.json', 'data/us-key/overrides-parks-*.json'], cwd=wk, capture_output=True, text=True,
                   env=dict(env, KPC_SAVE_SKIP=''), timeout=120)
check(r.returncode == 0 and 'US-3' in show('data/us-key/overrides-parks-02.json') and 'overrides-parks-02' in show('data/us-key/overrides.json'),
      'kpc_save_overwrite.sh: a quoted part pattern in the save paths stages a NEW part file with the manifest')
redo2 = "rm -f data/us-key/overrides-parks-02.json && printf '{\"parts\":[\"overrides-parks-01.json\"]}' > data/us-key/overrides.json"
r = subprocess.run(['bash', str(sh), 'bot a save 2', redo2, '--', 'data/us-key/overrides.json', 'data/us-key/overrides-parks-*.json'], cwd=wk, capture_output=True, text=True,
                   env=dict(env, KPC_SAVE_SKIP=''), timeout=120)
check(r.returncode == 0 and show('data/us-key/overrides-parks-02.json') == '', 'kpc_save_overwrite.sh: ... and stages a removed part (no orphan part left on main)')

# ---------------------------------------------------------------- no code reads the US overrides by file name outside the allowed places
ALLOWED = {
    ('kpc_us_key.py', "json.load(open(OUT / 'overrides.json')).get('blocked_ids')"),   # blocked_ids stay in the manifest
    ('kpc_fers.py', "for f in ('data/us-key/overrides.json', 'data/ca-key/overrides.json'):"),   # blocked_ids only (2-fer rule file)
    ('kpc_precheck.py', "for f in ('data/us-key/overrides.json', 'data/ca-key/overrides.json'):"),   # swapped out by kpc_precheck_whole.py
    ('kpc_precheck_whole.py', "for f in ('data/us-key/overrides.json', 'data/ca-key/overrides.json'):"),
    ('kpc_area_hash.py', "self.slice_file('data/us-key/overrides.json'"),   # Tree.json follows parts with the E4 hunk (D6)
    ('kpc_area_hash.py', "'data/us-key/overrides.json', 'data/ca-key/overrides.json'):"),
}
hits = []
for f in sorted(list(S.glob('*.py')) + list((ROOT / 'tools').glob('*.py'))):
    for i, ln in enumerate(f.read_text(encoding='utf-8', errors='replace').splitlines(), 1):
        s2 = ln.strip()
        if s2.startswith('#') or s2.startswith(('"', "'")) or re.search(r'kpc_overrides|_KOVR\.load|KO\.load', ln) or f.name == 'kpc_overrides.py': continue
        if f.name.startswith(('kpc_ca_', 'kpc_world_')): continue   # Canada / world keys read their own (single-file) overrides
        if re.search(r"us-key/overrides\.json|OUT / 'overrides\.json'|\{kind\}-key/overrides\.json|DIRS\[kind\]\[0\], 'overrides\.json'|KEYS\[k\]\['dir'\], 'overrides\.json'", ln) \
                and re.search(r'json\.load|load\(|open\(|for f in', ln) and not re.search(r"open\([^)]*'w'|json\.dump|write_text", ln):
            if not any(f.name == a and b in ln for a, b in ALLOWED): hits.append(f'{f.name}:{i}')
check(not hits, f'no other code reads the US overrides by file name (found: {hits[:8]})')
js = [str(p.name) for p in ROOT.glob('*.js') if p.name != 'kpc-maprep-extras.js' and re.search(r"us-key/overrides\.json|-key/overrides\.json'\)", p.read_text(encoding='utf-8', errors='replace'))]
check(not js, f'no page script fetches the US overrides by name outside the extras loader ({js})')

print('ALL PASS' if not bad else f'{bad} FAILED - SOME FAILED')
sys.exit(1 if bad else 0)
