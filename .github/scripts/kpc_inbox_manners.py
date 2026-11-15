#!/usr/bin/env python3
"""kpc_inbox_manners.py: the research inbox's request manners, the same as the outline store engine v3.6 (KPC owner, 2026-11-14).

kpc_research_inbox.py (run by kpc_problem_solver.py --inbox --retry) asks layer servers for records near a pin. Every live request
it makes goes through Manners, which does what the store engine does (engine kpc_outline_store.py: read_robots, RobotsTxt,
robots_hop_problem, Net.cap_problem / wait / spend; fetch-settings.json):
  1. robots.txt, asked ONCE per host per run (RFC 9309 2.3.1.3, the engine's one rule for every host):
       200 (a robots file)         = obeyed: the longest matching Allow / Disallow wins (a tie goes to Allow, as in the engine);
                                     a Crawl-delay longer than our 2 s floor is used; over 30 s the host is skipped this run;
       200 that is a web page      = could not be read: no reads from that host this run;
       400-499 except 429          = "unavailable" = no restrictions;
       429, any 5xx, no answer     = no reads from that host this run (tried again next run; a Retry-After is kept for next run).
     A robots.txt redirect is followed like the engine: at most 5 steps, https only, the same site (the same host, its www. twin
     or the same registered domain); each step passes the never-contact rules (kpc_net_guard), is paced, counted and capped.
  2. at least 2 s between two requests to one host (longer when Crawl-delay or Retry-After asks for more; Retry-After at most 300 s).
  3. at most 200 requests per host per hour and 1,500 per day (robots.txt counted). The counters are kept in a small state file
     (default <research cache>/_fetch-counts.json, which the workflow's cache carries from one run to the next) so they hold
     across runs. Past a cap: no request; the caller keeps the park on the retry list and prints one plain line.
The never-contact list (kpc_net_guard: services*.arcgis.com, apps.fs.usda.gov, ncnhde.natureserve.org, KPC_SAVED_ONLY_HOSTS, the
layers.json never_contact flags) keeps winning: it is checked before anything here and again by the guard on every open.
Not a rule file (kpc_key_freeze.NOT_RULES): it decides which request may go out, never a join. Standard library only."""
import datetime, email.utils, json, os, pathlib, re, time, urllib.error, urllib.parse, urllib.request
import kpc_net_guard; kpc_net_guard.install()   # never-contact hosts refused before any request, redirect hops included

# ---- the limits, in ONE place (the store engine's fetch-settings.json values and floors)
SETTINGS = {
    'per_host_per_hour': 200,              # requests to ONE host in any 60 minutes (robots.txt counted)
    'per_host_per_day': 1500,              # requests to ONE host in any 24 hours
    'min_seconds_between_requests': 2.0,   # never below 2 s; a longer Crawl-delay / Retry-After wins
    'skip_crawl_delay_over': 30.0,         # a robots.txt Crawl-delay above this: the host is skipped this run
    'retry_after_cap': 300.0,              # the longest Retry-After we wait for (engine RETRY_AFTER_CAP)
    'robots_max_hops': 5,                  # robots.txt redirects followed (engine ROBOTS_MAX_HOPS, RFC 9309 2.3.1.2)
    'robots_max_bytes': 512 * 1024,        # a robots.txt is read up to this size (engine cap)
}
HOUR, DAY = 3600.0, 86400.0
COUNTS_NAME = '_fetch-counts.json'
ROBOTS_ACCEPT = 'text/plain, text/*;q=0.5, */*;q=0.1'   # robots.txt is a text file (engine 3.3)


class Skip(Exception):
    """No request was made: a cap, a back-off, robots.txt or a host rule said no. str() is the plain reason."""


class Answer:
    __slots__ = ('status', 'headers', 'body', 'location')

    def __init__(self, status, headers=None, body=b'', location=''):
        self.status, self.headers, self.body, self.location = int(status or 0), {str(k).lower(): str(v) for k, v in (headers or {}).items()}, body or b'', location or ''


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl): return None   # robots.txt hops are followed by Manners itself


def _read(r, cap):
    return r.read(cap + 1)[:cap] if cap else r.read()


def open_url(url, accept, timeout, follow, cap=0, ua=''):
    """One real request -> Answer. An HTTP error answer is an Answer too; no answer at all raises (OSError / timeout)."""
    req = urllib.request.Request(url, headers={'User-Agent': ua, 'Accept': accept})
    op = urllib.request.build_opener() if follow else urllib.request.build_opener(_NoRedirect)
    try:
        r = op.open(req, timeout=timeout)
        return Answer(getattr(r, 'status', 200), dict(r.headers.items()), _read(r, cap))
    except urllib.error.HTTPError as e:
        try: body = _read(e, cap)
        except Exception: body = b''  # noqa: BLE001
        h = dict(e.headers.items()) if e.headers else {}
        return Answer(e.code, h, body, urllib.parse.urljoin(url, h.get('Location') or h.get('location') or ''))


# ---- robots.txt (the engine's own matcher: urllib.robotparser ignores * and $ before Python 3.13)
class RobotsTxt:
    """RFC 9309: the group for our product token, else the '*' group, else no rules. The longest matching Allow / Disallow wins (a tie
    goes to Allow); '*' = any characters, a final '$' = the end. An empty Disallow allows everything. A Disallow that is not understood
    disallows all; a Crawl-delay that is not understood counts as 120 s (= skipped). Copied from the store engine."""

    def __init__(self, text, ua):
        self.ua = str(ua).lower()
        self.groups = []
        cur, in_rules = None, False
        for raw in re.split(r'\r\n|\r|\n', str(text or '').lstrip('﻿')):
            line = raw.split('#', 1)[0].strip()
            if not line or ':' not in line: continue
            k, v = line.split(':', 1); k, v = k.strip().lower(), v.strip()
            if k in ('user-agent', 'useragent', 'user agent'):
                if cur is None or in_rules: cur = [set(), [], None]; self.groups.append(cur); in_rules = False
                cur[0].add(v.lower())
            elif k in ('allow', 'disallow'):
                if cur is None: continue
                in_rules = True
                if k == 'disallow' and v == '': continue
                if v and v[0] not in '/*':
                    if k == 'disallow': cur[1].append((False, '/'))
                    continue
                cur[1].append((k == 'allow', v))
            elif k == 'crawl-delay':
                if cur is None: continue
                in_rules = True
                try:
                    f = float(v)
                    if f != f: raise ValueError('nan')
                    cur[2] = max(f, cur[2] or 0.0)
                except ValueError: cur[2] = max(cur[2] or 0.0, 120.0)
        self.rules, self.crawl_delay, self.group = self._select()

    def _select(self):
        best, chosen, me = -1, [], self.ua.split()[0].split('/')[0] if self.ua.split() else ''
        for agents, rules, cd in self.groups:
            for a in agents:
                tok = a.split('/')[0].strip()
                if tok and tok != '*' and tok == me:
                    if len(tok) > best: best, chosen = len(tok), [(rules, cd)]
                    elif len(tok) == best: chosen.append((rules, cd))
        name = 'our group' if chosen else ''
        if not chosen:
            chosen = [(rules, cd) for agents, rules, cd in self.groups if '*' in agents]
            name = "the '*' group" if chosen else 'no group (everything allowed)'
        cds = [cd for _, cd in chosen if cd is not None]
        return [x for r, _ in chosen for x in r], (max(cds) if cds else 0.0), name

    @staticmethod
    def _match(pattern, path):
        end = pattern.endswith('$')
        p = urllib.parse.unquote(pattern[:-1] if end else pattern)
        p = re.sub(r'\*+', '*', p)[:2000]
        if not end: p += '*'
        i = j = 0; star = -1; mark = 0; n, m = len(path), len(p)
        while i < n:
            if j < m and p[j] != '*' and p[j] == path[i]: i += 1; j += 1
            elif j < m and p[j] == '*': star, mark = j, i; j += 1
            elif star >= 0: j = star + 1; mark += 1; i = mark
            else: return False
        while j < m and p[j] == '*': j += 1
        return j == m

    def allowed(self, url):
        sp = urllib.parse.urlsplit(url)
        path = urllib.parse.unquote(sp.path or '/') + ('?' + urllib.parse.unquote(sp.query) if sp.query else '')
        best, allow = -1, True
        for a, pat in self.rules:
            if self._match(pat, path):
                if len(pat) > best or (len(pat) == best and a): best, allow = len(pat), a
        return allow


def robots_verdict(status, body, ua):
    """-> ('parsed' | 'yes' | 'unreadable', RobotsTxt or None, why). The engine's read_robots rule (3.6), the same for every host."""
    if status == 200:
        txt = (body or b'').decode('utf-8', 'replace')
        if txt.lstrip('﻿ \t\r\n').startswith('<'): return 'unreadable', None, 'robots.txt answered with a web page, not a robots file: nothing read from this host this run'
        rb = RobotsTxt(txt, ua); return 'parsed', rb, f'robots.txt read ({rb.group})'
    if status == 429: return 'unreadable', None, 'robots.txt answered 429 (the server asks us to back off): nothing read from this host this run, tried next run'
    if 400 <= status < 500: return 'yes', None, f'robots.txt answered {status}: "unavailable" = no restrictions (RFC 9309 2.3.1.3)'
    return 'unreadable', None, f'robots.txt could not be read ({status or "no answer"}): nothing read from this host this run, tried next run'


REG_TLDS = {'gov', 'com', 'org', 'net', 'edu', 'mil', 'ca'}
CA_PROV = {'ab', 'bc', 'mb', 'nb', 'nl', 'ns', 'nt', 'nu', 'on', 'pe', 'qc', 'sk', 'yk'}


def registrable(host):
    """The registered domain of a host, or '' when unsure (the engine's rule: gc.ca, <province>.ca, gov.<province>.ca are suffixes)."""
    h = str(host or '').lower().rstrip('.')
    if not h or re.fullmatch(r'[\d.]+|\[?[0-9a-f:]+\]?', h) or '.' not in h: return ''
    p = h.split('.')
    if p[-1] not in REG_TLDS: return ''
    n = 2
    if p[-1] == 'ca' and len(p) >= 2 and (p[-2] == 'gc' or p[-2] in CA_PROV):
        n = 4 if len(p) >= 3 and p[-2] in CA_PROV and p[-3] in ('gov', 'gouv') else 3
    return '.'.join(p[-n:]) if len(p) > n else ''


def robots_hop_problem(old, new):
    """'' when a robots.txt redirect old -> new may be followed, else why not (the engine's rule)."""
    a, b = urllib.parse.urlsplit(old), urllib.parse.urlsplit(new)
    if b.scheme.lower() != 'https': return 'it points to a plain http address (only https is followed)'
    if '@' in b.netloc: return 'it carries a user name'
    if a.netloc.lower().rstrip('.') == b.netloc.lower().rstrip('.'): return ''
    try: pb = b.port
    except ValueError: return 'it has a bad port'
    if pb not in (None, 443): return 'it points to another port'
    ha, hb = (a.hostname or '').lower().rstrip('.'), (b.hostname or '').lower().rstrip('.')
    if ha == hb or ha == 'www.' + hb or hb == 'www.' + ha: return ''
    ra = registrable(ha)
    return '' if ra and ra == registrable(hb) else 'it points to another site'


def retry_after(headers, now, default=60.0):
    v = str((headers or {}).get('retry-after') or '').strip(); s = default
    if v.isdigit(): s = float(v)
    elif v:
        try: s = email.utils.parsedate_to_datetime(v).timestamp() - now
        except Exception: s = default  # noqa: BLE001
    return max(1.0, min(float(SETTINGS['retry_after_cap']), s))


def host_of(url): return urllib.parse.urlsplit(url).netloc.lower().rstrip('.')


class Manners:
    """Every live request of the research inbox. state_file keeps the per-host request times (hour / day caps) and any Retry-After
    across runs; robots.txt answers are kept for this run only (asked once per host per run). clock / sleep / opener are stubbed in tests."""

    def __init__(self, state_file, ua, clock=time.time, sleep=time.sleep, opener=open_url, refuse=None):
        self.state_file = pathlib.Path(state_file); self.ua = ua; self.clock, self.sleep, self.opener = clock, sleep, opener
        self.refuse = refuse or (lambda url: '')   # the caller's own never-read rules (a reason, or '')
        self.robots, self.crawl, self.last, self.backoff, self.noted, self.notes = {}, {}, {}, {}, set(), []
        self.times, self.not_before, self.dirty, self.slowed = {}, {}, False, set()
        try: d = json.load(open(self.state_file, encoding='utf-8'))
        except Exception: d = {}  # noqa: BLE001
        for h, v in ((d.get('hosts') or {}) if isinstance(d, dict) else {}).items():
            if not isinstance(v, dict): continue
            self.times[h] = [float(t) for t in v.get('t') or [] if isinstance(t, (int, float))]
            if isinstance(v.get('not_before'), (int, float)): self.not_before[h] = float(v['not_before'])
        self._prune()

    # ---- counters (kept between runs)
    def _prune(self):
        cut = self.clock() - DAY
        for h in list(self.times):
            self.times[h] = [t for t in self.times[h] if t > cut]
            if not self.times[h]: self.times.pop(h)
        for h in [h for h, t in self.not_before.items() if t <= self.clock()]: self.not_before.pop(h)

    def save(self):
        if not self.dirty: return
        self._prune()
        out = {'about': 'Research inbox request counts per host (UTC epoch seconds of each request in the last 24 hours) and any Retry-After '
                        '(not_before), so the 200 per hour / 1500 per day caps hold across runs (kpc_inbox_manners.py). Safe to delete.',
               'saved': datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC'),
               'hosts': {h: dict({'t': [round(t, 3) for t in sorted(self.times.get(h, []))]}, **({'not_before': round(self.not_before[h], 3)} if h in self.not_before else {}))
                         for h in sorted(set(self.times) | set(self.not_before))}}
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.state_file.with_name(self.state_file.name + '.tmp')
        json.dump(out, open(tmp, 'w', encoding='utf-8'), separators=(',', ':')); os.replace(tmp, self.state_file)
        self.dirty = False

    def cap_problem(self, host):
        now = self.clock(); ts = [t for t in self.times.get(host, []) if t > now - DAY]
        if len(ts) >= int(SETTINGS['per_host_per_day']): return f'cap reached for host {host} ({SETTINGS["per_host_per_day"]} requests per day)'
        if len([t for t in ts if t > now - HOUR]) >= int(SETTINGS['per_host_per_hour']): return f'cap reached for host {host} ({SETTINGS["per_host_per_hour"]} requests per hour)'
        return ''

    def note(self, host, line):
        """one plain line per host per run in the run notes"""
        if host in self.noted: return
        self.noted.add(host); self.notes.append(line); print(f'research inbox: {line}; its parks stay on the retry list for the next run')

    def gap(self, host): return max(float(SETTINGS['min_seconds_between_requests']), float(self.crawl.get(host) or 0.0))

    def _wait(self, host):
        target = max(self.last.get(host, -1e18) + self.gap(host), self.not_before.get(host, 0.0))
        w = target - self.clock()
        if w > 0: self.sleep(min(w, self.gap(host) + float(SETTINGS['retry_after_cap'])))

    def _send(self, url, accept, timeout, follow, cap=0):
        """paced, capped, counted, never-contact checked; -> Answer (raises Skip when no request was made, OSError when no answer)"""
        host = host_of(url)
        ok, why = kpc_net_guard.host_ok(url)
        if not ok: raise Skip(why)
        why = self.refuse(url)
        if why: raise Skip(why)
        c = self.cap_problem(host)
        if c: self.note(host, c); raise Skip(c)
        self._wait(host)
        self.last[host] = self.clock(); self.times.setdefault(host, []).append(self.clock()); self.dirty = True
        try: a = self.opener(url, accept, timeout, follow, cap, self.ua)
        finally: self.save()
        if a.status in (429, 503):   # Retry-After wins over our floor, and is kept for the next run
            self.not_before[host] = self.clock() + retry_after(a.headers, self.clock()); self.dirty = True; self.save()
        return a

    # ---- robots.txt
    def robots_check(self, url):
        """(True, '') or (False, why) for a live read of url. robots.txt is asked once per host per run."""
        host = host_of(url)
        if host in self.backoff: return False, self.backoff[host]
        if host not in self.robots:
            p = urllib.parse.urlsplit(url); cur = f'{p.scheme}://{p.netloc}/robots.txt'; seen = {cur}; verdict = None
            try:
                for hop in range(int(SETTINGS['robots_max_hops']) + 1):
                    a = self._send(cur, ROBOTS_ACCEPT, 25, False, int(SETTINGS['robots_max_bytes']))
                    if a.status in (301, 302, 303, 307, 308) and a.location:
                        nxt = a.location
                        prob = ('more than %d redirects' % SETTINGS['robots_max_hops']) if hop >= int(SETTINGS['robots_max_hops']) else \
                            ('a redirect loop' if nxt in seen else robots_hop_problem(cur, nxt) or ('' if kpc_net_guard.host_ok(nxt)[0] else kpc_net_guard.host_ok(nxt)[1]))
                        if prob: verdict = ('unreadable', None, f'robots.txt redirect to {host_of(nxt)} refused: {prob}: nothing read from this host this run'); break
                        seen.add(nxt); cur = nxt; continue
                    verdict = robots_verdict(a.status, a.body, self.ua)
                    break
            except Skip as e:
                if str(e).startswith('cap reached'): return False, str(e)   # not asked: the cap, tried again next run
                verdict = ('unreadable', None, f'robots.txt not asked ({e}): nothing read from this host this run')
            except Exception as e:  # noqa: BLE001  (no answer, timeout, refused by the guard)
                verdict = ('unreadable', None, f'robots.txt could not be read ({type(e).__name__}: no answer): nothing read from this host this run, tried next run')
            kind, rb, why = verdict
            if kind == 'unreadable': self.backoff[host] = f'{host}: {why}'; return False, self.backoff[host]
            cd = float(rb.crawl_delay) if rb else 0.0
            if cd > float(SETTINGS['skip_crawl_delay_over']):
                self.backoff[host] = f'{host}: robots.txt asks for {cd:g} s between requests (over {SETTINGS["skip_crawl_delay_over"]:g} s): skipped this run'
                return False, self.backoff[host]
            if cd: self.crawl[host] = cd
            self.robots[host] = rb   # None = no restrictions
        rb = self.robots[host]
        if rb is not None and not rb.allowed(url): return False, f'{host}: robots.txt disallows this path'
        return True, ''

    def get(self, url, timeout=90):
        """a live data read (robots.txt first) -> bytes. Raises Skip (no request made) or an error (the read failed)."""
        ok, why = self.robots_check(url)
        if not ok: raise Skip(why)
        host = host_of(url)
        a = self._send(url, 'application/json', timeout, True)
        if a.status in (429, 503) or a.status >= 500:
            if host in self.slowed: self.backoff[host] = f'{host}: answered {a.status} twice: nothing more read from this host this run, tried next run'
            self.slowed.add(host)
            raise Skip(f'{host}: answered {a.status} (back off): tried again next run')
        if a.status >= 400: raise urllib.error.HTTPError(url, a.status, f'HTTP {a.status}', None, None)
        return a.body


def manners_for(cache_dir, ua, **k):
    """the inbox's Manners, its counters kept next to the saved research outlines (the folder the workflow's cache carries over)"""
    return Manners(pathlib.Path(cache_dir) / COUNTS_NAME, ua, **k)
