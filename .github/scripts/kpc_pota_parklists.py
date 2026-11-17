#!/usr/bin/env python3
"""THE ONE PARK-LIST JOB (KPC owner, 2026-11-16, handoff item 7; v4 answers 2 and 3). Once a day:
  1. ONE request: POTA's all-parks export (all_parks_ext.csv: reference, name, active, entityId, locationDesc, latitude, longitude,
     grid), conditional on yesterday's ETag. It is compared with yesterday's saved copy (data/pota/saved/export-index.json); the
     difference names the ROWS that changed (v5: added, retired by the `active` column, changed name / pin / grid, gone; in
     data/pota/saved/export-changes.json), and only the saved lists of the locations holding them are rewritten, from the export
     itself (kpc_pota_door.sync_export). It replaces the 7-day re-pull. /locations is not used.
  2. /location/parks/<loc> ONLY for a location with NEW park rows (a retired, renamed or moved row keeps its counts), and only
     when a job needs a field the export lacks (activations,
     attempts, qsos, parktypeDesc: state_links, top25, state_leaders, KPC-Data pota_activity). US and CA locations: the day they
     change (and once, for a list that never had those fields). World locations: on the weekly world day only (a few days before the
     world key check). At most max_lists_per_run a run; the rest wait in the queue (export-index.json extra_due).
  3. Details (/park/<ref>, kept 30 days) of parks NEW in a changed US / CA location, at most max_details_per_run a run.
If the export is gone or too thin, the job says so and falls back to a 7-day re-pull of the US / CA lists (home_list_max_days).
Receipt with the real numbers: data/pota/saved/receipts/parklists.json.

world_pota, canada, northam, new_refs, pota_activity, state_links, top25, refcheck and new_lands read the saved copy only.

Settings: .github/pota-parklists.json
  python3 .github/scripts/kpc_pota_parklists.py [--world] [--dry-run]
Env: KPC_POTA_BUDGET (default here 80), KPC_PARKLIST_MINUTES."""
import argparse, datetime as dt, fnmatch, json, os, pathlib, sys, time
os.environ.setdefault('KPC_POTA_BUDGET', '80')
import kpc_net_guard; kpc_net_guard.install()
import kpc_pota_door as DOOR

SETTINGS = pathlib.Path('.github/pota-parklists.json')
DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
KEEP_DETAILS = ('US-0121',)   # Kure Atoll: in POTA's park data but in no location list (kpc_state_links.py MISSED)
HOME = ('US-', 'CA-')


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


def wants_extra(loc, cfg):
    pats = cfg.get('extra_fields_locations') or ['US-*', 'CA-*']
    if any(fnmatch.fnmatch(loc, p) for p in pats): return 'home'
    if any(fnmatch.fnmatch(loc, p) for p in (cfg.get('world_extra_locations') or [])): return 'world'
    return ''


def list_calls(idx, cfg, wday, stop):
    """The /location/parks calls of this run: queued changed locations (home any day, world on the world day), then home lists that
    never had the extra fields. Returns (done, left)."""
    cap = int(cfg.get('max_lists_per_run') or 20)
    queue = [l for l in idx.get('extra_due') or [] if wants_extra(l, cfg)]
    never = sorted(l for l in (idx.get('locations') or {}) if wants_extra(l, cfg) == 'home' and l not in queue and DOOR.saved_list_info(l)[3] is None)
    todo = [l for l in queue if wants_extra(l, cfg) == 'home'] + ([l for l in queue if wants_extra(l, cfg) == 'world'] if wday else []) + never
    done = []
    for loc in todo:
        if len(done) >= cap or time.time() > stop or DOOR.STAT['asked'] >= DOOR.BUDGET: break
        try: DOOR.fetch_park_list(loc); done.append(loc)
        except DOOR.DoorClosed: break
    idx['extra_due'] = sorted(set(idx.get('extra_due') or []) - set(done) - {l for l in idx.get('extra_due') or [] if not wants_extra(l, cfg)})
    return done, len([l for l in todo if l not in done])


def fallback(cfg, stop):
    """The export is gone or too thin: the US / CA saved lists older than home_list_max_days are re-pulled (7-day fallback)."""
    n, cap, done = float(cfg.get('home_list_max_days') or 7), int(cfg.get('max_lists_per_run') or 20), []
    try: locs = [str(l.get('locationDesc')) for l in DOOR.saved_locations()]
    except DOOR.DoorClosed: locs = []
    for loc in sorted(l for l in locs if l.startswith(HOME)):
        saved = DOOR.saved_list_info(loc)[0]
        if saved is not None and (time.time() - saved) / DOOR.DAY < n: continue
        if len(done) >= cap or time.time() > stop or DOOR.STAT['asked'] >= DOOR.BUDGET: break
        try: DOOR.fetch_park_list(loc); done.append(loc)
        except DOOR.DoorClosed: break
    return done


def main(argv=None):
    ap = argparse.ArgumentParser(); ap.add_argument('--world', action='store_true', help='make today a world day (by hand)')
    ap.add_argument('--dry-run', action='store_true'); a = ap.parse_args(argv)
    today = dt.date.today(); cfg = settings(); wday = a.world or world_day(today, cfg)
    stop = time.time() + 60 * float(os.environ.get('KPC_PARKLIST_MINUTES') or cfg.get('minutes') or 30)
    if a.dry_run:
        print(f'dry run: world day {wday}; budget {DOOR.BUDGET}; export {DOOR.EXPORT_URL}'); return 0
    rec = {'day': today.isoformat(), 'world_day': wday, 'mode': 'export'}
    try:
        r = DOOR.sync_export()
        rec['export'] = {k: (v[:60] if isinstance(v, list) else v) for k, v in r.items() if k != 'new_parks'}
        rec['export']['changed_count'] = len(r['changed'])
    except DOOR.ExportGone as e:
        rec['mode'] = 'fallback: 7-day re-pull'; rec['export_gone'] = str(e)
        print(f'::warning title=POTA park lists::the all-parks export is gone or too thin ({e}): falling back to the 7-day re-pull of the US / CA lists')
        rec['lists'] = fallback(cfg, stop)
        DOOR.write_receipt(rec, 'parklists'); return 0
    except DOOR.DoorClosed as e:
        print(f'::warning title=POTA park lists::the all-parks export was not read ({e}); every saved list stays')
        rec['mode'] = 'not read'; rec['error'] = str(e); DOOR.write_receipt(rec, 'parklists'); return 1
    idx = DOOR.export_index()
    done, left = list_calls(idx, cfg, wday, stop)
    DOOR._write(DOOR.root() / 'export-index.json', idx)
    details, dcap = 0, int(cfg.get('max_details_per_run') or 40)
    for loc, refs in sorted((r.get('new_parks') or {}).items()):
        if not loc.startswith(HOME): continue
        for ref in refs:
            if details >= dcap or time.time() > stop: break
            try: DOOR.park(ref); details += 1
            except DOOR.DoorClosed: break
    for ref in KEEP_DETAILS:   # in no location list, so the readers' saved copy comes from here (one read per 30 days)
        try: DOOR.park(ref)
        except DOOR.DoorClosed: pass
    rec.update(lists=done, lists_left_in_queue=left, new_park_details=details,
               expected_per_day={'spots': 288, 'export': 1, 'lists': f"locations with new park rows that need a field the export lacks, at most {cfg.get('max_lists_per_run') or 20} a run",
                                 'details_and_history': 'only when a stored copy is over 30 days old (and new parks)'})
    DOOR.write_receipt(rec, 'parklists')
    print(f"::notice title=POTA park lists::{today}: export {'unchanged (304)' if r.get('not_modified') else ('read' if r['asked'] else 'stored copy (under a day old)')}:"
          f" {r['parks']} parks in {r['locations']} locations; {len(r['changed'])} changed ({', '.join(r['changed'][:12])}{' ...' if len(r['changed']) > 12 else ''});"
          f" rows {r.get('rows') or {}}; {DOOR.STAT['asked']} POTA request(s);"
          f" {len(done)} location list(s) asked ({', '.join(done[:12])}); {left} left in the queue; {details} new park detail(s); world day {wday}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
