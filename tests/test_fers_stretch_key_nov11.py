#!/usr/bin/env python3
"""Nov 11 2026 (KPC owner): the 2-fer builder's 25 m trail / river minimum and the current-key gate. Offline, no run started.
- STRETCH is 25.0 and the header / docstrings say 25 metres (not 100 yards, not zero).
- line_spots (the real code that applies STRETCH, on a synthetic park + line): a 24 m stretch is dropped, a 26 m one kept;
  touching pieces of one line count together; passes 1-2 (screens) keep every stretch, pass 3 decides; a line whose whole saved
  copy is under 25 m is kept and marked line_short, and decide() makes it NOT SURE (never a silent drop).
- decide(): a key PIN park never makes a row (area, and the area half of a trail row); the line park of a trail row is not
  graded; an approximate park is kept and tagged approximate with the not-official note (pc_tag).
- Row lengths: a row's own stretch is kept apart (len_main), so copies of OTHER rows never shrink it to 0 m."""
import math, os, pathlib, sys, tempfile
HERE = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HERE / '.github/scripts'))
os.environ['PASS'] = '3'
_cwd = os.getcwd(); os.chdir(tempfile.mkdtemp())   # kpc_fers makes data/fers in the working folder: keep it out of the repo
import kpc_fers as K
import kpc_fers_key_status as FKS
os.chdir(_cwd)
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


src = (HERE / '.github/scripts/kpc_fers.py').read_text(encoding='utf-8')
check(K.STRETCH == 25.0, f'STRETCH == 25.0 (got {K.STRETCH})')
head = src.split('"""')[1]
check('AT LEAST 25 METRES LONG' in head and 'meet along 25 metres' in head and '100 YARDS LONG' not in head and 'along 100 yards' not in head,
      'the file header says 25 metres for trails / rivers (not 100 yards)')
check('at least STRETCH (25 metres) long' in K.line_spots.__doc__ and '100 yards' not in K.line_spots.__doc__, 'line_spots docstring says 25 metres')
check("along at least 25 metres of the line" in K.ABOUT, 'the data files\' about text says 25 metres')
for f in ('kpc-overlap-finder.html', '.claude/build/overlap-finder/main.html'):
    check('at least 25 metres of the line run inside the other park' in (HERE / f).read_text(encoding='utf-8'), f'{f}: HOW WE CHECK says 25 metres')

# ---- line_spots on a synthetic park: a 1 km square; the line's far piece lies outside every park (so the line is long)
lat0, lon0 = 45.0, -90.0
kx, ky = 111320 * math.cos(math.radians(lat0)), 110574


def P(x, y): return [lon0 + x / kx, lat0 + y / ky]


SQ = [[P(-500, -500), P(500, -500), P(500, 500), P(-500, 500), P(-500, -500)]]
BOX = [lon0 - 0.02, lat0 - 0.02, lon0 + 0.03, lat0 + 0.02]
FAR = [P(1500, 0), P(1700, 0)]


def spots(ls):
    return K.line_spots('US-LINE', ls, 'US-AREA', [SQ], False, BOX, 'trail')


s24, s26 = spots([[P(0, 0), P(24, 0)], FAR]), spots([[P(0, 0), P(26, 0)], FAR])
check(s24 == [], f'a 24 m stretch inside the park is dropped (got {[x["len_m"] for x in s24]})')
check(len(s26) == 1 and s26[0]['len_m'] == 26 and not s26[0].get('line_short'), f'a 26 m stretch is kept, measured 26 m to the line\'s end (got {[x["len_m"] for x in s26]})')
two = spots([[P(0, 0), P(15, 0)], [P(15, 0), P(30, 0)], FAR])
check(len(two) == 1 and two[0]['len_m'] == 30, f'two touching 15 m pieces of one line = one 30 m stretch, kept (got {[x["len_m"] for x in two]})')
check(spots([[P(0, 0), P(15, 0)], FAR]) == [], 'one 15 m piece alone is dropped')
edge = spots([[P(400, 0), P(800, 0)]])
check(len(edge) == 1 and 100 <= edge[0]['len_m'] <= 140, f'a line crossing the park edge keeps the stretch within 100 ft of the inside (got {[x["len_m"] for x in edge]})')
dot = spots([[P(0, 0), P(0, 0)], [P(100, 100), P(100, 100)]])
check(dot and all(x.get('line_short') == {'US-LINE': 0} for x in dot), 'a saved line that is only points (0 m in all) is kept and marked line_short, not dropped')
_p, _c = K.PASS, K.CELL
try:
    K.PASS, K.CELL = 1, 20.0
    p1 = spots([[P(0, 0), P(20, 0)], FAR])
    check(len(p1) == 1, 'pass 1 (a screen on saved copies) keeps a 20 m stretch: pass 3 decides')
finally:
    K.PASS, K.CELL = _p, _c
check(spots([[P(0, 0), P(20, 0)], FAR]) == [], 'pass 3 drops the same 20 m stretch')

# ---- decide(): the key gate (key status preset, the way the builder reads the current key)
FKS.clear(); FKS.KEY_STATUS.update({'US-OFF': 'official', 'US-PIN': 'pin', 'US-APX': 'approximate', 'US-LINE': 'pin'})
PIN = {r: (r + ' name', 45.0, -90.0, '', 'State Park', 'MN') for r in ('US-OFF', 'US-PIN', 'US-APX', 'US-LINE')}


def decided(refs, kind, G, LN, **kw):
    s = {'refs': refs, 'kind': kind, 'center': [45.0, -90.0], 'shape': [[-90, 45], [-90.001, 45]], 'id': '+'.join(refs) + '@' + kind, **kw}
    K.decide(s, {}, G, LN, PIN, '2026-11-11', set(), lambda r: 'US-MN'); return s


a = decided(['US-OFF', 'US-PIN'], 'area', {'US-OFF': [], 'US-PIN': []}, {})
check(str(a.get('status')).startswith('dropped: key PIN') and 'US-PIN' in a['status'], f'area row with a key-PIN park is dropped ({a.get("status")})')
a = decided(['US-OFF', 'US-PIN'], 'same land', {'US-OFF': [], 'US-PIN': []}, {})
check(str(a.get('status')).startswith('dropped: key PIN'), 'same-land row with a key-PIN park is dropped')
t = decided(['US-LINE', 'US-PIN'], 'trail', {'US-PIN': []}, {'US-LINE': {'lines': []}})
check(str(t.get('status')).startswith('dropped: key PIN') and '(US-PIN)' in t['status'], f'trail row whose AREA park is a key PIN is dropped ({t.get("status")})')
t = decided(['US-LINE', 'US-OFF'], 'river', {'US-OFF': []}, {'US-LINE': {'lines': []}})
check(not str(t.get('status')).startswith('dropped: key PIN'), f'river row whose LINE park is graded pin is not dropped for it (line-only park) ({t.get("status")})')
x = decided(['US-APX', 'US-OFF'], 'area', {'US-APX': [], 'US-OFF': []}, {})
check(not str(x.get('status')).startswith('dropped') and x.get('approx') and x.get('approx_refs') == ['US-APX'], f'an approximate park is not dropped by the key gate and is tagged approximate (status here comes from the stub data: {x.get("status")})')
d = K.pc_tag({'spots': [x]})['spots'][0]
check(d.get('tier') == 'approximate' and d.get('official_boundary') is False and 'Not the official boundary' in d.get('approx_note', ''),
      'pc_tag marks it approximate, not official, with the not-official note')
sh = decided(['US-LINE', 'US-OFF'], 'trail', {'US-OFF': []}, {'US-LINE': {'lines': []}}, line_short={'US-LINE': 1})
check(str(sh.get('status')).startswith('not sure: our saved copy of the official line for US-LINE is only 1 m long'), f'a line_short row is NOT SURE, not dropped ({sh.get("status")})')
check(FKS.key_line_match(['US-PIN', 'US-OFF'], 'trail') == '' and FKS.key_line_match(['US-PIN', 'US-OFF'], 'trail', lines=['US-PIN']) == ''
      and FKS.key_line_match(['US-PIN', 'US-OFF'], 'trail', lines=['US-OFF']).startswith('dropped'), 'key_line_match: lines= exempts only the line park')
FKS.clear()

# ---- row lengths: the main row's own stretch is kept apart; a copy of ANOTHER row with the same parks never shrinks it
r = ['US-A', 'US-B']
sp = [{'id': 'M', 'refs': r, 'kind': 'trail', 'status': 'candidate', 'len_m': 898, 'shape': [[0, 0], [0, 1]]},
      {'id': 'S', 'refs': r, 'kind': 'trail', 'status': 'candidate', 'len_m': 5301, 'shape': [[0, 2], [0, 3]]}]
K.one_row_per_line_pair(sp, None, {}, {})
main = [x for x in sp if x['status'] == 'candidate'][0]
sp += [{'id': 'NS', 'refs': r, 'kind': 'trail', 'status': 'not sure: no public owner', 'len_m': 44453, 'shape': [[5, 5], [5, 6]]},
       {'id': 'C', 'refs': r, 'kind': 'trail', 'status': 'candidate', 'len_m': 44453, 'shape': [[5, 5], [5, 6]]}]   # a copy of the not-sure row
K.dedupe_line_rows(sp)
check(main['id'] == 'S' and main['len_main'] == 5301 and main['len_m'] == 6199, f'one row per pair: own 5301 m + 898 m merged = 6199 m (got {main.get("len_main")}, {main.get("len_m")})')
old = [{'id': 'M', 'refs': r, 'kind': 'trail', 'status': 'candidate', 'len_m': 6199, 'stretches': 2, 'shape': [[0, 2], [0, 3]]},
       {'id': 'S', 'refs': r, 'kind': 'trail', 'status': 'merged into one row: M', 'len_m': 898, 'shape': [[0, 0], [0, 1]]},
       {'id': 'NS', 'refs': r, 'kind': 'trail', 'status': 'not sure: no public owner', 'len_m': 44453, 'shape': [[5, 5], [5, 6]]},
       {'id': 'C', 'refs': r, 'kind': 'trail', 'status': 'dropped: the same stretch twice (copy of NS)', 'len_m': 44453, 'shape': [[5, 5], [5, 6]]}]
K.dedupe_line_rows(old)
check(old[0]['len_main'] == 5301 and old[0]['len_m'] == 6199, f'a row merged before Nov 11: a copy of another row is not taken off its own length (got {old[0].get("len_main")}, {old[0].get("len_m")})')

print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
