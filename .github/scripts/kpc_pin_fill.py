#!/usr/bin/env python3
"""OFFICIAL PIN FILLS for the Canada and world answer keys (KPC owner, 2026-11-12; handoff item 5): an official pin is better than
no pin, and an existing pin is never moved.

The file: KPC-Data data/intake/official-pins-nov12.json (KPC-Data #76), {"about": text, "rows": [{ref, action, ready_to_apply,
lat, lon, source_name, source_url, confidence, ...}]}. Its path comes from env KPC_OFFICIAL_PINS (the key workflows lay a read-only
sparse copy of KPC-Data at .op/ and point the variable there). ONLY a row with action 'pin-fill' AND ready_to_apply true is used.
'point-circle-candidate' and 'held' rows (and anything else) do nothing here.
HELD (owner, Nov 12 2026): PF-0033 and PF-0034 are not filled even though their rows are ready (one shared low-confidence point). Nov 13 (Quality, delegated by Brandon 4:43 AM CT): CA-2241, CA-1974 and CA-1997 are held the same way (Ville de Montréal city-polygon fills; CA-1974's 'Site patrimonial de Montréal' site note rested on that fill and is not applied either). The other 19 ready Canada fills, and the CA-2274 note, still apply.

fill(P, area)  P = the builder's POTA park list (data/parkinfo/<file>.json 'parks': ref -> [name, url, type, ..., lat (5), lon (6), ...]).
               A ready fill for a park of this key ('CA' = refs CA-*, a world country 'PF' = refs PF-*) is used ONLY when POTA has no
               usable pin for that park at build time: the pin is absent or 0,0 (kpc_key_facts.pin_why 'nopin' / 'pin00', the keys' own
               test). A POTA pin that is usable is NEVER replaced: the fill is ignored and the run says so. An impossible POTA pin
               ('pinbad', e.g. latitude past 90) is never moved either (kpc_key_facts: 'NEVER moved'): ignored, said, a person checks.
               Returns a NEW dict (the filled parks get a copied row with the official lat / lon at 5 / 6, the rest are the same
               row objects); the input P and its rows are never changed. With nothing to fill, P itself is returned (same object).
mark(parks, P, pins=None)
               Just before the key's 'bk' stamp: every filled park of the key gets 'pf' = {la, lo, why, src, url, conf, pota}
               ('official pin (filled; POTA has none)'; a pin is a 100 ft circle, there is no boundary), and the POTA pins are given
               back: returns POTA's own park list (so 'bk' measures from POTA's pin and still says pin00 / nopin), and when `pins`
               (the Canada key's BKPIN, ref -> (lat, lon)) is given, its filled refs get POTA's pin back.

Never writes a file, never touches the POTA list / parkinfo files, no network. A file that is not given, cannot be read or is not
the expected shape applies NO fill (fail closed) with a loud warning; the country / province build goes on. Two ready rows for one
park, or a fill with an unusable coordinate, are not applied (said). Standard library only (kpc_key_facts is the keys' own module)."""
import json, math, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kpc_key_facts as KF  # noqa: E402  (pin_why: the keys' own usable-pin test)

ENV = 'KPC_OFFICIAL_PINS'
WHY = 'official pin (filled; POTA has none)'
FILLABLE = ('nopin', 'pin00')   # absent / 0,0. 'pinbad' (an impossible POTA pin) is never moved.
# Owner hold (Brandon, Nov 12 2026, 10:59 AM CT): PF-0033 and PF-0034 share ONE low-confidence official point (the Ramsar sheet of
# 'Lagon de Moorea'). Their ready rows in the official pins file are NOT applied: POTA's own (0,0) pin stays, the run lists them as
# held. Taking a ref off this list (after a person checks the point) is the only way to apply its fill.
# Nov 13 (Quality, delegated by Brandon 4:43 AM CT): hold CA-2241, CA-1974 and CA-1997 the same way. Their official pins are centres
# computed from a Ville de Montréal city-boundary polygon, not a stated point (CA-2241 low; CA-1974 and CA-1997 medium). CA-1974's
# 'Site patrimonial de Montréal' site note rested on that fill and is not applied either. The other 19 ready Canada fills still apply
# (Quebec only), and CA-2274 keeps its Tyre-Macfarlane site note.
HELD = {'PF-0033': 'owner hold Nov 12: shares one low-confidence official point with PF-0034',
        'PF-0034': 'owner hold Nov 12: shares one low-confidence official point with PF-0033',
        'CA-2241': "owner hold Nov 13 (Quality, delegated by Brandon 4:43 AM CT): low-confidence Ville de Montréal city-polygon fill (Parc Jean-Drapeau part); held like PF-0033/34",
        'CA-1974': "owner hold Nov 13 (Quality, delegated by Brandon 4:43 AM CT): medium-confidence Ville de Montréal city-polygon fill; the 'Site patrimonial de Montréal' site note that rested on it is held too",
        'CA-1997': "owner hold Nov 13 (Quality, delegated by Brandon 4:43 AM CT): medium-confidence Ville de Montréal city-polygon fill; held like PF-0033/34"}


def held_of(area):
    """{ref: reason} of owner-held fills that belong to this key (area 'CA' = refs CA-*, 'PF' = refs PF-*, ...)."""
    pre = f'{area}-'
    return {ref: why for ref, why in HELD.items() if ref.startswith(pre)}




def _say(notice, title, msg, loud=False):
    """A notice (the builder's own when given); loud = a warning, also a line in the run summary (the Canada build's log is a file)."""
    if loud: print(f"::warning title={title}::{msg}", flush=True)
    elif notice: notice(title, msg)
    else: print(f"::notice title={title}::{msg}", flush=True)
    sm = os.environ.get('GITHUB_STEP_SUMMARY')
    if sm:
        try:
            with open(sm, 'a', encoding='utf-8') as f: f.write(f"- {title}: {msg}\n")
        except OSError: pass


def load(path=None):
    """(rows, problem): the ready pin-fill rows of the file by ref, or ({}, why) when the file is not given / unreadable / malformed."""
    path = path if path is not None else (os.environ.get(ENV) or '').strip()
    if not path: return {}, f'not given ({ENV} is not set)'
    try:
        with open(path, encoding='utf-8') as f: doc = json.load(f)
    except FileNotFoundError: return {}, f'not found ({path})'
    except Exception as e: return {}, f'cannot be read ({type(e).__name__})'  # noqa: BLE001
    rows = doc.get('rows') if isinstance(doc, dict) else None
    if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows): return {}, 'not the expected shape (no list of rows)'
    ready, twice = {}, set()
    for r in rows:
        if r.get('action') != 'pin-fill' or r.get('ready_to_apply') is not True: continue
        ref = str(r.get('ref') or '')
        if not ref: continue
        if ref in ready: twice.add(ref)
        ready[ref] = r
    for ref in twice: ready[ref] = None   # two ready rows for one park: neither is used (never guess)
    return ready, ''


def _coord(r):
    try: la, lo = float(r.get('lat')), float(r.get('lon'))
    except (TypeError, ValueError): return None
    if math.isnan(la) or math.isnan(lo) or KF.pin_why((la, lo)): return None
    return la, lo


class Filled(dict):
    """The filled park list: a dict like P, plus .pota (POTA's own list) and .fills (ref -> the file's row)."""
    pota, fills = None, None


def fill(P, area, notice=None, path=None):
    """P with the ready fills of this key's parks applied where POTA has no usable pin (see the module text)."""
    title = f'Official pin fills ({area})'
    ready, problem = load(path)
    if problem:
        _say(notice, title, f'the official pins file is {problem}: NO official pin fill is applied this run (fail closed); the build goes on', loud=True)
        return P
    pre = f'{area}-'
    mine = {ref: r for ref, r in ready.items() if ref.startswith(pre)}
    if not mine:
        _say(notice, title, 'no ready pin fill for this key in the official pins file')
        return P
    done, kept, other, held = {}, [], [], []
    for ref, r in sorted(mine.items()):
        if ref in HELD: held.append(f'{ref} ({HELD[ref]})'); continue
        if r is None: other.append(f'{ref} (two ready rows: not used)'); continue
        x = P.get(ref)
        if x is None: other.append(f'{ref} (not in the POTA park list)'); continue
        pin = (x[5], x[6]) if isinstance(x, (list, tuple)) and len(x) > 6 else None
        why = KF.pin_why(pin)
        if not why: kept.append(ref); continue                      # POTA has a usable pin: it is never moved
        if why not in FILLABLE: other.append(f'{ref} (POTA pin is {why}: never moved, a person checks)'); continue
        c = _coord(r)
        if c is None: other.append(f'{ref} (the official coordinate is not usable)'); continue
        row = list(x) if len(x) > 6 else list(x) + [None] * (7 - len(x))
        row[5], row[6] = c
        done[ref] = (row, r, why)
    if held: _say(notice, title, f"{len(held)} fill(s) HELD by the owner, not applied (POTA's pin stays): {'; '.join(held)}")
    if kept: _say(notice, title, f"{len(kept)} fill(s) IGNORED, POTA now has a usable pin (a fill never moves a pin): {' '.join(kept)}")
    if other: _say(notice, title, f"{len(other)} fill(s) not applied: {'; '.join(other)}", loud=True)
    if not done:
        _say(notice, title, f'0 of {len(mine)} ready fill(s) applied')
        return P
    out = Filled(P)
    for ref, (row, _r, _w) in done.items(): out[ref] = row
    out.pota, out.fills = P, {ref: (r, w) for ref, (_row, r, w) in done.items()}
    _say(notice, title, f"{len(done)} of {len(mine)} ready fill(s) applied (POTA has no usable pin; the official pin is used to join, POTA's list is unchanged): {' '.join(sorted(done))}")
    return out


def mark(parks, P, pins=None):
    """Mark the filled parks ('pf') and give POTA's pins back. Returns POTA's own park list (P itself when nothing was filled)."""
    if not isinstance(P, Filled) or not P.fills: return P
    for ref, (r, why) in sorted(P.fills.items()):
        pk = parks.get(ref)
        if isinstance(pk, dict):
            la, lo = P[ref][5], P[ref][6]
            pk['pf'] = {'la': la, 'lo': lo, 'why': WHY, 'src': str(r.get('source_name') or ''), 'url': str(r.get('source_url') or ''),
                        'conf': str(r.get('confidence') or ''), 'pota': why}
        if pins is not None and ref in pins:
            x = P.pota.get(ref)
            pins[ref] = (x[5], x[6]) if isinstance(x, (list, tuple)) and len(x) > 6 else (None, None)
    return P.pota


if __name__ == '__main__':   # a dry look at the file: python3 kpc_pin_fill.py [file]
    rows, prob = load(sys.argv[1] if len(sys.argv) > 1 else None)
    if prob: print('not read:', prob); sys.exit(1)
    by = {}
    for ref in rows: by.setdefault(ref.split('-')[0], []).append(ref)
    print(json.dumps({k: sorted(v) for k, v in sorted(by.items())}, indent=1))
