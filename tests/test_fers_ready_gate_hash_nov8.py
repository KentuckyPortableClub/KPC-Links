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


def river_trail_approx(refs, kind, areas=None):
    """Approximate river/trail halves are an approximate 2-fer, not a hold."""
    if kind not in ('river', 'trail'):
        return []
    return [r for r in refs if KS.status_for(r, (areas or {}).get(r)) == 'approximate']


check(river_trail_approx(['US-12235', 'US-9999'], 'river') == ['US-12235'], 'approx river half is tagged, not held')
check(not river_trail_approx(['US-9999', 'US-8888'], 'river'), 'official river halves -> not approximate')
check(not river_trail_approx(['US-12235', 'US-9999'], 'area'), 'area kind is tagged in decide, not this helper')
# area approximate is allowed as an approximate 2-fer (not blocked)
msg = KS.key_line_match(['US-12235', 'US-9999'], 'area')
check(msg == '', f'area+approximate allowed as approximate 2-fer: {msg!r}')

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

# Approved hashes after merging main (#109) into this PR: US bbdcc89f8120 (from f489a836894f); fers c2456edee62e; CA and world unchanged
sys.path.insert(0, str(HERE / '.github/scripts'))
import kpc_preflight as PF
for k in ('us-key', 'ca-key', 'world-key'):
    got, h = KF.rules_hash(k, str(HERE)), PF.newest_hash(k)
    check(got == h and bool(h), f'{k} rules hash equals the newest one in docs/key-rules-change.txt ({got} == {h})')

fers_h = KF.rules_hash('fers', str(HERE))
check(fers_h == PF.newest_hash('fers') and bool(fers_h), f'fers rules hash equals the newest one in docs/key-rules-change.txt ({fers_h})')
print('FERS_RULES_HASH=' + fers_h)
docs = (HERE / 'docs/key-rules-change.txt').read_text(encoding='utf-8')
# Ledger is newest-first: the Nov 11 FR-14979 world-override declaration (no hash move), then the Nov 11 overlap finder / 25 m entry (fers), the Nov 11 world layer fall back entry, the Nov 11 FL box east edge entry, the Nov 10 layer-count entry, the Nov 10 master-step follow-up, the Nov 10 master-step entry, the Nov 10 refill entry, #109 (5:54 AM CST), then #108 (5:22 AM CST). Read the top ten entries so the new top declaration does not push the Nov 10 fers-v1 / hash lines out of the window.
# KPC owner, 2026-11-11 (job 6): + the French PatriNat world entry and the three French overrides entry on top: the top twelve.
# Nov 12 (rebased onto main with #154): + the Nov 11 Pacific area boxes entry (fers) under the French entries: the top thirteen.
# Nov 12 (rebased onto main with #157): + the picture-trace entry (fers 77b31e3427a4 -> cef323de4c9a) under the French entries: the top fourteen.
# Nov 12 (KPC owner, 2026-11-12; D6 tables out): + the D6 entry (US / world) on top: the top fifteen.
# Nov 12 (KPC-Links #151 readers, E4): + the US overrides split entry (US hash move) on top: the top fifteen.
# KPC owner, 2026-11-12 (official pin fills, CA / world): + that entry on top: (stacked set: the window is the top twenty).
# KPC owner, 2026-11-12 (Japan A10 crosswalk, world, switch off): + that entry on top: (inside the same window).
_head = '\n\n'.join([p for p in docs.split('\n\n') if p.strip()][:20])
check(fers_h in _head and 'fers v1' in _head,
      f'docs/key-rules-change.txt Nov 10 entries declare fers v1 hash {fers_h}')
# Public changelog keeps hashes and dates only (no quotes, no ids)
check(f'{fers_h} (FINAL' in _head and 'APPROVED' in _head and '7:52 PM CST' in _head and 'PENDING' not in _head and '"' not in docs,
      "docs record the approval (hash + date) next to the final fers hash, no quoted messages")
check('bbdcc89f8120' in _head and 'f489a836894f' in _head and '570b09c3cb52' in _head and '6444287722b9' in _head,
      'docs entries note the US hash move and CA/world hashes unchanged')

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
check('approximate 2-fer' in fers_src and 'APX_NOTE' in fers_src, 'kpc_fers tags approximate 2-fers instead of holding them')
check('approximate outline on a river/trail half' not in fers_src, 'decide() does not hold a river/trail half beside an approximate outline (tagged approximate)')
check('fers-ready-areas' in fers_src and 'FREADY' in fers_src, 'kpc_fers.main calls ready-areas gate')
check("rep['fers_rules']" in fers_src or 'fers_rules' in fers_src, 'run report records fers_rules')

pre = (HERE / '.github/scripts/kpc_fers_preline.py').read_text(encoding='utf-8')
check('FREADY' in pre and 'fers_rules' in pre, 'preline HOLDs non-ready areas and records fers_rules')

print('ALL_OK' if ok else 'FAILED')
sys.exit(0 if ok else 1)
