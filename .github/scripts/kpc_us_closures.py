#!/usr/bin/env python3
"""US state agency closures for every park tool (chat 2, Oct 25 2026; Brandon's maps to-do: 'closures for every state',
sources found by the outside research bot, round 4: .claude/build/research/KPC_Round4_results.xlsx).

Reads the agencies' OWN machine-readable feeds (ArcGIS status layers, a published CSV, RSS) - never a page that blocks
robots - ties each closure to POTA parks by the park's name (the US answer key's name rules) and, when the feed has a
location, only within NEAR_KM of the park's pin. Writes:
  data/alerts/us-parks.json  {about, sources: {id: {agency, st, page, ok, n, why}}, items: [...]}
  kpc-conditions.json        the same items as 'uc-...' entries (Kit, Park Notes, planners, reports and the app read it;
                             Kentucky's own bot keeps its 'pa-...' entries; nothing here posts anywhere).
A source that fails keeps its last items (a failed read is not 'reopened'). Only writes when something changed.
Never fails (exit 0). Run by .github/workflows/kpc-us-closures.yml every 6 hours. `--merge` = only redo the
kpc-conditions.json merge from data/alerts/us-parks.json (the workflow uses it when a push has to be retried)."""
import csv, datetime as dt, email.utils, html, io, json, pathlib, re, sys, time, types, urllib.parse, urllib.request
import xml.etree.ElementTree as ET
from kpc_save import save_json, source_clock

UA = {'User-Agent': 'KPC park closures (kentuckyportableclub.github.io)'}
OUT = pathlib.Path('data/alerts/us-parks.json')
COND = pathlib.Path('kpc-conditions.json')
NEAR_KM = 40
RSS_DAYS = 45            # a news-style closure post older than this is not shown
TODAY = dt.date.today()


def notice(t, m): print('::notice title=%s::%s' % (t, str(m).replace('%', '%25').replace('\n', ' ')[:900]), flush=True)


def get(url, params=None, raw=False, tries=3, timeout=90):
    u = url + ('?' + urllib.parse.urlencode(params) if params else '')
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=timeout) as r:
                b = r.read()
            if raw: return b
            j = json.loads(b.decode('utf-8', 'replace'))
            if isinstance(j, dict) and j.get('error'): raise RuntimeError(str(j['error'])[:160])
            return j
        except Exception as e:  # noqa: BLE001
            last = e; time.sleep(3 + 4 * i)
    raise last


def _key():     # the US answer key's name rules, loaded without running the key itself
    p = pathlib.Path(__file__).resolve().parent / 'kpc_us_key.py'
    src = p.read_text(encoding='utf-8').split('\nidx = {}\n')[0]
    m = types.ModuleType('kpc_us_key'); m.__file__ = str(p)
    exec(compile(src, 'kpc_us_key.py', 'exec'), m.__dict__)
    return m


# ---------------------------------------------------------------- small helpers
def F(a, *names):
    """First non-empty attribute among names, any letter case."""
    low = {k.lower(): v for k, v in a.items()}
    for n in names:
        v = low.get(n.lower())
        if v not in (None, '', ' '): return v
    return None


def day(v):
    """An ArcGIS date (ms), an ISO text or 'M/D/YYYY' -> date, else None."""
    if v in (None, ''): return None
    try:
        if isinstance(v, (int, float)) and v > 1e10: return dt.datetime.utcfromtimestamp(v / 1000).date()
        s = str(v).strip()
        for f in ('%Y-%m-%d', '%m/%d/%Y', '%m/%d/%y', '%B %d, %Y', '%b %d, %Y'):
            try: return dt.datetime.strptime(s[:len(dt.date.today().strftime(f)) + 4].strip(), f).date()
            except ValueError: pass
        m = re.match(r'(\d{4})-(\d\d)-(\d\d)', s)
        if m: return dt.date(*map(int, m.groups()))
        m = re.match(r'(\d{1,2})/(\d{1,2})/(\d{2,4})', s)
        if m:
            y = int(m.group(3)); y += 2000 if y < 100 else 0
            return dt.date(y, int(m.group(1)), int(m.group(2)))
    except Exception:  # noqa: BLE001
        return None
    return None


def clean(s, cap=300):
    s = html.unescape(re.sub(r'<[^>]+>', ' ', str(s or '')))
    return re.sub(r'\s+', ' ', s).strip()[:cap]


def xy(g):
    if not g: return None
    if 'x' in g and 'y' in g: return g['y'], g['x']
    pts = [p for r in (g.get('rings') or g.get('paths') or []) for p in r]
    if not pts: return None
    return sum(p[1] for p in pts) / len(pts), sum(p[0] for p in pts) / len(pts)


def km(a, b, c, d):
    import math
    p = math.pi / 180
    h = math.sin((c - a) * p / 2) ** 2 + math.cos(a * p) * math.cos(c * p) * math.sin((d - b) * p / 2) ** 2
    return 12742 * math.asin(math.sqrt(h))


def arcgis(url, where='1=1'):
    out, off = [], 0
    while True:
        j = get(url.rstrip('/') + '/query', {'where': where, 'outFields': '*', 'returnGeometry': 'true', 'outSR': 4326,
                                            'f': 'json', 'resultOffset': off, 'resultRecordCount': 1000})
        fs = j.get('features') or []
        out += fs
        if not fs or not j.get('exceededTransferLimit') or off > 20000: return out
        off += len(fs)


def rss(url):
    root = ET.fromstring(get(url, raw=True))
    out = []
    for it in root.iter('item'):
        t = lambda k: (it.findtext(k) or '').strip()  # noqa: E731
        try: d = email.utils.parsedate_to_datetime(t('pubDate')).date()
        except Exception: d = None  # noqa: E722
        out.append({'title': clean(t('title'), 200), 'text': clean(t('description'), 400), 'link': t('link'), 'date': d})
    return out


# ---------------------------------------------------------------- each source: rows of {name, title, text, link, end, at}
def src_ca():
    rows = []
    for f in arcgis('https://services2.arcgis.com/AhxrK3F6WM8ECvDi/arcgis/rest/services/CSPParkUnit_CurrentStatus/FeatureServer/0'):
        a = f.get('attributes') or {}
        st = str(F(a, 'Status', 'STATUS', 'CurrentStatus', 'Unit_Status', 'ParkStatus') or '')
        if not st or st.strip().upper() == 'OPEN': continue
        rows.append({'name': F(a, 'UNITNAME', 'UnitName'), 'title': st.title(),
                     'text': ' · '.join(x for x in (clean(F(a, 'closure_reason')), clean(F(a, 'status_notes_pub'))) if x),
                     'end': day(F(a, 'StatusReopenDate')), 'at': xy(f.get('geometry')), 'link': ''})
    return rows


def src_wi():
    rows = []
    for f in arcgis('https://services5.arcgis.com/Ul9AyFFeFTjf08DW/arcgis/rest/services/WI_Park_Closures_PUBLIC_VIEW/FeatureServer/0'):
        a = f.get('attributes') or {}
        if str(F(a, 'Active_Flag') or 'Y').strip().upper() in ('N', 'NO', '0', 'FALSE', 'INACTIVE'): continue
        end = day(F(a, 'Exp_End_Date'))
        if end and end < TODAY: continue
        rows.append({'name': F(a, 'Full_Prop_Name', 'Actual_Prop_Name', 'Property'), 'title': clean(F(a, 'Closure_Name'), 160) or 'Notice',
                     'text': clean(F(a, 'Reason', 'Description', 'Details')), 'end': end, 'at': xy(f.get('geometry')), 'link': ''})
    return rows


def src_fl():
    rows = []
    for lid, what in ((6, ''), (5, 'Campground: ')):
        for f in arcgis(f'https://services1.arcgis.com/nRHtyn3uE1kyzoYc/arcgis/rest/services/Florida_State_Parks_Operational_Status/FeatureServer/{lid}'):
            a = f.get('attributes') or {}
            st = str(F(a, 'PARK_STATUS', 'STATUS', 'CAMP_STATUS') or '')
            if not st or st.strip().lower().startswith('open'): continue
            nm = str(F(a, 'SITE_NAME', 'PARK_NAME') or '')
            rows.append({'name': re.sub(r'\s*[-–:]?\s*(full[- ]facility |primitive |group )?camp(ground|ing|site)s?\b.*$', '', nm, flags=re.I) or nm,
                         'title': what + st, 'text': clean(F(a, 'COMMENTS', 'Comments')), 'end': None,
                         'at': xy(f.get('geometry')), 'link': ''})
    return rows


def src_mt():
    rows = []
    for f in arcgis('https://services3.arcgis.com/Cdxz8r11hT0MGzg1/arcgis/rest/services/FWPLND_LANDS_CLOSURES_RESTRICTIONS/FeatureServer/0'):
        a = f.get('attributes') or {}
        end = day(F(a, 'DATE_END'))
        if end and end < TODAY: continue
        beg = day(F(a, 'DATE_BEGIN'))
        if beg and beg > TODAY + dt.timedelta(days=14): continue
        rows.append({'name': F(a, 'SITE_NAME'), 'title': clean(F(a, 'RESTRICTION'), 120) or 'Restriction',
                     'text': clean(F(a, 'DESCRIPTION')), 'end': end, 'at': xy(f.get('geometry')), 'link': F(a, 'WEBLINK') or ''})
    return rows


def src_mo():
    rows = []
    for f in arcgis('https://gis.dnr.mo.gov/server/rest/services/parks/State_Parks_Status_Viewer/MapServer/0'):
        a = f.get('attributes') or {}
        st = str(F(a, 'STATUS') or '').strip()
        adv = []
        for n in range(1, 11):
            if str(F(a, f'ADVISORY_{n}_SHOW') or '').strip().upper() == 'Y':
                t = clean(F(a, f'ADVISORY_{n}'), 200)
                if t: adv.append(t)
        if (not st or st.lower() == 'open') and not adv: continue
        rows.append({'name': F(a, 'LOC_NAME'), 'title': st if st and st.lower() != 'open' else 'Advisory',
                     'text': ' · '.join(adv), 'end': None, 'at': xy(f.get('geometry')), 'link': F(a, 'URL') or ''})
    return rows


def src_nj():
    rows = []
    for f in arcgis('https://services1.arcgis.com/QWdNfRs7lkPq4g4Q/arcgis/rest/services/'
                    'New_Jersey_State_Park_Service_Live_Status_Updates_(Public_View)/FeatureServer/0'):
        a = f.get('attributes') or {}
        st = str(F(a, 'Status') or '').strip()
        if not st or st.lower().startswith('open'): continue
        rows.append({'name': F(a, 'ParkName'), 'title': st, 'text': clean(F(a, 'Park_Hours', 'Notes', 'Comments')),
                     'end': None, 'at': xy(f.get('geometry')), 'link': F(a, 'Facility_URL') or ''})
    return rows


def src_or():
    rows = []
    for f in arcgis('https://nrimp.dfw.state.or.us/arcgis/rest/services/ORHAM/ORHAM/MapServer/6', 'alert_enabled=1'):
        a = f.get('attributes') or {}
        end = day(F(a, 'alert_end'))
        if end and end < TODAY: continue
        rows.append({'name': F(a, 'subdivision'), 'title': clean(F(a, 'alert_title'), 160) or 'Alert',
                     'text': clean(F(a, 'alert_text')), 'end': end, 'at': xy(f.get('geometry')), 'link': ''})
    return rows


def src_co():
    # Colorado Parks & Wildlife's own '2026 Weather and Drought Closures' list (a sheet CPW publishes and links from
    # cpw.state.co.us). Drought / low-water / fishing closures only.
    b = get('https://docs.google.com/spreadsheets/d/e/2PACX-1vQv8-zuZoYsA6jhM2l76icNnlVKK6NR36qeamBg_6s2f0POK6-nA0s66Nt_'
            'TcanQeClTXBvBvZGJls9/pub?gid=0&single=true&output=csv', raw=True).decode('utf-8', 'replace')
    rows = []
    for r in csv.DictReader(io.StringIO(b)):
        nm = F(r, 'Name of Location', 'Location')
        if not nm: continue
        end = day(F(r, 'End Date'))
        if end and end < TODAY: continue
        rows.append({'name': nm, 'title': clean(F(r, 'Type of Closure'), 120) or 'Closure',
                     'text': clean(' · '.join(str(v) for k, v in r.items() if k and v and re.search(r'detail|descr|note|reason', k, re.I))),
                     'end': end, 'at': None, 'link': 'https://cpw.state.co.us/'})
    return rows


def _rss_rows(url, keep=r'.'):
    rows = []
    for it in rss(url):
        if it['date'] and (TODAY - it['date']).days > RSS_DAYS: continue
        if not re.search(keep, it['title'] + ' ' + it['text'], re.I): continue
        rows.append({'name': None, 'hay': it['title'] + ' ' + it['text'], 'title': it['title'], 'text': it['text'],
                     'end': None, 'at': None, 'link': it['link'], 'date': it['date']})
    return rows


def src_ar(): return _rss_rows('https://www.agfc.com/category/wma-closure/feed/')
def src_nc(): return _rss_rows('https://www.ncparks.gov/blog-category/alerts/feed', r'clos|status|open|restrict|alert')


# ---------------------------------------------------------------- Georgia WRD closures page (chat 5, Oct 28 2026)
# RULE SHEET: 'GEORGIA WILDLIFE CLOSURES PAGE AS A SOURCE' (website.md) + chat 8's fixes GA-R1..R9
# (.claude/build/research/KPC_RuleSheet_GA_closures_desk.md) + Brandon's rulings GA1-GA9. The page is a hand-written list
# (area heading, 'Updated m/d/yy', free-text sentences), so it is read as plain text, sentence by sentence.
# PREVIEW: until GA_LIVE is True, Georgia's items go only into sources['ga-wrd']['preview'] (for checking), not onto cards.
GA_LIVE = True
GA_PAGE = 'https://georgiawildlife.com/closures'
_GA_AREA = re.compile(r"\b(WMA|PFA|VPA|Wildlife Management Area|Public Fishing Area|Hatchery|Wildlife Center|Education Center|Boat Ramp|Ramp)\b", re.I)
_GA_SECT = re.compile(r'^(WMA,? PFA,? ?(&|and) Hatchery Closures|Shooting Ranges?|Education Centers?|Boat Ramps?|Closures|Cautions|Region \d+.*)$', re.I)
_GA_MON = {m: i + 1 for i, m in enumerate(['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
                                            'september', 'october', 'november', 'december'])}


def _ga_lines(html_text):
    t = re.sub(r'(?is)<(script|style|noscript|nav|header|footer)\b.*?</\1>', ' ', html_text)
    t = re.sub(r'(?i)<br\s*/?>|</(p|div|li|h[1-6]|tr|td|section|article|strong|b)>|<(h[1-6]|li|p)\b[^>]*>', '\n', t)
    t = re.sub(r'<[^>]+>', ' ', t)
    import html as _h
    out = []
    for ln in _h.unescape(t).split('\n'):
        ln = re.sub(r'\s+', ' ', ln).strip()
        if ln: out.append(ln)
    return out


def _ga_end(sent, upd):
    """'through November', 'until January 2027', 'through the end of December' -> last day of that month."""
    m = re.search(r'\b(?:through|until|thru|to)\s+(?:the\s+end\s+of\s+)?(January|February|March|April|May|June|July|August|September|October|November|December)(?:\s+(\d{1,2})(?!\d))?(?:,?\s+(\d{4}))?', sent, re.I)
    if not m: return None
    mo = _GA_MON[m.group(1).lower()]
    yr = int(m.group(3)) if m.group(3) else (upd.year if upd else TODAY.year)
    if not m.group(3) and upd and mo < upd.month: yr += 1          # 'through January' written in August = next year
    if m.group(2):
        try: return dt.date(yr, mo, int(m.group(2)))
        except ValueError: return None
    nxt = dt.date(yr + (mo == 12), mo % 12 + 1, 1)
    return nxt - dt.timedelta(days=1)


def _ga_parse(lines):
    """-> list of (section, heading, heading_names, updated_date, sentence)"""
    out, sect, head, names, upd = [], '', '', [], None
    for ln in lines:
        if re.match(r'(?i)^last updated', ln): continue
        if _GA_SECT.match(ln) and len(ln) < 70:
            if not ln.lower().startswith('region'): sect = ln.lower()
            head, names, upd = (ln, [], None) if ln.lower().startswith('region') else (head, names, upd)
            continue
        mu = re.match(r'(?i)^updated:?\s*(\d{1,2})/(\d{1,2})/(\d{2,4})\s*[,:;-]?\s*(.*)$', ln)
        if mu:
            y = int(mu.group(3)); y += 2000 if y < 100 else 0
            try: upd = dt.date(y, int(mu.group(1)), int(mu.group(2)))
            except ValueError: upd = None
            ln = mu.group(4).strip()
            if not ln: continue
        if len(ln) < 110 and _GA_AREA.search(ln) and not re.search(r'[.!?]$', ln) and not re.search(r'\b(is|are|was|will|has|have)\b', ln):
            head, upd = ln, None
            names = [x.strip() for x in re.split(r'\s*/\s*', re.sub(r'\(.*?\)', '', ln)) if x.strip()]
            continue
        for sent in re.split(r'(?<=[.!?])\s+(?=[A-Z])', ln):
            sent = sent.strip()
            if len(sent) > 8: out.append((sect, head, names, upd, sent))
    return out


def _ga_rows(entries):
    rows, seen = [], {}
    for sect, head, names, upd, sent in entries:
        low = sent.lower()
        if 'shooting range' in sect or 'education' in sect: continue                     # not the park (sheet 2)
        if not names: continue                                                             # 'general' lines: no area named
        # GA-R7: a sentence repeated under two headings = one item, tied to the place the sentence names
        key = re.sub(r'\W+', ' ', low).strip()
        place = next((n for n in names if n.lower().split(' (')[0][:12] in low), None)
        for n in names:
            core = re.sub(r'(?i)\b(wma|pfa|vpa)\b', '', n).strip().lower()
            if core and core in low: place = n
        place = place or names[0]
        if key in seen: continue
        seen[key] = 1
        # GA-R10 (Oct 28, from the first live read): headings repeat the full sentence below them, and
        # 'This closure will affect ...' points back at the item before it: neither is an item of its own
        if re.match(r'^\s*[-\u2013\u2014]', sent): continue
        if len(sent.split()) < 12 and not re.search(r'\b(is|are|will|remains?|has|have|was|were)\b', low): continue
        if re.match(r'(?i)^\s*(this|that|these|the)\s+closures?\b', sent): continue
        tract = re.search(r"(?i)\b([A-Z][\w'. ]{2,40} Tract)\b", sent) or re.search(r"(?i)\b([A-Z][\w'. ]{2,40} Tract)\b", head)
        on = f' on the {tract.group(1)}' if tract else ''
        old = upd is not None and (TODAY - upd).days >= 365
        end = _ga_end(sent, upd)
        if end and end < TODAY: continue                                                  # a window that has ended (GA-R4)
        datestr = f"updated {upd.month}/{upd.day}/{str(upd.year)[2:]}" if upd else 'dates not given'
        base = {'name': place, 'end': end, 'at': None, 'link': GA_PAGE, 'date': upd}
        # NOT closures
        if re.search(r'\bno\b[^.]{0,40}\bclos|\bnot\b[^.]{0,20}\bclos|\bnone\b|remains? open|minimal impact', low) and not re.search(r'\bremains? closed', low):
            continue                                                                      # GA-R2 negations
        if re.search(r'\b(is|are)\s+open\b[^.]*\b(a\.?m\.?|p\.?m\.?)|\bopen from\b|\bgate\b[^.]*\bopen\b', low):
            continue                                                                      # GA-R5 hours = info, not closures
        if re.search(r'quota hunt|drawn hunters?', low):
            rows.append({**base, 'kind': 'Park notice', 'title': '🦌 Drawn quota hunts: check the agency page', 'text': f'Georgia DNR ({datestr}): "{sent}"'}); continue   # GA9
        if re.search(r'lease[^.]*(not (been )?renewed|ended|expired)|no longer (open|available)', low):
            rows.append({**base, 'kind': 'Park notice', 'title': 'ℹ️ May not be public land now', 'text': f'Georgia DNR ({datestr}): "{sent}"'}); continue   # GA3
        if not re.search(r'\bclos(e|ed|es|ing|ure|ures)\b', low): continue                # no closing word = not a closure
        if 'caution' in sect:
            rows.append({**base, 'kind': 'Park notice', 'title': 'Caution', 'text': f'Georgia DNR ({datestr}): "{sent}"'}); continue
        if old and not end:
            rows.append({**base, 'kind': 'Park notice', 'title': f'ℹ️ Old notice ({upd.month}/{upd.day}/{str(upd.year)[2:]})',
                         'text': f'"{sent}" May be out of date: check the agency page.'}); continue   # GA1 / GA-R8 (before the on/off rule)
        if re.search(r'intermittent|periodic|at times|on and off', low):
            rows.append({**base, 'kind': 'Park notice', 'title': '📅 On and off' + on, 'text': f'Georgia DNR ({datestr}): "{sent}"'}); continue   # GA6
        if re.search(r'closed to vehicles?|vehicle traffic', low) and not re.search(r'all traffic|all access|foot|pedestrian', low):
            rows.append({**base, 'kind': 'Park notice', 'title': 'Roads closed to vehicles (walking allowed)' + on, 'text': f'Georgia DNR ({datestr}): "{sent}"'}); continue   # GA2
        if old and not end:
            rows.append({**base, 'kind': 'Park notice', 'title': f'ℹ️ Old notice ({upd.month}/{upd.day}/{str(upd.year)[2:]})',
                         'text': f'"{sent}" May be out of date: check the agency page.'}); continue   # GA1 / GA-R8
        # GA-R3: 'the bathhouse and north side of the campground are closed' = a facility note + a part closure
        m2 = re.match(r'(?i)^(?:the\s+)?(bath ?house|restrooms?|showers?|office|pavilion)\s+and\s+(.+?)\s+(?:is|are|will be)\s+closed', sent)
        if m2:
            rows.append({**base, 'kind': 'Park notice', 'title': f'{m2.group(1).capitalize()} closed' + on, 'text': f'Georgia DNR ({datestr}): "{sent}"'})
            rows.append({**base, 'kind': 'Closure', 'title': f'PART CLOSED: {m2.group(2)}' + on, 'text': f'Georgia DNR ({datestr}): "{sent}"'})
            continue
        whole = re.search(r'closed to all (access|public use)', low) and any(n.lower().split(' (')[0] in low for n in names) \
            and not re.search(r'\b(lake|pond|road|trail|bridge|boardwalk|ramp|campground|area of|portion|section)\b', low)
        mp = re.match(r'(?i)^(?:the\s+)?(.{3,90}?)\s+(?:is|are|will be|remains?|has been|have been)\s+(?:currently\s+|temporarily\s+)?closed', sent)
        part = (mp.group(1) if mp else '').strip()
        if not part:
            mc = re.match(r'(?i)^(?:the\s+)?(.{3,80}?)\s+(?:has\s+a\s+)?(?:temporary\s+)?closure\b', sent)
            part = (mc.group(1) if mc else '').strip()
        if not part or len(part) > 60:                                                    # long lead-in: name the road/trail it is about
            mr = re.search(r"([A-Z][\w'.]*(?:\s+[A-Z0-9][\w'.]*){0,4}\s+(?:Road|Rd\.|Trail|Trailhead|Bridge|Boardwalk|Campground|Ramp))", sent)
            part = mr.group(1) if mr else ''
        if tract and tract.group(1).lower() in part.lower(): on = ''                     # don't say the tract twice
        title = 'CLOSED' + on if whole else ('PART CLOSED: ' + part + on if part else 'PART CLOSED' + on)
        rows.append({**base, 'kind': 'Closure', 'title': title, 'text': f'Georgia DNR ({datestr}): "{sent}"'})
    return rows


def src_ga():
    b = get(GA_PAGE, raw=True).decode('utf-8', 'replace')
    rows = _ga_rows(_ga_parse(_ga_lines(b)))
    if not rows and 'closure' not in b.lower():
        raise RuntimeError('page layout changed: nothing readable')   # keeps last items (sheet 4)
    return rows


SOURCES = [  # id, state, agency, its page for people, reader
    ('ca-parks', 'CA', 'California State Parks', 'https://www.parks.ca.gov/?page_id=30009', src_ca),
    ('wi-dnr', 'WI', 'Wisconsin DNR', 'https://dnr.wisconsin.gov/topic/parks/propertynotices', src_wi),
    ('fl-parks', 'FL', 'Florida State Parks', 'https://www.floridastateparks.org/', src_fl),
    ('mt-fwp', 'MT', 'Montana FWP', 'https://fwp.mt.gov/news/current-closures-restrictions', src_mt),
    ('mo-parks', 'MO', 'Missouri State Parks', 'https://mostateparks.com/basic-page/active-advisories', src_mo),
    ('nj-parks', 'NJ', 'NJ State Park Service', 'https://dep.nj.gov/parksandforests/', src_nj),
    ('or-odfw', 'OR', 'Oregon Dept. of Fish & Wildlife', 'https://myodfw.com/', src_or),
    ('co-cpw', 'CO', 'Colorado Parks & Wildlife', 'https://cpw.state.co.us/', src_co),
    ('ar-agfc', 'AR', 'Arkansas Game & Fish', 'https://www.agfc.com/category/wma-closure/', src_ar),
    ('nc-parks', 'NC', 'NC State Parks', 'https://www.ncparks.gov/', src_nc),
    ('ga-wrd', 'GA', 'Georgia DNR Wildlife Resources', 'https://georgiawildlife.com/closures', src_ga),
]


# ---------------------------------------------------------------- tie a row to parks
def park_list(st):
    try: P = json.load(open(f'data/parkinfo/US-{st}.json', encoding='utf-8'))['parks']
    except Exception: return {}  # noqa: E722
    return {ref: (v[0], v[2] or '', v[5], v[6]) for ref, v in P.items() if v[5] is not None and 'National' not in (v[2] or '')}


# the agencies' short forms (the key already knows SWA / SRA / SNA ...); 'ST' here is State Trail, not Saint
SHORT = [(r'\bSHP\b', 'State Historical Park'), (r'\bSHS\b', 'State Historic Site'), (r'\bSB\b', 'State Beach'),
         (r'\bSVRA\b', 'State Vehicle Recreational Area'), (r'\bSNR\b', 'State Natural Reserve'), (r'\bSP\b', 'State Park'),
         (r'\bSF\b', 'State Forest'), (r'\bST\b', 'State Trail'), (r'\bSWA\b', 'State Wildlife Area'),
         (r'\bWA\b$', 'Wildlife Area'), (r'\bFAS\b', 'Fishing Access Site')]


def match(K, row, parks, st=''):
    hit = []
    if row.get('name'):
        nm = str(row['name'])
        for rx, full in SHORT: nm = re.sub(rx, full, nm)
        kn = K.kinds(nm)
        for ref, (pn, typ, la, lo) in parks.items():
            if row.get('at') and km(la, lo, *row['at']) > NEAR_KM: continue
            if K.name_ok(pn, nm, K.kinds(pn) | K.kinds(typ), kn): hit.append(ref)
        if hit or not row.get('at'): return hit
        # close by (15 km) and every word of the park's own name inside the notice's longer name:
        # 'Dr. Edmund A. Babler Memorial State Park' = Babler Memorial State Park, 'Southern Unit - Kettle Moraine SF'
        have = set(K.norm(nm).split())
        for ref, (pn, typ, la, lo) in parks.items():
            if km(la, lo, *row['at']) > 15: continue
            core = [w for w in K.norm(pn).split() if w != st.lower()]
            if core and len(' '.join(core)) >= 6 and set(core) <= have and K.same_kind(K.kinds(pn) | K.kinds(typ), kn): hit.append(ref)
        return hit
    hay = ' ' + K.norm(row.get('hay') or '') + ' '            # news-style post: the park's own name inside the text
    for ref, (pn, typ, la, lo) in parks.items():
        core = K.norm(pn)
        if len(core) >= 8 and ' ' in core and f' {core} ' in hay: hit.append(ref)
    return hit


def merge():
    try: d = json.load(open(OUT, encoding='utf-8'))
    except Exception: return  # noqa: E722
    try: cond = json.load(open(COND, encoding='utf-8'))
    except Exception: cond = {'items': []}  # noqa: E722
    items = [c for c in cond.get('items', []) if not str(c.get('id', '')).startswith('uc-')]
    for it in d.get('items', []):
        items.append({k: it[k] for k in ('id', 'ref', 'kind', 'details', 'seen', 'call', 'expires', 'link') if it.get(k)})
    items.sort(key=lambda c: (c.get('seen', ''), c.get('id', '')), reverse=True)
    if items != cond.get('items'):
        cond['items'] = items
        cond['updated'] = TODAY.isoformat()
        COND.write_text(json.dumps(cond, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
        print(f'kpc-conditions.json: {sum(1 for c in items if c["id"].startswith("uc-"))} US closure entries')


def main():
    if '--merge' in sys.argv:
        merge(); return
    K = _key()
    try: was = json.load(open(OUT, encoding='utf-8'))
    except Exception: was = {}  # noqa: E722
    old = {}
    for it in was.get('items', []): old.setdefault(it['src'], []).append(it)
    first = {it['id']: it.get('seen') for it in was.get('items', [])}
    items, srcs, lines = [], {}, []
    for sid, st, agency, page, fn in SOURCES:
        try:
            rows = fn()
        except Exception as e:  # noqa: BLE001
            srcs[sid] = {'agency': agency, 'st': st, 'page': page, 'ok': False, 'why': str(e)[:160], **source_clock((was.get('sources') or {}).get(sid), False, None)}
            items += old.get(sid, [])                  # keep the last list: a failed read is not a reopening
            lines.append(f'{sid}: NOT READ ({str(e)[:80]}), kept {len(old.get(sid, []))}')
            continue
        parks = park_list(st)
        n, nomatch, prev = 0, [], []
        for r in rows:
            refs = match(K, r, parks, st)
            if not refs:
                nomatch.append(str(r.get('name') or r.get('title'))[:40]); continue
            exp = r['end'] if r.get('end') and r['end'] >= TODAY else TODAY + dt.timedelta(days=3)
            det = f"{agency}: {r['title']}" + (f" — {r['text']}" if r.get('text') and r['text'] != r['title'] else '')
            if r.get('end'): det += f" (until {r['end'].strftime('%b %-d')})"
            kind = r.get('kind') or ('Closure' if re.search(r'clos|restrict', r['title'] + ' ' + r['text'], re.I) else 'Park notice')
            if sid == 'ga-wrd' and not GA_LIVE:              # preview only: record what WOULD show, put nothing on cards
                prev.append({'refs': refs, 'kind': kind, 'details': det[:400], 'expires': exp.isoformat()}); n += 1; continue
            for ref in refs:
                key = re.sub(r'[^a-z0-9]+', '-', (r['title'] + ' ' + r['text'])[:60].lower()).strip('-')
                iid = f'uc-{sid}-{key}-{ref}'
                items.append({'id': iid, 'src': sid, 'ref': ref, 'kind': kind, 'details': det[:400],
                              'seen': first.get(iid) or (r.get('date') or TODAY).isoformat(), 'call': 'KPC BOT',
                              'expires': exp.isoformat(), 'link': r.get('link') or page})
                n += 1
        srcs[sid] = {'agency': agency, 'st': st, 'page': page, 'ok': True, 'rows': len(rows), 'n': n,
                     'unmatched': nomatch[:15], **({'preview': prev} if prev else {}),
                     **source_clock((was.get('sources') or {}).get(sid), True, n)}
        lines.append(f'{sid}: {len(rows)} notices, {n} park entries' + (f'; no park for: {"; ".join(nomatch[:6])}' if nomatch else ''))
    seen_ids, uniq = set(), []
    for it in sorted(items, key=lambda x: x['id']):
        if it['id'] not in seen_ids: seen_ids.add(it['id']); uniq.append(it)
    save_json(OUT, {'about': 'US state agency closures tied to POTA parks; built by .github/scripts/kpc_us_closures.py '
                             'from the agencies\' own feeds (chat 2). Shown everywhere through kpc-conditions.json (uc- ids).',
                    'sources': srcs, 'items': uniq}, indent=1)
    merge()
    for l in lines: notice('US closures', l)
    notice('US closures', f'{len(uniq)} park entries from {sum(1 for s in srcs.values() if s["ok"])} of {len(SOURCES)} sources')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:  # noqa: BLE001
        notice('US closures', f'stopped: {e}')
    sys.exit(0)
