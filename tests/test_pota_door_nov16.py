#!/usr/bin/env python3
"""KPC owner, 2026-11-16 (handoff 'proof of work', item 7: be polite to POTA).
  1. No NEW direct api.pota.app call: every code file (.py .js .mjs .html .yml .sh, not tests/ data/ docs/ notes/) is counted
     against tests/pota-door-baseline.json. A Python script may not name api.pota.app at all (only the door, kpc_pota_door.py;
     kpc_net_guard's / kpc_pin_guard's text); a page script may not name it more often than the baseline (the browser door
     snippet is not counted; spots are never read from POTA by a page). A new file naming it fails.
  2. The door: its selftest (ages, budget, report line, User-Agent with a contact).
  2b. v4: the park lists come from POTA's one all-parks export (no /locations); 20 location lists a run at most.
  3. The park-list readers read the saved copy only; the spotter, hunters and Discord ask read the club spot relay (its address in
     ONE setting, kpc-spots.json; POTA only when the relay does not answer or its copy is over 30 minutes old). Nothing saves spots
     anywhere (no live-spots branch, no spot commits); no force-push anywhere.
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
SNIP_RX = re.compile(r'/\* KPC POTA door for the browser.*?return\{spots,spotsResponse,parkList,poll,age,setting\}\}\)\(\);\n', re.S)
PY_OK = {'.github/scripts/kpc_pota_door.py', '.github/scripts/kpc_net_guard.py', '.github/scripts/kpc_pin_guard.py'}
SKIP = re.compile(r'^(tests|data|docs|notes|node_modules|\.git)/')
RELAY_CODE = 'tools/kpc-spot-relay.js'   # the spot relay itself (the Cloudflare Worker, #226): it reads POTA's spot list and names its own address
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
check(D.AGES['details'] == 30 * 86400 and D.AGES['activations'] == 30 * 86400 and D.AGES['export'] <= 86400 and 'locations' not in D.AGES and 'spots' not in D.AGES,
      '2. allowed ages: the all-parks export once a day, details and activation history 30 days (no /locations; spots come from the relay)')
# v4 answer 2: the park lists come from the one all-parks export, compared with yesterday's copy; /locations is never asked
py_loc = sorted(str(f.relative_to(ROOT)) for f in SCR.glob('*.py') if "_ask('/locations')" in f.read_text(encoding='utf-8', errors='replace'))
check(not py_loc, f'2. no script asks POTA for /locations ({py_loc})')
pl = (SCR / 'kpc_pota_parklists.py').read_text(encoding='utf-8')
check('DOOR.sync_export()' in pl and 'DOOR.ExportGone' in pl and 'DOOR.write_receipt(' in pl and D.EXPORT_URL.endswith('/all_parks_ext.csv'),
      '2. the park-list job reads the all-parks export, falls back when it is gone, and writes its receipt')
cfg = json.loads((ROOT / '.github/pota-parklists.json').read_text(encoding='utf-8'))
check(cfg.get('max_lists_per_run') == 20 and cfg.get('home_list_max_days') == 7, '2. at most 20 location lists a run; the 7-day re-pull is the fallback')
check('contact:' in D.UA and 'Kentucky Portable Club' in D.UA, '2. a club User-Agent with a contact')

for f in ('kpc_world_pota', 'kpc_canada', 'kpc_northam', 'kpc_new_refs', 'kpc_state_links', 'kpc_top25', 'kpc_refcheck', 'kpc_new_lands'):
    s = (SCR / f'{f}.py').read_text(encoding='utf-8')
    check('DOOR.saved_park_list(' in s and 'DOOR.fetch_' not in s and '_ask(' not in s, f'3. {f} reads the saved park lists only (never POTA)')
s = (SCR / 'kpc_state_links.py').read_text(encoding='utf-8')
check('DOOR.park(ref, ask_pota=False)' in s, '3. kpc_state_links reads park details from the saved copy only')
for f in ('kpc_pota_spotter', 'kpc_hunters', 'kpc_discord_ask'):
    check('DOOR.club_spots()' in (SCR / f'{f}.py').read_text(encoding='utf-8'), f'3. {f} reads the club spot relay (POTA only when it does not answer or is over 30 minutes old)')
# the spot relay: its address in ONE setting (kpc-spots.json), read by the door (bots) and the browser door (pages)
spot_cfg = json.loads((ROOT / 'kpc-spots.json').read_text(encoding='utf-8'))
RELAY = spot_cfg.get('relay', '')
check(RELAY == 'https://kpc-spots.kentuckyportableclub.workers.dev/spots' and spot_cfg.get('age_header') == 'x-kpc-spot-age' and spot_cfg.get('stale_seconds') == 1800,
      '3. kpc-spots.json holds the relay address, its age header and the 30-minute fallback age')
check(D.SPOT_CONFIG == ROOT / 'kpc-spots.json' and D.spot_setting()['relay'] == RELAY, '3. the door reads the relay address from kpc-spots.json')
host = RELAY.split('/')[2] if RELAY else 'kpc-spots.'
named = sorted(k for k in subprocess.run(['git', 'ls-files'], cwd=ROOT, capture_output=True, text=True).stdout.split('\n')
               + subprocess.run(['git', 'ls-files', '--others', '--exclude-standard'], cwd=ROOT, capture_output=True, text=True).stdout.split('\n')
               if k and k not in ('kpc-spots.json', RELAY_CODE) and not SKIP.match(k) and (ROOT / k).is_file()
               and host in (ROOT / k).read_text(encoding='utf-8', errors='replace'))
check(not named, f'3. the relay address is written in ONE place only, kpc-spots.json ({named[:5]})')
gone = [f for f in ('.github/scripts/kpc_live_spots_push.sh', '.github/scripts/kpc_pota_spots.py') if (ROOT / f).exists()]
check(not gone, f'3. no spot saver is left (the live-spots push and the club spot reader are gone) ({gone})')
ls = sorted(k for k in subprocess.run(['git', 'ls-files'], cwd=ROOT, capture_output=True, text=True).stdout.split('\n')
            if k and not k.startswith(('tests/', 'docs/', 'notes/', 'data/')) and (ROOT / k).is_file()
            and re.search(r'live-spots|live_spots|data/pota/spots\.json', (ROOT / k).read_text(encoding='utf-8', errors='replace')))
check(not ls, f'3. nothing reads or writes a live-spots branch or a saved spot file any more ({ls[:5]})')
wf = (ROOT / '.github/workflows/kpc-pota-discord.yml').read_text(encoding='utf-8')
main_wf = subprocess.run(['git', 'show', 'origin/main:.github/workflows/kpc-pota-discord.yml'], cwd=ROOT, capture_output=True, text=True).stdout
check(not main_wf or wf == main_wf, "3. the Discord spotter job is main's (no spot reads or saves added to it)")
forced = []
for p in list((ROOT / '.github').rglob('*.sh')) + list((ROOT / '.github').rglob('*.yml')) + list((ROOT / '.github').rglob('*.py')):
    for l in p.read_text(encoding='utf-8', errors='replace').splitlines():
        if re.search(r'git\b.*\bpush\b.*(--force\b|--force-with-lease|\s-f\b|\s\+\S+:)', l) and not l.lstrip().startswith('#'): forced.append((str(p.relative_to(ROOT)), l.strip()))
def _on_main(rel, line):   # a forced push already on main (its own job's data branch) is not this change's
    t = subprocess.run(['git', 'show', f'origin/main:{rel}'], cwd=ROOT, capture_output=True, text=True).stdout
    return line in {x.strip() for x in t.splitlines()}
new_forced = [f'{r}: {l[:80]}' for r, l in forced if not _on_main(r, l)]
check(not new_forced, f'3. no new force-push in any script or workflow ({new_forced[:3]})')

one = {x for v in snips.values() for x in v}
check(len(one) == 1 and len(snips) >= 10, f'4. every page script carries the same browser door ({len(snips)} files, {len(one)} version(s))')
sn = next(iter(one), '')
check("root()+'kpc-spots.json'" in sn and 'r.headers.get(c.hdr)' in sn and 'STALE=18e5' in sn and 'GAP=3e5' in sn and 'document.hidden||' in sn and 'kpcSpotAge' in sn
      and 'DAY=864e5' in sn and 'live-spots' not in sn and host not in sn,
      '4. the browser door reads the relay address from kpc-spots.json, shows the age from x-kpc-spot-age, and reads POTA only when the relay does not answer or is over 30 minutes old (at most once per 5 minutes per browser, never while hidden); lists kept 24 h')
spot_reads = sorted(k for k in now if k != RELAY_CODE and re.search(r"api\.pota\.app/spot/activator", SNIP_RX.sub('', (ROOT / k).read_text(encoding='utf-8', errors='replace'))))
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
