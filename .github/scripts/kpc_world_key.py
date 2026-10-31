"""WORLD boundary ANSWER KEY for the busy POTA programs (Brandon Oct 18 2026: 'have data waiting on you'). Same strict method as
kpc_us_key.py / kpc_ca_key.py: pull the country's OFFICIAL protected-area layers (found by kpc_world_probe.py), join to that program's
POTA parks (data/parkinfo/<CC>.json) ONLY when the name matches (generic words in that language dropped, accents dropped) AND the kind
of place matches, near the pin; every piece with that name joins; anything unsure goes on a check list, never joined.
COUNTRIES='AU DE' picks. Writes data/world-key/<CC>.json, data/world-key/review/<CC>.md, data/world-key/index.json.
Sources (official agencies only):
  AU  CAPAD 2024 terrestrial (DCCEEW, Australian Government)                     ArcGIS
  DE  BfN Schutzgebiete WFS (Bundesamt für Naturschutz)                          WFS: Nationalparke, Naturparke, Naturschutzgebiete, Landschaftsschutzgebiete,
                                                                                  Biosphärenreservate, FFH-Gebiete, Vogelschutzgebiete, Nationale Naturmonumente
  GB  Natural England open data (NNR, LNR, Country Parks, SSSI) ArcGIS + NatureScot WFS (cpk, nnr, lnr, …)
  JP  Ministry of the Environment national park areas via Esri Japan's 国立公園区域等 (nps_all) ArcGIS
  PL  GDOŚ refuses GitHub (403): Poland uses the EEA layers live in the tools; skipped here."""
import json, sys, os, re, time, unicodedata, urllib.parse, urllib.request, pathlib

UA = {'User-Agent': 'KPC (kentuckyportableclub.github.io)'}
OUT = pathlib.Path('data/world-key'); (OUT / 'review').mkdir(parents=True, exist_ok=True)
import gzip
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import kpc_match as KM  # noqa: E402

# Oct 25 (round 5 hand checks): a person's decisions per park, {ref: {join: [official names], no: [names], why}}
try:
    WOV = json.load(open('data/world-key/overrides.json', encoding='utf-8')).get('parks', {})
except Exception:  # noqa: BLE001
    WOV = {}


def low(x): return ' '.join(unicodedata.normalize('NFKD', str(x or '')).encode('ascii', 'ignore').decode().lower().replace("'", '').split())
from kpc_save import save_json, save_text  # noqa: E402  (Oct 25 storage plan: write only when the content changed)
# SHAPE DETAIL + SAVED COPY (Oct 22, Fable's review; the same scheme as kpc_us_key.py). Live runs have always fetched
# outlines at 0.01 degrees (~1.1 km) and then THINNED every ring to about 60 points - a whole national park in 60
# dots - which is what 'pin inside' and PIN_JOIN were judged against. A saved copy is fetched once, so it can afford
# more. GEO_CACHE_MODE: off (default, exactly as before) | use | refresh | only (no network: the fast rule test).
DETAIL = float(os.environ.get('GEO_DETAIL') or 0.01)
PREC = 3 if DETAIL >= 0.01 else 5
THIN_N = int(os.environ.get('GEO_THIN') or 60)
WCACHE = pathlib.Path(os.environ.get('GEO_CACHE') or 'cache/world')
CMODE = (os.environ.get('GEO_CACHE_MODE') or 'off').strip().lower()
WUSED, WSAVED, WMETA = [], [], {}


def wcache_file(cc): return WCACHE / f'W-{cc}.json.gz'


def wsave(cc, recs):
    WCACHE.mkdir(parents=True, exist_ok=True)
    rows = []
    for r in recs:
        o = {k: v for k, v in r.items() if k != '_k'}
        o['_r'] = [[[round(pt[0], 5), round(pt[1], 5)] for pt in ring if len(pt) >= 2] for ring in (r.get('_r') or [])]
        rows.append(o)
    with gzip.open(wcache_file(cc), 'wt', encoding='utf-8') as f:
        json.dump({'cc': cc, 'saved': time.strftime('%Y-%m-%d'), 'detail': DETAIL, 'thin': THIN_N, 'recs': rows}, f,
                  separators=(',', ':'), default=lambda o: sorted(o) if isinstance(o, (set, frozenset)) else str(o))
    WSAVED.append(cc)


def wload(cc):
    f = wcache_file(cc)
    if not f.exists(): return None
    try:
        with gzip.open(f, 'rt', encoding='utf-8') as fh: blob = json.load(fh)
    except Exception as e:  # noqa: BLE001
        print(f'{cc}: saved outlines unreadable ({e}); fetching', flush=True); return None
    recs = blob.get('recs') or []
    WMETA[cc] = (blob.get('detail'), blob.get('thin'))
    for r in recs:
        if '_k0' in r and not isinstance(r['_k0'], set): r['_k0'] = set(r['_k0'] or [])
        if r.get('_bb') is not None: r['_bb'] = list(r['_bb'])
    WUSED.append(cc)
    return recs
SRC = {
    'AU': [('CAPAD (DCCEEW)', 'arcgis', 'https://gis.environment.gov.au/gispubmap/rest/services/ogc_services/CAPAD/MapServer/0')],
    'DE': [('BfN ' + t, 'wfs', 'https://geodienste.bfn.de/ogc/wfs/schutzgebiet', 'schutzgebiet:' + t) for t in
           ('Nationalparke', 'Naturparke', 'Naturschutzgebiete', 'Biosphaerenreservate', 'Nationale_Naturmonumente', 'Fauna_Flora_Habitat_Gebiete', 'Vogelschutzgebiete', 'Landschaftsschutzgebiete')],
    'GB': [('Natural England ' + n, 'arcgis', f'https://services.arcgis.com/JJzESW51TqeY9uat/arcgis/rest/services/{s}/FeatureServer/0') for n, s in
           (('NNR', 'National_Nature_Reserves_England'), ('LNR', 'Local_Nature_Reserves_England'), ('Country Parks', 'Country_Parks_England'), ('SSSI', 'SSSI_England'),
            ('National Parks', 'National_Parks_England'), ('National Landscapes', 'Areas_of_Outstanding_Natural_Beauty_England'))]
          + [('NatureScot ' + t, 'wfs', 'https://ogc.nature.scot/geoserver/protectedareas/wfs', 'protectedareas:' + t) for t in ('cpk', 'nnr', 'lnr', 'sssi', 'rp', 'sac', 'spa')]
          + [('NRW Wales ' + n, 'wfs', 'https://datamap.gov.wales/geoserver/ows', t) for n, t in
             (('SSSI', 'inspire-nrw:NRW_SSSI'), ('NNR', 'inspire-nrw:NRW_NNR'), ('LNR', 'inspire-nrw:NRW_LNR'), ('National Parks', 'inspire-nrw:NRW_NATIONAL_PARK'),
              ('National Landscapes', 'inspire-nrw:NRW_AONB'), ('Country Parks', 'geonode:country_parks'), ('SAC', 'inspire-nrw:NRW_SAC'), ('SPA', 'inspire-nrw:NRW_SPA'))],
    'JP': [('Ministry of the Environment national parks (Esri Japan)', 'arcgis', 'https://services.arcgis.com/wlVTGRSYTzAbjjiC/arcgis/rest/services/nps_all/FeatureServer/0'),
           # Oct 18 (probe 2): nps_all has only the 34 national parks; MLIT's National Land Numerical Information A10 'natural park areas'
           # (all national, quasi-national and prefectural natural parks, one zip per prefecture, shapefiles) covers the rest
           ('MLIT natural park areas (A10)', 'a10', 'https://nlftp.mlit.go.jp/ksj/gml/datalist/KsjTmplt-A10-v3_1.html')],
}
# Oct 18 (Brandon: 'go ahead'): PL ES FR CH AT from the European Environment Agency (official EU inventory, one place for all five):
# Natura 2000 sites + Nationally designated areas (ex-CDDA; Switzerland reports there too, it has no Natura 2000).
EEA = 'https://bio.discomap.eea.europa.eu/arcgis/rest/services/ProtectedSites/'
EU = ('PL', 'ES', 'FR', 'CH', 'AT', 'NL', 'PT', 'SE', 'CZ', 'SI', 'NO', 'RO', 'IT', 'BE', 'DK', 'FI', 'HU', 'SK', 'HR', 'IE', 'LT', 'LV', 'EE', 'LU')   # Oct 19 PM: + the other Latin-alphabet EEA countries   # Oct 19: the next 8 busiest POTA programs (NO has no Natura 2000, CDDA only)
# Countries where the official names are written differently from POTA's, so a pin inside one area is the join
# (Oct 21: Japan had 30,420 areas loaded and only 102 parks joined because the names never matched).
NAME_JOIN = (os.environ.get('NAME_JOIN') or '1') != '0'
PIN_JOIN = {x.strip().upper() for x in (os.environ.get('PIN_JOIN') or 'JP').split(',') if x.strip()}
for _c in EU:
    SRC[_c] = [('EEA Natura 2000', 'arcgis', EEA + 'Natura2000Sites/MapServer/2', [f"MS='{_c}'", f"SITECODE LIKE '{_c}%'"]),
               ('EEA nationally designated areas', 'arcgis', EEA + 'CDDA_Dyna_WM/MapServer/4', [f"countryCode='{_c}'", f"countryCode LIKE '{_c}%'"])]
# Oct 18 (probe 2): Switzerland's own federal inventories (BAFU, data.geo.admin.ch STAC, shapefiles in Swiss LV95): POTA's 151 CH
# 'Natural Monument' parks are BLN objects, which the EEA list files under several designation codes at once.
CHB = [('BAFU landscapes and natural monuments (BLN)', 'ch.bafu.bundesinventare-bln'), ('BAFU hunting reserves', 'ch.bafu.bundesinventare-jagdbanngebiete'),
       ('BAFU water and migratory bird reserves', 'ch.bafu.bundesinventare-vogelreservate'), ('BAFU mire landscapes', 'ch.bafu.bundesinventare-moorlandschaften'),
       ('BAFU floodplains', 'ch.bafu.bundesinventare-auen'), ('BAFU raised bogs', 'ch.bafu.bundesinventare-hochmoore'), ('BAFU fens', 'ch.bafu.bundesinventare-flachmoore'),
       ('BAFU Ramsar sites', 'ch.bafu.schutzgebiete-ramsar'), ('BAFU parks of national importance', 'ch.bafu.schutzgebiete-paerke_nationaler_bedeutung_perimeter'),
       ('BAFU Emerald sites', 'ch.bafu.schutzgebiete-smaragd')]
SRC['CH'] = SRC['CH'] + [(a, 'chshp', b) for a, b in CHB]
CHPREF = {'Natural Monument': ['BAFU landscapes and natural monuments (BLN)'], 'Game Reserve': ['BAFU hunting reserves'],
          'Wildlife Reserve': ['BAFU water and migratory bird reserves', 'BAFU hunting reserves'], 'Wildlife Refuge': ['BAFU water and migratory bird reserves'],
          'Wetland Reserve': ['BAFU water and migratory bird reserves', 'BAFU mire landscapes', 'BAFU floodplains', 'BAFU raised bogs', 'BAFU fens'],
          'Ramsar Site': ['BAFU Ramsar sites'], 'Nature Park': ['BAFU parks of national importance'], 'Wilderness Park': ['BAFU parks of national importance'],
          'National Park': ['BAFU parks of national importance'], 'Landscape Park': ['BAFU parks of national importance', 'BAFU landscapes and natural monuments (BLN)']}
# Oct 20 (Brandon: 'keep working on building the database for boundaries'): POTA's 10,400 French 'Biological Reserve' parks are
# France's ZNIEFF wildlife zones (MNHN / INPN inventory). IGN Géoplateforme first; the Esri France copy of the same INPN data only
# when the Géoplateforme answers nothing. Australia: CAPAD leaves state forests out, so each state's own forestry map.
SRC['FR'] = SRC['FR'] + [('IGN Géoplateforme ZNIEFF ' + n, 'wfs', 'https://data.geopf.fr/wfs/ows', t) for n, t in
                         (('type I', 'patrinat_znieff1:znieff1'), ('type II', 'patrinat_znieff2:znieff2'), ('type I sea', 'patrinat_znieff1_mer:znieff1_mer'))] \
                      + [('ZNIEFF (INPN data, Esri France) layer ' + str(i), 'arcgis_alt', 'https://services.arcgis.com/d3voDfTFbHOCRwVR/arcgis/rest/services/ZNIEFF_2021/FeatureServer/' + str(i)) for i in (0, 1)]
SRC['AU'] = SRC['AU'] + [('NSW State Forest (Forestry Corporation NSW)', 'arcgis', 'https://services2.arcgis.com/iCBB4zKDwkw2iwDD/arcgis/rest/services/NSW_Dedicated_State_Forests/FeatureServer/0'),
                         ('QLD State Forest (Queensland Government)', 'arcgisfind', 'https://spatial-gis.information.qld.gov.au/arcgis/rest/services/PlanningCadastre/LandParcelPropertyFramework/MapServer', r'state forest|timber reserve')]
# Oct 25 (outside research bot, other countries round 2): Victoria DEECA + Western Australia DBCA state forest tenure, the
# Śląskie voivodeship copy of Poland's nature-and-landscape complexes, and Japan's NATIONAL A10 file (FY2010) whose park-name
# CODES (A10_005 -> KSJ codelist NaturalParkNameCd) name the areas the per-prefecture A10 files leave blank. Licences: VIC = same
# data as DataVic PLM25 (CC BY 4.0); WA = CC BY-NC 4.0; JP FY2010 = non-commercial (KPC is a non-commercial club); PL = none stated
# (regional copy of the national GDOŚ register). Northern Ireland (DAERA) left out: its terms forbid publishing maps without NIEA's
# written permission. WA 'forest blocks' left out: management units, not the legal forest boundary.
SRC['AU'] = SRC['AU'] + [('VIC DEECA state forests', 'arcgis', 'https://enterprise.mapshare.vic.gov.au/server/rest/services/Hosted/Public_Land___DEECA_Managed/FeatureServer/0', ["mmtgen='STATE FOREST' AND name<>' '"]),
                         ('WA DBCA state forests (legislated lands)', 'arcgis', 'https://public-services.slip.wa.gov.au/public/rest/services/SLIP_Public_Services/Property_and_Planning/MapServer/15', ["leg_category='State Forest'"])]
SRC['PL'] = SRC['PL'] + [('Śląskie ORSIP nature and landscape complexes (GDOŚ register)', 'arcgis', 'https://geoportal.orsip.pl/site1/rest/services/DaneRegionalne/FormyOchronyPrzyrodyZieloneSlaskie/MapServer/5')]
SRC['JP'] = SRC['JP'] + [('MLIT natural park areas, national file FY2010 (A10-10)', 'a10n', 'https://nlftp.mlit.go.jp/ksj/gml/data/A10/A10-10/A10-10_GML.zip')]
# Oct 30 (chat 2; chat 10 ask, Brandon 12:05 PM 'Yes to 2'): Colombia, South Africa, Chile = the national agencies' own registers
SRC['CO'] = [('Colombia RUNAP (national register of protected areas, DNP)', 'arcgis', 'https://mapasdnp.dnp.gov.co/server/rest/services/Hosted/RUNAP_Registro_%C3%9Anico_Nacional_de_%C3%81reas_Protegidas/FeatureServer/0')]
SRC['ZA'] = [('South Africa protected areas (DPME, from DFFE SAPAD)', 'arcgis', 'https://dpmegis.dpme.gov.za/arcgis/rest/services/Environmental2/MapServer/1'),
             ('South Africa SAPAD (DFFE)', 'arcgis', 'https://dffeportal.environment.gov.za/hosting/rest/services/PACA/SAPAD/MapServer/2')]
SRC['CL'] = [('Chile SIMBIO protected areas (MMA)', 'arcgis', 'https://arcgis.mma.gob.cl/server/rest/services/SIMBIO/SIMBIO_AP/FeatureServer/0'),
             ('Chile SIMBIO protected areas, layer 2 (MMA)', 'arcgis', 'https://arcgis.mma.gob.cl/server/rest/services/SIMBIO/SIMBIO_AP/FeatureServer/2')]
# Oct 30 (chat 2, Brandon 9:48 'Yes'): approved world layers (chat 11 YES / chat 10 AUTO-2), wired by kpc_key_layers.py (BOT W)
# into data/world-key/extra-layers.json {CC: [{label, url, where?}]}; ArcGIS layers only, a URL already listed above is skipped.
try:
    for _cc, _ls in (json.load(open('data/world-key/extra-layers.json')).get('countries') or {}).items():
        _have = {str(s[2]).rstrip('/').lower() for s in SRC.get(_cc, [])}
        for _l in _ls:
            _u = str(_l.get('url') or '').rstrip('/')
            if _u and _u.lower() not in _have: SRC[_cc] = SRC.get(_cc, []) + [(str(_l.get('label') or 'approved layer')[:80], 'arcgis', _u) + (([_l['where']],) if _l.get('where') else ())]
except FileNotFoundError: pass
except Exception as _e: print(f'::notice title=World key::extra-layers.json not read: {_e}', flush=True)  # noqa: BLE001
COUNTRIES = (os.environ.get('COUNTRIES') or 'AU DE GB JP PL ES FR CH AT NL PT SE CZ SI NO RO IT BE DK FI HU SK HR IE LT LV EE LU CO ZA CL').upper().split()


def _hook(t, v, tb):
    import traceback; notice('World key error', ''.join(traceback.format_exception(t, v, tb))[-3000:])
import sys; sys.excepthook = _hook


def notice(t, m): print('::notice title=%s::%s' % (t, str(m).replace('%', '%25').replace('\n', '%0A')[:3500]), flush=True)


def fetch(u, tries=4, timeout=240):
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=timeout) as r: return json.loads(r.read().decode('utf-8', 'replace'))
        except Exception as e:  # noqa: BLE001
            last = e; time.sleep(6 * (i + 1))
    raise last


def flat(s): return ''.join(c for c in unicodedata.normalize('NFKD', str(s or '')) if not unicodedata.combining(c)).lower().replace('ß', 'ss')


GEN = {
    'AU': r"nature conservation reserve|flora and fauna reserve|flora fauna reserve|nature recreation area|state recreation area|marine national park|national park|state park|wilderness park|wildlife reserve|state reserve|regional reserve|nature refuge|nature park|bushland reserve|historic reserve|resources reserve|resources area|coastal reserve|scenic reserve|regional park|conservation park|conservation reserve|state conservation area|conservation area|nature reserve|flora reserve|"
          r"state forest|forest reserve|historic site|historical reserve|game reserve|karst conservation reserve|aboriginal area|recreation park|recreation area|"
          r"indigenous protected area|marine park|reserve|park|area",
    'DE': r"nationalpark|naturpark|naturschutzgebiet|landschaftsschutzgebiet|biospharenreservat|biospharengebiet|nationales naturmonument|ffh gebiet|"
          r"vogelschutzgebiet|europaisches vogelschutzgebiet|fauna flora habitat gebiet|schutzgebiet|gebiet|nsg|lsg|ffh|spa|und|im|am|an|der|die|das|des|von|bei|zum|zur|"
          r"national park|nature park|nature reserve|biosphere reserve|landscape protection area|flora and fauna reserve|flora fauna reserve|recreation park|natura 2000|"
          r"special protection area|bird sanctuary|national natural monument|protected area|reserve|park|area",
    'GB': r"national nature reserve|local nature reserve|site of special scientific interest|site of significant scientific interest|sssi|nnr|lnr|country park|national park|regional park|nature reserve|"
          r"area of outstanding natural beauty|national landscape|aonb|conservation reserve|protected area|natural area|special area of conservation|"
          r"special protection area|sac|spa|ramsar|rspb|inc|reserve|park|area",
    'JP': r"quasi national park|national park|prefectural natural park|prefectural nature park|prefectural park|prefectural forest|prefectural|natural park|nature park|"
          r"kokuritsu koen|kokutei koen|kenritsu|touritsu|douritsu|furitsu|shizenkouen|kokuteikouen|kokuritsu|kokutei|kouen|chiiki|park",   # Oct 19: 'Prefectural Nature Park' left 'prefectural nature' in every name
}
_EN = (r"natura 2000|protected landscape area|nature and landscape complex|landscape park|ecological site|national park|natural monument|wetland reserve|"
       r"nature park|national recreation trail|biosphere reserve|world heritage site|protected landscape|state trail|biological reserve|marine conservation area|"
       r"conservation area|recreation park|conservation park|national nature reserve|regional park|forest reserve|ramsar site|game reserve|mire landscapes?|"
       r"landscape reserve|protected area|national reserve|nature conservation reserve|historic site|bird sanctuary|recreation site|nature reserve|park|reserve|area")
_LOC = {'PL': r"park narodowy|park krajobrazowy|rezerwat przyrody|rezerwat|obszar chronionego krajobrazu|zespol przyrodniczo krajobrazowy|uzytek ekologiczny|"
              r"pomnik przyrody|stanowisko dokumentacyjne|ostoja|obszar|plb\d*|plh\d*|i|w|na|nad|pod|im",
        'ES': r"parque nacional|parque natural|parque regional|parque rural|reserva natural|reserva natural parcial|paraje natural|monumento natural|paisaje protegido|"
              r"espacio natural protegido|espacio natural|zona especial de conservacion|zec|lic|zepa|humedal|de|del|la|las|los|el|y|en",
        'FR': r"parc national|parc naturel regional|parc naturel|reserve naturelle nationale|reserve naturelle regionale|reserve naturelle|reserve biologique integrale|"
              r"reserve biologique dirigee|reserve biologique|site classe|zps|zsc|sic|de|du|des|la|le|les|et|d|l|en|sur|aux|au",
        'CH': r"naturschutzgebiete|naturschutzgebiet|nsg|wasser und zugvogelreservat|zugvogelreservat|jagdbanngebiet|waldreservat|naturpark|regionaler naturpark|nationalpark|naturdenkmal|moorlandschaft|auengebiet|reserve naturelle|parc naturel|parco naturale|"
              r"riserva naturale|parco|monumento naturale|zona|und|im|am|an|der|die|das|des|von|bei|de|du|des|la|le|les|et|d|l|e|di|del|della|dei|e dintorni",
        'AT': r"naturschutzgebiete|landschaftsschutzgebiete|europaschutzgebiete|vogelschutzgebiet|naturschutzgebiet|landschaftsschutzgebiet|europaschutzgebiet|nsg|lsg|esg|naturpark|nationalpark|naturdenkmal|geschutzter landschaftsteil|ramsar|"
              r"und|im|am|an|der|die|das|des|von|bei|zum|zur",
        # Oct 19: next 8 busiest programs (official words in each language; longer phrases first)
        'NL': r"nationaal park|natuurgebied|natuurreservaat|natuurmonument|beschermd natuurmonument|staatsnatuurmonument|landgoed|bos|boswachterij|duinen|"
              r"vogelrichtlijngebied|habitatrichtlijngebied|natura 2000 gebied|gebied|park|het|de|en|van|der|den|op|aan|bij|in",
        'PT': r"parque nacional|parque natural|reserva natural|paisagem protegida|monumento natural|area protegida|area de paisagem protegida|sitio de interesse comunitario|"
              r"zona especial de conservacao|zona de protecao especial|zec|zpe|sic|ptcon\d*|ptzpe\d*|mata nacional|perimetro florestal|de|da|do|das|dos|e|em",
        'SE': r"nationalpark|naturreservat|naturvardsomrade|kulturreservat|djurskyddsomrade|fagelskyddsomrade|biotopskyddsomrade|naturminne|"
              r"vattenskyddsomrade|ekopark|reservat|omradet|omrade|och|i|vid|pa",
        'CZ': r"narodni park|chranena krajinna oblast|narodni prirodni rezervace|prirodni rezervace|narodni prirodni pamatka|prirodni pamatka|prirodni park|"
              r"ptaci oblast|evropsky vyznamna lokalita|evl|chko|nprp|nprr|pr|pp|np|a|v|na|u|pod|nad",
        'SI': r"narodni park|krajinski park|regijski park|naravni rezervat|strogi naravni rezervat|naravni spomenik|zavarovano obmocje|obmocje|pri|in|na|v|pod|nad",
        'NO': r"nasjonalpark|naturreservat|landskapsvernomrade|landskapsvernomradet|naturvernomrade|naturminne|biotopvernomrade|dyrelivsfredning|plantelivsfredning|"
              r"fuglefredningsomrade|marint verneomrade|verneomrade|omradet|og|i|pa|ved",
        'RO': r"parcul national|parc national|parcul natural|parc natural|rezervatia naturala|rezervatie naturala|rezervatia|rezervatie|monument al naturii|"
              r"sit de importanta comunitara|arie de protectie speciala avifaunistica|arie naturala protejata|rosci\d*|rospa\d*|sci|spa|parcul|lacul|de|din|si|la|al",
        'IT': r"parco nazionale|parco naturale regionale|parco naturale|parco regionale|riserva naturale statale|riserva naturale regionale|riserva naturale orientata|"
              r"riserva naturale|oasi|monumento naturale|area marina protetta|area naturale protetta|zona speciale di conservazione|zona di protezione speciale|"
              r"sito di importanza comunitaria|zsc|zps|sic|di|del|della|dei|delle|degli|dello|e|ed|in|al|alla|sul|lago|monte|valle",
        # Oct 19 PM (Brandon: 'give them something to do'): the rest of the EEA countries that use the Latin alphabet
        'BE': r"nationaal park|natuurreservaat|erkend natuurreservaat|vlaams natuurreservaat|bosreservaat|natuurpark|parc naturel|reserve naturelle domaniale|reserve naturelle agreee|reserve naturelle|"
              r"reserve forestiere|zone humide d interet biologique|site de grand interet biologique|habitatrichtlijngebied|vogelrichtlijngebied|het|de|en|van|der|du|des|la|le|les|et|d|l",
        'DK': r"nationalpark|naturpark|naturreservat|vildtreservat|fredning|fredet omrade|habitatomrade|fuglebeskyttelsesomrade|natura 2000 omrade|omrade|og|ved|i|pa",
        'FI': r"kansallispuisto|luonnonpuisto|luonnonsuojelualue|yksityinen luonnonsuojelualue|soidensuojelualue|lehtojensuojelualue|vanhojen metsien suojelualue|"
              r"harjujensuojelualue|lintuvesiensuojelualue|kansallinen kaupunkipuisto|retkeilyalue|eramaa alue|eramaa|natura alue|suojelualue|alue|ja",
        'HU': r"nemzeti park|tajvedelmi korzet|termeszetvedelmi terulet|termeszeti emlek|kiemelt jelentosegu termeszetmegorzesi terulet|kulonleges madarvedelmi terulet|"
              r"kulonleges termeszetmegorzesi terulet|natura 2000 terulet|terulet|es",
        'SK': r"narodny park|chranena krajinna oblast|narodna prirodna rezervacia|prirodna rezervacia|narodna prirodna pamiatka|prirodna pamiatka|chraneny areal|"
              r"chranene vtacie uzemie|uzemie europskeho vyznamu|chku|npr|pr|pp|np|a|v|na|pod|nad|pri",
        'HR': r"nacionalni park|park prirode|strogi rezervat|posebni rezervat|park suma|znacajni krajobraz|spomenik prirode|spomenik parkovne arhitekture|"
              r"podrucje ocuvanja znacajno za ptice|podrucje ocuvanja znacajno za vrste i stanisne tipove|i|na|u|kod",
        'IE': r"special area of conservation|special protection area|natural heritage area|proposed natural heritage area|statutory nature reserve|sac|spa|nha|pnha",
        'LT': r"nacionalinis parkas|regioninis parkas|valstybinis rezervatas|gamtinis rezervatas|biosferos poligonas|draustinis|rezervatas|ir|prie",
        'LV': r"nacionalais parks|dabas parks|dabas liegums|dabas rezervats|aizsargajamo ainavu apvidus|dabas piemineklis|biosferas rezervats|mikroliegums|un",
        'EE': r"rahvuspark|looduskaitseala|maastikukaitseala|hoiuala|kaitseala|looduspark|loodusala|linnuala|ja",
        'LU': r"zone protegee d interet national|zone protegee|reserve naturelle|reserve forestiere|naturschutzgebiet|naturpark|parc naturel|zone habitat|zone oiseaux|de|du|des|la|le|les|et|d|l|an|der|vum|am"}
for _c in EU: GEN[_c] = _LOC[_c] + r'|parc|parco|parque|krajobrazowy|naturalny|nacional|regional|' + _EN   # local (longer) words first
KINDS = {
    'AU': [('np', r'national park'), ('cp', r'conservation park|conservation reserve|conservation area|n\.\s?c\.\s?r|\bc\.\s?a\.'), ('nr', r'nature reserve|flora reserve|game reserve|\bn\.\s?r\.|f\.\s?f\.\s?r|\bf\.\s?r\b'),
           ('sf', r'state forest|forest reserve'), ('rp', r'regional park|recreation'), ('hist', r'historic'), ('mp', r'marine')],
    'DE': [('np', r'nationalpark|national park'), ('nat', r'naturpark|nature park'), ('nsg', r'naturschutzgebiet|\bnsg\b|nature reserve'),
           ('lsg', r'landschaftsschutzgebiet|\blsg\b|landscape protection'), ('br', r'biospharen|biosphere'),
           ('ffh', r'\bffh\b|fauna flora habitat|flora and fauna|natura 2000'), ('spa', r'vogelschutz|special protection area|bird sanctuary|natura 2000'),
           ('nnm', r'naturmonument|natural monument')],
    'GB': [('nnr', r'national nature reserve|\bnnr\b'), ('lnr', r'local nature reserve|\blnr\b'), ('cp', r'country park'), ('sssi', r'scientific interest|\bsssi\b'),
           ('np', r'national park'), ('rp', r'regional park'), ('aonb', r'national landscape|outstanding natural beauty|\baonb\b'), ('sac', r'special area of conservation|\bsac\b'), ('spa', r'special protection area|\bspa\b')],
    'JP': [('np', r'(?<!quasi.)national park|国立公園'), ('qnp', r'quasi.?national park|国定公園'), ('pnp', r'prefectural|県立')],
}
for _c in EU: KINDS[_c] = [('n2k', r'natura 2000|\bzps\b|\bzsc\b|\bzepa\b|\bzec\b')]
KINDS['CO'] = [('pnn', r'parque nacional|national (natural )?park|national nature reserve|reserva nacional natural|santuario|sanctuary'), ('pnr', r'parque natural regional|regional (natural )?park'),
               ('rn', r'reserva natural|nature reserve|reserva forestal|forest reserve'), ('dmi', r'distrito|management district|conservation area|area de recreacion|recreation area')]
KINDS['ZA'] = [('np', r'national park'), ('nr', r'nature reserve|game reserve|provincial park|reserve'), ('pe', r'protected environment'), ('mpa', r'marine protected area|marine reserve'), ('wa', r'wilderness|world heritage')]
KINDS['CL'] = [('pn', r'parque nacional|national park'), ('rn', r'reserva nacional|national reserve|reserva forestal'), ('mn', r'monumento natural|natural monument'),
               ('sn', r'santuario|sanctuary|conservation area|humedal|wetland|area marina|marine')]


ABBR = [(r'\bn\.\s?c\.\s?r\b\.?', ' nature conservation reserve '), (r'\bf\.\s?f\.\s?r\b\.?', ' flora fauna reserve '),
        (r'\bn\.\s?r\b\.?', ' nature reserve '), (r'\bf\.\s?r\b\.?', ' flora reserve '), (r'\bc\.\s?a\b\.', ' conservation area '), (r'\bs\.\s?f\b\.', ' state forest '),
        (r'\bb\.\s?r\b\.', ' bushland reserve '), (r'\bh\.\s?r\b\.', ' historic reserve ')]


def norm(cc, s):
    s = flat(s).replace('&', ' and ')
    if cc == 'AU':
        for a, b in ABBR: s = re.sub(a, b, s)
        s = re.sub(r'\bmt\b\.?', 'mount', s); s = re.sub(r'\bst\b\.?', 'saint', s)
        s = re.sub(r'\b[a-z]\d{1,4}\b', ' ', s)   # map codes like 'H57' (Victoria bushland reserves)
    if cc in ('DE', 'AT', 'CH'):
        for a, b in (('ae', 'a'), ('oe', 'o'), ('ue', 'u')): s = s.replace(a, b)   # Schwaebisch = Schwäbisch
    if cc in EU:
        s = re.sub(r"\b[a-z]{2}\d{6,8}\b", ' ', s)              # Natura codes inside POTA names (FR4100198)
        s = re.sub(r'^\s*\d{5,8}\s+', ' ', s)                   # Oct 19: Swedish register numbers in front ('2001220 Padjelanta')
        s = re.sub(r"\b(l|d|s|qu)['’]", ' ', s)                 # l'Etang, d'Arc
        s = re.sub(r'\bste?\b\.?', lambda m: 'sainte' if m.group(0).startswith('ste') else 'saint', s)
        s = s.replace('ł', 'l').replace('ø', 'o').replace('æ', 'ae').replace('đ', 'd')
    s = re.sub(r'\(.*?\)', ' ', s); s = re.sub(r"[’'`.]", '', s); s = re.sub(r'[-/,]', ' ', s)
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    s = re.sub(r'\b(' + GEN[cc] + r'|the|of|and)\b', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    if cc == 'JP':
        s = s.replace(' ', '')
        for a, b in (('ou', 'o'), ('oo', 'o'), ('uu', 'u'), ('aa', 'a'), ('ii', 'i'), ('nm', 'mm'), ('nb', 'mb'), ('np', 'mp')): s = s.replace(a, b)
    return s


KKS = None
def romaji(t):
    # Japanese layer names → Hepburn romaji so they can meet POTA's English names (pykakasi, installed in the workflow)
    global KKS
    if not re.search(r'[\u3040-\u30ff\u4e00-\u9fff]', t or ''): return t
    if KKS is None:
        try:
            import pykakasi; KKS = pykakasi.kakasi()
        except Exception: KKS = False  # noqa: BLE001
    if not KKS: return t
    return ' '.join(x['hepburn'] for x in KKS.convert(t))


def kinds(cc, s): s = flat(s) + ' ' + str(s or ''); return {k for k, r in KINDS[cc] if re.search(r, s)}
def codes(s): return set(re.findall(r'\b[a-z]\d{1,4}\b', flat(s)))


# Oct 24: Upper / Lower / North / South / East / West tell two halves of one place apart (the US key's Oct 22 rule,
# where Upper AND Lower White Oak Lake had both joined the one White Oak Lake State Park). Ported with the words of
# each language, grouped so that POTA's English 'North X' still meets the map's 'Nord X'. Words that mean something
# else in a language are left out of it: French 'sur' is 'on' (Villeneuve-sur-Lot), not Spanish 'south'. Japanese is
# skipped: kita / minami sit inside ordinary place names (Kitakyushu) and norm() removes the spaces there anyway.
SIDEW = {'n': 'north northern nord nordre norra noord norte nordlich polnocny severni severny', 's': 'south southern sud sondre sodra zuid sul sur meridionale sudlich poludniowy jizni juzny',
         'e': 'east eastern est ost ostre ostra oost este leste oriental ostlich wschodni vychodni', 'w': 'west western ouest vestre vastra oeste occidental westlich zachodni zapadni',
         'u': 'upper ober obere oberer haut haute alto alta gorny horni ovre ylinen', 'l': 'lower unter untere unterer bas basse bajo baja basso bassa dolny dolni nedre alinen', 'm': 'middle mittel mittlere'}
SIDE = {w: k for k, ws in SIDEW.items() for w in ws.split()}
SIDE_NOT = {'FR': {'sur'}, 'CH': {'sur'}, 'BE': {'sur'}, 'LU': {'sur'},   # French-speaking countries: 'sur' is a preposition, not a side
            'NO': {'alta', 'alto'}, 'SE': {'alta', 'alto'}, 'FI': {'alta', 'alto'}, 'DK': {'alta', 'alto'}}   # Alta is a Norwegian town


def _side(cc, s):
    if cc == 'JP': return set()
    skip = SIDE_NOT.get(cc, set())
    return {SIDE[w] for w in re.split(r'[\s/\-–,]+', re.sub(r'\(.*?\)', ' ', flat(s))) if w in SIDE and w not in skip}   # 'Dzawadi/Upper' splits; bracket text is not a side


def same_name(cc, a, b):
    if cc == 'AU':
        ca, cb = codes(a), codes(b)
        if ca and cb and not (ca & cb): return False      # 'Nullan I106' is not 'Nullan I108' (Oct 18 review)
    if _side(cc, a) != _side(cc, b): return False       # Oct 24: Upper White Oak Lake is not White Oak Lake
    a, b = norm(cc, a), norm(cc, b)
    if not a or not b: return False
    if a == b: return True
    if cc in ('LT', 'LV', 'EE'):   # Oct 20: Baltic names change their endings ('Aukstaitija' = 'Aukstaitijos'): word by word, same stem
        wa, wb = a.split(), b.split()
        def st(x, y):
            n = 0
            while n < min(len(x), len(y)) and x[n] == y[n]: n += 1
            return n >= 5 and n >= min(len(x), len(y)) - 3
        if len(wa) == len(wb) and all(st(x, y) for x, y in zip(wa, wb)): return True
    sh, lo = (a, b) if len(a) < len(b) else (b, a)
    return len(sh) > 4 and lo.startswith(sh) and len(sh) / len(lo) >= 0.6
OWNK = [('np', r'national park|nationaal park|nationalpark|narodni park|parco nazionale|parque nacional|parcul national|nasjonalpark|park narodowy|parc national'),
        ('lp', r'landscape park|krajinski park|regijski park|regional park|park krajobrazowy|landschaftspark'),
        ('nat', r'nature park|parco naturale|parque natural|parcul natural|parc naturel|naturpark|prirodni park'),
        ('nr', r'nature reserve|naturreservat|naravni rezervat|rezervatia naturala|rezervatie naturala|riserva naturale|natuurreservaat|reserva natural|prirodni rezervace|rezerwat')]
def ownk(s): f = flat(s); return {k for k, r in OWNK if re.search(r'\b(' + r + r')\b', f)}


# Oct 19: what each EEA national designation code means (official Eionet vocabulary 'Designation type code',
# dd.eionet.europa.eu/vocabulary/cdda/designationTypeCodeValue). One park in the CDDA list is often filed under several codes
# with no kind word in its name; the code's own label ('Nature Reserve', 'Nationalpark'…) says which one is which.
DKIND = [('np', r'national park|nationaal park|nationalpark|nasjonalpark|park narodowy|parque nacional|parc national|parco nazionale|narodni park|parcul national|parque natural nacional|kansallispuisto|nemzeti park|narodny park|nacionalni park|nacionalinis parkas|nacionalais parks|rahvuspark'),
         ('nnr', r'national nature reserve|narodni prirodni rezervace|reserve naturelle nationale|riserva naturale statale|national reserve'),
         ('nr', r'nature reserve|naturreservat|natuurreservaat|naturschutzgebiet|rezerwat|reserva natural|riserva naturale|rezervatia|rezervatie|prirodni rezervace|naravni rezervat|reserve naturelle|nature conservation reserve|natural reserve|state reserve|regional reserve|luonnonpuisto|luonnonsuojelualue|termeszetvedelmi terulet|prirodna rezervacia|posebni rezervat|strogi rezervat|gamtinis rezervatas|valstybinis rezervatas|draustinis|dabas rezervats|dabas liegums|looduskaitseala|vildtreservat'),
         ('lp', r'landscape park|protected landscape|landscape protection|landscape reserve|park krajobrazowy|chronionego krajobrazu|landschaftsschutz|chranena krajinna oblast|landskapsvern|paisagem protegida|paisaje protegido|krajinski park|regijski park|nature and landscape complex|zespol przyrodniczo|tajvedelmi korzet|znacajni krajobraz|aizsargajamo ainavu apvidus|maastikukaitseala'),
         ('nat', r'nature park|naturpark|parque natural|parc naturel|parco naturale|parco regionale|prirodni park|parcul natural|regional park|provincial park|natuurpark|park prirode|dabas parks|looduspark|regioninis parkas'),
         ('nm', r'natural monument|nature monument|pomnik przyrody|prirodni pamatka|naturminne|naturdenkmal|monumento natural|monumento naturale|monument naturel|naravni spomenik|monument al naturii|national monument')]
def dkinds(s):
    f = flat(s); k = {k for k, r in DKIND if re.search(r'\b(' + r + r')\b', f)}
    if 'nnr' in k: k.discard('nr')   # a national nature reserve is not the plain one
    return k
DT = None
def eea_dt():
    """{code: label} from the Eionet vocabulary (CSV, then JSON, then the page view); cached in data/world-key/eea-designations.json."""
    global DT
    if DT is not None: return DT
    cf = OUT / 'eea-designations.json'; DT = {}
    try: DT = json.load(open(cf))
    except Exception: pass  # noqa: BLE001
    if len(DT) > 300: return DT
    base = 'https://dd.eionet.europa.eu/vocabulary/cdda/designationTypeCodeValue'
    def raw(u):
        with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=90) as r: return r.read().decode('utf-8', 'replace')
    got = {}
    try:
        import csv, io
        rows = list(csv.reader(io.StringIO(raw(base + '/csv'))))
        h = [x.lower() for x in rows[0]]
        li = next(i for i, x in enumerate(h) if x.startswith('label')); ni = next(i for i, x in enumerate(h) if x.startswith('notation'))
        got = {r[ni].strip(): r[li].strip() for r in rows[1:] if len(r) > max(li, ni) and r[ni].strip()}
    except Exception as e: notice('EEA designation types', f'CSV not read: {e}')  # noqa: BLE001
    if len(got) < 300:
        for pg in range(1, 80):
            try: t = raw(base + f'/view?page={pg}')
            except Exception: break  # noqa: BLE001
            n0 = len(got)
            for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', t, re.S):
                cells = [re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', c)).strip() for c in re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)]
                nt = next((c for c in cells if re.fullmatch(r'[A-Z]{2}[0-9A-Z]{2,3}', c)), None)
                if nt and len(cells) > 1: got[nt] = cells[1]
            if len(got) == n0: break
            time.sleep(.4)
    if len(got) > len(DT): DT = got; json.dump(DT, open(cf, 'w'), ensure_ascii=False, indent=0, sort_keys=True)
    notice('EEA designation types', f'{len(DT)} codes known; sample: ' + '; '.join(f'{k}={v}' for k, v in list(sorted(DT.items()))[:6]))
    return DT


def words(cc, s): return set(w for w in norm(cc, s).split() if len(w) > 2)


def rings_of(g):
    if not g: return []
    if 'rings' in g: return g['rings']
    t, c = g.get('type'), g.get('coordinates') or []
    if t == 'Polygon': return c
    if t == 'MultiPolygon': return [r for p in c for r in p]
    return []
def bbox(rs):
    xs = [p[0] for r in rs for p in r]; ys = [p[1] for r in rs for p in r]
    return [min(xs), min(ys), max(xs), max(ys)] if xs else None
def thin(rs, n=None): n = n or THIN_N; return [r[::max(1, len(r) // n)] for r in rs]   # keep it light: only used for 'pin inside'
def in_ring(x, y, r):
    ins = False; j = len(r) - 1
    for i in range(len(r)):
        xi, yi, xj, yj = r[i][0], r[i][1], r[j][0], r[j][1]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / ((yj - yi) or 1e-15) + xi: ins = not ins
        j = i
    return ins
def inside(la, lo, rs): return sum(1 for r in rs if in_ring(lo, la, r)) % 2 == 1
def near(la, lo, b, pad): return b and b[0] - pad <= lo <= b[2] + pad and b[1] - pad <= la <= b[3] + pad


NAMEF = ['nom_site', 'leg_name', 'nazwa', 'NAME', 'Name', 'name', 'NNR_NAME', 'LNR_NAME', 'CP_NAME', 'SSSI_NAME', 'PA_NAME', 'NAME_E', 'NAME_EN', 'SITE_NAME', 'sitename', 'NAMEX', '名称', '公園名', 'nombre', 'NOMBRE', 'nombre_ap', 'NOMBRE_AP', 'nom_ap', 'NOM_AP', 'CUR_NME', 'cur_nme', 'PA_NAME']   # Oct 30: CO / CL (Spanish) + ZA (SAPAD CUR_NME)
TYPEF = ['TYPE', 'Type', 'type', 'PA_TYPE', 'DESIGNATION', 'desig', 'GAZ_TYPE', 'KIND', '種別', 'TYPE_E']


def pick(a, names):
    for n in names:
        for k in a:
            if k.lower() == n.lower() and a[k] not in (None, ''): return str(a[k])
    return ''
def pick_name(a):
    # known name fields first; else any English-looking *name* field (Welsh layers: SSSI_Name / Name_Welsh…)
    v = pick(a, NAMEF)
    if v: return v
    for k in a:
        if re.search(r'name|enw|nombre|_nme$', k, re.I) and not re.search(r'welsh|cymraeg|_cy$|^cy_|enw', k, re.I) and a[k] not in (None, ''): return str(a[k])
    return ''


def pull_arcgis(label, url, wheres=None):
    for w in (wheres or ['1=1']):
        got = pull_arcgis1(label, url, w)
        if got: return got
    return []


def pull_arcgis1(label, url, where):
    info = fetch(url + '?f=json'); mx = int(info.get('maxRecordCount') or 1000); oidf = info.get('objectIdField') or 'OBJECTID'
    if not oidf or oidf == 'OBJECTID': oidf = next((f['name'] for f in info.get('fields', []) if f.get('type') == 'esriFieldTypeOID'), oidf)
    fnames = [f['name'] for f in info.get('fields', [])]
    notice(f'{label} fields', ', '.join(fnames)[:900])
    recs, off = [], 0
    while True:
        qq = {'where': where, 'outFields': '*', 'returnGeometry': 'true', 'outSR': 4326, 'maxAllowableOffset': DETAIL,
              'geometryPrecision': PREC, 'f': 'json', 'resultOffset': off, 'resultRecordCount': min(mx, 1000), 'orderByFields': oidf}
        try:
            j = fetch(url + '/query?' + urllib.parse.urlencode(qq))
        except Exception:  # noqa: BLE001
            if DETAIL >= 0.01: raise
            qq.update(maxAllowableOffset=0.01, geometryPrecision=3)      # the server refused the finer outline: today's one
            j = fetch(url + '/query?' + urllib.parse.urlencode(qq))
        fs = j.get('features', [])
        for f in fs:
            a = f.get('attributes') or {}; rs = rings_of(f.get('geometry'))
            recs.append({'id': a.get(oidf), 'n': pick_name(a), 'ty': pick(a, TYPEF), 'src': label, '_bb': bbox(rs), '_r': thin(rs), '_a': a,
                         'code': str(a.get('SITECODE') or a.get('nationalId') or ''), 'dc': str(a.get('designationTypeCode') or a.get('SITETYPE') or '')})
        if j.get('error'): notice(f'{label} query error', j.get('error')); break
        if not fs or (not j.get('exceededTransferLimit') and len(fs) < min(mx, 1000)): break
        off += len(fs); time.sleep(.5)
    return recs


def pull_find(label, url, rx):
    # a map service with many layers: take the ones whose NAME matches (e.g. Queensland 'State forest'), all of them
    info = fetch(url + '?f=json'); got = []
    lays = [l for l in (info.get('layers') or []) if re.search(rx, l.get('name', ''), re.I) and not l.get('subLayerIds')]
    notice(f'{label} layers', ', '.join(f"{l['id']}:{l['name']}" for l in lays) or 'none matched: ' + ', '.join(l.get('name', '') for l in (info.get('layers') or [])[:40]))
    for l in lays: got += pull_arcgis(label, url + '/' + str(l['id']))
    return got


FMT, TOLD = {}, set()
def pull_wfs(label, url, typ):
    recs, start, step = [], 0, 1000
    while True:
        q = {'SERVICE': 'WFS', 'VERSION': '2.0.0', 'REQUEST': 'GetFeature', 'TYPENAMES': typ, 'OUTPUTFORMAT': 'application/json', 'SRSNAME': 'EPSG:4326',
             'COUNT': step, 'STARTINDEX': start}
        j = None
        for fmt in ([FMT[url]] if url in FMT else ['application/json', 'application/geo+json', 'json', 'geojson', 'application/json; subtype=geojson']):
            q['OUTPUTFORMAT'] = fmt
            try:
                j = fetch(url + '?' + urllib.parse.urlencode(q), tries=2); FMT[url] = fmt; break
            except Exception as e:  # noqa: BLE001
                try:
                    with urllib.request.urlopen(urllib.request.Request(url + '?' + urllib.parse.urlencode(q), headers=UA), timeout=120) as rr: body = rr.read(400)
                except Exception as e2: body = str(e2).encode()  # noqa: BLE001
                if (url, fmt) not in TOLD: TOLD.add((url, fmt)); notice(f'WFS {fmt}', body.decode('utf-8', 'replace'))
        if j is None: raise RuntimeError('no JSON output format worked')
        fs = j.get('features', [])
        for f in fs:
            p = f.get('properties') or {}; rs = rings_of(f.get('geometry'))
            # EPSG:4326 in WFS 2.0 can come back lat,lon: swap when the 'x' looks like a latitude for this country
            if rs and abs(rs[0][0][0]) > 40 and abs(rs[0][0][1]) < 20: rs = [[[q2[1], q2[0]] for q2 in r] for r in rs]
            recs.append({'id': f.get('id'), 'n': pick_name(p), 'ty': pick(p, TYPEF) or label, 'src': label, '_bb': bbox(rs), '_r': thin(rs), '_a': p})
        if len(fs) < step: break
        start += step; time.sleep(.5)
    if recs and not any(r['n'] for r in recs[:50]): notice(f'{label} name field?', ', '.join(list(recs[0]['_a'].keys())[:40]))
    return recs


JSUF = r'(国立公園|国定公園|(都|道|府|県)立自然公園|自然公園|県立公園|公園)$'
def jclean(t):
    # Oct 19: A10 names end in 地域 ('石鎚国定公園地域') and some start with the kind ('県立自然公園船形連峰'), so the old end-only strip missed them
    t = re.sub(r'(地域|区域|地区)$', '', str(t or '').strip())
    return re.sub(r'(国立|国定|都立|道立|府立|県立)?(自然)?公園', '', t).strip()
def jparts(t): return [q for q in (jclean(x) for x in re.split(r'[・、,\u3000]|\s{2,}', str(t or ''))) if q]   # one area can carry several park names
def jstrip(t): return re.sub(r'\s', '', jclean(t))
def jkind(t):
    t = str(t or '')
    return {'np'} if '国立公園' in t else {'qnp'} if '国定公園' in t else {'pnp'} if re.search(r'(都|道|府|県)立|自然公園', t) else set()


def pull_a10(label, page):
    import io, zipfile
    try: import shapefile
    except Exception:  # noqa: BLE001
        import subprocess, sys; subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', 'pyshp'], check=False); import shapefile
    with urllib.request.urlopen(urllib.request.Request(page, headers=UA), timeout=120) as r: html = r.read().decode('utf-8', 'replace')
    # Oct 19: the page names each file more than once (different paths, some 404): one download per prefecture, try each path
    grp = {}
    for ln in re.findall(r"[\w./-]*A10-15_\d\d_GML\.zip", html): grp.setdefault(ln.split('/')[-1], []).append(ln)
    links = sorted(grp)
    recs, told = [], False
    for ln in links:
        z, err = None, None
        for v in sorted(set(grp[ln]), key=lambda q: -len(q)):
            try:
                with urllib.request.urlopen(urllib.request.Request(urllib.parse.urljoin(page, v), headers=UA), timeout=300) as r: z = zipfile.ZipFile(io.BytesIO(r.read())); break
            except Exception as e: err = e  # noqa: BLE001
        if not z: notice(label, f'{ln} FAILED: {err}'); continue
        for sp in [n for n in z.namelist() if n.lower().endswith('.shp')]:
            b = sp[:-4]
            try: rd = shapefile.Reader(shp=io.BytesIO(z.read(sp)), dbf=io.BytesIO(z.read(b + '.dbf')), shx=io.BytesIO(z.read(b + '.shx')), encoding='cp932')
            except Exception as e: notice(label, f'{sp}: {e}'); continue  # noqa: BLE001
            fn = [f[0] for f in rd.fields[1:]]
            for i, (shp, rec) in enumerate(zip(rd.shapes(), rd.records())):
                a = dict(zip(fn, list(rec)))
                jv = [str(v) for v in a.values() if isinstance(v, str) and re.search(r'[぀-ヿ一-鿿]', v)]
                # Oct 19: OBJ_NAME = the park's name (CTV_NAME = towns it covers; using it joined city names like 鈴鹿市 to parks)
                on = str(a.get('OBJ_NAME') or '').strip()
                nm = on if re.search(r'[぀-ヿ一-鿿]', on) else next((v for v in jv if re.search(r'公園', v)), '')
                ty = next((v for v in jv if re.search(r'国立公園|国定公園|自然公園', v) and v != nm), '') or nm
                pts, parts = shp.points, list(shp.parts) + [len(shp.points)]
                rs = [[list(p) for p in pts[parts[k]:parts[k + 1]]] for k in range(len(parts) - 1)]
                recs.append({'id': f'a10:{ln[-10:-8]}:{b.split("/")[-1]}:{i}', 'n': nm, 'nj': nm, 'ty': ty, 'src': label, '_bb': bbox(rs), '_r': thin(rs), '_a': a,
                             'code': '', 'dc': '', '_k0': jkind(nm) | jkind(ty)})
            if not told:
                blank = next((r['_a'] for r in recs if not r['n']), None)
                if blank: notice(f'{label} blank-name row', '; '.join(f'{k}={v}' for k, v in blank.items())[:900])
                told = True; notice(f'{label} fields', f'{sp}: ' + ', '.join(fn) + ' | sample: ' + ' / '.join(f"{r['n']} [{r['ty']}]" for r in recs[-3:]))
        time.sleep(.4)
    # Oct 19: most zone rows (special zones etc.) have a blank OBJ_NAME; they share PREFEC_CD + THEMA_NO + AREA_CD with the named row
    # of the same park. Fill a blank row ONLY when exactly one name is known for that key (never a guess between two parks).
    def key(r): a = r['_a']; return (str(a.get('PREFEC_CD')), str(a.get('THEMA_NO')), str(a.get('AREA_CD')))
    names = {}
    for r in recs:
        if r['n']: names.setdefault(key(r), set()).add(r['n'])
    fill = amb = 0
    for r in recs:
        if r['n']: continue
        nn = names.get(key(r)) or set()
        if len(nn) == 1:
            r['n'] = r['nj'] = next(iter(nn)); r['ty'] = r['ty'] or r['n']; r['_k0'] = jkind(r['n']) | jkind(r['ty']); fill += 1
        elif nn: amb += 1
    # AREA_CD turned out not to be a park code (Oct 19 run: 0 filled). Second try by place: a blank zone row that sits inside the box of
    # named rows of ONE park only (same prefecture) takes that name; two parks around it = left blank.
    byp = {}
    for r in recs:
        if r['n'] and r['_bb']: byp.setdefault(str(r['_a'].get('PREFEC_CD')), []).append(r)
    sp = 0
    for r in recs:
        if r['n'] or not r['_bb']: continue
        b = r['_bb']; e = .002
        nn = {q['n'] for q in byp.get(str(r['_a'].get('PREFEC_CD')), []) if q['_bb'][0] - e <= b[0] and q['_bb'][1] - e <= b[1] and q['_bb'][2] + e >= b[2] and q['_bb'][3] + e >= b[3]}
        if len(nn) == 1:
            r['n'] = r['nj'] = next(iter(nn)); r['ty'] = r['ty'] or r['n']; r['_k0'] = jkind(r['n']) | jkind(r['ty']); sp += 1
    lay = {}
    for r in recs: lay.setdefault(str(r['_a'].get('LAYER_NO')), [0, 0])[0 if r['n'] else 1] += 1
    rem = [f"{r['_a'].get('LAYER_NO')}:{r['_a'].get('REMARK_STR')}" for r in recs if not r['n'] and str(r['_a'].get('REMARK_STR') or '').strip()][:8]
    notice(label, f'blank names filled by place: {sp}; by LAYER_NO [named, blank]: {lay}; REMARK_STR on blank rows: {rem}')
    th = {}
    for r in recs: th.setdefault(str(r['_a'].get('THEMA_NO')), [0, 0])[0 if r['n'] else 1] += 1
    notice(label, f'blank names filled from the same park code: {fill}; two names for one code (left blank): {amb}; by THEMA_NO [named, blank]: {th}')
    notice(label, f'{len(links)} prefecture files, {len(recs)} areas, {len({r["n"] for r in recs})} park names')
    return recs


def pull_a10n(label, url):
    # Japan's national A10 file (FY2010): one shapefile for the whole country; the park NAME is a code (A10_005) in the KSJ
    # codelist NaturalParkNameCd, and A10_003 says the class (1 national, 2 quasi-national, 3 prefectural)
    import io, zipfile
    try: import shapefile
    except Exception:  # noqa: BLE001
        import subprocess; subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', 'pyshp'], check=False); import shapefile
    names = {}
    for cu in ('https://nlftp.mlit.go.jp/ksj/gml/codelist/NaturalParkNameCd-v3_0.html', 'https://nlftp.mlit.go.jp/ksj/gml/codelist/NaturalParkNameCd.html'):
        try:
            with urllib.request.urlopen(urllib.request.Request(cu, headers=UA), timeout=120) as r: raw = r.read()
            html = None
            for enc in ('utf-8', 'cp932', 'euc-jp'):
                try: html = raw.decode(enc); break
                except Exception: pass  # noqa: BLE001
            for tr in re.findall(r'<tr[^>]*>(.*?)</tr>', html or '', re.S):
                cells = [re.sub(r'\s+', '', re.sub(r'<[^>]+>', '', c)) for c in re.findall(r'<td[^>]*>(.*?)</td>', tr, re.S)]
                code = next((c for c in cells if re.fullmatch(r'\d{3,6}', c)), None)
                nm = next((c for c in cells if re.search(r'公園', c)), None)
                if code and nm: names.setdefault(code, []).append(nm)
            if names: break
        except Exception as e: notice(label, f'codelist {cu}: {e}')  # noqa: BLE001
    notice(label, f'{len(names)} park-name codes read')
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=300) as r: z = zipfile.ZipFile(io.BytesIO(r.read()))
    recs = []
    for sp in [n for n in z.namelist() if n.lower().endswith('.shp')]:
        b = sp[:-4]
        rd = None
        for enc in ('cp932', 'utf-8'):
            try: rd = shapefile.Reader(shp=io.BytesIO(z.read(sp)), dbf=io.BytesIO(z.read(b + '.dbf')), shx=io.BytesIO(z.read(b + '.shx')), encoding=enc); rows = rd.records(); break
            except Exception: rd = None  # noqa: BLE001
        if not rd: continue
        fn = [f[0] for f in rd.fields[1:]]
        for i, (shp, rec) in enumerate(zip(rd.shapes(), rows)):
            a = dict(zip(fn, list(rec)))
            cls, code = str(a.get('A10_003') or '').strip(), str(a.get('A10_005') or '').strip()
            want = {'1': '国立公園', '2': '国定公園'}.get(cls)
            cand = names.get(code) or names.get(code.lstrip('0')) or names.get(code.zfill(3)) or []
            nm = next((c for c in cand if want and want in c), None) or next((c for c in cand if not want and not re.search(r'国立公園|国定公園', c)), None) or (cand[0] if len(cand) == 1 else '')
            if not nm: continue
            pts, parts = shp.points, list(shp.parts) + [len(shp.points)]
            rs = [[list(q) for q in pts[parts[k]:parts[k + 1]]] for k in range(len(parts) - 1)]
            recs.append({'id': f'a10n:{i}', 'n': nm, 'nj': nm, 'ty': nm, 'src': label, '_bb': bbox(rs), '_r': thin(rs), '_a': {'A10_003': cls, 'A10_005': code},
                         'code': '', 'dc': '', '_k0': jkind(nm) or ({'np'} if cls == '1' else {'qnp'} if cls == '2' else {'pnp'})})
    notice(label, f'{len(recs)} areas named from the codelist, e.g. ' + ' / '.join(r['n'] for r in recs[:4]))
    return recs


def chpart(s):
    t = str(s or '').lower(); o = set()
    for k, ws in (('n', ('nördlich', 'nord')), ('s', ('südlich', 'sud ', 'sud)')), ('w', ('westlich', 'ouest')), ('e', ('östlich', ' est)', ' est,', 'partie est'))):
        if any(w in t for w in ws): o.add(k)
    if 'teilraum' in t: o.add('t')
    return o


def lv95(e, n):
    # swisstopo's approximate LV95 → WGS84 formulas (about 1 m)
    y, x = (e - 2600000) / 1e6, (n - 1200000) / 1e6
    lo = 2.6779094 + 4.728982 * y + 0.791484 * y * x + 0.1306 * y * x * x - 0.0436 * y ** 3
    la = 16.9023892 + 3.238272 * x - 0.270978 * y * y - 0.002528 * x * x - 0.0447 * y * y * x - 0.0140 * x ** 3
    return [round(lo * 100 / 36, 6), round(la * 100 / 36, 6)]


def pull_chshp(label, col):
    import io, zipfile
    try: import shapefile
    except Exception:  # noqa: BLE001
        import subprocess, sys; subprocess.run([sys.executable, '-m', 'pip', 'install', '--quiet', 'pyshp'], check=False); import shapefile
    j = fetch(f'https://data.geo.admin.ch/api/stac/v0.9/collections/{col}/items?limit=20')
    hrefs = [a['href'] for it in j.get('features', []) for a in it.get('assets', {}).values() if re.search(r'_2056\.shp\.zip$', a.get('href', ''))]
    if not hrefs: notice(label, f'{col}: no shapefile asset'); return []
    with urllib.request.urlopen(urllib.request.Request(hrefs[0], headers=UA), timeout=300) as r: z = zipfile.ZipFile(io.BytesIO(r.read()))
    recs = []
    for sp in [n for n in z.namelist() if n.lower().endswith('.shp')]:
        b = sp[:-4]
        if not all(b + x in z.namelist() for x in ('.dbf', '.shx')): continue
        for enc in ('utf-8', 'cp1252'):
            try:
                rd = shapefile.Reader(shp=io.BytesIO(z.read(sp)), dbf=io.BytesIO(z.read(b + '.dbf')), shx=io.BytesIO(z.read(b + '.shx')), encoding=enc); rows = rd.records(); break
            except Exception: rd = None  # noqa: BLE001
        if not rd or rd.shapeType not in (5, 15, 25): continue
        fn = [f[0] for f in rd.fields[1:]]
        nf = next((f for f in fn if re.search(r'name', f, re.I) and not re.search(r'sub|teil|_fr$|_it$|_en$', f, re.I)), None) or next((f for f in fn if re.search(r'name', f, re.I)), None)
        if not nf: notice(label, f'{sp}: no name field in {fn}'); continue
        for i, (shp, rec) in enumerate(zip(rd.shapes(), rows)):
            a = dict(zip(fn, list(rec)))
            pts, parts = shp.points, list(shp.parts) + [len(shp.points)]
            rs = [[lv95(p[0], p[1]) for p in pts[parts[k]:parts[k + 1]][::max(1, (parts[k + 1] - parts[k]) // 400)]] for k in range(len(parts) - 1)]
            recs.append({'id': f'{col.split(".")[-1]}:{i}', 'n': str(a.get(nf) or ''), 'ty': label, 'src': label, '_bb': bbox(rs), '_r': thin(rs), '_a': {nf: a.get(nf)}, 'code': '', 'dc': '',
                         'tp': str(a.get('TeilObjNum') or ''), 'tpn': str(a.get('TeilObjNam') or '')})   # Oct 19: BLN part number / part name
        notice(f'{label} fields', f'{sp}: name={nf} | ' + ', '.join(fn[:20]) + f' | {len(recs)} areas, e.g. ' + ' / '.join(r['n'] for r in recs[:4]))
        tps = [f"{r['n'][:30]} #{r['tp']} {r['tpn'][:30]}" for r in recs if r.get('tp') and re.search(r'Säntis|Vierwald|Speer', r['n'])]
        if tps: notice(f'{label} parts', ' / '.join(tps[:14]))
    return recs


def wd_ja(P):
    """Japanese name of each POTA park from Wikidata (English label search, item in Japan): bridges POTA's English names to the
    Japanese map names (romaji guesses miss readings like 大山 = Daisen). Cached in data/world-key/jp-wikidata.json."""
    cf = OUT / 'jp-wikidata.json'
    try: C = json.load(open(cf))
    except Exception: C = {}  # noqa: BLE001
    n = 0
    for ref, x in sorted(P.items()):
        if ref in C: continue
        name = re.sub(r'\s+', ' ', x[0]).strip(); got = []
        for q in dict.fromkeys([name, re.sub(r'\s*(Prefectural (Nature |Natural )?Park|Quasi-National Park|National Park|National Government Park|Prefectural Forest)$', '', name)]):
            try:
                r = fetch('https://www.wikidata.org/w/api.php?' + urllib.parse.urlencode({'action': 'wbsearchentities', 'search': q, 'language': 'en', 'limit': 4, 'format': 'json'}), tries=2, timeout=40)
                ids = [h['id'] for h in r.get('search', [])]
                if ids:
                    e = fetch('https://www.wikidata.org/w/api.php?' + urllib.parse.urlencode({'action': 'wbgetentities', 'ids': '|'.join(ids), 'props': 'labels|claims', 'languages': 'ja|en', 'format': 'json'}), tries=2, timeout=40)
                    for qid, v in (e.get('entities') or {}).items():
                        cl = v.get('claims', {})
                        if not any((c['mainsnak'].get('datavalue') or {}).get('value', {}).get('id') == 'Q17' for c in cl.get('P17', [])): continue
                        ja = (v.get('labels', {}).get('ja') or {}).get('value')
                        co = next(((c['mainsnak'].get('datavalue') or {}).get('value') for c in cl.get('P625', [])), None)
                        if co and x[5] and (abs(co['latitude'] - x[5]) > .6 or abs(co['longitude'] - x[6]) > .6): continue   # same name far away
                        if ja: got.append([qid, ja])
            except Exception: pass  # noqa: BLE001
            if got: break
            time.sleep(.25)
        C[ref] = got[:3]; n += 1
        if n % 100 == 0: json.dump(C, open(cf, 'w'), ensure_ascii=False, separators=(',', ':'))
        time.sleep(.25)
    json.dump(C, open(cf, 'w'), ensure_ascii=False, separators=(',', ':'))
    notice('World key JP Wikidata', f'{sum(1 for v in C.values() if v)} of {len(C)} parks have a Japanese name from Wikidata ({n} looked up this run)')
    return {r: {jstrip(j) for _, j in v} for r, v in C.items()}


idx = {}
try: idx = json.load(open(OUT / 'index.json')).get('countries', {})
except Exception: pass  # noqa: BLE001
# Oct 22: the website draws a park's outline straight from the key (KPCB.worldKey), so it needs each ArcGIS source's address
try:
    if __name__ == '__main__':   # not when the golden tests load this file
        save_json(OUT / 'layers.json', {x[0]: x[2] for v in SRC.values() for x in v if x[1] in ('arcgis', 'arcgis_alt')}, indent=1)
except Exception as e: notice('World key layers', e)  # noqa: BLE001
for cc in COUNTRIES:
    try: P = json.load(open(f'data/parkinfo/{cc}.json'))['parks']
    except Exception: notice(f'World key {cc}', 'no park list yet (data/parkinfo); skipped'); continue  # noqa: BLE001
    recs = wload(cc) if CMODE in ('use', 'only') else None
    if recs is None and CMODE == 'only':
        print(f'{cc}: no saved outlines yet; skipped (saved-copy-only run)', flush=True); continue
    if recs is None:
        recs, failed = [], False
        for s in SRC.get(cc, []):
            try:
                if s[1] == 'arcgis_alt' and any(r['src'].startswith('IGN Géoplateforme ZNIEFF') for r in recs): continue   # the same zones already came from IGN
                got = pull_arcgis(s[0], s[2], s[3] if len(s) > 3 and s[1] != 'arcgisfind' else None) if s[1] in ('arcgis', 'arcgis_alt') else pull_find(s[0], s[2], s[3]) if s[1] == 'arcgisfind' else pull_a10(s[0], s[2]) if s[1] == 'a10' else pull_a10n(s[0], s[2]) if s[1] == 'a10n' else pull_chshp(s[0], s[2]) if s[1] == 'chshp' else pull_wfs(s[0], s[2], s[3])
                recs += got; print(f'{cc} {s[0]}: {len(got)}', flush=True)
            except Exception as e:  # noqa: BLE001
                notice(f'World key {cc}', f'{s[0]} FAILED: {e}'); failed = True
        # Oct 22: a source that did not answer must not cost the country its parks: use the last saved copy instead,
        # and never save a half-read copy over a good one
        old = wload(cc) if failed else None
        if old and len(recs) < .97 * len(old):   # only when the read came back SHORT (see the US key)
            notice(f'World key {cc}', f'a source did not answer ({len(recs)} areas read, {len(old)} saved), so the saved copy was used (nothing dropped)'); recs = old
        elif recs and CMODE in ('use', 'refresh'): wsave(cc, recs)
    if not recs: continue
    if cc == 'JP':
        for r in recs:
            r['_k0'] = r.get('_k0') or (kinds(cc, r['n']) | kinds(cc, r['ty']))
            if r.get('src', '').startswith('Ministry'): r['_k0'] = {'np'}          # nps_all = national parks only
            if r['n']:
                r['nj'] = r.get('nj') or r['n']; r['jp'] = jparts(r['nj'])
                r['parts'] = [romaji(q) for q in r['jp']] or [romaji(jclean(r['nj']))]; r['n'] = '   '.join(r['parts'])
        JA = wd_ja(P)
        notice('World key JP sample', '; '.join(f"{r.get('nj')} → {r['n']} [{r['ty']}]" for r in recs[:12]) + ' | fields: ' + ', '.join(list(recs[0]['_a'].keys())[:30]))
    for r in recs: r['_k'] = kinds(cc, r['n']) | kinds(cc, r['ty']) | kinds(cc, r['src']) | r.get('_k0', set())
    # Oct 25: dual names - Australia files many parks under the Aboriginal name with the English one in brackets
    # ('Bandilngan (Windjana Gorge)', 'Danggu (Geikie Gorge)'); norm() drops bracket text, so both names become parts
    if cc != 'JP':
        for r in recs:
            br = [q.strip() for q in re.findall(r'\(([^)]{3,})\)', r['n'] or '') if re.search(r'[A-Za-z]{3}', q)]
            if br: r['parts'] = [r['n']] + br + [re.sub(r'\(.*?\)', ' ', r['n']).strip()]
    # 1-degree grid so big countries (FR: 14k parks x 15k areas) stay quick
    GRID = {}
    for i, r in enumerate(recs):
        b = r['_bb']
        if not b: continue
        for gx in range(int((b[0] - .6) // 1), int((b[2] + .6) // 1) + 1):
            for gy in range(int((b[1] - .6) // 1), int((b[3] + .6) // 1) + 1): GRID.setdefault((gx, gy), []).append(i)
    def nearby(la, lo): return [recs[i] for i in GRID.get((int(lo // 1), int(la // 1)), [])] if la is not None else recs
    BYCODE = {str(r['code']).upper(): r for r in recs if r.get('code')}   # Oct 20: DE crashed on records without a code
    parks = {}
    for ref, x in sorted(P.items()):
        name, typ, la, lo = x[0], x[2], x[5], x[6]
        if not la and not lo: la = lo = None   # Oct 18: POTA has no pin for ~200 Canadian parks (0,0): match by name in the province only
        kp = kinds(cc, name) | kinds(cc, typ)
        m, c = [], []
        cand = [name] + ([q for q in re.split(r'\s+-\s+', name) if q.strip()] if cc == 'GB' and ' - ' in name else [])
        if cc in EU and re.search(r'\w/\w', name):   # Oct 19: 'Padjelanta/Badjelánnda National Park' = either name (+ the kind words)
            cand += [q.strip() for q in name.split('/') if q.strip()]
        mr = []
        if cc in EU:
            for code in re.findall(r'\b[A-Z]{2}[0-9A-Z]\d{4,6}\b', name):           # a Natura code in the POTA name = that exact site
                r = BYCODE.get(code)
                if r: m.append([r['id'], r['n'], r['src'], 'site code ' + code])
        for r in ([] if m else nearby(la, lo)):
            if la is not None and not near(la, lo, r['_bb'], .6): continue
            if cc in EU and (('n2k' in kp) != ('n2k' in r['_k'])): continue          # Natura 2000 parks only join Natura 2000 sites, and the other way round
            jam = cc == 'JP' and r.get('nj') and bool({re.sub(r'\s', '', q) for q in r.get('jp') or [jclean(r['nj'])]} & (JA.get(ref) or set()))
            if r['n'] and (jam or any(same_name(cc, q, rn) for q in cand for rn in (r.get('parts') or [r['n']]))) and (not kp or (kp & r['_k']) or (not r['_k'] and not (cc == 'AU' and r.get('ty')))):
                m.append([r['id'], r['n'], r['src'], 'name']); mr.append(r)
        # Oct 25 (round 5 hand checks, GB: 'Hill Rise', 'Castle Hill', 'Riverside' joined a same-named SMALL site 10-70 km
        # away): a small site found by name alone must sit near the pin; a big one (a national park) may reach it.
        if la is not None:
            m = [q for q in m if not q[3] == 'name' or (lambda b: not b or near(la, lo, b, .08) or (b[2] - b[0] > .15 or b[3] - b[1] > .15))(next((r.get('_bb') for r in mr if r['id'] == q[0] and r['n'] == q[1]), None))]
        ov = WOV.get(ref) or {}
        if ov:
            no = {low(x) for x in ov.get('no', [])}
            m = [q for q in m if low(q[1]) not in no]
            for want in ov.get('join', []):
                for r in nearby(la, lo):
                    if low(r['n']) == low(want) and (la is None or near(la, lo, r['_bb'], .6)) and not any(q[0] == r['id'] for q in m):
                        m.append([r['id'], r['n'], r['src'], 'reviewed'])
        pref = [q for q in m if q[2] in CHPREF.get(typ, [])] if cc == 'CH' else []
        if pref: m = pref                                                          # the federal inventory of that kind decides
        if cc == 'CH' and m:                                                       # Oct 19: '(südlicher Teil)', '(Teilraum 2)': parts of one BLN area
            pp, keep = chpart(name), []
            for q in m:
                qp = chpart(q[1])
                if qp - {'t'} and pp - {'t'} and (qp - {'t'}) != (pp - {'t'}): continue   # north part never joins the south part
                keep.append(q)
            m = keep
            tn = re.search(r'teilraum\s*(\d+)', name, re.I)
            if tn and m:                                                           # BLN keeps its own part numbers (TeilObjNum like 1601.1?)
                RID = {r['id']: r for r in recs}
                hit = [q for q in m if re.search(r'(^|\D)0*' + tn.group(1) + r'$', RID.get(q[0], {}).get('tp', '')) or
                       re.search(r'teilraum\s*0*' + tn.group(1) + r'\b', RID.get(q[0], {}).get('tpn', ''), re.I)]
                if hit: m = [[q[0], q[1], q[2], 'name + part ' + tn.group(1)] for q in hit]; pp = pp - {'t'}
            if 't' in pp and m and not any('t' in chpart(q[1]) for q in m):
                c = [[q[0], q[1], q[2], 'the park is one part (Teilraum) of this area; the map has the whole area'] for q in m][:6]; m = []
        elif cc in EU and len({r2['dc'] for r2 in mr if r2['src'] == 'EEA nationally designated areas'}) > 1 and (lambda kk: kk and [q for q, r2 in zip(m, mr) if ownk(r2['n']) & kk] and
                len({r2['dc'] for r2 in mr if ownk(r2['n']) & kk and r2['src'] == 'EEA nationally designated areas'}) == 1)(ownk(name)):
            kk = ownk(name); m = [[q[0], q[1], q[2], 'name + kind in its own name'] for q, r2 in zip(m, mr) if ownk(r2['n']) & kk]   # Oct 19: 'Krajinski park Goričko' is the landscape park
        elif cc in EU and len({r2['dc'] for r2 in mr if r2['src'] == 'EEA nationally designated areas'}) > 1 and (lambda kt: kt and (lambda keep:
                keep and len({r2['dc'] for r2 in keep}) == 1)([r2 for r2 in mr if r2['src'] == 'EEA nationally designated areas' and dkinds(eea_dt().get(r2['dc'], '')) & kt]))(dkinds(typ) | ownk(name)):
            kt = dkinds(typ) | ownk(name)   # Oct 19: the designation code's own label says which piece is the park's kind (unknown code = never joined)
            m = [[q[0], q[1], q[2], 'name + designation type ' + r2['dc'] + ' (' + eea_dt().get(r2['dc'], '')[:40] + ')'] for q, r2 in zip(m, mr)
                 if r2['src'] == 'EEA nationally designated areas' and dkinds(eea_dt().get(r2['dc'], '')) & kt]
        elif cc in EU and len({r2['dc'] for r2 in mr if r2['src'] == 'EEA nationally designated areas'}) > 1:
            c = [[q[0], q[1], q[2], 'same name, more than one kind of area'] for q in m]; m = []   # e.g. a reserve and a landscape park with one name
        if c: parks[ref] = {'n': name, 't': typ, 'm': [], 'c': c[:6]}; continue
        if not m and la is not None and cc in ('DE', 'AT'):
            # Oct 20 DE review: (1) the BfN name is a part of the POTA name (or the other way round), same kind of place,
            # and the POTA pin is inside it ('Bayerischer Spessart Nature Park' = Naturpark 'Spessart' around the pin);
            # (2) POTA's German type labels are often wrong ('Kendlmuehlfilzen National Park' is a Naturschutzgebiet):
            # an EXACT name with only one official area of that name nearby joins whatever the label says (not biosphere/UNESCO labels).
            near_r = [r for r in nearby(la, lo) if r['n'] and near(la, lo, r['_bb'], .1)]
            for r in near_r:
                w1, w2 = words(cc, name), words(cc, r['n'])
                if kp and (kp & r['_k']) and w1 and w2 and (w1 <= w2 or w2 <= w1) and inside(la, lo, r['_r']):
                    m.append([r['id'], r['n'], r['src'], 'name part + same kind + pin inside'])
            if not m and not re.search(r'biosph|unesco|geopark|natura 2000', (name or '') + ' ' + (typ or ''), re.I):
                ex = [r for r in near_r if norm(cc, r['n']) == norm(cc, name)]
                if len(ex) == 1 or (ex and len({r['src'] for r in ex}) == 1):
                    m += [[r['id'], r['n'], r['src'], 'exact name (POTA type label differs)'] for r in ex]
            if m: parks[ref] = {'n': name, 't': typ, 'm': m, 'c': []}; continue
        # Where POTA's names and the country's own names are written differently (Japan writes its parks in
        # Japanese, POTA romanises them), matching on names finds almost nothing. So: when the POTA pin sits
        # inside exactly ONE official area, that IS the park. Only one, and only of a kind that fits, so a pin
        # inside both a national park and a small reserve inside it is still left for a person to look at.
        if not m and la is not None and cc in PIN_JOIN:
            holds = [r for r in nearby(la, lo) if r['n'] and inside(la, lo, r['_r'])]
            if kp:
                fit = [r for r in holds if kp & r['_k']]
                if fit: holds = fit
            same = len({(r['src'], norm(cc, r['n'])) for r in holds}) == 1
            if len(holds) == 1 or (holds and same):
                m = [[r['id'], r['n'], r['src'], 'the POTA pin is inside it (names are written differently here)']
                     for r in holds[:1]]
                parks[ref] = {'n': name, 't': typ, 'm': m, 'c': []}
                continue
        # PIN + NAME WORDS, every country (Oct 24, step 3 of the Oct 22 plan: 'extend PIN_JOIN past Japan'). The pin
        # alone is too blunt outside Japan (it finds the forest around a small park), but the pin inside an area
        # whose name AGREES with the park's - the same name with a kind word in the way ('Aston Rowant SAC Conservation
        # Reserve' / Aston Rowant SSSI), or one name's words inside the other's ('Pfälzerwald Nature Park' /
        # 'Pfälzerwald-Nordvogesen', 'Roc de Chere Biological Reserve' / 'Roc De Chère') - is the shared scoring's
        # commonest 'would add' verdict (FR 225, GB 210, DE 62, CH 14 on the Oct 22 keys) and reads right by hand.
        # Only when every such holder is one and the same place. The website labels these Approximate (how text has
        # no 'name' at the front), so a wrong one is never shown as official.
        if not m and la is not None and NAME_JOIN:
            w1 = words(cc, name)
            def agrees(r):
                for q in cand:
                    if any(same_name(cc, q, rn) for rn in (r.get('parts') or [r['n']])): return 'same name'
                w2 = set().union(*[words(cc, rn) for rn in (r.get('parts') or [r['n']])])
                if w1 and w2 and len(w1 & w2) >= 1 and (w1 <= w2 or w2 <= w1) and max(len(w1), len(w2)) >= 2: return 'shared name words'
                return None
            holds = [(r, agrees(r)) for r in nearby(la, lo) if r['n'] and near(la, lo, r['_bb'], 0) and inside(la, lo, r['_r'])]
            # shared WORDS must not hand a small park the whole region around it ('Cape Cornwall Historic Site' is
            # not the Cornwall National Landscape; 'South Dartmoor Woods' is not Dartmoor National Park): a holder of a
            # big-area kind, or wider than about 50 km, only joins on the full name or when the park is that kind too
            BIGK = {'np', 'qnp', 'aonb', 'lsg', 'lp', 'nat', 'br'}
            def big(r): b = r['_bb']; return bool(r['_k'] & BIGK) or (b and (b[2] - b[0] > .5 or b[3] - b[1] > .5))
            holds = [(r, how) for r, how in holds if how and not (how == 'shared name words' and big(r) and not (kp & BIGK))]
            if holds and len({norm(cc, r['n']) for r, _ in holds}) == 1:
                if cc in EU:   # a Natura 2000 site and a national area of one name both hold the pin: the park's own kind decides
                    fit = [(r, how) for r, how in holds if ('n2k' in kp) == ('n2k' in r['_k'])]; holds = fit or holds
                m = [[r['id'], r['n'], r['src'], 'pin inside + ' + how] for r, how in holds]
                parks[ref] = {'n': name, 't': typ, 'm': m, 'c': []}
                continue
        if not m and la is not None:
            for r in nearby(la, lo):
                if not near(la, lo, r['_bb'], .03) or not r['n']: continue
                w1, w2 = words(cc, name), words(cc, r['n'])
                share = len(w1 & w2) / max(1, min(len(w1), len(w2))) if w1 and w2 else 0
                if same_name(cc, name, r['n']): why = 'same name, different kind of place'
                elif share >= .6: why = 'similar name'
                elif inside(la, lo, r['_r']): why = 'the POTA pin is inside it (different name)'
                else: continue
                c.append([r['id'], r['n'], r['src'], why])
            c = sorted(c, key=lambda q: (q[3] != 'similar name', q[3] != 'same name, different kind of place'))[:6]
        # NAME_JOIN (Oct 21): POTA often writes the kind onto the end of the official name - 'Nemuno delta
        # Regional Park' for an area simply called 'Nemuno delta'. norm() already strips the generic words, so
        # these names DO agree; the only thing keeping them out of the join is that the KIND did not match.
        # Take them when every same-name candidate points at one and the same official area; where two
        # different places share a name, leave it for a person. Measured across the saved keys before turning
        # it on: 600 of 6,850 joined, 44 left alone as ambiguous.
        if not m and c and NAME_JOIN:
            sn = [x for x in c if x[3] == 'same name, different kind of place']
            if sn and len({str(x[1]).strip().lower() for x in sn}) == 1:
                m = [[x[0], x[1], x[2], 'same name (POTA writes the kind into the name)'] for x in sn]
                c = [x for x in c if x not in sn]
        parks[ref] = {'n': name, 't': typ, 'm': m, 'c': c}
    # IS THE BOUNDARY WHERE IT SHOULD BE? (Oct 24: the US key's Oct 21-22 check, ported.) A name can match and still
    # be the wrong place, so: does the park's own pin fall inside the land it was joined to? Sorted the same three
    # ways as the US ('no shape to check against' = the check is blind, not the join; 'edge' = within about a mile;
    # 'well outside'), plus 'swap' = ANOTHER area with the SAME NAME does contain the pin, the one case that is a
    # wrong join with the right land already found. Recorded, never acted on; kpc_boundary_report.py reads it.
    # Outlines here are thinned (THIN_N points a ring), so 'edge' is wider than in the US and means less.
    try:
        RID = {(r['src'], r['id']): r for r in recs}
        for ref, pk in parks.items():
            mm = pk.get('m') or []
            la, lo = P[ref][5], P[ref][6]
            if not mm or not la and not lo: continue
            mine = [RID.get((x[2], x[0])) for x in mm]
            mine = [r for r in mine if r]
            shaped = [r for r in mine if r.get('_r')]
            if any(inside(la, lo, r['_r']) for r in shaped): continue
            pk['far'] = ('no shape to check against' if not shaped else
                         'edge' if any(near(la, lo, r['_bb'], .02) for r in shaped) else 'well outside')
            if shaped:
                jn = {norm(cc, x[1]) for x in mm if x[1]}
                mids = {(x[2], x[0]) for x in mm}
                # a DIFFERENT place of the same name: its land must not overlap the joined land (the same site listed
                # in two layers, SSSI and NNR say, is not a swap - the thinned NNR ring just missed the pin)
                def apart(b): return all(b[2] < r['_bb'][0] or b[0] > r['_bb'][2] or b[3] < r['_bb'][1] or b[1] > r['_bb'][3] for r in shaped if r['_bb'])
                swap = [r for r in nearby(la, lo) if norm(cc, r['n']) in jn and (r['src'], r['id']) not in mids
                        and r.get('_r') and near(la, lo, r['_bb'], 0) and apart(r['_bb']) and inside(la, lo, r['_r'])]
                if swap: pk['swap'] = [[r['id'], r['n'], r['src']] for r in swap[:2]]
    except Exception as e:  # noqa: BLE001
        notice(f'World key {cc}', f'boundary check stopped: {type(e).__name__}: {str(e)[:200]}')
    # SHADOW (Oct 22): the shared scoring's verdict for each park, written down ONLY where it disagrees with the join
    # above. Nothing it says changes a join. Names are read this script's way (each country's generic words, Baltic
    # endings, Japanese via romaji and the Wikidata bridge); kpc_match weighs the facts as it does for the US. PIN_JOIN
    # is ON here: across languages a name often cannot be compared, and the pin inside one area of a fitting kind is
    # then the best evidence there is (Japan 102 -> 182 joined that way).
    try:
        WCL = KM.name_clusters([(norm(cc, r['n']), r['_bb']) for r in recs if r['n']])
        for ref, x in sorted(P.items()):
            name, typ, la, lo = x[0], x[2], x[5], x[6]
            if not la and not lo: la = lo = None
            kp = kinds(cc, name) | kinds(cc, typ)
            cn = [name] + ([q for q in re.split(r'\s+-\s+', name) if q.strip()] if cc == 'GB' and ' - ' in name else [])
            if cc in EU and re.search(r'\w/\w', name): cn += [q.strip() for q in name.split('/') if q.strip()]
            cands = []
            for r in nearby(la, lo):
                if not r['n'] or (la is not None and not near(la, lo, r['_bb'], .6)): continue
                n2k_off = cc in EU and (('n2k' in kp) != ('n2k' in r['_k']))      # Natura 2000 only with Natura 2000...
                rparts = r.get('parts') or [r['n']]
                jam = cc == 'JP' and r.get('nj') and bool({re.sub(r'\s', '', q) for q in r.get('jp') or [jclean(r['nj'])]} & (JA.get(ref) or set()))
                ex = bool(jam) or any(same_name(cc, q, rn) and not (norm(cc, q) != norm(cc, rn) and (norm(cc, q).startswith(norm(cc, rn)) or norm(cc, rn).startswith(norm(cc, q))))
                                      for q in cn for rn in rparts)
                wd = (not ex) and any(same_name(cc, q, rn) or (words(cc, q) and words(cc, rn) and (words(cc, q) <= words(cc, rn) or words(cc, rn) <= words(cc, q)))
                                      for q in cn for rn in rparts)
                # ...unless the names are the SAME: POTA writes the kind onto the official name ('Kilcolman Bog Nature
                # Reserve' = the Natura 2000 site 'Kilcolman Bog SPA'), the key's NAME_JOIN. Oct 22 review: Ireland's 28,
                # Romania's 33 and Portugal's 16 'demotes' were all this. Counted as a kind clash, not thrown out.
                if n2k_off and not ex: continue
                holds = la is not None and near(la, lo, r['_bb'], 0) and KM.inside(la, lo, r['_r'])
                if not (ex or wd or holds): continue
                cands.append({'a': r, 'nn': norm(cc, r['n']), 'bb': r['_bb'], 'kind_ok': True, 'side_ok': True,
                              'kind_clash': n2k_off or bool(kp and r['_k'] and not (kp & r['_k'])),
                              'name_exact': ex, 'name_words': wd, 'name_unique': WCL.get(norm(cc, r['n']), 1) == 1,
                              'pin': (la, lo) if la is not None else None, 'g': r['_r'], 'acres': 0, 'holds': holds})
            fit = [c for c in cands if c['holds'] and kp and (kp & c['a']['_k'])]
            if fit:
                bba = lambda b: (b[2] - b[0]) * (b[3] - b[1]) if b else 1e9
                min(fit, key=lambda c: bba(c['bb']))['smallest_fit'] = True
            v, best, runner = KM.choose(cands)
            cur = parks.get(ref) or {}
            ids_now = {str(q[0]) for q in cur.get('m') or []}
            ids_new = {str(c['a']['id']) for c in best[2]} if (best and v == 'join') else set()
            if bool(ids_now) != (v == 'join') or (ids_now and ids_new and not ids_now & ids_new):
                cur['shadow'] = {'v': v, 'pts': best[0] if best else None, 'why': best[1] if best else [],
                                 'to': best[2][0]['a']['n'] if best else None,
                                 'vs': (runner[2][0]['a']['n'] + f' ({runner[0]})') if runner else None}
    except Exception as e:  # noqa: BLE001
        notice(f'World key {cc}', f'shadow scoring stopped: {type(e).__name__}: {str(e)[:200]}')
    cnt = {'parks': len(parks), 'matched': sum(1 for p in parks.values() if p['m']), 'check': sum(1 for p in parks.values() if not p['m'] and p['c']),
           'none': sum(1 for p in parks.values() if not p['m'] and not p['c']), 'areas': len(recs),
           'detail': (WMETA.get(cc) or (DETAIL, THIN_N))[0], 'thin': (WMETA.get(cc) or (DETAIL, THIN_N))[1],
           'pin_outside': sum(1 for p in parks.values() if p.get('far')),
           'pin_well_outside': sum(1 for p in parks.values() if p.get('far') == 'well outside'),
           'pin_no_shape': sum(1 for p in parks.values() if p.get('far') == 'no shape to check against'),
           'pin_swap': sum(1 for p in parks.values() if p.get('swap')),
           'shadow_demote': sum(1 for p in parks.values() if p['m'] and (p.get('shadow') or {}).get('v') in ('check', 'none')),
           'shadow_add': sum(1 for p in parks.values() if not p['m'] and (p.get('shadow') or {}).get('v') == 'join'),
           'shadow_other_place': sum(1 for p in parks.values() if p['m'] and (p.get('shadow') or {}).get('v') == 'join')}
    # Oct 22 (Brandon: 'anything they can do to complete our map have them do it'): a web page can only fetch an outline
    # by id from an ArcGIS map. Parks joined to anything else (France's ZNIEFF from IGN, Germany's BfN, NatureScot, Wales,
    # Switzerland's BAFU, Japan's A10) could not be drawn at all: 12,500 of 41,000 joined parks on Oct 22. Their outlines
    # are saved here, lightly thinned, 100 parks to a file, for KPCB.worldKey to draw: data/world-bounds/CC/<n>.json.
    try:
        BD = pathlib.Path('data/world-bounds') / cc
        LAY = {x[0] for v in SRC.values() for x in v if x[1] in ('arcgis', 'arcgis_alt')}
        byn = {}
        for r in recs: byn.setdefault((r.get('src'), r.get('n')), []).append(r)
        shards = {}
        for ref, pk in parks.items():
            mm = pk.get('m') or []
            if not mm or any(x[2] in LAY and x[0] is not None for x in mm): continue
            la, lo = P[ref][5], P[ref][6]
            polys = []
            for x in mm:
                for r in byn.get((x[2], x[1]), []):
                    if la and lo and r.get('_bb') and not near(la, lo, r['_bb'], .6): continue
                    for ring in (r.get('_r') or []):
                        if len(ring) >= 3: polys.append(ring)
            if polys:
                # light enough for a phone: the 12 biggest pieces, 50 points each (a guide outline, labelled as saved by KPC)
                def _area(rg):
                    xs, ys = [q[0] for q in rg], [q[1] for q in rg]; return (max(xs) - min(xs)) * (max(ys) - min(ys))
                keep = []
                for rg in sorted(polys, key=_area, reverse=True)[:12]:
                    k = max(1, len(rg) // 50); pts = [[round(q[0], 4), round(q[1], 4)] for q in rg[::k]]
                    if len(pts) >= 3: keep.append(pts + [pts[0]])
                num = int(re.sub(r'\D', '', ref.split('-', 1)[1]) or 0)
                if keep: shards.setdefault(num // 100, {})[ref] = {'n': mm[0][1], 's': mm[0][2], 'r': keep}
        if BD.exists():                       # Oct 25: only shards that no longer exist are removed; the rest are written only if they changed
            for old_f in BD.glob('*.json'):
                if old_f.stem.isdigit() and int(old_f.stem) not in shards: old_f.unlink()
        for b, d in shards.items(): save_json(BD / f'{b}.json', d)
        cnt['saved_outlines'] = sum(len(d) for d in shards.values())
    except Exception as e:  # noqa: BLE001
        notice(f'World key {cc}', f'saving outlines for the website stopped: {type(e).__name__}: {str(e)[:200]}')
    # W-2 USE UNTIL BETTER (Brandon Oct 30 12:22 PM via HQ): an EU compilation record (EEA Natura 2000 / CDDA) IS the park's outline
    # until the country's own agency layer gives one: grade APPROXIMATE, labelled 'EU compilation of national data', never Official.
    # When the park also has a piece from the agency's own layer, the EU pieces are dropped (the official one replaces them).
    _eu = lambda q: str(q[2]).startswith('EEA')
    n_eu = n_rep = 0
    for _p in parks.values():
        _m = _p.get('m') or []
        if not _m or not any(_eu(q) for q in _m): continue
        if all(_eu(q) for q in _m): _p['g'] = 'approx'; _p['gsrc'] = 'EU compilation of national data'; n_eu += 1
        else: _p['m'] = [q for q in _m if not _eu(q)]; n_rep += 1
    if n_eu or n_rep: notice(f'World key {cc}', f'W-2: {n_eu} parks outlined from the EU compilation (Approximate); {n_rep} had an agency outline that replaced it')
    save_json(OUT / f'{cc}.json', {'cc': cc, 'sources': [s[0] for s in SRC[cc]], 'counts': cnt, 'parks': parks})
    L = [f'# {cc}: POTA parks vs official land', '', f"Built by `.github/scripts/kpc_world_key.py` (date: data/status/kpc_world_key.json) from: {', '.join(s[0] for s in SRC[cc])}. "
         f"**{cnt['matched']} of {cnt['parks']}** joined (same name + same kind), **{cnt['check']}** to check, **{cnt['none']}** nothing found. Nothing below is joined.", '', '## To check (not joined)', '']
    L += [f"- **{r}** {p['n']} ({p['t']}) → " + '; '.join(f"{q[1]} ({q[2]}, {q[3]})" for q in p['c']) for r, p in parks.items() if not p['m'] and p['c']]
    L += ['', '## Nothing found', ''] + [f"- {r} {p['n']} ({p['t']})" for r, p in parks.items() if not p['m'] and not p['c']]
    save_text(OUT / 'review' / f'{cc}.md', '\n'.join(L) + '\n')
    idx[cc] = cnt
    notice(f'World key {cc}', f"{cnt['matched']} of {cnt['parks']} joined, {cnt['check']} to check, {cnt['none']} nothing found ({cnt['areas']} official areas read); "
                              f"pin outside the joined land: {cnt['pin_outside']} ({cnt['pin_no_shape']} unmeasurable, {cnt['pin_well_outside']} well outside, {cnt['pin_swap']} same-name swap)")
    save_json(OUT / 'index.json', {'countries': idx})
if CMODE != 'off':
    notice('World key saved outlines', f"mode {CMODE}, detail {DETAIL}, thin {THIN_N}: loaded {len(WUSED)} ({' '.join(WUSED)}), saved {len(WSAVED)} ({' '.join(WSAVED)})")
