#!/usr/bin/env python3
"""KPC WATCHER (chat 5, Oct 26 2026; Brandon GO 11:50 AM). Once a week: what CHANGED out there, routed to the chat
that should look at it. It only reads; it changes nothing on the site and posts nothing.

  Chat 8 (research desk)
    - Kentucky park official pages (the 'web' links in kpc-ky-data.json: parks.ky.gov, fw.ky.gov, eec.ky.gov, nps.gov
      ...): the lines about hours, fees, rules, closures. A change shows the old and new lines.
    - POTA / SOTA / WWFF rules pages (the ones our guides and rule cards link to, plus any NEW rules document their
      rules pages start linking to, like a new WWFF rules PDF version).
  Chat 2 (maps & park data)
    - Closure sources from research round 4 that were BLOCKED to robots (403 / Cloudflare / bad certificate) and now
      answer a plain, honest request. Never worked around: a blocked site just stays on the list.
  Chat 6 (campout & events)
    - ARRL hamfest listings and special-event stations for Kentucky and the states around it (TN IN OH IL MO VA WV):
      NEW listings since last week (name + link only; chat 6 checks them on ARRL's page before using them).

Manners: robots.txt is obeyed for every host, an honest User-Agent, one request at a time with a pause (3 s per
host), a time limit. MEMORY + REPORT: kept on the 'bot-state' branch (watcher-state.json + watcher-report.md, one
commit, replaced each week), so the weekly hashes never rebuild the site or grow the main branch.
The first run only records how things look today; changes show from the second week.
Usage: kpc_watcher.py <old state json or ''> <new state json> <report md>. Never fails (exit 0).
"""
import datetime as dt
import hashlib
import html
import json
import os
import pathlib
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser

UA = 'KPC-Watcher/1.0 (+https://kentuckyportableclub.github.io/KPC-Links/; weekly check of public pages)'
T0 = time.time()
LIMIT = float(os.environ.get('WATCH_MINUTES') or 35) * 60
TODAY = dt.date.today().isoformat()
NEAR = ['Kentucky', 'Tennessee', 'Indiana', 'Ohio', 'Illinois', 'Missouri', 'Virginia', 'West Virginia']
NEAR_AB = {'Kentucky': 'KY', 'Tennessee': 'TN', 'Indiana': 'IN', 'Ohio': 'OH', 'Illinois': 'IL', 'Missouri': 'MO',
           'Virginia': 'VA', 'West Virginia': 'WV'}
RULES_START = [
    ('POTA', 'https://docs.pota.app/docs/rules.html'),
    ('POTA', 'https://parksontheair.com/rules/'),
    ('POTA', 'https://docs.pota.app/docs/activator_reference/activator_guide-english.html'),
    ('WWFF', 'https://wwff.co/rules-faq/'),
    ('WWFF', 'https://wwff.co/wwff_cont/uploads/2025/09/WWFF-Global-Rules-V_5.10.pdf'),
    ('SOTA', 'https://www.sota.org.uk/'),
]
# Research round 4 (KPC_Round4_results.xlsx, Oct 25): closure / alert sources that refused robots then.
BLOCKED = [
    ('NY', 'State forests (DEC)', 'https://dec.ny.gov/'), ('NY', 'State parks', 'https://parks.ny.gov/'),
    ('TN', 'Wildlife agency (TWRA alerts)', 'https://www.tn.gov/twra/alerts.html'), ('NH', 'State forests', 'https://dncr.nh.gov/'),
    ('NH', 'Wildlife agency', 'https://wildlife.nh.gov/'), ('OH', 'ODNR (parks, forests, wildlife)', 'https://ohiodnr.gov/'),
    ('NE', 'State parks', 'https://outdoornebraska.gov/parks/park-faqs/safety/closures-and-safety-advisories/'),
    ('MS', 'Wildlife agency + state parks', 'https://www.mdwfp.com/'), ('NC', 'State parks closures page', 'https://www.ncparks.gov/closures'),
    ('NJ', 'Fish & Wildlife pages', 'https://dep.nj.gov/njfw/'), ('LA', 'State parks', 'https://www.lastateparks.com/'),
    ('AL', 'State parks alerts', 'https://www.alapark.com/'), ('AZ', 'Wildlife agency', 'https://www.azgfd.com/'),
    ('NV', 'Wildlife agency', 'https://ndow.org/'), ('MA', 'State parks / forests / wildlife (mass.gov)', 'https://www.mass.gov/orgs/department-of-conservation-and-recreation'),
    ('KS', 'Parks + wildlife', 'https://ksoutdoors.gov/'), ('SC', 'State forests', 'https://www.scfc.gov/'),
    ('AK', 'State forests', 'https://forestry.alaska.gov/'), ('CA', 'State forests (CAL FIRE)', 'https://www.fire.ca.gov/'),
    ('AR', 'State forests', 'https://www.agriculture.arkansas.gov/'),
]
CHALLENGE = re.compile(r'just a moment|attention required|access denied|not allowed|incapsula|request unsuccessful|'
                       r'enable javascript and cookies|cf-browser-verification|captcha', re.I)
KEYLINE = re.compile(r'\b(hours?|open(s|ing)?|clos(e|ed|es|ing|ure|ures)|fees?|\$\s?\d|admission|parking|permit|'
                     r'rules?|regulation|prohibit|not allowed|season(al)?|alert|notice|dawn|dusk|sunrise|sunset|'
                     r'a\.?m\.?|p\.?m\.?)\b', re.I)

_last, _robots = {}, {}
stats = {'requests': 0, 'robots_no': []}


def allowed(url):
    p = urllib.parse.urlparse(url)
    root = f'{p.scheme}://{p.netloc}'
    if root not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            req = urllib.request.Request(root + '/robots.txt', headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=20) as r:
                rp.parse(r.read(200000).decode('utf-8', 'replace').splitlines())
        except urllib.error.HTTPError as e:
            rp.parse([] if e.code >= 404 or e.code < 400 else ['User-agent: *', 'Disallow: /'])   # 401/403 = keep out
        except Exception:  # noqa: BLE001
            rp.parse([])                     # no robots.txt reachable: the page itself will say if we are welcome
        _robots[root] = rp
    return _robots[root].can_fetch(UA, url)


def fetch(url, data=None, raw=False):
    """-> (status, text or bytes, final url); status 0 = no answer; -1 = robots.txt says no"""
    if time.time() - T0 > LIMIT:
        return -2, 'time limit', url
    if not allowed(url):
        stats['robots_no'].append(url)
        return -1, 'robots.txt asks robots not to read this page', url
    host = urllib.parse.urlparse(url).netloc
    wait = 3 - (time.time() - _last.get(host, 0))
    if wait > 0:
        time.sleep(wait)
    _last[host] = time.time()
    stats['requests'] += 1
    try:
        body = urllib.parse.urlencode(data).encode() if isinstance(data, dict) else data
        req = urllib.request.Request(url, data=body, headers={'User-Agent': UA, 'Accept': '*/*'})
        with urllib.request.urlopen(req, timeout=40) as r:
            b = r.read(6_000_000)
            return r.status, (b if raw else b.decode('utf-8', 'replace')), r.geturl()
    except urllib.error.HTTPError as e:
        try:
            t = e.read(20000).decode('utf-8', 'replace')
        except Exception:  # noqa: BLE001
            t = ''
        return e.code, t, url
    except Exception as e:  # noqa: BLE001
        return 0, str(e)[:120], url


def text_lines(page):
    page = re.sub(r'(?is)<(script|style|noscript|svg|nav|header|footer|form|select)\b.*?</\1>', ' ', page)
    page = re.sub(r'(?i)<br\s*/?>|</(p|div|li|h[1-6]|tr|td|th|section|article)>', '\n', page)
    t = html.unescape(re.sub(r'<[^>]+>', ' ', page))
    out = []
    for ln in t.split('\n'):
        ln = re.sub(r'\s+', ' ', ln).strip()
        if len(ln) > 2 and ln not in out:
            out.append(ln[:400])
    return out


def h(x):
    return hashlib.sha256(x.encode('utf-8') if isinstance(x, str) else x).hexdigest()[:16]


def diff(old, new, n=4):
    a = [x for x in new if x not in set(old)]
    r = [x for x in old if x not in set(new)]
    s = ''
    if r:
        s += ' REMOVED: ' + ' | '.join(x[:160] for x in r[:n]) + (f' (+{len(r) - n})' if len(r) > n else '')
    if a:
        s += ' NEW: ' + ' | '.join(x[:160] for x in a[:n]) + (f' (+{len(a) - n})' if len(a) > n else '')
    return s.strip()


# ---------------------------------------------------------------- the four watches
def watch_ky(old, new, rep):
    try:
        parks = json.load(open('kpc-ky-data.json', encoding='utf-8')).get('parks') or []
    except Exception:  # noqa: BLE001
        parks = []
    seen = {}
    try: HRS = json.load(open('kpc-ky-hours.json', encoding='utf-8')).get('parks') or {}
    except Exception: HRS = {}  # noqa: BLE001
    ours = {}   # Oct 27 (research-bots review #7): next to a changed page, the park number + what WE show today, so the fix is one line
    for p in parks:
        u = str(p.get('web') or '')
        if not u.startswith('http') or 'pota.app' in u:
            continue
        seen.setdefault(u, []).append(f"{p.get('c')} {p.get('n')}")
        hv = HRS.get(p.get('c')) or {}
        mine = '; '.join(f'{k}: {v}' for k, v in hv.items() if k != 'link' and v)
        if mine: ours.setdefault(u, []).append(f"{p.get('c')} (kpc-ky-hours.json) {mine[:200]}")
    for u, names in sorted(seen.items()):
        c, t, _ = fetch(u)
        prev = old.get(u) or {}
        if c < 0:                       # robots.txt says no, or out of time: keep last week's picture
            new[u] = prev; continue
        if c != 200:
            new[u] = dict(prev, last_error=f'HTTP {c}' if c else 'no answer')
            if prev.get('lines') is not None and prev.get('last_error') and c in (404, 410):
                rep[8].append(f"{names[0]}: its official page no longer loads (HTTP {c} twice) {u}")
            continue
        lines = [x for x in text_lines(t) if KEYLINE.search(x)][:120]
        new[u] = {'hash': h('\n'.join(lines)), 'lines': lines, 'date': TODAY}
        if prev.get('hash') and prev['hash'] != new[u]['hash']:
            d = diff(prev.get('lines') or [], lines)
            if d:
                rep[8].append(f"{', '.join(names[:2])}: hours / fees / rules text changed on {u} —{d}"
                              + (' · WE SHOW: ' + ' | '.join(ours[u][:2]) if ours.get(u) else ' · we show no hours / fees for it'))


def watch_rules(old, new, rep):
    todo, done = list(RULES_START), set()
    while todo:
        prog, u = todo.pop(0)
        if u in done or len(done) > 24:
            continue
        done.add(u)
        is_pdf = u.lower().endswith('.pdf')
        c, t, final = fetch(u, raw=is_pdf)
        prev = old.get(u) or {}
        if c < 0:
            new[u] = prev; continue
        if c != 200:
            new[u] = dict(prev, last_error=f'HTTP {c}' if c else 'no answer')
            if c in (404, 410) and prev.get('hash'):
                rep[8].append(f'{prog}: rules page no longer loads (HTTP {c}): {u}')
            continue
        if is_pdf:
            new[u] = {'hash': h(t), 'date': TODAY, 'prog': prog}
            lines = []
        else:
            lines = text_lines(t)
            new[u] = {'hash': h('\n'.join(lines)), 'lines': lines[:400], 'date': TODAY, 'prog': prog}
            # follow links to rules documents on the same site (new versions show up here)
            base = urllib.parse.urlparse(final).netloc
            for href, label in re.findall(r'(?is)<a\b[^>]*href="([^"#]+)"[^>]*>(.*?)</a>', t):
                full = urllib.parse.urljoin(final, html.unescape(href))
                lab = re.sub(r'<[^>]+>', ' ', label)
                if urllib.parse.urlparse(full).netloc.endswith(base.replace('www.', '')) and re.search(r'rule', full + ' ' + lab, re.I):
                    if full not in done and all(full != x[1] for x in todo):
                        todo.append((prog, full))
        if not prev and old:
            rep[8].append(f'{prog}: a rules page/document we had not seen before: {u}')
        elif prev.get('hash') and prev['hash'] != new[u]['hash']:
            d = diff(prev.get('lines') or [], lines) if lines else 'the document file itself changed'
            rep[8].append(f'{prog}: rules page changed: {u} — {d}' if d else f'{prog}: rules page changed (layout only?): {u}')


def watch_closures(old, new, rep):
    for st, what, u in BLOCKED:
        c, t, _ = fetch(u)
        if c < 0:
            if old.get(u): new[u] = old[u]
            continue
        was = (old.get(u) or {}).get('answers')
        answers = c == 200 and not CHALLENGE.search(t[:6000] if isinstance(t, str) else '')
        new[u] = {'answers': answers, 'status': c, 'date': TODAY}
        if answers and was is not True:
            rep[2].append(f'{st} {what}: now answers a plain request ({u}); worth a look for kpc_us_closures.py')
        elif not answers and was is True:
            rep[2].append(f'{st} {what}: blocked again (HTTP {c}) {u}')


def watch_closure_pages(old, new, rep):
    """Oct 27 (research-bots review #6, HQ GO): the agencies' closure / alert PAGES that have no feed (data/closure-pages.json,
    research round 4): only their closure lines are hashed; a change goes to chat 2 with the link. Robots rules obeyed."""
    try: pages = json.load(open('data/closure-pages.json', encoding='utf-8')).get('pages') or []
    except Exception: pages = []  # noqa: BLE001
    for p in pages:
        u = p['page']; key = 'cp:' + u
        c, t, _ = fetch(u)
        prev = old.get(key) or {}
        if c < 0: new[key] = prev; continue
        if c != 200: new[key] = dict(prev, last_error=f'HTTP {c}' if c else 'no answer'); continue
        lines = [x for x in text_lines(t) if re.search(r'clos|restrict|reopen|open(ed|s)? again|fire|flood|hunt|quota|construction|alert', x, re.I)][:150]
        new[key] = {'hash': h('\n'.join(lines)), 'lines': lines, 'date': TODAY}
        if prev.get('hash') and prev['hash'] != new[key]['hash']:
            d = diff(prev.get('lines') or [], lines)
            if d: rep[2].append(f"{p['st']} {p['agency']}: closure page changed {u} —{d}")


def arrl_search(page_url, state_name):
    """Submit ARRL's own search form for one state (the way a person would) and return the listing links."""
    c, t, final = fetch(page_url)
    if c != 200:
        return None
    form = next((f for f in re.findall(r'(?is)<form\b[^>]*>.*?</form>', t) if re.search(r'(?i)name="[^"]*state[^"]*"', f)), None)
    if not form:
        return None
    action = (re.search(r'(?i)action="([^"]*)"', form) or [None, final])[1]
    method = (re.search(r'(?i)method="([^"]*)"', form) or [None, 'get'])[1].lower()
    fields = {}
    for inp in re.findall(r'(?is)<input\b[^>]*>', form):
        n = re.search(r'(?i)name="([^"]*)"', inp)
        if not n:
            continue
        typ = (re.search(r'(?i)type="([^"]*)"', inp) or [None, 'text'])[1].lower()
        if typ in ('checkbox', 'radio', 'submit', 'image') and 'checked' not in inp.lower():
            continue
        v = re.search(r'(?i)value="([^"]*)"', inp)
        fields[n.group(1)] = html.unescape(v.group(1)) if v else ''
    for sel in re.findall(r'(?is)<select\b.*?</select>', form):
        n = re.search(r'(?i)name="([^"]*)"', sel)
        if not n:
            continue
        opts = re.findall(r'(?is)<option\b[^>]*value="([^"]*)"[^>]*>(.*?)</option>', sel)
        if 'state' in n.group(1).lower():
            fields[n.group(1)] = next((v for v, lab in opts if re.sub(r'<[^>]+>', '', lab).strip().lower() in (state_name.lower(), NEAR_AB[state_name].lower())), NEAR_AB[state_name])
        else:
            fields.setdefault(n.group(1), '')
    target = urllib.parse.urljoin(final, html.unescape(action))
    if method == 'post':
        c, res, _ = fetch(target, data=fields)
    else:
        c, res, _ = fetch(target + ('&' if '?' in target else '?') + urllib.parse.urlencode(fields))
    if c != 200:
        return None
    out = {}
    for href, label in re.findall(r'(?is)<a\b[^>]*href="((?:https?://www\.arrl\.org)?/(?:hamfests|special_events|special-event)[^"]*/[a-z0-9\-]+)"[^>]*>(.*?)</a>', res):
        if '/search' in href:
            continue
        full = urllib.parse.urljoin('https://www.arrl.org/', href)
        lab = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', label))).strip()[:90]
        if not lab or re.fullmatch(r'(?i)(learn|read|see|view)( more)?|details|more', lab):
            lab = re.sub(r'-\d+$', '', full.rsplit('/', 1)[-1]).replace('-', ' ').title()      # 'Learn More' -> name from the address
        if full not in out or out[full] == full:
            out[full] = lab
    return out


def watch_arrl(old, new, rep):
    empty = {}
    for kind, page in (('Hamfest', 'https://www.arrl.org/hamfests-and-conventions-calendar'),
                       ('Special event station', 'https://www.arrl.org/special-event-stations')):
        for st in NEAR:
            key = f'arrl:{kind}:{st}'
            got = arrl_search(page, st)
            prev = old.get(key) or {}
            if got is None:
                new[key] = prev
                if st == 'Kentucky':
                    rep[6].append(f'ARRL {kind.lower()} search could not be read this week (form changed, robots.txt, or no answer); nothing new listed')
                    break          # same form for every state: don't knock 7 more times
                continue
            new[key] = {'links': got, 'date': TODAY}
            empty.setdefault(kind, []).append(len(got))
            if prev.get('links') is not None:
                for u, lab in sorted(got.items()):
                    if u not in prev['links']:
                        rep[6].append(f'{NEAR_AB[st]} new ARRL {kind.lower()} listing: {lab} {u}')
    for kind, ns in empty.items():
        if ns and not any(ns):
            rep[6].append(f'ARRL {kind.lower()} search answered but listed nothing for any of the {len(ns)} states (ARRL may have changed the page); nothing new can be spotted until that is fixed')


def main():
    a = sys.argv[1:]
    oldf = a[0] if len(a) > 0 else ''
    newf = a[1] if len(a) > 1 else 'watcher-state.json'
    repf = a[2] if len(a) > 2 else 'watcher-report.md'
    try:
        old = json.load(open(oldf, encoding='utf-8')) if oldf and os.path.exists(oldf) else {}
    except ValueError:
        old = {}
    first = not old
    new = {'ky': {}, 'rules': {}, 'closures': {}, 'arrl': {}}
    rep = {8: [], 2: [], 6: []}
    for part, fn in (('closures', watch_closures), ('closure pages', watch_closure_pages), ('rules', watch_rules), ('arrl', watch_arrl), ('ky', watch_ky)):
        try:
            fn(old.get(part) or {}, new[part], rep)
        except Exception as e:  # noqa: BLE001
            rep[8 if part in ('ky', 'rules') else 2 if part == 'closures' else 6].append(f'(watcher part {part} stopped early: {type(e).__name__}: {str(e)[:120]})')
        if not new[part] and old.get(part):
            new[part] = old[part]
    new['checked'] = TODAY
    json.dump(new, open(newf, 'w', encoding='utf-8'), ensure_ascii=False)
    names = {8: 'Chat 8 · Research desk (KY park pages, program rules)', 2: 'Chat 2 · Maps & park data (closure sources)',
             6: 'Chat 6 · Campout & events (ARRL hamfests, special events)'}
    md = [f'# KPC Watcher: what changed this week ({TODAY})', '',
          '_Weekly, read-only (.github/scripts/kpc_watcher.py). Each chat checks its own lines against the official page before using anything. '
          'Robots.txt obeyed, one polite request at a time; blocked sites are never worked around._', '']
    if first:
        md += ['**First run:** today\'s pages were recorded. Changes show from next week.', '']
    for c in (8, 2, 6):
        md.append(f'## {names[c]}')
        md += [f'- {x}' for x in rep[c][:80]] or ['- nothing changed']
        if len(rep[c]) > 80:
            md.append(f'- … and {len(rep[c]) - 80} more')
        md.append('')
    md.append(f"_{stats['requests']} requests; {len(stats['robots_no'])} page(s) skipped because robots.txt asks robots to stay out; "
              f"{len(new['ky'])} KY park pages, {len(new['rules'])} rules pages, {len(new['closures'])} closure sources, "
              f"{len(new['arrl'])} ARRL state searches on file._")
    pathlib.Path(repf).write_text('\n'.join(md) + '\n', encoding='utf-8')
    print('\n'.join(md))
    print(f"::notice title=KPC Watcher::{sum(len(v) for v in rep.values())} change(s): chat 8 {len(rep[8])}, chat 2 {len(rep[2])}, chat 6 {len(rep[6])}"
          + (' (first run: baseline only)' if first else ''), flush=True)


if __name__ == '__main__':
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f'::notice title=KPC Watcher::stopped early: {type(e).__name__}: {e}', flush=True)
    sys.exit(0)
