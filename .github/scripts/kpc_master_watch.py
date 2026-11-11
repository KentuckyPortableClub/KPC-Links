#!/usr/bin/env python3
"""kpc_master_watch.py (Nov 10): ask a person only when a download source looks CHANGED.

data/outlines/download-sources.json holds one entry per official download source (the Nov 10 hand-filled layer list), with the
last-seen FINGERPRINT: the file size, Last-Modified, ETag, the catalog's stated date or version, and the record count where stated.

  watch   a low-cost change check, allowed requests only: kpc_master.live_ok first (never a services*.arcgis.com host, never the
          never-contact hosts, nothing on the saved-copy-only list), then robots.txt (a 403 = no), 2 s per host, 60 s on hub portals.
          A HEAD of the direct file, or the catalog's own metadata (ScienceBase item JSON). Nothing is downloaded.
          A source a bot may not even check is check=person: it is NOT asked every run; once downloaded it goes on a rare
          reminder list instead (the PC helper's --reminders: done check=person rows older than REMIND_DAYS days).
          A changed fingerprint reopens the done needs-download rows of that source (source 'change check').
  seed    build download-sources.json (and needs-download rows) from the filled CSV. The CSV's licence notes are NOT copied
          into any public file: every entry only carries terms='see the source page'.
"""
import csv, datetime, json, os, pathlib, re, sys, urllib.error, urllib.parse, urllib.request
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kpc_master as M  # noqa: E402

FORMAT = 1
REMIND_DAYS = 90
FP_KEYS = ('size', 'last_modified', 'etag', 'version', 'count')
PADUS_ITEM = '6759abcfd34edfeb8710a004'   # USGS PAD-US 4.1 on ScienceBase (a fallback, not first-party)
CPCAD_ID = '6c343726'                      # ECCC CPCAD on open.canada.ca (a fallback, not first-party)
ABOUT = ('Official download sources for the saved copies, with the last-seen fingerprint (size, Last-Modified, ETag, stated '
         'date or version, record count). kind: first-party / fallback (PAD-US or CPCAD only) / none (no official download '
         'found yet). check: bot = a bot may check it for a change (allowed host, robots.txt permitting); person = a person '
         'checks it on the rare reminder list. Terms: see each source page.')


def today(): return datetime.date.today().isoformat()


def _areas(a):
    out = []
    for t in [x.strip() for x in str(a or '').split(';') if x.strip()]:
        out.append(t if t.startswith(('US', 'CA')) else 'W-' + t.upper())
    return out


def _layer(row):
    lid = str(row.get('layer_id') or '').split(';')[0].strip()
    if lid.startswith('ca:'): lid = ''
    return lid or f"h{int(row.get('row_id')):03d}"


def kind_of(row):
    page = row.get('official_download_page_url') or ''
    if not page and not row.get('direct_file_url'): return 'none'
    if PADUS_ITEM in page or CPCAD_ID in page: return 'fallback'
    return 'first-party'


def check_of(page, file_url):
    """'bot' when a bot may (by the host rules) ask the file for a HEAD or the catalog for its metadata; robots.txt is asked at run time."""
    if file_url and M.live_ok(file_url)[0]: return 'bot'
    if page and catalog_url(page) and M.live_ok(catalog_url(page))[0]: return 'bot'
    return 'person'


def catalog_url(page):
    m = re.search(r'https://www\.sciencebase\.gov/catalog/item/([0-9a-f]{24})', str(page or ''))
    return f'https://www.sciencebase.gov/catalog/item/{m.group(1)}?format=json' if m else None


def _tokens(row, by_url=None):
    """The row's layer ids. A 'ca:' token keeps its trailing spaces (a CA layer id is the first 12 letters of the label, spaces and all).
    A row with no layer id gets the US key's prefix for its layer address (by_url, from data/us-key/layers.json) when there is one."""
    out = [t.lstrip() for t in str(row.get('layer_id') or '').split(';') if t.strip()]
    out = [t if t.startswith('ca:') else t.strip() for t in out]
    if by_url:
        u = re.sub(r'/query/?$', '', str(row.get('current_source_url') or '').split('?')[0]).rstrip('/').lower()
        if u in by_url and by_url[u] not in out: out.append(by_url[u])
    return out


# the US key's national layers that are written in its code rather than in data/us-key/layers.json
US_BUILTIN = {'https://services.arcgis.com/qvengdapbd4lukLV/arcgis/rest/services/fwsinterest_simplified_authoritative/featureserver/0'.lower(): 'fws'}


def us_prefix_by_url(us_layers):
    """{layer address (lower case, no /query): US key prefix} from data/us-key/layers.json (prefix -> [url, ...])."""
    out = dict(US_BUILTIN)
    for k, v in ((M.load_json(us_layers, {}) or {}) if us_layers else {}).items():
        if isinstance(v, list) and v and isinstance(v[0], str):
            out.setdefault(re.sub(r'/query/?$', '', v[0].replace('svc:', '', 1).split('|')[0].split('?')[0]).rstrip('/').lower(), k)
    return out


def copy_count(area, row, copies, same_as=None, by_url=None, _memo={}):
    """Nov 10: how many records of this CSV row's layer the saved copy of this area already holds (0 = none, None = no copy).
    US-XX: any layer_id token as the OBJECTID prefix of US-XX.json.gz; 'US' (national): summed over every US copy.
    CA / CA-XX: the 'ca:' token (the first 12 letters of the source label, '~N') or the source label in CA-ALL.json.gz.
    W-XX: the source label (layer_name) in W-XX.json.gz, or its equivalent in same_as {area: {csv label: copy label}} (box-side)."""
    if not copies: return None
    d = pathlib.Path(copies)
    def counts(name):
        p = d / name
        if not p.exists(): return None
        k = (str(p), p.stat().st_mtime)
        if k not in _memo: _memo[k] = M.saved_counts(p)
        return _memo[k]
    toks = _tokens(row, by_url); label = (row.get('layer_name') or '').strip()
    if area.startswith('US'):
        names = [f'{area}.json.gz'] if area.startswith('US-') else sorted(p.name for p in d.glob('US-*.json.gz') if not p.name.startswith('prev-'))
        tot, seen = 0, False
        for nm in names:
            c = counts(nm)
            if c is None: continue
            seen = True; tot += max([c.get(t, 0) for t in toks if not t.startswith('ca:')] or [0])
        return tot if seen else None
    if area.startswith('CA'):
        c = counts('CA-ALL.json.gz')
        if c is None: return None
        ca = [t[3:] for t in toks if t.startswith('ca:')]
        n_id = [v for kk, v in c.items() if not kk.startswith('src:') and any(kk == t or (len(t.rstrip()) >= 6 and kk.rstrip() == t.rstrip()) for t in ca)]
        return max(n_id + [c.get('src:' + label, 0)] + [c.get('src:' + t, 0) for t in toks if not t.startswith('ca:')])
    c = counts(f'{area}.json.gz')
    if c is None: return None
    alt = ((same_as or {}).get(area) or {}).get(label)
    return max(c.get('src:' + label, 0), c.get('src:' + alt, 0) if alt else 0)


def seed(csv_path, sources_path, needs_rows_out=None, copies=None, same_as=None, us_layers=None):
    """CSV -> download-sources.json (+ needs rows). Only facts go public: no licence text, no finder notes.
    Nov 10: a row whose layer the saved copy of that area already holds (copies = a folder of the boundary-cache copies: US-XX,
    CA-ALL, W-XX) is DONE (have = the records held), whatever its source kind: a change at the source reopens it. A row whose
    official direct file a bot may fetch is a bot's (kpc_master.who_for with the file), not a person's."""
    rows = list(csv.DictReader(open(csv_path, encoding='utf-8-sig', newline='')))
    old = M.load_json(sources_path, {}) or {}
    src = dict(old.get('sources') or {})
    needs, by_url = [], us_prefix_by_url(us_layers)
    for r in rows:
        sid = f"h{int(r['row_id']):03d}"
        page, f = (r.get('official_download_page_url') or '').strip(), (r.get('direct_file_url') or '').strip()
        k = kind_of(r)
        never = r.get('host_rule') == 'never-contact'
        e = dict(src.get(sid) or {})
        e.update({'areas': _areas(r.get('area')), 'layer': _layer(r), 'name': (r.get('layer_name') or '')[:120], 'layer_url': r.get('current_source_url') or '',
                  'page': page, 'file': f, 'format': (r.get('file_format') or '')[:80], 'stated_count': r.get('stated_record_count') or None,
                  'version': (r.get('date_or_version') or '')[:120], 'kind': k, 'check': check_of(page, f), 'terms': 'see the source page'})
        e.setdefault('fp', {}); e.setdefault('fp_seen', None); e.setdefault('changed', None)
        # The CSV's stated date / count stay in 'version' / 'stated_count' (free text): the fingerprint 'fp' is only ever what a
        # check READ (the first check sets the baseline, so it never asks a person; only a later difference does).
        src[sid] = e
        for area in e['areas']:
            have = copy_count(area, r, copies, same_as, by_url)
            # the CSV's layers are saved-copy only, so the layer itself is never a bot's; its official direct file may be (same host rules)
            who = 'never' if never else ('bot' if f and M.live_ok(f)[0] else 'person')
            st, why = 'open', 'an official download exists for a layer a bot may not read (saved copies only)'
            if never: why = 'never contacted (no request of any kind); a first-party download elsewhere is still to be found'
            elif have: st, why = 'done', f'the saved copy already holds this layer ({have} records); a change at the source reopens it'
            elif k == 'fallback': st, why = 'held', 'fallback only (PAD-US or CPCAD, which the keys already read): no first-party download found yet'
            elif k == 'none': st, why = 'held', 'no official download found yet (needs research)'
            elif who == 'bot': why = 'an official direct file a bot may fetch exists for a layer a bot may not read: the fresh-start run downloads it'
            needs.append({**M.needs_row(area, e['layer'], e['layer_url'], why, 'hand-filled list (Nov 10)', who=who, page=page or None, have=have or None,
                                        note=('direct file: ' + f) if f else '', src=sid, check=e['check']), 'status': st})
    doc = {'format': FORMAT, 'about': ABOUT, 'sources': {k: src[k] for k in sorted(src)}}
    pathlib.Path(sources_path).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(sources_path).write_text(json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')
    if needs_rows_out: pathlib.Path(needs_rows_out).write_text(json.dumps({'format': M.NEEDS_FORMAT, 'rows': needs}, indent=1, sort_keys=True), encoding='utf-8')
    return doc, needs


def http_fetcher(offline=False):
    """head(url) -> (status, headers) and getj(url) -> json, only after live_ok and robots.txt say yes."""
    pacer = M.Pacer(); rcache = {}

    def raw(u, method='GET', limit=2_000_000):
        ok, why = M.live_ok(u)
        if not ok: raise M.LiveNotAllowed(why)
        pacer.wait(M.parts(u)[0])
        req = urllib.request.Request(u, method=method, headers={'User-Agent': M.UA})
        try:
            with M.host_checked_opener().open(req, timeout=30) as r: return r.status, {k.lower(): v for k, v in r.headers.items()}, (r.read(limit) if method == 'GET' else b'')
        except urllib.error.HTTPError as e: return e.code, {k.lower(): v for k, v in (e.headers or {}).items()}, b''

    def robots(u):
        def get(x):
            st, _, body = raw(x)
            return st, body.decode('utf-8', 'replace')
        return M.robots_allows(u, get, rcache)

    def head(u):
        if not robots(u): return 'robots', {}
        st, h, _ = raw(u, 'HEAD')
        return st, h

    def getj(u):
        if not robots(u): return None
        st, _, body = raw(u)
        if st != 200: return None
        try: return json.loads(body.decode('utf-8', 'replace'))
        except ValueError: return None
    return head, getj


def fingerprint(e, head, getj):
    """-> (fp dict or None, how). None = could not check this run (the old fingerprint stays)."""
    fp = {}
    if e.get('file') and M.live_ok(e['file'])[0]:
        st, h = head(e['file'])
        if st == 'robots': return None, 'robots.txt says no'
        if st != 200: return None, f'HEAD answered {st}'
        fp.update({'size': h.get('content-length'), 'last_modified': h.get('last-modified'), 'etag': h.get('etag')})
    cu = catalog_url(e.get('page'))
    if cu and M.live_ok(cu)[0]:
        j = getj(cu)
        if j:
            dates = {d.get('type'): d.get('dateString') for d in j.get('dates') or [] if isinstance(d, dict)}
            prov = j.get('provenance') or {}
            fp['version'] = prov.get('lastUpdated') or dates.get('Revision') or dates.get('Publication') or fp.get('version')
            sizes = [f.get('size') for f in j.get('files') or [] if isinstance(f, dict) and f.get('size')]
            if sizes and not fp.get('size'): fp['size'] = str(sum(int(x) for x in sizes))
    fp = {k: v for k, v in fp.items() if v not in (None, '')}
    return (fp or None), ('checked' if fp else 'nothing to compare')


def changed(old, new):
    """A field both fingerprints have, with a different value. A field only one side has is not a change (a server that stops
    sending ETag is not a new file)."""
    return any(old.get(k) not in (None, '') and new.get(k) not in (None, '') and str(old[k]) != str(new[k]) for k in FP_KEYS)


def _days_since(e, date):
    """Days since this source was last tried (fp_seen or the date in last_check); None = never."""
    seen = [str(x)[:10] for x in (e.get('fp_seen'), e.get('last_check')) if x]
    try: return min((datetime.date.fromisoformat(date) - datetime.date.fromisoformat(d)).days for d in seen) if seen else None
    except ValueError: return None


def watch(sources_path, needs_path=None, offline=False, head=None, getj=None, date=None, min_days=0):
    """Check every check=bot source; reopen the done needs rows of a changed source. Returns a summary dict. A source tried less than
    min_days ago is not asked again this run (owner rule, 2026-11-10); the file is written only when something in it changed."""
    date = date or today()
    doc = M.load_json(sources_path, {}) or {}
    before = json.dumps(doc, sort_keys=True)
    src = doc.get('sources') or {}
    if not offline and (head is None or getj is None): head, getj = http_fetcher()
    out = {'checked': 0, 'changed': [], 'not_checked': 0, 'person': 0}
    if head is not None:   # one request per URL per run (many layers share one PAD-US / CPCAD item)
        _h, _g, hc, gc = head, getj, {}, {}
        head = lambda u: hc[u] if u in hc else hc.setdefault(u, _h(u))   # noqa: E731
        getj = lambda u: gc[u] if u in gc else gc.setdefault(u, _g(u))   # noqa: E731
    for sid, e in sorted(src.items()):
        if e.get('check') != 'bot' or e.get('kind') == 'none':
            out['person'] += 1   # not asked every run: the PC helper's --reminders lists these rows every REMIND_DAYS days
            continue
        if offline: out['not_checked'] += 1; continue
        ds = _days_since(e, date)
        if min_days and ds is not None and 0 <= ds < min_days: out['recent'] = out.get('recent', 0) + 1; continue
        try: fp, how = fingerprint(e, head, getj)
        except Exception as ex: fp, how = None, f'{type(ex).__name__}'  # noqa: BLE001
        if fp is None: out['not_checked'] += 1; e['last_check'] = f'{date}: {how}'; continue
        out['checked'] += 1
        old = e.get('fp') or {}
        if old and changed(old, fp):
            e['fp_prev'] = old; e['changed'] = date; out['changed'].append(sid)
        e['fp'] = {**old, **fp}; e['fp_seen'] = date; e['last_check'] = f'{date}: {how}'
    doc['sources'] = src
    if json.dumps(doc, sort_keys=True) != before: pathlib.Path(sources_path).write_text(json.dumps(doc, indent=1, sort_keys=True, ensure_ascii=False) + '\n', encoding='utf-8')
    if needs_path and out['changed']:
        nd = M.load_needs(needs_path)
        nd, add, upd = M.merge_needs(nd, change_rows(src, out['changed'], date)); M.save_needs(nd, needs_path); out['reopened'] = add + upd
    return out


WHY_CHANGED = 'the official download looks CHANGED since it was last seen (size / date / version): download it again'


def change_rows(src, sids, date):
    """One open row per area of each changed source (source 'change check'). Merged into the ONE list, it reopens a done row
    (it is newer) and a held row (the change check is the one thing that reopens a held row)."""
    rows = []
    for sid in sids:
        e = src[sid]
        if e.get('kind') != 'first-party': continue   # a fallback (PAD-US / CPCAD) is read by the keys themselves: nothing to ask
        for area in e.get('areas') or []:
            rows.append(M.needs_row(area, e.get('layer'), e.get('layer_url') or '', WHY_CHANGED, 'change check', who='person', page=e.get('page') or None,
                                    date=date, note=('direct file: ' + e['file']) if e.get('file') else '', src=sid, check=e.get('check') or ''))
    return rows


def link_rows(sources_path, rows):
    """Give needs rows from the bots / the master step the src of the hand-filled source for the same layer and area."""
    src = (M.load_json(sources_path, {}) or {}).get('sources') or {}
    by = {}
    for sid, e in src.items():
        for a in e.get('areas') or []: by.setdefault((a, e.get('layer')), sid)
        if 'US' in (e.get('areas') or []): by.setdefault(('US*', e.get('layer')), sid)
    for r in rows:
        if r.get('src'): continue
        sid = by.get((r.get('area'), r.get('layer'))) or (by.get(('US*', r.get('layer'))) if str(r.get('area', '')).startswith('US-') else None)
        if sid:
            e = src[sid]; r['src'] = sid; r['check'] = e.get('check') or ''
            if e.get('page') and e.get('kind') == 'first-party': r['page'] = e['page']
            if e.get('file') and e.get('kind') == 'first-party' and 'direct file' not in (r.get('note') or ''): r['note'] = ((r.get('note') or '') + ' direct file: ' + e['file']).strip()
    return rows
