"""POTA pin guard for the nightly pin updaters (kpc_canada.py, kpc_northam.py, kpc_world_pota.py, kpc_search_lists.py).

The club never moves a POTA pin: the pin on the site is the pin api.pota.app gave. Two things can still go wrong between POTA's answer
and the file on the site, and this module is the one place that handles both:

  1. POTA CHANGES a park's coordinates. The new pin is published (it follows POTA), but the change is RECORDED in
     data/pota-pin-changes.json (old -> new, km, date, source), and a move of more than FLAG_KM is marked 'check' so a person sees it:
     the key joins, 2-fers and outline grades that were made with the old pin are not redone by themselves.
  2. POTA sends something that cannot be a pin (no number, 0,0, latitude past 90 / longitude past 180, NaN, or the old pin with
     latitude and longitude swapped). The LAST GOOD pin stays published and the glitch is recorded as 'kept-last-good'. A park that
     never had a good pin is left to the caller (what it did before this module), because the key marks those itself
     (pin00 / pinbad / nopin in kpc_key_facts.py, kpc_precheck.bad_pin).

decide() returns (pin, event). The pin is what to publish, or None when POTA's value is unusable and there is no earlier pin.
Impossible = the same test as kpc_precheck.bad_pin plus NaN and the swap; it is NOT a distance test: a possible pin always wins,
however far it moved, and a far move is only flagged (FLAG_KM / BIG_KM come from what the key code already uses: the ~1 km
'pin inside' slack of the rough outline copy, and the 15 km 'pin far from its record' prune in kpc_us_key.py).

No network. Tests: tests/test_pota_pin_guard_nov11.py."""
import datetime
import json
import math
import pathlib

LOG = pathlib.Path('data/pota-pin-changes.json')
SAME_DEG = 0.000005     # below one storage step (5 decimals is about 1.1 m): the same pin
FLAG_KM = 1.0           # a move past this is marked 'check' (the outline copy the key matches on is rough to about 1 km)
BIG_KM = 15.0           # a move past this is marked 'big' (the key drops a join whose record is farther than this from the pin)
KEEP_DAYS = 120
KEEP_MAX = 600
NOTE = ("POTA pins that changed upstream or that POTA sent unusable, noticed by the nightly pin bots. The site follows POTA's pin; a "
        "'check' or 'big' move, or a 'kept-last-good', is for a person. See .github/scripts/kpc_pin_guard.py.")


def _num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(v) or math.isinf(v) else v


def problem(la, lo):
    """'' for a usable pin, else why not. Same tests as kpc_precheck.bad_pin (plus NaN)."""
    a, b = _num(la), _num(lo)
    if a is None or b is None:
        return 'no usable coordinates'
    if a == 0 and b == 0:
        return '0,0 pin'
    if not (-90 <= a <= 90 and -180 <= b <= 180):
        return f'impossible pin {a},{b}'
    return ''


def km_between(a, b):
    """Great-circle km between two (lat, lon) pairs."""
    p1, p2 = math.radians(a[0]), math.radians(b[0])
    dp, dl = p2 - p1, math.radians(b[1] - a[1])
    h = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * 6371.0088 * math.asin(min(1.0, math.sqrt(h)))


def _swapped(old, new):
    """True when the new pin is the old pin with latitude and longitude exchanged (and that is not the same place)."""
    if abs(old[0] - old[1]) < 0.01:
        return False
    return abs(new[0] - old[1]) < 0.001 and abs(new[1] - old[0]) < 0.001


def _event(ref, name, kind, old, new, why, src, today, km=None, flag=''):
    return {'ref': ref, 'name': name or '', 'kind': kind, 'old': list(old) if old else None, 'new': list(new) if new else None,
            'km': None if km is None else round(km, 3), 'why': why, 'src': src, 'date': today, 'flag': flag}


def decide(ref, old, new, src, name='', today=None):
    """old = the pin now on the site (lat, lon) or None; new = what POTA gave today (lat, lon, may be None / junk).
    Returns (pin_to_publish_or_None, event_or_None)."""
    today = today or datetime.date.today().isoformat()
    old_ok = bool(old) and not problem(old[0], old[1])
    why = problem(*new) if new else 'no usable coordinates'
    if not why and old_ok and _swapped((float(old[0]), float(old[1])), (float(new[0]), float(new[1]))):
        why = 'latitude and longitude look swapped (the new pin is the old pin turned around)'
    if why:
        if old_ok:
            return (float(old[0]), float(old[1])), _event(ref, name, 'kept-last-good', old, new, 'POTA sent ' + why + ': last good pin kept', src, today, flag='check')
        return None, None
    new = (float(new[0]), float(new[1]))
    if not old_ok:
        return new, None
    o = (float(old[0]), float(old[1]))
    if abs(o[0] - new[0]) <= SAME_DEG and abs(o[1] - new[1]) <= SAME_DEG:
        return new, None
    d = km_between(o, new)
    flag = 'big' if d > BIG_KM else 'check' if d > FLAG_KM else ''
    return new, _event(ref, name, 'moved', o, new, f'POTA moved the pin {d:.3f} km; the site follows POTA', src, today, km=d, flag=flag)


def club_pin_event(ref, club, pota, src, name='', today=None):
    """A club-kept pin (Kentucky's kpc-ky-data.json) wins over POTA's on the search list; when the two differ, say so.
    club / pota = (lat, lon). Returns an event or None."""
    today = today or datetime.date.today().isoformat()
    if not club or not pota or problem(*pota) or problem(*club):
        return None
    c, p = (float(club[0]), float(club[1])), (float(pota[0]), float(pota[1]))
    if abs(c[0] - p[0]) <= SAME_DEG and abs(c[1] - p[1]) <= SAME_DEG:
        return None
    d = km_between(c, p)
    flag = 'big' if d > BIG_KM else 'check' if d > FLAG_KM else ''
    return _event(ref, name, 'club-pin-differs', c, p, f"the site shows the club's own pin; POTA's pin is {d:.3f} km away (old = site, new = POTA)", src, today, km=d, flag=flag)


def record(events, path=None, today=None, say=print):
    """Add events to the log (no duplicates of an event already on file, entries older than KEEP_DAYS dropped). Writes only when the
    content changed. Returns the number of NEW events. Prints one notice, and one warning when a person should look."""
    path = pathlib.Path(path) if path else LOG
    today = today or datetime.date.today().isoformat()
    try:
        d = json.loads(path.read_text(encoding='utf-8'))
        ev = d.get('events') if isinstance(d, dict) and isinstance(d.get('events'), list) else []
    except (OSError, ValueError):
        ev = []
    cut = (datetime.date.fromisoformat(today) - datetime.timedelta(days=KEEP_DAYS)).isoformat()
    ev = [e for e in ev if isinstance(e, dict) and str(e.get('date', today)) >= cut]
    seen = {(e.get('ref'), e.get('kind'), json.dumps(e.get('new')), json.dumps(e.get('old'))) for e in ev}
    fresh = []
    for e in events or []:
        k = (e['ref'], e['kind'], json.dumps(e['new']), json.dumps(e['old']))
        if k not in seen:
            seen.add(k)
            fresh.append(e)
    if fresh:
        ev = (fresh + ev)[:KEEP_MAX]
        out = {'note': NOTE, 'events': ev}
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            from kpc_save import save_json
            save_json(str(path), out)
        except Exception:  # noqa: BLE001   (kpc_save only adds the status file; the log itself must still be written)
            path.write_text(json.dumps(out, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n', encoding='utf-8')
        n_check = [e for e in fresh if e['flag'] or e['kind'] == 'kept-last-good']
        say(f"::notice title=POTA pin changes::{len(fresh)} recorded in {path.name} ({sum(1 for e in fresh if e['kind'] == 'moved')} moved, "
            f"{sum(1 for e in fresh if e['kind'] == 'kept-last-good')} unusable pin(s) from POTA: last good pin kept, "
            f"{sum(1 for e in fresh if e['kind'] == 'club-pin-differs')} club pin(s) differ from POTA's)")
        if n_check:
            say('::warning title=POTA pin check::a person should look at: ' + ', '.join(
                f"{e['ref']} ({e['kind']}{', %.1f km' % e['km'] if e['km'] is not None else ''})" for e in n_check[:12]) + (' ...' if len(n_check) > 12 else ''))
    return len(fresh)
