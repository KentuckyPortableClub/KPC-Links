#!/usr/bin/env python3
"""BUILD STAMP + FREEZE for the answer keys (Brandon Nov 2 7:11 AM: 'Every key build gets a build id stamp and is frozen while chat 11
grades it. Chat 11 grades only that stamped build, and the YES is tied to that id. No new build of that area can start until the
answers are saved and released.').

  stamp us-key|ca-key|world-key   write {'build': 'US-<run id>', 'built': UTC} into data/<kind>/index.json (the waiting room carries
                                  it with the held key, BOT C and chat 11 quote it, the release checks it)
  check us-key|ca-key|world-key   (Nov 3: also FROZEN when the newest stamp in KPC-Links data/<kind>/index.json has no chat 11 verdict)
                                  FROZEN when KPC-Data's waiting room holds a build of that key (data/waiting/in/data/<kind>/index.json
                                  'build') and chat 11 has not yet written a verdict tied to that build id in data/waiting/approved.json
                                  (item 'what' = kind, 'build' = the id, any chat11 text). Writes FROZEN=1 + FROZEN_BUILD=<id> to
                                  $GITHUB_ENV and one notice. FORCE=yes skips the freeze (by hand only).
Never fails (a read error = not frozen, said in the notice)."""
import base64, json, os, subprocess, sys, time

PRE = {'us-key': 'US', 'ca-key': 'CA', 'world-key': 'W'}
REPO = 'KentuckyPortableClub/KPC-Data'


def notice(m): print(f'::notice title=Key build freeze::{m}', flush=True)


def gh_json(path):
    r = subprocess.run(['gh', 'api', f'repos/{REPO}/contents/{path}', '--jq', '.content'], capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip(): return None
    try: return json.loads(base64.b64decode(r.stdout.strip()).decode('utf-8'))
    except Exception:  # noqa: BLE001  (big files come back without content: ask the raw media type)
        r = subprocess.run(['gh', 'api', '-H', 'Accept: application/vnd.github.raw', f'repos/{REPO}/contents/{path}'], capture_output=True, text=True)
        try: return json.loads(r.stdout)
        except Exception: return None  # noqa: BLE001


def stamp(kind):
    p = f'data/{kind}/index.json'
    try: d = json.load(open(p, encoding='utf-8'))
    except Exception: d = {}  # noqa: BLE001
    bid = f"{PRE[kind]}-{os.environ.get('GITHUB_RUN_ID') or time.strftime('%Y%m%d%H%M')}"
    d['build'] = bid; d['built'] = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())
    # Nov 2 review (Mapping #18): parts that failed in this build are named in the stamp (KPC_BUILD_FAILED_FILE = one code per line)
    failed = []
    ff = os.environ.get('KPC_BUILD_FAILED_FILE')
    if ff and os.path.exists(ff):
        failed = sorted({l.strip() for l in open(ff, encoding='utf-8') if l.strip()})
    if failed: d['failed'] = failed; d['complete'] = False
    else: d.pop('failed', None); d.pop('complete', None)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(d, open(p, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    notice(f'{kind} build stamped {bid}: chat 11 grades THIS build; its YES must say build {bid}'
           + (f" -- NOT a full build: {len(failed)} part(s) failed: {' '.join(failed[:20])}" if failed else ''))
    print(bid)


def check(kind):
    if (os.environ.get('FORCE') or '').lower() in ('yes', 'true', '1'):
        notice(f'{kind}: freeze skipped by hand (force)'); return
    held = gh_json(f'data/waiting/in/data/{kind}/index.json')
    bid = (held or {}).get('build')
    ap = gh_json('data/waiting/approved.json') or {}
    items = ap.get('items') if isinstance(ap, dict) else ap
    # Nov 3 (Brandon YES 5:29 PM): the waiting room still held an OLD build (US-f3d48d30899) while newer builds were saved straight
    # to KPC-Links, so the freeze never engaged and 4 US builds ran on Nov 3 before any was graded. Now the NEWEST stamped build in
    # KPC-Links' own data/<kind>/index.json counts too: if it is not the held one and chat 11 has written nothing for its id, a 2nd
    # build waits. FORCE=yes still skips (by hand only).
    live = None
    try: live = json.load(open(f'data/{kind}/index.json', encoding='utf-8'))
    except Exception: live = None  # noqa: BLE001
    lbid = str((live or {}).get('build') or '')
    if lbid and lbid != bid:
        said = [it for it in (items or []) if isinstance(it, dict) and it.get('what') == kind and (str(it.get('build') or '') == lbid or lbid in str(it.get('chat11') or '')) and str(it.get('chat11') or '').strip()]
        if not said:
            env = os.environ.get('GITHUB_ENV')
            if env:
                with open(env, 'a') as f: f.write(f'FROZEN=1\nFROZEN_BUILD={lbid}\n')
            notice(f"{kind}: FROZEN: the newest build {lbid} (KPC-Links data/{kind}/index.json, built {(live or {}).get('built')}) has no chat 11 verdict yet; no 2nd build until it is graded (force=yes by hand skips)"); return
    if not bid:
        notice(f'{kind}: no stamped build waiting for chat 11: building is allowed'); return
    graded = [it for it in (items or []) if isinstance(it, dict) and it.get('what') == kind and (str(it.get('build') or '') == bid or bid in str(it.get('chat11') or '')) and str(it.get('chat11') or '').strip()]   # the id in the verdict text counts too
    if graded:
        it = graded[-1]; v = str(it.get('chat11') or '').strip().upper()
        yes = v.startswith(('YES', 'PASS', 'KEY YES', 'KEY PASS'))
        per_park = kind == 'us-key' and v.startswith(('NO', 'KEY NO')) and (os.environ.get('KPC_PER_PARK', '1') != '0')
        used = gh_json('data/waiting/approved-used.json') or {}
        done = any(bid in k and f'"what": "{kind}"' in k for k in used)
        if (yes or per_park) and not done:   # Brandon: 'no new build ... until the answers are saved and RELEASED'
            env = os.environ.get('GITHUB_ENV')
            if env:
                with open(env, 'a') as f: f.write(f'FROZEN=1\nFROZEN_BUILD={bid}\n')
            notice(f"{kind}: FROZEN: build {bid} is graded ({v[:40]}) and waits for its release (every 2 h); no new build until it is out"); return
        notice(f"{kind}: build {bid} has chat 11's verdict ({v[:60]}){' and was released' if done else ''}: a new build may start"); return
    env = os.environ.get('GITHUB_ENV')
    if env:
        with open(env, 'a') as f: f.write(f'FROZEN=1\nFROZEN_BUILD={bid}\n')
    notice(f'{kind}: FROZEN: build {bid} waits for chat 11 (approved.json item what={kind}, build={bid}); no new build until it is graded')


if __name__ == '__main__':
    try:
        mode, kind = sys.argv[1], sys.argv[2]
        (stamp if mode == 'stamp' else check)(kind)
    except Exception as e: notice(f'stopped: {str(e)[:200]}')  # noqa: BLE001
    sys.exit(0)
