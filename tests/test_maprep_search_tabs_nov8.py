#!/usr/bin/env python3
"""Nov 8 (Brandon 1:08 PM CST): the three research searches become ONE panel with tabs (whole state | near a spot | by name),
one SEARCH button, and a live status panel (steps, bar, elapsed time, slow note, error + TRY AGAIN) the page jumps to."""
import pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[1]; bad = 0
def check(ok, msg):
    global bad; bad += not ok; print(('PASS ' if ok else 'FAIL ') + msg)
for f in ('kpc-maprep-reps.html', 'kpc-maprep.html', '.claude/build/maprep/main.html'):
    h = (ROOT / f).read_text(encoding='utf-8'); sec = h[h.find('id="mrResearch"'):h.find('id="mrCheckCard"')]
    check(all(f'data-rstab="{k}"' in sec for k in ('state', 'pin', 'name')) and sec.count('role="tab"') == 3, f'{f}: three tabs')
    check(sec.count('type="submit"') == 1 and 'id="mrRsGo"' in sec and '>SEARCH<' in sec, f'{f}: one SEARCH button')
    check(all(f'id="{i}"' in sec for i in ('mrRsFind', 'mrRsNear', 'mrRsTest', 'mrRsPlace', 'mrRsQ', 'mrRsMsg', 'mrRsOut')), f'{f}: every earlier control id is kept')
    check('id="mrRsStatus"' in sec and 'aria-live="polite"' in sec, f'{f}: live status panel')
    check(not re.search(r'\b(bot|AI|agent)\b', re.sub(r'<[^>]+>', ' ', sec)), f'{f}: no bot wording')
js = (ROOT / 'kpc-maprep-research.js').read_text(encoding='utf-8')
check('function setTab' in js and "run(tab)" in js, 'SEARCH runs the open tab')
check(all(x in js for x in ('function stBegin', 'function stStep', 'function stCount', 'function stEnd', 'scrollIntoView', 'mrRsRetry', 'Still waiting on the official server')),
      'status: steps, counts, jump to it, slow note, TRY AGAIN')
check(js.count('stEnd(') >= 5, 'every way out of a search ends the status (done or error)')
check("b('mrRsFind', () => run('state')); b('mrRsNear', () => run('pin')); b('mrRsTest', () => run('name'));" in js, 'old buttons still work')
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
