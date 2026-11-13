#!/usr/bin/env python3
"""Nov 13 (KPC owner): the master gate counted a Canada / US saved copy without its no-outline records, against a baseline that
was recorded with them. CA-ALL (60,479 records, 475 of them official point sites with no outline) counted as 60,004 against the
baseline 60,426, so every Canada build was held as SHORT. A US / CA copy is counted in full; a world copy keeps its filter.
Offline; prints PASS / FAIL lines."""
import gzip, json, pathlib, subprocess, sys, tempfile, shutil
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_world_hand as WH
ok = True
def check(c, msg):
    global ok; ok = ok and bool(c)
    print(('PASS ' if c else 'FAIL ') + msg)

full = [{'OBJECTID': f'x{i}', '_bb': [0, 0, 1, 1], '_r': [[[0, 0], [1, 0], [1, 1], [0, 0]]], 'src': 'CPCAD'} for i in range(8)]
points = [{'oid': f'QC-SPC:{i}', '_bb': None, '_r': [], 'src': 'QC-SPC'} for i in range(3)]      # official point sites: no outline
blob = {'recs': full + points}
check(WH.world_current_rec_count('CA-ALL.json.gz', blob, ROOT) == 11, 'CA-ALL: every record is counted, the no-outline ones too (11)')
check(WH.world_current_rec_count('CA-ALL', blob, ROOT) == 11, 'the same without the file ending')
check(WH.world_current_rec_count('US-KY.json.gz', blob, ROOT) == 11, 'a US copy is counted in full too')
check(WH.world_current_rec_count('CA-ALL.json.gz', {'recs': full}, ROOT) == 8, 'a copy that really lost records still counts fewer (8): a real short read is still caught')
check(WH.world_current_rec_count('CA-ALL.json.gz', {}, ROOT) == 0 and WH.world_current_rec_count('CA-ALL.json.gz', {'recs': 'x'}, ROOT) == 0, 'no record list = 0')
cz = WH.world_current_rec_count('W-CZ.json.gz', {'recs': full + points}, ROOT)
check(cz in (8, 11), f'a world copy keeps its own rule (the no-outline filter applies when its sources are known): {cz}')
check(all(not WH.rec_has_geometry(r) for r in points) and all(WH.rec_has_geometry(r) for r in full), 'rec_has_geometry itself is unchanged')

# the gate, end to end, on a CA-ALL-shaped copy with a baseline recorded on the full count
td = pathlib.Path(tempfile.mkdtemp())
try:
    (td / 'out').mkdir(); (td / 'cache').mkdir()
    lay = json.loads((ROOT / 'data/outlines/layers.json').read_text(encoding='utf-8'))
    lay['caches'] = {'CA-ALL': {'expected_count': 10, 'read_date': '2026-11-11', 'read_how': 'test'}}
    (td / 'out/layers.json').write_text(json.dumps(lay), encoding='utf-8')
    def gate(recs):
        for f in (td / 'cache').glob('**/*'):
            if f.is_file(): f.unlink()
        with gzip.open(td / 'cache/CA-ALL.json.gz', 'wt', encoding='utf-8') as f: json.dump({'saved': '2026-11-12', 'recs': recs}, f)
        rep = td / 'short.txt'; rep.unlink(missing_ok=True)
        r = subprocess.run([sys.executable, str(ROOT / '.github/scripts/kpc_master_cli.py'), 'gate', '--first-ok', '--root', str(td / 'out'), '--cache', str(td / 'cache'), '--report', str(rep)], capture_output=True, text=True, cwd=str(ROOT))
        return r.returncode, rep.exists() and rep.read_text().strip(), r.stdout + r.stderr
    rc, rep, out = gate(full + points)
    check(rc == 0 and not rep, f'gate: 11 records (3 with no outline) against a baseline of 10 passes (exit {rc})')
    rc, rep, out = gate(full)
    check(rc == 7 and rep == 'CA-ALL' and 'SHORT' in out, f'gate: 8 records against a baseline of 10 is still SHORT and held (exit {rc})')
finally:
    shutil.rmtree(td, ignore_errors=True)

real = json.loads((ROOT / 'data/outlines/layers.json').read_text(encoding='utf-8'))['caches'].get('CA-ALL') or {}
check(real.get('expected_count') == 60426, f"the recorded CA-ALL baseline is untouched ({real.get('expected_count')})")
print('ALL PASS' if ok else 'FAILED')
sys.exit(0 if ok else 1)
