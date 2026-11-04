#!/usr/bin/env python3
"""Offline test for the 2-fer pre-line and post-line checks (links-05; Brandon, directly (Mapping chat), 4:52 AM CST Nov 4: "2fer line
review? Plan and install any pre and post line bots for the 2fer system."). Small made-up repos in a temp folder; no network, no gh, no workflow is run.
Checks: every HOLD reason stops the line (go=no), the WARN-only items do not, FORCE=yes by hand, an error = HOLD and exit 0,
both checks are read-only on the key / pin / 2-fer files, the post-line check finds each case and never fails."""
import hashlib, importlib.util, json, os, pathlib, subprocess, sys, tempfile

HERE = pathlib.Path(__file__).resolve().parent.parent
S = HERE / '.github/scripts'


def mod(name):
    sys.path.insert(0, str(S))
    spec = importlib.util.spec_from_file_location(name, S / f'{name}.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m


PRE, POST = mod('kpc_fers_preline'), mod('kpc_fers_postline')
try: KF = mod('kpc_key_freeze'); HAS_RULES = hasattr(KF, 'rules_hash')
except Exception: KF, HAS_RULES = None, False  # noqa: BLE001
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


def w(p, d):
    p = pathlib.Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(d if isinstance(d, str) else json.dumps(d))


def tree_hash(root, skip=()):
    h = hashlib.sha256()
    for f in sorted(pathlib.Path(root).rglob('*')):
        if f.is_file() and '.git' not in f.parts and not any(str(f).startswith(str(s)) for s in skip): h.update(str(f).encode() + f.read_bytes())
    return h.hexdigest()


KEY = {'st': 'US-TN', 'parks': {'US-0001': {'n': 'Alpha State Park', 'm': [[11, 'Alpha State Park', 90, 'name']], 'ac': 50},
                                'US-0002': {'n': 'Bravo WMA', 'm': [[22, 'Bravo WMA', 90, 'name']], 'ac': 80},
                                'US-0003': {'n': 'Charlie Trail', 'm': [], 'ac': 0}}}


def setup(t, src='live', **kw):
    L, D = pathlib.Path(t) / 'links', pathlib.Path(t) / 'data'
    idx = {'build': 'US-100', 'built': '2026-11-04 09:00 UTC', 'failed': kw.get('failed', [])}
    for base in (L, D): w(base / 'data/us-key/US-TN.json', kw.get('key', KEY)); w(base / 'data/us-key/index.json', idx)
    if 'live_key' in kw: w(D / 'data/us-key/US-TN.json', kw['live_key'])
    w(L / 'data/us-key/answers-states.txt', kw.get('todo', ''))
    w(L / 'data/us-key/overrides.json', {'parks': kw.get('over', {})})
    w(L / 'locations.json', kw.get('locs', [['POTA', 'US-0001', 'Alpha', 36.1, -86.7, ''], ['POTA', 'US-0002', 'Bravo', 36.2, -86.6, '']]))
    if src == 'build':
        if HAS_RULES and kw.get('rules', True): idx['rules'] = KF.rules_hash('us-key', L)
        w(L / 'data/us-key/index.json', idx)
        if kw.get('post', True):
            w(L / 'data/status/key-check/last-us.json', {'build': 'US-100', 'report': 'us-US-100.json'})
            w(L / 'data/status/key-check/us-US-100.json', {'precheck': kw.get('precheck', {})})
    if kw.get('held_key'): w(D / 'data/waiting/in/data/us-key/US-TN.json', KEY)
    if kw.get('verdict'): w(L / f"data/status/key-check/verdicts/US-100.json", {'build': 'US-100', 'verdict': kw['verdict'], 'by': kw.get('by', 'Quality'), 'date': '2026-11-04'})
    return L, D


def pre(t, src='live', env=None, **kw):
    L, D = setup(t, src, **kw)
    before = tree_hash(L), tree_hash(D, skip=[D / 'out'])
    gho = pathlib.Path(t) / 'gho'
    e = {'STATES': 'US-TN', 'TAG': 'tn', 'KEY_SOURCE': src, 'DATA': str(D), 'OUT': str(D / 'out'), 'GITHUB_OUTPUT': str(gho), **(env or {})}
    r = PRE.main(e, links=str(L))
    r['_go'] = gho.read_text() if gho.exists() else ''
    r['_ro'] = before == (tree_hash(L), tree_hash(D, skip=[D / 'out']))
    return r


with tempfile.TemporaryDirectory() as t:
    r = pre(t); check(r['verdict'] == 'GO' and 'go=yes' in r['_go'], 'live key, nothing wrong: GO, go=yes')
    check(r['_ro'], 'the pre-line check changed no key, pin or answer file (read-only)')
    check((pathlib.Path(t) / 'data/out/tn.json').exists() and (pathlib.Path(t) / 'data/out/tn.md').exists(), 'report written to OUT/<tag>.json + .md')
for name, kw, want in [
        ('key file has no parks', {'key': {'parks': {}}}, 'no parks'),
        ('the build names the state FAILED', {'failed': ['US-TN']}, 'FAILED'),
        ('state still on answers-states.txt', {'todo': 'AK TN TX'}, 'rebuild list'),
        ("key still joins an overrides 'no' record (by id)", {'over': {'US-0001': {'no': ['11']}}}, "said NO"),
        ("key still joins an overrides 'no' record (by name)", {'over': {'US-0002': {'no': ['bravo wma']}}}, "said NO"),
        ('a newer key file waits in the waiting room (keys first)', {'held_key': True}, 'keys first')]:
    with tempfile.TemporaryDirectory() as t:
        r = pre(t, **kw); check(r['verdict'] == 'HOLD' and 'go=no' in r['_go'] and any(want in h for h in r['holds']), f'HOLD stops the line: {name}')
with tempfile.TemporaryDirectory() as t:
    r = pre(t, over={'US-0001': {'no': ['99']}}); check(r['verdict'] == 'GO', "an overrides 'no' the key no longer joins: GO")
with tempfile.TemporaryDirectory() as t:
    r = pre(t, locs=[['POTA', 'US-0001', 'Alpha', 0, 0, ''], ['POTA', 'US-0002', 'Bravo', 95, 10, '']], key={'parks': dict(KEY['parks'], **{'US-0004': {'n': 'D', 'm': [[4, 'D', 90, 'name']], 'ac': 0}})})
    a = r['areas']['US-TN']
    check(r['verdict'] == 'GO' and any('0,0' in x and 'US-0001' in x and 'US-0002' in x for x in a['warn']), 'bad and 0,0 pins: WARN only (listed), the line still builds')
    check(any('no area' in x and 'US-0004' in x for x in a['warn']), 'outline sanity: an outline with no area is a WARN')
    check(r['_ro'] and json.loads((pathlib.Path(t) / 'links/locations.json').read_text())[0][3] == 0, 'pins are never moved')
with tempfile.TemporaryDirectory() as t:
    r = pre(t, env={'FORCE': 'yes'}, todo='TN'); check(r['verdict'] == 'FORCED' and 'go=yes' in r['_go'], 'FORCE=yes by hand: FORCED, the report keeps the HOLD reasons')
with tempfile.TemporaryDirectory() as t:
    r = pre(t, env={'STATES': ''}); check(r['verdict'] == 'HOLD' and 'go=no' in r['_go'] and r.get('error'), 'an error (no STATES) = HOLD, not GO')
with tempfile.TemporaryDirectory() as t:
    r = pre(t, env={'STATES': 'US-KY'}); check(r['verdict'] == 'GO' and 'own key' in r['areas']['US-KY']['key'], 'US-KY: its own key from the official files, not checked here')
with tempfile.TemporaryDirectory() as t:   # inputs newer than the key: overrides.json committed after the key was built
    L, D = setup(t)
    for c in (['init', '-q'], ['add', '-A'], ['-c', 'user.name=t', '-c', 'user.email=t@t', 'commit', '-qm', 'x', '--date', '2026-11-04T10:00:00Z']):
        subprocess.run(['git', *c], cwd=L, env=dict(os.environ, GIT_COMMITTER_DATE='2026-11-04T10:00:00Z'), check=True)
    r = PRE.main({'STATES': 'US-TN', 'TAG': 'tn', 'DATA': str(D), 'OUT': str(D / 'out')}, links=str(L))
    check(r['verdict'] == 'HOLD' and any('newer than the key' in h for h in r['holds']), 'answers (overrides.json) changed after the key was built: HOLD')
with tempfile.TemporaryDirectory() as t:
    L, D = setup(t); r = PRE.main({'STATES': 'US-TN', 'TAG': 'tn', 'DATA': str(D), 'OUT': str(D / 'out')}, links=str(L))
    check(r['verdict'] == 'GO' and 'not checked' in r['areas']['US-TN'].get('inputs_time', ''), 'no git history (shallow): the time test is skipped and says so, no false HOLD')
# KEY_SOURCE=build (the chain)
if HAS_RULES:
    with tempfile.TemporaryDirectory() as t:
        r = pre(t, 'build'); check(r['verdict'] == 'GO' and r['held_key'], 'build on the current rules, post-checked, not graded yet: GO, marked HELD KEY')
    with tempfile.TemporaryDirectory() as t:
        r = pre(t, 'build', precheck={'hold_still_outline': [{'area': 'US-TN', 'park': 'US-0001'}], 'rule18': [{'area': 'US-TN', 'park': 'US-0002'}, {'area': 'US-OH', 'park': 'US-9'}]})
        a = r['areas']['US-TN']; check(r['verdict'] == 'GO' and any('review-pile' in x for x in a['warn']) and any('rule 18' in x and 'US-9' not in x for x in a['warn']), 'review pile + rule 18 rows of this state: WARN')
    for name, kw, want in [('build not on the current rules', {'rules': False}, 'current rules'), ('no links-01 post-key check on this build', {'post': False}, 'post-key check'),
                           ('graded NO by Quality', {'verdict': 'NO'}, 'graded NO'), ('graded FAIL by Brandon', {'verdict': 'FAIL: wrong lines', 'by': 'Brandon'}, 'graded FAIL'),
                           ('outline count fell > 20 % against the live key', {'live_key': {'parks': {f'US-{i}': {'m': [[i, 'x', 90, 'n']]} for i in range(10)}}}, 'outline sanity')]:
        with tempfile.TemporaryDirectory() as t:
            r = pre(t, 'build', **kw); check(r['verdict'] == 'HOLD' and 'go=no' in r['_go'] and any(want in h for h in r['holds']), f'KEY_SOURCE=build HOLD: {name}')
    with tempfile.TemporaryDirectory() as t:
        r = pre(t, 'build', verdict='NO', by='Mapping bot'); check(r['verdict'] == 'GO', 'a bot verdict file is not a grade (only Quality / Brandon)')
    with tempfile.TemporaryDirectory() as t:
        r = pre(t, 'build', verdict='YES'); check(r['verdict'] == 'GO' and r['held_key'], "FINAL-v2: a Quality YES is a report, not a person's sign-off: GO, still marked HELD KEY")
        r = pre(t, 'build', verdict='YES', by='Brandon'); check(r['verdict'] == 'GO' and not r['held_key'], 'signed YES by Brandon (after the restart): GO, not marked held')
        r = pre(t, 'build', verdict='YES', by='KZ4CP'); check(r['verdict'] == 'GO' and not r['held_key'], 'signed YES by KZ4CP: GO, not marked held')
        r = pre(t, 'build', verdict='WITHDRAWN', by='Quality'); check(r['verdict'] == 'HOLD', 'WITHDRAWN by Quality still HOLDS (a NO is the safe direction)')
else:
    with tempfile.TemporaryDirectory() as t:
        r = pre(t, 'build'); check(r['verdict'] == 'HOLD' and any('links-04' in h for h in r['holds']), 'without links-04 (no rules hash) KEY_SOURCE=build is HOLD')
# the command line never fails
with tempfile.TemporaryDirectory() as t:
    p = subprocess.run([sys.executable, '-B', str(S / 'kpc_fers_preline.py')], cwd=t, env=dict(os.environ, STATES='US-TN', DATA='/nonexistent', OUT=t + '/o', GITHUB_OUTPUT=t + '/g'), capture_output=True, text=True)
    check(p.returncode == 0 and 'go=no' in open(t + '/g').read(), 'command line: missing data = exit 0 and go=no')

# ---------- post-line ----------
def spot(refs, status='candidate', kind='area', wide=200.0, tier=''):
    return {'refs': refs, 'status': status, 'kind': kind, 'wide_m': wide, 'tier': tier}


OLD = {'pass3': '2026-11-04', 'spots': [spot(['US-0001', 'US-0002']), spot(['US-0001', 'US-0005']), spot(['US-0006', 'US-0007'], 'dropped in pass 3')]}
NEW = {'pass3': '2026-11-04', 'spots': [spot(['US-0001', 'US-0002']), spot(['US-0001', 'US-0005'], 'dropped: side by side, not layered'),
                                        spot(['US-0003', 'US-0001'], wide=47.0), spot(['US-0002', 'US-0008'], kind='river', status='not sure: water not checked'),
                                        spot(['US-0002', 'US-0009'], kind='same land'), spot(['US-0010', 'US-0011'], kind='same land', status='not sure: one record covers two parks (x): a person decides'),
                                        spot(['US-0012', 'US-0013'], wide=24.0, tier='bank only')]}
with tempfile.TemporaryDirectory() as t:
    L, D = setup(t, 'build')
    w(D / 'data/fers/US-TN.json', OLD); w(D / 'data/waiting/in/data/fers/US-TN.json', NEW); w(D / 'data/waiting/in/data/fers/notes.json', {'x': 1})
    held_key = json.loads(json.dumps(KEY)); held_key['parks']['US-0002']['m'] = [[23, 'Bravo WMA', 90, 'name']]
    w(L / 'data/us-key/US-TN.json', held_key)
    w(D / 'data/status/fers-preline/tn.json', {'tag': 'tn', 'states': ['US-TN'], 'verdict': 'GO', 'checked': '2026-11-04 10:00 UTC', 'key_source': 'build'})
    before = tree_hash(L), tree_hash(D, skip=[D / 'data/status/fers-postline'])
    rep = POST.main({'DATA': str(D), 'LINKS': str(L)}); a = rep['areas'].get('US-TN') or {}
    check(set(rep['areas']) == {'US-TN'}, 'post-line: compares each held area file (non-area files skipped)')
    check('US-0001+US-0003' in a.get('gained', []) and 'US-0012+US-0013' in a['gained'], 'pairs gained')
    check([x['pair'] for x in a.get('lost', [])] == ['US-0001+US-0005'] and 'side by side' in a['lost'][0]['now'], 'pairs lost, with the new status')
    check('US-0001+US-0002' in a['touch_held'] and 'US-0001+US-0003' in a['touch_pin_only'], 'pairs touching held parks (outline not the live one) and pin-only parks')
    check({x['pair'] for x in a['water_bank']} >= {'US-0002+US-0008', 'US-0012+US-0013'}, 'water / bank cases (river row, bank tier)')
    check({x['pair'] for x in a['same_land_one_record']} == {'US-0002+US-0009', 'US-0010+US-0011'}, 'single-record same land')
    check({(x['pair'], x['near']) for x in a['near_threshold']} >= {('US-0001+US-0003', '50 yd (very tight)'), ('US-0012+US-0013', '25 yd (kept)')} and not any(x['pair'] == 'US-0001+US-0002' for x in a['near_threshold']), 'overlap sizes near a threshold (and not the 200 m one)')
    check(a['stale_inputs'] == [] and a['preline']['verdict'] == 'GO', 'fresh inputs + a GO pre-line report: no stale flag')
    check(before == (tree_hash(L), tree_hash(D, skip=[D / 'data/status/fers-postline'])), 'post-line check is read-only: only data/status/fers-postline/ is written')
    check((D / 'data/status/fers-postline/latest.md').exists() and 'Quality' in (D / 'data/status/fers-postline/latest.md').read_text(), 'report for Quality in data/status/fers-postline/latest.md')
    w(D / 'data/waiting/in/data/fers/US-TN.json', dict(NEW, pass3='2026-11-01')); os.remove(D / 'data/status/fers-preline/tn.json')
    a = POST.main({'DATA': str(D), 'LINKS': str(L)})['areas']['US-TN']
    check(any('newer than this output' in x for x in a['stale_inputs']) and any('no pre-line report' in x for x in a['stale_inputs']), 'stale inputs: key newer than the output; no pre-line report')
with tempfile.TemporaryDirectory() as t:
    w(t + '/data/waiting/in/data/fers/US-TN.json', 'not json {'); w(t + '/data/fers/US-TN.json.gz', 'nope')
    p = subprocess.run([sys.executable, '-B', str(S / 'kpc_fers_postline.py')], cwd=t, env=dict(os.environ, DATA=t, LINKS='/nonexistent'), capture_output=True, text=True)
    check(p.returncode == 0 and os.path.exists(t + '/data/status/fers-postline/latest.json'), 'post-line never fails: broken files = exit 0 and a report')
src = (S / 'kpc_fers_postline.py').read_text() + (S / 'kpc_fers_preline.py').read_text()
check(not any(x in src for x in ('gh release', 'approved.json\', \'w', 'kpc_release_approved', 'workflow run', 'requests.', 'urllib')), 'neither check releases, publishes, dispatches or uses the network')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
