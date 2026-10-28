#!/usr/bin/env python3
"""ONE-TIME: the website release statement (Brandon's GO, Oct 28 2026 6:50 AM via HQ; 'send 8 am').
Posts data/release-post.txt EXACTLY as written, once to Discord (general / announcements webhook) and once to the
Facebook Page (never a Group). Each place is recorded in data/kpc-club-posts-state.json under 'release_post' as soon as
it works, so a second run never posts it again. Never fails (exit 0); never prints a key."""
import json, os, pathlib, sys, urllib.error, urllib.parse, urllib.request

TEXT = pathlib.Path('data/release-post.txt').read_text(encoding='utf-8').strip()
STATE = pathlib.Path('data/kpc-club-posts-state.json')
UA = {'User-Agent': 'KPC club bot (kentuckyportableclub.github.io)'}


def notice(m):
    print(f'::notice title=Release post::{m}', flush=True)


def http(url, data, headers=None):
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=data, headers={**UA, **(headers or {})}), timeout=45) as r:
            return r.status, r.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode('utf-8', 'replace')
    except Exception as e:  # noqa: BLE001
        return 0, str(e)


def main():
    st = json.loads(STATE.read_text(encoding='utf-8')) if STATE.exists() else {}
    rp = st.setdefault('release_post', {})
    if len(TEXT) > 1990:
        notice('text too long for one Discord message; nothing posted'); return
    if not rp.get('discord'):
        hook = next((h for h in ((os.environ.get(n) or '').strip().split() or [''] for n in ('KPC_GENERAL_WEBHOOK', 'KPC_DISCORD_WEBHOOK')) if h[0].startswith('https://')), [''])[0]
        if not hook:
            notice('no Discord webhook secret; Discord not posted')
        else:
            c, r = http(hook + ('&' if '?' in hook else '?') + 'wait=true',
                        json.dumps({'username': 'KPC-N4KPC-Bot', 'content': TEXT, 'allowed_mentions': {'parse': []}}).encode(),
                        {'Content-Type': 'application/json'})
            if c < 300:
                rp['discord'] = json.loads(r).get('id', 'posted') if r.strip().startswith('{') else 'posted'
                notice(f"Discord posted (message id {rp['discord']})")
            else:
                notice(f'Discord said HTTP {c}: {r[:150]}')
    else:
        notice(f"Discord already posted earlier (message id {rp['discord']}); not again")
    if not rp.get('facebook'):
        pid, tok = (os.environ.get('FB_PAGE_ID') or '').strip(), (os.environ.get('FB_PAGE_TOKEN') or '').strip()
        if not (pid and tok):
            notice('no Facebook secrets; Facebook not posted')
        else:
            c, r = http(f'https://graph.facebook.com/{pid}/feed', urllib.parse.urlencode({'access_token': tok, 'message': TEXT}).encode())
            if c < 300:
                rp['facebook'] = json.loads(r).get('id', 'posted')
                notice(f"Facebook Page posted (post id {rp['facebook']})")
            else:
                notice(f'Facebook said HTTP {c}: {r[:150]}')
    else:
        notice(f"Facebook already posted earlier (post id {rp['facebook']}); not again")
    STATE.write_text(json.dumps(st, indent=1) + '\n', encoding='utf-8')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:  # noqa: BLE001
        notice(f'stopped early: {type(e).__name__}: {str(e)[:200]}')
    sys.exit(0)
