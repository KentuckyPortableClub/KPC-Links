"""Nov 4 PM fix bundle item 11b (Quality should-fix; Brandon's yes relayed via Super Head Bot 4:53 PM CST): QUEUED pre-check re-runs.

data/status/key-check/precheck-queue.json lists re-runs that wait for a key file to be rebuilt. The first one: 'Re-run the
pre-check after the German rebuild' (health check Nov 4 PM, Quality follow-ups). It needs NO cron and starts nothing: the key
check (kpc-key-postcheck.yml) already re-runs the pre-check after every key build (workflow_run); this script, run in that job
right after the pre-check, looks at each WAITING entry and, once the entry's key file (data/world-key/DE.json) was last built in
'from_commit' or a later commit (AT OR AFTER; Brandon, relayed via Super Head Bot 5:36 PM CST Nov 4: the 3:24 PM CST German
build ddd815b34 counts as the real rebuild) - or, for an entry with 'after_commit' instead, a commit strictly AFTER it - keeps that run's pre-check result for the area under data/status/key-check/precheck-queue/<id>/
(counts.json + the area's review-pile / bad-pin rows) and marks the entry DONE with the build commit and time. A pre-check that
did not finish (no counts.json, or status red) leaves the entry WAITING with the reason. Read-only apart from those files; no web
request; never fails the job. Run: KEY=world PRECHECK_OUT=/tmp/kpc-precheck python3 .github/scripts/kpc_precheck_queue.py"""
import csv, json, os, pathlib, subprocess, sys, time

Q = pathlib.Path(os.environ.get('PRECHECK_QUEUE') or 'data/status/key-check/precheck-queue.json')
OUT = pathlib.Path(os.environ.get('PRECHECK_OUT') or '/tmp/kpc-precheck')


def git(*a):
    p = subprocess.run(['git', *a], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else None


def newer(after, last, same_ok=False):
    """Is build commit `last` a later commit than `after` (after is its ancestor)? same_ok: the same commit counts too."""
    if not last or not after: return False
    a, b = git('rev-parse', after), git('rev-parse', last)
    if not a or not b: return False
    if a == b: return same_ok
    return subprocess.run(['git', 'merge-base', '--is-ancestor', a, b], capture_output=True).returncode == 0


def rows(name, area):
    f = OUT / name
    if not f.exists(): return None, []
    with open(f, newline='', encoding='utf-8') as fh:
        r = list(csv.reader(fh))
    if not r: return None, []
    return r[0], [x for x in r[1:] if x and (x[0].startswith(area + '-') or (len(x) > 1 and x[1] == area))]


def main():
    if not Q.exists(): print('precheck queue: no queue file'); return 0
    q = json.load(open(Q, encoding='utf-8')); now = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime()); changed = False
    for e in q.get('queue', []):
        if e.get('state') != 'waiting': continue
        last = git('log', '-1', '--format=%H', '--', e['key_file'])
        frm = e.get('from_commit'); ref = frm or e.get('after_commit')
        if not newer(ref, last, same_ok=bool(frm)):
            print(f"precheck queue {e['id']}: still waiting ({e['key_file']} last built in {str(last)[:9] or '?'}, needs a build {'at or after' if frm else 'after'} {ref})"); continue
        try: c = json.load(open(OUT / 'counts.json', encoding='utf-8'))
        except Exception as x:  # noqa: BLE001
            e['last_try'] = f'{now}: the pre-check of this run did not finish ({str(x)[:80]}); waits for the next key build'; changed = True
            print(f"::warning title=Pre-check queue::{e['id']}: the pre-check did not finish; the entry waits"); continue
        if str(c.get('status', '')).lower() == 'red':
            e['last_try'] = f'{now}: the pre-check of this run was red; waits for the next key build'; changed = True
            print(f"::warning title=Pre-check queue::{e['id']}: the pre-check was red; the entry waits"); continue
        d = Q.parent / 'precheck-queue' / e['id']; d.mkdir(parents=True, exist_ok=True)
        json.dump(c, open(d / 'counts.json', 'w', encoding='utf-8'), indent=1)
        kept = {}
        for name in ('review-pile.csv', 'BAD_POTA_PIN_FLAGS.csv'):
            h, rs = rows(name, e['area'])
            if h is None: continue
            with open(d / name.replace('.csv', f"-{e['area']}.csv"), 'w', newline='', encoding='utf-8') as fh:
                w = csv.writer(fh); w.writerow(h); w.writerows(rs)
            kept[name] = len(rs)
        e.update(state='done', done=now, build_commit=last[:12], kept=kept, run=os.environ.get('RUN_URL', ''))
        changed = True
        print(f"::notice title=Pre-check queue::{e['id']}: pre-check re-run kept for {e['area']} after build {last[:9]} ({kept})")
    if changed: json.dump(q, open(Q, 'w', encoding='utf-8'), indent=1, ensure_ascii=False); open(Q, 'a').write('\n')
    return 0


if __name__ == '__main__':
    try: sys.exit(main())
    except Exception as x:  # noqa: BLE001
        print(f'::warning title=Pre-check queue::stopped: {str(x)[:200]}'); sys.exit(0)
