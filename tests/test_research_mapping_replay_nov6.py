#!/usr/bin/env python3
"""Quality FIX on PR 49: research field rows must not change builder mapping or tract output.

The 10 existing layer URLs that the new matchers caught (NT, ON, QC, NZ, NL, WA) keep the
pre-research mapping with KPC_RESEARCH_SOURCES off and in report mode. Saskatchewan matches
only gis.saskatchewan.ca Planning, not St John's NL or WA DBCA.
Offline. Does not write the repo.
"""
import json, os, pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / '.github' / 'scripts'))
os.environ.pop('KPC_RESEARCH_SOURCES', None)

import kpc_source_fields as SF
import kpc_tracts as TR

ok = True


def check(cond, msg):
    global ok
    if not cond:
        ok = False
        print('FAIL', msg)
    else:
        print('PASS', msg)


# Existing layers the research matchers used to steal. None of these had an explicit source row before.
EXISTING = [
    'https://www.apps.geomatics.gov.nt.ca/arcgis/rest/services/GNWT/Environment_LCC/MapServer/195',
    'https://ws.lioservices.lrc.gov.on.ca/arcgis2/rest/services/LIO_OPEN_DATA/LIO_Open03/MapServer/2',
    'https://geo.environnement.gouv.qc.ca/donnees/rest/services/Biodiversite/Aires_protegees/MapServer/10',
    'https://geo.environnement.gouv.qc.ca/donnees/rest/services/Biodiversite/Aires_protegees/MapServer/12',
    'https://geo.environnement.gouv.qc.ca/donnees/rest/services/Biodiversite/Aires_protegees/MapServer/23',
    'https://servicescarto.mrnf.gouv.qc.ca/pes/rest/services/Territoire/TRQ_WMS/MapServer/6',
    'https://servicescarto.mrnf.gouv.qc.ca/pes/rest/services/Territoire/TRQ_WMS/MapServer/16',
    'https://seasketch.doc.govt.nz/arcgis/rest/services/National/Public_Conservation_Land/MapServer/0',
    'https://map.stjohns.ca/mapsrv/rest/services/Mapcentre/Planning/MapServer/5',
    'https://public-services.slip.wa.gov.au/public/rest/services/SLIP_Public_Services/Property_and_Planning/MapServer/15',
]
NL = EXISTING[-2]
WA = EXISTING[-1]
SK = 'https://gis.saskatchewan.ca/arcgis/rest/services/Planning/MapServer'
# Fields that the Saskatchewan row would have added, and that AUTO does not claim.
FIELDS = ['PROP_OWN', 'PUBLICCL', 'NAME']
RESEARCH_KEYS = {s['key'] for s in SF.RESEARCH_SOURCES}

check(len(EXISTING) == 10, 'the ten existing layer URLs are the replay set')
check(not ({s['key'] for s in SF.SOURCES} & RESEARCH_KEYS), 'research rows are not in the builder source table')


def replay(url, fields):
    mp = SF.mapping(url, '', fields)
    attrs = {'NAME': 'Sample', 'PROP_OWN': 'X', 'PUBLICCL': 'public'}
    tract = TR.tract('1', 'Sample', 'name', attrs, mp)
    return SF.find(url), mp, SF.extra_fields(mp), tract


# No field list: before these rows, find() missed and the tract src stayed unknown.
# With PROP_OWN / PUBLICCL (what sk_whpa would have copied), AUTO still claims nothing,
# so the published tract src is the mapping key 'auto', not 'sk_whpa'.
for flag in ('off', 'report'):
    if flag == 'off':
        os.environ.pop('KPC_RESEARCH_SOURCES', None)
    else:
        os.environ['KPC_RESEARCH_SOURCES'] = 'report'
    first = None
    for url in EXISTING:
        hit, mp, asked, tract = replay(url, None)
        check(hit is None and mp.get('key') is None and mp.get('how') == 'none' and asked == [] and tract['src'] == 'unknown'
              and 'own' not in tract and 'access' not in tract,
              f'{flag} no-fields {url.rsplit("/", 2)[-2]}/{url.rsplit("/", 1)[-1]} stays unknown ({tract["src"]})')
        hit2, mp2, asked2, tract2 = replay(url, FIELDS)
        check(hit2 is None and mp2.get('how') == 'none' and asked2 == [] and tract2['src'] != 'sk_whpa' and 'own' not in tract2,
              f'{flag} with fields {url.rsplit("/", 1)[-1]} does not become sk_whpa ({tract2["src"]} asked={asked2})')
        if first is None:
            first = (mp2, asked2, tract2['src'])
        else:
            check(mp2 == first[0] and asked2 == first[1] and tract2['src'] == first[2],
                  'every one of these layers gets the same published mapping')

os.environ['KPC_RESEARCH_SOURCES'] = 'report'
check(SF.research_find(SK) and SF.research_find(SK)['key'] == 'sk_whpa', 'the Saskatchewan Planning service still has a research field row')
check(SF.research_find(SK + '/0') and SF.research_find(SK + '/0')['key'] == 'sk_whpa', 'a layer under that SK service matches')
check(SF.research_find(NL) is None, 'St John NL Mapcentre/Planning/MapServer/5 is not the Saskatchewan row')
check(SF.research_find(WA) is None or SF.research_find(WA)['key'] != 'sk_whpa', 'WA Property_and_Planning/MapServer/15 is not the Saskatchewan row')
check(SF.find(NL) is None and SF.find(WA) is None and (SF.find(SK) is None or SF.find(SK)['key'] != 'sk_whpa'),
      'builders do not use the Saskatchewan row for NL, WA, or the SK service')

# Every URL the keys already list: find() never returns a research key, off or report.
urls = set(EXISTING)
for p in ('data/ca-key/layers.json', 'data/us-key/layers.json', 'data/world-key/layers.json', 'data/state-gis.json'):
    blob = json.dumps(json.load(open(ROOT / p)))
    urls.update(u.split('?')[0] for u in __import__('re').findall(r'https://[^"\\ ]+', blob))
leaked = []
for flag in ('off', 'report'):
    if flag == 'off':
        os.environ.pop('KPC_RESEARCH_SOURCES', None)
    else:
        os.environ['KPC_RESEARCH_SOURCES'] = 'report'
    for u in urls:
        hit = SF.find(u)
        if hit and hit['key'] in RESEARCH_KEYS:
            leaked.append((flag, hit['key'], u[:100]))
check(not leaked, f'no existing layer URL takes a research field row ({leaked[:3]})')

os.environ.pop('KPC_RESEARCH_SOURCES', None)
print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
