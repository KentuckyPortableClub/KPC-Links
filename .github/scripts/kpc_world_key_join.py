#!/usr/bin/env python3
"""kpc_world_key_join.py (Nov 11, KPC owner, 2026-11-11): the world key join puts the build groups' parts together, per COUNTRY, from the
part that OWNS each country, and fails closed on any conflict (exit 1, nothing written). Same rule as kpc_us_key_join.py. Before, the
four shared files (layers / eea-designations / jp-wikidata / outline-test) were "the biggest copy wins": a part with a stale or
partial copy that happened to be larger replaced the others.

  python3 .github/scripts/kpc_world_key_join.py parts/world-key-part-* [--out data/world-key] [--bounds data/world-bounds]
                                                [--failed-out /tmp/world-failed.txt]

A part is one build job's artifact: countries.txt (the countries it was given), failed.txt, world-key/ (index.json, <CC>.json, review/<CC>.md,
tracts/<CC>.json, and whole copies of the shared files) and world-bounds/<CC>/.
Conflicts (any one = exit 1, no file written):
  - one country in the countries.txt of two parts;
  - a part that carries <CC>.json / review / tracts / world-bounds for a country it does not own (or that has no countries.txt);
  - a shared file changed (against the join's checkout) by two parts to different values for the same key;
  - outline-test.json (keyed by country): a part that changes a country it does not own.
A shared file that is a JSON object is merged key by key (only keys a part CHANGED count as its write; nothing is deleted); one that is not
an object is a whole-file write, and two different whole-file writes conflict. Not a rule file: it never decides a join. Standard library only.

Master gate (Nov 11, KPC owner, 2026-11-11; run 43082247085 saved to main on a red gate). With --gate, each part must carry the build job's
verdict, master-gate.json (written by `kpc_world_key_join.py verdict` as the last step of the part, from the gate step's exit code and its
list of short copies). Fail closed, per part:
  - no verdict, an unreadable one, another format, countries that are not the part's own, or files in the part that are not the files the
    verdict lists with their sha256 (a part changed or cut short after the verdict) = EVERY country of that part is held;
  - gate green = nothing held; gate red = the countries whose saved copy was moved aside are held; any other gate state = every country held.
A held country is not joined: its key / review / tracts / outlines and its index row are not taken, so main keeps its previous files
untouched; it is named failed (the stamp then says complete=false) and listed in --held-out. A part with every country held gives nothing,
not even its shared files; a part with some held gives its shared files minus the keys that name a held country (CC or CC-...), and no
whole-file write. A missing part (no artifact) is already not joined, and `kpc_key_freeze.py missing` names its countries failed.

  python3 .github/scripts/kpc_world_key_join.py verdict --part part --countries "AU DE" --rc-file F --short-file F

Nov 12 (KPC owner, 2026-11-11; run 43148551915 was cancelled and its join still saved a6c493c, which emptied the review files):
  - --planned-groups JSON (the plan's groups): every planned country must be in a part's countries.txt AND its done.txt (built this
    run); a missing or short part, or a country not built, = exit 1, built=0, NOTHING written (no partial save). --expected "AU MT"
    (the plan's checked expected holds) are not planned and are named "kept from main" in the step summary table
    (country | part present | verdict | joined or kept from main | why).
  - expected --file data/outlines/world-expected-holds.approved.json --countries "$ALL" --key data/world-key: the owner-signed
    expected holds for this run's list (stdout: "AU MT"). An entry is used only when its country is in the list, it has a reason, a
    person's sign-off (approved_by / approved_date, kpc_answer_words.signed_off) and no passed review_by date; anything else is
    ignored and said (the country is built as a normal country). An expected hold with NO joined park on main (nothing to keep) =
    exit 1 (the plan stops, nothing is built or saved).
  - keep-rows --countries "AU MT" --review data/world-key/review [--ref HEAD]: after the join check, the rows of the expected-hold
    countries in held-joins.json / .csv, held-joins-ledger.csv, join-check.json / .csv come back from main byte for byte (the join
    check writes those files whole from this run's changed key files only). A file whose rows cannot be split per country is put
    back from main whole (not written this run) and the run says so. No countries = nothing touched."""
import argparse, hashlib, json, os, pathlib, re, shutil, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

SHARED = ('layers.json', 'eea-designations.json', 'jp-wikidata.json', 'outline-test.json')
CC_RE = re.compile(r'^[A-Z]{2}$')
COUNTRY_KEYED = ('outline-test.json',)   # the keys of these files are country codes: a part may only change its own


class JoinConflict(Exception):
    pass


def _load(p, default=None):
    try: return json.load(open(p, encoding='utf-8'))
    except Exception: return default  # noqa: BLE001


def _words(p):
    try: return open(p, encoding='utf-8').read().split()
    except OSError: return []


VERDICT = 'master-gate.json'


def _sha(p):
    h = hashlib.sha256()
    with open(p, 'rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def part_files(d):
    """{relative path: sha256} of every file in a part, the verdict itself left out."""
    d = pathlib.Path(d)
    return {str(f.relative_to(d)).replace(os.sep, '/'): _sha(f) for f in sorted(d.rglob('*')) if f.is_file() and str(f.relative_to(d)) != VERDICT}


def make_verdict(part, countries, rc_text, short_text):
    """The build job's master gate verdict for its part. rc_text: the gate step's exit code as written (None = the step left none).
    0 = green; 7 = red, the short copies (W-<CC>, one per line) are held; anything else (no exit code, another code, a short list with
    exit 0, a short copy of a country this job does not own) = every country of the job held."""
    mine = sorted(set(str(countries or '').split()))
    rc = (rc_text or '').strip()
    short = [x for x in (short_text or '').split() if x]
    gate, held, why = 'unknown', mine, 'the gate step left no exit code'
    if rc == '0' and not short: gate, held, why = 'green', [], 'no short saved copy'
    elif rc == '0': gate, why = 'error', f'exit 0 but short copies listed ({" ".join(short[:10])})'
    elif rc == '7':
        cc = [x[2:] if x.startswith('W-') else x for x in short]
        if short and all(x.startswith('W-') for x in short) and set(cc) <= set(mine): gate, held, why = 'red', sorted(set(cc)), 'short saved copy moved aside: ' + ' '.join(short)
        else: gate, why = 'error', f'exit 7 with a short list that is not this job\'s copies ({" ".join(short[:10]) or "empty"})'
    elif rc: gate, why = 'error', f'the gate stopped (exit {rc[:20]})'
    return {'format': 1, 'gate': gate, 'held': held, 'why': why, 'countries': mine, 'short': short, 'files': part_files(part)}


def read_verdict(d, mine):
    """(held countries, why) for one part under --gate; every country of the part when anything is wrong (fail closed)."""
    d = pathlib.Path(d); allc = sorted(mine)
    try: v = json.load(open(d / VERDICT, encoding='utf-8'))
    except FileNotFoundError: return allc, 'no master gate verdict in the part'
    except Exception as e: return allc, f'the master gate verdict is unreadable ({type(e).__name__})'  # noqa: BLE001
    if not isinstance(v, dict) or v.get('format') != 1: return allc, 'the master gate verdict has another format'
    if sorted(v.get('countries') or []) != allc: return allc, 'the verdict names other countries than the part\'s countries.txt'
    if not isinstance(v.get('files'), dict) or v['files'] != part_files(d): return allc, 'the part\'s files are not the files its verdict lists (changed or cut short)'
    held = v.get('held')
    if not isinstance(held, list) or not set(held) <= set(mine): return allc, 'the verdict holds countries the part does not own'
    if v.get('gate') == 'green' and not held: return [], ''
    if v.get('gate') == 'red' and held: return sorted(set(held)), str(v.get('why') or 'short saved copy')
    return allc, f"gate {v.get('gate')!r}: {str(v.get('why') or '')[:200]}"


def _names_held(k, held):
    return any(k == c or str(k).startswith(c + '-') for c in held)


def plan(parts, out, gate=False):
    """Check every part first. Returns the write plan; raises JoinConflict on the first conflict. gate=True: each part's master
    gate verdict decides which of its countries are held (not joined)."""
    out = pathlib.Path(out)
    old = _load(out / 'index.json', {}) or {}
    owner, copies, bounds, rows, failed, shared = {}, [], [], {}, [], {}
    held_all = {}   # country -> why (under gate=True)
    n_parts = 0
    for d in sorted(pathlib.Path(p) for p in parts):
        if not d.is_dir(): continue
        n_parts += 1
        mine = set(_words(d / 'countries.txt'))
        for c in sorted(mine):
            if c in owner: raise JoinConflict(f'country {c} is in the countries of two parts ({owner[c]} and {d.name})')
            owner[c] = d.name
        failed += _words(d / 'failed.txt')
        wk = d / 'world-key'
        carried = [(f, f.stem) for f in wk.glob('*.json')] + [(f, f.stem) for f in (wk / 'review').glob('*.md')] + [(f, f.stem) for f in (wk / 'tracts').glob('*.json')]
        carried += [(f, f.name) for f in (d / 'world-bounds').glob('*') if f.is_dir()]
        for f, cc in carried:
            if CC_RE.match(cc) and cc not in mine:
                raise JoinConflict(f'{d.name} carries {f.relative_to(d)} but does not own {cc}' + ('' if mine else ' (it has no countries.txt)'))
        held, why = read_verdict(d, mine) if gate else ([], '')
        for c in held: held_all[c] = why
        if gate and held and set(held) == set(mine): continue   # nothing of this part is joined, not even its shared files
        pi = (_load(wk / 'index.json', {}) or {}).get('countries', {})
        for c in sorted(mine):
            if c in held: continue
            if (wk / f'{c}.json').exists():
                copies.append((wk / f'{c}.json', out / f'{c}.json'))
                if (wk / 'review' / f'{c}.md').exists(): copies.append((wk / 'review' / f'{c}.md', out / 'review' / f'{c}.md'))
                if (wk / 'tracts' / f'{c}.json').exists(): copies.append((wk / 'tracts' / f'{c}.json', out / 'tracts' / f'{c}.json'))
                if (d / 'world-bounds' / c).is_dir(): bounds.append((d / 'world-bounds' / c, c))
                if c in pi: rows[c] = pi[c]
        for name in SHARED:
            src = wk / name
            if not src.is_file(): continue
            base_p = out / name
            pj, bj = _load(src), _load(base_p)
            ent = shared.setdefault(name, {'writers': [], 'keys': {}, 'whole': None})
            if isinstance(pj, dict) and (bj is None or isinstance(bj, dict)):
                bj = bj or {}
                changed = {k: v for k, v in pj.items() if k not in bj or bj[k] != v}   # keys this part wrote (a stale copy of main is not a write)
                if held: changed = {k: v for k, v in changed.items() if not _names_held(k, held)}   # Nov 11: nothing of a held country
                # Known gap (same as kpc_us_key_join.py): the build jobs check out the run's commit, this join checks out the NEWEST main. A shared
                # key changed on main between the two looks like a write by every part (all with the same old value: reverted, not a conflict;
                # for outline-test, a country the part does not own: a false conflict, red). Only the world key itself writes these files today.
                if name in COUNTRY_KEYED:
                    bad = sorted(k for k in changed if k not in mine)
                    if bad: raise JoinConflict(f'{d.name} changes {name} for {" ".join(bad)}, which it does not own')
                for k, v in changed.items():
                    if k in ent['keys'] and ent['keys'][k][0] != v:
                        raise JoinConflict(f'{name} key {k} written differently by {ent["keys"][k][1]} and {d.name}')
                    ent['keys'][k] = (v, d.name)
                if changed: ent['writers'].append((d.name, src))
            else:   # not a JSON object: a whole-file write, when it differs from the checkout's copy
                if held: continue   # Nov 11: a part with a held country makes no whole-file write
                if base_p.is_file() and base_p.read_bytes() == src.read_bytes(): continue
                if ent['whole'] is not None and ent['whole'][0].read_bytes() != src.read_bytes():
                    raise JoinConflict(f'{name} sent differently by {ent["whole"][1]} and {d.name}')
                ent['whole'] = (src, d.name)
    return {'owner': owner, 'copies': copies, 'bounds': bounds, 'rows': rows, 'failed': sorted(set(failed) | set(held_all)), 'shared': shared, 'parts': n_parts, 'old': old,
            'held': dict(sorted(held_all.items()))}


def _style(text):
    """(indent, compact, ensure_ascii) that re-writes a JSON object the way the part wrote it."""
    ascii_ = not any(ord(ch) > 127 for ch in text)   # json.dump's default escapes non-ASCII; ensure_ascii=False leaves it
    if text.startswith('{\n "') or text.startswith('{\n  "'): return 1, False, ascii_
    if text.startswith('{\n"'): return 0, False, ascii_
    return None, True, ascii_


def apply(p, out, bounds_root):
    out = pathlib.Path(out); bounds_root = pathlib.Path(bounds_root)
    (out / 'review').mkdir(parents=True, exist_ok=True)
    for src, dst in p['copies']:
        dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy(src, dst)
    for src, c in p['bounds']:
        shutil.rmtree(bounds_root / c, ignore_errors=True); shutil.copytree(src, bounds_root / c)
    for name, ent in p['shared'].items():
        if ent['whole'] is not None: shutil.copy(ent['whole'][0], out / name); continue
        if not ent['writers']: continue
        if len(ent['writers']) == 1: shutil.copy(ent['writers'][0][1], out / name); continue   # one writer: its bytes, as its own writer made them
        merged = _load(out / name, {}) or {}
        merged.update({k: v for k, (v, _) in ent['keys'].items()})
        txt = ent['writers'][0][1].read_text(encoding='utf-8')
        ind, compact, asc = _style(txt)
        keys = list(_load(ent['writers'][0][1], {}) or {})
        if keys == sorted(keys):   # written by kpc_save.save_json (layers.json): the same writer, same bytes as a serial run
            from kpc_save import canon
            body = canon(merged, ind)
        else:   # written by json.dump (jp-wikidata, outline-test): the checkout's key order kept, new keys after, same format, no re-sort diff
            body = json.dumps(merged, ensure_ascii=asc, indent=ind, **({'separators': (',', ':')} if compact else {})) + ('\n' if txt.endswith('\n') else '')
        (out / name).write_text(body, encoding='utf-8')
    n = len([1 for src, dst in p['copies'] if dst.parent == out])
    old = p['old']
    idx = dict(old.get('countries') or {}); idx.update(p['rows'])
    new = {'countries': idx}
    pb, pt = old.get('build') or old.get('previous_build'), old.get('built') or old.get('previous_built')
    if pb: new['previous_build'] = pb
    if pt: new['previous_built'] = pt
    if n:
        if not os.environ.get('KPC_STATUS_NAME'):   # the same status file the inline join wrote (data/status/inline-<workflow>.json), never one named after this script
            wf = re.sub(r'[^a-z0-9]+', '-', str(os.environ.get('GITHUB_WORKFLOW') or '').lower()).strip('-')
            os.environ['KPC_STATUS_NAME'] = 'inline-' + wf if wf else 'inline'
        from kpc_save import save_json   # the same writer the key uses
        save_json(str(out / 'index.json'), new)
    return n


def main_verdict(argv):
    ap = argparse.ArgumentParser(description='write the build job\'s master gate verdict into its part (the last step before the upload)')
    ap.add_argument('verdict'); ap.add_argument('--part', required=True); ap.add_argument('--countries', required=True)
    ap.add_argument('--rc-file', required=True); ap.add_argument('--short-file', required=True)
    a = ap.parse_args(argv)
    def rd(p):
        try: return open(p, encoding='utf-8').read()
        except OSError: return None
    v = make_verdict(a.part, a.countries, rd(a.rc_file), rd(a.short_file) or '')
    pathlib.Path(a.part).mkdir(parents=True, exist_ok=True)
    (pathlib.Path(a.part) / VERDICT).write_text(json.dumps(v, indent=1, sort_keys=True) + '\n', encoding='utf-8')
    lvl = 'notice' if v['gate'] == 'green' else 'error'
    print(f"::{lvl} title=Master gate verdict::{v['gate']}: {v['why']}" + (f"; held (not joined): {' '.join(v['held'])}" if v['held'] else ''), flush=True)
    return 0


# ---- Nov 12 (KPC owner, 2026-11-11): no partial save; owner-signed expected holds; their review rows kept from main -------------------
EXPECTED_SUFFIX = '.approved.json'


def _today():
    import datetime
    return datetime.date.today()


def has_previous_join(key_dir, c):
    """True when main's data/world-key/<c>.json has at least one joined park (an 'm' list, not graded 'pin'): something to keep."""
    d = _load(pathlib.Path(key_dir) / f'{c}.json', {}) or {}
    return any(isinstance(p, dict) and p.get('m') and p.get('g') != 'pin' for p in (d.get('parks') or {}).values())


def load_expected(path, countries, key_dir, persons=None, today=None):
    """(held {CC: why}, notes [ignored entries], errors [held with nothing to keep]). Fail closed: only a file named *.approved.json is
    read; an entry is used only when it is signed, has a reason, its country is in this run's list and its review_by is not past."""
    import datetime
    today = today or _today()
    p = pathlib.Path(path) if path else None
    if p is None or not p.is_file(): return {}, [], []
    if not p.name.endswith(EXPECTED_SUFFIX): return {}, [f'{p.name}: only a file named *{EXPECTED_SUFFIX} is read'], []
    doc = _load(p)
    if not isinstance(doc, dict) or not isinstance(doc.get('holds'), dict): return {}, [f'{p.name}: unreadable or no "holds" object: not read'], []
    import kpc_answer_words as AW
    who = {w.lower() for w in (persons if persons is not None else AW.persons(os.environ.get('KPC_PERSONS')))} | {'kpc owner'}
    mine = set(str(countries or '').upper().split())
    held, notes, errors = {}, [], []
    for c, e in doc['holds'].items():
        if not CC_RE.match(str(c)) or not isinstance(e, dict): notes.append(f'{c}: not a country entry: ignored'); continue
        if c not in mine: notes.append(f'{c}: not in this run\'s countries: ignored'); continue
        if not str(e.get('reason') or '').strip(): notes.append(f'{c}: no reason: ignored, built as a normal country'); continue
        if not AW.signed_off(e.get('approved_by'), e.get('approved_date'), who, today=today):
            notes.append(f"{c}: not signed (approved_by {e.get('approved_by')!r}, approved_date {e.get('approved_date')!r}): ignored, built as a normal country"); continue
        rb = str(e.get('review_by') or '').strip()
        if rb:
            try: rbd = datetime.date.fromisoformat(rb[:10])
            except ValueError: notes.append(f'{c}: review_by {rb!r} is not a date: ignored, built as a normal country'); continue
            if rbd < today: notes.append(f'{c}: review_by {rb} has passed: ignored, built as a normal country'); continue
        if not has_previous_join(key_dir, c): errors.append(f'{c}: an expected hold, but main has no joined park for {c} (nothing to keep)'); continue
        held[c] = f"{str(e['reason']).strip()[:160]} (signed {e.get('approved_by')} {e.get('approved_date')}" + (f', review by {rb}' if rb else '') + ')'
    return dict(sorted(held.items())), notes, errors


def main_expected(argv):
    ap = argparse.ArgumentParser(description='the owner-signed expected holds of this run (the plan job)')
    ap.add_argument('expected'); ap.add_argument('--file', required=True); ap.add_argument('--countries', required=True)
    ap.add_argument('--key', default='data/world-key')
    a = ap.parse_args(argv)
    held, notes, errors = load_expected(a.file, a.countries, a.key)
    for n in notes: print(f'::warning title=Expected holds::{n}', file=sys.stderr, flush=True)
    for c, why in held.items(): print(f'::notice title=World key {c}::{c} held (expected): keeping the previous join. {why}', file=sys.stderr, flush=True)
    if errors:
        for x in errors: print(f'::error title=Expected holds::{x}: fix data/outlines/world-expected-holds.approved.json (the run stops, nothing is built)', file=sys.stderr, flush=True)
        return 1
    print(' '.join(held))
    return 0


REVIEW_FILES = ('held-joins.json', 'join-check.json', 'held-joins.csv', 'join-check.csv', 'held-joins-ledger.csv')


def _csv_records(text):
    """[(raw text of the record, {column: value})] after the header, and the header's raw text; the raw text keeps its own bytes."""
    import csv, io
    lines = io.StringIO(text, newline='').readlines()
    it = iter(lines); pos = [0]
    def feed():
        for ln in it:
            pos[0] += 1; yield ln
    rd = csv.reader(feed()); out = []
    try: head = next(rd)
    except StopIteration: return None, []
    head_raw = ''.join(lines[:pos[0]]); last = pos[0]
    for row in rd:
        out.append((''.join(lines[last:pos[0]]), dict(zip(head, row)))); last = pos[0]
    return (head_raw, head), out


def _row_cc(row, name):
    cc = str(row.get('area') or '') if name != 'held-joins-ledger.csv' else str(row.get('park') or '').split('-')[0]
    return cc if CC_RE.match(cc) else None


def merge_rows(name, main_text, cur_text, keep):
    """New text of one review file: this run's rows of every other country + main's rows of the `keep` countries (byte for byte),
    in country order. None = the rows cannot be split per country safely (the caller puts main's file back whole)."""
    keep = set(keep)
    if name.endswith('.json'):
        lk = 'parks' if name == 'held-joins.json' else 'rows'
        try: m, c = json.loads(main_text) if main_text else {lk: []}, json.loads(cur_text) if cur_text else None
        except ValueError: return None
        if c is None: c = dict(m)
        if not (isinstance(m.get(lk), list) and isinstance(c.get(lk), list)): return None
        rows = []
        for src, take in ((c[lk], lambda x: x not in keep), (m[lk], lambda x: x in keep)):
            for r in src:
                cc = _row_cc(r, name) if isinstance(r, dict) else None
                if cc is None: return None
                if take(cc): rows.append((cc, r))
        rows.sort(key=lambda t: t[0])   # stable: each country's rows keep their order
        c[lk] = [r for _, r in rows]
        if name == 'held-joins.json': c['count'] = len(c[lk])
        else: c['suspect'] = len(c[lk])   # 'held' stays this run's count (held-joins.json 'count' is the merged one)
        c['kept_from_main'] = sorted(keep)
        return json.dumps(c, indent=1, ensure_ascii=False)   # the join check's own format (json.dump, indent 1, no newline at the end)
    mh, mr = _csv_records(main_text or '')
    ch, cr = _csv_records(cur_text or '') if cur_text else (mh, [])
    if mh is None and ch is None: return cur_text
    if mh is not None and ch is not None and mh[1] != ch[1]: return None   # another header: the columns cannot be lined up
    rows = []
    for src, take in ((cr, lambda x: x not in keep), (mr, lambda x: x in keep)):
        for raw, r in src:
            cc = _row_cc(r, name)
            if cc is None: return None
            if take(cc): rows.append((cc, raw))
    rows.sort(key=lambda t: t[0])
    return (ch or mh)[0] + ''.join(raw for _, raw in rows)


def _git_show(ref, rel, cwd):
    import subprocess
    r = subprocess.run(['git', 'show', f'{ref}:{rel}'], cwd=cwd, capture_output=True)
    return r.stdout.decode('utf-8') if r.returncode == 0 else None


def keep_rows(review, keep, ref='HEAD'):
    """Write the merged review files; returns [(file, what happened)]."""
    import subprocess
    review = pathlib.Path(review); keep = sorted(set(keep))
    if not keep: return []
    top = subprocess.run(['git', 'rev-parse', '--show-toplevel'], cwd=review if review.is_dir() else review.parent, capture_output=True, text=True).stdout.strip()
    done = []
    for name in REVIEW_FILES:
        f = review / name
        rel = os.path.relpath(f.resolve(), top).replace(os.sep, '/')
        main_text = _git_show(ref, rel, top)
        cur_text = f.read_text(encoding='utf-8') if f.is_file() else None
        if main_text is None and cur_text is None: continue
        new = merge_rows(name, main_text, cur_text, keep)
        if new is None:
            if main_text is None: f.unlink(missing_ok=True)
            else: f.write_text(main_text, encoding='utf-8')
            done.append((name, 'NOT written this run: its rows cannot be split per country; main\'s copy kept whole')); continue
        if new != cur_text:
            f.parent.mkdir(parents=True, exist_ok=True); f.write_bytes(new.encode('utf-8'))
        done.append((name, f"rows of {' '.join(keep)} kept from main"))
    return done


def main_keep_rows(argv):
    ap = argparse.ArgumentParser(description='keep the review rows of the expected-hold countries from main (after the join check)')
    ap.add_argument('keep_rows'); ap.add_argument('--countries', default=''); ap.add_argument('--review', default='data/world-key/review')
    ap.add_argument('--ref', default='HEAD')
    a = ap.parse_args(argv)
    for name, what in keep_rows(a.review, a.countries.split(), a.ref):
        print(f"::{'warning' if what.startswith('NOT') else 'notice'} title=Review files::{name}: {what}", flush=True)
    return 0


def completeness(parts, planned_groups, expected=''):
    """(problems, table rows). Every planned country must be in a part's countries.txt and its done.txt (no missing or short part)."""
    try: groups = json.loads(planned_groups or '[]')
    except ValueError: return ['the plan\'s groups are not JSON'], []
    planned = sorted({c for g in groups for c in str((g or {}).get('countries') or '').split()})
    seen = {}
    for d in sorted(pathlib.Path(p) for p in parts):
        if not d.is_dir(): continue
        mine = set(_words(d / 'countries.txt')); done = set(_words(d / 'done.txt'))
        held, why = read_verdict(d, mine)
        for c in mine: seen[c] = (d.name, c in done, 'green' if c not in held else 'held', why if c in held else '')
    problems, rows = [], []
    for c in planned:
        if c not in seen: problems.append(f'{c}: no part'); rows.append((c, 'no', '-', 'kept from main (nothing saved)', 'its part is missing: the run saves nothing')); continue
        part, built, v, why = seen[c]
        if not built: problems.append(f'{c}: not built in {part}'); rows.append((c, 'yes', v, 'kept from main (nothing saved)', 'not built this run (failed, timed out or held by its build): the run saves nothing')); continue
        rows.append((c, 'yes', v, 'joined' if v == 'green' else 'kept from main (nothing saved)', why or 'built, gate green'))
    for c in sorted(set(seen) - set(planned)): problems.append(f'{c}: in a part but not planned'); rows.append((c, 'yes', seen[c][2], 'kept from main (nothing saved)', 'not in the plan'))
    for c in sorted(set(str(expected or '').split()) - set(planned)): rows.append((c, 'no (not built)', '-', 'kept from main', 'held (expected): keeping the previous join'))
    return problems, sorted(rows)


def write_summary(rows, problems):
    s = os.environ.get('GITHUB_STEP_SUMMARY')
    if not s: return
    t = '**World key join**' + (f" - NOTHING SAVED: {'; '.join(problems[:20])}" if problems else '') + '\n\n| country | part present | verdict | joined or kept from main | why |\n|---|---|---|---|---|\n'
    t += ''.join(f'| {" | ".join(str(x).replace("|", "/") for x in r)} |\n' for r in rows)
    open(s, 'a', encoding='utf-8').write(t + '\n')


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ['verdict']: return main_verdict(argv)
    if argv[:1] == ['expected']: return main_expected(argv)
    if argv[:1] == ['keep-rows']: return main_keep_rows(argv)
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('parts', nargs='*'); ap.add_argument('--out', default='data/world-key'); ap.add_argument('--bounds', default='data/world-bounds')
    ap.add_argument('--failed-out', default='/tmp/world-failed.txt')
    ap.add_argument('--gate', action='store_true', help='each part must carry its master gate verdict; held countries are not joined (fail closed)')
    ap.add_argument('--held-out', help='write the held countries here (one per line: CC why)')
    ap.add_argument('--planned-groups', help="the plan's groups (JSON): every planned country must be built in a part, else nothing is written")
    ap.add_argument('--expected', default='', help="the plan's expected holds (kept from main, not built)")
    a = ap.parse_args(argv)
    if a.held_out: pathlib.Path(a.held_out).write_text('')   # never a stale list from an earlier run
    if a.planned_groups is not None:   # Nov 12 (KPC owner, 2026-11-11): no partial save
        problems, rows = completeness(a.parts, a.planned_groups, a.expected)
        write_summary(rows, problems)
        if problems:
            print(f"::error title=World key join::a part is missing or short ({'; '.join(problems[:20])}): NOTHING written or saved this run (no partial save)", flush=True)
            if os.environ.get('GITHUB_OUTPUT'): open(os.environ['GITHUB_OUTPUT'], 'a').write('built=0\n')
            return 1
    try:
        p = plan(a.parts, a.out, gate=a.gate)
    except JoinConflict as e:
        print(f'::error title=World key join::{e}: the parts did not join per country, nothing written (fail closed)', flush=True)
        if os.environ.get('GITHUB_OUTPUT'): open(os.environ['GITHUB_OUTPUT'], 'a').write('built=0\n')   # Save / stamp / world-bounds skip on built == '0'
        return 1
    for c, why in p['held'].items():
        print(f'::error title=Master gate {c}::held, not joined (main keeps its previous {c} files): {why}', flush=True)
    if a.held_out: pathlib.Path(a.held_out).write_text(''.join(f'{c} {why}\n' for c, why in p['held'].items()))
    n = apply(p, a.out, a.bounds)
    pathlib.Path(a.failed_out).write_text(''.join(f + '\n' for f in p['failed']))
    if os.environ.get('GITHUB_OUTPUT'): open(os.environ['GITHUB_OUTPUT'], 'a').write(f'built={n}\n')
    print(f"::notice title=World key join::{n} countries from {p['parts']} job(s)" + (f"; failed or unfinished: {' '.join(p['failed'])}" if p['failed'] else ''), flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
