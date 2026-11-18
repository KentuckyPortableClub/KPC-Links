#!/usr/bin/env python3
"""THE AGENCY TABLE (matching plan section 2, Fable 17 Nov; owner: 'the part we need to nail'). Learned, never hand-written:
for every person-reviewed join in the US key (a row whose 'how' starts with 'reviewed', code-tagged rule rows left out), the host of
the park's POTA website (data/parkinfo field 1, 'www.' dropped) is counted against the joined record's manager (PAD-US Mang_Name,
or the state layer's code, which the key keeps in Mang_Name). Counted once per park: "parks whose website is fws.gov have their
land in these managers' records". Writes .github/key-agency-table.json (a US rule file, read by the contest tie-break,
switch KPC_AGENCY_TIE). By hand, offline:

  python3 .github/scripts/kpc_agency_table.py --cache DIR_WITH_US-XX.json.gz --parkinfo KPC-Data/data/parkinfo [--out FILE]
"""
import argparse, collections, datetime, glob, gzip, json, os, urllib.parse

RULE_ROWS = ('reviewed: the district = FWS fee', 'reviewed (official tract:')


def host(u):
    h = urllib.parse.urlparse(str(u or '')).netloc.lower().split(':')[0]
    return h[4:] if h.startswith('www.') else h


def learn(cache, parkinfo, keydir='data/us-key'):
    tab = collections.defaultdict(collections.Counter)
    for f in sorted(glob.glob(os.path.join(cache, 'US-??.json.gz'))):
        st = os.path.basename(f)[3:5]
        try:
            recs = {str(r['OBJECTID']): r for r in json.load(gzip.open(f, 'rt', encoding='utf-8'))['recs']}
            key = json.load(open(os.path.join(keydir, f'US-{st}.json'), encoding='utf-8'))['parks']
            pi = json.load(open(os.path.join(parkinfo, f'US-{st}.json'), encoding='utf-8'))['parks']
        except (OSError, ValueError, KeyError): continue
        for ref, p in key.items():
            h = host((pi.get(ref) or [None, ''])[1] if len(pi.get(ref) or []) > 1 else '')
            if not h: continue
            seen = set()
            for x in p.get('m') or []:
                how = str(x[3]) if len(x) > 3 else ''
                if not how.startswith('reviewed') or how.startswith(RULE_ROWS): continue
                r = recs.get(str(x[0]))
                if r and r.get('Mang_Name'): seen.add(str(r['Mang_Name']))
            if seen:
                tab[h]['_parks'] += 1
                for m in seen: tab[h][m] += 1
    return {h: dict(sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))) for h, c in sorted(tab.items()) if c['_parks'] >= 2}


if __name__ == '__main__':
    a = argparse.ArgumentParser(); a.add_argument('--cache', required=True); a.add_argument('--parkinfo', required=True)
    a.add_argument('--out', default='.github/key-agency-table.json'); a.add_argument('--date', default=datetime.date.today().isoformat())
    o = a.parse_args()
    t = learn(o.cache, o.parkinfo)
    doc = {'about': 'Learned by .github/scripts/kpc_agency_table.py from the person-reviewed joins: host of the POTA website -> '
                    'count of parks whose reviewed land is in that manager\'s records (_parks = parks counted). Read by the contest '
                    'tie-break (kpc_key_rules.agency_pick, switch KPC_AGENCY_TIE). Do not edit by hand: run the script again.',
           'learned': o.date, 'hosts': t}
    open(o.out, 'w', encoding='utf-8').write(json.dumps(doc, indent=1, ensure_ascii=False) + '\n')
    print(f'{len(t)} website hosts written to {o.out}')
