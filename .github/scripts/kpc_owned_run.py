#!/usr/bin/env python3
"""kpc_owned_run.py (Nov 11 2026, host rules, review package A): the safe way kpc-owned.yml runs the owned-land files.

kpc_owned.py is a 2-fer rule file (kpc_key_freeze.RULE_FILES['fers']), so it is not edited here. This runner:
  1. installs kpc_net_guard BEFORE kpc_owned is imported (kpc_owned also gets it through kpc_http_cache; this makes it explicit),
  2. checks, before any request, every map the chosen job reads. A map on a host the bots may never contact (services*.arcgis.com,
     apps.fs.usda.gov, ...) is read only from the saved copy: the HTTP_CACHE bundle (kpc_http_cache.py; a saved-copy-only host's kept
     answer is used whatever its age). No bundle = the job is NOT run: no request of any kind, robots.txt included,
  3. then keeps the last good file exactly as it is and says so where a person looks: a '::warning' in the log, a line in the step
     summary, and data/status/kpc_owned.json (blocked maps, the date the kept file was read = 'stale since', and a needs-download
     row in the KPC-Data list's schema for the layer a person must download).
Green with a visible note, not red: the kept file is still the agency's own data (its content is dated 2015) and the one thing a
person can do (download the layer in a browser for the saved copy) is listed on the needs-download row; a red run every month would
only repeat that. 'Did not answer' (an allowed map that failed) and 'blocked' (a host the rules forbid) are told apart.
  python3 .github/scripts/kpc_owned_run.py ky         (what kpc-owned.yml runs; same argument as kpc_owned.py)
"""
import datetime as dt, json, os, pathlib, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kpc_net_guard  # noqa: E402
kpc_net_guard.install()   # before kpc_owned / kpc_http_cache are imported: no request can go out unguarded
import kpc_http_cache as HC  # noqa: E402
import kpc_owned as KO  # noqa: E402

STATUS = pathlib.Path(os.environ.get('KPC_OWNED_STATUS') or 'data/status/kpc_owned.json')
# job -> (file it writes, area, the maps it reads: (label, layer url))
JOBS = {'ky': ('ky-dbnf-owned.geojson', 'US-KY',
               [('Forest Service Basic Ownership (EDW_BasicOwnership_02, layer 0)', KO.FSBO)])}


def say(kind, msg):
    print(f'::{kind} title=Owned land::{msg}', flush=True)
    if os.environ.get('GITHUB_STEP_SUMMARY'):
        try: open(os.environ['GITHUB_STEP_SUMMARY'], 'a', encoding='utf-8').write(f'**Owned land ({kind}):** {msg}\n')
        except Exception: pass  # noqa: BLE001


def saved_copy():
    """True when the HTTP_CACHE bundle (the saved answers) is there to read a saved-copy-only map from."""
    d = HC.DIR and pathlib.Path(HC.DIR)
    return bool(d and d.is_dir() and any(d.rglob('*.json.gz')))


def kept_date(path):
    try: return (json.load(open(path, encoding='utf-8')) or {}).get('read') or ''
    except Exception: return ''  # noqa: BLE001


def needs_row(area, label, url, why, have_date):
    """One row in the needs-download schema (KPC-Data data/needs-download.json, KPC-Links kpc_master.NEEDS_FIELDS)."""
    return {'id': f'{area}|owned:{kpc_net_guard.host_of(url)}', 'area': area, 'layer': f'owned:{label}', 'url': url, 'page': url,
            'host': kpc_net_guard.host_of(url), 'who': 'person', 'why': why + ': a person downloads it in a browser for the saved copy',
            'expected': None, 'have': f'kept file read {have_date}' if have_date else None, 'source': 'owned land (kpc_owned_run.py)',
            'added': dt.date.today().isoformat(), 'status': 'open', 'note': '', 'src': '', 'check': 'person'}


def write_status(job, out, state, blocked, why_not_read=''):
    old = {}
    try: old = json.load(open(STATUS, encoding='utf-8'))
    except Exception: pass  # noqa: BLE001
    have = kept_date(out)
    row = {'job': job, 'file': out, 'state': state, 'kept_file_read': have or None,
           'stale_since': (have or 'unknown') if state != 'fresh' else None,
           'blocked': [{'map': lb, 'url': u, 'why': w} for lb, u, w in blocked],
           'not_read': why_not_read or None,
           'needs': [needs_row(JOBS[job][1], lb, u, w, have) for lb, u, w in blocked]}
    doc = {'about': 'Owned-land maps the last run could not read (kpc_owned_run.py). blocked = a host the bots may never contact: the '
                    'saved copy only; not_read = an allowed map that did not answer. The file named here was kept as it was.',
           'jobs': dict(old.get('jobs') or {}, **{job: row})}
    if old.get('jobs', {}).get(job, {}) != row:   # the same note again = nothing to save
        STATUS.parent.mkdir(parents=True, exist_ok=True)
        STATUS.write_text(json.dumps(doc, indent=1, ensure_ascii=False, sort_keys=True) + '\n', encoding='utf-8')


def run(job):
    if job not in JOBS:
        say('notice', f'{job}: no such job (known: {", ".join(JOBS)}); nothing done'); return 0
    out, area, maps = JOBS[job]
    have = kept_date(out) or 'unknown'
    blocked = [(lb, u, kpc_net_guard.host_ok(u)[1]) for lb, u in maps if not kpc_net_guard.host_ok(u)[0]]
    if blocked and not saved_copy():
        for lb, u, why in blocked:
            say('warning', f'{job}: BLOCKED, not read: {lb} ({why}). No saved copy (HTTP_CACHE bundle) here, so nothing was asked; '
                           f'{out} is kept as it is, STALE since {have} (the date it was read). A needs-download row is in {STATUS}.')
        write_status(job, out, 'blocked', blocked)
        return 0
    if blocked:
        os.environ['HTTP_OFFLINE'] = '1'; HC.OFFLINE = True   # a saved-copy-only map comes from the bundle only, never live
    before = time.time()
    ok = KO.ky_dbnf(out) if job == 'ky' else False
    if ok:
        write_status(job, out, 'fresh', [])
        return 0
    why = '; '.join(KO.LOG[:3]) or 'no answer'
    refused = [x for x in KO.LOG if 'saved copies only' in x or 'never contacted' in x or 'not in the bundle' in x]
    if blocked or refused:
        say('warning', f'{job}: the saved copy did not hold every answer ({why}); {out} is kept as it is, STALE since {have}')
        write_status(job, out, 'blocked', blocked or [(lb, u, why) for lb, u in maps], why)
    else:
        say('warning', f'{job}: a map did not answer or read short ({why}; {round(time.time() - before)} s); {out} is kept as it is, '
                       f'STALE since {have}. The next run tries again.')
        write_status(job, out, 'not read', [], why)
    return 0


if __name__ == '__main__':
    try: rc = run((sys.argv[1:] or ['ky'])[0])
    except Exception as e:  # noqa: BLE001
        say('warning', f'stopped: {type(e).__name__}: {str(e)[:200]}; the last file stays'); rc = 0
    sys.exit(rc)
