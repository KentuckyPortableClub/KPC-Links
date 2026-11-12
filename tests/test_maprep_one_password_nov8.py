"""One password for the Mapping Rep Tool Box (Brandon Nov 8 3:39 PM CST, t759u). Hashes only, never the password."""
import re, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
bad = 0
def check(ok, what):
    global bad
    print(('PASS ' if ok else 'FAIL ') + what); bad += (not ok)
gate = (ROOT / 'kpc-maprep-gate.js').read_text(encoding='utf-8'); js = (ROOT / 'kpc-maprep.js').read_text(encoding='utf-8')
rh = re.search(r"RH = '([0-9a-f]{64})'", gate).group(1)
check(f"'{rh}'" in js and 'const GOOD = [RH, HASH]' in js, "the door's hash sha256('kpc-maprep:'+pw) is accepted by the inner lock")
check("(window.KPCRepGate && window.KPCRepGate.hash) ||" in js, 'inner lock reads the door hash when the door is on the page')
check('ok = !!(window.KPCRepGate && window.KPCRepGate.ok())' in js, 'door already passed = inner lock open (no second card)')
check("localStorage.getItem('kpcMapRep') === RH" in js and "GOOD.includes(localStorage.getItem('kpcMrOK'))" in js, 'either remembered key opens it')
check("GOOD.includes(h)" in js and "localStorage.setItem('kpcMapRep', RH)" in js, 'typing the door password in the inner card works and opens both')
check("let ok = !!$('mrPublic');" in js, 'the public Suggest page still needs no password')
for f in ('kpc-maprep.html', 'kpc-maprep-reps.html', '.claude/build/maprep/main.html'):
    h = (ROOT / f).read_text(encoding='utf-8'); check('kpc-maprep.js?v=20261111rule' in h, f'{f}: new script version (phones drop the cached old lock)')
check(re.search(r'kpc-maprep-gate\.js', (ROOT / 'kpc-maprep-reps.html').read_text(encoding='utf-8')) is not None, 'reps page keeps the door')
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
