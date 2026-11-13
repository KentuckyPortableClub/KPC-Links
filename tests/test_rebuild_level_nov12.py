#!/usr/bin/env python3
"""Offline: PR rebuild levels 1-5, with body line then label then auto, and a short doc in the repo."""
import sys, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_rebuild_level as L  # noqa: E402

ok = True
def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)

check('docs and tests are level 1', L.auto_level(['tests/test_foo.py', '.github/rebuild-levels.md', 'data/outlines/README.md'], ROOT)[0] == 1)
check('a world hand file is level 2', L.auto_level(['data/outlines/hand/hand-W-CZ.h217.geojson.gz'], ROOT)[0] == 2)
check('taking a country off expected-holds is level 2', L.auto_level(['data/outlines/world-expected-holds.approved.json'], ROOT)[0] == 2)
check('shared outlines catalog is level 4', L.auto_level(['data/outlines/layers.json'], ROOT)[0] == 4)
KF = L._freeze(ROOT)
check('a world rule file itself is level 5', L.file_level('.github/scripts/kpc_world_key.py', KF, ROOT) == 5)
check('auto caps a declared named-scope rule-file change at 3 (not a full-rebuild level 5)', L.auto_level(['.github/scripts/kpc_world_key.py'], ROOT)[0] == 3)
check('a NOT_RULES script stays level 1', L.auto_level(['.github/scripts/kpc_area_hash.py', '.github/scripts/kpc_world_hand.py'], ROOT)[0] == 1)
lv, why = L.decide(['.github/scripts/kpc_world_key.py'], body='Rebuild-level: 2\n', labels='rebuild:5', root=ROOT)
check(f'body line wins over label and auto (got {lv}: {why})', lv == 2 and 'body' in why)
lv, why = L.decide(['.github/scripts/kpc_world_key.py'], body='', labels='rebuild:3', root=ROOT)
check(f'label wins over auto (got {lv})', lv == 3)
check('the short levels doc is in the PR tree', (ROOT / '.github/rebuild-levels.md').is_file()
      and 'A full rebuild should almost never happen' in (ROOT / '.github/rebuild-levels.md').read_text())
check('the PR check workflow exists', (ROOT / '.github/workflows/kpc-rebuild-level.yml').is_file())

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
