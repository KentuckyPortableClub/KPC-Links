#!/usr/bin/env python3
"""BOT A: THE ANSWERS WRITER (Fable, Oct 29 2026 11:15 PM; Brandon 11:12 PM 'Do a'; plan: KPC_Key_And_2fer_Automation_Plan.md).
Copies chat 11's YES / NO answers from the waiting room's question files into the US key's rules file, data/us-key/overrides.json,
exactly the way chat 2 did by hand on Oct 29. It MOVES decisions; it never makes one: a row without a plain YES or NO changes
nothing, a layer the key does not read is skipped and listed, and a later answer on the same park + piece replaces the earlier one.

Reads  <DATA>/data/waiting/questions/*.json   (KPC-Data checkout; env DATA, default ../kpcdata, then ../kpc-data)
         rows: {ref, record, record_name, answer, checked_by, [layer], [acres|acres_approx], [kind]}  under 'questions' (list or dict)
       data/us-key/layers.json                 (key prefix per layer URL: a gis-hunter 'record' is a layer OBJECTID)
Writes data/us-key/overrides.json  parks[ref]: YES -> join += [id], fp[id] = [record_name, acres], (id taken out of 'no')
                                                NO  -> no += [id] (id taken out of 'join' + 'fp');  kind 'alias' + YES -> alias += [record_name]
       data/us-key/answers-applied.json       ledger {"<file>:<ref>:<id>": {answer, checked_by, applied}}: a row applied with the same
                                                answer is skipped, so the bot is safe to run every night; a changed answer is re-applied
       data/us-key/answers-states.txt         the states touched (for the changed-states rebuild, BOT B)
Prints one ::notice line. Exit 0 always (a bot step never goes red for a missing file).
  python3 kpc_key_answers.py            apply
  python3 kpc_key_answers.py --dry      show what would change, write nothing
"""
import datetime as dt, glob, json, os, pathlib, re, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try: from kpc_save import save_json
except Exception:  # noqa: BLE001
    def save_json(p, o, indent=1): json.dump(o, open(p, 'w'), indent=indent, ensure_ascii=False); return True

KEY = pathlib.Path(os.environ.get('KEY_DIR') or 'data/us-key')
OVR, LEDGER, STATES = KEY / 'overrides.json', KEY / 'answers-applied.json', KEY / 'answers-states.txt'
PAD = 'edits.nationalmap.gov/arcgis/rest/services/pad-us/pad_us/mapserver/0'
FWS = 'fwsinterest_simplified_authoritative/featureserver/0'
DRY = '--dry' in sys.argv
# Nov 3 (rules sort §9 conflict 1; proposed rule 21, accepted by Brandon Nov 3 11:44 AM CST: "only Brandon's decisions go in
# overrides.json; a checker's per-record YES goes in the answer sheet"). KPC_ANSWERS_TO=sheet writes each new checker YES / NO
# as a row of data/us-key/answers-for-sheet.csv (answer-sheet columns, status YES or NO, not signed) and leaves overrides.json
# alone; Super moves the rows into KPC-Data data/answer-sheet/US.csv through a batch. Default 'overrides' = today's behaviour,
# until the answer-sheet reader (kpc_us_key R1-R4) and the seed are merged; then flip the default here.
TO = (os.environ.get('KPC_ANSWERS_TO') or 'overrides').strip().lower()
SHEET_OUT = KEY / 'answers-for-sheet.csv'
SHEET_COLS = ['ref', 'key_id', 'record_id', 'layer', 'record_name', 'fp', 'status', 'quality_yes', 'approved_by', 'approved_date',
              'evidence', 'last_checked', 'seed_from', 'note']
# Nov 2 (Brandon, before the 3:17 AM run): question files BOT A must NOT read. map-audit.json holds the map audit's answers, and
# almost all of them are pattern answers ("pattern NEAR / SPILL / OUTSIDE ...", one verdict for a whole group of rows), not a
# person's look at that row; its "NO ... PIN" means "show the pin until fixed", not "ban this record for ever". Applied here they
# became ~590 hard joins / record bans that later rule fixes could not undo. Comma list of file names (no .json);
# KPC_ANSWERS_SKIP=none reads every file again (the old way). Turn it back on only once those rows mark who really looked.
SKIP = {x.strip().lower() for x in (os.environ.get('KPC_ANSWERS_SKIP') if os.environ.get('KPC_ANSWERS_SKIP') is not None else 'map-audit').split(',')
        if x.strip() and x.strip().lower() != 'none'}


def data_dir():
    for d in (os.environ.get('DATA'), '../kpcdata', '../kpc-data', 'kpcdata'):
        if d and pathlib.Path(d, 'data/waiting/questions').is_dir(): return pathlib.Path(d)
    return None


def load(p, d):
    try: return json.load(open(p))
    except Exception: return d  # noqa: BLE001


def rows_of(j):
    q = j.get('questions') if isinstance(j, dict) else j
    if isinstance(q, dict): q = list(q.values())
    return [r for r in (q or []) if isinstance(r, dict) and r.get('ref') and r.get('record') is not None]


def norm_url(u):
    u = str(u or '').strip().lower().split('?')[0].rstrip('/')
    u = re.sub(r'/query$', '', u)
    return re.sub(r'^https?://', '', u)


def layer_map():
    """layer URL (normalised) -> key prefix, from data/us-key/layers.json (a layer keeps its prefix for ever, see kpc_us_key.py)."""
    m = {}
    for pre, v in (load(KEY / 'layers.json', {}) or {}).items():
        if isinstance(v, list) and v and isinstance(v[0], str) and not v[0].startswith('file:'):
            u = norm_url(v[0]); m[u] = pre
            m[u.replace('/featureserver/', '/mapserver/')] = pre; m[u.replace('/mapserver/', '/featureserver/')] = pre
    return m


def key_id(row, lmap):
    """The key's own id for a question row: ('id' or None, why skipped)."""
    rec = str(row.get('record')).strip()
    lay = row.get('layer')
    if not lay:                                   # key-pieces rows: the record IS a key id (fws448, sgtni131, 195096, rst9580)
        return rec, ''
    u = norm_url(lay)
    if PAD in u: return rec, ''                   # PAD-US: the bare OBJECTID
    if FWS in u: return ('fws' + rec if not rec.startswith('fws') else rec), ''
    pre = lmap.get(u)
    if not pre: return None, f'layer not read by the key: {lay}'
    return (rec if rec.startswith(pre) else pre + rec), ''


def answer_of(row):
    # Oct 31 (Fable review #5): the FIRST word decides ('Yes.', 'YES (sector 2)', '**NO**'); NOT SURE is neither
    a = re.sub(r'^[^A-Za-z]+', '', str(row.get('answer') or '')).upper()
    if a.startswith('NOT'): return ''
    m = re.match(r'(YES|NO)\b', a)
    return m.group(1) if m else ''


def st_of(row):
    a = str(row.get('area') or row.get('st') or '')
    m = re.search(r'\b([A-Z]{2})\b', a.replace('US-', ''))
    return m.group(1) if m else ''


_AUTO_RX = re.compile(r'\(auto\b|\bauto \(T1|checked_by.?auto', re.I)
# Nov 3 addendum (Quality grade of the recut; Super relayed Brandon 7:11-7:12 PM CST, item 4): Mapping's own notes and calls are a
# bot desk's, never a person's answer. Same pattern as kpc_precheck.DESK (a test keeps the two in step).
DESK_RX = re.compile(r"\(Mapping(?:,|\)|'s\b| addendum\b| desk\b)|\bMapping, (?:Oct|Nov|Dec)\b|\bMapping's (?:own )?call\b|\bMapping addendum\b|^\s*Mapping[:,]|\bMapping desk\b")


def is_bot_row(row):
    """A bot's answer (auto T1 map-match and the like), not a person's."""
    return bool(row.get('auto')) or str(row.get('checked_by') or '').strip().lower().startswith('auto')


def has_person_answer(v):
    """Nov 3 (Brandon, relayed by Super 6:52 PM CST, Q6): a person's answer always wins. True when the park's overrides entry
    holds anything a person (or chat 11 / a hand review) decided: an entry with a 'why' note that is not only bot (auto) notes,
    or a join / no / none / alias with no note at all. Mapping's own notes and calls (DESK_RX) never count as a person's."""
    if not v: return False
    notes = [x for x in str(v.get('why') or '').split(' · ') if x.strip()]
    if notes: return any(not _AUTO_RX.search(x) and not DESK_RX.search(x) for x in notes)
    return any(v.get(k) for k in ('join', 'no', 'none', 'alias', 'alias_all'))


def main():
    D = data_dir()
    if D is None:
        print('::notice title=Key answers::no KPC-Data checkout with data/waiting/questions: nothing applied'); return
    lmap = layer_map()
    ovr = load(OVR, {'parks': {}}); P = ovr.setdefault('parks', {})
    led = load(LEDGER, {})
    today = dt.date.today().isoformat(); stamp = dt.datetime.now().strftime('%Y-%m-%d %H:%M')
    n_yes = n_no = n_alias = n_skip = n_same = n_none = n_bot = 0; skipped = []; bot_held = []; states = set(); touched = set(); sheet_rows = {}
    # last answer wins: rows are read file by file (sorted), in file order; the latest row for a (file, ref, id) is the one applied
    skipped_files = []
    for f in sorted(glob.glob(str(D / 'data/waiting/questions/*.json'))):
        name = pathlib.Path(f).stem
        if name.lower() in SKIP: skipped_files.append(name); continue   # Nov 2: see SKIP above
        latest = {}
        for row in rows_of(load(f, {})):
            kid, why = key_id(row, lmap)
            if not kid:
                if answer_of(row): n_skip += 1; skipped.append(f"{row.get('ref')} {why}")
                continue
            latest[(row['ref'], kid)] = row
        for (ref, kid), row in latest.items():
            ans = answer_of(row)
            if not ans: continue                                     # NOT SURE / blank: nothing changes
            lk = f'{name}:{ref}:{kid}'
            if (led.get(lk) or {}).get('answer') == ans: n_same += 1; continue
            nm = str(row.get('record_name') or '').strip()
            ac = row.get('acres') if row.get('acres') is not None else row.get('acres_approx')
            if TO == 'sheet':
                kind_alias = ans == 'YES' and str(row.get('kind') or '').lower() == 'alias'
                sheet_rows[(ref, kid)] = {
                    'ref': ref, 'key_id': kid, 'record_id': str(row.get('record')), 'layer': str(row.get('layer') or ''), 'record_name': nm,
                    'fp': json.dumps([nm, round(float(ac)) if ac not in (None, '') else 0], ensure_ascii=False), 'status': ans,
                    'quality_yes': f"{row.get('checked_by') or 'chat 11'} ({name}.json, {stamp})", 'approved_by': '', 'approved_date': '',
                    'evidence': str(row.get('evidence') or row.get('why') or '')[:300], 'last_checked': today, 'seed_from': f'kpc_key_answers {name}',
                    'note': '; '.join(x for x in ('alias name YES (the key joins it only with the pin inside)' if kind_alias else '',
                                                 'bot YES (auto T1), not a person: rule 22, a person always beats a bot' if row.get('auto') or str(row.get('checked_by') or '').lower().startswith('auto') else '') if x)}
                if ans == 'YES': n_yes += 1
                else: n_no += 1
                led[lk] = {'answer': ans, 'checked_by': row.get('checked_by'), 'applied': stamp, 'to': 'answer sheet'}
                touched.add(ref); st = st_of(row); states.add(st) if st else None
                continue
            # Nov 3 guard (Brandon Q6, relayed 6:52 PM CST): a bot's YES / NO never changes a park a person already answered (BOT A's
            # auto-T1 rows overturned person answers on US-4118, 13298, 11217, 11218, 4477 ... on Nov 3). It is counted and listed instead.
            if is_bot_row(row) and has_person_answer(P.get(ref)):
                n_bot += 1; bot_held.append(f"{ref} {kid}"); continue
            v = P.setdefault(ref, {})
            if ans == 'YES':
                if str(row.get('kind') or '').lower() == 'alias' and nm:
                    v.setdefault('alias', [])
                    if nm not in v['alias']: v['alias'].append(nm)
                    v.setdefault('alias_ok_names', [])   # Nov 2: the key joins a name variant only when chat 11 said YES to THAT name
                    if nm not in v['alias_ok_names']: v['alias_ok_names'].append(nm)
                    n_alias += 1
                else:
                    v['no'] = [x for x in v.get('no', []) if str(x) != kid]   # Nov 2 review: a YES clears even a SOLE NO (the old '... or v.get("no")' put it back)
                    if not v.get('no'): v.pop('no', None)
                    if kid in (v.get('nofp') or {}): v['nofp'].pop(kid)
                    if not v.get('nofp'): v.pop('nofp', None)
                    v.setdefault('join', [])
                    if kid not in [str(x) for x in v['join']]: v['join'].append(kid)
                    v.setdefault('fp', {})[kid] = [nm, round(float(ac)) if ac not in (None, '') else 0]
                    n_yes += 1
                    # Nov 2 evening (Mapping; quality notes 2026-11-02, US-12987 Klamath + US-4783 Beltrami Island): an older
                    # 'none' (a person found no outline of its own) stayed next to the YES join and contradicted it; it would also
                    # hide the park's check list again if the joined record ever went away. A YES join replaces it.
                    if v.pop('none', None): n_none += 1; v['why'] = (v.get('why', '') + ' · ' if v.get('why') else '') + f"{stamp}: the older 'none' (no outline of its own) is replaced by this YES join"
            else:
                v['join'] = [x for x in v.get('join', []) if str(x) != kid]
                if not v['join']: v.pop('join', None)
                if kid in (v.get('fp') or {}): v['fp'].pop(kid)
                if not v.get('fp'): v.pop('fp', None)
                v.setdefault('no', [])
                if kid not in [str(x) for x in v['no']]: v['no'].append(kid)
                # Nov 2 review: a NO is stored WITH the name + acres it was given for ('nofp', like 'fp' for a YES), so it can be
                # matched again after a PAD-US renumbering (the key uses it with KPC_NO_BY_NAME=1). A bare id said nothing.
                if nm: v.setdefault('nofp', {})[kid] = [nm, round(float(ac)) if ac not in (None, '') else 0]
                n_no += 1
            v['why'] = (v.get('why', '') + ' · ' if v.get('why') else '') + f"{stamp}: {name} row {ans} '{nm[:40]}' ({row.get('checked_by') or 'chat 11'}; applied by kpc_key_answers)"
            v['when'] = today
            led[lk] = {'answer': ans, 'checked_by': row.get('checked_by'), 'applied': stamp}
            touched.add(ref); st = st_of(row); states.add(st) if st else None
    # the same for parks a YES reached BEFORE this fix (the ledger skips them now): their last note is this bot's YES join
    # Nov 3 (Quality, Canada key fixes grade: US-7383, US-7854): a later NO from this bot on a DIFFERENT record (its name is not a
    # joined record's name) does not undo the YES, so it is stepped over. A NO on the joined record itself, or any note that is
    # not this bot's (a map-audit "PIN until fixed"), stops the walk: that is a person's call (US-10025, US-1080, US-7145).
    def _yes_is_last(v):
        jn = {str(x) for x in v.get('join') or []}
        if jn & {str(x) for x in v.get('no') or []}: return False
        names = [str(x[0]).lower() for x in (v.get('fp') or {}).values() if x] + [x.lower() for x in jn]
        for note in reversed(str(v.get('why') or '').split(' · ')):
            if 'applied by kpc_key_answers' not in note: return False
            if re.search(r" row YES '", note): return True
            m = re.search(r" row NO '([^']*)'", note)
            if not m: return False
            nm = m.group(1).strip().lower()
            if not nm or any(x.startswith(nm) or nm.startswith(x) for x in names): return False   # a NO on the joined record
        return False
    for ref, v in P.items():
        if v.get('none') and v.get('join') and _yes_is_last(v):
            v.pop('none'); n_none += 1; touched.add(ref)
            v['why'] = v['why'] + f" · {stamp}: the older 'none' (no outline of its own) is replaced by this YES join"
    msg = f"{n_yes} yes / {n_no} no / {n_alias} alias applied on {len(touched)} parks; {n_same} already applied; {n_skip} skipped; {n_none} old 'none' notes replaced by a YES join; states: {' '.join(sorted(states)) or '-'}"
    if n_bot: msg += f"; {n_bot} bot (auto) answers NOT applied because a person already answered the park: {' '.join(bot_held[:10])}"
    if skipped_files: msg += f"; files not read (KPC_ANSWERS_SKIP): {' '.join(skipped_files)}"
    if DRY:
        print('DRY ' + msg); [print('  skip ' + s) for s in skipped[:20]]; return
    if touched and TO == 'sheet':
        import csv
        old_rows = list(csv.DictReader(open(SHEET_OUT, encoding='utf-8'))) if SHEET_OUT.exists() else []
        keep = [r for r in old_rows if (r.get('ref'), r.get('key_id')) not in sheet_rows]   # the newest answer for a (park, record) wins
        with open(SHEET_OUT, 'w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(f, fieldnames=SHEET_COLS, extrasaction='ignore'); w.writeheader()
            for r in keep + [sheet_rows[k] for k in sorted(sheet_rows)]: w.writerow(r)
        save_json(LEDGER, led, 1)
        msg += f"; written to {SHEET_OUT} for the answer sheet (overrides.json not touched)"
    elif touched:
        save_json(OVR, ovr, 1); save_json(LEDGER, led, 1)
    # Oct 30 (chat 2): ADD to tonight's list, never replace it (other bots and hand fixes put states there too); the key's join
    # job takes the states it rebuilt off the list after saving
    old = set(STATES.read_text().split()) if STATES.exists() else set()
    if states - old: STATES.write_text(' '.join(sorted(old | states)) + '\n')
    print('::notice title=Key answers::' + msg + (f"; skipped: {'; '.join(skipped[:5])}" if skipped else ''))


if __name__ == '__main__':
    # Nov 2 review (loud failures): a stop is an ::error (red in the run summary), not a quiet notice. KPC_LOUD_FAIL=1 also
    # exits 1 so the job goes red; default 0 keeps today's exit code (the save step is loud on its own).
    try: main()
    except Exception as e:  # noqa: BLE001
        print(f'::error title=Key answers::stopped, chat 11\'s answers were NOT applied: {type(e).__name__}: {str(e)[:200]}')
        if os.environ.get('KPC_LOUD_FAIL', '0') == '1': sys.exit(1)
    sys.exit(0)
