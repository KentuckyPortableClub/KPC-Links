#!/usr/bin/env python3
"""The Japan A10 crosswalk in the world key, behind a switch that stays OFF (KPC owner, 2026-11-12; brief item 7, handoff item 6).
The Japan A10 licence terms are an open owner question: nothing here may change a result until he signs. Offline: every socket is
refused (here and in the builder this test starts); the real kpc_world_key.py runs on SYNTHETIC saved copies (GEO_CACHE_MODE=only).
  1. the file: 70 rows, 7 columns, no duplicate ref; findings listed (one name given for two parks: 多良岳, JP-1709 / JP-1717);
     with a KPC-Data checkout, every ref is in the JP park list; what the switch would use: 30 rows (class 1-3, match / note), held 2,
     not used 38 (34 class U facilities, 4 'other');
  2. the switch: unset / empty / off / anything else = OFF; 'on' = ON. OFF = the crosswalk is never read (zero reads) and apply()
     changes nothing; the run says 'JP A10 crosswalk: OFF (licence not signed)';
  3. the world key, end to end: switch OFF = every output byte-identical to the builder WITHOUT this commit (JP and the others);
     switch ON = only JP changes: a park joins its A10 record through the crosswalk name (near the pin), a record far from the pin
     is HELD (check by hand, not joined), one name for two parks is HELD, a class U facility is never joined to the natural park
     around it, a park already joined keeps its join; a malformed crosswalk = nothing applied (warning), output as OFF;
  4. hashes: world moved again (declared, scope none: no area is due with the switch off), CA / US / fers did not; kpc_key_facts.py
     and kpc_match.py untouched; kpc_jp_crosswalk.py is in NOT_RULES; the workflow passes the repo switch, default off."""
import contextlib, io, json, os, pathlib, re, subprocess, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import kpc_pinfill_fixture as H   # noqa: E402  (refuses every socket on import)
import kpc_jp_crosswalk as JPX   # noqa: E402
import kpc_key_freeze as KF, kpc_preflight as PF   # noqa: E402

ok = True
def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)

CSV = H.ROOT / JPX.FILE
# ---------------------------------------------------------------- 1. the file
rows, prob = JPX.read(str(CSV))
check(not prob and len(rows) == 70 and len({r['ref'] for r in rows}) == 70, f'70 rows, 70 different refs ({prob or len(rows)})')
an = JPX.anomalies(rows)
check(an == ['多良岳県立自然公園: one name for 2 parks (JP-1709 JP-1717)'], f'findings (reported, the file is not changed): {an}')
use, skip = JPX.plan(rows)
from collections import Counter
check(len(use) == 30 and Counter(v.split(':')[0] for v in skip.values()) == {'not used': 38, 'held': 2}
      and sum(1 for r in rows if r['park_class'] == 'U') == 34 and sum(1 for v in skip.values() if 'answer is other' in v) == 4,
      f'with the switch ON: 30 rows may join, 2 held (one name, two parks), 38 not used (34 class U facilities, 4 answered other)')
check(skip['JP-1709'].startswith('held') and skip['JP-1717'].startswith('held') and 'never the natural park around it' in skip['JP-1115'],
      'JP-1709 / JP-1717 are held (one A10 name for two parks); JP-1115 (Kairakuen, inside 水戸県立自然公園) is never joined to the park around it')
if H.DATA and (H.DATA / 'data/parkinfo/JP.json').is_file():
    jp = json.load(open(H.DATA / 'data/parkinfo/JP.json', encoding='utf-8'))['parks']
    check(not JPX.anomalies(rows, set(jp))[1:], 'KPC-Data park list: every crosswalk ref is a JP park')
else:
    print('     (no KPC-Data checkout next to this repo: the park-list check is skipped)')

# ---------------------------------------------------------------- 2. the switch
check([JPX.is_on({JPX.ENV: v} if v is not None else {}) for v in (None, '', 'off', 'OFF', 'yes', '1', 'true', 'on', ' On ')] == [False] * 7 + [True, True],
      'the switch: only on (any case) is ON; unset, empty, off, yes, 1, true are OFF')
reads = []
real_read = JPX.read
JPX.read = lambda *a, **k: reads.append(a) or real_read(*a, **k)
try:
    parks = {'JP-1047': {'n': 'x', 'm': [], 'c': []}}; before = json.dumps(parks)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): got = JPX.apply('JP', parks, {'JP-1047': ['x', '', '', '', '', 38.45, 140.63]}, [], lambda t: t, None, None, env={})
    check(not reads and got['on'] is False and json.dumps(parks) == before and 'JP A10 crosswalk::OFF (licence not signed)' in buf.getvalue(),
          'switch OFF: the crosswalk is never read (zero reads), nothing changes, the run says OFF (licence not signed)')
    with contextlib.redirect_stdout(io.StringIO()): JPX.apply('NZ', parks, {}, [], None, None, None, env={JPX.ENV: 'on'})
    check(not reads, 'another country never reads it, even with the switch on')
finally:
    JPX.read = real_read

# ---------------------------------------------------------------- 3. the world key, end to end
def wrow(n, t, la, lo): return [n, '', t, '', '', la, lo, 0, 0, 0, '']
def jrec(i, nj, la, lo, pref, kind, d=.02): return {'id': i, 'n': nj, 'nj': nj, 'ty': nj, 'src': 'MLIT natural park areas (A10)', '_bb': [lo - d, la - d, lo + d, la + d],
                                                    '_r': [H.ring(la, lo, d)], 'code': '', 'dc': '', '_a': {'PREFEC_CD': pref}, '_k0': [kind]}
WP = {'JP': {'JP-1047': wrow('Funagatarenpo Prefectural Nature Park', 'Prefectural Nature Park', 38.4503, 140.631),
             'JP-1146': wrow('Okumusashi Prefectural Nature Park', 'Prefectural Nature Park', 35.9061, 139.19),
             'JP-1709': wrow('Taradake Prefectural Nature Park', 'Prefectural Nature Park', 32.9983, 130.092),
             'JP-1717': wrow('Taradake Prefectural Nature Park', 'Prefectural Nature Park', 32.9563, 130.079),
             'JP-1115': wrow('Kairakuen Prefectural Park', 'Prefectural Park', 36.3725, 140.452),
             'JP-0017': wrow('Chubusangaku National Park', 'National Park', 36.449, 137.622),
             'JP-0114': wrow('Suigo-Tsukuba Quasi-National Park', 'Quasi-National Park', 35.99, 140.474),
             'JP-0999': wrow('Not In The Crosswalk Prefectural Park', 'Prefectural Park', 34.0, 135.0)},
      'NZ': {'NZ-0001': wrow('Abel Tasman National Park', 'National Park', -40.9, 173.0)}}
WR = {'JP': [jrec('a10:04:t:1', '船形連峰県立自然公園', 38.50, 140.631, '04', 'pnp'),          # 0.03 degree past the pin: near, not holding it
             jrec('a10:11:t:1', '奥武蔵県立自然公園', 35.50, 139.19, '11', 'pnp'),            # 0.4 degree away: far from the pin
             jrec('a10:42:t:1', '多良岳県立自然公園', 32.90, 130.20, '42', 'pnp'), jrec('a10:41:t:1', '多良岳県立自然公園', 33.10, 130.20, '41', 'pnp'),
             jrec('a10:08:t:1', '水戸県立自然公園', 36.3725, 140.452, '08', 'pnp', d=.05),      # the natural park around Kairakuen
             jrec('a10:20:t:1', '中部山岳国立公園', 36.449, 137.622, '20', 'np', d=.3),
             jrec('a10:08:t:2', '水郷筑波国定公園', 36.30, 140.10, '08', 'qnp', d=.2),         # a big area, 0.1 degree from the pin
             jrec('a10:27:t:1', 'どこか県立自然公園', 34.0, 135.0, '27', 'pnp')],
      'NZ': [{'id': 1, 'n': 'Abel Tasman National Park', 'ty': '', 'src': 'DOC', '_bb': [172.99, -40.91, 173.01, -40.89], '_r': [H.ring(-40.9, 173.0)], 'code': '', 'dc': ''}]}
EXTRA = {JPX.FILE: CSV.read_bytes()}
W_SRC = (H.SCRIPTS / 'kpc_world_key.py').read_text(encoding='utf-8')
W_OLD = H.strip_hook(W_SRC, '# Nov 12 (KPC owner, 2026-11-12; kpc_jp_crosswalk.py)', 'JPX.apply(')
check('kpc_jp_crosswalk' not in W_OLD and W_SRC.count('kpc_jp_crosswalk') == 2, 'the world builder without this commit = the builder minus its one crosswalk hook')
def cmp(a, b, skip=('data/status/', 'data/research-inbox/')):   # the build's outputs (not its run-status note, not the crosswalk input itself)
    ks = sorted(k for k in set(a) | set(b) if not k.startswith(skip) and not k.startswith('_'))
    return [k for k in ks if a.get(k) != b.get(k)]
CC = ['JP', 'NZ']
rW, oW = H.world_build(CC, WP, WR, {}, src=W_OLD, extra=EXTRA)
rF, oF = H.world_build(CC, WP, WR, {JPX.ENV: None}, extra=EXTRA)
rF2, oF2 = H.world_build(CC, WP, WR, {JPX.ENV: 'off'}, extra=EXTRA)
rN, oN = H.world_build(CC, WP, WR, {JPX.ENV: 'on'}, extra=EXTRA)
rB, oB = H.world_build(CC, WP, WR, {JPX.ENV: 'on'}, extra={JPX.FILE: b'ref,name\nJP-1047,x\n'})
check(all(r.returncode == 0 for r in (rW, rF, rF2, rN, rB)), f'the builder runs offline in every case (exit {[r.returncode for r in (rW, rF, rF2, rN, rB)]})')
check(not cmp(oW, oF) and not cmp(oW, oF2), f'switch OFF (unset or off): every output, JP included, is byte-identical to the builder without this commit ({cmp(oW, oF) + cmp(oW, oF2)})')
check('JP A10 crosswalk::OFF (licence not signed)' in rF.stdout and 'JP A10 crosswalk::OFF (licence not signed)' in rF2.stdout, "the run says 'JP A10 crosswalk: OFF (licence not signed)'")
check(not cmp(oW, oB) and '::warning title=JP A10 crosswalk::ON, but the crosswalk file is not the expected header' in rB.stdout,
      'switch ON with a malformed crosswalk: nothing applied, a warning, the output is as with the switch off')
ch = cmp(oW, oN)
check(ch and all(re.search(r'(/JP(\.json|\.md|/))|world-key/index\.json$', k) for k in ch) and not any('NZ' in k for k in ch),
      f'switch ON: only JP outputs change (NZ byte-identical): {ch}')
check(json.loads(oW['data/world-key/index.json'])['countries']['NZ'] == json.loads(oN['data/world-key/index.json'])['countries']['NZ'], 'index.json: the NZ row is the same')
kO, kN = json.loads(oW['data/world-key/JP.json'])['parks'], json.loads(oN['data/world-key/JP.json'])['parks']
p = kN['JP-1047']
check(not kO['JP-1047']['m'] and [q[0] for q in p['m']] == ['a10:04:t:1'] and p['m'][0][3] == JPX.HOW + '船形連峰県立自然公園',
      'JP-1047: joins 船形連峰県立自然公園 through the crosswalk name (the record is near the pin); without the switch it found nothing')
p = kN['JP-1146']
check(not p['m'] and any(q[0] == 'a10:11:t:1' and 'far from the POTA pin' in q[3] for q in p['c']), 'JP-1146: its record is 0.4 degree from the pin: HELD for a person (check by hand), not joined')
check(all(not kN[r]['m'] and any('two parks, one outline' in q[3] for q in kN[r]['c']) for r in ('JP-1709', 'JP-1717')),
      'JP-1709 / JP-1717: one A10 name for two parks: both HELD (the 41 and 42 records listed for a person), neither joined')
check(kN['JP-1115'] == kO['JP-1115'], 'JP-1115 (a class U facility): exactly as without the switch (never joined to the natural park around it by the crosswalk)')
check(kN['JP-0017'] == kO['JP-0017'] and kO['JP-0017']['m'], 'JP-0017: already joined (the pin is inside 中部山岳): its join is kept as it was')
check([q[0] for q in kN['JP-0114']['m']] == ['a10:08:t:2'] and not kO['JP-0114']['m'], 'JP-0114: a big quasi-national area 0.1 degree from the pin joins by its name (the join check after the builder still holds a new join over 5 km)')
check(kN['JP-0999'] == kO['JP-0999'], 'a JP park not in the crosswalk is unchanged')
check(sorted(r for r in kN if kN[r] != kO[r]) == ['JP-0114', 'JP-1047', 'JP-1146', 'JP-1709', 'JP-1717'], f'switch ON changes exactly those five parks ({sorted(r for r in kN if kN[r] != kO[r])})')
check('ON: 70 rows; joined 2 (JP-0114 JP-1047); held 3' in rN.stdout, 'the run says what the crosswalk did (joined 2, held 3)')
check(all(o['_parkinfo_unchanged'] for o in (oW, oF, oN, oB)), 'the POTA park list files are never changed')

# ---------------------------------------------------------------- 4. hashes and the workflow
cur = {k: KF.rules_hash(k) for k in ('us-key', 'ca-key', 'world-key', 'fers')}
log = (H.ROOT / 'docs/key-rules-change.txt').read_text(encoding='utf-8')
line = next((l for l in log.splitlines() if l.startswith('Japan A10 crosswalk in the world key')), '')
m = re.search(r'then this commit alone ([0-9a-f]{12}) to ([0-9a-f]{12})', line)
check(bool(m) and m.group(2) == PF.changelog_hashes(log, 'world-key')[1] and 'APPROVED, decided_by KPC owner, 2026-11-12' in line and 'FINAL' not in line and 'OFF' in line,
      f'the ledger line: world main -> new (and this commit\'s own step), decided_by KPC owner, 2026-11-12, switch OFF, not claimed FINAL ({m.groups() if m else None})')
check(cur['us-key'] == PF.newest_hash('us-key') and 'Japan A10' not in PF.changelog_hashes(log, 'us-key')[2] and   # Nov 12 CHANGED (stacked after D6 and the overrides split, which move US)
       cur['ca-key'] == PF.newest_hash('ca-key') and 'Japan A10' not in PF.changelog_hashes(log, 'ca-key')[2] and cur['fers'] == PF.newest_hash('fers'),
      'US, CA and fers do not move with this commit')
sc = json.load(open(H.ROOT / KF.SCOPE_FILES['world-key'], encoding='utf-8'))
e = next((c for c in sc['changes'] if c.get('id') == '2026-11-12-jp-a10-crosswalk-off'), {})
check(bool(m) and e.get('from') == m.group(1) and e.get('scope') == 'none', 'scope entry: from the pin-fill world hash, scope none (switch OFF: no country is due for it)')
check('kpc_jp_crosswalk.py' in KF.NOT_RULES and not any('kpc_jp_crosswalk' in f for v in KF.RULE_FILES.values() for f in v), 'kpc_jp_crosswalk.py is listed in NOT_RULES (the builder hook is the rule change)')
base = 'origin/main' if subprocess.run(['git', 'rev-parse', '-q', '--verify', 'origin/main'], cwd=H.ROOT, capture_output=True).returncode == 0 else None
if base:
    check(subprocess.run(['git', 'diff', '--quiet', base, '--', '.github/scripts/kpc_key_facts.py', '.github/scripts/kpc_match.py', '.github/scripts/kpc_key_rules.py'], cwd=H.ROOT).returncode == 0,
          f'kpc_key_facts.py, kpc_match.py and kpc_key_rules.py are as on {base}')
else:
    print('SKIP shared-rule-file diff: no origin/main in this clone')
import yaml   # noqa: E402
txt = (H.ROOT / '.github/workflows/kpc-world-key.yml').read_text(encoding='utf-8'); d = yaml.safe_load(txt)
st = next((s for s in d['jobs']['build']['steps'] if s.get('name') == 'Build (this job\'s countries)'), {})
check(st.get('env', {}).get(JPX.ENV) == "${{ vars.KPC_JP_A10_CROSSWALK || 'off' }}", 'the world build step passes the repo switch KPC_JP_A10_CROSSWALK, default off')
check(JPX.ENV not in (H.ROOT / '.github/workflows/kpc-ca-key.yml').read_text(encoding='utf-8') and JPX.ENV not in (H.ROOT / '.github/workflows/kpc-us-key.yml').read_text(encoding='utf-8'),
      'only the world key workflow knows the switch')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
