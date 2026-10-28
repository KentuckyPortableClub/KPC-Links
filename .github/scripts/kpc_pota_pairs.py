#!/usr/bin/env python3
"""POTA ACTIVATION HISTORY PAIRS (chat 2, Oct 27 2026; HQ 3:46 PM MISSING CHECK source 2, the proof-badge data pulled early). For each park
in a state, POTA's public activation list (api.pota.app/park/activations/<ref>), grouped by (activator, date): two parks activated
on the same day by the same call = a pair people really worked together. COUNTS ONLY are kept (no call signs, no dates):
data/fers/pota-pairs-<US-XX>.json {made, parks_read, pairs: {"A+B": times}}. Slow (1 request a second), re-read at most every
30 days. STATES='US-KY US-OH'. A hint, never proof (an activator can drive between two parks the same day). Never fails."""
import itertools, json, os, pathlib, sys, time, urllib.request
UA = {'User-Agent': 'KPC 2-fer missing check (kentuckyportableclub.github.io; counts only)'}
STATES = (os.environ.get('STATES') or 'US-KY').upper().replace(',', ' ').split()
OUT = pathlib.Path('data/fers')
T0 = time.time(); LIMIT = float(os.environ.get('PAIR_MINUTES') or 40) * 60


def get(url):
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r: return json.loads(r.read().decode('utf-8', 'replace'))
        except Exception:  # noqa: BLE001
            time.sleep(3 + 5 * i)
    return None


n_keys_shown = [0]


def main():
    for st in STATES:
        st = st if '-' in st else 'US-' + st
        f = OUT / f'pota-pairs-{st}.json'
        try: old = json.load(open(f))
        except Exception: old = {}  # noqa: BLE001
        if old.get('made', '') >= time.strftime('%Y-%m-%d', time.localtime(time.time() - 30 * 86400)) and old.get('complete'):
            print(f'::notice title=POTA pairs::{st}: read on {old["made"]}, kept', flush=True); continue
        if st == 'US-KY':
            refs = [p['c'] for p in json.load(open('kpc-ky-data.json'))['parks']]
        else:
            try: refs = list(json.load(open(f'data/parkinfo/{st}.json'))['parks'])
            except Exception:  # noqa: BLE001
                print(f'::notice title=POTA pairs::{st}: no park list (data/parkinfo/{st}.json), skipped', flush=True); continue
        days, counts, n, complete = {}, {}, 0, True
        for ref in sorted(refs):
            if time.time() - T0 > LIMIT: complete = False; break
            j = get(f'https://api.pota.app/park/activations/{ref}?count=all')
            time.sleep(1.0)
            if j is None: continue
            n += 1
            if not n_keys_shown[0] and isinstance(j, list) and j:
                n_keys_shown[0] = 1; print(f'::notice title=POTA pairs::record fields: {sorted(j[0])[:12]}', flush=True)
            for a in j if isinstance(j, list) else []:
                call = str(a.get('activeCallsign') or a.get('activator') or a.get('callsign') or '').upper()
                call = max(call.split('/'), key=len) if call else ''
                day = str(a.get('qso_date') or a.get('date') or '').replace('-', '')[:8]
                if call and day:
                    days.setdefault((call, day), set()).add(ref)
                    # HQ Oct 27: a pair POTA shows as ONE session logging both parks is always kept by the missing check.
                    # POTA's park lists carry no 'both parks' field, so the closest the data comes is the same call on the same
                    # day with IDENTICAL QSO counts at both parks (one log sent to both). Labelled as a likely one-session pair.
                    counts.setdefault((call, day), {})[ref] = (a.get('totalQSOs'), a.get('qsosCW'), a.get('qsosDATA'), a.get('qsosPHONE'))
        same = set()
        for cd, byref in counts.items():
            for (ra, ca), (rb, cb) in itertools.combinations(sorted(byref.items()), 2):
                if ca == cb and ca[0]: same.add(f'{ra}+{rb}' if ra < rb else f'{rb}+{ra}')
        pairs = {}
        for parks in days.values():
            for a, b in itertools.combinations(sorted(parks), 2): pairs[f'{a}+{b}'] = pairs.get(f'{a}+{b}', 0) + 1
        OUT.mkdir(parents=True, exist_ok=True)
        f.write_text(json.dumps({'about': 'Pairs of parks POTA activators worked on the same day (counts only, no calls or dates). A hint, never proof.',
                                 'made': time.strftime('%Y-%m-%d'), 'parks_read': n, 'complete': complete, 'pairs': dict(sorted(pairs.items())),
                                 'same_session': sorted(same), 'same_session_about': 'same call, same day, identical QSO counts at both parks = one session logged to both (a likely 2-fer; POTA publishes no "both parks" field)'}, indent=0) + '\n')
        print(f'::notice title=POTA pairs::{st}: {n} of {len(refs)} parks read, {len(pairs)} pairs worked the same day' + ('' if complete else ' (stopped for time)'), flush=True)


if __name__ == '__main__':
    try: main()
    except Exception as e:  # noqa: BLE001
        print(f'::notice title=POTA pairs::stopped: {e}', flush=True)
    sys.exit(0)
