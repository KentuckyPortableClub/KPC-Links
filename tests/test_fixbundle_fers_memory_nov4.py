"""Nov 4 PM fix bundle item 4: pass 5's water re-check streams the spots by place and drops far cached tiles before each spot
(the Southeast worker died near 12.5 GB because pass 5 kept every water tile), and the caches drop when memory passes
KPC_FERS_MEM_MB. Run: python3 -B tests/test_fixbundle_fers_memory_nov4.py"""
import ast, os, pathlib, sys
R = pathlib.Path(__file__).resolve().parents[1]; S = R / '.github/scripts'
sys.path.insert(0, str(S))
ok = True
def check(what, got, want):
    global ok
    good = got == want; ok &= good
    print(('PASS ' if good else 'FAIL ') + f'{what}: got {got!r}' + ('' if good else f', want {want!r}'))
src = open(S / 'kpc_fers.py', encoding='utf-8').read()
p5 = src[src.index('elif PASS == 5:'):]; p5 = p5[:p5.index("mark(f'water re-check of")]
check('pass 5: a far-tile drop before every water check (first look + the end re-check)', p5.count('evict(sbox(x))\n                WATER_MARK.clear()') + p5.count('evict(sbox(x))\n            WATER_MARK.clear()'), 2)
check('pass 5: a far-tile drop before the same-land access pins', 'evict(sbox(x))\n                try: x[\'access\'] = nearest_access' in p5, True)
check('pass 5: spots sorted saved-first, then by place', "cand.sort(key=lambda x: (0 if _saved_all(x) else 1,) + _cell(x))" in p5, True)
check('pass 5 reports the memory', "n['memory (MB now / cap; caches dropped for memory)']" in src, True)
os.environ.setdefault('PASS', '5')
try: import cv2  # noqa: F401
except ImportError:   # evict / rss_mb use no OpenCV: a stand-in lets the box test run without it (CI has the real one)
    import types; sys.modules['cv2'] = types.ModuleType('cv2'); print('NOTE cv2 not installed here: a stand-in module is used')
import kpc_fers as K
check('rss_mb reads this process (> 0 MB on Linux)', K.rss_mb() > 0, True)
check('default memory cap 5000 MB', K.MEM_MB, 5000.0)
# fake caches: 20 water tiles near (0.1-degree keys around lon -82, lat 28) and 20 far ones; small counts never evict...
def fill():
    K.NHDC.clear()
    for i in range(20):
        K.NHDC[(-820 + i, 280)] = [['wb', []]]; K.NHDC[(-820 + i, 280, 'd')] = 'saved'
        K.NHDC[(-700 + i, 400)] = [['wb', []]]; K.NHDC[(-700 + i, 400, 'd')] = 'saved'
fill(); K.MEM_MB = 0; K.evict([-82.0, 28.0, -81.95, 28.05])
check('under the tile count and no memory cap: nothing dropped (as before)', len(K.NHDC), 80)
fill(); K.MEM_MB = 1; K.evict([-82.0, 28.0, -81.95, 28.05])
left = {k[:2] for k in K.NHDC}
check('over the memory cap: only the tiles under the spot box stay', sorted(left), [(-820, 280)])
check('the memory drop is counted', K.EVICT_N['memory'] >= 1, True)
fill(); K.MEM_MB = 0; old = K.CACHE_TILES; K.CACHE_TILES = 10; K.evict([-82.0, 28.0, -81.95, 28.05])
check('over the tile count: the far tiles (12 degrees away) dropped, the near ones (1 degree) kept', (any(k[0] < -800 for k in K.NHDC), any(k[0] > -800 for k in K.NHDC)), (True, False))
K.CACHE_TILES = old
ast.parse(src)
print('ALL PASS' if ok else 'SOME FAILED'); sys.exit(0 if ok else 1)
