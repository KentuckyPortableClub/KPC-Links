"""Weekly: the 25 Kentucky POTA parks with the fewest QSOs and the 25 with the fewest activations.

Reads POTA's public park list for Kentucky (https://api.pota.app/location/parks/US-KY), which carries each
park's total activations, attempts and QSOs. The park list, names, counties and map points come from
kpc-ky-data.json `parks` (what every KPC tool uses). Writes kpc-top25.json for kpc-guide-top25.html.

Ranking rules (same as the KPC Top 25 PDF):
  List 1: lowest total QSOs first; activation count breaks ties.
  List 2: lowest total activations first; total QSOs breaks ties.
  Any tie left after that goes to the lower reference number.
If POTA can't be reached or answers with something odd, the old file is kept and the run says why.
"""
import datetime as dt
import json
import pathlib
import sys
import time
import urllib.request

UA = 'Mozilla/5.0 (compatible; KPC-top25; +https://kentuckyportableclub.github.io/KPC-Links/)'
URL = 'https://api.pota.app/location/parks/US-KY'
OUT = pathlib.Path('kpc-top25.json')
TOP = 25


def notice(title, msg):
    print('::notice title=%s::%s' % (title, str(msg).replace('%', '%25').replace('\n', '%0A')), flush=True)


def get(url, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept': 'application/json'})
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.loads(r.read().decode('utf-8', 'replace'))
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(5 * (i + 1))
    raise last


def num(ref):
    try:
        return int(ref.split('-')[1])
    except (IndexError, ValueError):
        return 10 ** 9


def build(stats, updated, parks):
    """stats: {ref: (activations, qsos, attempts or None)}; parks: kpc-ky-data.json parks list."""
    rows = []
    for p in parks:
        s = stats.get(p['c'])
        if not s:
            continue
        a, q, t = s
        row = {'c': p['c'], 'n': p['n'], 'co': p.get('co', ''), 'la': p.get('la'), 'lo': p.get('lo'), 'a': a, 'q': q}
        if t is not None:
            row['t'] = t
        rows.append(row)

    def ranked(key):
        out = []
        for i, r in enumerate(sorted(rows, key=key)[:TOP]):
            out.append(dict(r, r=i + 1))
        return out

    return {
        'updated': updated,
        'source': 'POTA public park statistics (api.pota.app), Kentucky parks from kpc-ky-data.json',
        'parks': len(rows),
        'qsos': ranked(lambda r: (r['q'], r['a'], num(r['c']))),
        'acts': ranked(lambda r: (r['a'], r['q'], num(r['c']))),
        # every ranked park as [ref, activations, QSOs], so the page can build a full 25 when a
        # visitor hides parks they have already activated (My Parks "NEW TO ME" / "ATNO")
        'all': [[r['c'], r['a'], r['q']] for r in sorted(rows, key=lambda r: num(r['c']))],
    }


def main():
    parks = json.load(open('kpc-ky-data.json', encoding='utf-8'))['parks']
    try:
        j = get(URL)
    except Exception as e:  # noqa: BLE001
        notice('POTA not reachable', '%s. Kept the old kpc-top25.json.' % e)
        return 0
    if not isinstance(j, list):
        notice('Odd answer from POTA', 'Expected a list of parks. Kept the old kpc-top25.json.')
        return 0
    stats = {}
    for x in j:
        ref = str(x.get('reference') or '').upper()
        if not ref.startswith('US-'):
            continue
        a, q = x.get('activations'), x.get('qsos', x.get('contacts'))
        try:
            stats[ref] = (int(a), int(q), int(x['attempts']) if x.get('attempts') is not None else None)
        except (TypeError, ValueError):
            continue
    ours = {p['c'] for p in parks}
    have = ours & set(stats)
    if len(have) < 0.9 * len(ours):
        notice('Too few park numbers', 'POTA gave numbers for %d of %d KPC parks. Kept the old kpc-top25.json.'
               % (len(have), len(ours)))
        return 0
    missing = sorted(ours - set(stats), key=num)
    extra = sorted(set(stats) - ours, key=num)
    if missing:
        notice('KPC parks not in the POTA list', ', '.join(missing))
    if extra:
        notice('POTA parks not in kpc-ky-data.json (left out)', ', '.join(extra))
    data = build(stats, dt.date.today().isoformat(), parks)
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    notice('Top 25 updated', 'Fewest QSOs: %s (%d). Fewest activations: %s (%d). %d parks ranked.' % (
        data['qsos'][0]['c'], data['qsos'][0]['q'], data['acts'][0]['c'], data['acts'][0]['a'], data['parks']))
    return 0


if __name__ == '__main__':
    sys.exit(main())
