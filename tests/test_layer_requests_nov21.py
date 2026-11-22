#!/usr/bin/env python3
"""New and partial official layers, 21 Nov 2026: every row of .github/layer-requests-new.json names the bot that provides it and
stays off until the licence allows our use and robots.txt allows the path. Offline: nothing is fetched or started.
Prints PASS / FAIL lines and ends ALL PASS or SOME FAILED."""
import json, pathlib, re, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_layer_requests as L  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


r = subprocess.run([sys.executable, '-B', str(ROOT / '.github/scripts/kpc_layer_requests.py'), '--selftest'], capture_output=True, text=True)
check('the checker self-test passes (each rule refuses what it should)', r.returncode == 0 and 'SELF-TEST PASSED' in r.stdout)
doc = json.loads((ROOT / '.github/layer-requests-new.json').read_text(encoding='utf-8'))
check('the shipped list passes every rule', L.problems(doc) == [])
rows = {x['id']: x for x in doc['rows']}
check('nothing is switched on', all(x['status'] != 'on' for x in rows.values()))
check('Sweden stays on hold until its licence is confirmed', rows['W-SE|naturvardsregistret']['status'] == 'hold')
check('the two layers already on the box ask for no download', all(rows[i]['target'] == 'fix' and rows[i].get('on_box') for i in ('US-IL|sgilc', 'W-PF|h210')))
check('Lake Simcoe is not added again (already on the Canada key list)', rows['CA-ON|ON-LSRCA']['target'] == 'none')
check('the 25 world items stay hand downloads, links only', sum(1 for x in rows.values() if x['area'].startswith('W-') and x['target'] == 'hand') == 25
      and all(not x.get('service') for x in rows.values() if x['target'] == 'hand'))
check('no keeper or intake row points at a saved-copies-only host', all(L._host_rule(u) == '' for x in rows.values() if x['target'] in ('keeper', 'intake')
                                                                   for u in (x.get('service'), (x.get('intake') or {}).get('source_url')) if u))
check('no park number anywhere in the list', not re.search(r'\b[A-Z]{2}-\d{4,5}\b', json.dumps(doc)))
check('the partial-id list holds counts and layer ids only', doc['partial_id']['counts']['ID found: filled on the whole layer'] == 112
      and all(set(x) == {'layer', 'verdict', 'id_field', 'filled_pct', 'parks', 'companion'} for x in doc['partial_id']['layers']))
side, why = L.intake_sidecar(doc, 'W-GB|naturescot-pa30x30')
check('the intake bot gets no sidecar while a row is off', side is None and 'not an intake row that is on' in why)

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
