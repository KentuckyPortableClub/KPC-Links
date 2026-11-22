#!/usr/bin/env python3
"""Review M7 (KPC owner, 22 Nov 2026): which gold parks are SEALED comes only from a PRIVATE list (KPC-Store; --sealed FILE or
the path in KPC_GOLD_SEALED), never from a hash with a salt written in public code. No list, or a bad list, stops the gold steps
(exit 4). A park on no private list is TUNE (so every park of the old, publicly hashed gold set is TUNE). 'sample --kind random
--by none' draws ONE plain simple random sample (the rate), not per-method strata pooled without weights. Invented parks only."""
import json, os, pathlib, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
os.environ.pop('KPC_GOLD_SEALED', None)
import kpc_key_grade as G  # noqa: E402

bad = 0
def ck(c, m):
    global bad; bad += not c; print(('PASS ' if c else 'FAIL ') + m, flush=True)

def stops(fn):
    try: fn()
    except SystemExit as e: return e.code == 4
    return False

src = (ROOT / '.github/scripts/kpc_key_grade.py').read_text(encoding='utf-8')
ck('GOLD_SALT' not in src and 'kpc-gold-v1' not in src and 'sha256' not in src, 'no salt and no hash decide the halves in public code')
G._SEALED = None
ck(stops(lambda: G.half_of('US-0001')), 'no private list loaded: half_of stops (exit 4), never a guess')
t = pathlib.Path(tempfile.mkdtemp())
ck(stops(lambda: G.load_sealed(None)), 'no --sealed and no KPC_GOLD_SEALED: stops (exit 4)')
ck(stops(lambda: G.load_sealed(str(t / 'missing.json'))), 'a missing private list: stops')
(t / 'empty.json').write_text('{"parks": []}'); ck(stops(lambda: G.load_sealed(str(t / 'empty.json'))), 'an empty private list: stops')
(t / 'bad.json').write_text('not json'); ck(stops(lambda: G.load_sealed(str(t / 'bad.json'))), 'an unreadable private list: stops')
(t / 's.json').write_text(json.dumps({'parks': ['US-0007']}))
G.load_sealed(str(t / 's.json'))
ck(G.half_of('US-0007') == 'SEALED' and G.half_of('US-0008') == 'TUNE', 'SEALED only when the park is on the private list; any other park is TUNE')
os.environ['KPC_GOLD_SEALED'] = str(t / 's.json'); G._SEALED = None
ck(G.load_sealed() == {'US-0007'}, 'the path may come from KPC_GOLD_SEALED')
os.environ.pop('KPC_GOLD_SEALED'); G._SEALED = None
ck(stops(lambda: G.main(['gold', '--gold', str(t / 'g.json'), '--keys', str(t), '--cache', str(t), '--parkinfo', str(t)])),
   'gold without the private list stops before reading anything')
G.load_sealed(str(t / 's.json'))
g = {'parks': {'US-0007': {'area': 'US-XX', 'name': 'Invented A', 'half': 'SEALED', 'cands': []},
               'US-0009': {'area': 'US-XX', 'name': 'Invented B', 'half': 'SEALED', 'cands': []}}, 'log': []}
(t / 'g.json').write_text(json.dumps(g)); (t / 'US-XX.json').write_text('{"parks": {}}')
g['parks']['US-0009'].pop('half'); g['parks']['US-0010'] = {'area': 'US-XX', 'name': 'Invented C', 'half': 'TUNE', 'cands': []}
(t / 'g.json').write_text(json.dumps(g))
lines = G.gold_score(str(t / 'g.json'), str(t), str(t / 'nocache'), str(t))
ck(any(x.startswith('SEALED: 1 gold parks') for x in lines) and any(x.startswith('TUNE: 2 gold parks') for x in lines),
   f'N13: a row\'s own half decides first; a row with no half takes the private list, never a public hash ({[x[:30] for x in lines]})')
fact = {'US-XX': {f'US-{i:04d}': {'rows': [[i]], 'weakest': ('name' if i % 3 else 'reviewed'), 'class': 'one'} for i in range(1, 31)}}
s1 = G.sample(fact, 'random', 'seed-a', n=10, by='none')
ck(len(s1['parks']) == 10 and {p['stratum'] for p in s1['parks']} == {'random'} and s1 == G.sample(fact, 'random', 'seed-a', n=10, by='none'),
   'sample random --by none: one plain random sample of n parks, one stratum, repeatable by seed')
s2 = G.sample(fact, 'random', 'seed-a', n=10, by='method')
ck({p['stratum'] for p in s2['parks']} == {'method:name', 'method:reviewed'}, 'the per-method strata are still there when asked for')
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
