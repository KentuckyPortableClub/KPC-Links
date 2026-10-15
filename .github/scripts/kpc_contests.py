#!/usr/bin/env python3
"""KPC contest calendar -> kpc-contests.json (Events page, section #contests).

Two sources:
 1. The WA7BNM Contest Calendar RSS feed (every contest in the next ~8 days). Its Terms of Use allow showing
    the RSS feed on a club website as long as it is labeled "WA7BNM Contest Calendar" and links to the site,
    so we only read the feed (never the web pages) and the Events page labels and links it.
 2. The big yearly contests worked out from their usual dates (ARRL and CQ contests, Winter Field Day),
    checked against the ARRL 2026 contest calendar and the sponsors' rules. Each links to the official rules.
Runs every morning from .github/workflows/kpc-ses.yml.
"""
import datetime as dt
import html
import json
import pathlib
import re
import sys
import time
import urllib.request

UA = 'Mozilla/5.0 (compatible; KPC-Links contest calendar; +https://kentuckyportableclub.github.io/KPC-Links/)'
OUT = pathlib.Path('kpc-contests.json')
NOW = dt.datetime.now(dt.timezone.utc)
TODAY = NOW.date()
MON = {m: i for i, m in enumerate(['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec'], 1)}


def notice(title, msg):
    print('::notice title=%s::%s' % (title, str(msg).replace('%', '%25').replace('\n', '%0A')), flush=True)


def get(url, tries=3):
    last = None
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=40) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(5 * (i + 1))
    raise last


def guess(name):
    n = name.upper()
    modes = []
    if re.search(r'\bCW\b|CWT|CWOPS|SKCC|STRAIGHT KEY|\bSST\b|\bMST\b|FISTS|\bQRQ\b|MORSE', n):
        modes.append('CW')
    if re.search(r'\bSSB\b|PHONE|\bVOICE\b|\bAM\b|\bFM\b|\bSPRINT LADDER\b', n):
        modes.append('PHONE')
    if re.search(r'RTTY|FT8|FT4|DIGI|PSK|JS8|\bMGM\b|OLIVIA|\bSSTV\b|\bDATA\b|BPSK|MFSK', n):
        modes.append('DIGITAL')
    kinds = []
    if re.search(r'QSO PARTY|\bQP\b', n):
        kinds.append('QSOPARTY')
    if re.search(r'VHF|UHF|MICROWAVE|\b50 ?MHZ|\b144|\b432|\b2 ?M\b|\b6 ?M\b|\bEME\b|GHZ|222', n):
        kinds.append('VHF')
    if re.search(r'QRP', n):
        kinds.append('QRP')
    return modes, kinds


def seg_times(desc):
    """'0000Z-0500Z, Oct 15' / '1500Z, Oct 17 to 0300Z, Oct 18' / '... and ...' -> [(start, end)] UTC datetimes."""
    out = []
    for part in re.split(r'\s+and\s+', desc.strip()):
        m = re.match(r'(\d{4})Z-(\d{4})Z,\s*([A-Za-z]{3})\s+(\d{1,2})$', part.strip())
        m2 = re.match(r'(\d{4})Z,\s*([A-Za-z]{3})\s+(\d{1,2})\s+to\s+(\d{4})Z,\s*([A-Za-z]{3})\s+(\d{1,2})$', part.strip())
        def mk(hhmm, mon, day):
            mo = MON[mon.lower()[:3]]
            y = TODAY.year + (1 if mo < TODAY.month - 6 else -1 if mo > TODAY.month + 6 else 0)
            return dt.datetime(y, mo, int(day), int(hhmm[:2]) % 24, int(hhmm[2:]), tzinfo=dt.timezone.utc) + (dt.timedelta(days=1) if hhmm == '2400' else dt.timedelta())
        try:
            if m:
                s = mk(m.group(1), m.group(3), m.group(4))
                e = mk(m.group(2), m.group(3), m.group(4))
                if e <= s:
                    e += dt.timedelta(days=1)
                out.append((s, e))
            elif m2:
                out.append((mk(m2.group(1), m2.group(2), m2.group(3)), mk(m2.group(4), m2.group(5), m2.group(6))))
        except Exception:  # noqa: BLE001
            pass
    return out


def wa7bnm():
    x = get('https://www.contestcalendar.com/calendar.rss')
    items = re.findall(r'(?is)<item>.*?<title>(.*?)</title>.*?<link>(.*?)</link>.*?<description>(.*?)</description>.*?</item>', x)
    out = []
    for t, link, desc in items:
        t, link, desc = html.unescape(t).strip(), html.unescape(link).strip(), html.unescape(desc).strip()
        segs = seg_times(desc)
        if not segs:
            continue
        if max(e for s, e in segs) < NOW - dt.timedelta(hours=1):
            continue
        modes, kinds = guess(t)
        out.append({'name': t, 'url': link, 'when': desc, 'segs': [[s.strftime('%Y-%m-%dT%H:%MZ'), e.strftime('%Y-%m-%dT%H:%MZ')] for s, e in segs],
                    'modes': modes, 'kinds': kinds, 'src': 'WA7BNM'})
    return out


def full_weekends(y, m):
    d = dt.date(y, m, 1)
    while d.weekday() != 5:
        d += dt.timedelta(days=1)
    if (d + dt.timedelta(days=1)).month != m:
        d += dt.timedelta(days=7)
    out = []
    while d.month == m and (d + dt.timedelta(days=1)).month == m:
        out.append(d)
        d += dt.timedelta(days=7)
    return out


def big():
    # (name, month, which full weekend (1..4 or -1 = last), start hour UTC Sat, length hours, modes, kinds, sponsor, rules url)
    R = [
        ('ARRL RTTY Roundup', 1, 1, 18, 30, ['DIGITAL'], ['BIG'], 'ARRL', 'https://www.arrl.org/rtty-roundup'),
        ('ARRL January VHF Contest', 1, 3, 19, 33, ['CW', 'PHONE', 'DIGITAL'], ['VHF', 'BIG'], 'ARRL', 'https://www.arrl.org/january-vhf'),
        ('Winter Field Day', 1, 4, 16, 30, ['CW', 'PHONE', 'DIGITAL'], ['FIELD', 'BIG'], 'Winter Field Day Association', 'https://www.winterfieldday.org/'),
        ('CQ 160-Meter Contest (CW)', 1, -1, -2, 48, ['CW'], ['BIG'], 'CQ', 'https://www.cq160.com/rules.htm'),
        ('ARRL International DX Contest (CW)', 2, 3, 0, 48, ['CW'], ['BIG'], 'ARRL', 'https://www.arrl.org/arrl-dx'),
        ('CQ 160-Meter Contest (SSB)', 2, -1, -2, 48, ['PHONE'], ['BIG'], 'CQ', 'https://www.cq160.com/rules.htm'),
        ('ARRL International DX Contest (Phone)', 3, 1, 0, 48, ['PHONE'], ['BIG'], 'ARRL', 'https://www.arrl.org/arrl-dx'),
        ('CQ WPX Contest (SSB)', 3, -1, 0, 48, ['PHONE'], ['BIG'], 'CQ', 'https://www.cqwpx.com/rules.htm'),
        ('CQ WPX Contest (CW)', 5, -1, 0, 48, ['CW'], ['BIG'], 'CQ', 'https://www.cqwpx.com/rules.htm'),
        ('ARRL International Digital Contest', 6, 1, 18, 24, ['DIGITAL'], ['BIG'], 'ARRL', 'https://www.arrl.org/arrl-digital-contest'),
        ('ARRL June VHF Contest', 6, 2, 18, 33, ['CW', 'PHONE', 'DIGITAL'], ['VHF', 'BIG'], 'ARRL', 'https://www.arrl.org/june-vhf'),
        ('ARRL Field Day', 6, 4, 18, 27, ['CW', 'PHONE', 'DIGITAL'], ['FIELD', 'BIG'], 'ARRL', 'https://www.arrl.org/field-day'),
        ('IARU HF World Championship', 7, 2, 12, 24, ['CW', 'PHONE'], ['BIG'], 'ARRL / IARU', 'https://www.arrl.org/iaru-hf-world-championship'),
        ('ARRL September VHF Contest', 9, 2, 18, 33, ['CW', 'PHONE', 'DIGITAL'], ['VHF', 'BIG'], 'ARRL', 'https://www.arrl.org/september-vhf'),
        ('CQ World Wide DX Contest (SSB)', 10, -1, 0, 48, ['PHONE'], ['BIG'], 'CQ', 'https://cqww.com/rules.htm'),
        ('ARRL November Sweepstakes (CW)', 11, 1, 21, 30, ['CW'], ['BIG'], 'ARRL', 'https://www.arrl.org/sweepstakes'),
        ('ARRL November Sweepstakes (Phone)', 11, 3, 21, 30, ['PHONE'], ['BIG'], 'ARRL', 'https://www.arrl.org/sweepstakes'),
        ('CQ World Wide DX Contest (CW)', 11, -1, 0, 48, ['CW'], ['BIG'], 'CQ', 'https://cqww.com/rules.htm'),
        ('ARRL 160-Meter Contest', 12, 1, -2, 42, ['CW'], ['BIG'], 'ARRL', 'https://www.arrl.org/160-meter'),
        ('ARRL 10-Meter Contest', 12, 2, 0, 48, ['CW', 'PHONE'], ['BIG'], 'ARRL', 'https://www.arrl.org/10-meter'),
    ]
    out = []
    for y in (TODAY.year, TODAY.year + 1):
        for name, m, w, h, length, modes, kinds, by, url in R:
            fw = full_weekends(y, m)
            sat = fw[w - 1] if w > 0 else fw[w]
            s = dt.datetime(sat.year, sat.month, sat.day, tzinfo=dt.timezone.utc) + dt.timedelta(hours=h)
            e = s + dt.timedelta(hours=length)
            if e < NOW or s > NOW + dt.timedelta(days=400):
                continue
            out.append({'name': name, 'url': url, 'when': 'Usual dates (' + by + '); check the rules', 'segs': [[s.strftime('%Y-%m-%dT%H:%MZ'), e.strftime('%Y-%m-%dT%H:%MZ')]],
                        'modes': modes, 'kinds': kinds, 'src': 'RULE', 'by': by})
    out.sort(key=lambda c: c['segs'][0][0])
    return out


def main():
    try:
        old = json.loads(OUT.read_text(encoding='utf-8'))
    except Exception:  # noqa: BLE001
        old = {}
    status = {}
    try:
        wk = wa7bnm()
        status['WA7BNM'] = 'ok (%d)' % len(wk)
    except Exception as e:  # noqa: BLE001
        wk = [c for c in old.get('week', []) if c['segs'][-1][1] >= NOW.strftime('%Y-%m-%dT%H:%MZ')]
        status['WA7BNM'] = 'failed, kept %d: %s' % (len(wk), e)
    data = {'week': wk, 'big': big(), 'status': status}
    if {k: v for k, v in old.items() if k != 'updated'} == data:
        notice('Contests', 'no changes ' + json.dumps(status))
        return 0
    data = {'updated': NOW.strftime('%Y-%m-%dT%H:%M:%SZ'), **data}
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    notice('Contests', json.dumps(status) + ' | ' + ' / '.join(c['name'] for c in wk[:5]))
    return 0


if __name__ == '__main__':
    sys.exit(main())
