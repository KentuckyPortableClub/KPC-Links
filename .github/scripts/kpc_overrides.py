#!/usr/bin/env python3
"""US-key overrides reader / writer (Nov 11 2026). data/us-key/overrides.json grew past the 1 MB per-file cap, so the parks
are split across the files named in its "parts" list (each under CAP bytes). This module loads them back as one document
and writes them that way. A file with no "parts" (the old single-file form, and every temp file the tests write) still
loads as itself. Not a rule file: it does not decide a join.

  load(path)  -> {note, blocked_ids, parks, ...} with every park in 'parks'
  save(path, doc)  writes path (and part files when needed), each file under CAP
"""
import json, pathlib

CAP = 1_000_000
# leave some room under the cap for pretty-printed JSON
PACK = 900_000


def _read(path, encoding='utf-8'):
    return json.loads(pathlib.Path(path).read_text(encoding=encoding))


def load(path, encoding='utf-8'):
    """Return the overrides document. When path names 'parts', merge those files' parks into one 'parks' dict.
    Later parts must not repeat a ref. A missing file or unreadable JSON raises; a missing path is the caller's to catch."""
    path = pathlib.Path(path)
    d = _read(path, encoding)
    if not isinstance(d, dict):
        return d
    parts = d.get('parts') or []
    if not parts:
        return d
    parks = {}
    for name in parts:
        if pathlib.Path(name).name != name or '/' in name or '\\' in name:
            raise ValueError(f'override part name must be a plain file name in the same folder: {name!r}')
        part = _read(path.parent / name, encoding)
        chunk = part.get('parks') if isinstance(part, dict) else None
        if not isinstance(chunk, dict):
            raise ValueError(f'override part {name} has no parks object')
        overlap = set(parks) & set(chunk)
        if overlap:
            raise ValueError(f'override parts overlap on {sorted(overlap)[:8]}')
        parks.update(chunk)
    out = {k: v for k, v in d.items() if k != 'parts'}
    out['parks'] = parks
    out['parts'] = list(parts)
    return out


def _dump(obj):
    return json.dumps(obj, indent=1, ensure_ascii=False) + '\n'


def _pack(parks):
    """Split parks into one or more dicts whose pretty-printed files stay under PACK (and under CAP)."""
    items = sorted(parks.items(), key=lambda kv: (kv[0].split('-')[0], int(kv[0].split('-')[1]) if kv[0].split('-')[1].isdigit() else kv[0]))
    parts, cur, cur_n = [], {}, 0
    # measure incrementally with a cheap lower bound, then confirm the dump
    def fits(d):
        return len(_dump({'parks': d}).encode('utf-8')) <= PACK

    for ref, row in items:
        trial = dict(cur); trial[ref] = row
        if cur and not fits(trial):
            parts.append(cur)
            cur, cur_n = {ref: row}, 1
            if not fits(cur):
                raise ValueError(f'a single override row will not fit under the cap: {ref}')
        else:
            cur, cur_n = trial, cur_n + 1
    if cur:
        parts.append(cur)
    # confirm every part file, and the manifest, is under CAP
    return parts


def save(path, doc, encoding='utf-8'):
    """Write doc to path. If the parks would make a single file over CAP, write them to part files and a short manifest at path."""
    path = pathlib.Path(path)
    doc = dict(doc or {})
    parks = dict(doc.get('parks') or {})
    # drop a previous parts list from the document we write
    single = {k: v for k, v in doc.items() if k != 'parts'}
    single['parks'] = parks
    blob = _dump(single).encode(encoding)
    # remove any leftover part files we no longer name
    existing = list(path.parent.glob('overrides-parks-*.json')) if path.parent.exists() else []
    if len(blob) <= CAP:
        path.write_text(_dump(single), encoding=encoding)
        for f in existing:
            f.unlink()
        return path
    chunks = _pack(parks)
    names = [f'overrides-parks-{i:02d}.json' for i in range(1, len(chunks) + 1)]
    for name, chunk in zip(names, chunks):
        body = _dump({'parks': chunk}).encode(encoding)
        if len(body) > CAP:
            raise ValueError(f'part {name} is {len(body)} bytes, over the {CAP} cap')
        (path.parent / name).write_bytes(body)
    manifest = {k: v for k, v in doc.items() if k not in ('parks', 'parts')}
    manifest['parts'] = names
    # keep a note that parks live in the part files
    note = str(manifest.get('note') or '')
    marker = 'parks are split across the files in \'parts\''
    if marker not in note:
        extra = ' · Nov 11 2026: parks are split across the files in \'parts\' (each under 1,000,000 bytes). Load with kpc_overrides.load.'
        manifest['note'] = (note.rstrip() + extra) if note else extra.strip(' ·')
    text = _dump(manifest)
    if len(text.encode(encoding)) > CAP:
        raise ValueError('the overrides manifest itself is over the 1 MB cap')
    path.write_text(text, encoding=encoding)
    keep = set(names)
    for f in existing:
        if f.name not in keep:
            f.unlink()
    return path
