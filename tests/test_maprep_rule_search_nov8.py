"""Mapping Rep Tool Box rule cards (Brandon Nov 8 2:43 PM CST, t752u): no download-boundary button; every NOT CONFIRMED rule card
says 'None found on file.' and has its own search button; the site section's search sits where 'none found' shows; no repeats."""
import re, sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parents[1]
bad = 0
def check(ok, what):
    global bad
    print(('PASS ' if ok else 'FAIL ') + what); bad += (not ok)
js = (ROOT / 'kpc-maprep-check.js').read_text(encoding='utf-8')
check(not re.search(r'download this boundary|data-dl|Boundary download', js, re.I) and 'function padTable' not in js and 'function padGeo(' not in js, 'download boundary removed with its dead code')
check('You can check:' not in js and 'CHECK_HOW' not in js, "no 'You can check' text that sends the rep elsewhere")
rs = js[js.find('  function ruleSearch('):js.find('  function btnHtml(')]
titles = set(re.findall(r"rules\.push\(rule\('(?:pass|fail|unknown)', '([^']+)'", js)) | set(re.findall(r"rule\('unknown', '([^']+)'", js))
titles |= {'Owned by the federal or state government', 'Managed by the federal or state government', 'Open to the public'}
for t in sorted(titles):
    check(f"case '{t}':" in rs, f'rule card has its own search: {t}')
rh = js[js.find('  function rulesHtml('):js.find('  function wireRuleSearch(')]
check("r.v === 'unknown'" in rh and 'None found on file.' in rh and 'q.b.map(btnHtml)' in rh, 'every NOT CONFIRMED card: None found on file + its buttons')
check("data-rlook" in js and "requestSubmit" in js and "$('mrDeskQ')" in js, 'boundary rule runs the Tool Box layer search right here')
check('fetch(' not in rs + rh, 'rule searches are plain links or the built-in search (nothing fetched)')
sb = js[js.find('  function siteBlock('):js.find('  function drawOnMap(')]
check(sb.count('None found on file.') == 1 and 'SEARCH HERE FOR THE OFFICIAL SITE' in sb and 'SEARCH HERE FOR A MAP' in sb, 'site section: search button where none found shows')
check("'site:' + h" not in sb, 'agency-site search lives only in the web-page rule card (no repeat)')
check('Search PAD-US yourself' not in js, 'PAD-US search lives only in the boundary rule card (no repeat)')
check(js.count('wireRuleSearch(box') == 3, 'both result views wire the in-card search')
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
