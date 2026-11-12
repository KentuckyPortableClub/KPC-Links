#!/usr/bin/env python3
"""Soft locks with a slower hash (Nov 11 2026, owner). Offline, no network.
 1. node runs each lock's own code on a made-up password: right password = PBKDF2-SHA256(hex SHA-256(prefix + password), the
    lock's salt, 200,000 rounds, 32 bytes) as done by node's crypto; a wrong password does not match (tests/soft_locks_nov11.js).
 2. No fast (single SHA-256) lock hash is left: every 64-hex string in a root .js / .html is one of the known slow values.
 3. The gate files say plainly that this is a soft lock and private data must not be in the public repo."""
import os, pathlib, re, subprocess, sys
HERE = pathlib.Path(os.environ.get('LINKS') or pathlib.Path(__file__).resolve().parent.parent)
fails = 0
def ok(c, m):
    global fails
    print(('PASS ' if c else 'FAIL ') + m)
    if not c: fails += 1
SLOW = {'ed00a12021b4460be189b4120e93d5f740408d2f769e108d332dcc4aa528ca61': 'member (PBKDF2 since Oct 27)',
        'dba69f2b5025da744d35d1c9136204ac81c4b1f23fa16a05c6cc63899cf23dab': 'VIP', 'd5a9320d7439f2c39d1edee093a44a78b395d6ac854a4f4f35e20cfd137c0ac6': 'beta',
        '45fefe8e34282a0ca0864229046044d4e47988cb79b054a2cdadf4c4213574b3': 'room', 'f9f2be57c06d88fe6d03a3fe59b7b3b9394be1a63993d74a2ddd65a5b1bf2c80': 'map rep',
        '8434d195558b7868f86ac72277738c2059573829795ef84d4a87b2fddb46bf0b': 'map rep inner (older)', 'd418e23294fd467806712474b9ef8e208d4b0c2d92804da0881c5dd58557c158': 'legacy members'}
try:
    r = subprocess.run(['node', str(HERE / 'tests/soft_locks_nov11.js'), str(HERE)], capture_output=True, text=True, timeout=300)
    print(r.stdout.rstrip()); ok(r.returncode == 0 and 'ALL PASSED' in r.stdout, 'node: every lock unlocks with the right password only' + (' ' + r.stderr[-200:] if r.returncode else ''))
except FileNotFoundError:
    print('SKIP node is not installed here'); 
other = []
for f in sorted(os.listdir(HERE)):
    if not re.search(r'\.(js|html?)$', f): continue
    t = (HERE / f).read_text(encoding='utf-8', errors='replace')
    for m in re.finditer(r'''['"`]([0-9a-f]{64})['"`]''', t):
        if m.group(1) not in SLOW: other.append('%s:%d' % (f, t.count('\n', 0, m.start()) + 1))
ok(not other, 'no fast lock hash left in root JS / HTML (only the slow values): ' + (', '.join(other[:5]) or 'none'))
for f in ('kpc-gate.js', 'kpc-vip.js', 'kpc-maprep-gate.js'):
    t = (HERE / f).read_text(encoding='utf-8')
    ok(re.search(r'soft lock', t, re.I) and re.search(r'private\s+data\s+must\s+(never|not)\s+(be\s+put\s+|be\s+)?in\s+(this|the)\s+public\s+repo', t, re.I), f + ': says it is a soft lock and private data must not be in the public repo')
print('SOME FAILED' if fails else 'ALL PASSED')
sys.exit(1 if fails else 0)
