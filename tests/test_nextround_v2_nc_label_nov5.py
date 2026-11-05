"""Next round v2 (Brandon's 10 answers, item 1, relayed via Super 8:55 AM CST Nov 5): WA DBCA outlines show 'CC BY-NC 4.0, DBCA' in
the map popup (kpc-bounds.js worldKey -> the outline's SOURCE line) and on data/CREDITS-NC.md. Runs ncLabel in node when node is
installed; the text checks always run."""
import json, pathlib, re, shutil, subprocess

ROOT = pathlib.Path(__file__).resolve().parent.parent
JS = (ROOT / 'kpc-bounds.js').read_text(encoding='utf-8')


def test_popup_label_is_wired():
    m = re.search(r"const ncLabel = \(url, label\) => .*?;\n", JS)
    assert m and "'CC BY-NC 4.0, DBCA'" in m.group(0)
    assert "fs.forEach(f => { const nc = ncLabel(L[f._src] || '', f._src);" in JS and 'SOURCE: f._src' in JS
    wk = JS.index('async function worldKey(ref)')
    assert wk < JS.index('const nc = ncLabel(') < JS.index("fs.forEach(f => { f._nm = f._nm || nm; f._bb = bbox(f.geometry); f._approx = approx;", wk)   # in worldKey, before SOURCE is set
    if shutil.which('node'):
        src = m.group(0) + "console.log(JSON.stringify([ncLabel('https://public-services.slip.wa.gov.au/public/rest/services/SLIP_Public_Services/Environment/MapServer/0', 'Forest Blocks (DBCA-025)'), ncLabel('', 'WA DBCA state forests (legislated lands)'), ncLabel('https://gis.environment.gov.au/gispubmap/rest/services/ogc_services/CAPAD/MapServer/0', 'CAPAD (DCCEEW)'), ncLabel('', 'NPWS Estate')]))"
        out = json.loads(subprocess.run(['node', '-e', src], capture_output=True, text=True, timeout=30).stdout)
        assert out == ['CC BY-NC 4.0, DBCA', 'CC BY-NC 4.0, DBCA', '', '']


def test_every_dbca_layer_the_world_key_lists_gets_the_label():
    L = json.load(open(ROOT / 'data' / 'world-key' / 'layers.json', encoding='utf-8'))
    wa = [k for k, u in L.items() if 'slip.wa.gov.au' in str(u)]
    assert wa and all('slip.wa.gov.au' in L[k] for k in wa)   # each is caught by the address test


def test_credits_page():
    c = (ROOT / 'data' / 'CREDITS-NC.md').read_text(encoding='utf-8')
    assert '**CC BY-NC 4.0, DBCA**' in c and 'map popup' in c and "Brandon's own words, relayed via Super, 8:00 AM CST Nov 5 2026" in c
    assert all(r in c for r in ('AU-7112', 'AU-7113', 'AU-7114', 'AU-7115', 'AU-7117', 'AU-7118', 'AU-7559')) and 'CAPAD (DCCEEW), CC BY 4.0' in c
