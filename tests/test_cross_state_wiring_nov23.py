#!/usr/bin/env python3
"""23 Nov 2026, owner 11:03 AM: 'Fix it' (rule W11; after job 7 and W10). A park across a state line can have a saved answer whose
record sits on a layer saved only for ANOTHER state (the Park Service legal boundaries saved for Alaska, a national forest layer
saved for Nevada ...). Such a record is in no saved copy of the park's own state nor of the states on its border, so the answer waits.
W11 lists that layer for the park's state too, in data/state-gis.json, for exactly the records its answers need (OBJECTID IN), with
the same address, so the prefix (and the saved ids) stay the same; the master step then asks the keeper for it; nothing is fetched
here. Offline. Prints PASS / FAIL, ends ALL PASS or SOME FAILED."""
import gzip, json, pathlib, re, socket, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))


def _no_net(*a, **k): raise RuntimeError('no network in tests')
socket.socket.connect = _no_net
import kpc_master_fill as F  # noqa: E402
import kpc_overrides as KO  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


sg = json.loads((ROOT / 'data/state-gis.json').read_text(encoding='utf-8'))['states']
lj = json.loads((ROOT / 'data/us-key/layers.json').read_text(encoding='utf-8'))
url_of = {k: str(v[0]).split('/query')[0].rstrip('/') for k, v in lj.items() if isinstance(v, list) and v}
pre_of = {u: k for k, u in url_of.items()}
w11 = [(st, l) for st, ls in sg.items() for l in ls if "rule W11" in str(l.get('note') or '')]
check('W11 lists 24 layer entries, across 17 states', len(w11) == 24 and len({st for st, _ in w11}) == 17)
check('each W11 entry names its records only (OBJECTID IN ...), never a whole layer', all(re.fullmatch(r'OBJECTID IN \(\d+(,\d+)*\)', l['where']) for _, l in w11))
check("each keeps the address of the layer as it is saved for the other state, so its prefix (and the saved ids) stay the same",
      all(str(l['url']).rstrip('/') in pre_of for _, l in w11))
check('no state lists one layer address twice', all(len([l for l in ls if str(l.get('url') or '').rstrip('/') == u]) <= 1
      for ls in sg.values() for u in {str(l.get('url') or '').rstrip('/') for l in ls}))
# every W11 record is a saved answer of a park of that state
ov = KO.load(ROOT / 'data/us-key/overrides.json')['parks']
st_of = {}
for f in sorted((ROOT / 'data/us-key').glob('US-??.json')):
    for ref in json.loads(f.read_text(encoding='utf-8')).get('parks') or {}: st_of.setdefault(ref, f.stem[3:])
wanted = {(st, pre_of[str(l['url']).rstrip('/')] + n) for st, l in w11 for n in re.findall(r'\d+', l['where'])}
joins = {(st_of.get(r), str(x)) for r, v in ov.items() for x in (v.get('join') or [])}
check("every W11 record is a saved answer's record of a park of that state (nothing extra is asked for)", wanted <= joins)
# the master step asks for each of them while the state's saved copy lacks the layer, and stops once it holds it
T = pathlib.Path(tempfile.mkdtemp(prefix='kpc-w11-'))
states = sorted({st for st, _ in w11})
for st in states:
    with gzip.open(T / f'US-{st}.json.gz', 'wt', encoding='utf-8') as fh: json.dump({'st': st, 'recs': [{'OBJECTID': 12345, 'Unit_Nm': 'x'}]}, fh)
new = F.new_layer_states(T, states, ROOT / 'data/us-key/layers.json', ROOT / 'data/state-gis.json')
check('the master step asks the keeper for every W11 layer of a state whose saved copy lacks it',
      all(str(l['url']).rstrip('/').lower() in [u.lower().rstrip('/') for u in new.get(st, [])] for st, l in w11))
st0, l0 = w11[0]
pre0 = pre_of[str(l0['url']).rstrip('/')]
with gzip.open(T / f'US-{st0}.json.gz', 'wt', encoding='utf-8') as fh:
    json.dump({'st': st0, 'recs': [{'OBJECTID': pre0 + re.findall(r'\d+', l0['where'])[0], 'Unit_Nm': 'x'}]}, fh)
new = F.new_layer_states(T, [st0], ROOT / 'data/us-key/layers.json', ROOT / 'data/state-gis.json')
check('once the saved copy holds it, it is no longer asked for', str(l0['url']).rstrip('/').lower() not in [u.lower().rstrip('/') for u in new.get(st0, [])])
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
