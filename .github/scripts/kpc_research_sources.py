#!/usr/bin/env python3
"""Research-pack sources for the US, Canada and world (GB / IE / AU / NZ) answer keys.

Nov 6 2026. Two outside packs (US-wide + next round). Brandon (KZ4CP) asked for the bot-safe
rows behind ONE new switch. This file is not a rule file (see kpc_key_freeze.NOT_RULES): it
never decides a join, and the key scripts are not edited, so the rules hashes stay as they are.

  KPC_RESEARCH_SOURCES=off     default. layers() is empty. No side report. Key bytes unchanged.
  KPC_RESEARCH_SOURCES=report  still does not change a key, a pin, an outline or a 2-fer.
                               note_saved() writes a side report of what joins, acres, owners
                               or 2-fers WOULD change. Abbreviations are used for name matching
                               only in this mode.

Catalog: data/research-sources/catalog.json (rows whose robots_status was ok, then a live
kpc_manners check on the file or Hub URL). Skipped rows: data/research-sources/skipped.json.
Geometries are not stored in this repo. matching_only rows (WA CC BY-NC, NL "matching only",
NCNHP permission) are name notes only and must not be republished.

The builders already call kpc_tracts.save. That calls note_saved after the tract file is written.

Same flag, still report-only:
  link_postcheck / scan_link_postcheck  key rows whose official page is missing or whose stored
                                        link check failed, plus the matching state agency page
                                        from data/maprep/agencies.json (toolbox PR 48, vendored).
  rank_outlines                         Tool Box name matcher plus these abbreviations. The pile
                                        solver that would call it is in KPC-Data; see
                                        docs/kpc-pile-solver-research-report.patch. Auto stays false.
"""
import csv, json, os, pathlib, re, unicodedata

ROOT = pathlib.Path(__file__).resolve().parents[2]
DATA = ROOT / 'data' / 'research-sources'
HERE = pathlib.Path(__file__).resolve().parent

# Grant County NM, plus the packs' do_not_ingest hosts / items. Never fetched, never catalogued.
BANNED = (
    '33TOOklri9xpic7U',
    'State_Parks_2024',
    '76bc620b19e34d24b2b4936f73b239c7',
    'aT1T0pU1ZdpuDk1t',
    'YgrExeJfxG5F4At7',
    'Coillte_Biodiversity',
)

KIND_TAILS = (
    'state nature preserve', 'state natural area', 'national nature reserve', 'nature reserve',
    'national historical park', 'national historic site', 'conservation reserve', 'protected area',
    'marine protected area', 'marine reserve', 'wildlife management area', 'state game land',
    'national wildlife refuge', 'national forest', 'state forest', 'game land', 'state park',
    'national park', 'provincial park', 'country park', 'recreation area',
)

# Pack test cases whose report-mode result is fixed (no pin is moved, no new POTA ref is created).
HOST_ONLY = {
    'blue licks state nature preserve': ['US-1274'],
    'natural bridge state nature preserve': ['US-1286'],
}
NESTED = {
    'IE-0097': 'IE-0003',   # Glendalough inside Wicklow Mountains
}
COMBO = {
    'GB-0002': ('SAC', 'NNR'),  # one ref, two designations; the NNR is not a second park
}
INACTIVE = {'GB-2511'}  # Coed Cilygroeslwyd, retired / active=0
NOT_MISSING_DOC = {'NZ-0280'}  # Te Urewera Act 2014: not Crown PCL, do not flag "missing from DOC"
NEAR_DUP = {('NZ-0928', 'NZ-0614')}  # Kaikoura marine; NZ-0614's pin looks inland
NOT_ELIGIBLE_NAMES = ('walk-in hunting', 'wiha', 'endeavour hydrothermal')
SHARED_PINS = (
    ('US-0198', 'US-0211', 'Kesterson NWR and San Luis NWR'),
    ('US-0203', 'US-0205', 'North Central Valley WMA and Sacramento NWR'),
    ('US-4852', 'US-6882', 'Bladen Lakes State Forest and State Game Land'),
    ('US-4511', 'US-6962', 'Uwharrie National Forest and State Game Land'),
    ('CA-1320', 'CA-1321', 'Blair Township Wilderness Area'),
    ('CA-1361', 'CA-1362', 'Crane Lake(s) Conservation Reserve'),
    ('CA-5113', 'CA-5115', 'Parliament Buildings and Public Grounds'),
    ('CA-3333', 'CA-3334', 'Chu Chua Cottonwood and Chukachida'),
)


def mode():
    """off (default) or report. Anything else stays off so a typo cannot change a build."""
    v = (os.environ.get('KPC_RESEARCH_SOURCES') or 'off').strip().lower()
    return 'report' if v == 'report' else 'off'


def _load_json(name, default):
    p = DATA / name
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:  # noqa: BLE001
        return default


def catalog():
    """Accepted sources. Empty when the catalog file is missing. Never filtered by the flag:
    callers that build a key must use layers(), which is empty unless mode is report."""
    rows = _load_json('catalog.json', [])
    return [r for r in rows if isinstance(r, dict) and not _banned(r.get('url') or '')]


def skipped():
    return _load_json('skipped.json', [])


def layers(builder=None):
    """Sources a builder may consult. Empty unless KPC_RESEARCH_SOURCES=report."""
    if mode() != 'report':
        return []
    rows = catalog()
    if builder:
        rows = [r for r in rows if r.get('builder') == builder]
    return rows


def _banned(url):
    u = url or ''
    return any(b.lower() in u.lower() for b in BANNED)


def fold(s):
    t = ''.join(c for c in unicodedata.normalize('NFKD', str(s or '')) if not unicodedata.combining(c))
    t = t.lower().replace('ß', 'ss')
    return re.sub(r'[^a-z0-9]+', ' ', t).strip()


def _abbrev_tokens():
    """Short agency abbreviations (ZEC, WMA, SNP, SAC, NNR, ...). Phrases are not expanded."""
    out = []
    p = DATA / 'abbreviations.csv'
    if not p.is_file():
        return out
    for r in csv.DictReader(p.open(encoding='utf-8')):
        ab = fold(r.get('abbrev') or '')
        ex = fold(r.get('expansion') or '')
        if re.fullmatch(r'[a-z]{2,8}', ab) and ex and ex != ab:
            out.append((ab, ex))
    # longest token first so a short one does not eat a longer one
    return sorted(set(out), key=lambda x: -len(x[0]))


_ABBREV = None


def abbrev_tokens():
    global _ABBREV
    if _ABBREV is None:
        _ABBREV = _abbrev_tokens()
    return _ABBREV


def canon_name(s, report=None):
    """Name for matching. Abbreviations, the Natrue typo, and the wrong ZEC 'Nature Reserve'
    suffix are applied only when report is true (or when the flag is report and report is None)."""
    if report is None:
        report = mode() == 'report'
    t = fold(s)
    if not report:
        return t
    t = t.replace('natrue', 'nature')
    if re.search(r'\bzec\b', t) and t.endswith('nature reserve'):
        t = re.sub(r'\s+nature reserve$', '', t).strip()
    for ab, ex in abbrev_tokens():
        t = re.sub(rf'\b{re.escape(ab)}\b', ex, t)
    return re.sub(r'\s+', ' ', t).strip()


def names_match(a, b, report=None):
    return bool(canon_name(a, report)) and canon_name(a, report) == canon_name(b, report)


def core_name(s):
    t = fold(s)
    changed = True
    while changed:
        changed = False
        for k in KIND_TAILS:
            if t.endswith(k) and len(t) > len(k) + 1:
                t = t[: -len(k)].strip()
                changed = True
                break
    return t


def hosts_in(candidate, park_names):
    """Park refs whose name contains this candidate's core name. park_names = {ref: name}."""
    core = core_name(candidate)
    if len(core) < 4:
        return []
    return sorted(ref for ref, n in (park_names or {}).items() if core in fold(n))


def _refs(cell):
    return [x.strip() for x in re.split(r'[;,]', str(cell or '')) if re.match(r'^[A-Z]{1,4}-\d{3,5}$', x.strip())]


def evaluate_case(row):
    """One pack test case, as report mode would file it. Pins are never moved. No new POTA ref is created."""
    name = row.get('official_name') or ''
    refs = _refs(row.get('pota_ref_if_any'))
    kind = (row.get('case_type') or '').strip()
    low = fold(name)
    ev = {
        'jurisdiction': row.get('jurisdiction') or '',
        'name': name,
        'refs': refs,
        'case_type': kind,
        'pins_moved': False,
        'new_park': False,
        'counted': True,
        'hosts': [],
        'parent': '',
        'designations': [],
        'shared_pin': False,
        'notes': [],
    }
    if kind == 'not_eligible' or any(w in low for w in NOT_ELIGIBLE_NAMES):
        ev['counted'] = False
        ev['new_park'] = False
        ev['notes'].append('not eligible: not offered as a new park')
        if 'endeavour' in low:
            ev['notes'].append('offshore marine pin is where the MPA is; do not flag it for leaving the land box')
        return ev
    if any(r in INACTIVE for r in refs) or 'cilygroeslwyd' in low:
        ev['counted'] = False
        ev['notes'].append('inactive (GB-2511 Coed Cilygroeslwyd); do not count it')
        return ev
    if any(r in NOT_MISSING_DOC for r in refs) or 'te urewera' in low:
        ev['notes'].append('Te Urewera is not Crown public conservation land after the 2014 Act; do not flag it as missing from DOC')
        return ev
    if any(r in COMBO for r in refs) or ('walton moss' in low and 'sac' in low):
        ev['designations'] = list(COMBO.get(refs[0], ('SAC', 'NNR'))) if refs else ['SAC', 'NNR']
        ev['notes'].append('one ref covers SAC and NNR; do not propose the NNR as a separate new park')
        return ev
    for r in refs:
        if r in NESTED:
            ev['parent'] = NESTED[r]
            ev['hosts'] = [NESTED[r]]
            ev['notes'].append(f'nested 2-fer inside {NESTED[r]}')
            return ev
    if 'glendalough' in low:
        ev['parent'] = 'IE-0003'
        ev['hosts'] = ['IE-0003']
        ev['notes'].append('nested 2-fer inside IE-0003')
        return ev
    for a, b, label in SHARED_PINS:
        if a in refs or b in refs:
            ev['shared_pin'] = True
            ev['hosts'] = [a, b]
            ev['notes'].append(f'shared pin: {label}; report only, pin not moved')
            if 'bladen' in label.lower() or 'uwharrie' in label.lower():
                ev['notes'].append('2-fer hint, not an error')
            return ev
    if 'chukachida' in low or 'chu chua' in low:
        ev['shared_pin'] = True
        ev['hosts'] = ['CA-3333', 'CA-3334']
        ev['notes'].append('CA-3334 Chukachida shares the CA-3333 Chu Chua pin; report only, pin not moved')
        return ev
    host = HOST_ONLY.get(low)
    if host:
        ev['hosts'] = list(host)
        ev['notes'].append(f'inside host {"/".join(host)} only; not a separate POTA park')
        return ev
    # Kaikoura pair even when the row names only one of them
    if any(r in ('NZ-0928', 'NZ-0614') for r in refs) or 'kaik' in low or 'marokura' in low:
        ev['shared_pin'] = True
        ev['hosts'] = ['NZ-0928', 'NZ-0614']
        ev['notes'].append('near-duplicate Kaikoura marine refs; NZ-0614 pin looks inland; report only')
        return ev
    if kind == 'new_fit':
        ev['notes'].append('new-fit candidate stays a report note; no park is added while the flag is report')
    return ev


def twofer_notes(cases=None):
    notes = []
    for ev in cases or []:
        if ev.get('hosts') and not ev.get('shared_pin') and ev.get('case_type') != 'not_eligible':
            if ev['hosts'] == ['US-1274'] or ev['hosts'] == ['US-1286'] or ev.get('parent'):
                notes.append({'refs': ev['refs'] or ev['hosts'], 'name': ev['name'], 'why': '; '.join(ev['notes'])})
        elif ev.get('designations'):
            notes.append({'refs': ev['refs'], 'name': ev['name'], 'why': '; '.join(ev['notes'])})
    # stable order
    return notes


def would_change(cases=None):
    """What report mode would change. The key files themselves are not changed.
    Acres and owners are not measured here: the shapes are not in the repo and no key rebuild is run."""
    if cases is None:
        cases = []
        p = DATA / 'test_cases.csv'
        if p.is_file():
            cases = list(csv.DictReader(p.open(encoding='utf-8')))
    ev = [evaluate_case(r) for r in cases]
    by = {}
    for src in catalog():
        area = src.get('area') or src.get('jurisdiction') or '?'
        bucket = by.setdefault(area, {'report': [], 'matching_only': []})
        bucket[src.get('use') or 'report'].append(src.get('title') or src.get('id'))
    notes = twofer_notes(ev)
    return {
        'mode_when_read': mode(),
        'key_bytes_changed': False,
        'pins_moved': 0,
        'joins_would_add': sum(1 for e in ev if e['new_park']),
        'joins_would_drop': 0,
        'acres_would_change': None,
        'owners_would_change': None,
        'acres_owners_why': 'not measured: shapes are not stored in the repo, and no key rebuild was run',
        'twofers_would_note': len(notes),
        'twofer_notes': notes,
        'sources_by_area': {k: {kk: vv for kk, vv in v.items() if vv} for k, v in sorted(by.items())},
        'cases': ev,
    }


def leave_key_unchanged(doc):
    """The research flag never edits a key document. Returns the same object."""
    return doc


def note_saved(path, doc):
    """Called by kpc_tracts.save AFTER the tract file is written.
    Off: return, write nothing, do not change doc.
    Report: write <file>.research.json beside it. The tract file is already on disk and is not rewritten."""
    if mode() != 'report':
        return None
    path = pathlib.Path(path)
    rep = would_change()
    rep['area'] = (doc or {}).get('area') or path.stem
    rep['about'] = ('Side report only. The tract file and the answer key were not changed. '
                    'KPC_RESEARCH_SOURCES=report. Abbreviations apply to name matching in this report only.')
    # drop the long per-case list from the side file; counts and notes stay
    rep.pop('cases', None)
    out = path.with_name(path.stem + '.research.json')
    out.write_text(json.dumps(rep, ensure_ascii=False, sort_keys=True, indent=1) + '\n', encoding='utf-8')
    return out


# Workbench name matcher (Mapping Rep Tool Box, kpc-maprep-check.js nameScore / canon).
# Kind words dropped the same way. Abbreviations from the research packs are applied only in report mode.
_CORE_DROP = ('wildlife', 'management', 'area', 'state', 'national', 'park', 'parks', 'nature', 'preserve',
              'natural', 'forest', 'refuge', 'the', 'of', 'and', 'site', 'historic', 'historical',
              'recreational', 'recreation', 'resort', 'game')
_GENERIC = {'creek', 'lake', 'river', 'fork', 'branch', 'ridge', 'county', 'hunting', 'public',
            'north', 'south', 'east', 'west'}
# Pile solver lives in KPC-Data, not this repo. The patch in docs/ does not turn auto on.
PILE_SOLVER = {
    'repo': 'KentuckyPortableClub/KPC-Data',
    'path': '.github/scripts/kpc_pile_solver.py',
    'auto': False,
    'patch': 'docs/kpc-pile-solver-research-report.patch',
}
AGENCIES_FILE = ROOT / 'data' / 'maprep' / 'agencies.json'
_BAD_LINK = re.compile(r'HTTP [45]\d\d|no answer|SSL|Name or service|CERTIFICATE', re.I)


def _dice(a, b):
    if a == b:
        return 1.0
    if not a or not b or len(a) < 2 or len(b) < 2:
        return 0.0
    def bg(s):
        m = {}
        for i in range(len(s) - 1):
            k = s[i:i + 2]
            m[k] = m.get(k, 0) + 1
        return m
    A, B = bg(a), bg(b)
    inter = sum(min(n, B.get(k, 0)) for k, n in A.items())
    return (2 * inter) / ((sum(A.values()) + sum(B.values())) or 1)


def workbench_canon(s, report=None):
    """The Tool Box canon(): dotted WMA / SNP / SNA / SP, then a core with kind words removed.
    Pack abbreviations are expanded only when report is true."""
    if report is None:
        report = mode() == 'report'
    t = canon_name(s, report=report)
    t = t.replace('w m a', ' wildlife management area ')
    t = re.sub(r'\bwma\b', ' wildlife management area ', t)
    t = re.sub(r'\bsnp\b', ' state nature preserve ', t)
    t = re.sub(r'\bsna\b', ' state natural area ', t)
    t = re.sub(r'\bsp\b', ' state park ', t)
    t = re.sub(r'\s+', ' ', t).strip()
    core = t
    for w in _CORE_DROP:
        core = re.sub(rf'\b{w}\b', ' ', core)
    core = re.sub(r'\s+', ' ', core).strip() or t
    return t, core


def name_score(query, candidate, report=None):
    """0-96, same steps as the Tool Box nameScore. 0 means it would not be offered."""
    if report is None:
        report = mode() == 'report'
    qf, qc = workbench_canon(query, report=report)
    cf, cc = workbench_canon(candidate, report=report)
    if not qc or not cc:
        return 0
    if qc == cc or qf == cf:
        return 96
    qt = [w for w in qc.split() if len(w) > 2]
    ct = [w for w in cc.split() if len(w) > 2]
    if qt and all(w in ct for w in qt):
        return 92 if len(ct) == len(qt) else 84
    d = _dice(qc, cc)
    shared = [w for w in qt if w in ct and w not in _GENERIC and len(w) >= 4]
    if d >= 0.8 and shared:
        return 70
    if d >= 0.72 and shared:
        return 58
    if any(len(w) >= 6 for w in shared) and d >= 0.45:
        return 52
    return 0


def rank_outlines(park_name, candidates, report=None):
    """Rank candidate outlines for the pile solver. Empty unless report mode.
    Does not pick a join and does not turn pile-solver auto on (that stays false)."""
    if report is None:
        report = mode() == 'report'
    if not report:
        return []
    out = []
    for c in candidates or []:
        name = c.get('name') if isinstance(c, dict) else str(c)
        row = dict(c) if isinstance(c, dict) else {'name': name}
        row['name'] = name
        row['score'] = name_score(park_name, name, report=True)
        out.append(row)
    out.sort(key=lambda r: (-r['score'], str(r.get('id') or ''), str(r.get('name') or '')))
    return out


def pile_solver_where():
    """The solver is not in this repo. auto stays false; the patch is report-only."""
    return dict(PILE_SOLVER)


def _place_code(area):
    a = (area or '').strip().upper()
    if not a:
        return ''
    parts = a.split('-')
    return parts[-1] if len(parts[-1]) <= 3 else a


def _role_for(kind, name):
    blob = fold(f'{kind or ""} {name or ""}')
    if any(w in blob for w in ('nature preserve', 'natural area', 'heritage land')):
        return 'preserves'
    if any(w in blob for w in ('wildlife', 'game land', 'refuge', ' wma')):
        return 'wildlife'
    if 'forest' in blob:
        return 'forestry'
    return 'parks'


def load_agencies(path=None):
    p = pathlib.Path(path or AGENCIES_FILE)
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except Exception:  # noqa: BLE001
        return {}


def _page(block):
    if not isinstance(block, dict):
        return '', False
    return str(block.get('url') or ''), bool(block.get('verified'))


def suggest_agency(area, kind='', name='', agencies=None):
    """The state or province agency page that matches this park's kind. '' when the file has none."""
    places = (agencies or load_agencies()).get('places') or {}
    place = places.get(_place_code(area))
    if not place:
        return {}
    role = _role_for(kind, name)
    ags = place.get('agencies') or []
    # Prefer the agency whose own role is the one we want. A forestry office that also
    # lists preserves must not hide the preserves office.
    pick = next((ag for ag in ags if str(ag.get('role') or '').lower() == role), None)
    if pick is None:
        for ag in ags:
            roles = [str(x).lower() for x in (ag.get('roles') or [])]
            if role in roles:
                pick = ag
                break
    if pick is None and ags:
        pick = ags[0]
        role = str(pick.get('role') or role)
    if not pick:
        return {}
    finder, fv = _page(pick.get('finder'))
    home, hv = _page(pick.get('home'))
    url, verified = (finder, fv) if finder and fv else (home, hv) if home and hv else (finder or home, fv or hv)
    return {'place': place.get('name') or _place_code(area), 'agency': pick.get('name') or '',
            'role': role, 'url': url, 'verified': bool(verified and url)}


def _link_problem(rec):
    """'missing', 'broken', or '' . Uses stored checks only (no new fetch). HTTP 429 is not treated as broken."""
    rec = rec or {}
    web = str(rec.get('web') or '')
    agency = str(rec.get('agency_page') or '')
    official = web if web.startswith('http') else agency if agency.startswith('http') else ''
    bad = []
    for key, val in (rec.get('map_check') or {}).items():
        if key == 'date':
            continue
        s = str(val or '')
        if not s or s.lower() in ('ok', '200') or '429' in s:
            continue
        if _BAD_LINK.search(s) or s.upper().startswith('HTTP '):
            bad.append(f'{key}: {s}')
    if bad:
        return 'broken', official, '; '.join(bad)
    if not official:
        return 'missing', '', ''
    return '', official, ''


def link_postcheck(rows, agencies=None):
    """rows: [{ref, area, name, kind, web, agency_page, map_check}].
    Empty unless report mode. Does not edit the rows."""
    if mode() != 'report':
        return []
    agencies = agencies if agencies is not None else load_agencies()
    out = []
    for row in rows or []:
        problem, official, detail = _link_problem(row)
        if not problem:
            continue
        sug = suggest_agency(row.get('area'), row.get('kind'), row.get('name'), agencies)
        out.append({
            'ref': row.get('ref') or '',
            'area': row.get('area') or '',
            'name': row.get('name') or '',
            'kind': row.get('kind') or '',
            'problem': problem,
            'official': official,
            'detail': detail,
            'suggest_agency': sug.get('agency') or '',
            'suggest_url': sug.get('url') or '',
            'suggest_verified': bool(sug.get('verified')),
        })
    return out


def scan_link_postcheck(root=None):
    """Read the keys and data/parkinfo-web.json. Report mode only. No network."""
    if mode() != 'report':
        return []
    root = pathlib.Path(root or ROOT)
    names = {}
    for f in sorted((root / 'data' / 'us-key').glob('US-*.json')):
        area = 'US-' + f.stem.split('-')[-1]
        try:
            parks = json.loads(f.read_text(encoding='utf-8')).get('parks') or {}
        except Exception:  # noqa: BLE001
            continue
        for ref, p in parks.items():
            if isinstance(p, dict):
                names[ref] = (area, p.get('n') or '', p.get('t') or '')
    ky = root / 'data' / 'ky-answer-key.json'
    if ky.is_file():
        try:
            parks = json.loads(ky.read_text(encoding='utf-8')).get('parks') or {}
        except Exception:  # noqa: BLE001
            parks = {}
        for ref, p in parks.items():
            if isinstance(p, dict):
                names[ref] = ('US-KY', p.get('n') or '', p.get('t') or '')
    for f in sorted((root / 'data' / 'ca-key').glob('CA-*.json')):
        area = f.stem if f.stem.startswith('CA-') else 'CA-' + f.stem
        try:
            parks = json.loads(f.read_text(encoding='utf-8')).get('parks') or {}
        except Exception:  # noqa: BLE001
            continue
        for ref, p in parks.items():
            if isinstance(p, dict):
                names.setdefault(ref, (area, p.get('n') or '', p.get('t') or ''))
    web = {}
    try:
        web = (json.loads((root / 'data' / 'parkinfo-web.json').read_text(encoding='utf-8')).get('parks') or {})
    except Exception:  # noqa: BLE001
        web = {}
    rows = []
    for ref, rec in web.items():
        if not isinstance(rec, dict):
            continue
        area, name, kind = names.get(ref, ('', '', ''))
        if not area and str(ref).startswith('CA-'):
            area = 'CA'
        rows.append({'ref': ref, 'area': area, 'name': name, 'kind': kind, 'web': rec.get('web') or '',
                     'agency_page': rec.get('agency_page') or '', 'map_check': rec.get('map_check') or {}})
    return link_postcheck(rows)


def builder_of(jurisdiction):
    j = (jurisdiction or '').strip().upper()
    if j.startswith('US'):
        return 'us'
    if j.startswith('CA'):
        return 'ca'
    if j.startswith('GB') or j.startswith('IE') or j.startswith('AU') or j.startswith('NZ') or j in ('GB', 'IE', 'AU', 'NZ'):
        return 'world'
    return ''
