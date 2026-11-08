"""Mapping Rep Tool Box result view (Brandon Nov 8 2:19 PM CST, t751u): no repeats, no military check, plain wording for a rule
we could not confirm, and web-search links when we have no official site or map."""
import re, sys, pathlib, subprocess, json
ROOT = pathlib.Path(__file__).resolve().parents[1]
bad = 0
def check(ok, what):
    global bad
    print(('PASS ' if ok else 'FAIL ') + what); bad += (not ok)
js = (ROOT / 'kpc-maprep-check.js').read_text(encoding='utf-8')
rc = js[js.find('  function renderContext('):js.find('  async function contextFromFeature(')]
nf = js[js.find('data-mr-result="none"'):js.find("box.querySelectorAll('[data-near]')")]
check('Not named as a military base' not in js and not re.search(r"rule\([^)]*military", js, re.I), 'military base check removed')
check('STILL UNKNOWN' not in js and "'UNKNOWN'" not in js, "no 'still unknown' / UNKNOWN wording")
check('We could not confirm this.' in js and 'You can check:' in js and 'TO CONFIRM YOURSELF' in js, 'plain wording: what we could not confirm and what to check')
check(all(k in js for k in ("'Owned by the federal or state government'", "'Open to the public'", "'Has an official government web page'")) and 'const CHECK_HOW' in js, 'each rule has a what-you-can-check line')
for nm, part in (('found place', rc), ('no exact match', nf)):
    check(part.count('<h3>Rules checklist</h3>') == 1 and part.count('<h3>Official website and map</h3>') == 1 and part.count('<h3>POTA status</h3>') == 1, f'{nm}: one of each heading')
    check(part.count('directoryBlock(') == 1, f'{nm}: agency directory shown once')
    check(part.count('A helper, not the final word') == 1 and 'Before you click an official link' not in part, f'{nm}: helper note once')
    check(not re.search(r'\d · ', part), f'{nm}: plain headings')
check('padTable(' not in rc and rc.count('padCard(') == 1, 'found place: the official record card is shown once (no second PAD-US table)')
check("recCard\n      ? recCard" in rc or 'recCard\n      ? recCard' in rc or '(recCard' in rc, 'found place: short facts list only when there is no record card')
check(rc.count('pota.app/#/park/') == 2, 'found place: POTA park links only in POTA status (park list + similar names)')
for k in ('Designation', 'Managing agency', 'Acres'): check(f"kv('{k}'" in rc, f'found place without a record card still shows {k}')
check('ctx.overlapHtml' in rc and 'Overlaps, 2-fers and club notes' in rc, '2-fer and overlap results kept')
sb = js[js.find('  function siteBlock('):js.find('  function drawOnMap(')]
check("official site'" in sb and "' map'" in sb and "'site:' + hst" in sb and 'google.com/search?q=' in js, 'search fallbacks: official site, map, and the agency site')
check('fetch(' not in sb, 'search fallbacks are plain links (nothing fetched)')
check(nf.count('siteBlock(') == 1 and rc.count('siteBlock(') == 1, 'both result views use the site block')
r = (ROOT / 'kpc-maprep-research.js').read_text(encoding='utf-8')
check("card0.open = false" in r, 'FULL RULES CHECK folds the search card so the record is not shown twice')
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
