#!/usr/bin/env python3
"""KPC owner's Nov 10 call (relayed for the Nov 11 batch): a picture trace (data/fers-approx-outlines.json) can be an approximate
2-fer ONLY when it sits inside a bigger park's outline. Offline: no network (every map read is stubbed to fail).
1 a trace wholly inside a bigger official outline -> approximate 2-fer, with the not-official note
2 a trace that overlaps but pokes out (more than the 25-yard SHRINK) -> no 2-fer (dropped, with the reason)
3 a trace inside a SMALLER or the SAME outline -> no
4 trace versus trace -> no. KPC owner, Nov 11: official pins (100 ft circle), trails and rivers COUNT under the existing rules, so
  trace versus a point-circle park, a trail line or a river line -> exactly the same answer as without the rule (never dropped)
5 an official / official pair -> the rule does nothing (same answer as with the rule switched off)
6 the hand-placement fields (via 'hand points', the click set) do not change the outcome"""
import copy, json, math, os, pathlib, sys, tempfile, types
HERE = pathlib.Path(__file__).resolve().parent.parent
S = HERE / '.github/scripts'
sys.path.insert(0, str(S))
os.environ.setdefault('PASS', '3')
try: import cv2  # noqa: F401
except Exception: sys.modules['cv2'] = types.ModuleType('cv2')  # noqa: BLE001
import kpc_fers as K
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg, flush=True); ok = ok and bool(c)


def _off(*a, **k): raise RuntimeError('offline test: no map is read')
K.get = _off; K._get = _off
K.land_check = lambda s, G, live=True: 'ok'
K.nearest_access = lambda s, st_of: {}
K.access_pin = lambda s, G, LN, st_of: {'from': 'none'}
K.key_line_match = lambda *a, **k: ''
K.CELL = 5.0


def sq(x0, y0, dx, dy): return [[[x0, y0], [x0 + dx, y0], [x0 + dx, y0 + dy], [x0, y0 + dy], [x0, y0]]]


BIG = sq(-121.10, 47.00, .20, .20)          # an official state forest, about 15 x 22 km
IN = sq(-121.05, 47.05, .05, .05)           # a trace well inside it
POKE = sq(-120.93, 47.05, .05, .05)         # a trace that runs 1.5 km out of it
SAME = sq(-121.10, 47.00, .20, .20)         # a trace the same as the official outline
parks = {'US-1': {'st': 'US-WA', 'ids': [1001], 'names': {}}, 'US-2': {'st': 'US-WA', 'ids': [1002], 'names': {}},
         'US-T1': {'st': 'US-WA', 'ids': ['apx|US-T1'], 'approx': True, 'names': {}}, 'US-T2': {'st': 'US-WA', 'ids': ['apx|US-T2'], 'approx': True, 'names': {}},
         'US-PC': {'st': 'US-WA', 'ids': ['pc|US-PC'], 'pc': True, 'names': {}}}
PIN = {r: (r + ' name', 47.07, -121.0, '', '', 'WA') for r in list(parks) + ['US-L']}
K.PINS.update(PIN); K.APX_PARKS.update({'US-T1', 'US-T2'}); K.PCT.add('US-PC')
st_of = lambda r: 'US-WA'


def decide(refs, G, kind='area', LN=None):
    s = {'refs': sorted(refs), 'kind': kind, 'id': '+'.join(sorted(refs)) + '@' + kind, 'center': [47.07, -121.02], 'shape': [[-121.03, 47.06], [-121.01, 47.08]],
         'box': [-121.06, 47.04, -120.99, 47.11], 'acres': 50.0, 'wide_m': 200, 'passes': [1, 1, 1], 'status': 'pass 3'}
    with tempfile.TemporaryDirectory() as t:
        cwd = os.getcwd(); os.chdir(t)
        try: K.decide(s, parks, G, LN or {}, PIN, '2026-11-11', set(), st_of)
        finally: os.chdir(cwd)
    return s


DROP = "dropped: a picture trace is an approximate 2-fer only when it sits inside a bigger park's outline"
# 1 inside a bigger official outline
s = decide(['US-1', 'US-T1'], {'US-1': [BIG], 'US-T1': [IN]})
check(not str(s['status']).startswith(DROP) and s.get('approx') and s.get('approx_note') == K.APX_NOTE and 'US-T1' in (s.get('approx_refs') or []),
      f"a trace inside a bigger official outline stays an approximate 2-fer with the not-official note ({str(s['status'])[:40]})")
check(K.pc_tag({'spots': [dict(s)]})['spots'][0].get('official_boundary') is False, 'and it is tagged approximate / not official as before')
# 2 pokes out
s = decide(['US-1', 'US-T1'], {'US-1': [BIG], 'US-T1': [POKE]})
check(str(s['status']).startswith(DROP) and 'US-T1 name' in s['status'], f"a trace that pokes out of the other park is not a 2-fer ({str(s['status'])[:60]}...)")
edge = sq(-121.05, 47.05, .05 + 10 / (111320 * math.cos(math.radians(47.07))), .05)   # 10 m past the official line on one side
s = decide(['US-1', 'US-T1'], {'US-1': [sq(-121.10, 47.00, .10, .20)], 'US-T1': [edge]})
check(not str(s['status']).startswith(DROP), 'a trace within the 25-yard edge allowance of the line still counts as inside (traces are approximate)')
# 3 smaller or the same
s = decide(['US-1', 'US-T1'], {'US-1': [IN], 'US-T1': [BIG]})
check(str(s['status']).startswith(DROP), 'a trace around a SMALLER official outline is not a 2-fer (the trace is not inside it)')
s = decide(['US-1', 'US-T1'], {'US-1': [BIG], 'US-T1': [SAME]})
check(str(s['status']).startswith(DROP), 'a trace the same as the official outline is not a 2-fer (not bigger)')
# 4 trace x trace, trace x point-circle, trace x line
s = decide(['US-T1', 'US-T2'], {'US-T1': [IN], 'US-T2': [BIG]})
check(str(s['status']).startswith(DROP), 'trace versus a bigger trace is not a 2-fer (two approximate traces never make one)')
def norule(refs, G, **k):
    f0 = K.is_picture_trace; K.is_picture_trace = lambda r, p: False
    try: return decide(refs, G, **k)
    finally: K.is_picture_trace = f0


LINE = [[[-121.06, 47.07], [-120.98, 47.07]]]
for name, refs, G, kw in (
        ('a point-circle park (100 ft circle around the official pin)', ['US-PC', 'US-T1'], {'US-PC': [IN], 'US-T1': [BIG]}, {}),
        ('a point-circle park, trace poking out', ['US-PC', 'US-T1'], {'US-PC': [BIG], 'US-T1': [POKE]}, {}),
        ('a trail line', ['US-L', 'US-T1'], {'US-T1': [IN]}, {'kind': 'trail', 'LN': {'US-L': {'lines': LINE, 'kind': 'trail'}}}),
        ('a river line', ['US-L', 'US-T1'], {'US-T1': [IN]}, {'kind': 'river', 'LN': {'US-L': {'lines': LINE, 'kind': 'river'}}}),
        ('a river line on an area row', ['US-L', 'US-T1'], {'US-T1': [POKE]}, {'LN': {'US-L': {'lines': LINE, 'kind': 'river'}}}),
        ('a 3-fer with a pin and a smaller outline', ['US-1', 'US-PC', 'US-T1'], {'US-1': [IN], 'US-PC': [IN], 'US-T1': [BIG]}, {})):
    a = decide(refs, G, **kw); b = norule(refs, G, **kw)
    check(a == b and not str(a['status']).startswith(DROP), f'trace versus {name}: counts under the existing rules, same answer as without the rule ({str(a["status"])[:40]})')
s = decide(['US-1', 'US-2', 'US-T1'], {'US-1': [BIG], 'US-2': [sq(-121.06, 47.04, .03, .03)], 'US-T1': [IN]})
check(not str(s['status']).startswith(DROP), 'a 3-fer counts when the trace sits inside a bigger park of the row')
# 5 official / official: the rule does nothing
G2 = {'US-1': [BIG], 'US-2': [IN]}
a = decide(['US-1', 'US-2'], G2)
f0 = K.is_picture_trace; K.is_picture_trace = lambda r, p: False
try: b = decide(['US-1', 'US-2'], G2)
finally: K.is_picture_trace = f0
check(a == b and not str(a['status']).startswith(DROP), 'an official / official pair gets exactly the same answer with or without the rule')
check(K.trace_inside_bigger('US-T1', 'US-1', {'US-1': [BIG], 'US-T1': [IN]}) and not K.trace_inside_bigger('US-T1', 'US-1', {'US-1': [IN], 'US-T1': [BIG]}),
      'trace_inside_bigger: inside a bigger outline yes, around a smaller one no')
# 6 hand placements: the extra fields do not change anything
with tempfile.TemporaryDirectory() as t:
    t = pathlib.Path(t); (t / 'data').mkdir()
    base = {'name': 'Trace park', 'st': 'US-WA', 'src': 'picture trace of the official map', 'approx': True, 'rings': IN}
    outs = []
    for extra in ({}, {'via': 'hand points', 'clicks': [[10, 12], [40, 12], [40, 44]], 'click_set': 'a'}):
        (t / 'data/fers-approx-outlines.json').write_text(json.dumps({'parks': {'US-T9': dict(base, **extra)}}))
        K.APX_OUT = {}; pk = {}; K.PINS['US-T9'] = PIN['US-T9'] = ('Trace park', 47.07, -121.02, '', '', 'WA')
        K.add_approx_outlines(pk, PIN, {}, 'na', root=str(t))
        parks['US-T9'] = pk['US-T9']
        outs.append((copy.deepcopy(pk['US-T9']), decide(['US-1', 'US-T9'], {'US-1': [BIG], 'US-T9': [IN]})['status'],
                     decide(['US-1', 'US-T9'], {'US-1': [BIG], 'US-T9': [POKE]})['status']))
    K.APX_OUT = {}
check(outs[0] == outs[1] and not str(outs[0][1]).startswith(DROP) and str(outs[0][2]).startswith(DROP),
      "the hand-placement fields (via 'hand points', clicks) do not change the outcome")
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
