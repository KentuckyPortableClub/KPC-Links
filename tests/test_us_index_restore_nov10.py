#!/usr/bin/env python3
"""Nov 10: the shape-guard index restore must write the updated row back.

Run 42797939226 put the live US-FL.json back (padus 21,993) but left the
index FL row at 5,198. The workflow step copies counts from the restored
file onto a new row dict; that row has to be assigned back onto
d['states'][st] before the index is written.

This test runs the python3 -c from kpc-us-key.yml on a fixture. It does
not import kpc_us_key or touch the real key files.
"""
import json, os, pathlib, re, subprocess, sys, tempfile

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


def restore_snippet():
    text = (ROOT / '.github/workflows/kpc-us-key.yml').read_text(encoding='utf-8')
    yaml.safe_load(text)
    m = re.search(
        r"python3 -c '(import json,sys; from pathlib import Path; st=sys.argv\[1\]; f=Path\(\"data/us-key/US-%s.json\"%st\);[^']+)' \"\$st\"",
        text,
    )
    check('workflow still parses and contains the index-restore python3 -c', bool(m))
    code = m.group(1) if m else ''
    check('snippet assigns the updated row back onto d["states"][st]',
          'd.setdefault("states", {})[st] = row' in code
          or "d.setdefault('states', {})[st] = row" in code
          or 'd.setdefault("states",{})[st]=row' in code
          or "d.setdefault('states',{})[st]=row" in code)
    return code


def test_restore_writes_index_row():
    code = restore_snippet()
    if not code:
        return
    with tempfile.TemporaryDirectory() as td:
        root = pathlib.Path(td)
        key = root / 'data' / 'us-key'
        key.mkdir(parents=True)
        (key / 'US-FL.json').write_text(json.dumps({
            'counts': {'padus': 21993, 'matched': 400},
        }) + '\n', encoding='utf-8')
        (key / 'index.json').write_text(json.dumps({
            'states': {
                'FL': {'padus': 5198, 'matched': 100, 'seconds': 60},
                'GA': {'padus': 1000},
            },
        }, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
        r = subprocess.run(['python3', '-c', code, 'FL'], cwd=root, capture_output=True, text=True)
        check('restore step exits 0', r.returncode == 0)
        if r.returncode != 0:
            print('stderr:', r.stderr)
        idx = json.loads((key / 'index.json').read_text(encoding='utf-8'))
        fl = (idx.get('states') or {}).get('FL') or {}
        check('FL padus is 21993 from the restored file, not 5198', fl.get('padus') == 21993)
        check('other FL fields from counts are copied', fl.get('matched') == 400)
        check('unrelated FL fields are kept', fl.get('seconds') == 60)
        check('other states are left alone', (idx.get('states') or {}).get('GA') == {'padus': 1000})


if __name__ == '__main__':
    test_restore_writes_index_row()
    sys.exit(0 if ok else 1)
