#!/usr/bin/env python3
"""Nov 11 2026 (KPC owner): trail join guard (job 4). Offline, no network, no git needed.
- The 31 parks that already grade official line (trail-31 sheet, Nov 11): every key entry (data/us-key/US-XX.json,
  data/ca-key/CA-XX.json) and every overrides.json entry they have is byte-identical to Links 11f908d9 (sha256 of the entry's
  canonical JSON, taken at that base). A key run that re-grades one of them makes this fail on purpose: look before you accept it.
- The trail / river 2-fer minimum stretch is still 25 m (kpc_fers.STRETCH, read from the source) and the four rules hashes are
  the ones the handoff names (US 46ef34a04ab0, CA 4b4176190334, world 9358c2ede2d5, fers aa7561256260): no trail join moved one.
- No trail line geometry lives in KPC-Links: data/trails/ stays git-ignored (KPC-Data holds the one true copy, laid over at build
  time by kpc_overlay.sh) and no tracked file is a trail line copy (data/trails/* or *trail-lines*.geojson.gz)."""
import hashlib, json, pathlib, re, subprocess, sys
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


def fp(x):
    return hashlib.sha256(json.dumps(x, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()[:16]


# sha256[:16] of each key entry at Links 11f908d9 (ref -> {key file: fingerprint})
KEY31 = {
    'US-0642': {'data/us-key/US-AL.json': '87f87bf649a28d19', 'data/us-key/US-MS.json': '7bc3c305f9e66655', 'data/us-key/US-TN.json': 'fd724199f8b78ec2'},
    'US-10426': {'data/us-key/US-AR.json': 'bdca81e4687fa16d'},
    'US-10508': {'data/us-key/US-AR.json': '78920a3434e42681'},
    'US-13622': {'data/us-key/US-AR.json': '2fd04a76150e3a49'},
    'US-13623': {'data/us-key/US-AR.json': '6701058720680b99'},
    'US-9681': {'data/us-key/US-AR.json': '6b525764572084e7'},
    'US-0197': {'data/us-key/US-CA.json': '03f355e27ad353d0'},
    'US-5749': {'data/us-key/US-CO.json': '6a81bfebd2230ed7', 'data/us-key/US-UT.json': 'cea67607a9cd45b3'},
    'US-6281': {'data/us-key/US-FL.json': '53e55e0318a0966f'},
    'US-9758': {'data/us-key/US-GA.json': '315c11b6214fba1f', 'data/us-key/US-NC.json': '2e1c46dd3ab73797', 'data/us-key/US-SC.json': '23c9d5672f28fc6f'},
    'US-3424': {'data/us-key/US-ID.json': 'e01e98a2718870b2', 'data/us-key/US-MT.json': 'e01e98a2718870b2', 'data/us-key/US-OR.json': 'e01e98a2718870b2', 'data/us-key/US-WA.json': 'e01e98a2718870b2'},
    'US-7973': {'data/us-key/US-MD.json': 'ccbff1e9c86ddc93'},
    'US-12786': {'data/us-key/US-MI.json': '00454da339925eab'},
    'US-12794': {'data/us-key/US-MI.json': '2d6d069961ef480a'},
    'US-12796': {'data/us-key/US-MI.json': 'd60cbc13ae6a4b8a'},
    'US-10398': {'data/us-key/US-NC.json': '5ad9a500d73eccbe'},
    'US-13626': {'data/us-key/US-NH.json': '7e26792ddfce1ea1'},
    'US-0684': {'data/us-key/US-NJ.json': 'b4f0740abb229770', 'data/us-key/US-PA.json': 'b4f0740abb229770'},
    'US-11815': {'data/us-key/US-NM.json': 'c45de80b7732b3a5'},
    'US-13206': {'data/us-key/US-NV.json': '03d914d0fdc6b604'},
    'US-13214': {'data/us-key/US-NV.json': '103677e99589bf38'},
    'US-12959': {'data/us-key/US-OR.json': '8ba948fa4a82c0cd'},
    'US-9203': {'data/us-key/US-SC.json': 'b7982829761cf84c'},
    'US-11004': {'data/us-key/US-UT.json': '7be960ae0d048d31'},
    'US-11176': {'data/us-key/US-UT.json': '3bc796eabcaeee04'},
    'US-11661': {'data/us-key/US-UT.json': 'c0d72d84fc397de8'},
    'US-11730': {'data/us-key/US-UT.json': '917f996391375dc5'},
    'US-5841': {'data/us-key/US-UT.json': 'bf844d99253af5e8'},
    'US-5935': {'data/us-key/US-UT.json': '7c3e75c4504c2b08'},
    'US-5993': {'data/us-key/US-UT.json': '186f2802d09aa4d4'},
    'US-10877': {'data/us-key/US-WY.json': '50ebf6fa127f0fb8'}}
# the overrides.json entries the 31 had at 11f908d9 (ref -> (file, fingerprint)); the other 21 had none
OV31 = {
    'US-10508': ('data/us-key/overrides.json', '0e7726ddcb766028'),
    'US-0197': ('data/us-key/overrides.json', '3136ea5a9f35b4d8'),
    'US-6281': ('data/us-key/overrides.json', '7229ba1d6b15c561'),
    'US-9758': ('data/us-key/overrides.json', '021b72e54673993c'),
    'US-12786': ('data/us-key/overrides.json', '700f701f626122fe'),
    'US-12794': ('data/us-key/overrides.json', '028e0a9c0027441a'),
    'US-12796': ('data/us-key/overrides.json', 'ff7fb4b073e8721c'),
    'US-0684': ('data/us-key/overrides.json', '1ff9d6e85e77cb7f'),
    'US-0642': ('data/us-key/overrides.json', 'c1aa4dc9277fbc1e'),
    'US-11176': ('data/us-key/overrides.json', '8500603623b469c7')}
check(len(KEY31) == 31, f'31 official-line parks pinned (got {len(KEY31)})')
cache = {}


def parks(rel):
    if rel not in cache: cache[rel] = json.load(open(HERE / rel, encoding='utf-8')).get('parks') or {}
    return cache[rel]


bad = []
for ref, files in KEY31.items():
    for rel, h in files.items():
        p = parks(rel).get(ref)
        if p is None or fp(p) != h: bad.append(f'{ref} in {rel}')
check(not bad, f"the 31 official-line parks' key entries are byte-identical to 11f908d9 ({len(bad)} changed: {', '.join(bad[:8])})")
g = [ref for ref, files in KEY31.items() if not any((parks(rel).get(ref) or {}).get('g') == 'official' for rel in files)]
check(not g, f'each of the 31 still grades official in at least one key file (not: {g})')
badov = [ref for ref, (rel, h) in OV31.items() if fp(parks(rel).get(ref)) != h]
newov = [ref for ref in KEY31 if ref not in OV31 and any(ref in parks(f) for f in ('data/us-key/overrides.json', 'data/ca-key/overrides.json'))]
check(not badov and not newov, f'the overrides of the 31 are unchanged (changed: {badov}; new: {newov})')

src = (HERE / '.github/scripts/kpc_fers.py').read_text(encoding='utf-8')
m = re.search(r'^STRETCH = ([0-9.]+)\s*$', src, re.M)
check(m and float(m.group(1)) == 25.0, f'the trail / river 2-fer stretch is still 25 m (STRETCH = {m.group(1) if m else None})')
import kpc_key_freeze as F
got = {k: F.rules_hash(k) for k in ('us-key', 'ca-key', 'world-key', 'fers')}
want = {'us-key': '46ef34a04ab0', 'ca-key': '4b4176190334', 'world-key': '9358c2ede2d5', 'fers': 'cef323de4c9a'}
check(got == want, f'rules hashes unchanged (got {got})')

gi = (HERE / '.gitignore').read_text(encoding='utf-8').split('\n')
check('data/trails/' in [x.strip() for x in gi], '.gitignore keeps data/trails/ out of KPC-Links (the line files stay in KPC-Data)')
try:
    tracked = subprocess.run(['git', '-C', str(HERE), 'ls-files'], capture_output=True, text=True, timeout=60).stdout.split('\n')
except Exception:  # noqa: BLE001  (no git here: the .gitignore check above still stands)
    tracked = []
lines = [t for t in tracked if t.startswith('data/trails/') or re.search(r'trail-lines/.*\.geojson(\.gz)?$', t)]
check(not lines, f'no trail line copy is tracked in KPC-Links ({lines[:5]})')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
