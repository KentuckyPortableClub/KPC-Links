#!/usr/bin/env python3
"""BOT A for the WORLD key (chat 2, Oct 30 2026 11:10 AM; chat 10's ask after AUTO-1W, Brandon 10:44 AM 'All 3').
Copies YES / NO answers on world-finder rows (chat 11, or the bot's own six-check 'auto recheck (AUTO-1W)') into the world key's rules
file data/world-key/overrides.json, the way chat 2 did by hand for Australia on Oct 30 5:55 AM. It MOVES decisions; it never makes one.

Reads  <DATA>/data/waiting/questions/world-finder.json   rows {area, ref, record_name, layer, answer, checked_by}
Writes data/world-key/overrides.json        parks[ref]: YES -> join += [record_name] (taken out of 'no'); NO -> no += [record_name]
       data/world-key/answers-applied.json  ledger: the same answer is never applied twice (safe every night); a changed one is
       data/world-key/answers-countries.txt the countries touched -> the nightly world run rebuilds only those (kpc-world-key.yml)
Rules: only countries the world key builds (a data/parkinfo/<CC>.json park list and a source list); an automatic YES on an EU
compilation layer (EEA) is skipped (W-2: EEA = a candidate for chat 11 only, never joined by a bot). Exit 0 always.
"""
import datetime as dt, json, os, pathlib, re, sys

KEY = pathlib.Path('data/world-key')
OVR, LEDGER, CCS = KEY / 'overrides.json', KEY / 'answers-applied.json', KEY / 'answers-countries.txt'
BUILT = set('AU DE GB JP PL ES FR CH AT NL PT SE CZ SI NO RO IT BE DK FI HU SK HR IE LT LV EE LU'.split())   # kpc-world-key.yml ALL


def data_dir():
    for d in (os.environ.get('DATA'), '../kpcdata', '../kpc-data', 'kpcdata'):
        if d and pathlib.Path(d, 'data/waiting/questions').is_dir(): return pathlib.Path(d)
    return None


def load(p, d):
    try: return json.load(open(p, encoding='utf-8'))
    except Exception: return d  # noqa: BLE001


def main():
    D = data_dir()
    if D is None: print('::notice title=World answers::no KPC-Data checkout: nothing applied'); return
    j = load(D / 'data/waiting/questions/world-finder.json', {})
    q = j.get('questions') if isinstance(j, dict) else j
    q = list(q.values()) if isinstance(q, dict) else (q or [])
    ovr = load(OVR, {'parks': {}}); P = ovr.setdefault('parks', {})
    led = load(LEDGER, {})
    stamp = dt.datetime.now().strftime('%Y-%m-%d %H:%M'); ccs = set(); n = {'YES': 0, 'NO': 0, 'same': 0, 'skip': 0}
    latest = {}
    for r in q:
        if not isinstance(r, dict): continue
        ans = str(r.get('answer') or '').strip().upper()
        ref, nm = str(r.get('ref') or ''), str(r.get('record_name') or '').strip()
        if ans not in ('YES', 'NO') or not ref or not nm: continue
        latest[(ref, nm.lower())] = r
    for (ref, _), r in latest.items():
        ans = str(r['answer']).strip().upper(); nm = str(r['record_name']).strip()
        cc = str(r.get('area') or ref.split('-')[0]).upper()[:2]
        by = str(r.get('checked_by') or '')
        if cc not in BUILT or not pathlib.Path(f'data/parkinfo/{cc}.json').exists() and not (D / f'data/parkinfo/{cc}.json').exists():
            n['skip'] += 1; continue
        if ans == 'YES' and 'auto' in by.lower() and re.search(r'\beea\b|nationally designated|natura ?2000', str(r.get('layer') or ''), re.I):
            n['skip'] += 1; continue                                     # W-2: a bot never joins an EU compilation record
        lk = f'{ref}:{nm.lower()}'
        if (led.get(lk) or {}).get('answer') == ans: n['same'] += 1; continue
        v = P.setdefault(ref, {})
        if ans == 'YES':
            v['no'] = [x for x in v.get('no', []) if x.lower() != nm.lower()]
            if not v['no']: v.pop('no')
            v.setdefault('join', [])
            if nm.lower() not in [x.lower() for x in v['join']]: v['join'].append(nm)
        else:
            v['join'] = [x for x in v.get('join', []) if x.lower() != nm.lower()]
            if not v['join']: v.pop('join')
            v.setdefault('no', [])
            if nm.lower() not in [x.lower() for x in v['no']]: v['no'].append(nm)
        v['why'] = (v.get('why', '') + ' · ' if v.get('why') else '') + f"{stamp}: world-finder row {ans} ({by or 'chat 11'}; applied by kpc_world_answers)"
        led[lk] = {'answer': ans, 'checked_by': by, 'applied': stamp}
        n[ans] += 1; ccs.add(cc)
    if n['YES'] or n['NO']:
        json.dump(ovr, open(OVR, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        json.dump(led, open(LEDGER, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        old = set(CCS.read_text().split()) if CCS.exists() else set()
        CCS.write_text(' '.join(sorted(old | ccs)) + '\n')
    print(f"::notice title=World answers::{n['YES']} yes / {n['NO']} no applied; {n['same']} already applied; {n['skip']} skipped "
          f"(country the world key does not build yet, or a bot YES on an EEA layer); countries: {' '.join(sorted(ccs)) or '-'}")


if __name__ == '__main__':
    try: main()
    except Exception as e: print(f'::notice title=World answers::stopped: {str(e)[:200]}')  # noqa: BLE001
    sys.exit(0)
