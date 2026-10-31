#!/usr/bin/env python3
"""BOT A for the CANADA key (chat 2, Oct 30 2026 9:40 PM; chat 10 AUTO-1 ask 1: Canada SURE rows got the YES but nothing joined them). Same as kpc_ca_answers.py (the WORLD key) (chat 2, Oct 30 2026 11:10 AM; chat 10's ask after AUTO-1W, Brandon 10:44 AM 'All 3').
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

KEY = pathlib.Path('data/ca-key')
OVR, LEDGER, CCS = KEY / 'overrides.json', KEY / 'answers-applied.json', KEY / 'answers-provinces.txt'
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
    if D is None: print('::notice title=Canada answers::no KPC-Data checkout: nothing applied'); return
    q = []
    for f in sorted((D / 'data/waiting/questions').glob('*.json')):   # every question file: gis-hunter, key-pieces… (Canada rows only)
        j = load(f, {}); x = j.get('questions') if isinstance(j, dict) else j
        q += [r for r in (list(x.values()) if isinstance(x, dict) else (x or [])) if isinstance(r, dict) and str(r.get('ref', '')).startswith('CA-')]
    ovr = load(OVR, {'parks': {}}); P = ovr.setdefault('parks', {})
    led = load(LEDGER, {})
    stamp = dt.datetime.now().strftime('%Y-%m-%d %H:%M'); ccs = set(); n = {'YES': 0, 'NO': 0, 'same': 0, 'skip': 0}
    latest = {}
    for r in q:
        if not isinstance(r, dict): continue
        _a = re.sub(r'^[^A-Za-z]+', '', str(r.get('answer') or '')).upper()   # Oct 31 (Fable #5): first word decides; NOT SURE is neither
        ans = '' if _a.startswith('NOT') else (re.match(r'(YES|NO)\b', _a).group(1) if re.match(r'(YES|NO)\b', _a) else '')
        ref, nm = str(r.get('ref') or ''), str(r.get('record_name') or '').strip()
        if ans not in ('YES', 'NO') or not ref or not nm: continue
        latest[(ref, nm.lower())] = r
    for (ref, _), r in latest.items():
        _a = re.sub(r'^[^A-Za-z]+', '', str(r['answer'])).upper(); ans = re.match(r'(YES|NO)\b', _a).group(1); nm = str(r['record_name']).strip()
        cc = str(r.get('area') or '').upper().replace('CA-', '')[:2] or 'CA'
        by = str(r.get('checked_by') or '')
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
        v['why'] = (v.get('why', '') + ' · ' if v.get('why') else '') + f"{stamp}: question row {ans} ({by or 'chat 11'}; applied by kpc_ca_answers)"
        led[lk] = {'answer': ans, 'checked_by': by, 'applied': stamp}
        n[ans] += 1; ccs.add(cc)
    if n['YES'] or n['NO']:
        json.dump(ovr, open(OVR, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        json.dump(led, open(LEDGER, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
        old = set(CCS.read_text().split()) if CCS.exists() else set()
        CCS.write_text(' '.join(sorted(old | ccs)) + '\n')
    print(f"::notice title=Canada answers::{n['YES']} yes / {n['NO']} no applied; {n['same']} already applied; {n['skip']} skipped "
          f"(a bot YES on an EU layer); provinces: {' '.join(sorted(ccs)) or '-'}")


if __name__ == '__main__':
    try: main()
    except Exception as e: print(f'::notice title=Canada answers::stopped: {str(e)[:200]}')  # noqa: BLE001
    sys.exit(0)
