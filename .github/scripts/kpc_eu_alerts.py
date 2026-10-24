#!/usr/bin/env python3
"""Europe's weather warnings for the KPC Field Weather page (Opus Oct 24 2026; Activators Lounge step 5,
Brandon: weather alerts for Canada and Europe). MeteoAlarm publishes every national weather service's warnings as one
Atom feed per country; a web page can't be sure of reading those directly, so this job copies them every 3 hours into
data/alerts/eu.json = {updated, countries: {ISO2: {name, link, items: [{area, event, level, sev, onset, expires}]}}}.
Only writes when something changed, keeps a country's last list when its feed fails, never fails (exit 0)."""
import datetime as dt
import json
import pathlib
import re
import sys
import urllib.request
import xml.etree.ElementTree as ET

OUT = pathlib.Path('data/alerts/eu.json')
FEED = 'https://feeds.meteoalarm.org/feeds/meteoalarm-legacy-atom-'
C = {'AT': 'austria', 'BE': 'belgium', 'BA': 'bosnia-herzegovina', 'BG': 'bulgaria', 'HR': 'croatia', 'CY': 'cyprus',
     'CZ': 'czechia', 'DK': 'denmark', 'EE': 'estonia', 'FI': 'finland', 'FR': 'france', 'DE': 'germany', 'GR': 'greece',
     'HU': 'hungary', 'IS': 'iceland', 'IE': 'ireland', 'IL': 'israel', 'IT': 'italy', 'LV': 'latvia', 'LT': 'lithuania',
     'LU': 'luxembourg', 'MT': 'malta', 'MD': 'moldova', 'ME': 'montenegro', 'NL': 'netherlands', 'MK': 'republic-of-north-macedonia',
     'NO': 'norway', 'PL': 'poland', 'PT': 'portugal', 'RO': 'romania', 'RS': 'serbia', 'SK': 'slovakia', 'SI': 'slovenia',
     'ES': 'spain', 'SE': 'sweden', 'CH': 'switzerland', 'GB': 'united-kingdom', 'UA': 'ukraine'}
NS = {'a': 'http://www.w3.org/2005/Atom', 'cap': 'urn:oasis:names:tc:emergency:cap:1.2'}
LEVEL = {'Minor': 'yellow', 'Moderate': 'yellow', 'Severe': 'orange', 'Extreme': 'red'}


def note(m):
    print(f'::notice title=EU weather warnings::{m}', flush=True)


def get(u):
    req = urllib.request.Request(u, headers={'User-Agent': 'KPC weather (kentuckyportableclub.github.io)'})
    with urllib.request.urlopen(req, timeout=40) as f:
        return f.read()


def txt(e, tag):
    x = e.find(tag, NS)
    return (x.text or '').strip() if x is not None and x.text else ''


def main():
    try:
        old = json.loads(OUT.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        old = {'countries': {}}
    now = dt.datetime.now(dt.timezone.utc)
    out, bad, n = {}, [], 0
    for iso, slug in C.items():
        try:
            root = ET.fromstring(get(FEED + slug))
        except Exception as e:  # noqa: BLE001
            bad.append(iso)
            if iso in old.get('countries', {}):
                out[iso] = old['countries'][iso]
            continue
        items = []
        for en in root.findall('a:entry', NS):
            sev, ex = txt(en, 'cap:severity'), txt(en, 'cap:expires')
            try:
                if ex and dt.datetime.fromisoformat(ex.replace('Z', '+00:00')) < now:
                    continue
            except ValueError:
                pass
            if txt(en, 'cap:status') not in ('', 'Actual') or txt(en, 'cap:msgType') == 'Cancel':
                continue
            ev = txt(en, 'cap:event') or re.sub(r'^.*?(?:warning|Warning)\s*', '', txt(en, 'a:title'))
            items.append({'area': txt(en, 'cap:areaDesc'), 'event': ev, 'level': LEVEL.get(sev, 'yellow'), 'sev': sev,
                          'onset': txt(en, 'cap:onset') or txt(en, 'cap:effective'), 'expires': ex})
        order = {'Extreme': 0, 'Severe': 1, 'Moderate': 2, 'Minor': 3}
        items.sort(key=lambda x: (order.get(x['sev'], 9), x['area']))
        out[iso] = {'name': slug.replace('republic-of-', '').replace('-', ' ').title(), 'link': 'https://meteoalarm.org/', 'items': items[:300]}
        n += len(items)
    if old.get('countries') == out:
        note(f'no change ({n} warnings, {len(bad)} feeds did not answer)')
        return
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps({'updated': now.isoformat(timespec='minutes'), 'countries': out}, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    note(f'{n} warnings in {len(out)} countries' + (f'; no answer from {", ".join(bad)} (kept their last list)' if bad else ''))


if __name__ == '__main__':
    try:
        main()
    except Exception as e:  # noqa: BLE001
        note(f'stopped early: {e}')
    sys.exit(0)
