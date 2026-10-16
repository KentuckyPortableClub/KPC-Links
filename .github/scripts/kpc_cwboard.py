"""CW Challenge Leaderboard: copies the 'KPC CW Challenge Leaderboard' form answers into kpc-cw-board.json.
Needs the GitHub secret KPC_CWBOARD_CSV (the answer sheet's "Publish to web" CSV link).

A score shows when Approved says YES, or when Approved is EMPTY and: the call is a club member / pre-approved or a
real licensed call, the week is this week or last week (when it was sent), and the numbers look possible.
Best score per call per week per challenge. The last 8 weeks are kept."""
import os, re, sys, datetime
sys.path.insert(0, os.path.dirname(__file__))
import kpc_formtools as T, kpc_preapproved as PA

URL = os.environ.get('KPC_CWBOARD_CSV', '').strip()
OUT = 'kpc-cw-board.json'
N = lambda m: T.notice('CW Leaderboard', m)
if not URL: N('KPC_CWBOARD_CSV secret not set yet; nothing to do.'); sys.exit(0)
H, rows = T.sheet(URL)
PRE = PA.load()
c = lambda name: T.col(H, name)
C = dict(ts=c('Timestamp'), call=c('Call sign'), kind=c('Which challenge?'), wk=c('Week'), pts=c('Points'), wpm=c('Top WPM'), app=c('Approved'))
if C['call'] is None: N('The sheet has no "Call sign" column; is this the right CSV link?'); sys.exit(0)
wkid = lambda d: '%d-W%02d' % d.isocalendar()[:2]
today = datetime.date.today()
keep = {wkid(today - datetime.timedelta(weeks=i)) for i in range(8)}
best, waiting = {}, 0
for r in rows:
    g = lambda k: T.cell(r, C[k])
    ap = T.approval(g('app'))
    if ap == 'no': continue
    call = T.base(g('call')); wk = g('wk').upper().strip()
    if not call or not re.fullmatch(r'20\d\d-W\d\d', wk) or wk not in keep: continue
    kind = 'gauntlet' if 'gauntlet' in g('kind').lower() else 'copy'
    try: pts, wpm = int(float(g('pts'))), int(float(g('wpm')))
    except ValueError: continue
    sent = T.sheet_date(g('ts')) or today
    if ap != 'yes':
        ok = (call in PRE or T.real_call(call) is True) and wk in (wkid(sent), wkid(sent - datetime.timedelta(weeks=1)))
        ok = ok and (0 <= pts <= 3000 and 0 <= wpm <= 5 if kind == 'gauntlet' else 0 <= pts <= 20000 and 5 <= wpm <= 70)   # Gauntlet: 'Top WPM' carries the round reached
        if not ok: waiting += 1; continue
    k = (wk, kind, call)
    if k not in best or pts > best[k]['pts']:
        best[k] = {'call': call, 'pts': pts, 'wpm': wpm, 'date': sent.isoformat()}
weeks = {}
for (wk, kind, _), v in best.items():
    weeks.setdefault(wk, {'copy': [], 'gauntlet': []})[kind].append(v)
for w in weeks.values():
    for k in w: w[k].sort(key=lambda v: (-v['pts'], -v['wpm'], v['date']))
T.save_cache()
T.write_if_changed(OUT, {'updated': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%MZ'), 'weeks': dict(sorted(weeks.items(), reverse=True))}, 'weeks')
N(f'{len(best)} score(s) on the leaderboard ({len(weeks)} week(s)); {waiting} waiting for YES in the Approved column.')
