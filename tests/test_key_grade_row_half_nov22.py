#!/usr/bin/env python3
"""Review N13 (KPC owner, 22 Nov 2026): the score step hides and lists gold parks by the gold row's OWN half first (KPC-Store marked
every leaked row TUNE), the same lookup as when a row is added; only a row with no half takes the private list (KPC-Store's
sample answer key 'sealed_next', passed with --sealed). Never the public salt. Invented parks only; offline."""
import csv, json, pathlib, sys, tempfile
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
import kpc_key_grade as G  # noqa: E402
bad = 0
def ck(c, m):
    global bad; bad += not c; print(('PASS ' if c else 'FAIL ') + m, flush=True)

t = pathlib.Path(tempfile.mkdtemp())
(t / 'key.json').write_text(json.dumps({'about': 'x', 'sealed_next': ['US-0007', 'US-0008']}))
G.load_sealed(str(t / 'key.json'))
ck(G.half_of('US-0007') == 'SEALED' and G.half_of('US-0001') == 'TUNE', "the private list may be KPC-Store's sample answer key (sealed_next)")
gold = t / 'gold.json'
gold.write_text(json.dumps({'parks': {'US-0007': {'area': 'US-XX', 'name': 'Invented A', 'half': 'TUNE', 'cands': []}}, 'log': []}))
def park(ref): return {'area': 'US-XX', 'stratum': 'random', 'plant': False, 'graded': 'single', 'outcome': 'WRONG LAND', 'letters': ['A'],
                       'name': 'Invented', 'act': 1, 'class': 'one', 'flags': [], 'verdicts': {'A': 'UNSURE'}}
rep = {'graders': {}, 'rates': {}, 'disputes': [], 'parks': {'US-0007': park('US-0007'), 'US-0008': park('US-0008')}}
parks = {r: {'cands': {'A': {'name': 'Invented rec', 'methods': ['name'], 'joined': True}}, 'plant': False} for r in ('US-0007', 'US-0008')}
G.write_score(rep, parks, {}, str(t / 'out'), str(gold))
listed = {x['ref'] for x in csv.DictReader(open(t / 'out' / 'findings.csv'))}
shown = json.loads((t / 'out' / 'score.json').read_text())['parks']
ck('US-0007' in listed and not shown['US-0007'].get('sealed'), "a row whose own half is TUNE is listed and shown, even when the private list names it")
ck('US-0008' not in listed and shown['US-0008'].get('sealed'), 'a park with no gold row yet takes the private list: SEALED, hidden')
print('ALL PASS' if not bad else 'SOME FAILED'); sys.exit(1 if bad else 0)
