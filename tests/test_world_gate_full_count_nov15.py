#!/usr/bin/env python3
"""The master gate counts a world saved copy the way its baseline was recorded (KPC owner, 2026-11-15).

Run 43803039057 (world key, store mode, GB JP) held both copies as SHORT although nothing was missing: the baselines in
data/outlines/layers.json are FULL record counts (W-GB 58931, W-JP 30425: 'live key file counts.areas'), but the gate counted only
the current-layer records with geometry (W-GB 56446 = 58931 - 2484 records of the 3 dropped Forestry England layers - 1 without
geometry; W-JP 30423 = 30425 - 2 without geometry). Made-up copies with the REAL composition of the two copies (the real labels,
the real numbers), run through `kpc_master_cli.py gate` as the world workflow calls it:
- complete GB / JP copies pass (like with like); the same copies one record short are SHORT and moved aside;
- a copy that lost a record of a current layer is SHORT even when the dropped-layer records are all there;
- W-AU's current-layer baseline is still compared with the current-layer count (a dropped-layer record cannot hide a lost one).
Offline, temp folders only."""
import gzip, json, os, pathlib, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
SC = ROOT / '.github/scripts'
sys.path.insert(0, str(SC))
import kpc_world_hand as WH  # noqa: E402
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


caches = json.load(open(ROOT / 'data/outlines/layers.json', encoding='utf-8'))['caches']
check(f"the real baselines: W-GB {caches['W-GB']['expected_count']}, W-JP {caches['W-JP']['expected_count']}, both full counts (counts.areas)",
      caches['W-GB']['expected_count'] == 58931 and caches['W-JP']['expected_count'] == 30425
      and all(caches[k]['read_how'].startswith('live key file counts.areas') for k in ('W-GB', 'W-JP')))
G = {'_bb': [0, 0, 1, 1], '_r': [[0, 0], [1, 0], [1, 1]]}
NOG = {'_bb': None, '_r': []}
cur_gb, drop_gb = WH._world_label_sets('GB', ROOT)
cur_jp, _ = WH._world_label_sets('JP', ROOT)
check(f'GB: the three layers the key no longer reads are the dropped ones ({sorted(drop_gb)})', {'FE_Ownership_160726', 'Forest_Blocks', 'INV_BLKDATA'} <= set(drop_gb))
cg, cj = sorted(cur_gb)[0], sorted(cur_jp)[0]


def gb(n_cur=56446, fe=1653, fb=481, inv=350, nog=1):   # the real W-GB copy: 56446 + 1653 + 481 + 350 + 1 (FE, no geometry) = 58931
    return ([dict(G, src=cg) for _ in range(n_cur)] + [dict(G, src='FE_Ownership_160726') for _ in range(fe)] + [dict(NOG, src='FE_Ownership_160726') for _ in range(nog)]
            + [dict(G, src='Forest_Blocks') for _ in range(fb)] + [dict(G, src='INV_BLKDATA') for _ in range(inv)])


def jp(n=30423, nog=2): return [dict(G, src=cj) for _ in range(n)] + [dict(NOG, src=cj) for _ in range(nog)]


def gate(copies):
    """{stem: recs} -> (exit code, stems moved aside, output), the gate run as the world workflow runs it."""
    with tempfile.TemporaryDirectory() as t:
        t = pathlib.Path(t)
        for stem, recs in copies.items():
            with gzip.open(t / f'{stem}.json.gz', 'wt') as f: json.dump({'cc': stem[2:], 'saved': '2026-11-04', 'recs': recs}, f)
        r = subprocess.run([sys.executable, str(SC / 'kpc_master_cli.py'), 'gate', '--cache', str(t), '--report', str(t / 'short.txt'), '--allow-trimmed',
                            '--approved', str(ROOT / 'data/outlines/world-baselines.approved.json')], cwd=ROOT, capture_output=True, text=True)
        short = (t / 'short.txt').read_text().split() if (t / 'short.txt').exists() else []
        return r.returncode, short, r.stdout + r.stderr


b = {'recs': gb()}
check(f"the GB fixture has the real numbers: {len(b['recs'])} records, current-layer count {WH.world_current_rec_count('W-GB.json.gz', b, ROOT)}",
      len(b['recs']) == 58931 and WH.world_current_rec_count('W-GB.json.gz', b, ROOT) == 56446)
check(f"the JP fixture has the real numbers: 30425 records, current-layer count {WH.world_current_rec_count('W-JP.json.gz', {'recs': jp()}, ROOT)}",
      WH.world_current_rec_count('W-JP.json.gz', {'recs': jp()}, ROOT) == 30423)
rc, short, out = gate({'W-GB': gb(), 'W-JP': jp()})
check(f'complete W-GB (58931) and W-JP (30425) pass the gate: exit {rc}, moved aside {short}', rc == 0 and short == [] and 'SHORT' not in out)
check('the gate says why it counted in full (2485 records from dropped layers or with no geometry; 2 for JP)',
      'W-GB: counted in full like its baseline (58931 records; 2485 of them' in out and 'W-JP: counted in full like its baseline (30425 records; 2 of them' in out)
rc, short, out = gate({'W-GB': gb(fb=480), 'W-JP': jp(nog=1)})
check(f'one record fewer (58930 / 30424) = SHORT, both moved aside, exit 7: {short}', rc == 7 and short == ['W-GB', 'W-JP'] and 'read 58930 of 58931' in out and 'read 30424 of 30425' in out)
rc, short, out = gate({'W-GB': gb(n_cur=56000)})
check(f'a copy that lost 446 current-layer records is SHORT: {short}', rc == 7 and short == ['W-GB'] and 'read 58485 of 58931' in out)
# W-AU: its baseline is the current-layer count (read_how 'current-layer count ...', #135): still compared like with like
au = caches['W-AU']
check(f"W-AU's baseline is a current-layer count ({au['expected_count']})", au['read_how'].startswith('current-layer count'))
cur_au, drop_au = WH._world_label_sets('AU', ROOT)
ca, da = sorted(cur_au)[0], sorted(drop_au)[0]
n = au['expected_count']
rc, short, out = gate({'W-AU': [dict(G, src=ca) for _ in range(n)] + [dict(G, src=da) for _ in range(5)]})
check(f'W-AU complete (current {n} + 5 dropped-layer records) passes', rc == 0 and short == [])
rc, short, out = gate({'W-AU': [dict(G, src=ca) for _ in range(n - 1)] + [dict(G, src=da) for _ in range(5)]})
check(f'W-AU one current-layer record short is SHORT although the total is higher (dropped records do not count): {short}', rc == 7 and short == ['W-AU'])
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
