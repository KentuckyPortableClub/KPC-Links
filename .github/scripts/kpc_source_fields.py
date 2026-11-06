#!/usr/bin/env python3
"""ONE TABLE: which field of each official source is its stable id, its official acres, its owner and its parent (Nov 6 2026,
big key / 2-fer patch; Brandon via Super: 'this program is worldwide ... one config table, not hardcoded per state').

Every layer the US, Canada and world keys already read gets the same treatment: the tract records (kpc_tracts.py) carry
  sid     the source's own STABLE id (PAD-US Source_PAID, NPS UNIT_CODE, FWS ORGCODE, KDFWR_ID, CPCAD ZONE_ID, WDPA WDPAID, Natura 2000
          SITECODE, CDDA cddaId ...). None = the source has no stable id, and the record id (an OBJECTID, which servers renumber) is used.
  ac      the source's OWN official area, in acres (hectares / km2 / m2 converted here)
  own     the owner the source names (owner type kept apart in own_type)
  parent  the source's parent id (CPCAD PARENT_ID, WDPA WDPA_PID, NPS tracts' UNIT_CODE ...): feeds the nested-park links
  access  the source's public-access code, when it has one (PAD-US Pub_Access)
  basis   what kind of line it is (FWS: fee / easement / approved boundary)

How a source is found (first match wins):
  1. SOURCES below, matched by the layer URL (regex) or, for the world key, by the source label.
  2. AUTO: any other ArcGIS / WFS layer (the ~290 state-agency layers in data/state-gis.json, the provincial layers, the world's national
     layers) is read by its own field list with the AUTO_* patterns below. AUTO answers are marked 'auto' in the coverage report so a person
     can promote a source to an explicit row.
Fields are only ever ADDED to a query the key already makes (no new request, no new host); a server that refuses an added field is asked
again without it (kpc_us_key fetch fallback), so a wrong guess here can never lose a layer.
'verified' = the field list was read from the live service (or its published spec) on Nov 6 2026; False = from the agency's docs only.

Nothing in this module changes a join, an outline, a pin or a 2-fer: it only names fields.
"""
import re

HA, KM2, M2, AC = 2.4710538, 247.10538, 1 / 4046.8564, 1.0

# key, match (regex on the layer url, or 'label:' + regex on the world source label), field names, unit of the acres field
SOURCES = [
    # ---------------- United States, national
    dict(key='padus', match=r'PAD-US/PAD_US/MapServer', id='Source_PAID', acres='GIS_Acres', unit=AC, owner='Own_Name', owner2='Loc_Own',
         own_type='Own_Type', access='Pub_Access', verified=True, about='USGS PAD-US: Source_PAID = the provider\'s own id (kept across PAD-US versions)'),
    dict(key='fws_interest', match=r'FWSInterest', id='ORGCODE', acres='SUM_GISACRES', unit=AC, owner_const='U.S. Fish and Wildlife Service', basis='INTTYPE1',
         verified=False, about='USFWS land interest: ORGCODE = the refuge\'s FWS org code; INTTYPE1 = F fee / E easement / L lease / S secondary...'),
    dict(key='fws_approved', match=r'FWSApproved', id='ORGCODE', acres='GISACRES', unit=AC, owner_const='U.S. Fish and Wildlife Service', basis_const='approved boundary',
         verified=False, about='USFWS approved (acquisition) boundary: NOT ownership; never a 2-fer spot by itself'),
    dict(key='nps_boundary', match=r'NPS_Land_Resources_Division_Boundary_and_Tract_Data_Service/FeatureServer/2', id='UNIT_CODE', acres='GIS_Acres', unit=AC,
         owner_const='National Park Service', verified=False, about='NPS Land Resources Division legislated boundary: UNIT_CODE = 4-letter park code'),
    dict(key='nps_tracts', match=r'NPS_Land_Resources_Division_Boundary_and_Tract_Data_Service/FeatureServer/1', id='TRACT_ID', parent='UNIT_CODE', acres='GIS_Acres', unit=AC,
         owner='STATUS', basis='ESTATE', verified=False, about='NPS land tracts: ESTATE Fee/Easement, STATUS Federal/Private...; parent = UNIT_CODE'),
    dict(key='usfs_ownership', match=r'EDW_BasicOwnership', id=None, owner='OWNERCLASSIFICATION', parent='FORESTNAME', verified=False,
         about='Forest Service Basic Ownership: OWNERCLASSIFICATION = USDA FOREST SERVICE / NON-FS ...'),
    dict(key='usfs_boundary', match=r'EDW_ForestSystemBoundaries', id='ADMINFORESTID', acres='GIS_ACRES', unit=AC, owner_const='USDA Forest Service', verified=False),
    dict(key='usfs_wilderness', match=r'EDW_Wilderness', id='WID', acres='GIS_ACRES', unit=AC, verified=False),
    dict(key='blm_hma', match=r'BLM_Natl_WHB/MapServer/0', id='HMA_ID', acres='BLM_ACRES', unit=AC, owner_const='Bureau of Land Management', verified=False),
    dict(key='blm_ha', match=r'BLM_Natl_WHB/MapServer/1', id='HA_NO', acres='BLM_ACRES', unit=AC, owner_const='Bureau of Land Management', verified=False),
    dict(key='nps_wsr', match=r'WildScenicRiverBoundaries', id=None, acres='GIS_ACRES', unit=AC, verified=False),
    dict(key='usace_rec', match=r'usace_recreation_areas', id='RECAREAID', owner='MANAGINGAGENCY', verified=False),
    # ---------------- United States, state agencies (explicit rows; every other state layer goes through AUTO)
    dict(key='ky_kdfwr', match=r'Ky_Public_Hunting_Areas', id='KDFWR_ID', acres='ACRES_CAL', unit=AC, verified=True,
         about='KDFWR public hunting areas / WMAs: KDFWR_ID = the stable KY area id (field list from the KY GIS workbench catalog, ky-gis-layers.json; '
               'read live Nov 6). No owner field: the layer also lists federal and private land open to hunting'),
    dict(key='ky_state_parks', match=r'Ky_State_Parks_Features', id=None, acres='ABSOLUTE_ACREAGE', unit=AC, owner_const='Kentucky Department of Parks', verified=True),
    dict(key='ky_knp', match=r'Ky_KNP_(State_Nature_Preserves|Natural_Areas|Wild_River)', id=None, acres='ACRES', unit=AC, owner='MA_OWNER', access='PUB_ACCESS', verified=True),
    dict(key='ky_hlcf', match=r'Ky_KNP_Heritage_Land_Conservation_Fund', id='TRACT_NAME', acres='ACRES', unit=AC, owner='MA_OWNER', verified=True),
    # ---------------- Canada
    dict(key='cpcad', match=r'CWS_SCF/CPCAD', id='ZONE_ID', parent='PARENT_ID', acres='O_AREA_HA', unit=HA, owner='OWNER_E', own_type='OWNER_TYPE', verified=True,
         about='Canadian Protected and Conserved Areas Database: ZONE_ID = this zone, PARENT_ID = the protected area it belongs to'),
    # ---------------- World
    dict(key='wdpa', match=r'(?i)wdpa|protectedplanet', id='WDPAID', parent='WDPA_PID', acres='REP_AREA', acres2='GIS_AREA', unit=KM2, owner='OWNERSHIP', own_type='OWN_TYPE',
         verified=False, about='WDPA: WDPAID = the site, WDPA_PID = the parcel; areas in km2'),
    dict(key='natura2000', match=r'Natura2000Sites|label:EEA Natura 2000', id='SITECODE', acres='Area_ha', unit=HA, verified=True,
         about='EEA Natura 2000: SITECODE (e.g. ES0000024) is stable across releases'),
    dict(key='cdda', match=r'CDDA_Dyna|label:EEA nationally designated', id='inspireIDLocalId', id2='nationalId', acres='siteArea', unit=HA, verified=True,
         about='EEA nationally designated areas (CDDA, 2025 Reportnet layer): no cddaId any more; inspireIDLocalId (else nationalId), siteArea in hectares (checked Nov 6: Triglav 83,982 ha)'),
    dict(key='capad', match=r'CAPAD', id='PA_PID', parent='PA_ID', acres='GIS_AREA', unit=HA, owner='AUTHORITY', verified=False,
         about='Australia CAPAD: PA_ID, PA_PID, GIS_AREA in hectares'),
]

# Research-pack field names (Nov 6). Registered here so the names are in one file, but NOT in SOURCES.
# find() / mapping() / extra_fields() never read this list, whether KPC_RESEARCH_SOURCES is off or report.
# Builders keep requesting the same fields, and tract records keep the same src. A side report may call
# research_find(); that result is never written into a key or a tract file.
# Saskatchewan is the gis.saskatchewan.ca Planning service only. It must not match St John's
# Mapcentre/Planning/MapServer/5 or WA Property_and_Planning/MapServer/15.
RESEARCH_SOURCES = [
    dict(key='usfs_surface', match=r'BdyOwn_LSRS_SurfaceOwnership', acres='GIS_ACRES', unit=AC, owner='OWNERCLASSIFICATION',
         parent='FORESTNAME', verified=False,
         about='Forest Service Surface Ownership detailed gdb (data.fs.usda.gov). Field names follow the Basic Ownership sibling; the gdb was not opened in this repo.'),
    dict(key='nb_pna', match=r'items/be8127efc1fc459c8c204bf48d5396f6', id='PNA_CODE', acres='HECTARES', unit=HA, owner='OWNER', verified=False,
         about='New Brunswick protected natural areas. Name field NAME.'),
    dict(key='nb_parks', match=r'geonb_provincialparks-parcsprovinciaux', acres='SHAPE.AREA', unit=M2, owner='HOLDER', verified=False,
         about='GeoNB provincial parks shapefile. Area is SHAPE.AREA in square metres. REST has no name field.'),
    dict(key='nb_wildlife', match=r'items/5706f19aa80f4e35b73f594a0760f180', acres='SHAPE.AREA', unit=M2, access='W_CLASS', verified=False,
         about='New Brunswick wildlife refuges, including WMAs. Name field NAME.'),
    dict(key='nt_parks', match=r'Environment_LCC/MapServer/204', verified=False, about='NWT established territorial parks. Name field NAME. No acres field in the pack.'),
    dict(key='nt_protected', match=r'Environment_LCC/MapServer/(193|195)', acres='Size_Km2', unit=KM2, verified=False,
         about='NWT terrestrial protected areas and federal/territorial conservation areas. Name field Name. Size_Km2 is square kilometres.'),
    dict(key='on_conrvreg', match=r'LIO_Open03/MapServer/2|CONRVREG\.zip', id='PROTECTED_SITE_IDENT',
         owner='OWNER_ENG', parent='PARENTID', verified=False,
         about='Ontario regulated conservation reserves. Name field PROTECTED_AREA_NAME_ENG. REGULATED_AREA is present but the pack did not say the unit, so it is not converted.'),
    dict(key='on_provpreg', match=r'PROVPREG\.zip', verified=False,
         about='Ontario regulated provincial parks shapefile (OGL-Ontario). Field names were not in the pack; AUTO applies once the file is read.'),
    dict(key='qc_ap_reg', match=r'Biodiversite/Aires_protegees/MapServer', id='MACODE', acres='HA_LEGAL', unit=HA, owner='RESPONSABL',
         parent='CORESPONSA', verified=False, about='Quebec protected-areas register. Name field NOM.'),
    dict(key='qc_trq', match=r'TRQ_WMS/MapServer/(6|16)', id='CODE_ADMINISTRATIF', acres='SUPERFICIE_KM2', unit=KM2, verified=False,
         about='Quebec recreation territories (regional parks layer 6, ZECs layer 16). Name field NOM_OFFICIEL.'),
    dict(key='sk_whpa', match=r'gis\.saskatchewan\.ca/arcgis/rest/services/Planning/MapServer(?:/\d+)?(?:\?|$)|items/1ffa27744fd04ee6986de4bee7ad4052',
         owner='PROP_OWN', access='PUBLICCL', verified=False,
         about='Saskatchewan Planning MapServer on gis.saskatchewan.ca, or that Hub item. Not any other Planning/MapServer.'),
    dict(key='ga_conservation', match=r'FrameWork/Conservation/FeatureServer/5', owner='ownr_categ', verified=False,
         about='Georgia DNR conservation lands. Name field name.'),
    dict(key='me_ecoreserve', match=r'MEBPL_Lands_Ecoreserve/MapServer/1', acres='Total_Acres', unit=AC, verified=False,
         about='Maine BPL ecological reserves. Name field Unit.'),
    dict(key='nc_marea', match=r'marea_ManagedArea_', id='MA_ID', acres='ACRES', unit=AC, owner='OWNER', verified=False,
         about='NC NHP managed areas. Matching only until NCNHP says a public map is allowed. Name field MA_NAME. Do not republish the file.'),
    dict(key='ny_dec_lands', match=r'gisservices\.dec\.ny\.gov/arcgis/rest/services/reference/MapServer/2', id='LANDS_UID', acres='ACRES', unit=AC,
         owner='MANAGE_BY', access='PUBLICUSE', verified=False, about='NY DEC lands reference layer. Name field FACILITY.'),
    dict(key='ny_wma', match=r'dil_land_activities/MapServer/2', verified=False, about='NY DEC wildlife management areas. Name field WMA. OBJECTID is not the stable id.'),
    dict(key='wv_protected', match=r'wv_protected_lands/MapServer/(6|9|10|11)', id='Source_PAID', acres='GIS_Acres', unit=AC, owner='Own_Name',
         access='Pub_Access', verified=False, about='West Virginia protected-lands layers (PAD-US style fields). Name field Unit_Nm.'),
    dict(key='capad_file', match=r'fed\.dcceew\.gov\.au/api/download', id='PA_ID', acres='GIS_AREA', acres2='GAZ_AREA', unit=HA, owner='AUTHORITY',
         verified=False, about='CAPAD 2024 file download (terrestrial and marine). The live CAPAD MapServer still uses the capad row above.'),
    dict(key='au_ipa', match=r'Indigenous_Protected_Areas/FeatureServer', acres='GIS_AREA', acres2='GAZ_AREA', unit=HA, owner='AUTHORITY', verified=False,
         about='Australia Indigenous Protected Areas. Name field NAME.'),
    dict(key='act_reserves', match=r'items/da83e065513747f3aa46ade410ccf959', id='ZONE_OVERLAY_AREA_ID', verified=False,
         about='ACT public land reserves. Name field Reserve_Name.'),
    dict(key='gb_subcompartments', match=r'items/a29f272bb2014c658d3d9940bfd1de16', id='SUBCOMPTID', verified=False,
         about='National Forest Estate subcompartments (England). Name field FOREST.'),
    dict(key='ie_nha', match=r'NHA_ITM_', acres='Ha', unit=HA, verified=False, about='NPWS Natural Heritage Areas (ITM). Name field was not in the pack.'),
    dict(key='ie_sac', match=r'SAC_ITM_', acres='Ha', unit=HA, verified=False, about='NPWS Special Areas of Conservation (ITM). Name field was not in the pack.'),
    dict(key='nz_pcl', match=r'items/72354ba9bf7a4706af3fdfe60f86eea1|Public_Conservation_Land/MapServer|Hauraki/Marine_Reserves/MapServer',
         id='NaPALIS_ID', acres='Recorded_Area', unit=HA, verified=False,
         about='DOC public conservation land and the Hauraki marine-reserves copy. Name field Name. Te Urewera is not Crown PCL.'),
]

# AUTO: the field list of any other layer (names are matched without case)
AUTO_ID = re.compile(r'^(wdpa_?pid|wdpaid|site_?code|cdda_?id|zone_?id|unit_?code|parcel_?id|tract_?id|area_?id|site_?id|park_?id|unit_?id|'
                     r'[a-z]{2,16}_id|[a-z]{2,16}id|code|loc_?code|nationalid|natcode|cod_?\w*)$', re.I)
AUTO_ID_NOT = re.compile(r'^(object_?id|objectid_\d+|fid|global_?id|gid|shape|ogc_fid|esri_oid|oid|id|guid|uuid|user_?id|county_?id|state_?id|fips_?id)$|_oid$|^rid$|editor|created|update|globalid', re.I)
AUTO_ACRES = [(re.compile(r'acre|^ac$|_ac$|gis_?ac', re.I), AC), (re.compile(r'(^|_)(ha|hectares?|area_?ha|ha_?area|surf_?ha|site_?area)($|_)|hectare', re.I), HA),
              (re.compile(r'km2|sq_?km|rep_area|gis_area', re.I), KM2)]
AUTO_OWNER = re.compile(r'^(own|owner|owner_?name|own_?name|ma_?owner|eigentuemer|proprietaire|ownership|owner_?e|landowner)$', re.I)
AUTO_PARENT = re.compile(r'^(parent_?id|wdpa_?pid|pa_?pid|parent|parent_?code|unit_?code)$', re.I)
AUTO_ACCESS = re.compile(r'^(pub_?access|public_?access|access)$', re.I)


def _match_row(rows, url='', label=''):
    for s in rows:
        for part in re.split(r'\|(?=label:)', s['match']):
            if part.startswith('label:'):
                if label and re.search(part[6:], label, re.I): return s
            elif url and re.search(part, url): return s
    return None


def find(url='', label=''):
    """The explicit SOURCES row for a layer url / world source label, or None.
    Research-pack rows are not included. The flag does not change this."""
    return _match_row(SOURCES, url, label)


def research_find(url='', label=''):
    """A research-pack field row, for a side report only. mapping() does not call this."""
    return _match_row(RESEARCH_SOURCES, url, label)


def _ci(fields, name):
    if not name: return None
    lo = {str(f).lower(): f for f in fields}
    return lo.get(str(name).lower())


def mapping(url='', label='', fields=None):
    """{'key','how'('explicit'|'auto'|'none'), 'id','id2','acres','acres2','unit','owner','owner2','own_type','parent','access','basis',
    'owner_const','basis_const'} with field names as the layer spells them (when its field list is known; else as the table spells them)."""
    fields = list(fields or [])
    s = find(url, label)
    out = {'key': None, 'how': 'none', 'unit': AC}
    if s:
        out.update({k: v for k, v in s.items() if k not in ('match', 'about', 'verified')}); out['how'] = 'explicit'; out['verified'] = s.get('verified', False)
        if fields:   # spell as the layer does; drop what it does not have
            for k in ('id', 'id2', 'acres', 'acres2', 'owner', 'owner2', 'own_type', 'parent', 'access', 'basis'):
                if out.get(k): out[k] = _ci(fields, out[k])
        return out
    if not fields: return out
    out['key'] = 'auto'; out['how'] = 'auto'
    ids = [f for f in fields if AUTO_ID.match(str(f)) and not AUTO_ID_NOT.search(str(f))]
    out['id'] = ids[0] if ids else None
    for f in fields:
        for rx, unit in AUTO_ACRES:
            if rx.search(str(f)) and not re.search(r'shape|length|perim|calc_?date', str(f), re.I):
                out['acres'], out['unit'] = f, unit; break
        if out.get('acres'): break
    out['owner'] = next((f for f in fields if AUTO_OWNER.match(str(f))), None)
    out['parent'] = next((f for f in fields if AUTO_PARENT.match(str(f)) and f != out['id']), None)
    out['access'] = next((f for f in fields if AUTO_ACCESS.match(str(f))), None)
    if not any(out.get(k) for k in ('id', 'acres', 'owner', 'parent')): out['how'] = 'none'
    return out


def extra_fields(mp):
    """The field names to ADD to a query that already reads this layer."""
    return [mp[k] for k in ('id', 'id2', 'acres', 'acres2', 'owner', 'owner2', 'own_type', 'parent', 'access', 'basis') if mp.get(k)]


def _num(v):
    try:
        x = float(str(v).replace(',', '')) if v not in (None, '') else None
        return x if x is not None and x == x and x >= 0 else None
    except (TypeError, ValueError): return None


def _get(a, f):
    if not f or not isinstance(a, dict): return None
    if f in a: return a[f]
    fl = str(f).lower()
    return next((v for k, v in a.items() if str(k).lower() == fl), None)


def read(mp, attrs):
    """The facts of one record: {'sid','ac','own','own_type','parent','access','basis'} (only what is there)."""
    if not mp or mp.get('how') == 'none' or not isinstance(attrs, dict): return {}
    o = {}
    sid = _get(attrs, mp.get('id'))
    if sid in (None, '', ' ') and mp.get('id2'): sid = _get(attrs, mp['id2'])
    if sid not in (None, '', ' '): o['sid'] = str(sid).strip()
    ac = _num(_get(attrs, mp.get('acres')))
    if ac is None and mp.get('acres2'): ac = _num(_get(attrs, mp['acres2']))
    if ac is not None: o['ac'] = round(ac * (mp.get('unit') or 1.0), 1)
    own = _get(attrs, mp.get('owner')) or _get(attrs, mp.get('owner2')) or mp.get('owner_const')
    if own not in (None, ''): o['own'] = str(own)
    for k in ('own_type', 'parent', 'access', 'basis'):
        v = _get(attrs, mp.get(k))
        if v not in (None, '', ' '): o[k] = str(v)
    if 'basis' not in o and mp.get('basis_const'): o['basis'] = mp['basis_const']
    if mp.get('owner2') and _get(attrs, mp['owner2']) not in (None, ''): o['loc_own'] = str(_get(attrs, mp['owner2']))
    return o


FWS_BASIS = {'F': 'fee', 'E': 'easement', 'L': 'lease', 'S': 'secondary', 'P': 'primary', 'O': 'other', 'A': 'agreement', 'W': 'withdrawal'}


def basis_word(source_key, basis):
    """FWS / NPS line kinds in plain words: 'fee' (owned land), 'easement', 'approved boundary' (acquisition line, NOT ownership) ..."""
    b = str(basis or '').strip()
    if source_key == 'fws_interest': return FWS_BASIS.get(b[:1].upper(), b.lower() or 'interest (unknown kind)')
    if source_key == 'fws_approved': return 'approved boundary'
    if source_key == 'nps_tracts': return b.lower() or 'tract'
    return b.lower() or None


def is_ownership(source_key, basis):
    """True when the line is land the agency OWNS (fee); False for an easement / approved boundary; None = the source does not say."""
    w = basis_word(source_key, basis)
    if w is None: return None
    if w in ('fee', 'primary', 'withdrawal'): return True
    if w in ('easement', 'approved boundary', 'lease', 'secondary', 'agreement'): return False
    return None
