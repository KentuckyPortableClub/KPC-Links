#!/usr/bin/env python3
"""R-FJ1 (KPC owner, 19 Nov 11:49 AM: "yes pins are only references they are not always right"; Fable's sheet, .claude/notes/
key-quality.md section 19 items 26-27). A person's saved join may reach a record FAR from POTA's pin (past the 0.6 degree box)
only when the answer names that exact record id in 'join' AND 'far', carries decided_by + evidence (who, source, saw, date), and
the record read today still fits its saved fingerprint. Switch KPC_FAR_JOIN (default ON).
The sheet's six examples, with the real records (19 Nov saved shapes):
  1. Custer Gallatin NF US-4501 + PAD-US 2660 'Gallatin National Forest' (1,850,408 ac; pin 45.5048, -105.997, record box ends at
     -109.556): joins.
  2. the same answer without 'far': nothing (today's behaviour).
  3. a 'far' id that now holds another name (or acres 10% off): check, no join.
  4. 'far' without evidence: ignored, warning.
  5. a NAME in 'far': ignored.
  6. Ouachita NF in Oklahoma US-4424 + PAD-US 3001 (353,440 ac; FS report 353,430) would join the same way (evidence batch 03).
Also: an 'approx' answer never far-joins; a NO wins; switch OFF = nothing; scope entry + changelog line."""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCR = ROOT / '.github' / 'scripts'
sys.path.insert(0, str(SCR))
import kpc_key_rules as KR  # noqa: E402
FAILS = []


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok: FAILS.append(what)


EV = {'who': 'Fable (sitting 3)', 'source': 'USFS Land Areas Report FY2025', 'saw': 'Gallatin NF 1,850,468 NFS ac', 'date': '2026-11-19'}
GALLATIN = {'OBJECTID': 2660, 'Unit_Nm': 'Gallatin National Forest', 'Loc_Nm': 'Custer Gallatin National Forest', 'Mang_Name': 'USFS', 'GIS_Acres': 1850408}
ANS = {'join': ['sgidd145', '2660'], 'far': ['2660'], 'fp': {'2660': ['Gallatin National Forest', 1850408]}, 'decided_by': 'evidence batch 02', 'evidence': EV}

# 1. the rule's own test (kpc_key_rules.far_join_ok)
check(KR.DEFAULTS.get('KPC_FAR_JOIN') == '1', 'switch KPC_FAR_JOIN is ON by default')
check(KR.far_join_ok(ANS, '2660', GALLATIN)[0] == 'ok', "1. Custer Gallatin US-4501 + 2660 'Gallatin National Forest': a far join")
check(KR.far_join_ok(dict(ANS, far=[]), '2660', GALLATIN)[0] is None, "2. the same answer without 'far': not asked for (today's behaviour)")
check(KR.far_join_ok(ANS, '2660', dict(GALLATIN, Unit_Nm='Beaverhead National Forest', Loc_Nm='Beaverhead-Deerlodge National Forest'))[0] == 'nofit',
      '3. the far id now holds another name: check, no join')
check(KR.far_join_ok(ANS, '2660', dict(GALLATIN, GIS_Acres=1500000))[0] == 'nofit', '3b. the far id now holds acres 19% off: check, no join')
check(KR.far_join_ok(dict(ANS, evidence={}), '2660', GALLATIN)[0] == 'noevidence' and KR.far_join_ok(dict(ANS, decided_by=''), '2660', GALLATIN)[0] == 'noevidence'
      and KR.far_join_ok(dict(ANS, evidence=dict(EV, source='')), '2660', GALLATIN)[0] == 'noevidence', "4. 'far' without decided_by or full evidence: ignored")
check(KR.far_join_ok(dict(ANS, fp={}), '2660', GALLATIN)[0] == 'noevidence', "4b. 'far' without a fingerprint: ignored")
check(KR.far_join_ok(dict(ANS, far=['Gallatin National Forest']), '2660', GALLATIN)[0] is None, "5. a NAME in 'far' is not an id: ignored")
check(KR.far_join_ok(dict(ANS, approx=True), '2660', GALLATIN)[0] == 'approx', "an 'approx' answer never far-joins (Q1 keeps it a pin)")
check(KR.far_join_ok(dict(ANS, join=['sgidd145']), '2660', GALLATIN)[0] is None, "an id in 'far' but not in 'join': not asked for")
OUACHITA = {'OBJECTID': 3001, 'Unit_Nm': 'Ouachita National Forest', 'Loc_Nm': 'Ouachita National Forest', 'Mang_Name': 'USFS', 'GIS_Acres': 353440}
check(KR.far_join_ok({'join': ['3001'], 'far': ['3001'], 'fp': {'3001': ['Ouachita National Forest', 353440]}, 'decided_by': 'x', 'evidence': EV}, '3001', OUACHITA)[0] == 'ok',
      '6. Ouachita NF in Oklahoma US-4424 + 3001 would join the same way (evidence batch 03)')

# 2. the build's join path, cut out of kpc_us_key.py and run on stand-ins (the real Montana build: key-quality.md section 19 item 30)
src = (SCR / 'kpc_us_key.py').read_text(encoding='utf-8')
i = src.find("            for want in ov.get('join', []):"); j = src.find("        _sct, _sfirst = [], False")
check(0 < i < j, 'the saved-join loop is in kpc_us_key.py')
body = src[i:j]
check("_kr('KPC_FAR_JOIN')" in body and 'KR.far_join_ok(ov, _want0, a)' in body and '(_near or _far)' in body and 'str(want) == _want0' in body,
      'the join path asks far_join_ok only for the exact saved id (never a re-found one) and only past the 0.6 degree box')
fn = 'def _join(ref, name, ov, recs, m, c, la, lo, st, sw):\n    no = {str(x) for x in ov.get("no", [])}\n' + '\n'.join(l[8:] for l in body.splitlines()) + '\n    return m, c\n'
fn = fn.replace("_kr('KPC_FAR_JOIN')", 'sw')


def near(la, lo, b, pad): return b and b[0] - pad <= lo <= b[2] + pad and b[1] - pad <= la <= b[3] + pad


FJ = []
ns = {'KR': KR, 're': re, '_oid': lambda a: str(a['OBJECTID']), '_nf': KR.nf, 'near': near, '_no_all': lambda ov, a: False,
      '_kr': lambda name: name == 'KPC_ID_JOIN_NAME', 'FAR_JOIN': FJ}
exec(fn, ns)
PIN = (45.5048, -105.997)
recs = [dict(GALLATIN, _bb=[-111.593, 44.487, -109.556, 46.292]),
        {'OBJECTID': 2652, 'Unit_Nm': 'Custer National Forest', 'Loc_Nm': 'Custer Gallatin National Forest', 'GIS_Acres': 1115748, '_bb': [-110.157, 45.003, -104.042, 45.924]}]
m, c = ns['_join']('US-4501', 'Custer Gallatin National Forest', ANS, recs, [[2652, 'Custer Gallatin National Forest (Custer National Forest)', 1115748, 'name']], [], *PIN, 'MT', True)
check(sorted(str(x[0]) for x in m) == ['2652', '2660'] and next(x for x in m if str(x[0]) == '2660')[3] == 'reviewed' and FJ == [['MT', 'US-4501', '2660', 'Gallatin National Forest']],
      "build: US-4501 keeps 2652 and gains 2660 as a person's join; the run names it once")
FJ.clear()
m, c = ns['_join']('US-4501', 'Custer Gallatin National Forest', ANS, recs, [[2652, 'x', 1115748, 'name']], [], *PIN, 'MT', False)
check([str(x[0]) for x in m] == ['2652'] and not FJ, 'build, switch OFF: nothing joins (as today)')
m, c = ns['_join']('US-4501', 'Custer Gallatin National Forest', dict(ANS, far=[]), recs, [[2652, 'x', 1115748, 'name']], [], *PIN, 'MT', True)
check([str(x[0]) for x in m] == ['2652'], "build, no 'far': nothing joins (as today)")
moved = [dict(recs[0], Unit_Nm='Beaverhead National Forest', Loc_Nm='Beaverhead-Deerlodge National Forest'), recs[1]]
m, c = ns['_join']('US-4501', 'Custer Gallatin National Forest', ANS, moved, [[2652, 'x', 1115748, 'name']], [], *PIN, 'MT', True)
check([str(x[0]) for x in m] == ['2652'] and any(str(x[0]) == '2660' and 'R-FJ1' in x[3] for x in c), 'build: the far id now holds another forest: check row, no join')
m, c = ns['_join']('US-4501', 'Custer Gallatin National Forest', dict(ANS, no=['2660']), recs, [[2652, 'x', 1115748, 'name']], [], *PIN, 'MT', True)
check([str(x[0]) for x in m] == ['2652'], 'build: a NO on the id wins over the far join')
m, c = ns['_join']('US-4501', 'Custer Gallatin National Forest', dict(ANS, join=['Gallatin National Forest'], far=['Gallatin National Forest']), recs, [[2652, 'x', 1115748, 'name']], [], *PIN, 'MT', True)
check([str(x[0]) for x in m] == ['2652'], 'build: a join BY NAME never reaches past the box (names repeat)')

# 3. the saved answer itself, scope entry and changelog line
sys.path.insert(0, str(SCR)); import kpc_overrides as KO  # noqa: E402
ov = KO.load(str(ROOT / 'data/us-key/overrides.json'))['parks'].get('US-4501') or {}
check('2660' in [str(x) for x in ov.get('join') or []] and ov.get('far') == ['2660'] and (ov.get('fp') or {}).get('2660') == ['Gallatin National Forest', 1850408]
      and all(str((ov.get('evidence') or {}).get(k) or '').strip() for k in KR.FAR_EVIDENCE) and str(ov.get('decided_by') or '').strip(),
      "US-4501's saved answer: join + far 2660, fingerprint, decided_by, evidence")
sc = next((c for c in json.loads((ROOT / '.github/us-key-rule-scope.json').read_text())['changes'] if c.get('id') == '2026-11-19-r-fj1-far-join'), {})
check(sc.get('from') == 'ee2b6f1e9673' and sc.get('scope', {}).get('states') == ['US-MT'] and 'APPROVED' in str(sc.get('approved')),
      "scope entry 2026-11-19-r-fj1-far-join (from main's ee2b6f1e9673, Montana, approved)")
log = (ROOT / 'docs/key-rules-change.txt').read_text(encoding='utf-8')
own = next((x for x in log.splitlines() if 'branch prep/r-fj1-far-join' in x and 'US rules ee2b6f1e9673 -> ' in x), '')
check(bool(own) and 'APPROVED, decided_by KPC owner' in own and 'pins are only references' in own, "this change's changelog line quotes the owner's 11:49 AM words")

print('ALL PASS' if not FAILS else 'SOME FAILED')
sys.exit(1 if FAILS else 0)
