"""Point-circle card notes (Brandon t954u, Nov 9 2026): every user card that shows a point-circle park or 2-fer says plainly that
there is no official boundary, that a 100 ft circle around the agency's official point is used, names the source layer/record, and
says to check before activating. Neutral words only (t952u: no inside rule info). Offline, no network.
Run from the KPC-Links root: python3 tests/test_point_circle_notes.py"""
import ast, json, math, os, pathlib, re, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
E = {'kind': 'point-circle-100ft', 'pt': [-121.34178, 61.85507], 'record_id': '31', 'record_name': 'Fort Simpson',
     'layer_url': 'https://www.apps.geomatics.gov.nt.ca/arcgis/rest/services/GNWT/Environment_LCC/MapServer/204'}
WANT = ("No official boundary on file. Using a 100 ft circle around the agency\u2019s official point (Fort Simpson, "
        "Environment LCC layer 204, record 31). The real boundary may be larger, so check before you activate.")
INSIDE = re.compile(r'brandon|t9\d\du|quality|bot\b|rule|hash|decided|tier', re.I)   # inside words a user card must not carry


def fers_funcs():
    src = (ROOT / '.github/scripts/kpc_fers.py').read_text(encoding='utf-8')
    tree = ast.parse(src); keep = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ('pc_note', 'pc_tag')]
    g = {'re': re, 'PC': {'CA-0754': E}, 'PCT': {'CA-0754'}, 'PC_LIST': 'point-circle'}
    exec(compile(ast.Module(body=keep, type_ignores=[]), 'kpc_fers.py', 'exec'), g); return g


def test_python_note_and_tag():
    g = fers_funcs()
    assert g['pc_note']('CA-0754') == WANT
    assert not INSIDE.search(WANT)
    d = g['pc_tag']({'spots': [{'refs': ['CA-0754', 'CA-0001']}, {'refs': ['CA-0002', 'CA-0003']}]})
    a, b = d['spots']
    assert a['tier'] == 'point-circle' and a['official_boundary'] is False and a['pc_note'] == {'CA-0754': WANT}
    assert 'pc_note' not in b and 'tier' not in b                 # a normal 2-fer gets no note
    g['PC']['X-1'] = {'kind': 'point-circle-100ft', 'pt': [0, 0]}  # no record data: the note still reads cleanly
    assert g['pc_note']('X-1').startswith('No official boundary on file. Using a 100 ft circle around the agency\u2019s official point. ')


def js_block():
    s = (ROOT / 'kpc-bounds.js').read_text(encoding='utf-8')
    gt = re.search(r'  function gradeText\(o\) \{.*?\n  \}\n', s, re.S).group(0)
    pc = re.search(r'  let PCD = null, PCS = \{\};.*?const pcSync = ref => PCS\[ref\] \|\| null;', s, re.S).group(0)
    return gt + pc


def test_js_cards_same_text():
    node = shutil.which('node')
    if not node: print('  (node missing: JS part skipped)'); return
    prog = ("const DATA=" + json.dumps({'parks': {'CA-0754': E}}) + ";globalThis.fetch=()=>Promise.resolve({ok:true,json:()=>Promise.resolve(DATA)});\n"
            + js_block() + "\nsetTimeout(()=>{console.log(JSON.stringify({note:pcNote(pcSync('CA-0754')),"
            "pin:gradeText({label:'pin',ref:'CA-0754'}),plain:gradeText({label:'pin',ref:'US-0001'}),"
            "off:gradeText({label:'official',ref:'CA-0754'})}))},20);")
    out = json.loads(subprocess.run([node, '-e', prog], capture_output=True, text=True, check=True).stdout)
    assert out['note'] == WANT                                     # the same words as the 2-fer cards (Python)
    assert out['pin'] == 'Pin only (no official outline yet). ' + WANT
    assert out['plain'] == 'Pin only (no official outline yet)'    # a park without a circle: unchanged
    assert out['off'] == 'Official outline'                        # a real boundary wins: no note


def test_every_card_wired():
    ov = (ROOT / 'kpc-overlap-finder.js').read_text(encoding='utf-8')
    fn = lambda name: re.search(r'function ' + name + r'\(.*?\n  function ', ov, re.S).group(0)
    assert 'pcLine(ps)' in fn('rowHtml') and 'POINT CIRCLE: NO OFFICIAL BOUNDARY' in fn('rowHtml')   # 2-fer list card
    assert 's.pc_note[p.ref]' in fn('parkPop')                                                     # park popup on the 2-fer map
    assert 'pcLine([s])' in fn('patchPop')                                                         # overlap popup on the map
    assert 'pcNotes(g.best' in fn('fileOut')                                                       # GPX / KML export
    assert 'ref:s.c' in (ROOT / 'kpc-us-planner.js').read_text(encoding='utf-8')                   # Tool Box park card grade line
    mc = (ROOT / 'kpc-maprep-check.js').read_text(encoding='utf-8')
    assert 'KPCB.pcNote(_pc)' in mc                                                                # mapping rep checklist card
    assert 'B.pcNote(pc)' in (ROOT / 'kpc-kit.js').read_text(encoding='utf-8')                       # Activation Kit park card
    assert 'KPCB.pcNote(pc)' in (ROOT / 'kpc-access.js').read_text(encoding='utf-8')                  # Access Finder park card
    assert 'KPCB.pcNote(pc)' in (ROOT / 'kpc-gps.js').read_text(encoding='utf-8')                     # GPS / GPX / KML pin text
    assert re.search(r'window\.KPCB = \{ pointCircle, pcSync, pcNote,', (ROOT / 'kpc-bounds.js').read_text(encoding='utf-8'))


if __name__ == '__main__':
    n = 0
    for k, f in list(globals().items()):
        if k.startswith('test_'): f(); n += 1; print('ok', k)
    print(n, 'point-circle note tests passed')
