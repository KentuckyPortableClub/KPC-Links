"""Builds kpc-events-auto.json for events.html.

1. Recurring events worked out by rule (POTA Support Your Parks, ARRL Field Day, Winter Field Day).
2. Kentucky hamfests found in the ARRL hamfest database.
3. Kentucky SOTA events posted on the SOTA Reflector (like the yearly SOTA Kentucky Campout).
4. Events members sent in on the KPC Reports form (kpc-events-submitted.json, written by kpc_reports.py),
   added to "found" with source MEMBER so every page, Discord and Facebook post that reads this file shows them.

Anything found automatically is labelled on the page so people confirm details with the organizer.
If a source can't be reached, the last good results for that source are kept.
"""
import datetime as dt
import html
import json
import pathlib
import re
import sys
import time
import urllib.parse
import urllib.request

OUT = pathlib.Path('kpc-events-auto.json')
UA = 'Mozilla/5.0 (compatible; KPC-events-bot; +https://kentuckyportableclub.github.io/KPC-Links/events.html)'
TODAY = dt.date.today()
HORIZON = TODAY + dt.timedelta(days=430)
MONTHS = {m: i for i, m in enumerate(['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'], 1)}


def log(*a):
    print(*a, flush=True)


def notice(title, msg):
    """Shows up as an annotation on the workflow run (handy for checking what a source returned)."""
    print('::notice title=%s::%s' % (title, str(msg).replace('%', '%25').replace('\r', '').replace('\n', '%0A')), flush=True)


def get(url, data=None, tries=3):
    last = None
    for i in range(tries):
        try:
            body = urllib.parse.urlencode(data).encode() if data is not None else None
            req = urllib.request.Request(url, data=body, headers={'User-Agent': UA, 'Accept-Language': 'en-US'})
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read().decode('utf-8', 'replace'), r.geturl()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(4 * (i + 1))
    raise last


def text_of(h):
    h = re.sub(r'(?is)<(script|style)\b.*?</\1>', ' ', h)
    h = re.sub(r'(?i)<br\s*/?>|</(p|div|li|tr|h\d)>', '\n', h)
    h = re.sub(r'<[^>]+>', ' ', h)
    h = html.unescape(h)
    return re.sub(r'[ \t\r\f\v]+', ' ', re.sub(r'\n\s*\n+', '\n', h)).strip()


def iso(d):
    return d.isoformat()


# ------------------------------------------------------------------ 1. recurring, by rule
def full_weekends(y, m):
    out = []
    d = dt.date(y, m, 1)
    while d.month == m:
        if d.weekday() == 5 and (d + dt.timedelta(days=1)).month == m:
            out.append(d)
        d += dt.timedelta(days=1)
    return out


def recurring():
    ev = []
    for y in (TODAY.year, TODAY.year + 1, TODAY.year + 2):
        for m in (1, 4, 7, 10):
            s = full_weekends(y, m)[2]
            ev.append({'name': 'POTA Support Your Parks Weekend', 'tags': ['POTA'], 'start': iso(s), 'end': iso(s + dt.timedelta(days=1)),
                       'where': 'Any Kentucky park. Get out and activate!', 'by': 'Parks on the Air', 'url': 'https://pota.app/', 'rule': 'Third full weekend of Jan, Apr, Jul and Oct'})
        s = full_weekends(y, 6)[3]
        ev.append({'name': 'ARRL Field Day', 'tags': ['ONAIR'], 'start': iso(s), 'end': iso(s + dt.timedelta(days=1)),
                   'time': 'Starts 1800 UTC Saturday (2 PM Eastern)', 'where': 'Clubs and portable stations everywhere. A great weekend to operate from a park.',
                   'by': 'ARRL', 'url': 'https://www.arrl.org/field-day', 'rule': 'Fourth full weekend of June'})
        s = full_weekends(y, 1)[-1]
        ev.append({'name': 'Winter Field Day', 'tags': ['ONAIR'], 'start': iso(s), 'end': iso(s + dt.timedelta(days=1)),
                   'where': 'Portable and home stations. Cold-weather field operating.', 'by': 'Winter Field Day Association', 'url': 'https://winterfieldday.org/', 'rule': 'Last full weekend of January'})
    return [e for e in ev if TODAY <= dt.date.fromisoformat(e['end']) and dt.date.fromisoformat(e['start']) <= HORIZON]


# ------------------------------------------------------------------ 2. ARRL hamfest database (Kentucky)
def parse_dates(t):
    """Find the first date or date range in text. Returns (start, end) dates or (None, None)."""
    m = re.search(r'(\d{1,2})/(\d{1,2})/(\d{4})(?:\s*(?:-|–|to|thru|through)\s*(\d{1,2})/(\d{1,2})/(\d{4}))?', t)
    if m:
        s = dt.date(int(m[3]), int(m[1]), int(m[2]))
        e = dt.date(int(m[6]), int(m[4]), int(m[5])) if m[4] else s
        return s, e
    m = re.search(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+(\d{1,2})(?:\s*(?:-|–|to)\s*(?:(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+)?(\d{1,2}))?,?\s+(\d{4})', t, re.I)
    if m:
        y = int(m[5])
        sm = MONTHS[m[1][:3].lower()]
        s = dt.date(y, sm, int(m[2]))
        em = MONTHS[m[3][:3].lower()] if m[3] else sm
        e = dt.date(y, em, int(m[4])) if m[4] else s
        return s, e
    return None, None


def arrl_hamfests():
    base = 'https://www.arrl.org/hamfests-and-conventions-calendar'
    page, url = get(base)
    forms = re.findall(r'(?is)<form\b[^>]*>.*?</form>', page)
    form = next((f for f in forms if re.search(r'(?i)name="[^"]*state[^"]*"', f)), None)
    links = set()
    if form:
        action = html.unescape(re.search(r'(?i)action="([^"]*)"', form).group(1)) if re.search(r'(?i)action="([^"]*)"', form) else url
        method = (re.search(r'(?i)method="([^"]*)"', form) or [None, 'get'])[1].lower()
        fields = {}
        for inp in re.findall(r'(?is)<input\b[^>]*>', form):
            n = re.search(r'(?i)name="([^"]*)"', inp)
            if not n:
                continue
            typ = (re.search(r'(?i)type="([^"]*)"', inp) or [None, 'text'])[1].lower()
            if typ in ('checkbox', 'radio') and 'checked' not in inp.lower():
                continue
            v = re.search(r'(?i)value="([^"]*)"', inp)
            fields[n.group(1)] = html.unescape(v.group(1)) if v else ''
        for sel in re.findall(r'(?is)<select\b.*?</select>', form):
            n = re.search(r'(?i)name="([^"]*)"', sel).group(1)
            opts = re.findall(r'(?is)<option\b[^>]*value="([^"]*)"[^>]*>(.*?)</option>', sel)
            if 'state' in n.lower():
                pick = next((v for v, t in opts if text_of(t).strip().lower() in ('kentucky', 'ky')), None)
                fields[n] = pick or 'KY'
                log('ARRL: state field', n, '=', fields[n])
            else:
                fields.setdefault(n, '')
        target = urllib.parse.urljoin(url, action)
        log('ARRL: submitting', method.upper(), target, {k: v for k, v in fields.items() if v})
        if method == 'post':
            res, _ = get(target, data=fields)
        else:
            res, _ = get(target + ('&' if '?' in target else '?') + urllib.parse.urlencode(fields))
        links |= set(re.findall(r'href="((?:https?://www\.arrl\.org)?/hamfests/[a-z0-9\-]+)"', res))
    else:
        log('ARRL: search form not found; scanning page links only')
    out, samples = [], []
    for href in sorted(links)[:60]:
        full = urllib.parse.urljoin('https://www.arrl.org/', href)
        try:
            d, _ = get(full)
        except Exception as e:  # noqa: BLE001
            log('ARRL: could not read', full, e)
            continue
        body = re.sub(r'(?is)<(select|form|nav|header|footer)\b.*?</\1>', ' ', d)
        t = text_of(body)
        if not samples:
            samples.append(t[:900])
        if not re.search(r'\bKentucky\b|,\s*KY\b', t):
            continue
        lines = [x.strip() for x in t.split('\n') if x.strip()]
        title = ''
        for i, x in enumerate(lines):
            if x.upper().startswith('HAMFEST/CONVENTION') or x.upper() == 'CONVENTION' or x.upper() == 'HAMFEST':
                title = lines[i - 1] if i else ''
                break
        if not title:
            title = href.rsplit('/', 1)[-1].replace('-', ' ').title()
            title = re.sub(r'\s+\d+$', '', title)

        def label(name):
            m = re.search(r'(?im)^\s*' + name + r'\s*:\s*(.*)$', t)
            return m.group(1).strip() if m else ''
        sd, ed = label('Start Date'), label('End Date')
        s, e = parse_dates(sd + (' - ' + ed if ed and ed != sd else '')) if sd else parse_dates(t)
        if not s or e < TODAY or s > HORIZON:
            continue
        where = ''
        m = re.search(r'(?is)Location:\s*(.*?)\n\s*(?:Website|Sponsor|Type|Talk-In|Public Contact)\s*:', t)
        if m:
            where = ', '.join(x.strip() for x in m.group(1).split('\n') if x.strip())
        if not re.search(r'\bKY\b|Kentucky', where or t):
            continue
        site = re.search(r'(?is)Website:\s*(https?://\S+)', t)
        sponsor = label('Sponsor')
        talk = label('Talk-In')
        ev = {'name': title, 'tags': ['HAMFEST', 'AUTO'], 'start': iso(s), 'end': iso(e) if e != s else None,
              'where': where or 'Kentucky', 'by': (sponsor or 'See the listing') + ' (from the ARRL hamfest database)',
              'url': site.group(1) if site else full, 'source': 'ARRL'}
        if site:
            ev['url2'] = full
            ev['url2label'] = 'ARRL LISTING ↗'
        if talk:
            ev['time'] = 'Talk-in: ' + talk
        out.append(ev)
        log('ARRL: found', title, s, e)
        notice('ARRL found', '%s | %s | %s' % (title, s, out[-1]['where']))
    return out


# ------------------------------------------------------------------ 3. SOTA Reflector (Discourse)
def sota_reflector():
    base = 'https://reflector.sota.org.uk'
    cats = {}
    try:
        cj = json.loads(get(base + '/categories.json')[0])
        cats = {c['id']: c['name'] for c in cj.get('category_list', {}).get('categories', [])}
    except Exception as e:  # noqa: BLE001
        log('SOTA: categories unavailable', e)
    seen, out = set(), []
    for q in ('kentucky', 'W4K', 'kentucky campout'):
        try:
            j = json.loads(get(base + '/search.json?' + urllib.parse.urlencode({'q': q + ' order:latest'}))[0])
        except Exception as e:  # noqa: BLE001
            log('SOTA: search failed', q, e)
            continue
        for tpc in j.get('topics', []):
            if tpc['id'] in seen:
                continue
            seen.add(tpc['id'])
            title = tpc.get('title', '')
            created = dt.date.fromisoformat(tpc.get('created_at', '1970-01-01')[:10])
            cat = cats.get(tpc.get('category_id'), '')
            eventish = cat.lower().startswith('event') or re.search(r'(?i)campout|workshop|meet[- ]?up|gathering|activity (day|weekend)|hamfest|presentation', title)
            kentucky = re.search(r'(?i)kentucky|\bW4K\b|\bKY\b', title)
            if not (eventish and kentucky) or (TODAY - created).days > 330:
                continue
            s, e = parse_dates(title)
            ev = {'name': title, 'tags': ['SOTA', 'AUTO'], 'where': 'See the announcement', 'by': 'Posted on the SOTA Reflector',
                  'url': f"{base}/t/{tpc.get('slug', 'topic')}/{tpc['id']}", 'source': 'SOTA', 'posted': iso(created)}
            if s and e >= TODAY:
                ev.update({'start': iso(s), 'end': iso(e) if e != s else None})
            else:
                ev.update({'tba': True, 'when': 'Posted ' + created.strftime('%b %d, %Y') + '. See the announcement for dates.'})
            out.append(ev)
            log('SOTA: found', title, cat, created)
    return out


def member_events():
    """Upcoming events from kpc-events-submitted.json (approved KPC Reports form rows)."""
    try:
        evs = json.loads(pathlib.Path('kpc-events-submitted.json').read_text(encoding='utf-8')).get('events', [])
    except Exception:  # noqa: BLE001
        return []
    return [e for e in evs if isinstance(e, dict) and e.get('name') and e.get('start') and dt.date.fromisoformat(e.get('end') or e['start']) >= TODAY]


def main():
    try:
        old = json.loads(OUT.read_text(encoding='utf-8'))
    except Exception:  # noqa: BLE001
        old = {}
    prev_found = old.get('found', [])
    found, status = [], {}
    for name, fn in (('ARRL', arrl_hamfests), ('SOTA', sota_reflector)):
        try:
            got = fn()
            found += got
            status[name] = 'ok (%d)' % len(got)
        except Exception as e:  # noqa: BLE001
            keep = [f for f in prev_found if f.get('source') == name]
            found += keep
            status[name] = 'failed, kept %d from last run: %s' % (len(keep), e)
            log(name, 'FAILED:', e)
    def nn(s):
        return re.sub(r'[^a-z0-9]+', ' ', str(s).lower()).strip()
    rec = recurring()
    have = {(nn(e.get('name')), e.get('start')) for e in rec + found}
    mem = [dict(e, source='MEMBER') for e in member_events() if (nn(e['name']), e['start']) not in have]
    found += mem
    status['MEMBER'] = 'ok (%d)' % len(mem)
    for f in found:
        if f.get('end') is None:
            f.pop('end', None)
    data = {'recurring': rec, 'found': found, 'status': status}
    if {k: v for k, v in old.items() if k != 'updated'} == data:
        log('No changes')
        notice('Events finder', 'no changes ' + json.dumps(status))
        return
    data = {'updated': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), **data}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    log('Saved', OUT, status)
    notice('Events finder', json.dumps(status))


if __name__ == '__main__':
    sys.exit(main())
