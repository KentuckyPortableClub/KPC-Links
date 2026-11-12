#!/usr/bin/env python3
"""JOIN ACREAGE + DISTANCE CHECK (Nov 6 2026 improvements 4, Mapping; Brandon directly in Mapping's chat, 4:58 PM CST Nov 5: "You
write the code and I think super and quality would agree to it"). Runs in the key build, right after the builder wrote the key
files and before the build stamp (kpc-us-key.yml, kpc-ca-key.yml, kpc-world-key.yml). OFFLINE (key files + data/acres.json only).

v2 (Quality grade 2026-11-06, L04 NO "far joins still stamp"; Mapping's chat 5:28 PM CST Nov 5): a join whose nearest
outline part is over 15 km from the POTA pin is HELD BEFORE THE STAMP (KPC_JOIN_HOLD=hold, the default; =mark is v1).

For every JOINED park of the key files this build changed it computes:
  outline_ac   the joined land's acres (US 'ac', else the joined records' own acres; world records carry none: unknown)
  official_ac  the park's official acres where known (data/acres.json, the acres bot's file; else unknown)
  pin_km       km from the POTA pin to the NEAREST PART of the joined outline (the key's own 'bk' field, links-10: the minimum
               over the joined records of the pin-to-edge distance, 0 inside; not the centre; None = not measured)
HELD (pin_km > 15, not exempt): the joined records move from 'm' to 'c' ('held: <reason>'), 'g' becomes 'pin', 'ac' moves into
  'held' {why, was_g, ids, km, ac, decided_by}; the park is listed in data/<kind>/review/held-joins.json + .csv and one pile-enter
  proposal per park is written to data/<kind>/review/held-joins-ledger.csv (the agreement ledger's columns; a PROPOSAL for a
  person, not a ledger row: nothing is added to the ledger). Nothing is deleted: the records stay in 'c' and in the evidence.
EXEMPT (never held, only marked): a join a person already approved:
  - an overrides.json entry of that key naming a joined record ('join': ids or names),
  - a joined record whose 'how' starts 'reviewed' (Brandon's rulings / reviews; v2.1: a 'chat 11 YES' how does NOT exempt),
  - a signed answer-sheet row for the park naming a joined record (status YES or a 'Quality YES' note; ANSWER_SHEET=<dir>,
    default data/answer-sheet, else ../kpcdata/data/answer-sheet; none found = this exemption is empty, said in the report),
  - trails and linear features: 'line' parks such as US-9905/9906, 'trl' ids, a linear KIND ('t': Trail, Wild and Scenic River,
    Heritage River, Parkway); never a word in the name (v2.1), where the pin is legitimately far from parts of the line.
MARKED only ('suspect', evidence): outline_ac / official_ac outside 0.5x - 2x, outline_ac == 0 (not for line parks), and every
  exempt far join. The acreage bar is not unified here (it waits, 5:28 PM CST Nov 5).
Under Brandon's verify-then-fix rule (decided_by 'Brandon standing rule 2026-11-05 verify-then-fix') a held join is a hold, not
a removal: a person verifies, then fixes (overrides 'join' to keep it, or a better record).
Not a rules file (kpc_key_freeze.RULE_FILES), on purpose: it is a check run after the builder in every build, so the
rules hash (US 3dc53f70256a) stays the same; the hold shows from each key's next build. Counting it as a rule would force a
full rebuild of every key (say so to change it: add it to RULE_FILES).

  KEY=us|ca|world (or the kind: us-key, ...)   ALL=1 (check every area file, not only the ones git shows changed)
  OFFICIAL_ACRES=<file> (default data/acres.json)   KPC_JOIN_HOLD=hold|mark   ANSWER_SHEET=<dir>   DRY=1 (count only, no file written)
  --selftest (rule-18 style, frozen cases, temp folder)
Never fails the build: exit 0 (the selftest exits 1 on a failed case)."""
import csv, glob, json, os, pathlib, re, subprocess, sys

FAR_KM = 15.0
NEW_KM = 5.0   # Nov 8 (Quality KEY NO on US-42487204632, must-fix 2): a join NEW in this build (record id not joined in the previous key) is held over 5 km
RATIO = (0.5, 2.0)
DECIDED_BY = 'Brandon standing rule 2026-11-05 verify-then-fix'
LINEAR_KIND = re.compile(r'\b(trail|wild (and|&) scenic river|heritage river|parkway)\b', re.I)   # v2.1: the park KIND ('t') only, never its name
LEDGER_FIELDS = ['park', 'kind', 'proposed_by', 'proposal', 'source', 'confirmed_by', 'confirmed_at', 'decided_by', 'agreed_lat', 'agreed_lon',
                 'pota_lat', 'pota_lon', 'notes']   # = KPC-Data kpc_agreement_ledger.FIELDS (checked by the test)
SHEET = {'us': 'US.csv', 'ca': 'CA.csv', 'world': 'world.csv'}
DIRS = {'us': ('data/us-key', 'US-??.json'), 'ca': ('data/ca-key', 'CA-??.json'), 'world': ('data/world-key', '??.json')}


def joined(p): return bool((p or {}).get('m')) and (p or {}).get('g') != 'pin'


def outline_acres(p):
    if isinstance(p.get('ac'), (int, float)) and not isinstance(p.get('ac'), bool): return float(p['ac'])
    a = [x[2] for x in (p.get('m') or []) if isinstance(x, list) and len(x) > 2 and isinstance(x[2], (int, float)) and not isinstance(x[2], bool)]
    return float(sum(a)) if a else None


def pin_km(p):
    bk = p.get('bk') or []
    return float(bk[1]) if len(bk) > 1 and isinstance(bk[1], (int, float)) and not isinstance(bk[1], bool) else None


def check_join(p, official=None):
    """(outline_ac, official_ac, pin_km, [reasons]) for one joined park."""
    ac, km, why = outline_acres(p), pin_km(p), []
    if km is not None and km > FAR_KM: why.append(f'the nearest joined record is {km:.1f} km from the POTA pin (over {FAR_KM:.0f} km)')
    if ac is not None and ac <= 0 and not linear(p): why.append('the joined land has 0 acres')
    elif ac is not None and official and not (RATIO[0] <= ac / official <= RATIO[1]):
        why.append(f'the joined land is {ac:,.0f} ac vs the official {official:,.0f} ac ({ac / official:.2f}x, outside {RATIO[0]}x-{RATIO[1]}x)')
    return ac, official, km, why


def linear(p):
    """A true trail / linear park (the pin is legitimately far from parts of the line): a 'line' park, a 'trl' trail-line id, or a
    linear KIND (t: '... Trail', 'Wild and Scenic River', 'Heritage River', 'Parkway'). v2.1 (Quality should-fix): never by a
    word in the park's NAME or source (Owyhee River Wilderness, Great River NWR, Merrimack River SF are area parks)."""
    m = [x for x in (p.get('m') or []) if isinstance(x, list)]
    if p.get('line') or any(str(x[0]).startswith('trl') for x in m if x): return True
    return bool(LINEAR_KIND.search(str(p.get('t') or '')))


SIGNED, SIGNED_BY = {}, {}   # {ref: ids + names} of overrides.json joins that carry decided_by (filled by approvals())


def approvals(root, kind, env):
    """{ref: set(ids and names)} a person approved: overrides.json 'join' + signed answer-sheet rows. (map, sheet file or None)"""
    ok = {}; SIGNED.clear(); SIGNED_BY.clear(); NOS.clear()
    # Nov 12 2026 (KPC-Links #151): the US overrides are a manifest + parts; kpc_overrides.load reads them whole or raises
    _ov = __import__('kpc_overrides').load(os.path.join(root, DIRS[kind][0], 'overrides.json'), missing_ok=True)
    try:
        for r, v in ((_ov.get('parks')) or {}).items():
            if isinstance(v, dict) and (v.get('no') or v.get('nofp')):   # Nov 8: a person's NO, by name (+ acres) as well as by id
                nf_ = v.get('nofp') if isinstance(v.get('nofp'), dict) else {}
                NOS[r] = [(z[0], z[1] if len(z) > 1 else None, k) for k, z in nf_.items() if isinstance(z, list) and z and z[0]]
                NOS[r] += [(z, None, '') for z in (v.get('no') or []) if not re.fullmatch(r'[a-z]*\d+', str(z))]
            if isinstance(v, dict) and v.get('join'):
                ok.setdefault(r, set()).update(str(x) for x in v['join'])
                if str(v.get('decided_by') or '').strip():   # Nov 8 (Quality NO on US-42446831487): a SIGNED override (decided_by) is never held
                    SIGNED.setdefault(r, set()).update(str(x) for x in v['join']); SIGNED_BY[r] = str(v['decided_by']).strip()
                    for _id, _fp in ((v.get('fp') or {}).items() if isinstance(v.get('fp'), dict) else []):
                        if isinstance(_fp, list) and _fp and _fp[0]: SIGNED[r].add(str(_fp[0]))
    except Exception: pass  # noqa: BLE001
    sheet = None
    for d in [env.get('ANSWER_SHEET'), os.path.join(root, 'data/answer-sheet'), os.path.join(root, '../kpcdata/data/answer-sheet')]:
        if d and os.path.isfile(os.path.join(d, SHEET[kind])): sheet = os.path.join(d, SHEET[kind]); break
    if sheet:
        try:
            for row in csv.DictReader(open(sheet, encoding='utf-8')):
                if str(row.get('status') or '').strip().upper() == 'YES' or str(row.get('quality_yes') or '').strip().upper().startswith('QUALITY YES'):
                    ok.setdefault(row.get('ref') or '', set()).update(str(row.get(c) or '') for c in ('record_id', 'key_id', 'record_name') if row.get(c))
        except Exception: sheet = None  # noqa: BLE001
    return ok, sheet


def exempt(ref, p, ok):
    """Why a far join is NOT held ('' = it is held)."""
    m = [x for x in (p.get('m') or []) if isinstance(x, list) and x]
    if linear(p): return 'trail / linear feature (nearest part of the line measured)'
    sg = SIGNED.get(ref) or set()
    if any(str(x[0]) in sg or (len(x) > 1 and str(x[1]) in sg) for x in m):
        return f"signed override in overrides.json (decided_by {SIGNED_BY.get(ref, 'a person')})"
    if any(str(x[3] if len(x) > 3 else '').lower().startswith('reviewed') for x in m):   # v2.1: a 'chat 11 YES' how no longer exempts
        return 'a person approved this join (reviewed)'
    got = ok.get(ref) or set()
    if any(str(x[0]) in got or (len(x) > 1 and str(x[1]) in got) for x in m): return 'approved in overrides.json or the answer sheet'
    return ''


def hold(ref, p, why):
    """Hold one join: the records go to 'c' (nothing deleted), the park becomes a pin until a person verifies."""
    m = [x for x in p.get('m') or [] if isinstance(x, list)]
    p['held'] = {'why': why, 'was_g': p.get('g'), 'ids': [x[0] for x in m if x], 'km': pin_km(p), 'ac': p.pop('ac', None), 'decided_by': DECIDED_BY}
    p['c'] = [x[:3] + ['held: ' + why] for x in m] + [x for x in (p.get('c') or []) if x not in m]
    p['m'], p['g'] = [], 'pin'


def official_acres(path=None):
    f = path or 'data/acres.json'
    try: d = json.load(open(f, encoding='utf-8'))
    except Exception: return {}  # noqa: BLE001
    d = d.get('parks', d) if isinstance(d, dict) else {}
    out = {}
    for r, v in d.items():
        a = v.get('acres') if isinstance(v, dict) else v
        if isinstance(a, (int, float)) and not isinstance(a, bool) and a > 0: out[r] = float(a)
    return out


def changed_files(d, pat, root='.'):
    """Area files git shows changed or new under d (this build's); None when git cannot tell."""
    try:
        r = subprocess.run(['git', 'status', '--porcelain', '--untracked-files=all', '--', d], cwd=root, capture_output=True, text=True, timeout=60)
        if r.returncode != 0: return None
    except Exception: return None  # noqa: BLE001
    import fnmatch
    return sorted({ln[3:].strip() for ln in r.stdout.splitlines() if fnmatch.fnmatch(os.path.basename(ln[3:].strip()), pat)})


NOS = {}   # {ref: [(name, acres or None, old id)]} a person's NO for the park (overrides.json 'no' + 'nofp'; filled by approvals())


def _nf(t): return re.sub(r'\s+', ' ', str(t or '')).strip().casefold()


def _close(a, b):
    """acres about the same (10% or 20 ac); unknown acres on either side count as the same."""
    try: a, b = float(a or 0), float(b or 0)
    except (TypeError, ValueError): return True
    return not a or not b or abs(a - b) <= max(20.0, .1 * max(a, b))


def join_base(f, root='.', env=None):
    """The key to compare with: KPC_JOIN_BASE, else the commit in data/key-join-base.json (by key folder) (a person sets it to the last
    good key when a graded-NO build is on main, so the rebuild is compared with the key before it), else HEAD (the key before
    this build). A commit missing from a shallow checkout is fetched once (depth 1)."""
    env = os.environ if env is None else env
    b = (env.get('KPC_JOIN_BASE') or '').strip()
    if not b:
        t = pathlib.Path(root) / 'data' / 'key-join-base.json'   # {"us-key": "<commit>", ...}; outside the answer-key folders
        try: b = str((json.loads(t.read_text(encoding='utf-8')) if t.is_file() else {}).get(pathlib.Path(f).resolve().parent.name) or '')
        except Exception: b = ''  # noqa: BLE001
    if not re.fullmatch(r'[0-9a-f]{7,40}', b): return 'HEAD'
    if subprocess.run(['git', 'cat-file', '-e', b + '^{commit}'], cwd=root, capture_output=True, timeout=30).returncode != 0:
        subprocess.run(['git', 'fetch', '-q', '--depth', '1', 'origin', b], cwd=root, capture_output=True, timeout=120)
    return b


def previous(f, root='.'):
    """The previous key's parks for this area file (join_base: HEAD, i.e. before this build wrote it, or the declared good key);
    {} when git cannot tell."""
    try:
        r = subprocess.run(['git', 'show', join_base(f, root) + ':' + os.path.relpath(os.path.abspath(f), os.path.abspath(root)).replace(os.sep, '/')],
                           cwd=root, capture_output=True, timeout=60)
        return (json.loads(r.stdout).get('parks') or {}) if r.returncode == 0 and r.stdout.strip() else {}
    except Exception: return {}  # noqa: BLE001


def no_carried(ref, p, prev):
    """Nov 8 must-fix 1: a person's NO follows the LAND, not the source id. A joined record whose id is not the NO'd id but whose
    name (+ acres when known) matches a NO fingerprint, or a record the previous key listed as 'a person said NO', is the same land
    re-keyed (hma12 -> sgnvi433, sgakh1214 -> sgnvh1214). Returns [(joined id, name, old id)]."""
    # only a NEW join on a park the previous key left as a pin: a park that was already joined keeps its reviewed join (a same-name
    # duplicate record NO'd beside the joined one is not a re-key); no previous key = nothing to compare with
    if not prev or joined(prev): return []
    fresh = {str(i) for i in (new_ids(p, prev) or [])}
    fps = list(NOS.get(ref) or [])
    for x in ((prev or {}).get('c') or []):
        if isinstance(x, list) and len(x) > 3 and 'a person said no' in str(x[3]).lower():
            fps.append((x[1], x[2] if len(x) > 2 else None, x[0]))
    sg = SIGNED.get(ref) or set()
    out = []
    for x in (p.get('m') or []):
        if not (isinstance(x, list) and len(x) > 1) or str(x[0]) not in fresh or str(x[0]) in sg or str(x[3] if len(x) > 3 else '').lower().startswith('reviewed'): continue   # signed / reviewed by a person wins
        for nm, ac, old in fps:
            if str(x[0]) != str(old) and nm and _nf(x[1]) == _nf(nm) and _close(x[2] if len(x) > 2 else None, ac):
                out.append((x[0], x[1], old)); break
    return out


def new_ids(p, prev):
    """Joined record ids that the previous key did not join for this park (None = no previous key to compare with)."""
    if prev is None: return None
    old = {str(x[0]) for x in (prev.get('m') or []) if isinstance(x, list) and x}
    return [x[0] for x in (p.get('m') or []) if isinstance(x, list) and x and str(x[0]) not in old]


def unsigned_on_signed(ref, p, prev):
    """Nov 8 should-fix 3: the signed exemption is PER ID. On a park with a signed override, a joined record the person did not
    sign, that the previous key had held / checked / NO'd (in 'c'), goes back to 'c'. Returns [(id, the previous reason)]."""
    sg = SIGNED.get(ref)
    if not sg: return []
    was = {str(x[0]): str(x[3]) for x in ((prev or {}).get('c') or []) if isinstance(x, list) and len(x) > 3}
    return [(x[0], was[str(x[0])]) for x in (p.get('m') or []) if isinstance(x, list) and x and str(x[0]) not in sg
            and not (len(x) > 1 and str(x[1]) in sg) and str(x[0]) in was]


def drop_ids(p, ids, why):
    """Move some joined records back to 'c' (nothing deleted); the outline's acres and nearest-part distance are no longer known."""
    ids = {str(i) for i in ids}
    out = [x for x in p.get('m') or [] if isinstance(x, list) and x and str(x[0]) in ids]
    p['m'] = [x for x in p.get('m') or [] if not (isinstance(x, list) and x and str(x[0]) in ids)]
    p['c'] = [x[:3] + ['held: ' + why] for x in out] + list(p.get('c') or [])
    p.pop('ac', None)
    if (p.get('bk') or [None])[0] is not None and str(p['bk'][0]) in ids: p['bk'] = [None, None, '', 'held']


def mark_file(f, official, plain=False, mode='hold', ok=None, dry=False, near=None, root='.', prev=None):
    """Check one key file in place. Returns (evidence rows, held rows, file changed?). prev: the previous key's parks of this file
    ({} = none; None = read it from git HEAD)."""
    d = json.load(open(f, encoding='utf-8')); rows, held, changed = [], [], False
    if prev is None: prev = previous(f, root)
    for ref, p in (d.get('parks') or {}).items():
        if not isinstance(p, dict): continue
        if joined(p) and mode == 'hold':
            pv = prev.get(ref) if prev else None
            nos = no_carried(ref, p, pv)
            if nos:   # must-fix 1: the whole park back to a pin until a person signs
                r = 'a person said NO to this land under its old id (' + ', '.join(f'{i} = {o} "{n}"' for i, n, o in nos) + ')'
                ids, nm, ga, km0 = [x[0] for x in p['m'] if isinstance(x, list) and x], [str(x[1]) for x in p['m'] if isinstance(x, list) and len(x) > 1], p.get('g'), pin_km(p)
                hold(ref, p, r); changed = True
                held.append({'park': ref, 'area': pathlib.Path(f).stem, 'name': p.get('n') or '', 'pin_km': km0, 'was_g': ga,
                             'held_ids': ' | '.join(map(str, ids)), 'held_names': ' | '.join(nm), 'reason': r, 'decided_by': DECIDED_BY,
                             'to_keep_it': "a person signs the new id in overrides.json 'join' (with decided_by)"})
                continue
            un = unsigned_on_signed(ref, p, pv)
            if un:    # should-fix 3: only the signed ids are exempt
                r = 'not signed in overrides.json; the previous key had it out (' + '; '.join(f'{i}: {w}' for i, w in un) + ')'
                drop_ids(p, [i for i, _ in un], r); changed = True
                held.append({'park': ref, 'area': pathlib.Path(f).stem, 'name': p.get('n') or '', 'pin_km': pin_km(p), 'was_g': p.get('g'),
                             'held_ids': ' | '.join(str(i) for i, _ in un), 'held_names': '', 'reason': r, 'decided_by': DECIDED_BY,
                             'to_keep_it': "a person adds the id to the park's signed overrides.json 'join'"})
        if not joined(p):
            if 'suspect' in p: p.pop('suspect'); changed = True
            continue
        own = pin_km(p)
        km_all = near[ref] if near and own is not None and near.get(ref) is not None and near[ref] < own else None
        ac, oa, km, why = check_join(p if km_all is None else dict(p, bk=[None, km_all]), official.get(ref))
        was = p.get('suspect')
        nw = new_ids(p, prev.get(ref) or {}) if prev else None
        far = km is not None and (km > FAR_KM or (bool(nw) and km > NEW_KM))   # must-fix 2: 5 km for a NEW join, 15 km for the rest
        ex = exempt(ref, p, ok or {}) if far else ''
        if why:
            p['suspect'] = '; '.join(why) + (f' (not held: {ex})' if ex else '')
            rows.append({'park': ref, 'area': pathlib.Path(f).stem, 'name': p.get('n') or '', 'outline_ac': '' if ac is None else round(ac),
                         'official_ac': '' if oa is None else round(oa), 'pin_km': '' if km is None else km, 'suspect': p['suspect'],
                         'decided_by': DECIDED_BY, 'evidence_only': 'yes: a person verifies, then fixes; nothing is removed by this check'})
        else: p.pop('suspect', None)
        changed |= p.get('suspect') != was
        # Nov 8 regrade should-fix 1 (Quality on US-42504172086): over 5 km only because of NEW ids, on a park whose previous joins are
        # still here: hold just the new ids (back to 'c') and keep the live outline of the old ones (US-13132, 13134, 13138, 4868, 4886)
        keep_old = [x for x in (p.get('m') or []) if isinstance(x, list) and x and str(x[0]) not in {str(i) for i in (nw or [])}]
        if far and not ex and mode == 'hold' and km <= FAR_KM and nw and keep_old:
            r = f'a new join ({", ".join(map(str, nw))}) on a park already joined: the outline is {km:.1f} km from the POTA pin (over {NEW_KM:.0f} km for a new join); the earlier joins stay'
            drop_ids(p, nw, r); changed = True
            held.append({'park': ref, 'area': pathlib.Path(f).stem, 'name': p.get('n') or '', 'pin_km': km, 'was_g': p.get('g'),
                         'held_ids': ' | '.join(map(str, nw)), 'held_names': '', 'reason': r, 'decided_by': DECIDED_BY,
                         'to_keep_it': "a person verifies; to keep the new piece add it to overrides.json 'join' (or a signed answer-sheet row)"})
            continue
        if far and not ex and mode == 'hold':
            r = (f'the nearest part of the joined outline is {km:.1f} km from the POTA pin (over {FAR_KM:.0f} km)' if km > FAR_KM else
                 f'a new join ({", ".join(map(str, nw))}): the nearest part is {km:.1f} km from the POTA pin (over {NEW_KM:.0f} km for a new join)')
            ids, nm, ga = [x[0] for x in p['m'] if isinstance(x, list) and x], [str(x[1]) for x in p['m'] if isinstance(x, list) and len(x) > 1], p.get('g')
            hold(ref, p, r); changed = True
            held.append({'park': ref, 'area': pathlib.Path(f).stem, 'name': p.get('n') or '', 'pin_km': km, 'was_g': ga,
                         'held_ids': ' | '.join(map(str, ids)), 'held_names': ' | '.join(nm), 'reason': r, 'decided_by': DECIDED_BY,
                         'to_keep_it': "a person verifies; to keep the join add it to overrides.json 'join' (or a signed answer-sheet row)"})
    if changed and not dry and plain:
        json.dump(d, open(f, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    elif changed and not dry:
        try:
            sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent)); from kpc_save import save_json
            save_json(f, d)
        except Exception:  # noqa: BLE001
            json.dump(d, open(f, 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
    return rows, held, changed


def ledger_rows(held, kind):
    """One pile-enter PROPOSAL per held park (the agreement ledger's columns; a person confirms it in the ledger)."""
    return [{'park': h['park'], 'kind': 'pile-enter', 'proposed_by': f'kpc_join_check.py ({kind} key build)',
             'proposal': f"pile-enter: join held before the stamp ({h['reason']}); held records {h['held_ids']}",
             'source': f'data/{DIRS[kind][0].split("/")[-1]}/review/held-joins.csv', 'confirmed_by': '', 'confirmed_at': '',
             'decided_by': DECIDED_BY, 'agreed_lat': '', 'agreed_lon': '', 'pota_lat': '', 'pota_lon': '',
             'notes': 'proposal only: confirm in the ledger, or keep the join via overrides.json join'} for h in held]


def run(env=None, root='.', plain=False):
    """plain=True writes key files with json.dump (the selftest: kpc_save would stamp data/status/ of the cwd)."""
    env = dict(os.environ if env is None else env)
    k = (env.get('KEY') or '').lower().replace('-key', '')
    if k not in DIRS: print('::warning title=Join check::no key given (KEY=us|ca|world)'); return None
    mode = 'mark' if (env.get('KPC_JOIN_HOLD') or 'hold').lower() == 'mark' else 'hold'
    dry = env.get('DRY') == '1'
    d, pat = DIRS[k]
    files = None if env.get('ALL') == '1' else changed_files(d, pat, root)
    if files is None: files = sorted(os.path.relpath(x, root) for x in glob.glob(os.path.join(root, d, pat)))
    acres_f = os.path.join(root, env.get('OFFICIAL_ACRES') or 'data/acres.json')
    official = official_acres(acres_f)
    acres_note = 'acres check on' if official else ('acres check off: no acres file' if not os.path.isfile(acres_f) else 'acres check off: the acres file has no usable rows')
    ok, sheet = approvals(root, k, env)
    # a park in several area files (US multi-state parks: Yellowstone's Idaho piece is 37 km from the WY pin) is measured to the
    # NEAREST part of its WHOLE outline: the smallest bk distance over every area file of this key, not only the changed ones
    near = {}
    for x in glob.glob(os.path.join(root, d, pat)):
        try:
            for ref, p in (json.load(open(x, encoding='utf-8')).get('parks') or {}).items():
                if isinstance(p, dict) and joined(p) and pin_km(p) is not None: near[ref] = min(near.get(ref, 1e9), pin_km(p))
        except Exception: pass  # noqa: BLE001
    rows, held, n_changed, joined_n = [], [], 0, 0
    for rel in files:
        f = os.path.join(root, rel)
        if not os.path.exists(f): continue
        try:
            joined_n += sum(1 for p in (json.load(open(f, encoding='utf-8')).get('parks') or {}).values() if isinstance(p, dict) and joined(p))
            r, h, ch = mark_file(f, official, plain, mode, ok, dry, near, root); rows += r; held += h; n_changed += ch
        except Exception as e: print(f'::warning title=Join check::{rel} not checked ({type(e).__name__}: {str(e)[:120]})')  # noqa: BLE001
    rep = {'key': k, 'mode': mode, 'files_checked': len(files), 'joined_parks': joined_n, 'suspect': len(rows), 'held': len(held),
           'files_changed': n_changed, 'official_acres_known': len(official), 'acres_check': acres_note, 'approved_parks_known': len(ok),
           'answer_sheet': os.path.relpath(sheet, root) if sheet else 'not found (overrides.json and reviewed joins still exempt)',
           'rule': {'hold_far_km': FAR_KM, 'distance': 'pin to the nearest part of the joined outline', 'acres_ratio': RATIO, 'zero_acres': True},
           'decided_by': DECIDED_BY, 'note': 'far joins HELD before the stamp (records kept in c), others marked; nothing deleted', 'rows': rows, 'held_rows': held}
    if dry: return rep
    out = pathlib.Path(root, d, 'review'); out.mkdir(parents=True, exist_ok=True)
    json.dump({x: v for x, v in rep.items() if x != 'held_rows'}, open(out / 'join-check.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    with open(out / 'join-check.csv', 'w', newline='', encoding='utf-8') as fh:
        cols = ['park', 'area', 'name', 'outline_ac', 'official_ac', 'pin_km', 'suspect', 'decided_by', 'evidence_only']
        w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(rows)
    json.dump({'key': k, 'count': len(held), 'decided_by': DECIDED_BY, 'about': 'joins HELD before the build stamp (nearest outline part over '
               f'{FAR_KM:.0f} km from the pin, not approved by a person); a person verifies, then fixes', 'parks': held},
              open(out / 'held-joins.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    for name, cols, data in (('held-joins.csv', ['park', 'area', 'name', 'pin_km', 'was_g', 'held_ids', 'held_names', 'reason', 'decided_by', 'to_keep_it'], held),
                             ('held-joins-ledger.csv', LEDGER_FIELDS, ledger_rows(held, k))):
        with open(out / name, 'w', newline='', encoding='utf-8') as fh:
            w = csv.DictWriter(fh, fieldnames=cols); w.writeheader(); w.writerows(data)
    print(f"::notice title=Join check::{k} key ({mode}): {len(held)} far join(s) HELD before the stamp, {len(rows)} of {joined_n} joined parks "
          f"marked suspect in {len(files)} file(s); {acres_note}; evidence {d}/review/held-joins.csv + join-check.csv; nothing deleted")
    return rep


def selftest():
    import tempfile
    ok, n = True, 0
    def check(name, got, want):
        nonlocal ok, n
        n += 1; good = got == want; ok &= good
        print(('PASS ' if good else 'FAIL ') + name + ('' if good else f'  got={got!r} want={want!r}'))
    J = lambda ac=100: [1, 'X', ac, 'name']
    check('14.9 km: not suspect', check_join({'m': [J()], 'bk': [1, 14.9]})[3], [])
    check('15.0 km: not suspect (over 15 only)', check_join({'m': [J()], 'bk': [1, 15.0]})[3], [])
    check('15.1 km: suspect', len(check_join({'m': [J()], 'bk': [1, 15.1]})[3]), 1)
    check('no distance measured: not suspect, pin_km None', check_join({'m': [J()], 'bk': [1, None, '', '-', 'nopin']})[2:], (None, []))
    check('0.5x official: fine', check_join({'m': [J(50)]}, 100.0)[3], [])
    check('0.49x official: suspect', len(check_join({'m': [J(49)]}, 100.0)[3]), 1)
    check('2x official: fine', check_join({'m': [J(200)]}, 100.0)[3], [])
    check('2.1x official: suspect', len(check_join({'m': [J(210)]}, 100.0)[3]), 1)
    check("US 'ac' wins over the records' sum", outline_acres({'ac': 70, 'm': [J(100), J(100)]}), 70.0)
    check('world records carry no acres: unknown, no acres reason', check_join({'m': [[1, 'X', 'CAPAD (DCCEEW)', 'name']]}, 100.0)[0::3], (None, []))
    check('0 acres joined land: suspect', check_join({'m': [J(0)]})[3], ['the joined land has 0 acres'])
    check('far AND too big: both reasons', len(check_join({'m': [J(900)], 'bk': [1, 30.0]}, 100.0)[3]), 2)
    T9905 = {'n': 'FS trail', 't': 'Trail', 'g': 'official', 'line': 1, 'm': [['trl9905', 'FS trail', 0, 'official trail line (US Forest Service)']], 'bk': ['trl9905', None, '', '-', 'noshape']}
    check('US-9905-style trail line: 0 acres is no reason, not held', (check_join(T9905)[3], exempt('US-9905', T9905, {})[:5]), ([], 'trail'))
    check("linear by KIND (t 'National Scenic Trail' / 'Wild and Scenic River'), far: exempt", (bool(exempt('X', {'n': 'A', 't': 'National Scenic Trail', 'm': [J()]}, {})),
          bool(exempt('X', {'n': 'B', 't': 'National Wild and Scenic River', 'm': [J()]}, {}))), (True, True))
    for nm, t in (('Owyhee River Wilderness Area', 'Wilderness Area'), ('Great River National Wildlife Refuge', 'National Wildlife Refuge'), ('Merrimack River State Forest', 'State Forest')):
        check(f"v2.1: area park with 'River' in its name is NOT linear: {nm} far = HELD", exempt('X', {'n': nm, 't': t, 'm': [[1, nm, 9, 'name']], 'bk': [1, 28.0]}, {}), '')
    check("v2.1: a 'chat 11 YES' how no longer exempts (HELD); 'reviewed' still does", (exempt('X', {'n': 'L', 'm': [[1, 'X', 9, 'name (chat 11 YES)']]}, {}),
          bool(exempt('X', {'n': 'L', 'm': [[1, 'X', 9, 'reviewed']]}, {}))), ('', True))
    check("'reviewed' join (Brandon / Quality ruling), far: exempt", bool(exempt('X', {'n': 'Lake', 'm': [[1, 'X', 9, 'reviewed: Brandon']], 'bk': [1, 40.0]}, {})), True)
    check('overrides / answer sheet names a joined record: exempt; another record: held', (bool(exempt('X', {'m': [[7, 'A', 9, 'name']]}, {'X': {'7'}})),
          bool(exempt('X', {'m': [[8, 'B', 9, 'name']]}, {'X': {'7'}}))), (True, False))
    td = pathlib.Path(tempfile.mkdtemp(prefix='kpc-join-check-')); (td / 'data/us-key').mkdir(parents=True); (td / 'data/answer-sheet').mkdir(parents=True)
    parks = {'US-0001': {'n': 'Far', 'g': 'official', 'm': [J()], 'c': [[9, 'Other', 5, 'name']], 'bk': [1, 22.0], 'ac': 100},
             'US-0002': {'n': 'Fine', 'g': 'official', 'm': [J()], 'c': [], 'bk': [1, 0.0], 'suspect': 'old mark'},
             'US-0003': {'n': 'Pin', 'g': 'pin', 'm': [], 'c': [J()], 'suspect': 'old mark'},
             'US-0004': {'n': 'Far but kept', 'g': 'official', 'm': [[44, 'Kept', 10, 'name']], 'c': [], 'bk': [44, 30.0]},
             'US-0005': {'n': 'Far, sheet YES', 'g': 'official', 'm': [[55, 'Sheet', 10, 'name']], 'c': [], 'bk': [55, 30.0]},
             'US-9905': T9905}
    json.dump({'parks': parks}, open(td / 'data/us-key/US-AA.json', 'w'))
    json.dump({'parks': {'US-0004': {'join': ['44'], 'why': 'person'}}}, open(td / 'data/us-key/overrides.json', 'w'))
    open(td / 'data/answer-sheet/US.csv', 'w').write('ref,record_id,key_id,record_name,status,quality_yes\nUS-0005,55,,Sheet,YES,\n')
    before = json.load(open(td / 'data/us-key/US-AA.json'))['parks']
    drep = run({'KEY': 'us', 'ALL': '1', 'DRY': '1'}, root=str(td), plain=True)
    check('DRY=1: counts the hold, writes nothing', (drep['held'], json.load(open(td / 'data/us-key/US-AA.json'))['parks'] == before, (td / 'data/us-key/review').exists()), (1, True, False))
    mrep = run({'KEY': 'us', 'ALL': '1', 'KPC_JOIN_HOLD': 'mark'}, root=str(td), plain=True)
    after = json.load(open(td / 'data/us-key/US-AA.json'))['parks']
    check('KPC_JOIN_HOLD=mark (v1): nothing held, the far join only marked', (mrep['held'], after['US-0001']['m'] == before['US-0001']['m'], 'suspect' in after['US-0001']), (0, True, True))
    json.dump({'parks': before}, open(td / 'data/us-key/US-AA.json', 'w'))
    rep = run({'KEY': 'us', 'ALL': '1'}, root=str(td), plain=True)
    after = json.load(open(td / 'data/us-key/US-AA.json'))['parks']
    h = after['US-0001']
    check('default hold: the far join leaves m, its record kept in c, g pin, ac kept in held', (h['m'], h['g'], [x[0] for x in h['c']], h['held']['ac'], 'ac' in h),
          ([], 'pin', [1, 9], 100, False))
    check('held record carries the reason in c', h['c'][0][3].startswith('held: the nearest part of the joined outline is 22.0 km'), True)
    check('exempt far joins (overrides, answer sheet, trail line) are kept, marked not held',
          ([bool(after[r]['m']) for r in ('US-0004', 'US-0005', 'US-9905')], '(not held:' in after['US-0004'].get('suspect', '')), ([True, True, True], True))
    check('run(): a park that passes loses an old mark', ('suspect' in after['US-0002'], 'suspect' in after['US-0003']), (False, False))
    check('run(): no other join, candidate or grade changed', all(after[r].get(f) == before[r].get(f) for r in before if r != 'US-0001' for f in ('m', 'c', 'g')), True)
    check('run(): held list + reason + decided_by', [(x['park'], x['decided_by'], x['held_ids']) for x in rep['held_rows']], [('US-0001', DECIDED_BY, '1')])
    check('run(): evidence files written', sorted(os.listdir(td / 'data/us-key/review')), ['held-joins-ledger.csv', 'held-joins.csv', 'held-joins.json', 'join-check.csv', 'join-check.json'])
    lr = list(csv.DictReader(open(td / 'data/us-key/review/held-joins-ledger.csv')))
    check('ledger proposal file: one pile-enter row per held park, ledger columns, unconfirmed', (list(lr[0]), [(x['park'], x['kind'], x['confirmed_by']) for x in lr]),
          (LEDGER_FIELDS, [('US-0001', 'pile-enter', '')]))
    json.dump({'parks': {'US-0006': {'n': 'Two-state', 'g': 'official', 'm': [J()], 'c': [], 'bk': [1, 37.3]}}}, open(td / 'data/us-key/US-BB.json', 'w'))
    json.dump({'parks': {'US-0006': {'n': 'Two-state', 'g': 'official', 'm': [J()], 'c': [], 'bk': [2, 0.0]}}}, open(td / 'data/us-key/US-CC.json', 'w'))
    r2 = run({'KEY': 'us', 'ALL': '1'}, root=str(td), plain=True)
    check("multi-state park: the far state piece is measured to the nearest part of the WHOLE outline (another file: 0 km): kept",
          (r2['held'], bool(json.load(open(td / 'data/us-key/US-BB.json'))['parks']['US-0006']['m'])), (0, True))
    check('a second run holds nothing more (idempotent)', run({'KEY': 'us', 'ALL': '1'}, root=str(td), plain=True)['held'], 0)
    print(f"SELFTEST {'PASS' if ok else 'FAIL'}: {n} cases")
    return ok


if __name__ == '__main__':
    if '--selftest' in sys.argv: sys.exit(0 if selftest() else 1)
    try: run()
    except Exception as e:  # noqa: BLE001
        print(f'::warning title=Join check::stopped ({type(e).__name__}: {str(e)[:200]}); the key build is not affected')
    sys.exit(0)
