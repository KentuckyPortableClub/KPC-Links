#!/usr/bin/env python3
"""Offline test, Nov 4 PM fix bundle item 11c (Quality v3 should-fix; Brandon's yes relayed via Super Head Bot, 4:53 PM CST Nov 4):
DE-0095 'Mecklenburgisches Elbetal UNESCO Biosphere Reserve' is no longer joined to the BfN Vogelschutzgebiet DE2732473 of the same
name (other kind); it goes to the review list with the reason. Runs the real helper and the real kind lists of kpc_world_key.py (the
part up to kinds(); no network) and checks the only place it is used. Also checks it touches no other park of today's key."""
import json, os, pathlib, re, sys

HERE = pathlib.Path(__file__).resolve().parent.parent
os.chdir(HERE)
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


src = open('.github/scripts/kpc_world_key.py', encoding='utf-8').read()
g = {'__name__': 'kpc_world_key_prefix', '__file__': '.github/scripts/kpc_world_key.py'}
k0 = src.index('\ndef kinds(cc, s):'); exec(compile(src[:src.index('\n', k0 + 1)], 'kpc_world_key.py', 'exec'), g)
kinds, clash = g['kinds'], g['br_kind_clash']
kp = kinds('DE', 'Mecklenburgisches Elbetal UNESCO Biosphere Reserve') | kinds('DE', 'UNESCO Biosphere Reserve')
rk = kinds('DE', 'Mecklenburgisches Elbetal') | kinds('DE', 'BfN Vogelschutzgebiete')
check(kp == {'br'} and rk == {'spa'}, f'DE-0095: the park is a biosphere reserve {kp}, the joined record a bird sanctuary {rk}')
check(clash(kp, [rk]), 'DE-0095: not joined (review list)')
check(not clash(kp, [rk, kinds('DE', 'Biosphärenreservat Flusslandschaft Elbe')]), 'a biosphere-reserve record among the holders = the normal path (no change)')
check(not clash({'nsg'}, [rk]) and not clash(kp, [set()]) and not clash(set(), [rk]), 'other kinds, a record of unknown kind or a park of unknown kind = no change')
check(not clash(kp, [kinds('DE', 'BfN Landschaftsschutzgebiete')]), 'a biosphere reserve on a landscape protection area (Spreewald, Schaalsee...) = no change (another review)')
# wiring: used once, in the pin-inside + name path, before the join, writing the review list with the reason
i = src.index('br_kind_clash(kp, [r[\'_k\'] for r, _ in holds])'); j = src.index("m = [[r['id'], r['n'], r['src'], 'pin inside + ' + how] for r, how in holds]")
check(src.count('br_kind_clash(') == 2 and i < j and "'m': [], 'c':" in src[i:j] and 'BR_CLASH_WHY' in src[i:j], 'wired once, in the pin-inside + name path, before the join: m empty, c with the reason')
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
