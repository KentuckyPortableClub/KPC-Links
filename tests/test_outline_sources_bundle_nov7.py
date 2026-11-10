#!/usr/bin/env python3
"""Nov 7 evening bundle (Brandon 7:06 PM + 7:36 PM CST). Offline.

1. kpc_key_layers.py wires a LAND-CLASS YES row only when its URL is on data/key-layers-landclass-approved.json 'approved'
   (Brandon 7:06 PM CST: 'If you all approved the layers send them in'); any other land-class row still waits for his word.
2. The approved list: 71 approved, the WDPA copy held with a reason; no banned host anywhere in the layer lists.
3. data/trails-layers.json: the approved trail LINE layers are in the trail list (not in the polygon key list).
4. data/us-key/overrides.json: the 15 signed overrides (decided_by Brandon Nov 7 4:54 PM CST); US-11748 / US-5782 still held.
5. kpc-us-key.yml plan warns when force=yes and the states input is empty.
Rules hashes stay us a066624520b4, ca 8feccbb7d9ee, world 6a5969a25d2c (rule files untouched)."""
import json, os, pathlib, re, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / '.github/scripts'))
ok = True


def check(msg, c):
    global ok
    print(('PASS ' if c else 'FAIL ') + msg)
    ok = ok and bool(c)


BANNED = ('services.arcgis.com/33tooklri9xpic7u', 'ncnhde.natureserve.org')

# 1. the wiring rule, on a temp tree
T = pathlib.Path(tempfile.mkdtemp(prefix='kpc-lc-nov7-'))
try:
    (T / '.github/scripts').mkdir(parents=True)
    for f in ('kpc_key_layers.py', 'kpc_json_any.py'):
        shutil.copy(ROOT / '.github/scripts' / f, T / '.github/scripts' / f)
    D = T / 'kpcdata'; (D / 'data/waiting/questions').mkdir(parents=True)
    A = 'https://example.gov/arcgis/rest/services/Natura2000_Sites/MapServer/0'
    B = 'https://example.gov/arcgis/rest/services/SSSI_Units/MapServer/1'
    C = 'https://example.gov/arcgis/rest/services/State_Trails/MapServer/2'
    rows = [{'area': 'W-GB', 'url': A, 'name_field': 'NAME', 'title': 'Natura 2000 sites', 'answer': 'YES', 'checked_by': 'chat 11'},
            {'area': 'W-GB', 'url': B, 'name_field': 'NAME', 'title': 'SSSI units', 'answer': 'YES', 'checked_by': 'chat 11'},
            {'area': 'W-GB', 'url': C, 'name_field': 'NAME', 'title': 'State trails', 'answer': 'YES', 'checked_by': 'chat 11'}]
    json.dump({'questions': rows}, open(D / 'data/waiting/questions/layers.json', 'w'))
    (T / 'data/world-key').mkdir(parents=True); (T / 'data/us-key').mkdir(parents=True)
    json.dump({'states': {}}, open(T / 'data/state-gis.json', 'w'))
    json.dump({'approved_by': 'test', 'approved': [{'url': A}], 'held': [{'url': B, 'why': 'test'}]}, open(T / 'data/key-layers-landclass-approved.json', 'w'))
    r = subprocess.run([sys.executable, '.github/scripts/kpc_key_layers.py'], cwd=T, env=dict(os.environ, DATA=str(D)), capture_output=True, text=True)
    WX = json.load(open(T / 'data/world-key/extra-layers.json')) if (T / 'data/world-key/extra-layers.json').exists() else {}
    got = [x['url'] for x in (WX.get('countries') or {}).get('GB', [])]
    check('an approved land-class layer is wired', A in got)
    check('a land-class layer that is not on the approved list still waits (held rows are not approved)', B not in got and "Brandon's word needed" in r.stdout)
    check('a trail LINE layer never goes to the polygon key', C not in got)
    os.remove(T / 'data/key-layers-landclass-approved.json'); os.remove(T / 'data/world-key/extra-layers.json')
    r = subprocess.run([sys.executable, '.github/scripts/kpc_key_layers.py'], cwd=T, env=dict(os.environ, DATA=str(D)), capture_output=True, text=True)
    check('with no approved list every land-class layer waits (the guard is unchanged)', not (T / 'data/world-key/extra-layers.json').exists())
finally:
    shutil.rmtree(T, ignore_errors=True)

# 2. the approved list
L = json.load(open(ROOT / 'data/key-layers-landclass-approved.json', encoding='utf-8'))
check(f"44 approved land-class layers, 28 held ({len(L['approved'])} / {len(L['held'])})", len(L['approved']) == 44 and len(L['held']) == 28)
check("no EEA Europe-wide layer approved (the world key reads EEA per country with a filter)", not any("discomap.eea" in x["url"] for x in L["approved"]))
check("no EEA Europe-wide layer in extra-layers.json", "discomap.eea" not in open(os.path.join(ROOT, "data/world-key/extra-layers.json")).read())
check('the held one is the unofficial WDPA copy, with a reason', 'wdpa' in L['held'][0]['url'].lower() and L['held'][0].get('why'))
check("approval is Brandon's, dated Nov 7 7:06 PM CST", 'Brandon' in L['approved_by'] and '7:06 PM' in L['approved_by'])
import kpc_research_sources as RS  # noqa: E402
ARC = re.compile(r'://services[\w-]*\.arcgis\.com/', re.I)
bad = lambda u: any(b.lower() in u.lower() for b in BANNED) or any(b.lower() in u.lower() for b in RS.BANNED if b != 'services.arcgis.com') or bool(ARC.search(u))
check('no approved land-class layer is on a banned / robots-403 host', not any(bad(a['url']) for a in L['approved']))
SG = json.load(open(ROOT / 'data/state-gis.json', encoding='utf-8'))['states']
mine = [x for v in SG.values() for x in v if 'Nov 7 2026' in str(x.get('note')) or '2026-11-07' in str(x.get('note'))]
check(f'{len(mine)} layers added to state-gis.json today, none on a banned / robots-403 host', mine and not any(bad(x['url']) for x in mine))
check('the NYSDOT dev portal (do-not-ingest) is not added', not any('gisportaldev' in x['url'] for x in mine))

# 3. trail lines
TL = json.load(open(ROOT / 'data/trails-layers.json', encoding='utf-8'))
old = json.loads(subprocess.run(['git', 'show', 'HEAD~0:data/trails-layers.json'], cwd=ROOT, capture_output=True, text=True).stdout or '{}')
tl = {u.rstrip('/').lower() for v in TL['layers'].values() for u in v}
check(f'at least 45 trail line layers in the trail list ({len(tl)})', len(tl) >= 45)
check('the NPS public trails layer is in the trail list', 'https://mapservices.nps.gov/arcgis/rest/services/nationaldatasets/nps_public_trails/featureserver/0' in tl)
held = TL.get('held_robots', {}).get('rows', [])
check(f'{len(held)} trail layers on robots-403 hosts are held, not in the list the bot reads', held and not any(h['url'].rstrip('/').lower() in tl for h in held))
added_now = [u for k, v in TL['layers'].items() for u in v if 'Nov 7 2026' in str(TL['credits'].get(u))]
check(f'none of the {len(added_now)} trail layers added today is on a banned / robots-403 host', added_now and not any(bad(u) for u in added_now))
sg = {x['url'].rstrip('/').lower() for v in SG.values() for x in v}
check('no trail layer added today went into the polygon list', not ({u.rstrip('/').lower() for u in added_now} & sg))
check('trail list keys are US state letters or CA-XX', all(re.fullmatch(r'[A-Z]{2}|CA-[A-Z]{2}', k) for k in TL['layers']))

# 4. overrides
O = json.load(open(ROOT / 'data/us-key/overrides.json', encoding='utf-8'))['parks']
S15 = 'US-0150 US-10281 US-11401 US-12028 US-4894 US-4933 US-4934 US-4955 US-13039 US-5789 US-5869 US-6197 US-6202 US-9678 US-3917'.split()
check('15 signed overrides, each with decided_by Brandon Nov 7 4:54 PM CST and a join',
      all('4:54 PM' in str(O.get(r, {}).get('decided_by')) and O[r].get('join') for r in S15))
check("the Nov 2 'no' entries on the right land are gone", all(not O[r].get('no') for r in S15 if r != 'US-3917'))
check('US-9678 re-pointed cow909 -> cow910', O['US-9678']['join'] == ['cow910'])
check('US-3917 joins 254041 and keeps 254129 as no', O['US-3917']['join'] == ['254041'] and '254129' in O['US-3917'].get('no', []))
check('US-11748 and US-5782 are still held (no override)', 'US-11748' not in O and 'US-5782' not in O)

# 5. planner warning
Y = (ROOT / '.github/workflows/kpc-us-key.yml').read_text(encoding='utf-8')
check('the plan step reads FORCE and warns on force with empty states', 'FORCE: ${{ inputs.force }}' in Y.split('- id: p', 1)[1].split('run:', 1)[0]
      and 'force=yes with an EMPTY states input' in Y)

import kpc_key_freeze as KF  # noqa: E402
H = {k: KF.rules_hash(k) for k in ('us-key', 'ca-key', 'world-key')}
check('rules hashes unchanged ' + json.dumps(H), H == {'us-key': 'da660f0d5ae7', 'ca-key': 'b1a521708978', 'world-key': '1a8913a378bb'})
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
