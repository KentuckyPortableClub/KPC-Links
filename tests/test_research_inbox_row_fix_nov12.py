"""Nov 12 2026: a --retry run must not stop when an owner short-list (brandon_flip) entry has no 'row'
(6 such entries on main: US-10823, US-12978, US-12981, CA-4773, CA-4779, CA-4780). Offline, temp folder only."""
import json, pathlib, sys, tempfile
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / '.github/scripts'))
import kpc_research_inbox as RI  # noqa: E402
bad = []
def check(c, m):
    print(('ok   ' if c else 'FAIL ') + m)
    if not c: bad.append(m)
t = pathlib.Path(tempfile.mkdtemp()); inbox = t / 'data/research-inbox'; inbox.mkdir(parents=True); (t / 'kd').mkdir()
flip = {'US-10823': {'status': 'SOLUTION FOUND vs earlier NO', 'record_id': '42', 'record_name': 'Example Park', 'earlier_no': {'date': '2026-10-22', 'decision': 'NO to 41'}}}
json.dump({'about': 'test', 'parks': {}, 'brandon_flip': flip}, open(inbox / 'needs-another-look.json', 'w'))
before = (inbox / 'needs-another-look.json').read_text()
try:
    RI.run([], root=t, kpcdata=t / 'kd', cache=t / 'cache', offline=True, retry=True, ledger={}); err = ''
except Exception as e:  # noqa: BLE001
    err = f'{type(e).__name__}: {e}'
check(not err, f'a --retry run with a brandon_flip entry that has no row completes ({err or "no error"})')
bl = (inbox / 'brandon-list.md').read_text(encoding='utf-8') if (inbox / 'brandon-list.md').exists() else ''
check('**US-10823**' in bl and 'found record 42' in bl, 'the owner short list is written and still names the entry')
nal = json.load(open(inbox / 'needs-another-look.json'))
check((inbox / 'needs-another-look.json').read_text() != before and 'US-10823' in (nal.get('brandon_flip') or {}), 'needs-another-look.json is rewritten by the run and keeps the entry')
print('ALL PASS' if not bad else f'{len(bad)} FAILED'); sys.exit(1 if bad else 0)
