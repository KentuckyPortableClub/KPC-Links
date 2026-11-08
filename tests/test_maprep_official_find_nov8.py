"""Official site / map look-up (Brandon Nov 8 2:49-2:50 PM CST, t753u/t754u/t755u): on file -> lookup file -> live (FULL RULES
CHECK only) -> None found on file + SEARCH HERE. The finder is by hand only, honours robots.txt, keeps 60 s per host, no banned hosts."""
import re, sys, pathlib, subprocess
ROOT = pathlib.Path(__file__).resolve().parents[1]
bad = 0
def check(ok, what):
    global bad
    print(('PASS ' if ok else 'FAIL ') + what); bad += (not ok)
js = (ROOT / 'kpc-maprep-check.js').read_text(encoding='utf-8')
sb = js[js.find('  function siteBlock('):js.find('  function drawOnMap(')]
i_page, i_found, i_none = sb.find('h += page ?'), sb.find('found.site ?'), sb.find("none('Official website'")
check(0 < i_page < i_found < i_none, 'website: on the record first, then a lookup result, then None found + SEARCH HERE')
check(sb.find('mapUrl ?') < sb.find('found.map ?') < sb.find("none('Official map'"), 'map: same order')
lk = js[js.find('  async function officialLookup('):js.find('  async function fillSite(')]
check("data/parkinfo-web.json" in lk and "'data/official-links/' + code" in lk and 'ky-official-maps' in lk, 'lookup files are read')
check(lk.find("take(r, 'file')") < lk.find("take(r, 'live')") and 'if (deep &&' in lk, 'lookup file before the live match; live only when deep')
fs = js[js.find('  async function fillSite('):js.find('  function normU(')]
check('deep = fullMode' in fs, 'live look-up only in FULL RULES CHECK mode')
check('function showFull(la, lo) { fullMode = true;' in js and 'if (!full) fullMode = false;' in js, 'any other check turns the live look-up off')
r = (ROOT / 'kpc-maprep-research.js').read_text(encoding='utf-8')
check('W.KPCMapCheck.showFull(p.pt[0], p.pt[1])' in r, 'FULL RULES CHECK uses the full mode')
check(not re.search(r'wikidata|sparql', js + r, re.I), 'no Wikidata (its robots.txt disallows /w/ and /sparql)')
check('fetch(' not in lk.replace('fetch(u)', ''), 'the page fetches only our own data files')
check('From ${esc(x.src)}' in sb, 'each found link says where it came from and how sure')
py = (ROOT / '.github/scripts/kpc_official_find.py').read_text(encoding='utf-8')
check('DELAY = 60' in py and 'robotparser' in py and 'can_fetch(UA' in py, 'finder: robots.txt and 60 s per host')
check("services\\d*\\.arcgis\\.com" in py and 'ncnhde' in py and 'maps\\.gov\\.bc\\.ca' in py and '33TOOklri9xpic7U' in py, 'finder: banned hosts')
check('wikidata' not in py.lower().replace('wikidata is not used', ''), 'finder: no Wikidata')
wf = (ROOT / '.github/workflows/kpc-official-find.yml').read_text(encoding='utf-8')
check('workflow_dispatch' in wf and 'schedule' not in wf.split('on:')[1].split('permissions')[0], 'finder workflow is by hand only (no cron)')
check(subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_official_find.py'), 'selftest'], capture_output=True).returncode == 0, 'finder selftest')
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
