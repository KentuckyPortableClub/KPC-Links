"""Keep the 'Kentucky boundary answer key' review issue up to date (label ky-answer-key).
Body = the review list from data/ky-answer-key.json; what changed this run = a comment (GitHub emails watchers)."""
import json, subprocess, sys
LABEL = 'ky-answer-key'
res = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
d = json.load(open('data/ky-answer-key.json'))
P = d['parks']
def gh(*a, inp=None):
    r = subprocess.run(['gh', *a], input=inp, text=True, capture_output=True)
    if r.returncode: print('gh error:', r.stderr.strip())
    return r.stdout
NM = {'bstate': 'State Parks file', 'bwma': 'WMA file', 'bsnp': 'Nature Preserves file', 'bsna': 'Natural Areas file', 'bdbnf': 'DBNF line',
      'bnps': 'NPS file', 'bwild': 'Wild Rivers file', 'bwilder': 'Wilderness file', 'bfws': 'USFWS file', 'bkpc': 'KPC-drawn'}
pieces = lambda p: sum(t[4] if len(t) > 4 else 1 for t in p['tracts'])
L = [f"Built {d['updated']} by `.github/scripts/kpc_ky_key.js` from the Kentucky outline files, using the same matching rules as the map tools. "
     "Full list: `data/ky-answer-key.json`. Updated every Monday and whenever an outline file or kpc-ky-data.json changes.", '',
     f"**{len(P)} POTA parks** · {sum(1 for p in P.values() if p['tracts'])} have an outline · {sum(1 for p in P.values() if pieces(p) > 1)} are in 2+ pieces (tracts) · "
     f"{len(d['missing'])} have none · {len(d['nonum'])} outlines are government land with no park number · {len(d['kffonly'])} are KFF only", '']
L += ['### ⚠ No outline at all', *(f"- {r} {P[r]['n']}" for r in d['missing']), '']
weak = [r for r, p in P.items() if p['tracts'] and all(t[3] == 'pin' for t in p['tracts'])]
if weak: L += ['### ⚠ Matched only because the POTA pin is inside (check the name)', *(f"- {r} {P[r]['n']} → {', '.join(t[1] for t in P[r]['tracts'])}" for r in weak), '']
alias = [(r, t) for r, p in P.items() for t in p['tracts'] if t[3] == 'alias']
L += ['<details><summary>Matched by KPC\'s alias list (' + str(len(alias)) + ')</summary>', '', *(f"- {r} {P[r]['n']} ← {t[1]} ({NM.get(t[0], t[0])})" for r, t in alias), '</details>', '']
L += ['<details><summary>Government land with no POTA / KFF number (' + str(len(d['nonum'])) + ')</summary>', '',
      *(f"- {x[1]} ({NM.get(x[0], x[0])}, ~{x[2]:,} acres)" + (f" · POTA pin inside: {', '.join(x[3])}" if x[3] else '') + (f" · KFF inside: {', '.join(x[4])}" if x[4] else '') + (f" · SOTA: {', '.join(x[5])}" if x[5] else '') for x in d['nonum']), '</details>', '']
L += ['<details><summary>KFF reference, no POTA number (' + str(len(d['kffonly'])) + ')</summary>', '', *(f"- {x[1]} → {', '.join(x[3])}" for x in d['kffonly']), '</details>', '']
many = sorted(((pieces(p), r) for r, p in P.items() if pieces(p) > 1), reverse=True)[:25]
L += ['<details><summary>Most pieces (tracts)</summary>', '', *(f"- {r} {P[r]['n']}: {n} pieces in {len(P[r]['tracts'])} outline(s)" for n, r in many), '</details>']
body = '\n'.join(L)
gh('label', 'create', LABEL, '--color', 'D5A63A', '--description', 'Kentucky park ↔ outline answer key (weekly)', '--force')
found = json.loads(gh('issue', 'list', '--label', LABEL, '--state', 'open', '--json', 'number', '--limit', '1') or '[]')
title = 'Kentucky boundary answer key: review list'
if found:
    num = str(found[0]['number']); gh('issue', 'edit', num, '--title', title, '--body-file', '-', inp=body)
else:
    num = gh('issue', 'create', '--title', title, '--label', LABEL, '--body-file', '-', inp=body).strip().rsplit('/', 1)[-1]
if res.get('changes'):
    gh('issue', 'comment', num, '--body-file', '-', inp='**What changed:**\n\n' + '\n'.join('- ' + c for c in res['changes']))
print(f'::notice title=KY answer key::{len(res.get("changes", []))} change(s); issue #{num}')
