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
check('a planned state whose part never came back (not-built) is a FAULT (the run stays red for it)', rec2['faults'] == ['WV'] and 'WV' not in rec2['held'])
# Fable's review of #294 (1): one line per code
p2 = part(t, 'us-key-part-1', ['GA', 'AL', 'MS'], failed=['AL'])
ff = t / 'failed.txt'; ff.write_text('MS\n')
rec3 = J.record([p2], json.dumps([{'states': 'GA AL MS'}]), failed_file=str(ff))
codes = {a: x['code'] for a, x in rec3['areas'].items()}
check("code 'failed' (planned but not built / a short shape source not refilled) is a FAULT", codes['AL'] == 'failed' and 'AL' in rec3['faults'])
check("code 'failed' (named failed in the stamp) is a FAULT", codes['MS'] == 'failed' and 'MS' in rec3['faults'])
check("code 'held-gate' is HELD (a warning)", rec['areas']['KY']['code'] == 'held-gate' and 'KY' in rec['held'])
check("code 'drop-guard' is HELD (a warning)", rec['areas']['OH']['code'] == 'drop-guard' and 'OH' in rec['held'])
check("code 'built' is neither", 'GA' not in rec3['faults'] and 'GA' not in rec3['held'] and rec3['areas']['GA']['code'] == 'built')
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
_st_env = wf.split('id: us_stamp')[1].split('run:')[0]
check("the stamp records the drop limits the guard ran with (the guard writes them; the three values are set once, on the guard step)",
      'KPC_KEY_SOURCE:' in _st_env and 'KPC_DROP_LIMITS_FILE: /tmp/kpc-drop-limits.json' in _st_env
      and not any(x in _st_env for x in ('KPC_DROP_OK:', 'KPC_DROP_PCT:', 'KPC_DROP_MIN:'))
      and 'KPC_DROP_LIMITS_OUT: /tmp/kpc-drop-limits.json' in wf)
lf = pathlib.Path(tempfile.mkdtemp()) / 'limits.json'
lf.write_text(json.dumps({'pct': 0.0, 'min_parks': 0, 'let_through': ['MT']}))
got = F.run_settings('us-key', env={'KPC_DROP_LIMITS_FILE': str(lf), 'KPC_DROP_PCT': '3'})['drop_limits']
check("the stamp takes the guard's file over the environment", got['pct'] == 0.0 and got['min_parks'] == 0 and got['let_through'] == ['MT'] and got['by_park'])
check('no rule file is edited by S2 workflow parts (they move no rules hash)',
      not any(f in F.RULE_FILES['us-key'] for f in ('.github/scripts/kpc_key_freeze.py', '.github/scripts/kpc_us_key_join.py',
                                                     '.github/scripts/kpc_key_drop_guard.py', '.github/scripts/kpc_key_scope_check.py')))

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
