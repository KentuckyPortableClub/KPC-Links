#!/usr/bin/env python3
"""KPC test keys on this PC (22 Nov 2026, owner: "set up our test so we can do larger chunks and work through us and canada
quickly and easy"): build the answer keys for any states and Canada from the SAVED copies only and report, in counts, what
changed against the key on the website today AND against this PC's last test of the same state. Nothing is downloaded from
any map server, nothing is uploaded or published, nothing on GitHub changes. Kentucky uses its own key builder (Node.js);
the other states the US key builder; Canada the Canada key builder (one run for all provinces).

  py -3 kpc_test_keys.py                 asks (Enter = KY FL TX)
  py -3 kpc_test_keys.py FL TX GA        these states
  py -3 kpc_test_keys.py US              every state
  py -3 kpc_test_keys.py CA              Canada
  py -3 kpc_test_keys.py US CA           everything
Results: reports\\test-<date-time>\\REPORT.txt (counts only; safe to send to Claude, written after every state) and one
.log per state.

23 Nov 2026 (owner: "update pc version to reflect"): the report's first lines now say WHICH rules, park facts and kit
updates this test ran, so a report can always be matched to the rules on GitHub. Three inputs the GitHub build has and this
kit did not are now given the same way: the Recreation.gov saved copy (data/access-leads), the official sizes file made
from the park facts (data/acres.json, made fresh each run), and Canada's official pins file (KPC_OFFICIAL_PINS).
"""
import datetime, json, os, pathlib, re, shutil, subprocess, sys, time

HERE = pathlib.Path(__file__).resolve().parent
LINKS = HERE / 'links'
ORIG = HERE / 'originals'          # the website's key, kept once per state, so every test compares with the same thing
LAST = HERE / 'last-test'          # this PC's last test of each state, to see what the newest change did
STORE = HERE.parent / 'Tools' / 'KPC-TOOLS-NOV14' / '1-STORE-TOOL' / 'kpc-outline-store-full' / 'results' / 'store'
US_ALL = ('AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA '
          'RI SC SD TN TX UT VT VA WA WV WI WY').split()


def say(*a):
    print(*a, flush=True)


def keyfiles(st):
    if st == 'KY': return [LINKS / 'data/ky-answer-key.json']
    if st == 'CANADA': return sorted((LINKS / 'data/ca-key').glob('CA-*.json'))
    return [LINKS / f'data/us-key/US-{st}.json']


def load(p):
    try: return json.loads(pathlib.Path(p).read_text(encoding='utf-8'))
    except (OSError, ValueError): return None


def joins(p):
    """{park: set of joined record ids} and {park: number of check rows} of one key file."""
    d = load(p) or {}
    J, C = {}, {}
    for ref, row in (d.get('parks') or {}).items():
        if not isinstance(row, dict): continue
        ids = row.get('m') if 'm' in row else row.get('tracts')
        J[ref] = {str(x[0]) for x in ids or [] if isinstance(x, (list, tuple)) and x}
        C[ref] = len(row.get('c') or [])
    return J, C


def far_outlined(p, km=5.0):
    """23 Nov 2026 (owner 6:34 PM; log-rule idea 5, report only): parks joined to land that NOTHING else confirms (status
    'outlined': no id, link, page or size proof) whose POTA pin lies more than 5 km from that land ('bk' distance). Counts only."""
    d = load(p) or {}
    n = 0
    for row in (d.get('parks') or {}).values():
        if not isinstance(row, dict) or not row.get('m'): continue
        bk = row.get('bk') or []
        if (row.get('match') or {}).get('status') == 'outlined' and len(bk) > 1 and isinstance(bk[1], (int, float)) and bk[1] > km: n += 1
    return n


def compare(label, old, new):
    """Counts: what the new key changed against an older one."""
    oJ, oC = joins(old); nJ, nC = joins(new)
    refs = set(oJ) | set(nJ)
    n = {'parks': len(nJ), 'parks_before': len(oJ),
         'outline': sum(1 for v in nJ.values() if v), 'outline_before': sum(1 for v in oJ.values() if v),
         'gained': sum(1 for r in refs if nJ.get(r, set()) - oJ.get(r, set())),
         'lost': sum(1 for r in refs if oJ.get(r, set()) - nJ.get(r, set())),
         'to_pin': sum(1 for r in refs if oJ.get(r) and not nJ.get(r)),
         'from_pin': sum(1 for r in refs if nJ.get(r) and not oJ.get(r)),
         'check': sum(nC.values()), 'check_before': sum(oC.values()), 'far_outlined': far_outlined(new)}
    return [f'  {label}: {n["parks"]} parks ({n["parks_before"]} before); with an outline {n["outline"]} (before {n["outline_before"]}); '
            f'gained a record {n["gained"]}, lost a record {n["lost"]}; outline to pin {n["to_pin"]}, pin to outline {n["from_pin"]}; '
            f'check rows {n["check"]} (before {n["check_before"]}); outlined only with the pin over 5 km off {n["far_outlined"]}'], n



def check_row_collapse_lines(key_roots):
    """24 Nov 2026 (owner approved D; review fix): report-only collapse of check rows, by reason class.
    Counts only; the key's c rows are not rewritten. Looks for US-*.json under each root (data/us-key)."""
    scripts = (HERE / 'links' / '.github' / 'scripts')
    if not scripts.is_dir():
        scripts = HERE.parents[1] / '.github' / 'scripts'
    if scripts.is_dir() and str(scripts) not in sys.path:
        sys.path.insert(0, str(scripts))
    try:
        import kpc_cleanup_report as CR
    except ImportError:
        return ['Check rows: the collapse report could not be loaded (kpc_cleanup_report.py was not found).']
    lines, seen = [], set()
    for root in key_roots:
        root = pathlib.Path(root)
        keys_dir = root if (root.is_dir() and any(root.glob('US-*.json'))) else root / 'data' / 'us-key'
        if not keys_dir.is_dir() or not any(keys_dir.glob('US-*.json')):
            continue
        key = str(keys_dir.resolve())
        if key in seen:
            continue
        seen.add(key)
        rows = CR.rows_from_key_dir(keys_dir)
        lines.append(CR.report_line(CR.collapse_summary(rows)))
    return lines


def notices(log):
    """The builder's own count lines for the report (never a park name)."""
    out = []
    for ln in log.splitlines():
        m = re.search(r'::notice title=(?:US key [A-Z]{2}|Canada key[^:]*)::(match checks: .*)', ln)
        if m: out.append('  ' + m.group(1)[:900])
        elif ln.startswith('Recreation.gov saved copy') and not any('Recreation.gov' in o for o in out): out.append('  ' + ln.strip()[:160])
        elif '::notice title=Boundary check::' in ln: out.append('  pins: ' + ln.split('::', 2)[-1].replace('%25', '%').strip()[:300])
        elif re.search(r'::(error|warning) title=', ln) or 'golden cases' in ln or 'US key STOPPED' in ln:
            out.append('  ' + re.sub(r'(US|CA)-\d{3,5}', r'\1-####', ln.strip())[:300])
    return out[:16]


def store_attrs():
    """The outline store's agency id fields for the match checks (KPC_RECORD_ATTRS); '' when the store is not on this PC."""
    out = LINKS / '.pf' / 'record-attrs.json.gz'
    if not STORE.is_dir():
        say(f'  (the outline store folder is not at {STORE}: the id checks use the saved copies only)')
        return ''
    newest = max((p.stat().st_mtime for p in STORE.glob('*.kpcstore.json.gz')), default=0)
    fmt = 0
    if out.is_file():   # 24 Nov: a file made before the '@' fix and the name-and-size index with map boxes (format 3) is made again
        try:
            import gzip
            with gzip.open(out, 'rt', encoding='utf-8') as fh: fmt = int(json.load(fh).get('format') or 0)
        except Exception: fmt = 0  # noqa: BLE001
    if not out.is_file() or out.stat().st_mtime < newest or fmt < 5:   # 25 Nov (B1, #379): format 5 keeps every re-found record apart, with its name and size
        say('  reading the agency id fields from the outline store (once, about a minute)...')
        out.parent.mkdir(exist_ok=True)
        subprocess.run([sys.executable, '-X', 'utf8', '.github/scripts/kpc_store_attrs.py', '--store', str(STORE), '--out', str(out)], cwd=LINKS)
    return str(out) if out.is_file() else ''


def park_facts():
    f = HERE / 'park-facts.json.gz' if (HERE / 'park-facts.json.gz').is_file() else LINKS / '.pf' / 'data' / 'park-facts.json.gz'
    return str(f)


def kit_lines():
    """Which rules, park facts and kit updates this test runs (so a report can be matched to GitHub). Never a park name."""
    out = []
    try:
        code = ("import sys; sys.path.insert(0, '.github/scripts'); import kpc_key_freeze as K; "
                "print('US ' + K.rules_hash('us-key') + ', Canada ' + K.rules_hash('ca-key'))")
        r = subprocess.run([sys.executable, '-X', 'utf8', '-c', code], cwd=LINKS, capture_output=True, text=True, timeout=180)
        out.append('Rules on this PC: ' + (r.stdout.strip() or 'could not be read') + '. (The same numbers as GitHub = the same rules.)')
    except Exception as e:  # noqa: BLE001
        out.append(f'Rules on this PC: could not be read ({str(e)[:60]}).')
    try:
        import gzip
        with gzip.open(park_facts(), 'rt', encoding='utf-8') as fh: head = fh.read(4000)
        made = re.search(r'"made":\s*"([^"]+)"', head); tool = re.search(r'"tool":\s*"([^"]+)"', head)
        out.append(f"Park facts: made {made.group(1) if made else '?'} by {tool.group(1) if tool else '?'}.")
    except Exception:  # noqa: BLE001
        out.append('Park facts: not found on this PC (the match checks have nothing to read).')
    ups = sorted(p.name.replace('.done-', '') for p in LINKS.glob('.done-*'))
    out.append('Kit updates added: ' + (', '.join(ups) if ups else 'none after 22 Nov') + '.')
    # 24 Nov plan B: park-facts hash, page-reader version, restock stamps, rule changes since last test
    try:
        import sys as _sys
        _sys.path.insert(0, str(LINKS / '.github' / 'scripts'))
        import kpc_confirm_report as _CR
        last = ''
        last_rep = HERE / 'last-test' / 'RULES.txt'
        if last_rep.is_file():
            last = last_rep.read_text(encoding='utf-8').split()[0] if last_rep.stat().st_size else ''
        states = [s for s in (os.environ.get('STATES') or '').upper().replace(',', ' ').split() if s and s not in ('US', 'CA', 'KY', 'CANADA')]
        extra = _CR.header_lines(root=LINKS, facts_path=park_facts(),
                                 cache_dir=str(LINKS / 'cache' / 'us'),
                                 states=states or None,
                                 last_rules=os.environ.get('KPC_LAST_TEST_RULES') or last)
        # drop the rules line (kit_lines already printed it) and keep the rest
        out.extend(x for x in extra if not x.startswith('Rules this run:'))
    except Exception as e:  # noqa: BLE001
        out.append(f'Confirm-report stamps skipped ({str(e)[:80]}).')
    return out


def official_sizes():
    """As the GitHub build does before the key: the official sizes file (data/acres.json), made fresh from the park facts."""
    tool, pf, out = LINKS / '.github/scripts/kpc_park_facts_read.py', park_facts(), LINKS / 'data' / 'acres.json'
    if not tool.is_file() or not os.path.isfile(pf): return
    try:
        if out.is_file(): out.unlink()
        subprocess.run([sys.executable, '-X', 'utf8', str(tool), 'acres', '--out', 'data/acres.json'], cwd=LINKS,
                       env=dict(os.environ, PARK_FACTS=pf, PYTHONUTF8='1', PYTHONIOENCODING='utf-8'), capture_output=True, timeout=300)
    except Exception as e:  # noqa: BLE001
        say(f'  (the official sizes file was not made: {str(e)[:80]})')


def run_build(st, rep, attrs):
    if st == 'KY':
        node = shutil.which('node')
        if not node: return None, 'KY: Node.js is not installed, so the Kentucky key could not be built. Install the free "LTS" version from nodejs.org and run this again.'
        cmd, env = [node, '.github/scripts/kpc_ky_key.js'], dict(os.environ)
    else:
        pf = park_facts()
        common = dict(os.environ, GEO_CACHE_MODE='only', GEO_DETAIL='0.001', KPC_KEY_OFFLINE='1', GEO_PAGE='200', KPC_MASTER_OWNS='1',
                      MINUTES='600', PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONUNBUFFERED='1', PARK_FACTS=pf)
        if attrs: common['KPC_RECORD_ATTRS'] = attrs
        if st == 'CANADA':
            if not (LINKS / 'cache' / 'ca' / 'CA-ALL.json.gz').is_file(): return None, 'Canada: no saved copy in links\\cache\\ca (CA-ALL.json.gz); skipped'
            env = dict(common, GEO_CACHE=str(LINKS / 'cache' / 'ca'), KPC_CA_HAND=str(LINKS / 'cache' / 'ca-hand'))
            if (LINKS / '.op/data/intake/official-pins-nov12.json').is_file():   # as kpc-ca-key.yml gives it (read only)
                env['KPC_OFFICIAL_PINS'] = '.op/data/intake/official-pins-nov12.json'
            cmd = [sys.executable, '-X', 'utf8', '.github/scripts/kpc_ca_key.py']
        else:
            if not (LINKS / 'cache' / 'us' / f'US-{st}.json.gz').is_file():
                return None, f'{st}: no saved copy in links\\cache\\us (US-{st}.json.gz); skipped'
            env = dict(common, STATES=st, GEO_CACHE=str(LINKS / 'cache' / 'us'))
            cmd = [sys.executable, '-X', 'utf8', '.github/scripts/kpc_us_key.py']
    kept = []
    with open(rep / f'{st}.log', 'w', encoding='utf-8', errors='replace') as lf:
        if st == 'CANADA':   # store mode: the hard-look file is set aside for the build and put back after (as on GitHub)
            subprocess.run([sys.executable, '-X', 'utf8', '.github/scripts/kpc_ca_store_keep.py', 'aside'], cwd=LINKS, env=env)
        p = subprocess.Popen(cmd, cwd=LINKS, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                             encoding='utf-8', errors='replace', bufsize=1)
        for ln in p.stdout:
            lf.write(ln); lf.flush(); kept.append(ln)
            print('    ' + re.sub(r'(US|CA)-\d{3,5}', r'\1-####', ln.rstrip())[:160], flush=True)
        p.wait()
        if st == 'CANADA':
            subprocess.run([sys.executable, '-X', 'utf8', '.github/scripts/kpc_ca_store_keep.py', 'back'], cwd=LINKS, env=env)
    return p.returncode, ''.join(kept)


def run_state(st, rep, attrs, tot):
    ORIG.mkdir(exist_ok=True); LAST.mkdir(exist_ok=True)
    for kf in keyfiles(st):   # the website's key, kept once, and put back before each build so every test starts the same
        if kf.is_file() and not (ORIG / kf.name).is_file(): shutil.copy2(kf, ORIG / kf.name)
        if (ORIG / kf.name).is_file(): shutil.copy2(ORIG / kf.name, kf)
    say(f'  building {st} ... (its progress lines show below)')
    t0 = time.time()
    rc, log = run_build(st, rep, attrs)
    if rc is None: return [log]
    mins = (time.time() - t0) / 60
    lines = [f'{st}: built in {mins:.1f} minutes (exit {rc}).']
    tot['minutes'] = tot.get('minutes', 0) + mins
    if rc != 0:
        tail = [l for l in log.splitlines() if l.strip()][-4:]
        return lines + ['  it stopped with an error; the last lines of its log:'] + ['    ' + re.sub(r'(US|CA)-\d{3,5}', r'\1-####', l)[:300] for l in tail]
    for kf in keyfiles(st):
        tag = kf.stem
        if (ORIG / kf.name).is_file():
            l, n = compare(f'{tag} against the website', ORIG / kf.name, kf); lines += l
            for k, v in n.items(): tot[k] = tot.get(k, 0) + v
        else:
            lines.append(f'  {tag}: no website key to compare with')
        if (LAST / kf.name).is_file():
            lines += compare(f"{tag} against this PC's last test", LAST / kf.name, kf)[0]
        shutil.copy2(kf, LAST / kf.name)
    return lines + notices(log)


def main(argv):
    want = [a.upper() for a in argv if a.strip()]
    if not want:
        say('Type the states with a space between them (US = every state, CA = Canada), or just press Enter for KY FL TX.')
        want = input('States: ').upper().split() or ['KY', 'FL', 'TX']
    order = []
    for a in want:
        for s in (US_ALL if a == 'US' else ['CANADA'] if a in ('CA', 'CANADA') else [a]):
            if s not in order: order.append(s)
    rep = HERE / 'reports' / ('test-' + datetime.datetime.now().strftime('%Y-%m-%d-%H%M'))
    rep.mkdir(parents=True, exist_ok=True)
    attrs = store_attrs() if any(s != 'KY' for s in order) else ''
    if any(s != 'KY' for s in order): official_sizes()
    out = [f'KPC test keys, {datetime.datetime.now():%d %b %Y %I:%M %p}. Saved copies only: nothing was downloaded or uploaded.',
           'Counts only, no park names. "website" = the key on the website today; "last test" = this PC\'s previous test of that state.',
           f'Store id fields: {"used" if attrs else "not found (saved copies only)"}.'] + kit_lines() + ['']
    tot = {}
    for st in order:
        say(f'{st}:')
        out += run_state(st, rep, attrs, tot) + ['']
        (rep / 'REPORT.txt').write_text('\n'.join(out) + '\n', encoding='utf-8')   # after every state: a closed window keeps what was done
    if len(order) > 1 and tot:
        out += ['ALL OF THEM against the website: '
                f'{tot.get("parks", 0)} parks; with an outline {tot.get("outline", 0)} (before {tot.get("outline_before", 0)}); '
                f'gained a record {tot.get("gained", 0)}, lost a record {tot.get("lost", 0)}; outline to pin {tot.get("to_pin", 0)}, '
                f'pin to outline {tot.get("from_pin", 0)}; check rows {tot.get("check", 0)} (before {tot.get("check_before", 0)}); '
                f'outlined only with the pin over 5 km off {tot.get("far_outlined", 0)} (report only: the owner decides); '
                f'{tot.get("minutes", 0):.0f} minutes in all.']
    out += [''] + check_row_collapse_lines([LINKS / 'data' / 'us-key', LINKS])
    (rep / 'REPORT.txt').write_text('\n'.join(out) + '\n', encoding='utf-8')
    say(''); [say(l) for l in out]
    say(f'\nThe report is in {rep / "REPORT.txt"}. Send that file to Claude.')


if __name__ == '__main__':
    main(sys.argv[1:])
