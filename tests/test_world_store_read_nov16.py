#!/usr/bin/env python3
"""World store run reads the world parks (KPC owner, 2026-11-16). Offline: no network. Test only; no rule file is touched.
1 store_ids: a US / Canadian park keeps its key ids; a world park's records are looked up as '<area>:<layer>:<id>', the way the
  world store files them (a test run of Belgium read 0 of 648 parks before this)
2 install() hands a world store run its own saved_world (read from the store, as saved_ca); a US / Canada run keeps the bot's
3 the lazy loader re-reads a world park with the same keys (no 'store changed during the run' on first use)"""
import os, pathlib, re, sys, types
HERE = pathlib.Path(__file__).resolve().parent.parent
S = HERE / '.github/scripts'
sys.path.insert(0, str(S))
os.chdir(HERE)
try: import cv2  # noqa: F401
except Exception: sys.modules['cv2'] = types.ModuleType('cv2')  # noqa: BLE001
import kpc_fers_store as FS
ok = True


def check(c, msg):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg); ok = ok and bool(c)


# 1
check(FS.store_ids({'st': 'US-RI', 'ids': [57154, 3644]}) == [57154, 3644], 'a US park keeps its key ids')
check(FS.store_ids({'st': 'CA-AB', 'ids': ['abc1']}) == ['abc1'], 'a Canadian park keeps its key ids')
w = {'st': 'W-BE', 'ids': [352, 746], 'm': [[352, 'De Maten', 'EEA Natura 2000', 'pin inside'], [746, 'De Maten', 'EEA Natura 2000', 'pin inside']]}
check(FS.store_ids(w) == ['W-BE:EEA Natura 2000:352', 'W-BE:EEA Natura 2000:746'], 'a world park is looked up as <area>:<layer>:<id>')
w2 = {'st': 'W-BE', 'ids': [275], 'm': [[275, 'X', 'BE: Réserves naturelles domaniales (approved layer 2)', 'name']]}
check(FS.store_ids(w2) == ['W-BE:BE: Réserves naturelles domaniales (approved layer 2):275'], 'a layer name with a colon in it is kept whole')

# 2 and 3 (source checks: install() needs a whole store to run)
src = (S / 'kpc_fers_store.py').read_text(encoding='utf-8')
check(re.search(r"def saved_world\(parks\):[^\n]*\n\s+w = \{r: p for r, p in parks.items\(\) if str\(p.get\('st', ''\)\).startswith\('W-'\)\}\n\s+return store_download\(KF, st, w, list\(w\), budget\)\[0\]", src) is not None,
      'a world store run has its own saved_world, read from the store')
check(re.search(r"\n    if world_on: KF\.saved_world = saved_world\n", src) is not None, 'install() hands it to the bot only when the run is a world store run')
check("ids = store_ids(p)" in src and "store_ids(parks[ref])" in src, 'the first read and the lazy re-read use the same record keys')
check("ids = list(p['ids'])" not in src.split('def store_download', 1)[1].split('\ndef ', 1)[0], 'store_download no longer looks a world park up by its bare ids')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
