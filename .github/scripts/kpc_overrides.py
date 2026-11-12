#!/usr/bin/env python3
"""US-key overrides reader / writer (KPC-Links #151, Nov 11 2026; readers fixed Nov 12 2026). data/us-key/overrides.json grew past
the 1 MB per-file cap, so its parks are split. Not a rule file (kpc_key_freeze.NOT_RULES): it never decides a join.

Layout (what a person edits):
  data/us-key/overrides.json            the MANIFEST: note, blocked_ids_about, blocked_ids, parts = [part file names], and
                                         parks = every park whose override has a 'no' list (a person's NO). The 2-fer rule files
                                         (kpc_fers_guard.override_no, kpc_fers.py, kpc_fers_preline.py) read only the 'no' lists
                                         and blocked_ids of this file, so they still see every one without a code change (the
                                         2-fer rules hash does not move).
  data/us-key/overrides-parks-NN.json   {"parks": {...}}: every other park, sorted by ref, each file under CAP bytes.
  The manifest's parts_sha256 = {part: sha256 of its parks, canonical JSON}. So every override change also changes the manifest:
  kpc_fers_preline.py (a 2-fer rule file, not edited) dates 'overrides newer than the key' by overrides.json's commit time, and
  that stays true. A part edited by hand without the manifest no longer matches: every reader stops until `split` is run.
  To change one park: edit it where it is (`python3 .github/scripts/kpc_overrides.py where data/us-key/overrides.json US-1234`).
  A park that gets a 'no' list belongs in the manifest: run `python3 .github/scripts/kpc_overrides.py split data/us-key/overrides.json`
  after a hand edit (it moves it and re-sorts; same content, same bytes when nothing changed). Until then every reader stops loudly.

  load(path)            -> {note, blocked_ids_about, blocked_ids, parks, parts} with every park in 'parks'. FAILS CLOSED: a missing
                           manifest (unless missing_ok and no part file exists), a missing / unreadable part, a part without a
                           'parks' object, two files holding one ref, a part park with a 'no' list, or a part file in the folder the
                           manifest does not name all raise. An empty override set would un-sign every signed answer.
  merge(m, read_part)   the same merge for any tree (a git revision: kpc_area_hash); keep_parts=False gives the single-file shape.
  save(path, doc)       writes the manifest + parts (one file when the whole document fits under CAP). Deterministic; a park
                           stays in the part it is in, so a one-park edit rewrites one part (and the manifest only when its 'no'
                           parks or headers change). Every file is checked under CAP before anything is written.
  python3 kpc_overrides.py split|check|paths|where|sha PATH [REF]
"""
import hashlib, json, pathlib, sys

CAP = 1_000_000
PACK = 900_000            # a part over this is packed again (room under the cap)
FILL = 700_000            # a fresh pack fills each part to about this, so parts can grow a long way before a repack
PART_GLOB = 'overrides-parks-*.json'
PART_NAME = 'overrides-parks-{:02d}.json'
NOTE = ("Nov 11 2026 (KPC-Links #151): parks are split across the files in 'parts' (each under 1,000,000 bytes); parks with a "
        "'no' list stay in this file. Load with .github/scripts/kpc_overrides.py (load), write with its save or 'split'.")


class OverridesError(ValueError):
    """The override set cannot be read whole. Never treat it as empty."""


def has_no(v):
    """True when the park's override carries a person's NO (the same test as kpc_fers_guard.override_no)."""
    return isinstance(v, dict) and bool([x for x in (v.get('no') or []) if x is not None])


def sort_key(ref):
    a, _, b = str(ref).partition('-')
    return (a, int(b) if b.isdigit() else 10 ** 9, str(ref))


def _plain(name):
    if not isinstance(name, str) or not name or pathlib.PurePosixPath(name).name != name or '\\' in name or name in ('.', '..'):
        raise OverridesError(f'override part name must be a plain file name in the same folder: {name!r}')
    return name


def merge(manifest, read_part, keep_parts=True, strict=True):
    """manifest = the parsed overrides.json; read_part(name) -> the parsed part file (raise when missing). A document with no
    'parts' is returned as it is. keep_parts=False drops the 'parts' key (the single-file shape: kpc_area_hash). parts_sha256 is
    checked part by part and never returned (it is bookkeeping, not an override). strict=False (only `split`, which re-sorts a
    hand edit) skips the digest and the 'no'-placement checks; a missing part or a ref in two files still raises."""
    if not isinstance(manifest, dict):
        raise OverridesError('overrides.json is not a JSON object')
    parts = manifest.get('parts')
    if not parts:
        return manifest
    if not isinstance(parts, list):
        raise OverridesError("overrides.json 'parts' must be a list of file names")
    own = manifest.get('parks') or {}
    if not isinstance(own, dict):
        raise OverridesError("overrides.json 'parks' must be an object")
    parks, where = dict(own), {r: 'overrides.json' for r in own}
    sums = manifest.get('parts_sha256')
    if strict and (not isinstance(sums, dict) or set(sums) != set(parts)):
        raise OverridesError("overrides.json parts_sha256 must name every part: run python3 .github/scripts/kpc_overrides.py split data/us-key/overrides.json")
    for name in parts:
        part = read_part(_plain(name))
        chunk = part.get('parks') if isinstance(part, dict) else None
        if not isinstance(chunk, dict):
            raise OverridesError(f'override part {name} has no parks object')
        if strict and canon_sha(chunk) != sums.get(name):
            raise OverridesError(f'override part {name} does not match its parts_sha256 in overrides.json (edited by hand?): '
                                 'run python3 .github/scripts/kpc_overrides.py split data/us-key/overrides.json and commit every file it writes')
        for r, v in chunk.items():
            if r in where:
                raise OverridesError(f'{r} is in both {where[r]} and {name}: one park, one place')
            if strict and has_no(v):
                raise OverridesError(f"{r} in {name} has a 'no' list: it belongs in overrides.json (the 2-fer guard reads 'no' there). "
                                     f"Run: python3 .github/scripts/kpc_overrides.py split data/us-key/overrides.json")
            where[r] = name
        parks.update(chunk)
    out = {k: v for k, v in manifest.items() if k not in ('parts', 'parks', 'parts_sha256')}
    out['parks'] = {r: parks[r] for r in sorted(parks, key=sort_key)}
    if keep_parts:
        out['parts'] = list(parts)
    return out


def _read(path, encoding='utf-8'):
    try:
        return json.loads(pathlib.Path(path).read_text(encoding=encoding))
    except FileNotFoundError:
        raise
    except ValueError as e:
        raise OverridesError(f'{path} is not readable JSON: {e}') from e


def load(path, encoding='utf-8', missing_ok=False, strict=True):
    """The whole overrides document (see the module text). missing_ok: a missing manifest with NO part file beside it returns
    {'parks': {}} (a temp tree, a key that has no overrides yet); anything else that is missing raises."""
    path = pathlib.Path(path)
    stray = sorted(f.name for f in path.parent.glob(PART_GLOB)) if path.parent.is_dir() else []
    if not path.is_file():
        if missing_ok and not stray:
            return {'parks': {}}
        raise OverridesError(f'{path} is missing' + (f' but its part files are there ({", ".join(stray)})' if stray else '')
                             + ': refusing to read an empty override set')
    d = _read(path, encoding)
    named = set((d.get('parts') or []) if isinstance(d, dict) and isinstance(d.get('parts'), list) else [])
    extra = [n for n in stray if n not in named]
    if extra:
        raise OverridesError(f'{path.parent}: part file(s) {", ".join(extra)} are not named in {path.name} parts: '
                             'a writer that bypassed kpc_overrides.save would fork the data')

    def part(name):
        p = path.parent / name
        if not p.is_file():
            raise OverridesError(f'override part {p} named in {path.name} is missing: refusing to read a partial override set')
        return _read(p, encoding)
    return merge(d, part, strict=strict)


def load_parks(path, missing_ok=False):
    return load(path, missing_ok=missing_ok).get('parks') or {}


def _dump(obj):
    return json.dumps(obj, indent=1, ensure_ascii=False) + '\n'


def _size(obj):
    return len(_dump(obj).encode('utf-8'))


_W = len(_dump({'parks': {'a': 0}}).encode('utf-8')) - len('  "a": 0'.encode('utf-8'))


def _entry(r, v):
    """bytes one park adds to a pretty-printed {"parks": {...}} file (the comma and newline between entries counted apart)."""
    return _size({'parks': {r: v}}) - _W


def _gsize(g, parks, sz):
    return _W + sum(sz[r] for r in g) + 2 * max(0, len(g) - 1) if g else _size({'parks': {}})


def _greedy(refs, parks, sz):
    out, cur, n = [], [], 0
    for r in refs:
        if sz[r] + _W > PACK:
            raise OverridesError(f'a single override row will not fit under the cap: {r}')
        add = sz[r] + (2 if cur else 0)
        if cur and _W + n + add > FILL:
            out.append(cur); cur, n, add = [], 0, sz[r]
        cur.append(r); n += add
    if cur:
        out.append(cur)
    return out


def _existing(path):
    """[[refs] per part] of the layout on disk, in part order; [] when there is none (or it cannot be read)."""
    try:
        d = json.loads(path.read_text(encoding='utf-8'))
        out = []
        for name in d.get('parts') or []:
            out.append(list((json.loads((path.parent / _plain(name)).read_text(encoding='utf-8')).get('parks') or {}).keys()))
        return out
    except Exception:  # noqa: BLE001  (no layout to keep: pack from scratch)
        return []


def layout(path, doc):
    """{file name: bytes} that save() would write (the manifest under path.name). Pure apart from reading the layout on disk."""
    path = pathlib.Path(path)
    doc = dict(doc or {})
    parks = dict(doc.get('parks') or {})
    head = {k: v for k, v in doc.items() if k not in ('parks', 'parts', 'parts_sha256')}
    single = dict(head); single['parks'] = parks
    if _size(single) <= CAP and not _existing(path):
        return {path.name: _dump(single).encode('utf-8')}
    own = {r: parks[r] for r in sorted(parks, key=sort_key) if has_no(parks[r])}
    rest = sorted((r for r in parks if r not in own), key=sort_key)
    sz = {r: _entry(r, parks[r]) for r in rest}
    old = [[r for r in refs if r in parks and r not in own] for refs in _existing(path)]
    old = [refs for refs in old if refs]
    if old:
        # sticky: a park stays in its part; a new park goes to the first part whose last ref sorts at or after it (else the last)
        placed = {r: i for i, refs in enumerate(old) for r in refs}
        groups = [list(refs) for refs in old]
        ends = [max(refs, key=sort_key) for refs in old]
        for r in rest:
            if r in placed: continue
            i = next((i for i, e in enumerate(ends) if sort_key(r) <= sort_key(e)), len(groups) - 1)
            groups[i].append(r)
        if any(_gsize(g, parks, sz) > PACK for g in groups):
            groups = _greedy(rest, parks, sz)     # a part outgrew the room: pack again from scratch (rare)
    else:
        groups = _greedy(rest, parks, sz)
    names = [PART_NAME.format(i) for i in range(1, len(groups) + 1)]
    note = str(head.get('note') or '')
    if 'parks are split across the files' not in note:
        head['note'] = (note.rstrip() + ' · ' + NOTE) if note else NOTE
    chunks = [{r: parks[r] for r in sorted(g, key=sort_key)} for g in groups]
    manifest = dict(head); manifest['parts'] = names
    manifest['parts_sha256'] = {n: canon_sha(c) for n, c in zip(names, chunks)}
    manifest['parks'] = own
    files = {path.name: _dump(manifest).encode('utf-8')}
    for name, c in zip(names, chunks):
        files[name] = _dump({'parks': c}).encode('utf-8')
    for name, b in files.items():
        if len(b) > CAP:
            raise OverridesError(f'{name} would be {len(b)} bytes, over the {CAP} cap: nothing written')
    return files


def save(path, doc, encoding='utf-8'):
    """Write doc (a whole overrides document, as load returns it) to path and its parts; remove part files no longer named."""
    path = pathlib.Path(path)
    files = layout(path, doc)
    for name, b in files.items():
        p = path.parent / name
        if not p.is_file() or p.read_bytes() != b:
            p.write_bytes(b)
    for f in path.parent.glob(PART_GLOB):
        if f.name not in files:
            f.unlink()
    return path


def paths(path):
    """The manifest and its part files (for 'git add' / save lists)."""
    path = pathlib.Path(path)
    d = _read(path)
    return [str(path)] + [str(path.parent / _plain(n)) for n in (d.get('parts') or [])]


def canon_sha(parks):
    return hashlib.sha256(json.dumps(parks, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')).hexdigest()


def check(path):
    """[] when the override files are whole, placed right and under the cap; else the problems."""
    path = pathlib.Path(path); bad = []
    try:
        d = load(path)
    except (OverridesError, FileNotFoundError) as e:
        return [str(e)]
    for p in paths(path):
        n = pathlib.Path(p).stat().st_size
        if n > CAP: bad.append(f'{p} is {n} bytes, over the {CAP} cap')
    if d.get('parts'):
        want = layout(path, d)
        if sorted(want) != sorted([path.name] + list(d['parts'])) or any((path.parent / n).read_bytes() != b for n, b in want.items()):
            bad.append(f'{path}: the files are not in the layout save() writes (run kpc_overrides.py split)')
    return bad


def main(argv):
    if len(argv) < 3 or argv[1] not in ('split', 'check', 'paths', 'where', 'sha'):
        print(__doc__); return 2
    cmd, path = argv[1], pathlib.Path(argv[2])
    if cmd == 'split':
        d = load(path, strict=False); before = canon_sha(d['parks'])   # takes in a hand edit of a part (the digests are written new)
        save(path, d)
        after = load(path)
        if canon_sha(after['parks']) != before:
            print(f'::error title=Overrides::{path}: the split changed the content'); return 1
        print(f'{path}: {len(after["parks"])} parks, canonical sha256 {before}; files: ' +
              ', '.join(f'{pathlib.Path(p).name} {pathlib.Path(p).stat().st_size}' for p in paths(path)))
        return 0
    if cmd == 'check':
        bad = check(path)
        for b in bad: print(f'::error title=Overrides::{b}')
        if not bad: print(f'{path}: whole, placed right, every file under {CAP} bytes')
        return 1 if bad else 0
    if cmd == 'paths':
        print('\n'.join(paths(path))); return 0
    if cmd == 'sha':
        d = load(path); print(len(d['parks']), canon_sha(d['parks'])); return 0
    ref = argv[3] if len(argv) > 3 else ''
    d = _read(path)
    if ref in (d.get('parks') or {}): print(path); return 0
    for n in d.get('parts') or []:
        if ref in (_read(path.parent / _plain(n)).get('parks') or {}): print(path.parent / n); return 0
    print(f'{ref}: no override'); return 1


if __name__ == '__main__':
    sys.exit(main(sys.argv))
