#!/usr/bin/env python3
"""26 Nov 2026 (owner's PC test, Red Lake State Forest US-4820): Minnesota's forest layer (sgmnf) also holds Wildlife Management
Areas ('Red Lake WMA', UNIT_TYPE 'Wildlife Management Area'). The layer's kind ('forest') was added to every record, so the WMA
counted as a forest and three WMA records (about 324,500 acres) joined Red Lake State Forest by name. A layer's kind is now only
a fallback: a record whose own name or own type field says a kind keeps that kind alone.
Invented layers off; reads the builder's own source. Prints PASS / FAIL and ends ALL PASS or SOME FAILED."""
import os, pathlib, sys, types
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
os.chdir(ROOT)
src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
us = types.ModuleType('kpc_us_key_kind'); us.__dict__['__file__'] = str(ROOT / '.github/scripts/kpc_us_key.py')
import io, contextlib
with contextlib.redirect_stdout(io.StringIO()):
    exec(compile(src.split('\nidx = {}\n')[0], 'kpc_us_key.py', 'exec'), us.__dict__)
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


def kind_of(nm, rt, kk):   # the builder's own line, read from its source
    line = [l.strip() for l in src.split('\n') if l.strip().startswith('k = kinds(nm) or kinds(_rt) or kk')]
    check('the state-layer reader takes the record\'s own kind first (one line in the builder)', len(line) == 1)
    return eval(line[0][4:], {'kinds': us.kinds, 'nm': nm, '_rt': rt, 'kk': kk})


park = 'Red Lake State Forest'; kp = us.kinds(park) | us.kinds('State Forest')
wma = {'OBJECTID': 'sgmnf5898', 'Unit_Nm': 'Red Lake WMA', 'Loc_Nm': '', '_k': kind_of('Red Lake WMA', 'Wildlife Management Area', {'sf'})}
check(f"a WMA record in a forest layer is a WMA, not a forest ({wma['_k']})", wma['_k'] == {'wma'})
check('Red Lake WMA no longer joins Red Lake State Forest', us.join_how(park, kp, wma, True) is None)
sf = {'OBJECTID': 'sgmnf4051', 'Unit_Nm': 'Red Lake', 'Loc_Nm': '', '_k': kind_of('Red Lake', 'State Forest', {'sf'})}
check(f"the forest's own record still joins ({us.join_how(park, kp, sf, True)})", us.join_how(park, kp, sf, True) == 'name')
bare = kind_of('Red Lake', '', {'sf'})
check('a record with no kind word and no type field still takes the layer kind', bare == {'sf'})
check('the shapefile reader: a layer kind is a fallback there too', "k = (kinds(nm) | kk) if tf else (kinds(nm) or kk)" in src)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
