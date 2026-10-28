#!/usr/bin/env python3
"""KPC CHECK-UP, daily part: KEYS + TOKENS (chat 5, Oct 28 2026; HQ/Brandon GO 1:55 PM).
Each key the bots use gets ONE tiny call to see that it still answers; the Facebook Page token's expiry date is read
with Graph debug_token and flagged ~14 days ahead. A key is never printed: every message is scrubbed of the secret
values before it is written. Only keys that are SET in this repo are checked (missing = skipped).
  KPC-Links (the nightly check-up): FB_PAGE_TOKEN, NPS_API_KEY, RIDB_API_KEY  -> checkup-out/keys.json, and it adds
      KPC-Data's own result (data/status/keys.json there, written by KPC-Data's daily YouTube-comments job).
  KPC-Data (KEYS_OUT=data/status/keys.json): YOUTUBE_API_KEY, NPS_API_KEY, RIDB_API_KEY, FCC_BDC_USERNAME + FCC_BDC_TOKEN.
      That file carries no time stamp, so it only changes (one commit) when a key's result changes.
A key that is REFUSED (HTTP 401/403, Graph 'invalid') = problem. A timeout or a busy server = note only (no email).
Never fails."""
import datetime as dt, json, os, pathlib, sys, urllib.error, urllib.parse, urllib.request

NOW = dt.datetime.now(dt.timezone.utc)
OUT = os.environ.get('KEYS_OUT', 'checkup-out/keys.json')
DATA_MODE = OUT.startswith('data/')
WHERE = 'KPC-Data' if DATA_MODE else 'KPC-Links'
SECRETS = [v for k, v in os.environ.items() if k in ('FB_PAGE_TOKEN', 'NPS_API_KEY', 'RIDB_API_KEY', 'YOUTUBE_API_KEY', 'FCC_BDC_TOKEN') and v]
problems, notes, ok = [], [], []


def scrub(s):
    s = str(s)
    for v in SECRETS:
        s = s.replace(v, '***').replace(urllib.parse.quote(v, safe=''), '***')
    return s[:200]


def call(url, headers=None):
    """-> (http status or 0, parsed json or None, error text)"""
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'KPC-checkup', **(headers or {})}), timeout=30) as r:
            body = r.read()
            try: return r.status, json.loads(body), ''
            except ValueError: return r.status, None, ''
    except urllib.error.HTTPError as e:
        try: j = json.loads(e.read())
        except Exception: j = None
        return e.code, j, f'HTTP {e.code}'
    except Exception as e:  # noqa: BLE001
        return 0, None, type(e).__name__


def judge(name, status, err, refused=(401, 403)):
    key = f'keys:{WHERE}:{name}'
    if status == 200:
        ok.append(f'{name} key answers ({WHERE})')
    elif status in refused:
        problems.append({'key': key, 'chat': 5, 'msg': f'{name} key ({WHERE} secret) is REFUSED ({err}): it may be expired or turned off. Brandon makes a new one and puts it in {WHERE} → Settings → Secrets.'})
    else:
        notes.append({'chat': 5, 'msg': f'{name} key ({WHERE}): no clear answer today ({scrub(err) or status}); checked again tomorrow'})


def fb():
    t = os.environ.get('FB_PAGE_TOKEN', '').strip()
    if not t: return
    st, j, err = call('https://graph.facebook.com/v19.0/debug_token?' + urllib.parse.urlencode({'input_token': t, 'access_token': t}))
    d = (j or {}).get('data') or {}
    if st != 200 or not d:
        if st in (400, 401, 403) and j and 'error' in j:
            problems.append({'key': 'keys:fb:invalid', 'chat': 5, 'msg': f"Facebook Page token is REFUSED by Facebook ({scrub((j['error'] or {}).get('message', err))}). Posting to the Page stops until Brandon makes a new one (Secret FB_PAGE_TOKEN)."})
        else:
            notes.append({'chat': 5, 'msg': f'Facebook token: no clear answer today ({scrub(err) or st})'})
        return
    if not d.get('is_valid'):
        problems.append({'key': 'keys:fb:invalid', 'chat': 5, 'msg': 'Facebook Page token is NOT VALID any more. Posting to the Page stops until Brandon makes a new one (Secret FB_PAGE_TOKEN).'})
        return
    ends = [(x, d.get(x)) for x in ('expires_at', 'data_access_expires_at') if d.get(x)]
    if not ends:
        ok.append('Facebook Page token is valid and never expires'); return
    what, ts = min(ends, key=lambda e: e[1])
    when = dt.datetime.fromtimestamp(ts, dt.timezone.utc)
    days = (when - NOW).total_seconds() / 86400
    label = 'expires' if what == 'expires_at' else "loses data access (Facebook's 90-day rule)"
    if days <= 14:
        problems.append({'key': f'keys:fb:expiring:{when.date()}', 'chat': 5, 'msg': f'Facebook Page token {label} on {when:%b %d, %Y} ({max(0, days):.0f} days). Brandon: make a new Page token and replace Secret FB_PAGE_TOKEN before then.'})
    else:
        ok.append(f'Facebook Page token is valid; {label} {when:%b %d, %Y} ({days:.0f} days)')


def nps():
    k = os.environ.get('NPS_API_KEY', '').strip()
    if k:
        st, _, err = call('https://developer.nps.gov/api/v1/parks?limit=1', {'X-Api-Key': k}); judge('NPS', st, err)


def ridb():
    k = os.environ.get('RIDB_API_KEY', '').strip()
    if k:
        st, _, err = call('https://ridb.recreation.gov/api/v1/organizations?limit=1', {'apikey': k}); judge('RIDB (Recreation.gov)', st, err)


def youtube():
    k = os.environ.get('YOUTUBE_API_KEY', '').strip()
    if k:
        st, j, err = call('https://www.googleapis.com/youtube/v3/channels?' + urllib.parse.urlencode({'part': 'id', 'forHandle': '@kpc-n4kpc', 'key': k}))
        if st == 400 and 'API key' in json.dumps(j or {}): st = 403          # Google says 'API key not valid' with a 400
        judge('YouTube', st, err)


def fcc():
    u, k = os.environ.get('FCC_BDC_USERNAME', '').strip(), os.environ.get('FCC_BDC_TOKEN', '').strip()
    if u and k:
        st, _, err = call('https://broadbandmap.fcc.gov/api/public/map/listAsOfDates', {'username': u, 'hash_value': k}); judge('FCC broadband map', st, err)


def main():
    for f in (fb, nps, ridb, youtube, fcc):
        try: f()
        except Exception as e:  # noqa: BLE001
            notes.append({'chat': 5, 'msg': f'{f.__name__} check stopped: {scrub(e)}'})
    if DATA_MODE:
        out = {'problems': sorted(problems, key=lambda x: x['key']), 'notes': sorted(notes, key=lambda x: x['msg']), 'ok': sorted(ok)}
    else:
        # KPC-Data's own keys (its daily job writes the result there; public file, no secrets in it)
        st, j, err = call('https://raw.githubusercontent.com/KentuckyPortableClub/KPC-Data/main/data/status/keys.json')
        if st == 200 and j:
            problems.extend(j.get('problems', [])); notes.extend(j.get('notes', [])); ok.extend(j.get('ok', []))
        else:
            notes.append({'chat': 5, 'msg': f"KPC-Data's key results not found yet ({err or st}); they come from its daily YouTube-comments job"})
        out = {'part': 'keys', 'date': NOW.date().isoformat(), 'problems': problems, 'notes': notes, 'ok': ok}
    txt = json.dumps(out, indent=1, ensure_ascii=False)
    for v in SECRETS:                                   # belt and braces: no key ever lands in a file

        if v in txt: txt = txt.replace(v, '***')
    pathlib.Path(OUT).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(OUT).write_text(txt + '\n', encoding='utf-8')
    print(f'::notice title=Check-up keys ({WHERE})::{len(problems)} problem(s), {len(notes)} note(s), {len(ok)} fine')


if __name__ == '__main__':
    try: main()
    except Exception as e:  # noqa: BLE001
        print(f'::notice title=Check-up keys::stopped early: {scrub(e)}')
    sys.exit(0)
