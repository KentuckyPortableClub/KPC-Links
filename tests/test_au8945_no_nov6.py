#!/usr/bin/env python3
"""Nov 6 improvements v2.1 (Quality v2 grade MUST-ADD): world overrides 'no' for AU-8945 Scarborough State Beach against QLD Places
FeatureServer/11 record 805 (official name Godwin Beach, 11.7 km from the pin), verify-then-fix. The world builder's 'no' matches a
record id or a name (kpc_world_key.py rule 21), so record 805 never joins AU-8945 on any build path. Data only: no rules hash change."""
import json, pathlib, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = True
def check(msg, cond):
    global ok
    ok &= bool(cond); print(('PASS ' if cond else 'FAIL ') + msg)
e = json.load(open(ROOT / 'data/world-key/overrides.json', encoding='utf-8'))['parks'].get('AU-8945') or {}
check('AU-8945 no = ["805", "Godwin Beach", "Scarborough Beach"]', e.get('no') == ['805', 'Godwin Beach', 'Scarborough Beach'])
check("decided_by 'Brandon standing rule 2026-11-05 verify-then-fix'", e.get('decided_by') == 'Brandon standing rule 2026-11-05 verify-then-fix')
check('the why carries the evidence (record 805 = Godwin Beach, 11.7 km)', all(w in e.get('why', '') for w in ('805', 'Godwin Beach', '11.7 km')))
check('no join list for AU-8945 (nothing forced in)', not e.get('join'))
src = (ROOT / '.github/scripts/kpc_world_key.py').read_text()
check("the builder matches a 'no' by record id or name (rule 21)", "_isno = lambda rid, rn: low(str(rid)) in no or low(rn) in no" in src)
r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_key_freeze.py'), 'rules', 'world-key'], capture_output=True, text=True, cwd=ROOT)
# Nov 6 big patch (Links #44): kpc_world_key.py (a rule file) gained the tract side-file call + KPC_WORLD_ACRES (default off), so
# the world rules hash moved 463bcf9e8e3f -> 1b50faf1dfe8 on purpose (a full world rebuild is due on merge). The point of this check
# stays: overrides.json is data, so the hash equals the hash of the rule files alone.
# Nov 7 world rebuild (B1 B2 B3 B4 B6, world-failed-diagnosis.md section 7; Brandon OK'd the world hash move): kpc_world_key.py
# changed on purpose, so the world rules hash moved 1b50faf1dfe8 -> 6a5969a25d2c. US and CA stay; this check still pins all three.
check('overrides.json is data, not a rules file: world rules hash stays 10e4092cc97f (1b50faf1dfe8 before the Nov 7 world rebuild, 463bcf9e8e3f before Links #44)', r.stdout.strip() == '10e4092cc97f')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
