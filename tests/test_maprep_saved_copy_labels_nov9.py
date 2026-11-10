#!/usr/bin/env python3
"""Tool Box saved-copy labels: services.arcgis.com, services1.arcgis.com, and apps.fs.usda.gov
are marked saved copy and are never queried live. The Tool Box layer list is not in a rule hash."""
import json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = True

def check(c, m):
    global ok
    print(('PASS ' if c else 'FAIL ') + m)
    ok = ok and bool(c)

SAVED_HOSTS = {'services.arcgis.com', 'services1.arcgis.com', 'apps.fs.usda.gov'}

def host(u):
    m = re.match(r'https?://([^/]+)', u or '', re.I)
    return (m.group(1).lower() if m else '')

sl = json.loads((ROOT / 'data/maprep-state-layers.json').read_text(encoding='utf-8'))
saved, bad_ok, bad_label = [], [], []
added = 0
for code, lst in (sl.get('areas') or {}).items():
    for L in lst:
        if host(L.get('url')) in SAVED_HOSTS:
            saved.append((code, L))
            if L.get('ok'):
                bad_ok.append((code, L.get('label'), L.get('url')))
            if L.get('read') != 'saved copy' or L.get('live') is not False or 'saved copy' not in str(L.get('why') or '').lower():
                bad_label.append((code, L.get('label'), L.get('read'), L.get('live'), L.get('why')))
        if L.get('read') == 'saved copy' and '(saved copy)' in str(L.get('label') or '') and L.get('live') is False:
            added += 1

check(len(saved) >= 83, f'saved-only hosts listed in state layers ({len(saved)})')
check(not bad_ok, f'no saved-only host is queried live (ok:true) ({len(bad_ok)})')
check(not bad_label, f'saved-only hosts are labelled saved copy, live false ({len(bad_label)})')
check('saved copy' in (sl.get('about') or '').lower() and 't764u' not in (sl.get('about') or ''),
      'state-layers about names saved-copy hosts and has no ticket ids')

cat = json.loads((ROOT / 'data/maprep/catalog.json').read_text(encoding='utf-8'))
old = [s for s in (cat.get('skipped') or []) if s.get('why') == 'services*.arcgis.com treated as disallow']
relabelled = [s for s in (cat.get('skipped') or []) if s.get('why') == 'saved copy — not queried live']
check(not old, 'catalog no longer treats those hosts as only "disallow"')
check(len(relabelled) >= 137, f'catalog skipped rows labelled saved copy ({len(relabelled)})')
check('saved copy' in (cat.get('note') or '').lower(), 'catalog note mentions saved copy')

js = (ROOT / 'kpc-maprep-research.js').read_text(encoding='utf-8')
check('function isSavedCopy' in js and 'SAVED_ONLY_HOSTS' in js, 'research page has a saved-copy check')
check('!isSavedCopy(L)' in js or 'isSavedCopy(L)' in js, 'state-layer search skips saved copies')
check('t764u' not in js.split('state / province layers')[1][:800] if 'state / province layers' in js else False,
      'state-layer comment has no ticket id')

# The Tool Box / maprep layer lists are not inputs to the US, CA, or world rule hashes.
for rel in ('.github/us-key-rule-scope.json', '.github/ca-key-rule-scope.json', '.github/fers-rule-scope.json'):
    text = (ROOT / rel).read_text(encoding='utf-8')
    check('maprep-state-layers.json' not in text and 'maprep/catalog.json' not in text,
          f'{rel} does not include the Tool Box layer lists')

sys.path.insert(0, str(ROOT / '.github/scripts'))
import kpc_key_freeze as KF  # noqa: E402
# freeze file list
for kind, files in KF.RULE_FILES.items():
    hit = [f for f in files if 'maprep' in f or 'catalog.json' in f or 'point-circles' in f]
    check(not hit, f'{kind} rule files do not include the Tool Box list ({hit})')

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
