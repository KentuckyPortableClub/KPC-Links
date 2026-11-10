"""Whole-state search must not stall on the last step (Brandon Nov 8 3:50 PM CST, t760u: "Iowa gets stuck on last step").
Cause: the last step looked up each nearby POTA park's key outline LIVE, one park at a time, through every agency layer
(about 400 requests for Iowa, no time limit). Now: one batched load of the key outlines, then all comparisons on the device."""
import re, sys, json, subprocess, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
bad = 0
def check(ok, what):
    global bad
    print(('PASS ' if ok else 'FAIL ') + what); bad += (not ok)
js = (ROOT / 'kpc-maprep-research.js').read_text(encoding='utf-8')
check('async function prefetchOutlines' in js, 'key outlines are loaded up front in batches')
check(re.search(r"Loading the key outlines near these places \(one batch\)", js) is not None, 'the status shows the batch load as its own step')
check('(on this device)' in js, 'the last step says the comparison is on the device (not a live lookup)')
check(js.count('await prefetchOutlines(places, code, ctx') == 2, 'both Search all and Check all use the batch')
check('Math.min(4, total)' in js, 'at most 4 requests at once')
check(re.search(r'within\(checkPlace\(p, code, ctx\), 15000', js) is not None, 'each place has a time limit')
check(re.search(r'within\(keyFile\(code\), 30000, null\), within\(pins\(\), 30000, \[\]\)', js) is not None, 'answer key and pins have a time limit')
check(re.search(r"outlineP\[ref\] = within\(", js) is not None, 'a single live outline has a time limit')
check('await tick()' in js, 'the phone gets to draw between places')
check("id=\"mrRsRetry\">TRY AGAIN" in js, 'error path keeps TRY AGAIN')
check('usKeyLayers: () => layers()' in (ROOT / 'kpc-bounds.js').read_text(encoding='utf-8'), 'agency layer list shared from kpc-bounds')
for f in ('kpc-maprep.html', 'kpc-maprep-reps.html', '.claude/build/maprep/main.html'):
    h = (ROOT / f).read_text(encoding='utf-8')
    _v = re.search(r'kpc-maprep-research\.js\?v=(\w+)', h)   # any version from 20261108s on
    check(bool(_v) and _v.group(1) >= '20261108s' and 'kpc-bounds.js?v=20261109am2' in h, f + ': new script versions')
node = r"""
global.window = {}; const R = require(%s);
(async () => {
  const t = Date.now(); const v = await R.within(new Promise(() => {}), 200, 'fb');
  const e = await R.within(Promise.reject(new Error('x')), 200, 'fb2');
  const ok = await R.within(Promise.resolve(7), 200, 0);
  console.log(JSON.stringify([v, e, ok, Date.now() - t < 1500]));
})();
""" % json.dumps(str(ROOT / 'kpc-maprep-research.js'))
try:
    out = subprocess.run(['node', '-e', node], capture_output=True, text=True, timeout=20).stdout.strip().splitlines()[-1]
    check(json.loads(out) == ['fb', 'fb2', 7, True], 'a wait that never answers gives up on time; an error falls back')
except Exception as ex:
    check(False, 'node time-limit check ran (' + str(ex) + ')')
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
