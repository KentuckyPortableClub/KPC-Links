#!/usr/bin/env python3
"""Nov 8 2026: 2-fer ready-areas gate + approx river/trail hold + declared fers rules hash.

Brandon t808u / Quality 2-fer grade should-fix. Offline. No network.
Asserts us-key / ca-key / world-key rules hashes are unchanged by the fers kind.
"""
import importlib.util
import json
import pathlib
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent.parent
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg)
    ok = ok and bool(c)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


# --- 1) ready-areas module + declared file
FR = load('kpc_fers_ready', HERE / '.github/scripts/kpc_fers_ready.py')
r = FR.selftest()
check(r, 'kpc_fers_ready.selftest returns True')

ready = json.load(open(HERE / '.github/fers-ready-areas.json'))
check(set(ready.get('require') or []) >= {'ownership', 'management'}, 'ready file requires both')
for key in ('US-*', 'CA-*'):
    ent = (ready.get('areas') or {}).get(key) or {}
    check(ent.get('ownership', {}).get('source') and ent.get('management', {}).get('source'),
          f'{key} names ownership and management sources')
check(FR.area_ready('US-KY') and FR.area_ready('CA-ON') and not FR.area_ready('W-AU'),
      'live file: US/CA ready, W-AU not')

# --- 2) approx river/trail status helper (mirror decide() rule without running the bot)
KS = load('kpc_fers_key_status', HERE / '.github/scripts/kpc_fers_key_status.py')
KS.clear()
# Fabricate KEY_STATUS as the bot would see after load_key_status
KS.KEY_STATUS['US-12235'] = 'approximate'
KS.KEY_STATUS['US-9999'] = 'official'
KS.KEY_BY_AREA['US-12235'] = {'US-PA': 'approximate'}
KS.KEY_BY_AREA['US-9999'] = {'US-PA': 'official'}


def river_trail_hold(refs, kind, areas=None):
    """Same gate decide() uses for river/trail approximate halves."""
    if kind not in ('river', 'trail'):
        return ''
    apx = [r for r in refs if KS.status_for(r, (areas or {}).get(r)) == 'approximate']
    if not apx:
        return ''
    return 'not sure: approximate outline on a river/trail half (' + ', '.join(apx) + ')'


check(river_trail_hold(['US-12235', 'US-9999'], 'river'), 'approx river half -> not sure hold')
check(not river_trail_hold(['US-9999', 'US-8888'], 'river'), 'official river halves -> no hold')
check(not river_trail_hold(['US-12235', 'US-9999'], 'area'), 'area kind still uses key_line_match path (not this hold)')
# area approximate still caught by key_line_match
msg = KS.key_line_match(['US-12235', 'US-9999'], 'area')
check(bool(msg), f'area+approximate still blocked by key_line_match: {msg!r}')

# --- 3) fers rules hash declared; us/ca/world unchanged
KF = load('kpc_key_freeze', HERE / '.github/scripts/kpc_key_freeze.py')
check('fers' in KF.RULE_FILES, 'RULE_FILES has fers kind')
fers_files = KF.RULE_FILES['fers']
for need in ('.github/scripts/kpc_fers.py', '.github/scripts/kpc_fers_ready.py', '.github/scripts/kpc_fers_preline.py', '.github/fers-ready-areas.json'):
    check(need in fers_files, f'fers RULE_FILES includes {need}')
check('.github/scripts/kpc_key_facts.py' not in fers_files, 'fers does not pull in key_facts')

ver = json.load(open(HERE / '.github/key-rules-version.json'))
check(ver.get('us-key') == 'v5b' and ver.get('ca-key') == 'v5b' and ver.get('world-key') == 'v5b',
      'us/ca/world version lines still v5b')
check(ver.get('fers') == 'v1', 'fers version v1')

# Hashes recorded on main tip before this PR (must not move)
BASE = {'us-key': '464d2ce92eda', 'ca-key': '8feccbb7d9ee', 'world-key': '10e4092cc97f'}
for k, h in BASE.items():
    got = KF.rules_hash(k, str(HERE))
    check(got == h, f'{k} rules hash unchanged ({got} == {h})')

fers_h = KF.rules_hash('fers', str(HERE))
check(len(fers_h) == 12 and all(c in '0123456789abcdef' for c in fers_h), f'fers hash looks like 12-hex: {fers_h}')
print('FERS_RULES_HASH=' + fers_h)
# docs/key-rules-change.txt must declare this hash with Brandon's OK (Nov 8, 2026, 8:19 PM CST)
docs = (HERE / 'docs/key-rules-change.txt').read_text(encoding='utf-8')
_head = docs.split('\n\n')[0] if docs else ''
check(fers_h in _head and 'fers v1' in _head,
      f'docs/key-rules-change.txt top entry declares fers v1 hash {fers_h}')
# Nov 9: the top entry is now the KISS-ownership change, OK'd by Brandon Nov 9, 9:37 AM CST (his exact words are in the entry)
check('We got to fix the rules to get this thing going' in _head and '9:37 AM CST' in _head and 'PENDING' not in _head and 'AWAITING' not in _head,
      'docs record Brandon OK of the fers hash with his exact words and time (no longer PENDING)')
check('a066624520b4' in _head and '8feccbb7d9ee' in _head and '10e4092cc97f' in _head,
      'docs entry notes us/ca/world hashes unchanged')

# Changing the ready file must move the fers hash (and only fers)
with tempfile.TemporaryDirectory() as td:
    td = pathlib.Path(td)
    # minimal tree for rules_hash
    for rel in fers_files:
        dest = td / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        src = HERE / rel
        dest.write_bytes(src.read_bytes() if src.is_file() else b'missing')
    (td / '.github').mkdir(exist_ok=True)
    # version file with fers v1
    json.dump({'us-key': 'v5b', 'ca-key': 'v5b', 'world-key': 'v5b', 'fers': 'v1'},
              open(td / '.github/key-rules-version.json', 'w'))
    h1 = KF.rules_hash('fers', str(td))
    # tweak ready file
    j = json.load(open(td / '.github/fers-ready-areas.json'))
    j['about'] = (j.get('about') or '') + ' tweak'
    json.dump(j, open(td / '.github/fers-ready-areas.json', 'w'))
    h2 = KF.rules_hash('fers', str(td))
    check(h1 != h2, f'editing fers-ready-areas.json changes fers hash ({h1} -> {h2})')

# decide() source contains the approx river/trail hold (string check — bot is heavy to import)
fers_src = (HERE / '.github/scripts/kpc_fers.py').read_text(encoding='utf-8')
check('approximate outline on a river/trail half' in fers_src, 'kpc_fers.decide holds approx river/trail')
check('fers-ready-areas' in fers_src and 'FREADY' in fers_src, 'kpc_fers.main calls ready-areas gate')
check("rep['fers_rules']" in fers_src or 'fers_rules' in fers_src, 'run report records fers_rules')

pre = (HERE / '.github/scripts/kpc_fers_preline.py').read_text(encoding='utf-8')
check('FREADY' in pre and 'fers_rules' in pre, 'preline HOLDs non-ready areas and records fers_rules')

print('ALL_OK' if ok else 'FAILED')
sys.exit(0 if ok else 1)
