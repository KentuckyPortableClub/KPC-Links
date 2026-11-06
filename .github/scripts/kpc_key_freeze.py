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
Never fails (a read error = not frozen, said in the notice).

Nov 4 2026 (links-04; Brandon, Super Head Bot chat, 4:51 AM CST Nov 4, relayed via Super Head Bot:
"In the new pr fix that issues so we no longer have that problem so once quality is done and we push problems solved and we on the new system"):
  * chat 11 is gone. A held build is released from the freeze only by a PERSON'S SIGN-OFF (FINAL-v2, Quality grade Nov 4 5:30 AM
    must-fix 1): 'by' is exactly one of KPC_PERSONS (default Brandon, KZ4CP; kpc_answer_words.persons / signed_off rules) and the
    sign-off is dated at or after the restart, 9:37 AM CST Nov 2 2026 (15:37 UTC). It is read from
      - KPC-Links data/status/key-check/verdicts/<build>.json {build, verdict, by, date}, or
      - a KPC-Data data/waiting/approved.json item what=<kind>, build=<id> with 'verdict', 'by' and a date.
    NOT a sign-off: a Quality note (Quality grades through the links-01 report; its note is a report, never an unfreeze), any bot,
    old chat 11 text (any 'chat11' field), a YES dated before the restart, a sign-off with no readable date or a future date.
    graded_no() is separate and stricter-safe: a NO / FAIL / WITHDRAWN from a person OR Quality (or old chat 11 text) still HOLDS
    2-fers on that build (the 2-fer pre-line check and the chain plan use it); it never unfreezes anything.
  * a held build NEVER blocks a new build when it was built on other RULES (no 'rules' hash in its stamp, or a hash that is not
    rules_hash(kind) of this checkout: the key's rule scripts + .github/key-rules-version.json), or when it is older than
    KPC_FREEZE_MAX_DAYS days (default 3, see NOTES). A 'built' date that cannot be read counts as EXPIRED (FINAL-v2 should-fix).
  * RULES_CHANGED=1 goes to $GITHUB_ENV when the newest build of this key was not a full build on the current rules: the plan then
    builds the WHOLE key (US: all states, not the nightly 'already built today' skip; Canada / world: not the nightly skip).
  * stamp stores 'rules' only for a FULL build with no failed part (env KPC_FULL_BUILD=1 from the plan); a partial build keeps the
    previous 'rules', so a partial build on new rules can never hide states still on old rules.
  * FORCE=yes still skips the freeze (by hand only).
Nothing is deleted: an old held build simply stops counting.

  rules us-key|ca-key|world-key   print the current rules hash (12 hex)"""
import base64, datetime, hashlib, json, os, pathlib, re, subprocess, sys, time

PRE = {'us-key': 'US', 'ca-key': 'CA', 'world-key': 'W'}
REPO = 'KentuckyPortableClub/KPC-Data'
# Nov 4 (links-04): the files whose content IS the key's rules. A change to any of them = a rules change. Not rules (they do not
# decide a join): kpc_host_pace.py (request pacing), kpc_save.py (file writer), the issue / answers / layers / lost-finds helpers.
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
VERSION_FILE = '.github/key-rules-version.json'
RULE_FILES = {'us-key': ['.github/scripts/kpc_us_key.py', '.github/scripts/kpc_key_rules.py', '.github/scripts/kpc_match.py'],
              'ca-key': ['.github/scripts/kpc_ca_key.py', '.github/scripts/kpc_ca_fill_bounds.py', '.github/scripts/kpc_ca_hardlook.py'],
              'world-key': ['.github/scripts/kpc_world_key.py', '.github/scripts/kpc_match.py',
                            '.github/scripts/kpc_number_rules.py']}   # next round v3 C10: same_name's one-side number test (world only; not US)
NOT_RULES = {'kpc_key_freeze.py', 'kpc_key_order.py', 'kpc_host_pace.py', 'kpc_save.py', 'kpc_us_key_issue.py', 'kpc_ca_key_issue.py', 'kpc_key_answers.py',
             'kpc_key_layers.py', 'kpc_ca_answers.py', 'kpc_world_answers.py', 'kpc_lost_finds.py', 'kpc_ca_whynot.py', 'kpc_overlay.sh',
             'kpc_save_overwrite.sh', 'kpc_push_data.sh',
             'kpc_join_check.py',
             # Nov 6: after the US builder. A state whose shape read is zero or under half the live key fails
             # the job instead of publishing pins. It does not decide a join (US rules hash stays a066624520b4).
             'kpc_shape_guard.py',
             # Nov 6 big patch (Quality grade FIX, Links #44): the source-field table and the tract side-file writer only write
             # data/*/tracts/ side files (KPC_TRACT_STORE) and never decide a join, so they stay out of the rules hash.
             'kpc_source_fields.py', 'kpc_tracts.py', 'kpc_pin_edge.py',
             # Nov 6 follow-up (report only, post-key check): 0.25 mi pin cover, 'also in' notes, the workbench name matcher
             'kpc_pin_cover.py', 'kpc_also_in.py', 'kpc_name_match.py',
             # Nov 6 research packs: catalog, name abbreviations and the would-change side report. Off by default
             # (KPC_RESEARCH_SOURCES). It never decides a join, so it stays out of the rules hash (Links #44/#45).
             'kpc_research_sources.py'}   # Nov 6 improvements 4 (v2): holds far joins after the builder, before the stamp; kept out of the rules hash on purpose (5:28 PM CST Nov 5: US stays 3dc53f70256a)
MAX_DAYS_DEFAULT = 3
GRADERS = ('quality', 'brandon', 'kz4cp')   # who may grade a build NO for graded_no() (a hold only, never an unfreeze)
NOT_PERSONS = ('quality', 'super', 'mapping', 'chat 11', 'chat11', 'bot')
# Nov 4 (links-10; per Brandon via Super Head Bot (relayed), 7:13 AM CST Nov 4: 'Yes, add distance and kind to the keys in this
# rebuild'): kpc_key_facts.py writes every key's per-park 'bk' (pin distance + record kind), so it is a rule file of all three keys.
for _kind in RULE_FILES: RULE_FILES[_kind].append('.github/scripts/kpc_key_facts.py')
# FINAL-v2 (must-fix 1): sign-offs dated before the restart (9:37 AM CST Nov 2 2026 = 15:37 UTC) never count.
RESTART = datetime.datetime(2026, 11, 2, 15, 37, tzinfo=datetime.timezone.utc)
DATE_KEYS = ('date', 'signed', 'when', 'approved_date', 'at')
NO_RE = r'\W*(KEY\s+)?(NO|FAIL|WITHDRAWN)\b'


def rules_hash(kind, root=None):
    """sha256 (12 hex) over this key's rule files + its line in .github/key-rules-version.json. A missing file counts as 'missing'."""
    root = pathlib.Path(root or ROOT); h = hashlib.sha256()
    for rel in sorted(RULE_FILES[kind]):
        f = root / rel
        h.update(rel.encode() + b'\0' + (f.read_bytes() if f.is_file() else b'missing') + b'\0')
    try: ver = json.load(open(root / VERSION_FILE, encoding='utf-8')).get(kind)
    except Exception: ver = None  # noqa: BLE001
    h.update(b'version\0' + str(ver).encode())
    return h.hexdigest()[:12]


def built_at(s):
    try: return datetime.datetime.strptime(str(s or ''), '%Y-%m-%d %H:%M UTC').replace(tzinfo=datetime.timezone.utc)
    except Exception: return None  # noqa: BLE001


def max_days():
    try: return max(0.0, float(os.environ.get('KPC_FREEZE_MAX_DAYS') or MAX_DAYS_DEFAULT))
    except ValueError: return float(MAX_DAYS_DEFAULT)


def not_blocking(stamp, kind, now=None, rules=None):
    """'' when this held build may still block a new build; else why it never blocks (other rules / too old)."""
    rules = rules or rules_hash(kind)
    r = str((stamp or {}).get('rules') or '')
    if not r: return f"built before rules hashes existed (no 'rules' in its stamp): superseded by the current rules {rules}"
    if r != rules: return f'built on other rules ({r}; now {rules}): superseded'
    t = built_at((stamp or {}).get('built')); now = now or datetime.datetime.now(datetime.timezone.utc)
    if t is None:   # FINAL-v2 should-fix: a build date that cannot be read counts as expired (it never blocks forever)
        return f"its build date cannot be read ({(stamp or {}).get('built')!r}): counted as expired, it no longer blocks"
    if (now - t).total_seconds() > max_days() * 86400:
        return f"older than {max_days():g} days (built {(stamp or {}).get('built')}): it no longer blocks"
    return ''


def _persons():
    try:
        sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); import kpc_answer_words as AW   # noqa: E402
        who = AW.persons(os.environ.get('KPC_PERSONS'))
    except Exception: who = {'brandon', 'kz4cp'}  # noqa: BLE001
    return {w for w in who if not any(n in w for n in NOT_PERSONS)}   # a Quality / bot name can never be made a person by config


def signed_when(rec):
    """The sign-off time of a verdict record (UTC), or None when no date can be read. Accepts 'YYYY-MM-DD HH:MM UTC', ISO 8601 with
    a zone, 'YYYY-MM-DD HH:MM CST|CDT', or a bare date (YYYY-MM-DD = the START of that day in CST: a bare Nov 2 is before the restart)."""
    for k in DATE_KEYS:
        s = str((rec or {}).get(k) or '').strip()
        if not s: continue
        t = built_at(s)
        if t: return t
        m = re.match(r'^(\d{4}-\d{2}-\d{2})[ T](\d{1,2}):(\d{2})\s*(CST|CDT)$', s)
        if m:
            off = -6 if m.group(4) == 'CST' else -5
            d = datetime.datetime.fromisoformat(f'{m.group(1)}T{int(m.group(2)):02d}:{m.group(3)}')
            return (d - datetime.timedelta(hours=off)).replace(tzinfo=datetime.timezone.utc)
        try:
            d = datetime.datetime.fromisoformat(s.replace('Z', '+00:00'))
            if d.tzinfo: return d.astimezone(datetime.timezone.utc)
            if len(s) == 10: return (d + datetime.timedelta(hours=6)).replace(tzinfo=datetime.timezone.utc)   # bare date: 00:00 CST
        except ValueError: pass
    return None


def is_person(by):
    """kpc_answer_words.signed_off rule: one of the comma / semicolon / plus / ampersand / 'and' separated names is EXACTLY a person.
    'Quality', 'Brandon via Super', 'not Brandon' and bots are not."""
    names = {n.strip().lower() for n in re.split(r'[,;+&]|\band\b', str(by or '')) if n.strip()}
    return bool(names & _persons())


def signoff_why(rec, now=None):
    """'' when rec is a person's sign-off that counts; else why it does not count."""
    now = now or datetime.datetime.now(datetime.timezone.utc)
    if not str((rec or {}).get('verdict') or '').strip(): return 'no verdict text' + (' (old chat 11 text never counts)' if (rec or {}).get('chat11') else '')
    if not is_person(rec.get('by')): return f"by {rec.get('by')!r} is not a person's sign-off (only {', '.join(sorted(_persons()))}; a Quality note is a report)"
    w = signed_when(rec)
    if w is None: return 'no readable sign-off date'
    if w < RESTART: return f'signed {w:%Y-%m-%d %H:%M} UTC, before the 9:37 AM CST Nov 2 restart'
    if w > now + datetime.timedelta(hours=1): return f'signed in the future ({w:%Y-%m-%d %H:%M} UTC)'
    return ''


def _records(kind, bid, items, links_root):
    f = pathlib.Path(links_root or '.') / 'data/status/key-check/verdicts' / f'{bid}.json'
    try:
        v = json.load(open(f, encoding='utf-8'))
        if isinstance(v, dict) and str(v.get('build') or bid) == bid: yield v, f'verdicts/{bid}.json'
    except Exception: pass  # noqa: BLE001
    for it in items or []:
        if isinstance(it, dict) and it.get('what') == kind and (str(it.get('build') or '') == bid or bid in str(it.get('chat11') or '') + str(it.get('verdict') or '')):
            yield it, 'approved.json'


def verdict(kind, bid, items, links_root=None, now=None):
    """(text, by) of the newest PERSON'S SIGN-OFF for this build (verdict file first, then approved.json), or None.
    FINAL-v2: only KPC_PERSONS (Brandon, KZ4CP), dated at or after the 9:37 AM CST Nov 2 restart; Quality notes, bots and old
    chat 11 text never count."""
    hit = None
    for rec, _where in _records(kind, bid, items, links_root):
        if not signoff_why(rec, now): hit = (str(rec['verdict']).strip(), str(rec.get('by')))
        if hit and _where.startswith('verdicts/'): return hit
    return hit


def graded_no(kind, bid, items, links_root=None):
    """(text, by) when a person, Quality or old chat 11 text graded this build NO / FAIL / WITHDRAWN, else None. A HOLD signal for
    2-fers only (the safe direction); it never unfreezes a key build."""
    for rec, _where in _records(kind, bid, items, links_root):
        for key, by in (('verdict', rec.get('by')), ('chat11', 'chat 11 (old)')):
            txt = str(rec.get(key) or '').strip()
            if txt and re.match(NO_RE, txt.upper()) and (key == 'chat11' or str(by or '').strip().lower().startswith(GRADERS) or is_person(by)):
                return txt, str(by)
    return None


def _env(**kv):
    env = os.environ.get('GITHUB_ENV')
    if env:
        with open(env, 'a') as f: f.write(''.join(f'{k}={v}\n' for k, v in kv.items()))


def notice(m): print(f'::notice title=Key build freeze::{m}', flush=True)


def gh_json(path):
    r = subprocess.run(['gh', 'api', f'repos/{REPO}/contents/{path}', '--jq', '.content'], capture_output=True, text=True)
    if r.returncode != 0 or not r.stdout.strip(): return None
    try: return json.loads(base64.b64decode(r.stdout.strip()).decode('utf-8'))
    except Exception:  # noqa: BLE001  (big files come back without content: ask the raw media type)
        r = subprocess.run(['gh', 'api', '-H', 'Accept: application/vnd.github.raw', f'repos/{REPO}/contents/{path}'], capture_output=True, text=True)
        try: return json.loads(r.stdout)
        except Exception: return None  # noqa: BLE001


def _git(*a, cwd=None, timeout=120):
    try: r = subprocess.run(['git', *a], cwd=cwd, capture_output=True, timeout=timeout)
    except Exception: return 1, b''  # noqa: BLE001
    return r.returncode, r.stdout


def load_index(kind, ref=None, cwd=None):
    """Nov 4 PM fix bundle (item 1; Brandon's yes relayed via Super Head Bot, 4:53 PM CST Nov 4). The stamp a decision is made on.
    KPC_INDEX_REF unset = this checkout's data/<kind>/index.json (as before). KPC_INDEX_REF=origin/main = the NEWEST main's copy
    (fetched now): a queued run's checkout is the commit of the moment it was queued, so its index can be older than main (the
    9:43 AM CST Nov 4 boundary check read the Nov 3 stamp US-41695918852 although US-41846994942 had been saved a minute before it
    started, and a queued second Canada start read the stamp from before the first one). Falls back to the checkout's copy."""
    p = f'data/{kind}/index.json'
    ref = (os.environ.get('KPC_INDEX_REF') or '').strip() if ref is None else ref
    if ref:
        tgt = ref
        if ref.startswith('origin/'):
            rc, _ = _git('fetch', '-q', '--depth', '1', 'origin', ref.split('/', 1)[1], cwd=cwd)
            if rc == 0: tgt = 'FETCH_HEAD'
        rc, out = _git('show', f'{tgt}:{p}', cwd=cwd)
        if rc == 0:
            try:
                d = json.loads(out.decode('utf-8'))
                if isinstance(d, dict): return d
            except Exception: pass  # noqa: BLE001
        notice(f'{kind}: could not read {p} at {ref}: the checkout\'s copy is used')
    try:
        d = json.load(open(os.path.join(cwd or '.', p), encoding='utf-8'))
        return d if isinstance(d, dict) else {}
    except Exception: return {}  # noqa: BLE001


# Nov 4 PM fix bundle (item 2): what a build of each key was made FROM, besides its rules: the builds of the keys before it in the
# build order (kpc_key_order.py WAIT_FOR). A chained start whose newest build has the same rules_of_run and the same inputs skips.
INPUTS = {'us-key': (), 'ca-key': ('us-key',), 'world-key': ('us-key', 'ca-key')}


def inputs_of(kind, ref=None, cwd=None):
    return {k: str(load_index(k, ref, cwd).get('build') or '') for k in INPUTS.get(kind, ())}


def _committed_rules(kind):
    """the 'rules' / 'rules_files' of this key's index as committed at HEAD (the builders rewrite index.json with only
    previous_build / previous_built, so the previous rules hash was lost on every partial build: item 1)"""
    rc, out = _git('show', f'HEAD:data/{kind}/index.json')
    if rc != 0: return {}
    try: o = json.loads(out.decode('utf-8'))
    except Exception: return {}  # noqa: BLE001
    return {k: o[k] for k in ('rules', 'rules_files') if isinstance(o, dict) and o.get(k)}


# Key hotfix (Nov 5; Brandon's approval relayed via Super Head Bot 4:21 AM CST): only a key's own answer key workflow stamps it (the
# by-hand key measure with commit=yes too). In GitHub Actions (GITHUB_WORKFLOW_REF set) any other workflow is refused: the boundary
# check stamped the live US index as US-41995722306 at 2:36 AM CST Nov 5.
STAMPERS = {'us-key': ('kpc-us-key.yml', 'kpc-key-measure.yml'), 'ca-key': ('kpc-ca-key.yml', 'kpc-key-measure.yml'),
            'world-key': ('kpc-world-key.yml', 'kpc-key-measure.yml')}


def may_stamp(kind, ref=None):
    ref = os.environ.get('GITHUB_WORKFLOW_REF', '') if ref is None else ref
    if not ref: return True   # a local run / the tests
    wf = ref.split('@')[0].rsplit('/', 1)[-1]
    return wf in STAMPERS.get(kind, ())


def stamp(kind):
    p = f'data/{kind}/index.json'
    if not may_stamp(kind):
        print(f"::error title=kpc_key_freeze.py::{kind} NOT stamped: {os.environ.get('GITHUB_WORKFLOW_REF')} is not this key's answer key workflow "
              f"({' / '.join(STAMPERS.get(kind, ()))}); the index is left as it is")
        return
    try: d = json.load(open(p, encoding='utf-8'))
    except Exception: d = {}  # noqa: BLE001
    # Nov 4 PM fix bundle (item 1): links-04 meant 'a partial build keeps the previous rules', but the builders' index write drops
    # them, so the 9:43 AM CST boundary check (a 3-state rebuild) was stamped 'rules none' and the next nightly rebuilt the WHOLE US key,
    # then Canada and the world. The previous hash now comes back from the committed index when the builder dropped it.
    if not d.get('rules'):
        for k, v in _committed_rules(kind).items(): d.setdefault(k, v)
    # Nov 4 PM fix bundle (item 2): the rules this run was built on (also for a partial or failed build) and its inputs
    d['rules_of_run'] = rules_hash(kind)
    if INPUTS.get(kind): d['inputs'] = inputs_of(kind)
    bid = f"{PRE[kind]}-{os.environ.get('GITHUB_RUN_ID') or time.strftime('%Y%m%d%H%M')}"
    d['build'] = bid; d['built'] = time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime())
    # Nov 2 review (Mapping #18): parts that failed in this build are named in the stamp (KPC_BUILD_FAILED_FILE = one code per line)
    failed = []
    ff = os.environ.get('KPC_BUILD_FAILED_FILE')
    if ff and os.path.exists(ff):
        failed = sorted({l.strip() for l in open(ff, encoding='utf-8') if l.strip()})
    if failed: d['failed'] = failed; d['complete'] = False
    else: d.pop('failed', None); d.pop('complete', None)
    # Nov 4 (links-04): the rules hash goes with a FULL build that has no failed part; otherwise the previous one stays
    if os.environ.get('KPC_FULL_BUILD') == '1' and not failed: d['rules'] = rules_hash(kind); d['rules_files'] = sorted(RULE_FILES[kind]) + [VERSION_FILE]
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(d, open(p, 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    notice(f'{kind} build stamped {bid} (rules {d.get("rules") or "none: not a full build"}): Brandon / KZ4CP sign off THIS build (data/status/key-check/verdicts/{bid}.json); the Quality report is data/status/key-check/'
           + (f" -- NOT a full build: {len(failed)} part(s) failed: {' '.join(failed[:20])}" if failed else ''))
    print(bid)


def check(kind, now=None):
    """Nov 4 (links-04). FROZEN only while the newest held build of this key (KPC-Links' own stamp or KPC-Data's waiting room) was
    built on the CURRENT rules, is at most KPC_FREEZE_MAX_DAYS old, and has no person's sign-off yet (Brandon / KZ4CP, after the restart; or a YES whose
    answers wait for their release). Returns (frozen, build, why) for the tests."""
    rules = rules_hash(kind)
    live = load_index(kind)   # Nov 4 PM fix bundle (item 1): KPC_INDEX_REF=origin/main = the newest main's stamp, not a stale checkout's
    lbid = str((live or {}).get('build') or '')
    if str((live or {}).get('rules') or '') != rules:   # the newest build here was not a full build on the current rules
        _env(RULES_CHANGED=1)
        notice(f"{kind}: RULES CHANGED: the newest build ({lbid or 'none'}) has rules {(live or {}).get('rules') or 'none'}, the current rules are {rules}: the next run builds the WHOLE key")
    if (os.environ.get('FORCE') or '').lower() in ('yes', 'true', '1'):
        notice(f'{kind}: freeze skipped by hand (force)'); return (False, '', 'force')
    held = gh_json(f'data/waiting/in/data/{kind}/index.json') or {}
    hbid = str(held.get('build') or '')
    ap = gh_json('data/waiting/approved.json') or {}
    items = ap.get('items') if isinstance(ap, dict) else ap
    used = None
    for bid, st, where in ((lbid, live, f'KPC-Links data/{kind}/index.json'), (hbid, held, 'the KPC-Data waiting room')):
        if not bid or (where.startswith('the') and bid == lbid): continue
        why = not_blocking(st, kind, now, rules)
        if why: notice(f'{kind}: build {bid} ({where}) does not block: {why}'); continue
        v = verdict(kind, bid, items, None, now)
        if not v:
            _env(FROZEN=1, FROZEN_BUILD=bid)
            notice(f"{kind}: FROZEN: build {bid} ({where}, built {st.get('built')}, current rules) waits for a person's sign-off "
                   f"(Brandon / KZ4CP: data/status/key-check/verdicts/{bid}.json or an approved.json item, dated after the Nov 2 restart; a Quality note is a report, not a sign-off); it stops blocking after {max_days():g} days; force=yes by hand skips")
            return (True, bid, 'ungraded')
        text = v[0].upper()
        yes = text.lstrip('*" ').startswith(('YES', 'PASS', 'KEY YES', 'KEY PASS'))
        if yes and bid == hbid:
            used = gh_json('data/waiting/approved-used.json') if used is None else used
            if not any(bid in k and f'"what": "{kind}"' in k for k in (used or {})):   # Brandon Nov 2: no new build until the answers are RELEASED
                _env(FROZEN=1, FROZEN_BUILD=bid)
                notice(f'{kind}: FROZEN: build {bid} is graded ({text[:40]}, by {v[1]}) and waits for its release; it stops blocking after {max_days():g} days')
                return (True, bid, 'graded, not released')
        notice(f'{kind}: build {bid} has a sign-off by a person ({text[:40]}, by {v[1]}): a new build may start')
    notice(f'{kind}: nothing blocks: building is allowed'); return (False, '', 'free')


if __name__ == '__main__':
    try:
        mode, kind = sys.argv[1], sys.argv[2]
        if mode == 'rules': print(rules_hash(kind))
        else: (stamp if mode == 'stamp' else check)(kind)
    except Exception as e: notice(f'stopped: {str(e)[:200]}')  # noqa: BLE001
    sys.exit(0)
