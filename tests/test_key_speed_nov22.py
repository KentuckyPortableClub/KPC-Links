#!/usr/bin/env python3
"""22 Nov 2026 (owner: "fix the mapping so it is quicker building so it dont search every piece"): the builder's speed-ups
give the same answers. Invented records only. Fails before the change (no RecordGrid, no remembered names)."""
import ast, math, pathlib, random, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = (ROOT / '.github' / 'scripts' / 'kpc_us_key.py').read_text(encoding='utf-8')
bad = []


def check(name, ok):
    print(('PASS ' if ok else 'FAIL ') + name)
    if not ok: bad.append(name)


tree = ast.parse(SRC)
want = {'norm', '_norm_once', 'near', 'RecordGrid', 'by_id', '_oid', 'name_clusters_swept'}
got = {n.name: n for n in tree.body if isinstance(n, (ast.FunctionDef, ast.ClassDef)) and n.name in want}
check('the builder has the name memory, the record grid and the id lookup', set(got) >= want)
if set(got) >= want:
    ns = {'re': re, 'math': math, 'unicodedata': __import__('unicodedata')}
    for assign in tree.body:   # the constants norm() reads (ABBR, GEN, NOTNAME, ...)
        if isinstance(assign, ast.Assign) and all(isinstance(t, ast.Name) and t.id.isupper() or (isinstance(t, ast.Name) and t.id in ('_NORM_MEMO', '_BY_ID')) for t in assign.targets):
            try: exec(compile(ast.Module([assign], []), 'k', 'exec'), ns)
            except Exception: pass  # noqa: BLE001
    for n in want: exec(compile(ast.Module([got[n]], []), 'k', 'exec'), ns)
    norm, near, RG, by_id = ns['norm'], ns['near'], ns['RecordGrid'], ns['by_id']
    names = ['Test Lake State Park', 'TEST LAKE', 'Ft. Test', 'Test Creek WMA - North Unit', 'Test (Joe A.) Memorial', '']
    check('a remembered name is the same as one worked out fresh', all(norm(x) == ns['_norm_once'](x) and norm(x, True) == ns['_norm_once'](x, True) for x in names * 2))
    rnd = random.Random(7)
    recs = []
    for i in range(3000):
        x, y = rnd.uniform(-90, -80), rnd.uniform(25, 36)
        w, h = rnd.choice([0.001, 0.01, 0.2, 1.5]), rnd.choice([0.001, 0.02, 0.3, 2.0])
        recs.append({'OBJECTID': f'tst{i}', 'Unit_Nm': rnd.choice(['Test Lake', 'Other Place', 'Far Test']), '_bb': [x, y, x + w, y + h] if i % 50 else None})
    recs.append({'OBJECTID': 'huge', 'Unit_Nm': 'Huge Test', '_bb': [-125, 20, -60, 50]})
    g = RG(recs, pad=.6)
    ok = True
    for _ in range(400):
        la, lo = rnd.uniform(24, 37), rnd.uniform(-91, -79)
        nn = norm(rnd.choice(['Test Lake', 'Far Test', 'Nothing']))
        old = [a for a in recs if near(la, lo, a['_bb'], .6) or norm(a.get('Unit_Nm') or '') == nn]
        new = [a for a in g.around(la, lo, nn) if near(la, lo, a['_bb'], .6) or norm(a.get('Unit_Nm') or '') == nn]
        ok = ok and old == new
    check('the grid hands a park every record the old loop could join, in the same order (400 invented pins)', ok)
    check('no pin, or a pin that is not a number: every record, as before', g.around(None, None, '') == recs and g.around(float('nan'), 1.0, '') == recs)
    check('a record too big for the grid is always looked at', any(a['OBJECTID'] == 'huge' for a in g.around(25.0, -80.0, 'x')))
    d1 = by_id(recs); d2 = by_id(recs)
    check('the id lookup is built once and matches the old one', d1 is d2 and d1 == {str(a['OBJECTID']): a for a in recs})
    recs.append({'OBJECTID': 'new1', 'Unit_Nm': 'x', '_bb': None})
    check('the id lookup is rebuilt when the record list grows', 'new1' in by_id(recs))

# 22 Nov (round 2): the name clusters sweep and the remembered pin test give the same answers
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import kpc_match as KM  # noqa: E402
import kpc_match_checks as MC  # noqa: E402


def clusters_brute(items):
    byname = {}
    for nn, bb in items:
        if bb: byname.setdefault(nn, []).append(bb)
    out = {}
    for nn, bbs in byname.items():
        par = list(range(len(bbs)))
        def f(i):
            while par[i] != i: par[i] = par[par[i]]; i = par[i]
            return i
        for i in range(len(bbs)):
            for j in range(i + 1, len(bbs)):
                if not KM._apart(bbs[i], bbs[j]): par[f(i)] = f(j)
        out[nn] = len({f(i) for i in range(len(bbs))})
    return out


rnd2 = random.Random(11)
items = []
for i in range(1500):
    x, y = rnd2.uniform(-85, -80), rnd2.uniform(25, 30)
    w, h = rnd2.choice([0.001, 0.05, 0.3]), rnd2.choice([0.001, 0.05, 0.3])
    items.append((rnd2.choice(['test a', 'test b', 'test c', 'test d']), [x, y, x + w, y + h] if i % 40 else None))
swept = ns.get('name_clusters_swept') if 'ns' in dir() else None
if swept: swept.__globals__['KM'] = KM
check('the west-to-east sweep counts the same separate places as every pair did (1,500 invented boxes)',
      bool(swept) and swept(items) == clusters_brute(items) == KM.name_clusters(items))
calls = []
rows = [[f'r{i}', 'Test', 1, 'same name'] for i in range(30)]
holds_fn = lambda ref, i: calls.append(i) or i in ('r3', 'r7')
memo = {}
holds = lambda i: memo[i] if i in memo else memo.setdefault(i, holds_fn('K4-1', i))
held = [x for x in rows if holds(str(x[0])) is True]
same = all(MC.pin_3c(q, rows, holds, 'Test Park') == MC.pin_3c(q, rows, holds, 'Test Park', held=held) for q in rows)
check('the pin test with the held rows worked out once gives the same flags, and each record is tested once',
      same and sorted(set(calls)) == sorted(calls))

check('the join loop uses the grid', 'for a in near_idx.around(la, lo, norm(name)):' in SRC)
print('ALL PASS' if not bad else f'{len(bad)} FAIL')
sys.exit(1 if bad else 0)
