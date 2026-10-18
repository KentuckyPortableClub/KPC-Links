"""One review issue for the US answer key (label us-answer-key): a table of every state, the ones needing the most checking first,
each linking to its review page data/us-key/review/US-XX.md."""
import json, subprocess
LABEL = 'us-answer-key'
idx = json.load(open('data/us-key/index.json'))['states']
def gh(*a, inp=None):
    r = subprocess.run(['gh', *a], input=inp, text=True, capture_output=True)
    if r.returncode: print('gh error:', r.stderr.strip())
    return r.stdout
URL = 'https://github.com/KentuckyPortableClub/KPC-Links/blob/main/data/us-key/review/US-%s.md'
rows = sorted(idx.items(), key=lambda kv: -((kv[1]['check'] + kv[1]['none']) / max(1, kv[1]['parks'])))
tot = {k: sum(v[k] for v in idx.values()) for k in ('parks', 'matched', 'check', 'none')}
L = ['Every state but Kentucky (Kentucky has its own list, issue label ky-answer-key). Built by `.github/scripts/kpc_us_key.py` from USGS PAD-US federal + state land and POTA.',
     'A park is **joined** only when the name AND the kind of place match (WMA to WMA, state park to state park). Everything else is only listed for a person to check.', '',
     f"**All states: {tot['matched']:,} of {tot['parks']:,} parks joined · {tot['check']:,} to check · {tot['none']:,} nothing found**", '',
     '| State | Parks | Joined | To check | Nothing found | % joined |', '|---|---:|---:|---:|---:|---:|']
L += [f"| [{st}]({URL % st}) | {c['parks']} | {c['matched']} | {c['check']} | {c['none']} | {round(100 * c['matched'] / max(1, c['parks']))}% |" for st, c in rows]
body = '\n'.join(L)
gh('label', 'create', LABEL, '--color', 'D5A63A', '--description', 'US park ↔ official land answer key', '--force')
f = json.loads(gh('issue', 'list', '--label', LABEL, '--state', 'open', '--json', 'number', '--limit', '1') or '[]')
t = 'US boundary answer key: review list (every state but Kentucky)'
if f: n = str(f[0]['number']); gh('issue', 'edit', n, '--title', t, '--body-file', '-', inp=body)
else: n = gh('issue', 'create', '--title', t, '--label', LABEL, '--body-file', '-', inp=body).strip().rsplit('/', 1)[-1]
print(f'::notice title=US answer key issue::#{n}')
