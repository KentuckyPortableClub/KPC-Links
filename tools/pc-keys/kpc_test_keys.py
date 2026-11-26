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
import datetime, gzip, json, os, pathlib, re, shutil, subprocess, sys, time

HERE = pathlib.Path(__file__).resolve().parent
LINKS = HERE / 'links'
ORIG = HERE / 'originals'          # the website's key, kept once per state, so every test compares with the same thing
LAST = HERE / 'last-test'          # this PC's last test of each state, to see what the newest change did
KITWEB_NAME = '.kit-website-keys'  # batch 16: the website's key files (main) and their sha256, brought by the kit (read only)
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
    try:
        p = pathlib.Path(p)
        if p.suffix == '.gz':
            with gzip.open(p, 'rt', encoding='utf-8') as f: return json.load(f)
        return json.loads(p.read_text(encoding='utf-8'))
    except (OSError, ValueError, EOFError): return None


def keep_key(kf, rep):
    """25 Nov 2026 (owner: 'YOU HAVE 10 MN AND NY FROM TODAY TO COMPARE TOO'): every test keeps its own key files, zipped,
    in its report folder (keys\\<name>.gz), so any later test can be compared with it park by park."""
    d = rep / 'keys'; d.mkdir(parents=True, exist_ok=True)
    with open(kf, 'rb') as f, gzip.open(d / (kf.name + '.gz'), 'wb') as g: shutil.copyfileobj(f, g)
    return d / (kf.name + '.gz')


def earlier_tests(kf, rep, n=3):
    """The newest earlier tests (report folder name = date and time) that kept this key file, newest first."""
    out = []
    for r in sorted((HERE / 'reports').glob('test-*'), reverse=True):
        if r.name >= rep.name: continue
        k = r / 'keys' / (kf.name + '.gz')
        if k.is_file(): out.append((r.name, k))
        if len(out) >= n: break
    return out


def park_changes(label, old, new):
    """Park by park (owner 25 Nov: 'WHY ARE WE DROPPING STUFF ALL THE TIME'): every park that went outline -> pin, pin ->
    outline, or changed records, with the records before and after and the builder's own reason (its best try and the first
    check row). For CHANGES-<state>.txt in the report folder: it stays on this PC unless the owner sends it."""
    o = (load(old) or {}).get('parks') or {}; n = (load(new) or {}).get('parks') or {}
    def ids(row): return [(str(x[0]), str(x[1])[:50]) for x in (row or {}).get('m') or [] if isinstance(x, (list, tuple)) and len(x) > 1]
    def why(row):
        row = row or {}; bk = row.get('bk') or []; c = row.get('c') or []
        w = []
        if bk and bk[0] is not None: w.append(f'best try {bk[0]} ({" ".join(str(x) for x in bk[2:] if x)})')
        elif len(bk) > 4: w.append(f'best try none ({bk[4]})')
        if c and isinstance(c[0], (list, tuple)) and len(c[0]) > 3: w.append(f'first check row {c[0][0]} {str(c[0][1])[:40]}: {str(c[0][3])[:140]}')
        return '; '.join(w) or 'no reason written'
    groups = {'OUTLINE TO PIN': [], 'PIN TO OUTLINE': [], 'RECORDS CHANGED': []}
    for ref in sorted(set(o) | set(n)):
        a, b = ids(o.get(ref)), ids(n.get(ref))
        if {x[0] for x in a} == {x[0] for x in b}: continue
        name = str((n.get(ref) or o.get(ref) or {}).get('n') or '')[:60]
        g = 'OUTLINE TO PIN' if a and not b else 'PIN TO OUTLINE' if b and not a else 'RECORDS CHANGED'
        line = f'  {ref} {name}: before {a or "pin"} ; now {b or "pin"}'
        if g != 'PIN TO OUTLINE': line += f'\n      why: {why(n.get(ref))}'
        groups[g].append(line)
    out = [f'{label}: outline to pin {len(groups["OUTLINE TO PIN"])}, pin to outline {len(groups["PIN TO OUTLINE"])}, '
           f'records changed {len(groups["RECORDS CHANGED"])}']
    for g, ls in groups.items():
        if ls: out += [f' {g}:'] + ls
    return out + ['']


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
        m = re.search(r'::notice title=(?:US key [A-Z]{2}|Canada key[^:]*)::(match checks: .*|same land .*|fresh source .*)', ln)   # 25 Nov: the matcher's lines
        if m: out.append('  ' + m.group(1)[:3000])   # 24 Nov (F2): was cut at 900
        elif ln.startswith('Recreation.gov saved copy') and not any('Recreation.gov' in o for o in out): out.append('  ' + ln.strip()[:160])
        elif '::notice title=Boundary check::' in ln: out.append('  pins: ' + ln.split('::', 2)[-1].replace('%25', '%').strip()[:300])
        elif re.search(r'::(error|warning) title=', ln) or 'golden cases' in ln or 'US key STOPPED' in ln:
            out.append('  ' + re.sub(r'(US|CA)-\d{3,5}', r'\1-####', ln.strip())[:300])
    return out[:20]


def store_attrs():
    """The outline store's agency id fields for the match checks (KPC_RECORD_ATTRS); '' when the store is not on this PC."""
    out = LINKS / '.pf' / 'record-attrs.json.gz'
    if not STORE.is_dir():
        say(f'  (the outline store folder is not at {STORE}: the id checks use the saved copies only)')
        return ''
    newest = max((p.stat().st_mtime for p in list(STORE.glob('*.kpcstore.json.gz')) + list(STORE.glob('*.layer-records.json.gz'))), default=0)   # 25 Nov: and every layer record
    fmt = 0
    if out.is_file():   # 24 Nov: a file made before the '@' fix and the name-and-size index with map boxes (format 3) is made again
        try:
            import gzip
            with gzip.open(out, 'rt', encoding='utf-8') as fh: fmt = int(json.load(fh).get('format') or 0)
        except Exception: fmt = 0  # noqa: BLE001
    if not out.is_file() or out.stat().st_mtime < newest or fmt < 13:   # 25 Nov (better matcher): 6 adds each record's name, size, box and light outline; 7 its area, read date, PAD-US words; 8 the layer records + manifest; 9 each layer file's identity (Q1); 10 the agency record ids and FWS realty fields (R1, R5); 11 the layer's own acres field (round 15); 12 the agency's own record ids, 13 the layer's second name (batch 16)
        say('  reading the agency id fields from the outline store (once, about a minute)...')
        out.parent.mkdir(exist_ok=True)
        rc = subprocess.run([sys.executable, '-X', 'utf8', '.github/scripts/kpc_store_attrs.py', '--store', str(STORE), '--out', str(out)], cwd=LINKS).returncode
        if rc != 0:   # P2 (grade of round 6): a failed run never falls back to an older id file
            return None
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
                                 store_dir=str(STORE),   # 25 Nov: the full layer files' dates (LAYER-RECORDS), not only the Nov 12 copy
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
            env = dict(common, STATES=st, GEO_CACHE=str(LINKS / 'cache' / 'us'),
                       KPC_FP_PROPOSALS=str(rep / 'saved-answers-no-fingerprint.csv'),   # 25 Nov: the owner's lists (never data/)
                       KPC_PIN_ONLY_LIST=str(rep / 'pin-only-parks.csv'), KPC_REPOINTS=str(rep / 'saved-answers-moved.csv'),
                       KPC_LISTED=str(rep / 'rows-kept-but-listed.csv'), KPC_NOSTORE_LIST=str(rep / 'layers-not-in-store.csv'),
                       KPC_GAP_LIST=str(rep / 'layers-not-complete.csv'),
                       KPC_PROOF_LIST=str(rep / 'row-proof.csv'))   # R6: why each old row of a park that lost rows did or did not prove   # 25 Nov (owner 8:48 AM): a state stops on a gap
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


def sha(p):
    import hashlib
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def kitweb():
    return LINKS / KITWEB_NAME


def _web_shas():
    d = load(kitweb() / 'sha256.json')
    return (d.get('files') or {}) if isinstance(d, dict) else {}


def web_copy(kf):
    """Batch 16 (grade of #380, 25 Nov 2026: the PC's 'website copy' of MN and NY in originals was a key a test had built that
    morning, and every MN / NY test after it compared against it). The trusted website copy of a key file, READ ONLY:
      - the kit lists main's sha256 for each website key file (links\\.kit-website-keys\\sha256.json); a copy counts only when its
        bytes match: the kit's own copy first, then originals;
      - a file the kit lists no sha for (an older kit): originals as before, not checked.
    None = no trusted copy. This test never writes into originals."""
    name = pathlib.Path(kf).name
    want = _web_shas().get(name)
    if want:
        for c in (kitweb() / name, ORIG / name):
            if c.is_file() and sha(c) == want: return c
        return None
    return ORIG / name if (ORIG / name).is_file() else None


def links_path(name):
    """Where a website key file lives in links\\ (as on GitHub)."""
    if name == 'layers.json' or name.startswith('US-'): return LINKS / 'data' / 'us-key' / name
    if name.startswith('CA-'): return LINKS / 'data' / 'ca-key' / name
    return LINKS / 'data' / name


def put_back_website_copies():
    """Batch 16 (the owner's PC, 25 Nov evening: links\\data\\us-key still held the 24 Nov all-states test's keys of the other 49
    areas, and layers.json as the 2:28 PM test wrote it, so a MN / NY build read them: cross-state marks, layer prefixes). Before
    anything is built, EVERY website file the kit lists goes back into links\\ from its trusted copy (web_copy), so each test
    starts from the website's state, as GitHub does. Returns how many were put back. originals is only read."""
    n = 0
    for name in _web_shas():
        w = web_copy(name)
        if not w: continue
        dst = links_path(name)
        if dst.is_file() and dst.read_bytes() == w.read_bytes(): continue
        dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(w, dst); n += 1
    return n


def website_copies_check():
    """Batch 16 item 4 (grade of #380, 25 Nov): before ANY state is built, every website key file the kit lists (66: the US
    states, Canada's provinces, Kentucky) must have a trusted copy (web_copy: the kit's own copy or originals, sha256 equal to
    main's). Returns the names that differ or are missing ([] = all good; also [] for an older kit that lists none)."""
    return sorted(n for n in _web_shas() if not web_copy(n))


def web_copy_problem(kf):
    """'' when the website copy of kf is trusted (or the kit lists none); else one plain line for the report."""
    name = pathlib.Path(kf).name
    want = _web_shas().get(name)
    if not want or web_copy(kf): return ''
    o = ORIG / name
    have = f'its sha256 is {sha(o)[:12]}' if o.is_file() else 'there is none'
    return (f"the saved website copy of {name} in originals is not the website's key ({have}; the website's is {want[:12]}). "
            f"Nothing was built for this state. A kit update that brings {KITWEB_NAME}\\{name} fixes it.")


def not_built_reason(st, log):
    """K1 (grade fix): the builder can exit 0 and write nothing: no park file, FAILED, a gate (Canada's 'GATE FAIL' is in the
    notice TITLE), or the golden cases ('US key STOPPED ... NO keys were written'). Also: every key file is still byte for byte
    the website copy. '' when the state was built."""
    m = re.search(r'::notice title=(?:US key ' + st + r'|Canada key[^:]*)::(FAILED: .*|no park file, skipped.*|.*GATE FAIL.*)', log)
    if m: return m.group(1)
    m = re.search(r'::notice title=(?:Canada key GATE FAIL|US key STOPPED)[^:]*::(.*)', log)
    if m: return m.group(1) or 'the build stopped'
    files = [kf for kf in keyfiles(st) if web_copy(kf)]
    if files and all(kf.is_file() and kf.read_bytes() == web_copy(kf).read_bytes() for kf in files):
        return 'every key file is still the website copy (nothing was written)'
    return ''


def join_check_lines(st):
    """24 Nov (B2): kpc_join_check.py's holds (a person's NO carried under an old id, far joins), as the GitHub build applies them.
    The answer sheet is links\\data\\answer-sheet (a kit update brings it) or ANSWER_SHEET; without it more joins are held."""
    cwd = os.getcwd()
    try:
        os.chdir(LINKS)
        if str(LINKS / '.github' / 'scripts') not in sys.path: sys.path.insert(0, str(LINKS / '.github' / 'scripts'))
        import kpc_join_check as JC
        kind = 'ca' if st == 'CANADA' else 'us'
        ok, sheet = JC.approvals(str(LINKS), kind, dict(os.environ))
        off = JC.official_acres(str(LINKS / 'data' / 'acres.json'))
        near = {}   # grade fix: as JC.run(), a park in several area files is measured to the NEAREST part of its whole outline
        d_, pat = JC.DIRS[kind]
        mine = {kf.name for kf in keyfiles(st)}
        for x in (LINKS / d_).glob(pat):
            if x.name not in mine and web_copy(x): x = web_copy(x)   # other areas: the website copy, as GitHub reads
            for ref, p in ((load(x) or {}).get('parks') or {}).items():
                if isinstance(p, dict) and JC.joined(p) and JC.pin_km(p) is not None: near[ref] = min(near.get(ref, 1e9), JC.pin_km(p))
        nh, no_prev = 0, 0
        for kf in keyfiles(st):
            prev = (load(web_copy(kf)) or {}).get('parks') or {} if web_copy(kf) else {}
            no_prev += not web_copy(kf)
            _r, h, _c = JC.mark_file(str(kf), off, mode='hold', ok=ok, near=near, prev=prev, root=str(LINKS))
            nh += len(h)
        return [f'  join check (as on GitHub): {nh} join(s) held' + ('' if sheet else '; NO answer sheet found, so more holds than GitHub')
                + (f'; {no_prev} file(s) had no website copy (checked with no previous key, as GitHub would)' if no_prev else '')]
    except Exception as e:  # noqa: BLE001
        return [f'  JOIN CHECK NOT RUN ({type(e).__name__}: {str(e)[:120]}): do not compare this state 1:1 with the website']
    finally:
        os.chdir(cwd)


def canada_keep_lines():
    """24 Nov (K3): a hard look is a live read, so a store-mode build makes none; GitHub keeps main's hard-look joins after the
    build (kpc_ca_store_keep.py keep). Same rule here, from the website copy: a park the build left with no join gets its old entry."""
    try:
        if str(LINKS / '.github' / 'scripts') not in sys.path: sys.path.insert(0, str(LINKS / '.github' / 'scripts'))
        import kpc_ca_store_keep as HK
        kept = 0
        for kf in keyfiles('CANADA'):
            o, n = (load(web_copy(kf)) if web_copy(kf) else None), load(kf)
            if not o or not n: continue
            k0, parks = kept, n.get('parks') or {}
            for ref, p in (o.get('parks') or {}).items():
                if HK.hl_joined(p) and ref in parks and not (parks[ref] or {}).get('m'):
                    parks[ref] = p; kept += 1
            if kept > k0: kf.write_text(json.dumps(n, ensure_ascii=False), encoding='utf-8')
        return [f'  Canada hard look: {kept} join(s) kept from the website key (as GitHub store mode keeps them)']
    except Exception as e:  # noqa: BLE001
        return [f'  CANADA HARD LOOK NOT KEPT ({type(e).__name__}: {str(e)[:120]}): its parks show as pins']


def run_state(st, rep, attrs, tot):
    """Batch 16: originals is only READ. The website's key (web_copy: its sha256 checked against the kit's list) is put back into
    links\\ before each build, so every test starts the same; a state with no trusted website copy is not built (one plain line)."""
    LAST.mkdir(exist_ok=True)
    probs = [p for p in (web_copy_problem(kf) for kf in keyfiles(st)) if p]
    if probs:
        return [f'{st}: NOT BUILT: ' + probs[0]]
    for kf in keyfiles(st):
        w = web_copy(kf)
        if w: kf.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(w, kf)
    return _run_state(st, rep, attrs, tot)


def _run_state(st, rep, attrs, tot):
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
    # 24 Nov (K1): the builder can end with exit 0 and still not build (no park file, FAILED, a gate): say so, compare nothing
    _nb = not_built_reason(st, log)
    if _nb:
        return lines + ['  NOT BUILT: ' + re.sub(r'(US|CA)-\d{3,5}', r'\1-####', _nb)[:300],
                        '  (the key file is still the website copy: there is nothing to compare, and the last-test copy is not changed)']
    if st == 'CANADA':   # 24 Nov (K3): Canada's hard-look joins kept from the website key, as kpc-ca-key.yml 'keep' does in store
        lines += canada_keep_lines()   # mode; BEFORE the join check, in the workflow's order (keep :178, join check :225)
    if st != 'KY':   # 24 Nov (B2): the join check, as the workflows run it after the builder, with the WEBSITE key as 'previous'
        lines += join_check_lines(st)   # (the PC folder is not a git checkout, so the check's own git read would find nothing)
    tot['compared'] = tot.get('compared', 0) + 1
    for kf in keyfiles(st):
        tag = kf.stem
        if web_copy(kf):
            l, n = compare(f'{tag} against the website', web_copy(kf), kf); lines += l
            for k, v in n.items(): tot[k] = tot.get(k, 0) + v
        else:
            lines.append(f'  {tag}: no website key to compare with')
        if (LAST / kf.name).is_file():
            lines += compare(f"{tag} against this PC's last test", LAST / kf.name, kf)[0]
        shutil.copy2(kf, LAST / kf.name)
        try:   # 25 Nov: this test keeps its key; compare park by park with the website and the last 3 tests that kept one
            kept = keep_key(kf, rep)
            ch = [f'{tag}, built {rep.name}. Park numbers and names: this file stays on this PC unless you send it.', '']
            if web_copy(kf): ch += park_changes('Against the website', web_copy(kf), kept)
            for nm, k in earlier_tests(kf, rep):
                l, _ = compare(f'{tag} against {nm}', k, kept); lines += l
                ch += park_changes(f'Against {nm}', k, kept)
            (rep / f'CHANGES-{tag}.txt').write_text('\n'.join(ch) + '\n', encoding='utf-8')
            lines.append(f'  park by park: CHANGES-{tag}.txt in the report folder')
        except Exception as e:  # noqa: BLE001
            lines.append(f'  park-by-park list not written ({type(e).__name__}: {str(e)[:120]})')
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
    if any(s != 'KY' for s in order) and subprocess.run([sys.executable, '-c', 'import shapely, pyproj, shapefile'], capture_output=True).returncode:
        say('STOPPED: the map packages (shapely, pyproj, pyshp) are not installed for this Python, so the keys would not match GitHub. '
            'Run START-HERE.bat again, or tell Claude.')   # 24 Nov (K2): without shapely the keys differ with no warning
        return
    rep = HERE / 'reports' / ('test-' + datetime.datetime.now().strftime('%Y-%m-%d-%H%M'))
    rep.mkdir(parents=True, exist_ok=True)
    bad = website_copies_check()
    if bad:   # batch 16 item 4: one wrong website copy and nothing is built (originals is never changed by this test)
        msg = [f'STOPPED: {len(bad)} of the {len(_web_shas())} saved website copies in originals are not the website\'s key files '
               f"(their sha256 differs from the website's, or the file is missing): {', '.join(bad[:12])}{' ...' if len(bad) > 12 else ''}.",
               'Nothing was built. The kit update that brings links\\.kit-website-keys with these files fixes it; tell Claude.']
        (rep / 'REPORT.txt').write_text('\n'.join(msg) + '\n', encoding='utf-8')
        [say(l) for l in msg]
        return
    _pb = put_back_website_copies()   # batch 16: every test starts from the website's files, not an earlier test's
    if _pb: say(f'  {_pb} file(s) put back to the website copy before the build (an earlier test had changed them)')
    attrs = store_attrs() if any(s != 'KY' for s in order) else ''
    if attrs is None:
        say('STOPPED: the agency id fields could not be read from the outline store (kpc_store_attrs.py failed; see above). '
            'The test never uses an older id file. Tell Claude.')
        return
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
    _h = next((re.search(r'US ([0-9a-f]{12})', l).group(1) for l in out if l.startswith('Rules on this PC: US ') and re.search(r'US ([0-9a-f]{12})', l)), '')
    if _h and tot.get('compared'):   # 24 Nov (F3): read by the next test; only when at least one state was built and compared
        LAST.mkdir(exist_ok=True); (LAST / 'RULES.txt').write_text(_h + '\n', encoding='utf-8')
    say(''); [say(l) for l in out]
    say(f'\nThe report is in {rep / "REPORT.txt"}. Send that file to Claude.')


if __name__ == '__main__':
    main(sys.argv[1:])
