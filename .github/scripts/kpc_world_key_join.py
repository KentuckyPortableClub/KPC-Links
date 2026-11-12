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
  - --planned-groups JSON (the plan's groups). Nov 12 (KPC owner, 2026-11-12; run 43200398601: five short countries blocked the French
    layers and every other save): EACH COUNTRY STANDS ALONE. A planned country with no part, not in its part's done.txt, or held by
    its part's gate is NOT joined: its key / review page / tracts / outlines / index row / shared-file keys stay main's bytes, it is
    named failed, listed red in --record and in GITHUB_OUTPUT red=; every other country is joined. Exit 1 (built=0, NOTHING written)
    only on a conflict, unreadable groups, or a country in a part the plan did not give it. --expected "AU MT" (the plan's checked
    expected holds) are kept from main and not red. --record F: per country {built, verdict, action saved|kept, code, why}; the one
    run summary table is written from it after the stamp (kpc_area_join.py summary).
  - check-saved --record F --key-dir data/world-key: "may we save the green set?": exit 1 when a saved country was not built green or a
    kept country is not main's bytes (then nothing is saved).
  - expected --file data/outlines/world-expected-holds.approved.json --countries "$ALL" --key data/world-key [--cache cache/world]:
    the owner-signed expected holds for this run's list (stdout: "AU MT"). An entry is used only when its country is in the list,
    it has a reason, a real person's sign-off (approved_by / approved_date; 'Brandon (KZ4CP)' counts; 'KPC owner' is not a
    signature), a source, a copy_sha256 (the sha256 of W-<CC>.json.gz), and no passed review_by date; anything else is ignored
    and said (the country is built as a normal country). With --cache, the hold applies only when the saved copy's sha matches;
    a changed or missing copy does not inherit the hold. An expected hold with NO joined park on main (nothing to keep) =
    exit 1 (the plan stops, nothing is built or saved).
  - keep-rows --countries "AU MT" [--unchanged data/world-key] --review data/world-key/review [--ref HEAD]: after the join check, the
    rows of the given countries (Nov 12: and with --unchanged of EVERY country whose key file this run did not change) in held-joins.json / .csv, held-joins-ledger.csv, join-check.json / .csv come back from main byte for byte (the join
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


def plan(parts, out, gate=False, exclude=None):
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
        # Nov 12 (KPC owner, 2026-11-12): a planned country NOT built this run (exclude) is treated like a held one: nothing of it is
        # joined (key, review, tracts, outlines, index row, its keys in the shared files) and its part makes no whole-file write
        ex = sorted(mine & set(exclude or ()))
        failed += ex
        held = sorted(set(held) | set(ex))
        if held and set(held) == set(mine): continue   # nothing of this part is joined, not even its shared files
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


def _hold_signed(approved_by, approved_date, who, today=None):
    """A real person's sign-off. 'KPC owner' is not a signature. The display form 'Brandon (KZ4CP)' counts when Brandon or
    KZ4CP is a listed person (kpc_answer_words.signed_off requires an exact name, so the parenthetical form is accepted here)."""
    import datetime, kpc_answer_words as AW
    who = {str(w).strip().lower() for w in (who or []) if str(w).strip().lower() != 'kpc owner'}
    if AW.signed_off(approved_by, approved_date, who, today=today):
        return True
    tokens = set()
    for part in re.split(r'[,;+&]|\band\b', str(approved_by or '')):
        part = part.strip()
        if not part:
            continue
        m = re.fullmatch(r'(.+?)\s*\(([^)]+)\)', part)
        if m:
            tokens.add(m.group(1).strip().lower()); tokens.add(m.group(2).strip().lower())
        else:
            tokens.add(part.lower())
    if not tokens & who:
        return False
    try: d = datetime.date.fromisoformat(str(approved_date or '').strip()[:10])
    except ValueError: return False
    return d <= (today or datetime.date.today())


def _copy_file_sha(cache_dir, c):
    """sha256 of cache/W-<CC>.json.gz, or '' if the file is not there. None when no cache was given (no live check)."""
    if not cache_dir:
        return None
    p = pathlib.Path(cache_dir) / f'W-{c}.json.gz'
    return _sha(p) if p.is_file() else ''


def load_expected(path, countries, key_dir, persons=None, today=None, cache_dir=None):
    """(held {CC: why}, notes [ignored entries], errors [held with nothing to keep]). Fail closed: only a file named *.approved.json is
    read; an entry is used only when it is signed by a real person, has a reason and a source, its copy_sha256 is the sha256 of one
    saved copy, its country is in this run's list and its review_by is not past. With cache_dir, the hold applies only when the
    copy's sha matches (a changed or missing copy does not inherit the hold). 'KPC owner' is not a signature."""
    import datetime
    today = today or _today()
    p = pathlib.Path(path) if path else None
    if p is None or not p.is_file(): return {}, [], []
    if not p.name.endswith(EXPECTED_SUFFIX): return {}, [f'{p.name}: only a file named *{EXPECTED_SUFFIX} is read'], []
    doc = _load(p)
    if not isinstance(doc, dict) or not isinstance(doc.get('holds'), dict): return {}, [f'{p.name}: unreadable or no "holds" object: not read'], []
    import kpc_answer_words as AW
    who = {w.lower() for w in (persons if persons is not None else AW.persons(os.environ.get('KPC_PERSONS')))}
    mine = set(str(countries or '').upper().split())
    held, notes, errors = {}, [], []
    for c, e in doc['holds'].items():
        if not CC_RE.match(str(c)) or not isinstance(e, dict): notes.append(f'{c}: not a country entry: ignored'); continue
        if c not in mine: notes.append(f"{c}: not in this run's countries: ignored"); continue
        if not str(e.get('reason') or '').strip(): notes.append(f'{c}: no reason: ignored, built as a normal country'); continue
        if not _hold_signed(e.get('approved_by'), e.get('approved_date'), who, today=today):
            notes.append(f"{c}: not signed (approved_by {e.get('approved_by')!r}, approved_date {e.get('approved_date')!r}): ignored, built as a normal country"); continue
        if not str(e.get('source') or '').strip():
            notes.append(f'{c}: no source: ignored, built as a normal country'); continue
        want = str(e.get('copy_sha256') or '').strip().lower()
        if not re.fullmatch(r'[0-9a-f]{64}', want):
            notes.append(f'{c}: no copy_sha256 (the hold is for one saved copy): ignored, built as a normal country'); continue
        got = _copy_file_sha(cache_dir, c)
        if got is not None and got != want:
            if not got:
                notes.append(f'{c}: no saved copy W-{c}.json.gz in the cache to check the hold against: ignored, built as a normal country')
            else:
                notes.append(f'{c}: copy sha mismatch (hold is for {want[:12]}, this copy {got[:12]}): ignored, built as a normal country')
            continue
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
    ap.add_argument('--cache', default='', help='folder of W-<CC>.json.gz copies; a hold applies only when the copy sha matches')
    a = ap.parse_args(argv)
    held, notes, errors = load_expected(a.file, a.countries, a.key, cache_dir=(a.cache or None))
    for n in notes: print(f'::warning title=Expected holds::{n}', file=sys.stderr, flush=True)
    for c, why in held.items(): print(f'::notice title=World key {c}::{c} held (expected): keeping the previous join. {why}', file=sys.stderr, flush=True)
    if errors:
        for x in errors: print(f'::error title=Expected holds::{x}: fix data/outlines/world-expected-holds.approved.json (the run stops, nothing is built)', file=sys.stderr, flush=True)
        return 1
    print(' '.join(held))
    return 0


import kpc_area_join as AJ   # Nov 12 (KPC owner, 2026-11-12): the per-area review merge now lives there (world, US and Canada use it)
REVIEW_FILES = AJ.REVIEW_FILES
_csv_records = AJ.csv_records


def _row_cc(row, name):
    a = AJ.row_area(row, name)
    return a if a and CC_RE.match(a) else None


def merge_rows(name, main_text, cur_text, keep):
    """New text of one review file: this run's rows of every other country + main's rows of the `keep` countries (byte for byte),
    in country order. None = the rows cannot be split per country safely (the caller puts main's file back whole)."""
    return AJ.merge_rows(name, main_text, cur_text, keep)


def keep_rows(review, keep, ref='HEAD', unchanged_of=None):
    """Write the merged review files; returns [(file, what happened)]. unchanged_of = data/world-key: every country whose key file
    this run did not change keeps main's rows too (Nov 12: the a6c493c wipe can no longer happen on a partial save)."""
    return AJ.keep_rows(review, keep, ref, unchanged_of)


def main_keep_rows(argv):
    ap = argparse.ArgumentParser(description='keep the review rows of the expected-hold countries from main (after the join check)')
    ap.add_argument('keep_rows'); ap.add_argument('--countries', default=''); ap.add_argument('--review', default='data/world-key/review')
    ap.add_argument('--ref', default='HEAD')
    ap.add_argument('--unchanged', default='', help='the key folder (data/world-key): every country whose key file did not change keeps main\'s rows')
    a = ap.parse_args(argv)
    for name, what in keep_rows(a.review, a.countries.split(), a.ref, a.unchanged or None):
        print(f"::{'warning' if what.startswith('NOT') else 'notice'} title=Review files::{name}: {what}", flush=True)
    return 0


def hint(c):
    """What a person does next for a country held on its saved copy (Nov 12 update: run 43222090832 rebuilt BE CH CZ DE PT and all five
    stayed short, because the key run only gate-checks the copy; the refresh is kpc-world-cache.yml)."""
    return (f'. Next: refresh the saved copy with KPC saved shapes (kpc-world-cache.yml, countries={c}), then rerun the world key for {c} '
            '(a key run only gate-checks the copy, it cannot refresh it)')


def classify(parts, planned_groups, expected=''):
    """Nov 12 (KPC owner, 2026-11-12): each country stands alone. (fatal problems, {country: record}). Fatal (nothing is joined or
    saved): the plan's groups are not JSON, or a part carries a country the plan did not give it. Not fatal: a planned country with no
    part, or not built in its part (failed, timed out, held by its build): it is NOT joined, keeps its previous files from main
    byte for byte, and is named failed; every other country is joined as usual."""
    try: groups = json.loads(planned_groups or '[]')
    except ValueError: return ['the plan\'s groups are not JSON'], {}
    if not isinstance(groups, list): return ['the plan\'s groups are not a list'], {}
    planned = sorted({c for g in groups if isinstance(g, dict) for c in str(g.get('countries') or '').split()})
    seen = {}
    for d in sorted(pathlib.Path(p) for p in parts):
        if not d.is_dir(): continue
        mine = set(_words(d / 'countries.txt')); done = set(_words(d / 'done.txt'))
        heldb = set(_words(d / 'held.txt')); failed = set(_words(d / 'failed.txt'))
        held, why = read_verdict(d, mine)
        for c in mine: seen[c] = (d.name, c in done, c in heldb, c in failed, c in held, why if c in held else '')
    fatal, out = [], {}
    for c in sorted(set(seen) - set(planned)): fatal.append(f'{c}: in a part ({seen[c][0]}) but not planned')
    for c in planned:
        if c not in seen:
            out[c] = {'part': '', 'built': 'no', 'verdict': '-', 'code': 'not-built', 'why': 'its part is missing (no artifact came back)'}; continue
        part, built, heldb, failed, gheld, gwhy = seen[c]
        if not built:
            code, why = 'failed', ('held by its build (exit 3: a source failed or came back empty, no saved records)' if heldb else
                                    'error, time limit or not finished in its build' if failed else 'not in its part\'s done list')
            out[c] = {'part': part, 'built': 'no', 'verdict': 'held' if gheld else 'green', 'code': 'held-gate' if gheld else code,
                      'why': (gwhy + hint(c)) if gheld else why}; continue
        out[c] = {'part': part, 'built': 'yes', 'verdict': 'held' if gheld else 'green', 'code': 'held-gate' if gheld else 'built',
                  'why': (gwhy + hint(c)) if gheld else 'built, gate green'}
    for c in sorted(set(str(expected or '').split()) - set(planned)):
        out[c] = {'part': '', 'built': 'no (not built)', 'verdict': '-', 'code': 'held-expected', 'why': 'owner-signed expected hold: keeping the previous join'}
    return fatal, out


def _write_record(path, rec):
    if path: pathlib.Path(path).write_text(json.dumps(rec, indent=1, sort_keys=True) + '\n', encoding='utf-8')


def main_check_saved(argv):
    """join_verdict: may we save the green set? Every saved country was built in its part with a green gate; every other planned
    country is main's bytes (key, review page, tracts, index row). Exit 1 = nothing is saved."""
    ap = argparse.ArgumentParser(); ap.add_argument('check_saved'); ap.add_argument('--record', required=True); ap.add_argument('--key-dir', default='data/world-key')
    ap.add_argument('--ref', default='HEAD')
    a = ap.parse_args(argv)
    rec = _load(a.record)
    if not isinstance(rec, dict): print('::error title=World key join::no join record: nothing is saved', flush=True); return 1
    bad = [f"{c}: saved but {r.get('code')}" for c, r in (rec.get('areas') or {}).items() if r.get('action') == 'saved' and (r.get('code') != 'built' or r.get('verdict') != 'green')]
    bad += AJ.assert_kept(rec, a.key_dir, a.ref)
    for b in bad: print(f'::error title=World key join::{b}', flush=True)
    if bad: print('::error title=World key join::the green set cannot be saved safely: NOTHING is saved this run (fail closed)', flush=True); return 1
    sv = sorted(c for c, r in rec['areas'].items() if r.get('action') == 'saved'); kp = sorted(c for c, r in rec['areas'].items() if r.get('action') != 'saved')
    print(f"::notice title=World key join::saving {len(sv)} countr{'y' if len(sv) == 1 else 'ies'}: {' '.join(sv)}" + (f"; kept from main (not saved): {' '.join(kp)}" if kp else ''), flush=True)
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv[:1] == ['verdict']: return main_verdict(argv)
    if argv[:1] == ['expected']: return main_expected(argv)
    if argv[:1] == ['keep-rows']: return main_keep_rows(argv)
    if argv[:1] == ['check-saved']: return main_check_saved(argv)
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('parts', nargs='*'); ap.add_argument('--out', default='data/world-key'); ap.add_argument('--bounds', default='data/world-bounds')
    ap.add_argument('--failed-out', default='/tmp/world-failed.txt')
    ap.add_argument('--gate', action='store_true', help='each part must carry its master gate verdict; held countries are not joined (fail closed)')
    ap.add_argument('--held-out', help='write the held countries here (one per line: CC why)')
    ap.add_argument('--planned-groups', help="the plan's groups (JSON): a planned country not built in a part is not joined (kept from main, named failed)")
    ap.add_argument('--expected', default='', help="the plan's expected holds (kept from main, not built)")
    ap.add_argument('--record', help='write the join record here (per country: built?, verdict, saved or kept, reason code, why)')
    a = ap.parse_args(argv)
    if a.held_out: pathlib.Path(a.held_out).write_text('')   # never a stale list from an earlier run
    out = os.environ.get('GITHUB_OUTPUT')
    areas, exclude = {}, set()
    if a.planned_groups is not None:   # Nov 12 (KPC owner, 2026-11-12): each country stands alone
        fatal, areas = classify(a.parts, a.planned_groups, a.expected)
        if fatal:
            print(f"::error title=World key join::{'; '.join(fatal[:20])}: NOTHING written or saved this run (fail closed)", flush=True)
            _write_record(a.record, {'rows_key': 'countries', 'areas': {}, 'problems': ['join-refused: ' + '; '.join(fatal[:20])], 'joined': [], 'red': ['join-refused']})
            if out: open(out, 'a').write('built=0\nred=join-refused\n')
            return 1
        exclude = {c for c, r in areas.items() if r['code'] in ('not-built', 'failed')}
    try:
        p = plan(a.parts, a.out, gate=a.gate, exclude=exclude)
    except JoinConflict as e:
        print(f'::error title=World key join::{e}: the parts did not join per country, nothing written (fail closed)', flush=True)
        _write_record(a.record, {'rows_key': 'countries', 'areas': {}, 'problems': [f'join-refused: {e}'], 'joined': [], 'red': ['join-refused']})
        if out: open(out, 'a').write('built=0\nred=join-refused\n')   # Save / stamp / world-bounds skip on built == '0'
        return 1
    for c, why in p['held'].items():
        print(f'::error title=Master gate {c}::held, not joined (main keeps its previous {c} files): {why}', flush=True)
        if c in areas and areas[c]['code'] != 'held-gate': areas[c].update(verdict='held', code='held-gate', why=why + hint(c))
    if a.held_out: pathlib.Path(a.held_out).write_text(''.join(f'{c} {why}\n' for c, why in p['held'].items()))
    joined = sorted({dst.stem for src, dst in p['copies'] if dst.parent == pathlib.Path(a.out)})
    for c, r in areas.items():
        if c in joined: r['action'] = 'saved'
        else:
            r['action'] = 'kept'
            if r['code'] == 'built': r.update(code='not-built', why='built, but its part carries no key file for it')
    for c in joined:
        areas.setdefault(c, {'part': p['owner'].get(c, ''), 'built': 'yes', 'verdict': 'green', 'code': 'built', 'why': 'built, gate green', 'action': 'saved'})
    n = apply(p, a.out, a.bounds)
    pathlib.Path(a.failed_out).write_text(''.join(f + '\n' for f in p['failed']))
    red = sorted(c for c, r in areas.items() if r['action'] != 'saved' and r['code'] != 'held-expected')
    _write_record(a.record, {'rows_key': 'countries', 'areas': areas, 'joined': joined, 'red': red, 'problems': [],
                             'planned': sorted(c for c, r in areas.items() if r['code'] != 'held-expected')})
    if out: open(out, 'a').write(f'built={n}\nred={" ".join(red)}\n')
    print(f"::notice title=World key join::{n} countries from {p['parts']} job(s)" + (f"; failed or unfinished: {' '.join(p['failed'])}" if p['failed'] else '')
          + (f"; RED, kept from main (not saved): {' '.join(red)}" if red else ''), flush=True)
    for c in red: print(f"::error title=World key {c}::not saved this run, its previous join is kept from main ({areas[c]['code']}: {areas[c]['why']})", flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
