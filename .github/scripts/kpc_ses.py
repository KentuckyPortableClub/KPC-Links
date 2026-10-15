#!/usr/bin/env python3
"""KPC special event stations.

Reads the ARRL Special Event Stations listing (every station that registered with ARRL) for the next
HORIZON days and saves kpc-special-events.json, which the Events page calendar and the Live page spot filter read.
Also works out the dates of the big yearly on-the-air events (13 Colonies, Museum Ships Weekend, ...).
Runs every day from .github/workflows/kpc-ses.yml (or by hand from the Actions tab).
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

UA = 'Mozilla/5.0 (compatible; KPC-Links special event finder; +https://kentuckyportableclub.github.io/KPC-Links/)'
OUT = pathlib.Path('kpc-special-events.json')
TODAY = dt.datetime.now(dt.timezone.utc).date()
HORIZON = 75
MONTHS = {m: i for i, m in enumerate(['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'], 1)}
STATES = set('AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY PR VI GU'.split())
PROV = set('AB BC MB NB NL NS NT NU ON PE QC SK YT'.split())
CALL = re.compile(r'\b(?:[A-Z]{1,2}\d{1,2}[A-Z]{1,4}|\d[A-Z]\d[A-Z]{1,3})(?:/\d|/[A-Z]{1,2}\d?)?\b')


def log(*a):
    print(*a, flush=True)


def notice(title, msg):
    print('::notice title=%s::%s' % (title, str(msg).replace('%', '%25').replace('\r', '').replace('\n', '%0A')), flush=True)


def get(url, data=None, tries=3):
    last = None
    for i in range(tries):
        try:
            body = urllib.parse.urlencode(data).encode() if data is not None else None
            req = urllib.request.Request(url, data=body, headers={'User-Agent': UA, 'Accept-Language': 'en-US'})
            with urllib.request.urlopen(req, timeout=40) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(4 * (i + 1))
    raise last


def text_of(h):
    h = re.sub(r'(?is)<(script|style)\b.*?</\1>', ' ', h)
    h = re.sub(r'<[^>]+>', ' ', h)
    return re.sub(r'\s+', ' ', html.unescape(h)).strip()


def year_for(mon, ref):
    """Year for a month that appears near the listing's start date (handles Dec -> Jan)."""
    y = ref.year
    if mon < ref.month - 6:
        y += 1
    elif mon > ref.month + 6:
        y -= 1
    return y


def parse_when(s, listed):
    """'Oct 8-Oct 16, 0000Z-2359Z' / 'Oct 17, 1400Z-2000Z' / 'Dec 31-Jan 2' -> (start, end, times)."""
    m = re.match(r'\s*([A-Za-z]{3})[a-z]*\.?\s*(\d{1,2})(?:\s*-\s*(?:([A-Za-z]{3})[a-z]*\.?\s*)?(\d{1,2}))?', s)
    if not m:
        return listed, listed, ''
    m1 = MONTHS.get(m.group(1).lower()[:3])
    if not m1:
        return listed, listed, ''
    d1 = int(m.group(2))
    start = dt.date(year_for(m1, listed), m1, d1)
    end = start
    if m.group(4):
        m2 = MONTHS.get((m.group(3) or m.group(1)).lower()[:3]) or m1
        end = dt.date(year_for(m2, start), m2, int(m.group(4)))
        if end < start:
            end = dt.date(end.year + 1, end.month, end.day)
    t = re.search(r'(\d{4}Z\s*-\s*\d{4}Z)', s)
    return start, end, (t.group(1).replace(' ', '') if t else '')


def arrl():
    start, end = TODAY - dt.timedelta(days=21), TODAY + dt.timedelta(days=HORIZON)
    path = '/special_events/search/page:%d/Date.start:' + start.isoformat() + '/Date.end:' + end.isoformat() + '/model:Event'
    out, seen = [], set()
    for page in range(1, 40):
        h = get('https://www.arrl.org' + (path % page))
        items = re.findall(r'(?is)<li>\s*<h3>\s*<span>\s*(\d{2})/(\d{2})/(\d{4})\s*\|\s*</span>(.*?)</h3>\s*<p>(.*?)</p>\s*</li>', h)
        if not items:
            break
        for mo, da, yr, title, body in items:
            listed = dt.date(int(yr), int(mo), int(da))
            title = text_of(title)
            bm = re.search(r'(?is)<b>(.*?)</b>', body)
            head = text_of(bm.group(1)) if bm else ''
            links = re.findall(r'(?is)href="([^"]+)"', body)
            url = next((u for u in links if re.match(r'https?://\S+\.\S+', u) and u not in ('http://', 'https://')), '')
            rest = text_of(re.sub(r'(?is)<a\b.*?</a>', '', re.sub(r'(?is)<b>.*?</b>', '', body, count=1)))
            s, e, times = parse_when(head, listed)
            hp = [x.strip() for x in head.split(',')]
            call = hp[-1].upper() if hp and CALL.fullmatch(hp[-1].upper()) else ''
            # rest looks like: ", Harleysville, PA. WV2M.  7.030 7.240 14.030. QSL. Frank Gallo, 106 Tweed Way, ..."
            parts = [x.strip(' ,') for x in re.split(r'(?<!St)(?<!Ft)(?<!Mt)(?<!Pt)(?<!Jr)(?<!Sr)(?<!Dr)\.\s+', rest.lstrip(', ').strip())]
            where = parts[0] if parts else ''
            by = parts[1] if len(parts) > 1 else ''
            freqs = parts[2] if len(parts) > 2 and re.search(r'\d', parts[2]) else ''
            qsl = ''
            for p in parts[2:]:
                if re.match(r'(?i)^(qsl|certificate|certificate & qsl|qsl & certificate|e-?qsl|lotw)', p):
                    qsl = p
                    break
            st = ''
            m = re.search(r',\s*([A-Z]{2})$', where)
            if m and (m.group(1) in STATES or m.group(1) in PROV):
                st = m.group(1)
            calls = [call] if call else []
            for c in CALL.findall(rest.upper()):
                base = c.split('/')[0]
                if re.fullmatch(r'[KNW]\d[A-Z]', base) and c not in calls:
                    calls.append(c)  # extra 1x1 / 2x1 event calls named in the text (W7B, W7I, ...)
            if e < TODAY:
                continue
            key = (title.lower(), s.isoformat(), call)
            if key in seen:
                continue
            seen.add(key)
            out.append({'title': title, 'start': s.isoformat(), 'end': e.isoformat(), 'times': times, 'call': call,
                        'calls': calls[:12], 'where': where, 'st': st, 'by': by if by.upper() not in ('N/A', 'NA') else '',
                        'freqs': freqs, 'qsl': qsl, 'url': url, 'note': rest[:400]})
        if not re.search(r'class="next"', h):
            break
        time.sleep(1.5)
    out.sort(key=lambda x: (x['start'], x['title']))
    return out


def nth_full_weekend(y, m, n):
    """Saturday of the n-th full (Sat+Sun) weekend of a month."""
    d = dt.date(y, m, 1)
    while d.weekday() != 5:
        d += dt.timedelta(days=1)
    if (d + dt.timedelta(days=1)).month != m:
        d += dt.timedelta(days=7)
    return d + dt.timedelta(days=7 * (n - 1))


def nth_weekday(y, m, wd, n):
    d = dt.date(y, m, 1)
    while d.weekday() != wd:
        d += dt.timedelta(days=1)
    return d + dt.timedelta(days=7 * (n - 1))


def yearly():
    out = []
    for y in (TODAY.year, TODAY.year + 1):
        ev = [
            ('Straight Key Night', dt.date(y, 1, 1), dt.date(y, 1, 1), '0000Z-2359Z', 'Every January 1. CW with a straight key or bug; everyone is welcome, no score.',
             'W1AW and stations everywhere', 'https://www.arrl.org/straight-key-night'),
            ('Museum Ships Weekend', nth_full_weekend(y, 6, 1), nth_full_weekend(y, 6, 1) + dt.timedelta(days=1), '0000Z Sat-2359Z Sun',
             'First full weekend of June. Battleships, submarines, lightships and other museum ships on the air.', 'NJ2BB (USS New Jersey) and 100+ ships', 'https://www.nj2bb.org/museum/'),
            ('13 Colonies Special Event', dt.date(y, 7, 1), dt.date(y, 7, 7), '1300Z Jul 1-0400Z Jul 7',
             'Every July 1-7. Work all 13 colonies plus the bonus stations for a clean sweep certificate.', 'K2A-K2M, WM3PEN, GB13COL', 'https://www.13colonies.net/'),
            ('International Lighthouse Lightship Weekend (ILLW)', nth_full_weekend(y, 8, 3), nth_full_weekend(y, 8, 3) + dt.timedelta(days=1), '0001Z Sat-2400Z Sun',
             'Third full weekend of August. Hundreds of lighthouses worldwide on the air.', 'Lighthouse stations worldwide', 'https://illw.net/'),
            ('Route 66 On The Air', nth_weekday(y, 9, 5, 2), nth_weekday(y, 9, 5, 2) + dt.timedelta(days=8), '',
             'Usually starts the second Saturday of September for 9 days. Stations along historic Route 66 (W6A-W6U style calls).', 'Citrus Belt ARC (W6JBR) and stations along Route 66', 'https://www.arrl.org/Events/view/159881'),
            ('Jamboree on the Air (JOTA)', nth_full_weekend(y, 10, 3), nth_full_weekend(y, 10, 3) + dt.timedelta(days=1), '',
             'Third full weekend of October. Scouts on the air around the world; be kind and slow down for them.', 'K2BSA and Scout stations everywhere', 'https://en.wikipedia.org/wiki/Jamboree_on_the_Air'),
        ]
        for name, s, e, times, about, calls, url in ev:
            if e >= TODAY and s <= TODAY + dt.timedelta(days=430):
                out.append({'title': name, 'start': s.isoformat(), 'end': e.isoformat(), 'times': times, 'about': about, 'calls': calls, 'url': url})
    out.sort(key=lambda x: x['start'])
    return out


def main():
    try:
        old = json.loads(OUT.read_text(encoding='utf-8'))
    except Exception:  # noqa: BLE001
        old = {}
    status = {}
    try:
        st = arrl()
        status['ARRL'] = 'ok (%d)' % len(st)
    except Exception as e:  # noqa: BLE001
        st = [x for x in old.get('stations', []) if x.get('end', '') >= TODAY.isoformat()]
        status['ARRL'] = 'failed, kept %d: %s' % (len(st), e)
        log('ARRL FAILED', e)
    data = {'stations': st, 'yearly': yearly(), 'status': status}
    if {k: v for k, v in old.items() if k != 'updated'} == data:
        notice('Special events', 'no changes ' + json.dumps(status))
        return 0
    data = {'updated': dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), **data}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    notice('Special events', json.dumps(status) + ' | first: ' + ' / '.join('%s %s %s' % (x['start'], x['call'], x['title']) for x in st[:4]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
