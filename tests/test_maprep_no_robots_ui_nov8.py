#!/usr/bin/env python3
"""Nov 8 (Brandon t777u): Mapping Rep pages never show robots.txt / disallow / skipped-blocked notes. Blocked layers stay silent."""
import json, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]; ok = True
def check(c, m):
    global ok; print(('PASS ' if c else 'FAIL ') + m); ok = ok and bool(c)
rx = re.compile(r'robots\.txt|robots disallows|robots-blocked|services\*\.arcgis\.com = disallow', re.I)
for f in ('kpc-maprep.html', 'kpc-maprep-reps.html', '.claude/build/maprep/main.html', 'kpc-maprep-research.js', 'kpc-maprep.js'):
    t = (ROOT / f).read_text(encoding='utf-8')
    # meta name="robots" is fine (HTML noindex); strip it before the check
    t2 = re.sub(r'<meta name="robots"[^>]*>', '', t)
    # code comments that are not rendered: allow in .js only if not assigned to UI strings — still ban the phrases Brandon named
    hits = rx.findall(t2)
    check(not hits, f + ': no rep-facing robots wording ' + str(hits[:3]))
reg = json.loads((ROOT / 'data/maprep-state-layers.json').read_text(encoding='utf-8'))
blob = json.dumps(reg)
check(not rx.search(blob), 'maprep-state-layers.json has no robots wording for the page')
js = (ROOT / 'kpc-maprep-research.js').read_text(encoding='utf-8')
check('skipped layers stay silent' in js and 'S.skipped.length + \' skipped\'' not in js, 'status panel does not say N skipped')
check("if (S.skipped.length) stLine" not in js, 'no skipped why line on the status panel')
for f in ('kpc-maprep.html', 'kpc-maprep-reps.html', '.claude/build/maprep/main.html'):
    check('kpc-maprep-research.js?v=20261111rule' in (ROOT / f).read_text(encoding='utf-8'), f + ': script version')
sys.exit(0 if ok else 1)
