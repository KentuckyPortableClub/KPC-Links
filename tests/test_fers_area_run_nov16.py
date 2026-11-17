#!/usr/bin/env python3
"""KPC owner, 2026-11-16 (handoff 'proof of work', item 3): one list of steps for GitHub and the PC (kpc_fers_area_run.py).
Offline, dry runs only (every command is printed, nothing is run): the step list and its order; a store run runs the bot as ONE
process (kpc_fers_store.py chain 1,2,3,5), any other run as the separate passes; the PC's settings file gives only paths; no step
calls POTA (the POTA history step is gone, item 7); done is the receipt (a red receipt = exit 2, never 0)."""
import json, os, pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCR = ROOT / '.github' / 'scripts'
DRV = SCR / 'kpc_fers_area_run.py'
sys.path.insert(0, str(SCR))
FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok: FAILS.append(what)


def drv(*a, cwd=None):
    r = subprocess.run([sys.executable, str(DRV)] + list(a), capture_output=True, text=True, cwd=cwd)
    return r.returncode, r.stdout + r.stderr


import kpc_fers_area_run as A  # noqa: E402
check(A.STEPS == ('overlay', 'last-files', 'key-gate', 'seed', 'bot', 'expected', 'jump', 'pick', 'annotate', 'waiting-room'),
      'the step list, in order: overlay, last files, key gate, seed, bot, expected, pick, annotate, waiting room')
rc, out = drv('--kpcdata', 'kpcdata', '--states', 'US-RI', '--tag', 'us-ri', '--store', 'on', '--dry-run')
lines = [l for l in out.splitlines() if l.startswith('[') and ' done in ' not in l]
order = list(dict.fromkeys(l[1:l.index(']')] for l in lines))
check(rc == 0 and order == list(A.STEPS), f'a dry run walks every step in order ({order})')
bot = [l for l in lines if l.startswith('[bot]')]
check(len(bot) == 1 and 'kpc_fers_store.py chain 1,2,3,5' in bot[0], 'a store run: the bot is ONE process, passes 1, 2, 3, 5 (the store loaded once)')
rc, out = drv('--kpcdata', 'kpcdata', '--states', 'US-KY', '--region', 'ky', '--dry-run', '--only', 'bot')
bl = [l for l in out.splitlines() if l.startswith('[bot]') and 'kpc_fers.py' in l]
check(rc == 0 and len(bl) == 4 and 'kpc_fers_known.py' in out, f'a run that downloads (Kentucky): the separate passes stay ({len(bl)} pass commands) + the known pairs')
check('pota' not in out.lower().replace('kpc_fers', ''), 'no step of the list asks POTA for anything (the POTA history step is gone)')
check(subprocess.run([sys.executable, str(DRV), '--states', 'US-RI', '--store', 'on', '--dry-run', '--only', 'nosuch'], capture_output=True).returncode == 4, 'an unknown step is refused')
with tempfile.TemporaryDirectory() as td:
    s = pathlib.Path(td) / 'settings.json'
    s.write_text(json.dumps({'kpcdata': str(pathlib.Path(td) / 'kd'), 'store_dir': str(pathlib.Path(td) / 'store'), 'pota_history': True}))
    rc, out = drv('--settings', str(s), '--states', 'US-RI', '--tag', 'us-ri', '--store', 'on', '--dry-run', '--only', 'key-gate')
    check(rc == 0 and str(pathlib.Path(td) / 'kd') in out, "the PC's settings file gives the paths (and pota_history is not read: nothing uses it)")
check('pota_history' not in DRV.read_text().replace("'pota_history'", ''), 'the driver has no POTA history switch')
# done = the receipt: a bot step whose receipt is red ends the run with exit 2
import kpc_fers_receipt as R  # noqa: E402
with tempfile.TemporaryDirectory() as td:
    t = pathlib.Path(td)
    (t / 'data/fers').mkdir(parents=True)
    a = A.parse(['--states', 'US-RI', '--tag', 'us-ri', '--links', str(t), '--store', 'off'])
    r = A.Run(a)
    r.sh = lambda *x, **k: 0   # the passes "ran" and said 0, but wrote no receipt
    try: r.bot(); code = 0
    except A.StepFailed as e: code = e.code
    check(code == 2, 'exit 0 from the passes but no receipt: the bot step is red (done is the receipt, never the exit code or the log)')
    import kpc_key_freeze as KFZ
    for q in (1, 2, 3, 5):
        p, doc = R.merge(t / 'data/fers', 'us-ri', q, {'areas': {'US-RI': 'measured'}, 'rules_hash': KFZ.rules_hash('fers', t)})
        p.write_text(json.dumps(doc))
    try: r.bot(); code = 0
    except A.StepFailed as e: code = e.code
    check(code == 0, 'a receipt with every pass measured on today\'s rules: the bot step is done')
print('ALL PASS' if not FAILS else 'SOME FAILED')
sys.exit(1 if FAILS else 0)
