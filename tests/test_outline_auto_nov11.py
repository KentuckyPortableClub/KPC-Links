#!/usr/bin/env python3
"""KPC owner, 2026-11-11: the outline build is the automatic last step of the US key run, the save never writes an outline file
older than main's, and a state that loses more than 3% of its official parks fails the run with nothing saved."""
import gzip, json, os, pathlib, subprocess, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_master as M
import kpc_outlines_keep_main as K
import kpc_key_drop_guard as D

ok = True
def check(name, cond):
    global ok
    print(('PASS ' if cond else 'FAIL ') + name)
    ok = ok and bool(cond)

SQ = {'type': 'Polygon', 'coordinates': [[[0, 0], [0, 1], [1, 1], [1, 0], [0, 0]]]}
def rec(ref, g='official', layer='file:US-FL.json.gz', date='2026-11-11', ids=('1',)):
    return M.make_record(ref, ref, g, SQ, 'agency', layer, list(ids), 10, date, '', 'key')

# ---- record rules
a, b = rec('US-1', ids=('1',)), rec('US-1', ids=('2',))
check('same kind, same layer, same day: this run\'s fresh read wins', K.pick(a, b) is b)
check('same kind, same layer: an older date_read never replaces main', K.pick(rec('US-1', date='2026-11-11', ids=('1',)), rec('US-1', date='2026-11-09', ids=('2',)))['date_read'] == '2026-11-11')
check('a lower kind never replaces main', K.pick(rec('US-1'), rec('US-1', g='approximate', ids=('3',)))['g'] == 'official')
check('a higher kind replaces main', K.pick(rec('US-1', g='approximate'), rec('US-1', ids=('3',)))['g'] == 'official')
check('same kind from another layer: main is kept', K.pick(a, rec('US-1', layer='file:US-FL.sgfla.geojson.gz', ids=('9',))) is a)
out, kept, older = K.put_together({'US-1': a, 'US-2': rec('US-2')}, {'US-1': a, 'US-3': rec('US-3')})
check('put together: main-only kept, run-only added', sorted(out) == ['US-1', 'US-2', 'US-3'] and kept == ['US-2'] and older == [])

out, kept, older = K.put_together({'US-1': a}, {'US-1': a, 'US-7': rec('US-7'), 'US-8': rec('US-8')}, pins={'US-8'})
check('a park the key grades pin never gets a new outline', sorted(out) == ['US-1', 'US-7'])
m_ = {'files': [{'name': 'a'}, {'name': 'b'}]}; r_ = {'files': [{'name': 'b', 'x': 1}, {'name': 'c'}]}
check('raw-manifest rows only main had are kept; a row both have is the run\'s', K.rows_keep('raw-manifest.json', m_, r_) == 1 and r_['files'] == [{'name': 'a'}, {'name': 'b', 'x': 1}, {'name': 'c'}])
r_ = {'layers': {'y': 2}}
check('layers.json rows only main had are kept', K.rows_keep('layers.json', {'layers': {'x': 1, 'y': 9}, 'caches': {'c': 1}}, r_) == 2 and r_ == {'layers': {'x': 1, 'y': 2}, 'caches': {'c': 1}})

# ---- this morning, in a real git repo: main gains outlines while the run is going; the run's older file is copied on top
def sh(d, *a): return subprocess.run(a, cwd=d, capture_output=True, text=True)
with tempfile.TemporaryDirectory() as t:
    d = pathlib.Path(t); root = d / 'data/outlines'; root.mkdir(parents=True)
    sh(d, 'git', 'init', '-q'); sh(d, 'git', 'config', 'user.name', 't'); sh(d, 'git', 'config', 'user.email', 't@t')
    base = {r: rec(r) for r in ('US-1', 'US-2')}
    M.save_area('US-FL', base, root); M.save_area('US-GA', base, root); M.save_area('US-AL', base, root)
    (root / 'US-FL.sgfla.geojson.gz').write_bytes(b'layer file, not an area file')
    sh(d, 'git', 'add', '-A'); sh(d, 'git', 'commit', '-qm', 'base')
    run_fl = dict(base, **{'US-9': rec('US-9')})                          # what the run built from the old checkout
    M.save_area('US-FL', dict(base, **{r: rec(r) for r in ('US-3', 'US-4', 'US-5')}), root)   # main moves on (#129)
    sh(d, 'git', 'add', '-A'); sh(d, 'git', 'commit', '-qm', 'main moved')
    M.save_area('US-FL', run_fl, root)                                    # the copy-back: the older file on top of main
    ga_before = (root / 'US-GA.geojson.gz').read_bytes()
    (root / 'US-AL.geojson.gz').unlink()                                  # a file the run lost
    (root / 'US-FL.sgfla.geojson.gz').write_bytes(b'changed layer file')
    rc = K.run(d, root, 'HEAD'); got = M.load_area('US-FL', root)
    check('FL: every outline main had is still there, plus the run\'s new one', rc == 0 and sorted(got) == ['US-1', 'US-2', 'US-3', 'US-4', 'US-5', 'US-9'])
    check('an unchanged file is not rewritten', (root / 'US-GA.geojson.gz').read_bytes() == ga_before)
    check('a file the run lost is put back from main', sorted(M.load_area('US-AL', root)) == ['US-1', 'US-2'])
    check('a layer file is left alone', (root / 'US-FL.sgfla.geojson.gz').read_bytes() == b'changed layer file')
    check('a second pass changes nothing', K.run(d, root, 'HEAD') == 0 and sorted(M.load_area('US-FL', root)) == sorted(got))
    (root / 'US-FL.geojson.gz').write_bytes(b'not gzip')                  # fail closed
    rc = K.run(d, root, 'HEAD')
    check('a file that cannot be read: exit 1 and main\'s copy is kept', rc == 1 and sorted(M.load_area('US-FL', root)) == ['US-1', 'US-2', 'US-3', 'US-4', 'US-5'])
    check('a ref that does not exist: exit 1', K.run(d, root, 'nope') == 1)

    # ---- drop guard
    key = d / 'data/us-key'; key.mkdir(parents=True)
    def kf(st, n_off, n_pin=5):
        parks = {f'US-{st}{i}': {'g': 'official'} for i in range(n_off)}; parks.update({f'US-{st}p{i}': {'g': 'pin'} for i in range(n_pin)})
        (key / f'US-{st}.json').write_text(json.dumps({'parks': parks}))
    for st, n in (('AA', 100), ('BB', 100), ('CC', 20), ('DD', 100)): kf(st, n)
    sh(d, 'git', 'add', '-A'); sh(d, 'git', 'commit', '-qm', 'key')
    G = str(ROOT / '.github/scripts/kpc_key_drop_guard.py')
    def guard(env=None):
        m = d / 'mark'; m.unlink(missing_ok=True)
        r = subprocess.run([sys.executable, G, '--repo', str(d), '--ref', 'HEAD', '--mark', str(m)], capture_output=True, text=True, env=dict(os.environ, **(env or {})))
        return r.returncode, r.stdout, (m.read_text().split() if m.exists() else [])
    kf('AA', 97); kf('BB', 103); kf('CC', 19); kf('EE', 3)
    rc, o, mark = guard()
    check('exactly 3% down, a gain, one park of 20, a new state: pass', rc == 0 and not mark)
    kf('AA', 96); kf('DD', 50)
    rc, o, mark = guard()
    check('4% down and 50% down: exit 1, both named in the mark', rc == 1 and mark == ['AA', 'DD'] and 'US-AA::official parks 100 -> 96' in o)
    rc, o, mark = guard({'KPC_DROP_OK': 'dd'})
    check('KPC_DROP_OK lets only the named state through', rc == 1 and mark == ['AA'] and 'let through by KPC_DROP_OK' in o)
    # M2 drops outlines the key does not list, so these 50 refs have to be in US-AA.json or save_area would write an empty file
    kf('AA', 96)
    more = json.loads((key / 'US-AA.json').read_text())
    more['parks'].update({f'US-{i}': {'g': 'official'} for i in range(50)})
    (key / 'US-AA.json').write_text(json.dumps(more))
    M.save_area('US-AA', {f'US-{i}': rec(f'US-{i}') for i in range(50)}, root); sh(d, 'git', 'add', '-A'); sh(d, 'git', 'commit', '-qm', 'outlines')
    M.save_area('US-AA', {f'US-{i}': rec(f'US-{i}') for i in range(40)}, root)
    rc, o, mark = guard({'KPC_DROP_OK': 'DD'})
    check('an outline file with 20% fewer outlines than main fails too', rc == 1 and 'outlines 50 -> 40' in o and mark == ['AA'])
    M.save_area('US-AA', {f'US-{i}': rec(f'US-{i}') for i in range(50)}, root)
    rc, o, mark = guard({'KPC_DROP_OK': 'AA, DD'})
    check('both named: pass', rc == 0 and not mark)
    (key / 'US-AA.json').write_text('{broken')
    check('an unreadable key file fails the guard', guard({'KPC_DROP_OK': 'AA DD'})[0] == 1)
check('judge: counts and percent', D.judge({'NV': 210, 'WI': 318, 'ND': 200}, {'NV': 183, 'WI': 300, 'ND': 195}) == ([('NV', 210, 183, 12.9), ('WI', 318, 300, 5.7)], []))

# ---- the workflow
import yaml
wf = (ROOT / '.github/workflows/kpc-us-key.yml').read_text(encoding='utf-8'); steps = yaml.safe_load(wf)['jobs']['join']['steps']
names = [s.get('name', '') for s in steps]
def at(word): return next(i for i, n in enumerate(names) if n.startswith(word))
build = steps[at('Outlines from the key')]['run']
# Nov 12 (KPC owner, 2026-11-12): the drop guard now runs BEFORE the stamp (a state it keeps from main is named failed in the stamp)
check('order: collect -> outlines from the key -> master check -> drop guard -> stamp -> BOT C -> save',
      at('Master step') < at('Outlines from the key') < at('Master check of the joined') < at('Drop guard') < at('BUILD STAMP') < at('BOT C line') < at('Save'))
check('the outline step builds each built state from the release copy, then re-reads main',
      'kpc_outlines_from_key.py --cache .okcache --states "$st"' in build and 'gh release download boundary-cache' in build
      and build.index('kpc_outlines_from_key.py') < build.index('kpc_outlines_keep_main.py --fetch --ref origin/main') and '--dry-run' not in build)
check('the outline step is skipped when the collect failed', build.index('/tmp/kpc-outlines-bad') < build.index('pip install'))
save = steps[at('Save')]['run']; guard_step = steps[at('Drop guard')]
check('the save puts the outline files together with the newest main on every try, and stops when either command fails',
      'KPC_SAVE_REDO_STOP=yes' in save and "'python3 /tmp/done-states.py && python3 .github/scripts/kpc_outlines_keep_main.py --ref HEAD' -- data/us-key data/status data/outlines" in save)
check('a failed drop guard saves nothing', 'kpc_key_drop_guard.py --ref HEAD --mark /tmp/kpc-key-drop-bad' in guard_step['run'] and not guard_step.get('continue-on-error')
      and save.index('/tmp/kpc-key-drop-bad') < save.index('kpc_save_overwrite.sh') and 'exit 1' in save[save.index('/tmp/kpc-key-drop-bad'):save.index('git config')])
sv = (ROOT / '.github/scripts/kpc_save_overwrite.sh').read_text(); sv = sv[sv.index('if ! { git fetch -q origin main && git reset -q --hard origin/main; }'):]
check('the save script runs the redo after the copy-back on the newest main, before the commit', sv.index('cp -p "$stash/$f" "$f"') < sv.index('bash -c "$redo"') < sv.index('git commit -qm "$msg" && git push'))
# a failed redo stops the save: a real origin, a real push attempt
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); o = t / 'origin.git'; w = t / 'work'
    subprocess.run(['git', 'init', '-q', '--bare', '-b', 'main', str(o)]); subprocess.run(['git', 'clone', '-q', str(o), str(w)], capture_output=True)
    def g(*a): return subprocess.run(['git', *a], cwd=w, capture_output=True, text=True)
    g('config', 'user.name', 't'); g('config', 'user.email', 't@t'); g('checkout', '-q', '-b', 'main')
    (w / 'data').mkdir(); (w / 'data/x.json').write_text('{"a":1}'); g('add', '-A'); g('commit', '-qm', 'base'); g('push', '-q', 'origin', 'main')
    head = g('rev-parse', 'origin/main').stdout.strip()
    def save(redo, stop):
        (w / 'data/x.json').write_text('{"a":2}')
        r = subprocess.run(['bash', str(ROOT / '.github/scripts/kpc_save_overwrite.sh'), '--copy', 'T save', redo, '--', 'data'], cwd=w, capture_output=True, text=True,
                           env=dict(os.environ, KPC_SAVE_TRIES='1', KPC_SAVE_REDO_STOP=stop, KPC_QUIET_HOURS='0'))
        return r.returncode, subprocess.run(['git', 'rev-parse', 'main'], cwd=o, capture_output=True, text=True).stdout.strip()
    rc, now = save('true && false', 'yes')
    check('KPC_SAVE_REDO_STOP=yes: a failed redo = exit 1 and nothing pushed', rc == 1 and now == head)
    rc, now = save('false && true', 'yes')
    check('the first command failing stops it too (&&)', rc == 1 and now == head)
    rc, now = save('true && true', 'yes')
    check('both commands fine: saved', rc == 0 and now != head)
import kpc_key_freeze as F
fk = (ROOT / '.github/scripts/kpc_outlines_from_key.py').read_text()
check('the key-to-outline tool skips a park the key grades pin', "if q.get('g') == 'pin': continue" in fk)
check('no rules hash holds these files', not any('keep_main' in x or 'drop_guard' in x or x.endswith('.yml') for v in F.RULE_FILES.values() for x in v))
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
