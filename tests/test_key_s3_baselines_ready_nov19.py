#!/usr/bin/env python3
"""S3 (keys-first hand-off rev 3.1, F11; Opus 19 Nov 2026): the three baselines, the gate's findings, the ready check. Offline.
Prints PASS / FAIL lines and ends ALL PASS or SOME FAILED."""
import contextlib, gzip, io, json, os, pathlib, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_ready as K  # noqa: E402
import kpc_master_cli as CLI  # noqa: E402
import kpc_key_freeze as F  # noqa: E402

ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg, flush=True)


def rows(prefix, n):
    return [{'OBJECTID': f'{prefix}{i + 1}', 'Unit_Nm': f'x{i}'} for i in range(n)]


# --- the three baselines (no re-read: the saved copies' rows, counted 19 Nov from boundary-cache 2026-11-12) ---
L = json.loads((ROOT / 'data/outlines/layers.json').read_text(encoding='utf-8'))['layers']
check('CO sgcoa, OR sgorf, WA sgorf baselines are the saved copies\' rows (317, 2,150, 228), not the capped 200',
      [L[k]['expected_count'] for k in ('US-CO.sgcoa', 'US-OR.sgorf', 'US-WA.sgorf')] == [317, 2150, 228]
      and all('no re-read' in L[k].get('baseline_how', '') for k in ('US-CO.sgcoa', 'US-OR.sgorf', 'US-WA.sgorf')))
check('no layer baseline is still the capped 200 with a bigger read on file',
      not [k for k, v in L.items() if v.get('expected_count') == 200 and (v.get('source_count') or 0) > 200])

# --- findings and the ready check, made-up state ZZ ---
doc = {'caches': {'US-ZZ': {'expected_count': 9}}, 'layers': {
    'US-ZZ.sgzza': {'expected_count': 5}, 'US-ZZ.sgzzb': {'expected_count': 3}, 'sgzza': {'expected_count': 6}}}
blob = {'recs': rows('sgzza', 5) + rows('sgzzb', 2) + rows('wsa', 3)}
f = K.stale_baselines('US-ZZ', blob, doc)
check('stale: the state baseline 9 vs 10 records, layer sgzzb 3 vs 2 rows; sgzza 5 = 5 is fine',
      ('state', 'US-ZZ', 9, 10) in f and ('layer', 'US-ZZ.sgzzb', 3, 2) in f and not any(x[1] == 'US-ZZ.sgzza' for x in f))
sg = {'states': {'ZZ': [{}, {}, {}]}}   # three state-gis entries = sgzza, sgzzb, sgzzc
needs = [{'area': 'US-ZZ', 'layer': 'wsa', 'who': 'bot', 'status': 'open'},
         {'area': 'US-ZZ', 'layer': 'hand1', 'who': 'person', 'status': 'open'},
         {'area': 'US-ZZ', 'layer': 'done1', 'who': 'bot', 'status': 'done'}]
r = K.ready('US-ZZ', blob, sg, doc, needs)
check('ready: sgzza short of its own total (5 of 6), sgzzb short (2 of 3), sgzzc missing, wsa with a bot, hand1 a hand download',
      r.get('sgzza') == ['short'] and r.get('sgzzb') == ['short'] and r.get('sgzzc') == ['missing']
      and r.get('wsa') == ['bot'] and r.get('hand1') == ['hand'] and 'done1' not in r)
check('the ids are the builder\'s (sgcoa .. sgcoz, sgcoaa)', K.sg_ids('CO', 28)[:2] == ['sgcoa', 'sgcob'] and K.sg_ids('CO', 28)[26:] == ['sgcoaa', 'sgcoab'])
check('missing, short and bot block; a hand download alone does not', K.blocks(['short']) and K.blocks(['bot']) and not K.blocks(['hand']))
check('no saved copy: every key layer is missing', all(v == ['missing'] for v in K.ready('US-ZZ', None, sg, doc, []).values())
      and len(K.ready('US-ZZ', None, sg, doc, [])) == 3)


def gate(env, expect='US-ZZ US-YY', needs_rows=None):
    t = pathlib.Path(tempfile.mkdtemp())
    (t / 'root').mkdir(); (t / 'cache').mkdir()
    (t / 'root/layers.json').write_text(json.dumps(dict(doc, caches={'US-ZZ': {'expected_count': 10}}, format=1)))
    with gzip.open(t / 'cache/US-ZZ.json.gz', 'wt') as fh:
        json.dump(blob, fh)
    (t / 'sg.json').write_text(json.dumps(sg))
    (t / 'needs.json').write_text(json.dumps({'rows': needs if needs_rows is None else needs_rows}))
    old = {k: os.environ.get(k) for k in ('KPC_GATE_STALE_REFUSE', 'KPC_READY_BLOCK')}
    os.environ.update(env)
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            rc = CLI.main(['gate', '--cache', str(t / 'cache'), '--root', str(t / 'root'), '--report', str(t / 'short.txt'),
                           '--expect', expect, '--state-gis', str(t / 'sg.json'), '--needs', str(t / 'needs.json'),
                           '--ready-report', str(t / 'ready.json'), '--us-layers', ''])   # made-up states: ids by position
    finally:
        for k, v in old.items():
            if v is None: os.environ.pop(k, None)
            else: os.environ[k] = v
    rep = json.loads((t / 'ready.json').read_text()) if (t / 'ready.json').exists() else {}
    return rc, out.getvalue(), rep, (t / 'cache/short/US-ZZ.json.gz').exists()


rc, out, rep, held = gate({})
check('switches OFF: nothing is held, the copy is used, the report names the stale layer and the ready findings',
      rc == 0 and not held and 'US-ZZ' in rep.get('stale', {}) and rep['ready']['US-ZZ'].get('sgzzc') == ['missing']
      and 'report only' in out)
check('a missing expected copy is a FINDING (named in the report and a warning), not a skip, and it holds nothing',
      rep.get('missing_copies') == ['US-YY'] and 'MISSING COPY' in out and 'US-YY' in rep.get('ready', {}))
rc, out, rep, held = gate({'KPC_GATE_STALE_REFUSE': '1'})
check('KPC_GATE_STALE_REFUSE on: a copy with FEWER rows than a baseline (sgzzb 2 of 3) is moved aside', rc == 7 and held and 'SHORT OF BASELINE' in out)
_saved_doc = json.loads(json.dumps(doc)); doc['layers']['US-ZZ.sgzzb']['expected_count'] = 1   # now every baseline is at or below the copy
rc, out, rep, held = gate({'KPC_GATE_STALE_REFUSE': '1'})
check('KPC_GATE_STALE_REFUSE on: a baseline LOWER than its copy (sgzzb 1, copy 2) never holds; it is named to be raised',
      not held and 'LOW BASELINE' in out and rep['stale']['US-ZZ']['low_baseline'] and not rep['stale']['US-ZZ']['short'])
doc.clear(); doc.update(_saved_doc)
rc, out, rep, held = gate({'KPC_READY_BLOCK': '1'})
check('KPC_READY_BLOCK on: a state with a missing / short / bot layer is moved aside', rc == 7 and held and 'NOT READY' in out)

# a clean state: no stale baseline, every layer whole, only a hand download open
doc_clean = {'caches': {}, 'layers': {'US-ZZ.sgzza': {'expected_count': 5}}}
r2 = K.ready('US-ZZ', {'recs': rows('sgzza', 5)}, {'states': {'ZZ': [{}]}}, doc_clean, [{'area': 'US-ZZ', 'layer': 'h', 'who': 'person', 'status': 'open'}])
check('a layer waiting for a hand download is reported as hand only and never blocks the state', r2 == {'h': ['hand']} and not any(K.blocks(k) for k in r2.values()))

# --- Fable's review of #300: (4) rows with no area, (5.1) raise low baselines, (5.4) source gaps, (6) the ids tied to the builder ---
needs_na = [{'area': '', 'layer': 'sgzzc', 'who': 'person', 'status': 'open'},
            {'area': None, 'layer': 'url:https://x.gov/zz/1', 'who': 'person', 'status': 'open'},
            {'area': None, 'layer': 'sgqqa', 'who': 'person', 'status': 'open'}]
sg2 = {'states': {'ZZ': [{}, {'url': 'https://x.gov/zz/1'}, {}]}}
r4 = K.ready('US-ZZ', blob, sg2, doc, needs_na)
check('a needs-download row with NO area is matched by its layer id (sgzzc) or by its address (url: -> sgzzb); another state\'s id is not',
      r4.get('sgzzc') == ['hand'] and r4.get('sgzzb') == ['hand-held'] and 'sgqqa' not in r4)
check("Fable (19 Nov): an open hand download whose layer the copy already holds is 'hand-held' (row never closed); none in the copy is 'hand'",
      r4.get('sgzzb') == ['hand-held'] and r4.get('sgzzc') == ['hand'] and not K.blocks(['hand-held']))
hd = K.hand_downloads('US-ZZ', blob, sg2, doc, needs_na + [{'area': None, 'layer': 'sgzzc', 'who': 'person', 'status': 'open', 'url': 'https://x.gov/zz/3', 'page': 'https://x.gov/p'}])
check('the real download list holds only layers the copy has none of, with their links',
      {h['layer'] for h in hd} == {'sgzzc'} and any(h['url'] == 'https://x.gov/zz/3' and h['page'] == 'https://x.gov/p' for h in hd))
d5 = {'caches': {'US-ZZ': {'expected_count': 7}}, 'layers': {'US-ZZ.sgzza': {'expected_count': 4}, 'US-ZZ.sgzzb': {'expected_count': 3}}}
up = K.raise_low_baselines(d5, 'US-ZZ', blob, 'test')
check('the sweep raises a baseline lower than its copy (state 7 -> 10, sgzza 4 -> 5) and never lowers one (sgzzb 3 stays, copy 2)',
      up == [('US-ZZ', 7, 10), ('US-ZZ.sgzza', 4, 5)] and d5['layers']['US-ZZ.sgzzb']['expected_count'] == 3
      and d5['caches']['US-ZZ']['baseline_how'] == 'test')
check('a server count beside the baseline is information (source gap), never a hold',
      K.source_gaps('US-ZZ', {'layers': {'US-ZZ.a': {'expected_count': 317, 'source_count': 324}}}) == [('US-ZZ.a', 317, 324)])
import re as _re
_src = (ROOT / '.github/scripts/kpc_us_key.py').read_text(encoding='utf-8')
_m = _re.search(r"k = (f'sg\{st\.lower\(\)\}' \+ \(chr\(97 \+ n\) if n < 26 else chr\(97 \+ n // 26 - 1\) \+ chr\(97 \+ n % 26\)\))", _src)
check("sg_ids() names the layers exactly as kpc_us_key.py does (the builder's line, run for 0..60)",
      _m is not None and [eval(_m.group(1), {'st': 'CO', 'n': n}) for n in range(60)] == K.sg_ids('CO', 60))
_c = json.loads((ROOT / 'data/outlines/layers.json').read_text(encoding='utf-8'))['caches']
check('the sweep is in the file: 24 US state baselines carry the ruling (FL 21,993 -> 84,718, MA 62,739 -> 119,649)',
      _c['US-FL']['expected_count'] == 84718 and _c['US-MA']['expected_count'] == 119649
      and sum(1 for k, v in _c.items() if k.startswith('US-') and 'Fable' in str(v.get('baseline_how', ''))) == 24)

# --- wiring ---
wf = (ROOT / '.github/workflows/kpc-us-key.yml').read_text(encoding='utf-8')
check("the US gate step passes --expect, --state-gis, --needs, --ready-report and both switches default to '0'",
      '--expect "$(for st in $STATES' in wf and '--state-gis data/state-gis.json' in wf and '--ready-report part-ready.json' in wf
      and "KPC_GATE_STALE_REFUSE: ${{ vars.KPC_GATE_STALE_REFUSE || '0' }}" in wf and "KPC_READY_BLOCK: ${{ vars.KPC_READY_BLOCK || '0' }}" in wf)
check('S3 edits no rule file (the ready helper and the gate move no rules hash)',
      not any(x in F.RULE_FILES['us-key'] for x in ('.github/scripts/kpc_key_ready.py', '.github/scripts/kpc_master_cli.py', 'data/outlines/layers.json')))

# Opus, 20 Nov: with the key's id table a layer is counted under the id the builder gave its ADDRESS (34 rows of round 3 were not)
SH = 'https://x.example/arcgis/rest/services/Shared/FeatureServer/3'
usl = {'sgyya': [SH + '/query', 'NAME'], 'sgzza': ['https://x.example/arcgis/rest/services/Own/FeatureServer/0/query', 'NAME']}
sg3 = {'states': {'YY': [{'url': SH, 'nm': 'NAME'}],
                  'ZZ': [{'url': 'https://x.example/arcgis/rest/services/Own/FeatureServer/0', 'nm': 'NAME'},
                         {'url': SH + '/', 'nm': 'NAME'}, {'url': 'https://x.example/no-number', 'nm': 'NAME'}, {'url': SH.replace('/3', '/4')},
                         {'url': 'https://x.example/arcgis/rest/services/New/FeatureServer/1', 'nm': 'NAME'}]}}
ids = [lid for _, lid in K.layer_ids(sg3, usl)['ZZ']]
check(f"a shared address keeps the builder's id; entries it never reads are left out; a new address gets the next free id {ids}",
      ids == ['sgzza', 'sgyya', 'sgzzb'])
doc3 = {'layers': {}}
r5 = K.ready('US-ZZ', {'recs': rows('sgzza', 3) + rows('sgyya', 4)}, sg3, doc3, [], usl)
check(f'with the table: the shared layer\'s rows in the copy count, only the new layer is missing {r5}', r5 == {'sgzzb': ['missing']})
r6 = K.ready('US-ZZ', {'recs': rows('sgzza', 3) + rows('sgyya', 4)}, sg3, doc3, [])
check(f'without the table: the old reading by position, unchanged {sorted(r6)}', sorted(r6) == ['sgzzb', 'sgzzc', 'sgzzd', 'sgzze'])

# Opus, 20 Nov: the owner's approval to build named states on their saved copies as they are (KPC owner 9:10 AM, "1 yes")
import json as _j, tempfile as _tf
with _tf.TemporaryDirectory() as _d:
    ap = pathlib.Path(_d) / 'ready-approved.json'
    ap.write_text(_j.dumps({'approved_by': 'KPC owner', 'states': {'US-ZZ': {'sgzzb': {'kinds': ['missing'], 'rows': 0}, 'sgzza': {'kinds': ['short'], 'rows': 3}}},
                            'stale': {'US-ZZ': {'US-ZZ.sgzza': {'baseline': 5, 'rows': 3}}}}))
    A = K.load_ready_approved(str(ap))
    blob = {'recs': rows('sgzza', 3)}
    check('approved gaps do not hold the state', K.ready_unapproved('US-ZZ', {'sgzza': ['short'], 'sgzzb': ['missing']}, blob, A) == {})
    check('a copy that got smaller than when approved still holds', K.ready_unapproved('US-ZZ', {'sgzza': ['short']}, {'recs': rows('sgzza', 2)}, A) == {'sgzza': ['short']})
    check('a gap the approval does not name still holds', K.ready_unapproved('US-ZZ', {'sgzzc': ['missing']}, blob, A) == {'sgzzc': ['missing']})
    check('another state is not covered', K.ready_unapproved('US-YY', {'sgzza': ['short']}, blob, A) == {'sgzza': ['short']})
    check('a short of baseline is covered only at the approved count or more',
          K.stale_unapproved('US-ZZ', [('layer', 'US-ZZ.sgzza', 5, 3)], A) == [] and K.stale_unapproved('US-ZZ', [('layer', 'US-ZZ.sgzza', 5, 2)], A) == [('layer', 'US-ZZ.sgzza', 5, 2)])
    ap.write_text(_j.dumps({'approved_by': 'someone', 'states': {'US-ZZ': {}}}))
    check('an approval not signed by the KPC owner is not read (fail closed)', K.load_ready_approved(str(ap)) == {})
    check('no approval file = nothing approved', K.load_ready_approved(str(pathlib.Path(_d) / 'none.json')) == {} and K.load_ready_approved('') == {})

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
