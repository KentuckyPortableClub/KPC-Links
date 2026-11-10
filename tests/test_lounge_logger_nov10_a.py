#!/usr/bin/env python3
"""Nov 10: Hunters Lounge dock: park prefix carry-over (KPCHuntRefFix + refList), delete confirm on log entries,
voice keyer button only with a CAT radio, and #dkForm keeps every field id on both pages."""
import pathlib, re, subprocess, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]
js = (ROOT / 'kpc-hunt.js').read_text(encoding='utf-8')
ok = True
def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)

# 1: the pure helper, run with node
m = re.search(r"  const refFix = v => .*\n", js)
check(bool(m), 'refFix helper present')
check('window.KPCHuntRefFix = refFix' in js, 'exposed as window.KPCHuntRefFix')
check('refFix(v).toUpperCase().split(' in js, 'refList uses refFix')
nr = re.search(r"  const nref = r => \{.*?\n  \};\n", js, re.S)
harness = nr.group(0) + m.group(0) + """
const t = (a, b) => { if (refFix(a) !== b) { console.log('BAD', JSON.stringify(a), '->', JSON.stringify(refFix(a))); process.exit(1); } };
t('US-1234, 5678', 'US-1234, US-5678'); t('us-1234 5678 99999', 'US-1234 US-5678 US-99999');
t('CA-0456,1111', 'CA-0456,CA-1111'); t('US-1234, CA-0001', 'US-1234, CA-0001');
t('5678', '5678'); t('', ''); t('US-1234', 'US-1234'); t('K-1234, 5678', 'K-1234, US-5678');
t('US-1234, US-', 'US-1234, US-'); t('US-1234, 56', 'US-1234, 56');
console.log('ok');
"""
r = subprocess.run(['node', '-e', harness], capture_output=True, text=True)
check(r.stdout.strip() == 'ok', 'KPCHuntRefFix cases (node) ' + (r.stdout + r.stderr).strip()[:120])
check('refBad = (L, el)' in js and 'Not a park or summit ref' in js, 'refBad message kept')
check("el.value = body + (e.data === ','" in js and "e.inputType !== 'insertText'" in js, 'prefix pre-fill only on typed separator (not on backspace)')

# 5: delete confirm beside the handler
i = js.index("closest('[data-qd]')")
seg = js[i:i + 600]
check("confirm(`Delete ${Q.q[i].call} ${fmtD(Q.q[i].d)} ${fmtT(Q.q[i].tm)}? This cannot be undone.`)" in seg, 'delete asks confirm before splice')
check(seg.index('confirm(') < seg.index('Q.q.splice'), 'confirm comes before the delete')
check('UNDO' in js and 'Deleted ${x.call}' in seg, 'undo toast kept')

# 8: voice keyer
check("'.dk-top [data-vk-open]'" in js and 'window.KPCCat && KPCCat.connected()' in js and 'KPCCat.onStatus(vkBtn)' in js, 'voice keyer toggled by KPCCat')
check('b.hidden = !on' in js, 'uses .hidden; hidden when KPCCat is missing')

# the dock form keeps every field
ids = ['dFreq', 'dMode', 'dBand', 'dRef', 'dName', 'dCall', 'dRs', 'dRr', 'dSt', 'dNote', 'dkClr', 'dkLog']
for pg in ['kpc-hunters.html', 'kpc-hunt.html']:
    h = (ROOT / pg).read_text(encoding='utf-8')
    f = re.search(r'<form[^>]*id="dkForm".*?</form>', h, re.S)
    check(bool(f), pg + ' has #dkForm')
    for x in ids:
        check(bool(f) and f'id="{x}"' in f.group(0), f'{pg} #dkForm keeps #{x}')
    check('data-vk-open' in h, pg + ' keeps the voice keyer button in the HTML')
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
