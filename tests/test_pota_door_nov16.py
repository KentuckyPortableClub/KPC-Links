#!/usr/bin/env python3
"""KPC owner, 2026-11-16 (handoff 'proof of work', item 7: be polite to POTA).
  1. No NEW direct api.pota.app call: every code file (.py .js .mjs .html .yml .sh, not tests/ data/ docs/ notes/) is counted
     against tests/pota-door-baseline.json. A Python script may not name api.pota.app at all (only the door, kpc_pota_door.py;
     kpc_net_guard's / kpc_pin_guard's text); a page script may not name it more often than the baseline (the browser door
     snippet is not counted; spots are never read from POTA by a page). A new file naming it fails.
  2. The door: its selftest (ages, budget, report line, User-Agent with a contact).
  3. The park-list readers read the saved copy only; the spotter and hunters read the club spot file.
  4. Every page script that carries the browser door carries the SAME copy; no page reads POTA's spot feed.
  5. No schedule changed: every 'cron:' line is as on main (git), and no new workflow file."""
import json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCR = ROOT / '.github' / 'scripts'
FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok: FAILS.append(what)


sys.path.insert(0, str(SCR))
SNIP_RX = re.compile(r'/\* KPC POTA door for the browser.*?return\{spots,spotsResponse,parkList,poll,SPOTS\}\}\)\(\);\n', re.S)
PY_OK = {'.github/scripts/kpc_pota_door.py', '.github/scripts/kpc_net_guard.py', '.github/scripts/kpc_pin_guard.py'}
SKIP = re.compile(r'^(tests|data|docs|notes|node_modules|\.git)/')
EXT = ('.py', '.js', '.mjs', '.html', '.yml', '.yaml', '.sh')


def counts(root=ROOT):
    out, snips = {}, {}
    files = subprocess.run(['git', 'ls-files'], cwd=root, capture_output=True, text=True).stdout.split('\n')
    files += subprocess.run(['git', 'ls-files', '--others', '--exclude-standard'], cwd=root, capture_output=True, text=True).stdout.split('\n')
    for rel in sorted(set(f for f in files if f)):
        if SKIP.match(rel) or not rel.endswith(EXT): continue
        p = root / rel
        if not p.is_file(): continue
        s = p.read_text(encoding='utf-8', errors='replace')
        m = SNIP_RX.findall(s)
        if m: snips[rel] = m
        n = SNIP_RX.sub('', s).count('api.pota.app')
        if n: out[rel] = n
    return out, snips


if __name__ == '__main__' and '--write-baseline' in sys.argv[1:]:
    c, _ = counts()
    doc = {'about': 'Item 7 (KPC owner, 2026-11-16): api.pota.app mentions per code file. A Python script names it only in the door. '
                    'A page may not name it more often than here (its self-spot POST, park details / lookups / user stats it reads on a '
                    'person\'s click). Lower a number when a call goes; never raise one.',
           'files': {k: v for k, v in c.items() if not k.endswith('.py') or k in PY_OK}}
    (ROOT / 'tests/pota-door-baseline.json').write_text(json.dumps(doc, indent=1) + '\n', encoding='utf-8')
    print('written'); sys.exit(0)

base = json.loads((ROOT / 'tests/pota-door-baseline.json').read_text(encoding='utf-8'))['files']
now, snips = counts()
py_bad = sorted(k for k in now if k.endswith('.py') and k not in PY_OK)
check(not py_bad, f'1. no Python script names api.pota.app except the door ({py_bad})')
grew = sorted(f'{k}: {base.get(k, 0)} -> {v}' for k, v in now.items() if v > base.get(k, 0))
check(not grew, f'1. no new direct api.pota.app call in any code file ({grew})')
check('kpc_social.js' in ' '.join(base) and base.get('.github/scripts/kpc_social.js') == 1, '1. kpc_social.js names POTA once (its own paced door)')

import kpc_pota_door as D  # noqa: E402
r = subprocess.run([sys.executable, '-B', str(SCR / 'kpc_pota_door.py'), '--selftest'], capture_output=True, text=True)
check(r.returncode == 0 and 'SELFTEST PASS' in r.stdout, '2. the door selftest passes (stored copy first, ages, budget, report line)')
check(D.AGES['spots'] == 300 and D.AGES['details'] == 30 * 86400 and D.AGES['activations'] == 30 * 86400 and D.AGES['locations'] == 86400,
      '2. allowed ages: spots 5 min, /locations 1 day, details and activation history 30 days')
check('contact:' in D.UA and 'Kentucky Portable Club' in D.UA, '2. a club User-Agent with a contact')

for f in ('kpc_world_pota', 'kpc_canada', 'kpc_northam', 'kpc_new_refs', 'kpc_state_links', 'kpc_top25', 'kpc_refcheck', 'kpc_new_lands'):
    s = (SCR / f'{f}.py').read_text(encoding='utf-8')
    check('DOOR.saved_park_list(' in s and 'DOOR.fetch_' not in s and '_ask(' not in s, f'3. {f} reads the saved park lists only (never POTA)')
s = (SCR / 'kpc_state_links.py').read_text(encoding='utf-8')
check('DOOR.park(ref, ask_pota=False)' in s, '3. kpc_state_links reads park details from the saved copy only')
for f in ('kpc_pota_spotter', 'kpc_hunters'):
    check('DOOR.club_spots(' in (SCR / f'{f}.py').read_text(encoding='utf-8'), f'3. {f} reads the club spot file')
check('DOOR.fetch_spots()' in (SCR / 'kpc_pota_spots.py').read_text(encoding='utf-8'), '3. the one club spot reader asks through the door')

one = {x for v in snips.values() for x in v}
check(len(one) == 1 and len(snips) >= 10, f'4. every page script carries the same browser door ({len(snips)} files, {len(one)} version(s))')
spot_reads = sorted(k for k in now if re.search(r"api\.pota\.app/spot/activator", SNIP_RX.sub('', (ROOT / k).read_text(encoding='utf-8', errors='replace'))))
check(not spot_reads, f'4. no page or script reads POTA\'s spot feed itself ({spot_reads})')

def crons(ref=None):
    out = {}
    if ref:
        names = subprocess.run(['git', 'ls-tree', '--name-only', ref, '.github/workflows/'], cwd=ROOT, capture_output=True, text=True).stdout.split()
        for n in names:
            t = subprocess.run(['git', 'show', f'{ref}:{n}'], cwd=ROOT, capture_output=True, text=True).stdout
            out[n] = [l.strip() for l in t.splitlines() if 'cron:' in l]
    else:
        for p in sorted((ROOT / '.github/workflows').glob('*.y*ml')):
            out[f'.github/workflows/{p.name}'] = [l.strip() for l in p.read_text(encoding='utf-8').splitlines() if 'cron:' in l]
    return out
base_ref = next((r for r in ('origin/main', 'main') if subprocess.run(['git', 'rev-parse', '--verify', '-q', r], cwd=ROOT, capture_output=True).returncode == 0), None)
if base_ref:
    a, b = crons(base_ref), crons()
    check(a == b, f'5. no schedule changed and no new workflow (against {base_ref})')
else: print('SKIP 5: no main to compare with')

print('ALL PASS' if not FAILS else 'SOME FAILED')
sys.exit(1 if FAILS else 0)
