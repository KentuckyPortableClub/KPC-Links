#!/usr/bin/env python3
"""KPC-Links #151 readers (Nov 12 2026, KPC owner, 2026-11-12): the split alone must not make any area "due". For the same content,
every US state's and every 2-fer area's parts in kpc_area_hash (the overrides slice above all) are IDENTICAL whether
data/us-key/overrides.json is the old single file or the manifest + parts. Needs kpc_area_hash.Tree.json to follow the parts (the
E4 hunk, folded into D6's commit); without it this test SKIPs and says so. Offline: a hard-linked copy of this tree in a temp
folder gets the single file back; no network.

  python3 tests/test_overrides_area_hash_nov12.py
"""
import json, os, pathlib, shutil, socket, subprocess, sys, tempfile

def _no_net(*a, **k): raise RuntimeError('network refused in this test')
socket.socket.connect = _no_net; socket.create_connection = _no_net

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_overrides as KO  # noqa: E402
import kpc_area_hash as A  # noqa: E402

bad = 0
def check(ok, msg):
    global bad; bad += not ok; print(('PASS ' if ok else 'FAIL ') + msg)

man = json.loads((ROOT / 'data/us-key/overrides.json').read_text(encoding='utf-8'))
if not man.get('parts'):
    print('SKIP data/us-key/overrides.json is a single file here (not split)'); sys.exit(0)
if 'kpc_overrides' not in (ROOT / '.github/scripts/kpc_area_hash.py').read_text(encoding='utf-8'):
    print('NOTE kpc_area_hash.py does not follow the override parts yet: without E4-area-hash-overrides-hunk.patch (D6) every US state '
          'and every 2-fer area would lose its overrides slice once and go due')
    print('SKIP the area-hash invariant needs the E4 hunk in kpc_area_hash.py'); sys.exit(0)

tmp = pathlib.Path(tempfile.mkdtemp())
try:
    copy = tmp / 'tree'
    copy.mkdir()
    for e in ROOT.iterdir():
        if e.name != '.git': subprocess.run(['cp', '-al', str(e), str(copy / e.name)], check=True)
    whole = KO.load(ROOT / 'data/us-key/overrides.json')
    single = {k: v for k, v in whole.items() if k not in ('parts', 'parks')}; single['parks'] = whole['parks']
    for f in (copy / 'data/us-key').glob('overrides*.json'): f.unlink()   # hard links: unlink, never write through
    (copy / 'data/us-key/overrides.json').write_text(json.dumps(single, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    for kind in ('us', 'fers'):
        pa = A.Kind(A.Tree(copy), kind).parts(); pb = A.Kind(A.Tree(ROOT), kind).parts()
        diff = sorted(a for a in set(pa) | set(pb) if pa.get(a) != pb.get(a))
        withov = sum(1 for a in pa if any('overrides' in k for k in pa[a]))
        check(not diff and withov == len(pa), f'{kind}: all {len(pa)} areas have identical parts with the single file and with the split '
              f'({withov} carry an overrides part; differ: {diff[:6]})')
    # a missing part is loud in the area hash too: the slice turns unreadable for every area, never an empty slice
    gone = tmp / 'gone'; gone.mkdir()
    for e in ROOT.iterdir():
        if e.name != '.git': subprocess.run(['cp', '-al', str(e), str(gone / e.name)], check=True)
    (gone / 'data/us-key' / man['parts'][-1]).unlink()
    pg = A.Kind(A.Tree(gone), 'us').parts()
    check(all(any(k.endswith('overrides.json!unreadable') for k in pg[a]) for a in pg),
          f'a missing part ({man["parts"][-1]}) = shared:data/us-key/overrides.json!unreadable in every US area (all due, loud)')
finally:
    shutil.rmtree(tmp, ignore_errors=True)

print('ALL PASS' if not bad else f'{bad} FAILED - SOME FAILED')
sys.exit(1 if bad else 0)
