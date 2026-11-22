#!/usr/bin/env python3
"""D6 leftovers (20 Nov). The last two per-area tables leave the rule scripts.

EASEMENT_RECHECK_STATES is in data/us-key/area-tables.json. The North Macedonia
switch-gated layer is in data/world-key/area-tables.json (SRC_SWITCH) and is
appended only when KPC_MK_LAYER_93 is on (off by default). The builders are
not imported (they run on import). Prefixes are exec'd the same way as
test_area_tables_nov12.py. No production build. Proof: in-memory tables
match main, and the new table parts are attributed only to NY and MK.
Counts only; no park names.
"""
import ast, copy, json, os, pathlib, subprocess, sys, tempfile, types

ROOT = pathlib.Path(__file__).resolve().parent.parent
S = ROOT / '.github/scripts'
sys.path.insert(0, str(S))

import kpc_area_hash as AH  # noqa: E402
import kpc_preflight as PF  # noqa: E402
# kpc_key_freeze is run as a subprocess so this test never imports a builder.

FAILS = []
# The base is the commit just before D6 (bfe61e69) landed, so the check still
# means 'new versus before D6' after D6 is on main.
MAIN = 'bfe61e691~1'


def check(ok, what):
    print(('PASS ' if ok else 'FAIL ') + what, flush=True)
    if not ok:
        FAILS.append(what)


def world_ns(src, env=None):
    g = {'__name__': 'kpc_world_key_prefix', '__file__': str(S / 'kpc_world_key.py')}
    saved = {k: os.environ.get(k) for k in ('KPC_MK_LAYER_93',)}
    if env:
        os.environ.update(env)
    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        exec(compile(src[:src.index('\nfor cc in COUNTRIES:')], 'kpc_world_key.py', 'exec'), g)
    finally:
        os.chdir(cwd)
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return g


def us_ns(src):
    m = types.ModuleType('kpc_us_key_prefix')
    m.__file__ = str(S / 'kpc_us_key.py')
    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        exec(compile(src.split('\nidx = {}\n')[0], 'kpc_us_key.py', 'exec'), m.__dict__)
    finally:
        os.chdir(cwd)
    return m.__dict__


# 1. The two leftover assignments are gone.
def scan(src):
    out = []
    areas = set(AH.US_ALL) | set(AH.Kind(AH.Tree(ROOT), 'world').areas)

    def is_area(n):
        if not (isinstance(n, ast.Constant) and isinstance(n.value, str)):
            return False
        v = n.value[3:] if n.value.startswith(('US-', 'CA-', 'W-')) else n.value
        return v in areas and bool(__import__('re').fullmatch(r'(?:(?:US|CA|W)-)?[A-Z]{2}', n.value))

    for node in ast.walk(ast.parse(src)):
        if not isinstance(node, (ast.Assign, ast.AugAssign, ast.AnnAssign)) or getattr(node, 'value', None) is None:
            continue
        tg = node.targets if isinstance(node, ast.Assign) else [node.target]
        why = [f'assigns the area key {ast.unparse(t.slice)}' for t in tg if isinstance(t, ast.Subscript) and is_area(t.slice)]
        st = [node.value]
        while st and not why:
            x = st.pop()
            if isinstance(x, (ast.Lambda, ast.FunctionDef)):
                continue
            if isinstance(x, ast.Dict) and any(k is not None and is_area(k) for k in x.keys):
                why.append('a dict keyed by area codes')
            elif isinstance(x, (ast.Set, ast.List, ast.Tuple)) and x.elts and all(is_area(e) for e in x.elts):
                why.append('a set / list of area codes')
            st.extend(ast.iter_child_nodes(x))
        if why:
            out.append((node.lineno, ','.join(ast.unparse(t) for t in tg)[:40], why[0]))
    return out


us_src = (S / 'kpc_us_key.py').read_text(encoding='utf-8')
w_src = (S / 'kpc_world_key.py').read_text(encoding='utf-8')
left_us = [(ln, tg, why) for ln, tg, why in scan(us_src)
           if tg not in {'DES', 'SZ_US'}]
left_w = scan(w_src)
check(not any(tg == 'EASEMENT_RECHECK_STATES' for _, tg, _ in left_us),
      f'EASEMENT_RECHECK_STATES is not a leftover assignment ({left_us[:3]})')
check(not any("SRC['MK']" in tg or 'SRC["MK"]' in tg for _, tg, _ in left_w),
      f"SRC['MK'] is not assigned as a leftover ({left_w[:3]})")

# 2. In-memory values match what main had. Prefix only: no key files are written.
os.environ.pop('KPC_MK_LAYER_93', None)
U = us_ns(us_src)
W = world_ns(w_src)
check(U['EASEMENT_RECHECK_STATES'] == {'NY'},
      f"EASEMENT_RECHECK_STATES is still {{NY}} ({U['EASEMENT_RECHECK_STATES']})")
mk_urls = [str(s[2]).rstrip('/').lower() for s in W['SRC'].get('MK') or []]
check(W['MK93'].lower() not in mk_urls,
      'with the switch off (default), SRC[MK] does not gain the extra layer')
check(W['MK94'].lower() in mk_urls,
      'with the switch off, the sheet layer already on main is still present')

W_on = world_ns(w_src, env={'KPC_MK_LAYER_93': '1'})
on_rows = [[x[0], x[1], x[2]] for x in W_on['SRC']['MK']]
on_urls = [str(x[2]).rstrip('/').lower() for x in on_rows]
check(W_on['MK93'].lower() in on_urls and W_on['MK94'].lower() in on_urls,
      'with the switch on, SRC[MK] has both the sheet layer and the extra layer')
extra = [x for x in on_rows if str(x[2]).rstrip('/').lower() == W_on['MK93'].lower()]
check(extra == [['Заштитени подрачја (areas, MapServer/93)', 'arcgis', W_on['MK93']]],
      f'the extra row matches the one the code used to append ({extra})')

# 3. Fail closed if a moved table is missing.
def load_us(doc):
    p = pathlib.Path(tempfile.mkdtemp(prefix='kpc-d6-')) / 'area-tables.json'
    p.write_text(json.dumps(doc), encoding='utf-8')
    try:
        U['area_tables'](p)
        return 'loaded'
    except SystemExit as e:
        return str(e)


def load_w(doc):
    p = pathlib.Path(tempfile.mkdtemp(prefix='kpc-d6-')) / 'area-tables.json'
    p.write_text(json.dumps(doc), encoding='utf-8')
    try:
        W['area_tables'](p)
        return 'loaded'
    except SystemExit as e:
        return str(e)


uj = json.loads((ROOT / 'data/us-key/area-tables.json').read_text(encoding='utf-8'))
wj = json.loads((ROOT / 'data/world-key/area-tables.json').read_text(encoding='utf-8'))
u_miss = copy.deepcopy(uj)
u_miss.pop('EASEMENT_RECHECK_STATES')
w_miss = copy.deepcopy(wj)
w_miss.pop('SRC_SWITCH')
check('missing or empty' in load_us(u_miss) and load_us(uj) == 'loaded',
      'US tables fail closed if EASEMENT_RECHECK_STATES is missing')
check('missing or empty' in load_w(w_miss) and load_w(wj) == 'loaded',
      'world tables fail closed if SRC_SWITCH is missing')

# 4. Rules fingerprints: US and world moved from the pre-D6 hashes; Canada equals
# the newest declared changelog line (so a later declared Canada move is not a leftovers failure); 2-fers stay put.
def rules(kind):
    return subprocess.check_output(
        [sys.executable, str(S / 'kpc_key_freeze.py'), 'rules', kind],
        cwd=str(ROOT), text=True,
    ).strip()


us_now, ca_now, wo_now, fe_now = rules('us-key'), rules('ca-key'), rules('world-key'), rules('fers')
check(us_now != '7e4883bfbb45', f'US rules hash moved from 7e4883bfbb45 to {us_now}')
check(wo_now != 'b1f23bf0deea', f'world rules hash moved from b1f23bf0deea to {wo_now}')
check(ca_now == PF.newest_hash('ca-key'), f'Canada rules hash equals the newest declared changelog line ({ca_now})')
check(fe_now == '6a9d67ea4100', f'2-fer rules hash is unchanged ({fe_now})')
print(f'HASHES us={us_now} ca={ca_now} world={wo_now} fers={fe_now}', flush=True)

# 5. New table parts are attributed only to NY (US) and MK (world).
# The shared hook and the scope file are in every area's hash, so every
# area hash of that kind may also move; that is reported as a count.
_, p_main_us = AH.compute(str(ROOT), MAIN, 'us')
_, p_now_us = AH.compute(str(ROOT), None, 'us')
d_us = AH.diff_parts(p_main_us, p_now_us)
ease = 'data/us-key/area-tables.json:EASEMENT_RECHECK_STATES'
ease_added = [a for a, whys in d_us.items() if any(ease in w and 'added' in w for w in whys)]
ease_other = [a for a, whys in d_us.items() if any(ease in w and 'added' not in w for w in whys)]
check(ease_added == ['NY'] and not ease_other,
      f'the new EASEMENT table part is attributed only to NY (added={ease_added}, other={ease_other})')

_, p_main_w = AH.compute(str(ROOT), MAIN, 'world')
_, p_now_w = AH.compute(str(ROOT), None, 'world')
d_w = AH.diff_parts(p_main_w, p_now_w)
swk = 'data/world-key/area-tables.json:SRC_SWITCH'
sw_added = [a for a, whys in d_w.items() if any(swk in w and 'added' in w for w in whys)]
sw_other = [a for a, whys in d_w.items() if any(swk in w and 'added' not in w for w in whys)]
check(sw_added == ['MK'] and not sw_other,
      f'the new SRC_SWITCH table part is attributed only to MK (added={sw_added}, other={sw_other})')

hs_main_us, _ = AH.compute(str(ROOT), MAIN, 'us')
hs_now_us, _ = AH.compute(str(ROOT), None, 'us')
moved_us = sorted(a for a in hs_main_us if hs_main_us[a] != hs_now_us.get(a))
hs_main_w, _ = AH.compute(str(ROOT), MAIN, 'world')
hs_now_w, _ = AH.compute(str(ROOT), None, 'world')
moved_w = sorted(a for a in hs_main_w if hs_main_w[a] != hs_now_w.get(a))
print(f'AREA HASHES moved US {len(moved_us)}/{len(hs_main_us)} world {len(moved_w)}/{len(hs_main_w)}', flush=True)
check('NY' in moved_us, f'NY area hash moved (n={len(moved_us)})')
check('MK' in moved_w, f'MK area hash moved (n={len(moved_w)})')

# No-output proof (predicted, no production build): with the switch off, the
# in-memory tables the builder uses are the same as on main, so today's saved
# keys would stay byte-identical. The only value that would change is SRC[MK]
# when the switch is turned on, and that switch stays off.
check(U['EASEMENT_RECHECK_STATES'] == {'NY'} and W['MK93'].lower() not in mk_urls,
      'no-output proof: default in-memory tables match main (switch off)')

if FAILS:
    print(f'{len(FAILS)} FAIL', flush=True)
    sys.exit(1)
print('OK', flush=True)
