#!/usr/bin/env python3
"""WHEN ARE THE HUNTERS OUT? (Opus, Oct 23 2026; Brandon: 'Yeah sounds good and it will go to discord park info and
Facebook also?'). POTA does not publish when hunters are on, so we count it ourselves.

  collect  (every 15 min)  reads api.pota.app/spot/activator and counts, for each clock hour, the HUNTER spots on US
           parks (a spot posted by someone other than the activator = a hunter who just worked or heard them), how
           many activators were on, and the band. Only counts are kept (no call signs): data/hunters/buckets.json.
  build    (after collect) turns the last 8 weeks into kpc-hunters.json for the Happening Now card (an hour-by-day
           grid in Central time, the busiest windows, the best band in each) + app/hunters.json for the app's
           'Hunters are out' alert ({windows:[{days:[1-7], from, to, note}]}, 1 = Monday).
  post     (Fridays)       once there are 14+ days of counts: one post to Discord (park news) and the Facebook Page.
Every step exits 0: a POTA hiccup skips that run quietly (no email)."""
import datetime as dt
import json
import os
import pathlib
import re
import sys
import urllib.parse
import urllib.request
from zoneinfo import ZoneInfo

UA = 'KPC-Hunters/1.0 (+https://kentuckyportableclub.github.io/KPC-Links/)'
SITE = 'https://kentuckyportableclub.github.io/KPC-Links/'
B = pathlib.Path('data/hunters/buckets.json')
OUT, APP = pathlib.Path('kpc-hunters.json'), pathlib.Path('app/hunters.json')
CT = ZoneInfo('America/Chicago')
KEEP_DAYS, READY_DAYS = 56, 14
DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
DAYS_LONG = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
BANDS = [(1800, 2000, '160m'), (3500, 4000, '80m'), (5330, 5410, '60m'), (7000, 7300, '40m'), (10100, 10150, '30m'),
         (14000, 14350, '20m'), (18068, 18168, '17m'), (21000, 21450, '15m'), (24890, 24990, '12m'), (28000, 29700, '10m'),
         (50000, 54000, '6m'), (144000, 148000, '2m'), (420000, 450000, '70cm')]


def notice(t, m=''):
    print(f'::notice title={t}::' + str(m).replace('%', '%25').replace('\n', '%0A'), flush=True)


def band(khz):
    try:
        f = float(khz)
    except (TypeError, ValueError):
        return ''
    if f < 1000: f *= 1000          # some spots give MHz
    for lo, hi, n in BANDS:
        if lo <= f <= hi: return n
    return ''


def base(call):
    c = str(call or '').upper().strip()
    parts = [p for p in c.split('/') if p]
    return max(parts, key=len) if parts else ''


CLOSED = False   # did this run finish an hour (only then the saved files change)
W = pathlib.Path('data/hunters/work.json')   # the open hours + recent spot ids; kept in the Actions cache, not the repo


def _j(p, d):
    try:
        return json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return d


def load():
    return _j(B, {'since': '', 'b': {}})


def save(d):
    B.parent.mkdir(parents=True, exist_ok=True)
    B.write_text(json.dumps(d, separators=(',', ':'), sort_keys=True) + '\n', encoding='utf-8')


def _h(s):
    import hashlib
    return hashlib.sha1(s.encode()).hexdigest()[:8]


def collect():
    """Counts go to the hour of the poll. A spot is new when its spot id is new; when POTA gives a running 'count' per
    activation, its growth since the last poll is used instead (it also catches spots between two polls)."""
    try:
        req = urllib.request.Request('https://api.pota.app/spot/activator', headers={'User-Agent': UA, 'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=40) as r:
            spots = json.load(r)
        if not isinstance(spots, list): raise ValueError('not a list')
    except Exception as e:  # noqa: BLE001
        notice('Hunters', f'POTA spots not read this time ({e}); skipped'); return False
    first = not W.exists()   # no memory of the last poll (first run, or the cache was lost): learn the list, count nothing
    d, w = load(), _j(W, {'open': {}, 'ids': [], 'cnt': {}})
    now = dt.datetime.now(dt.timezone.utc)
    hour = now.strftime('%Y-%m-%dT%H')
    d['since'] = d.get('since') or now.date().isoformat()
    seen, cnt = set(w.get('ids', [])), w.get('cnt', {})
    o = w['open'].setdefault(hour, {'h': 0, 'a': [], 'bd': {}})
    new, used_count = 0, 0
    for s in spots:
        ref = str(s.get('reference') or '')
        if not ref.startswith('US-'): continue
        act = base(s.get('activator'))
        if not act: continue
        ak = _h(act + '|' + ref)
        if _h(act) not in o['a']: o['a'].append(_h(act))
        add = 0
        sid = str(s.get('spotId') or '')
        if sid and sid not in seen:
            seen.add(sid)
            if base(s.get('spotter')) and base(s.get('spotter')) != act: add = 1
        c = s.get('count')
        if isinstance(c, int):
            used_count += 1
            if ak in cnt and c > cnt[ak]: add = max(add, c - cnt[ak])
            cnt[ak] = c
        if add and not first:
            new += add; o['h'] += add
            bn = band(s.get('frequency'))
            if bn: o['bd'][bn] = o['bd'].get(bn, 0) + add
    # an hour that has ended moves into the saved counts (the only file committed: once an hour)
    global CLOSED
    for k in sorted(w['open']):
        if k < hour:
            v = w['open'].pop(k)
            d['b'][k] = {'h': v['h'], 'a': len(v['a']), 'bd': v['bd']}
            CLOSED = True
    cut = (now - dt.timedelta(days=KEEP_DAYS)).strftime('%Y-%m-%dT%H')
    d['b'] = {k: v for k, v in d['b'].items() if k >= cut}
    live = {_h(base(s.get('activator')) + '|' + str(s.get('reference') or '')) for s in spots}
    w['cnt'] = {k: v for k, v in cnt.items() if k in live}
    w['ids'] = sorted(seen)[-3000:]
    W.parent.mkdir(parents=True, exist_ok=True)
    W.write_text(json.dumps(w, separators=(',', ':')), encoding='utf-8')
    save(d)
    keys = sorted(spots[0].keys()) if spots else []
    notice('Hunters', f'{len(spots)} spots read, {new} new spots this poll; {len(d["b"])} hours saved since {d["since"]}; '
                      f'running count used for {used_count}; spot fields: {", ".join(keys)[:300]}')
    return True


def build():
    d = load()
    if not d.get('b'):
        notice('Hunters', 'nothing collected yet'); return None
    now = dt.datetime.now(dt.timezone.utc)
    grid = [[[] for _ in range(24)] for _ in range(7)]           # Central day x hour -> list of hunter spots per hour
    acts = [[[] for _ in range(24)] for _ in range(7)]
    bands = [[{} for _ in range(24)] for _ in range(7)]
    first = min(d['b'])
    days = set()
    # every clock hour from the first bucket to the last full hour counts, empty ones as 0
    t = dt.datetime.strptime(first, '%Y-%m-%dT%H').replace(tzinfo=dt.timezone.utc)
    end = now.replace(minute=0, second=0, microsecond=0)
    while t < end:
        k = t.strftime('%Y-%m-%dT%H'); v = d['b'].get(k, {'h': 0, 'a': 0, 'bd': {}})
        c = t.astimezone(CT); wd, hr = c.weekday(), c.hour
        grid[wd][hr].append(v['h']); acts[wd][hr].append(v['a']); days.add(c.date())
        for bn, n in v.get('bd', {}).items(): bands[wd][hr][bn] = bands[wd][hr].get(bn, 0) + n
        t += dt.timedelta(hours=1)
    avg = [[round(sum(x) / len(x), 1) if x else 0 for x in row] for row in grid]
    aact = [[round(sum(x) / len(x), 1) if x else 0 for x in row] for row in acts]
    ndays = len(days)
    # busiest window per day: the best 3-hour run between 6 AM and 11 PM Central
    win = []
    for wd in range(7):
        best = max(range(6, 21), key=lambda h: sum(avg[wd][h:h + 3]))
        tot = sum(avg[wd][best:best + 3])
        bb = {}
        for h in range(best, best + 3):
            for bn, n in bands[wd][h].items(): bb[bn] = bb.get(bn, 0) + n
        win.append({'day': wd + 1, 'from': f'{best:02d}:00', 'to': f'{best + 3:02d}:00', 'perHour': round(tot / 3, 1),
                    'band': max(bb, key=bb.get) if bb else ''})
    order = sorted(win, key=lambda w: -w['perHour'])
    # Oct 23 (Brandon: 'it is really not counting hunters more of when is pota activity busy?'): spots show when POTA
    # is busy. The activator's question is different: when do I get the most spots for being on the air? = spots per
    # activator (pooled over the 3 hours), only where at least 3 activators were on so a quiet hour can't win
    sp = [[sum(x) for x in row] for row in grid]; ac = [[sum(x) for x in row] for row in acts]
    odds = []
    for wd in range(7):
        ok = [h for h in range(6, 21) if sum(aact[wd][h:h + 3]) / 3 >= 3]
        if not ok: continue
        best = max(ok, key=lambda h: sum(sp[wd][h:h + 3]) / max(1, sum(ac[wd][h:h + 3])))
        odds.append({'day': wd + 1, 'from': f'{best:02d}:00', 'to': f'{best + 3:02d}:00',
                     'perAct': round(sum(sp[wd][best:best + 3]) / max(1, sum(ac[wd][best:best + 3])), 1)})
    odds.sort(key=lambda w: -w['perAct'])
    allb = {}
    for wd in range(7):
        for h in range(24):
            for bn, n in bands[wd][h].items(): allb[bn] = allb.get(bn, 0) + n
    tb = sum(allb.values()) or 1
    out = {'updated': now.isoformat(timespec='minutes'), 'since': d.get('since'), 'days': ndays, 'ready': ndays >= READY_DAYS,
           'tz': 'America/Chicago', 'what': 'Spots on US parks posted by someone other than the activator, per hour, averaged over the last 8 weeks. It shows when POTA is busiest, not a head count of hunters.',
           'grid': avg, 'activators': aact, 'windows': win, 'top': order[:3], 'odds': odds[:3],
           'bands': [[bn, round(100 * n / tb)] for bn, n in sorted(allb.items(), key=lambda x: -x[1])][:6]}
    OUT.write_text(json.dumps(out, separators=(',', ':')) + '\n', encoding='utf-8')
    if out['ready']:
        APP.parent.mkdir(parents=True, exist_ok=True)
        APP.write_text(json.dumps({'updated': out['updated'], 'note': 'Busiest POTA times, Central time, from KPC counts of POTA spots',
                                   'windows': [{'days': [w['day']], 'from': w['from'], 'to': w['to'],
                                                'note': f"POTA is at its busiest about now ({DAYS[w['day'] - 1]})" + (f", mostly on {w['band']}" if w['band'] else '')}
                                               for w in order[:4]]}, indent=1) + '\n', encoding='utf-8')
    notice('Hunters', f"{ndays} days counted; busiest: " + '; '.join(f"{DAYS[w['day'] - 1]} {w['from']}-{w['to']} ({w['perHour']}/h)" for w in order[:3]))
    return out


def fmt(h):
    h = int(h[:2]); return '12 PM' if h == 12 else (f'{h - 12} PM' if h > 12 else ('12 AM' if h in (0, 24) else f'{h} AM'))


def post():
    try:
        out = json.loads(OUT.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        notice('Hunters post', 'no counts file yet'); return
    if not out.get('ready'):
        notice('Hunters post', f"only {out.get('days', 0)} days counted; posting starts at {READY_DAYS}"); return
    top = out['top']
    wk = {w['day']: w for w in out['windows']}
    pick = top + [wk[d] for d in (6, 7) if d in wk and wk[d] not in top]     # the weekend days always listed
    lines = [f"• {DAYS_LONG[w['day'] - 1]} {fmt(w['from'])}–{fmt(w['to'])}" + (f" (mostly {w['band']})" if w['band'] else '') for w in pick]
    bands = ', '.join(f'{b} {p}%' for b, p in out.get('bands', [])[:3])
    odds = [f"• {DAYS_LONG[w['day'] - 1]} {fmt(w['from'])}–{fmt(w['to'])}" for w in out.get('odds', [])[:3]]
    title = '🏹 When is POTA busiest?'
    text = ('Heading to a park this weekend? The busiest POTA times on US parks over the last '
            f"{min(out['days'], KEEP_DAYS)} days (Central time):\n" + '\n'.join(lines) +
            ('\n\nBest odds for an activator (the most spots for each activator on the air):\n' + '\n'.join(odds) if odds else '') +
            (f"\n\nMost spots by band: {bands}." if bands else '') +
            '\n\nCounted by the KPC bots from POTA spots. 73, KPC')
    link = SITE + 'kpc-live.html#hunters'
    hook = ((os.environ.get('KPC_PARKS_WEBHOOK') or os.environ.get('DISCORD_WEBHOOK_URL') or '').strip().split() or [''])[0]
    sent = []
    if hook.startswith('https://'):
        body = {'username': 'KPC', 'allowed_mentions': {'parse': []},
                'embeds': [{'title': title, 'url': link, 'color': 0xd5a63a, 'description': text[:4000]}]}
        sent.append('Discord ' + str(_http(hook, json.dumps(body).encode(), {'Content-Type': 'application/json'})))
    fid, tok = (os.environ.get('FB_PAGE_ID') or '').strip(), (os.environ.get('FB_PAGE_TOKEN') or '').strip()
    if fid and tok:
        data = urllib.parse.urlencode({'access_token': tok, 'message': f'{title}\n\n{text}', 'link': link}).encode()
        sent.append('Facebook ' + str(_http(f'https://graph.facebook.com/{fid}/feed', data)))
    notice('Hunters post', ', '.join(sent) or 'no Discord/Facebook secrets here; nothing sent')


def _http(url, data, headers=None):
    try:
        req = urllib.request.Request(url, data=data, headers={'User-Agent': UA, **(headers or {})})
        with urllib.request.urlopen(req, timeout=60) as r: return r.status
    except Exception as e:  # noqa: BLE001
        return getattr(e, 'code', str(e)[:80])


if __name__ == '__main__':
    what = sys.argv[1:] or ['collect', 'build']
    try:
        if 'collect' in what: collect()
        if 'build' in what and (CLOSED or not OUT.exists() or 'collect' not in what): build()
        if 'post' in what: post()
    except Exception as e:  # noqa: BLE001
        notice('Hunters', f'skipped: {e}')
    sys.exit(0)
