#!/usr/bin/env python3
"""S2 workflow parts (keys-first hand-off rev 3.1, F21 / F22 / F7; Opus 19 Nov 2026). Offline.
1) a HELD state ends the US key run as a warning, not a failed run; a part that never came back is still red;
2) the backup daily start does not come back with the schedule;
3) every build writes its source mode, drop limits and every switch value into index.json 'settings'.
Prints PASS / FAIL lines and ends ALL PASS or SOME FAILED."""
import contextlib, io, json, os, pathlib, shutil, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_us_key_join as J  # noqa: E402
import kpc_key_freeze as F  # noqa: E402
import kpc_key_drop_guard as DG  # noqa: E402
import kpc_key_rules as KR  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


def part(t, name, states, short=(), failed=()):
    d = t / name
    d.mkdir()
    (d / 'states.txt').write_text('\n'.join(states) + '\n')
    (d / 'index.json').write_text('{}')
    if short: (d / 'master-short.txt').write_text('\n'.join('US-' + s for s in short) + '\n')
    if failed: (d / 'failed-states.txt').write_text('\n'.join(failed) + '\n')
    return str(d)


# --- 1) held = warning, missing part = red ---
t = pathlib.Path(tempfile.mkdtemp())
p1 = part(t, 'us-key-part-0', ['TN', 'KY', 'OH'], short=['KY'])
drop = t / 'drop.txt'; drop.write_text('OH\n')
groups = json.dumps([{'states': 'TN KY OH'}, {'states': 'WV'}])
rec = J.record([p1], json.dumps([{'states': 'TN KY OH'}]), drop_file=str(drop))
check('a state held by the master gate or the drop guard is HELD, not a fault',
      rec['held'] == ['KY', 'OH'] and rec['faults'] == [] and rec['red'] == ['KY', 'OH'])
rec2 = J.record([p1], groups, drop_file=str(drop))
check('a planned state whose part never came back is a FAULT (the run stays red for it)', rec2['faults'] == ['WV'] and 'WV' not in rec2['held'])
out = t / 'rec.json'
buf = io.StringIO()
with contextlib.redirect_stdout(buf):
    J.main(['record', p1, '--planned-groups', json.dumps([{'states': 'TN KY OH'}]), '--drop', str(drop), '--out', str(out)])
check('held states print a ::warning, not an ::error', '::warning title=US key run::HELD' in buf.getvalue() and '::error' not in buf.getvalue())
wf = (ROOT / '.github/workflows/kpc-us-key.yml').read_text(encoding='utf-8')
check("the run summary goes red only on faults ('faults'), and only warns on held states",
      "sys.exit(1 if r.get('faults', r.get('red')) else 0)" in wf and '::warning title=US key run::HELD' in wf
      and 'RED: the states above were kept from main' not in wf)

# --- 2) the schedule ---
check('no daily start is on, and the backup start is marked as gone when the schedule returns',
      '\n  schedule:' not in wf and "- cron: '46 11" not in wf and 'the backup start is gone' in wf)

# --- 3) settings in index.json ---
s = F.run_settings('us-key', env={})
check('settings: live source, the 3% / 1 park drop limits, every switch with its areas and default',
      s['source_mode'] == 'live' and s['drop_limits']['pct'] == 3.0 and s['drop_limits']['min_parks'] == 1
      and set(s['switches']) == set(KR.DEFAULTS) | set(KR.switch_file(str(ROOT / '.github/key-switches.json')))
      and all('on' in v and 'default' in v for v in s['switches'].values()))
st = F.run_settings('us-key', env={'KPC_KEY_SOURCE': 'store', 'KPC_DROP_PCT': '0', 'KPC_DROP_MIN': '0', 'KPC_DROP_OK': 'nv,ut',
                                  'KPC_SAVED_ID_LAND': '1'})
check('store mode: source store, drop judged park by park, the let-through states, an environment switch value is recorded',
      st['source_mode'] == 'store' and st['drop_limits']['by_park'] and st['drop_limits']['let_through'] == ['NV', 'UT']
      and st['switches'].get('KPC_SAVED_ID_LAND', {}).get('env') == '1')
check('the drop guard and the stamp read the drop limits the same way', DG.limits({}) == (3.0, 1, []) and
      DG.limits({'KPC_DROP_PCT': '0', 'KPC_DROP_MIN': '0'})[:2] == (0.0, 0))

w = pathlib.Path(tempfile.mkdtemp())
(w / 'data/us-key').mkdir(parents=True)
(w / 'data/us-key/index.json').write_text(json.dumps({'rules': 'x', 'states': {'TN': {'rules': 'x'}}}))
here = os.getcwd()
saved = {k: os.environ.get(k) for k in ('GITHUB_WORKFLOW_REF', 'KPC_KEY_SOURCE', 'GITHUB_RUN_ID', 'KPC_FULL_BUILD')}
try:
    os.chdir(w)
    os.environ.pop('GITHUB_WORKFLOW_REF', None); os.environ['KPC_KEY_SOURCE'] = 'store'; os.environ['GITHUB_RUN_ID'] = '1'
    with contextlib.redirect_stdout(io.StringIO()):
        F.stamp('us-key')
    d = json.loads((w / 'data/us-key/index.json').read_text())
finally:
    os.chdir(here)
    for k, v in saved.items():
        if v is None: os.environ.pop(k, None)
        else: os.environ[k] = v
check("the build stamp writes 'settings' into index.json (source mode, drop limits, switches)",
      d.get('build') == 'US-1' and d.get('settings', {}).get('source_mode') == 'store'
      and 'drop_limits' in d['settings'] and len(d['settings'].get('switches') or {}) >= 20)
check("the stamp step passes the source mode and the drop guard's three values",
      all(x in wf.split('id: us_stamp')[1].split('run:')[0] for x in ('KPC_KEY_SOURCE:', 'KPC_DROP_OK:', 'KPC_DROP_PCT:', 'KPC_DROP_MIN:')))
check('no rule file is edited by S2 workflow parts (they move no rules hash)',
      not any(f in F.RULE_FILES['us-key'] for f in ('.github/scripts/kpc_key_freeze.py', '.github/scripts/kpc_us_key_join.py',
                                                     '.github/scripts/kpc_key_drop_guard.py', '.github/scripts/kpc_key_scope_check.py')))

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
