#!/usr/bin/env python3
"""Nov 9 evening (Brandon t915u 4:40 PM CST; KZ4CP 5:12 PM CST): a rules change must NOT rebuild every US state. Each rule change
declares its scope in a file INSIDE its rules hash; the US key rebuilds only the declared states; a park with saved record ids keeps
its result through rule changes; the 2-fer scope file is in the 2-fer hash; a manual 'all' is the emergency full rebuild."""
import contextlib, io, json, os, pathlib, re, subprocess, sys, tempfile
HERE = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE / '.github/scripts'))
import kpc_key_freeze as KF
ok = True
def check(c, m):
    global ok; ok &= bool(c); print(('PASS ' if c else 'FAIL ') + m)
for k, f in (('us-key', '.github/us-key-rule-scope.json'), ('ca-key', '.github/ca-key-rule-scope.json'), ('fers', '.github/fers-rule-scope.json')):
    check(KF.SCOPE_FILES.get(k) == f and f in KF.RULE_FILES[k] and (HERE / f).is_file(), f'{k}: the scope file {f} is inside its rules hash')
# a tree WITHOUT the scope file keeps its old hash (so main's a066624520b4 / 8feccbb7d9ee still match the live stamps)
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    for rel in KF.RULE_FILES['fers'] + [KF.VERSION_FILE]:
        if (HERE / rel).is_file(): (t / rel).parent.mkdir(parents=True, exist_ok=True); (t / rel).write_bytes((HERE / rel).read_bytes())
    h1 = KF.rules_hash('fers', t); (t / KF.SCOPE_FILES['fers']).unlink(); h0 = KF.rules_hash('fers', t)
    check(h1 == KF.rules_hash('fers', HERE) and h0 != h1, 'the 2-fer scope file moves the 2-fer hash; with it removed the hash is the old one (no "missing" token)')
    # the scope chain
    (t / '.github').mkdir(exist_ok=True)
    (t / KF.SCOPE_FILES['us-key']).write_text(json.dumps({'changes': [
        {'id': 'a', 'from': 'h0', 'scope': {'states': ['US-TN']}}, {'id': 'b', 'from': 'h1', 'scope': {'states': ['US-KY', 'US-OH']}},
        {'id': 'c', 'from': 'h2', 'scope': 'none'}, {'id': 'd', 'from': 'h3', 'scope': {'parks': ['US-0001']}}]}))
    check(KF.pending_scope('us-key', 'h0', t) == ({'US-TN', 'US-KY', 'US-OH'}, False, {'US-0001'}), 'builds behind: the declared states and parks of every pending change, together')
    (t / KF.SCOPE_FILES['us-key']).write_text(json.dumps({'changes': [{'id': 'd', 'from': 'h3', 'scope': {'parks': ['US-0001']}}, {'id': 'e', 'from': 'h4', 'scope': {'states': []}}]}))
    check(KF.pending_scope('us-key', 'h3', t) == ('all', False, set()), 'a scope that lists nothing means ALL (KZ4CP 5:41 PM CST)')
    (t / KF.SCOPE_FILES['us-key']).write_text(json.dumps({'changes': [{'id': 'c', 'from': 'h2', 'scope': 'none'}, {'id': 'd', 'from': 'h3', 'scope': {'parks': ['US-0001']}}]}))
    check(KF.pending_scope('us-key', 'h2', t) == (set(), False, {'US-0001'}), "scope 'none' touches nothing; a park-scoped change names only its parks")
    check(KF.pending_scope('us-key', 'h3', t) == (set(), False, {'US-0001'}), 'a park-scoped change alone: no whole state, just the park')
    check(KF.pending_scope('us-key', 'zzz', t) == (None, False, set()), 'a build whose hash no change names: undeclared = the whole key (safe default)')
    (t / KF.SCOPE_FILES['us-key']).write_text(json.dumps({'changes': [{'id': 'a', 'from': 'h0', 'scope': 'all'}, {'id': 'b', 'from': 'h1', 'scope': {'states': ['US-TN'], 'saved_ids': True}}]}))
    check(KF.pending_scope('us-key', 'h0', t)[0] == 'all' and KF.pending_scope('us-key', 'h1', t) == ({'US-TN'}, True, set()), "'all' = whole key; saved_ids: true asks to re-match saved ids")
# check(): an empty declared scope sets no RULES_CHANGED; a declared state list sets RULES_SCOPE
def run_check(built, scope_changes):
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t); env = t / 'env'; env.write_text('')
        (t / '.github').mkdir(); (t / KF.SCOPE_FILES['us-key']).write_text(json.dumps({'changes': scope_changes}))
        (t / 'data/us-key').mkdir(parents=True); json.dump({'parks': {'US-0001': {}, 'US-0002': {}}}, open(t / 'data/us-key/US-TN.json', 'w'))
        old = (KF.ROOT, KF.load_index, KF.gh_json, os.environ.get('GITHUB_ENV'))
        KF.ROOT = t; KF.load_index = lambda k: {'build': 'US-1', 'rules': built}; KF.gh_json = lambda *a, **k: {}
        os.environ['GITHUB_ENV'] = str(env)
        try:
            with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()): KF.check('us-key')
        except SystemExit: pass
        finally:
            KF.ROOT, KF.load_index, KF.gh_json = old[:3]
            if old[3] is None: os.environ.pop('GITHUB_ENV', None)
            else: os.environ['GITHUB_ENV'] = old[3]
        return env.read_text()
e = run_check('h0', [{'id': 'a', 'from': 'h0', 'scope': 'none'}])
check('RULES_CHANGED' not in e, 'check(): a declared change that touches no state does not set RULES_CHANGED (nothing rebuilt)')
e = run_check('h0', [{'id': 'a', 'from': 'h0', 'scope': {'states': ['US-TN']}}])
check('RULES_CHANGED=1' in e and 'RULES_SCOPE=US-TN' in e, 'check(): a declared change with states sets RULES_SCOPE to just those states')
e = run_check('h0', [{'id': 'a', 'from': 'h0', 'scope': {'parks': ['US-0001']}}])
check('RULES_SCOPE=US-TN' in e and 'RULES_PARKS=US-0001' in e and 'RULES_ONLY_STATES=US-TN' in e and 'RULES_ONLY_PARKS=US-0001' in e,
      'check(): a park-scoped change reads only that park\'s state again, and only for that park')
e = run_check('h0', [{'id': 'a', 'from': 'h0', 'scope': {'parks': ['US-9999']}}])
check('RULES_CHANGED=1' in e and 'RULES_SCOPE' not in e, 'check(): a named park the key does not have = the whole key (safe default)')
e = run_check('h0', [{'id': 'a', 'from': 'h0', 'scope': {'states': []}}])
check('RULES_CHANGED=1' in e and 'RULES_SCOPE' not in e, 'check(): a scope that lists nothing = the whole key')
e = run_check('nope', [])
check('RULES_CHANGED=1' in e and 'RULES_SCOPE' not in e, 'check(): an undeclared change still asks for the whole key')
# the US plan step, extracted and run
wf = (HERE / '.github/workflows/kpc-us-key.yml').read_text()
m = re.search(r"python3 - <<'PY' >> \"\$GITHUB_OUTPUT\"\n(.*?)\n\s*PY\n", wf[wf.index('      - id: p'):], re.S)
code = '\n'.join(l[10:] for l in m.group(1).split('\n'))
def plan(**env):
    with tempfile.TemporaryDirectory() as t:
        os.makedirs(f'{t}/data/us-key'); json.dump({'built': '2000-01-01 00:00 UTC', 'states': {}}, open(f'{t}/data/us-key/index.json', 'w'))
        open(f'{t}/data/us-key/answers-states.txt', 'w').write('')
        e = {k: v for k, v in os.environ.items() if k not in ('FROZEN', 'RULES_CHANGED', 'RULES_SCOPE', 'RULES_REMATCH_IDS', 'STATES', 'SCHED')}; e.update(env)
        out = subprocess.run([sys.executable, '-c', code], cwd=t, env=e, capture_output=True, text=True).stdout
        g = re.search(r'^groups=(.*)$', out, re.M); f = re.search(r'^full=(.*)$', out, re.M); r = re.search(r'^rematch=(.*)$', out, re.M)
        return sorted(sum((x['states'].split() for x in json.loads(g.group(1))), [])) if g else [], (f.group(1) if f else ''), (r.group(1) if r else '')
check(plan(RULES_CHANGED='1', RULES_SCOPE='US-TN US-OH', SCHED='17 9 * * *') == (['OH', 'TN'], '1', ''), 'plan: a declared rules change builds ONLY its states (TN, OH) and that is enough to stamp the new rules (full=1)')
check(plan(RULES_CHANGED='1', RULES_SCOPE='US-TN', STATES='WI') == (['TN', 'WI'], '1', ''), 'plan: states given by hand are added to the declared ones')
check(plan(RULES_CHANGED='1', RULES_SCOPE='US-TN', RULES_REMATCH_IDS='1')[2] == '1', 'plan: a change with saved_ids: true passes rematch=1 to the build')
s, f, _ = plan(RULES_CHANGED='1')
check(len(s) == 50 and f == '1', 'plan: an UNDECLARED rules change still builds every state (safe default)')
s, f, _ = plan(STATES='all')
check(len(s) == 50 and f == '1', "plan: the 'all' input = the emergency full rebuild")
def plan2(**env):
    with tempfile.TemporaryDirectory() as t:
        os.makedirs(f'{t}/data/us-key'); json.dump({'built': '2000-01-01 00:00 UTC', 'states': {}}, open(f'{t}/data/us-key/index.json', 'w'))
        e = {k: v for k, v in os.environ.items() if not k.startswith('RULES_') and k not in ('FROZEN', 'STATES', 'SCHED')}; e.update(env)
        out = subprocess.run([sys.executable, '-c', code], cwd=t, env=e, capture_output=True, text=True).stdout
        return dict(re.findall(r'^(only_states|only_parks|full)=(.*)$', out, re.M))
o = plan2(RULES_CHANGED='1', RULES_SCOPE='US-TN US-OH', RULES_PARKS='US-0001', RULES_ONLY_STATES='US-TN')
check(o == {'full': '1', 'only_states': 'TN', 'only_parks': 'US-0001'}, f'plan: a park-scoped change: TN is read again only for US-0001; OH (a whole-state change) in full ({o})')
o = plan2(RULES_CHANGED='1', RULES_SCOPE='US-TN', RULES_PARKS='US-0001', RULES_ONLY_STATES='US-TN', STATES='TN')
check(o.get('only_states') == '' and o.get('only_parks') == '', 'plan: a state given by hand is rebuilt in full')
o = plan2(RULES_CHANGED='1', RULES_SCOPE='US-TN', RULES_PARKS='US-0001', RULES_ONLY_STATES='US-TN', SCHED='37 9 1 * *')
check(o.get('only_states') == '', 'plan: the monthly run is a full rebuild (no park limit)')
check('KPC_KEY_ONLY_STATES: ${{ needs.plan.outputs.only_states }}' in wf and 'KPC_KEY_ONLY_PARKS: ${{ needs.plan.outputs.only_parks }}' in wf, 'the build gets the park limit from the plan')
caw = (HERE / '.github/workflows/kpc-ca-key.yml').read_text()
check("KPC_KEY_ONLY_PARKS: ${{ !((github.event.schedule || inputs.as_schedule) == '43 10 2 * *' && !inputs.saved) && env.RULES_ONLY_PARKS || '' }}" in caw, 'Canada: the park limit on saved-copy runs only (not the monthly live re-read)')
check('KPC_KEY_REMATCH_IDS: ${{ needs.plan.outputs.rematch }}' in wf and 'rematch: ${{ steps.p.outputs.rematch }}' in wf, 'the build gets KPC_KEY_REMATCH_IDS from the plan')
# the saved-id carry in kpc_us_key.py, extracted and run on a small case
src = (HERE / '.github/scripts/kpc_us_key.py').read_text()
i = src.index("    if os.environ.get('KPC_KEY_REMATCH_IDS') != '1':"); j = src.index('    try:\n        for ref, t in transfers()', i)
blk = '\n'.join(l[4:] for l in src[i:j].split('\n'))
def carry(rematch=''):
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t)
        json.dump({'parks': {'US-1': {'n': 'Old name', 'm': [['10', 'A', 5, 'id']]}, 'US-2': {'m': [['20', 'B', 5, 'id']]}, 'US-3': {'m': [['30', 'C', 5, 'id']]},
                             'US-4': {'m': [['40', 'D', 5, 'id']]}, 'US-5': {'m': [['50', 'E', 5, 'id']]}}}, open(t / 'US-TN.json', 'w'))
        parks = {'US-1': {'n': 'New name', 'm': [['11', 'X', 9, 'name']]}, 'US-2': {'m': [['21', 'Y', 9, 'name']]}, 'US-3': {'m': [['31', 'Z', 9, 'name']]},
                 'US-4': {'m': []}, 'US-5': {'m': [['50', 'E', 5, 'id']]}}
        g = {'os': os, 'json': json, 'OUT': t, 'st': 'TN', 'recs': [{'OBJECTID': x} for x in (10, 11, 20, 21, 31, 40, 50)], '_oid': lambda a: str(a['OBJECTID']),
             'parks': parks, 'OVR': {'US-2': {'join': ['21']}}, 'BLOCKED': {'US-4': {'40'}}, 'notice': lambda *a: None}
        old = os.environ.get('KPC_KEY_REMATCH_IDS'); os.environ['KPC_KEY_REMATCH_IDS'] = rematch
        try: exec(blk, g)
        finally:
            if old is None: os.environ.pop('KPC_KEY_REMATCH_IDS')
            else: os.environ['KPC_KEY_REMATCH_IDS'] = old
        return parks
p = carry()
check(p['US-1']['m'][0][0] == '10' and p['US-1']['n'] == 'New name' and p['US-1'].get('kept_ids'), 'a park with saved ids (all still in the read) keeps its result through a rules change (POTA name refreshed)')
check(p['US-2']['m'][0][0] == '21', "a person's override wins (hand decisions are applied as they are)")
check(p['US-3']['m'][0][0] == '31', 'a saved id gone from the read: no carry (the keep-last-good guard handles a missing record)')
check(p['US-4']['m'] == [], 'a saved id on the bad-ID block list: no carry')
check(not p['US-5'].get('kept_ids'), 'an unchanged result is left as it is')
check(carry('1')['US-1']['m'][0][0] == '11', 'KPC_KEY_REMATCH_IDS=1 (a change with saved_ids: true): parks are matched fresh')
i = src.index("    _only = set((os.environ.get('KPC_KEY_ONLY_PARKS')"); j = src.index('    try:\n        for ref, t in transfers()', i)
blk2 = '\n'.join(l[4:] for l in src[i:j].split('\n'))
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t)
    json.dump({'parks': {'US-1': {'m': [['1']]}, 'US-2': {'m': [['2']]}, 'US-3': {'m': [['3']]}}}, open(t / 'US-TN.json', 'w'))
    parks = {'US-1': {'m': [['9']]}, 'US-2': {'m': [['8']]}, 'US-3': {'m': [['7']]}, 'US-4': {'m': [['6']]}}
    old = {k: os.environ.get(k) for k in ('KPC_KEY_ONLY_PARKS', 'KPC_KEY_ONLY_STATES')}
    os.environ.update(KPC_KEY_ONLY_PARKS='US-1', KPC_KEY_ONLY_STATES='TN')
    try: exec(blk2, {'os': os, 'json': json, 'OUT': t, 'st': 'TN', 'parks': parks, 'OVR': {'US-3': {}}, 'notice': lambda *a: None})
    finally:
        for k, v in old.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v
    check(parks['US-1']['m'] == [['9']] and parks['US-2']['m'] == [['2']] and parks['US-3']['m'] == [['7']] and parks['US-4']['m'] == [['6']],
          'US key: only the named park is re-matched; others keep their result (a person override and a new park are applied as they are)')
cs = (HERE / '.github/scripts/kpc_ca_key.py').read_text()
check("_ONLY = set((os.environ.get('KPC_KEY_ONLY_PARKS')" in cs and '_r not in _ONLY and _r not in OVR' in cs, 'Canada key: same park limit')
# 2-fers: a park-scoped change stamps only that park, so only its pairs (the park + the parks touching it) are tested again
import kpc_fers as F
F.SCOPE[:] = [{'id': 'p1', 'scope': {'parks': ['US-0001']}}, {'id': 'n', 'scope': 'none'}]; F._STAMP.clear()
check(F.rule_stamp('US-0001') == ['p1'] and F.rule_stamp('US-0002') == [], '2-fers: a park-scoped change stamps only the named park (its pairs, i.e. the parks touching it, are retested)')
F.SCOPE[:] = [{'id': 'e', 'scope': {'states': [], 'parks': []}}]; F._STAMP.clear()
check(F.rule_stamp('US-0002') == ['e'], '2-fers: a scope that lists nothing means ALL')
fs = json.load(open(HERE / '.github/fers-rule-scope.json'))
check('parks' in fs['about'] and all(c.get('scope') != {} for c in fs['changes']), 'the 2-fer scope file explains park refs')
print('ALL PASS' if ok else 'FAILED'); sys.exit(0 if ok else 1)
