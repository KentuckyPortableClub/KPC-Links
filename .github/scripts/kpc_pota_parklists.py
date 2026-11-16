#!/usr/bin/env python3
"""THE ONE PARK-LIST JOB (KPC owner, 2026-11-16, handoff item 7). Once a day: reads POTA's /locations and saves it; re-pulls a US
state's or Canadian province's park list ONLY when POTA's own park count for it (in /locations) changed since the saved list;
world lists once a week, on the weekly world day (a few days before the world key check). Everything goes through kpc_pota_door
(paced 2 s, per-run budget, club User-Agent) into data/pota/saved/ (locations.json, parks/<loc>.json.gz).
For a re-pulled US / CA list it also reads the details (/park/<ref>, kept 30 days) of parks that are new in it, so the readers
(state_links) find them in the saved copy.

world_pota, canada, northam, new_refs, pota_activity, state_links, top25, refcheck and new_lands read the saved copy only.

Settings: .github/pota-parklists.json {"world_weekday": "Wed", "world_before_monthly_check_days": 3, "home_list_max_days": 7, "minutes": 95}
  (the world key check runs on the 3rd of each month; the world lists are also re-pulled that many days before it; a world list
  not reached on its day (time / budget) is pulled on the next nights; POTA's /locations rows carry NO park count today, so until
  they do a US / CA list is re-pulled after home_list_max_days - the owner decides)
  python3 .github/scripts/kpc_pota_parklists.py [--world] [--dry-run]
Env: KPC_POTA_BUDGET (default here 4500: /locations lists about 4,000 places), KPC_PARKLIST_MINUTES."""
import argparse, datetime as dt, json, os, pathlib, sys, time
os.environ.setdefault('KPC_POTA_BUDGET', '4500')
import kpc_net_guard; kpc_net_guard.install()
import kpc_pota_door as DOOR

SETTINGS = pathlib.Path('.github/pota-parklists.json')
DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']


KEEP_DETAILS = ('US-0121',)   # Kure Atoll: in POTA's park data but in no /location/parks list (kpc_state_links.py MISSED)

def settings():
    try: return json.loads(SETTINGS.read_text(encoding='utf-8'))
    except (OSError, ValueError): return {}


def world_day(today, cfg):
    """True on the weekly world weekday, and on the day N days before the monthly world key check (the 3rd)."""
    wd = str(cfg.get('world_weekday') or 'Wed')[:3].title()
    if DAYS[today.weekday()] == wd: return True
    n = int(cfg.get('world_before_monthly_check_days') or 3)
    nxt = (today.replace(day=1) + dt.timedelta(days=32)).replace(day=3) if today.day >= 3 else today.replace(day=3)
    return (nxt - today).days == n


def due(loc, loc_row, now, wday, cfg):
    """Is this location's saved park list due for a re-pull? (True, why) / (False, '')."""
    saved, cnt = DOOR.saved_list_info(loc)
    if saved is None: return True, 'no saved copy'
    age = (now - saved) / DOOR.DAY
    if str(loc).startswith(('US-', 'CA-')):
        pc = DOOR.park_count(loc_row)
        if pc is not None: return (pc != cnt, f'POTA count {cnt} -> {pc}') if pc != cnt else (False, '')
        # POTA's /locations rows carry no park count today (checked Nov 16): until they do, the list is re-pulled after
        # home_list_max_days (an owner setting), so a new park still arrives
        n = float(cfg.get('home_list_max_days') or 7)
        return (age >= n, f'no count in /locations; {age:.0f} days old') if age >= n else (False, '')
    if (wday and age >= 6) or age >= 8: return True, f'world list {age:.0f} days old'
    return False, ''


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument('--world', action='store_true', help='pull the world lists today (by hand)')
    ap.add_argument('--dry-run', action='store_true'); a = ap.parse_args(argv)
    today = dt.date.today(); cfg = settings(); wday = a.world or world_day(today, cfg)
    stop = time.time() + 60 * float(os.environ.get('KPC_PARKLIST_MINUTES') or cfg.get('minutes') or 95)
    if a.dry_run:
        print(f'park-list job {today}: world day {wday}; budget {DOOR.BUDGET}'); return 0
    try: locs, pulled = DOOR.fetch_locations()
    except DOOR.DoorClosed as e:
        print(f'::warning title=POTA park lists::/locations not read ({e}); every saved list stays'); return 1
    now = time.time(); done, kept, failed, details, why_n, left = [], 0, [], 0, {}, 0
    rows_by = sorted(locs, key=lambda x: (not str(x.get('locationDesc') or '').startswith(('US-', 'CA-')), str(x.get('locationDesc') or '')))   # home lists first
    for l in rows_by:
        loc = str(l.get('locationDesc') or '')
        if not loc: continue
        is_due, why = due(loc, l, now, wday, cfg)
        if not is_due: kept += 1; continue
        if time.time() > stop or DOOR.STAT['asked'] >= DOOR.BUDGET: left += 1; continue
        old = DOOR._read(DOOR.root() / 'parks' / f'{loc}.json.gz') or {}
        try: rows, got = DOOR.fetch_park_list(loc, DOOR.park_count(l), due=True)
        except DOOR.DoorClosed: failed.append(loc); continue
        done.append(loc); why_n[why.split(' ')[0]] = why_n.get(why.split(' ')[0], 0) + 1
        if loc.startswith(('US-', 'CA-')) and old:
            was = {str(r.get('reference')) for r in (old.get('data') or []) if isinstance(r, dict)}
            for r in rows or []:
                ref = str(r.get('reference') or '') if isinstance(r, dict) else ''
                if ref and ref not in was:
                    try: DOOR.park(ref); details += 1
                    except DOOR.DoorClosed: break
    for ref in KEEP_DETAILS:   # in no park list, so the readers' saved copy comes from here (one read per 30 days)
        try: DOOR.park(ref)
        except DOOR.DoorClosed: pass
    print(f"::notice title=POTA park lists::{today}: /locations {'read' if pulled else 'stored copy'}; {len(done)} list(s) re-pulled"
          f" ({', '.join(done[:12])}{' ...' if len(done) > 12 else ''}); {kept} not due; {left} due but left for the next run (time or budget);"
          f" {len(failed)} not read; {details} new park detail(s); world day {wday}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
