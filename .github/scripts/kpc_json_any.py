#!/usr/bin/env python3
"""Read JSON / JSONL from a path or that path plus '.gz', preferring .gz when it is on disk.

Same rule as KPC-Data's kpc_json_any.py (the storage pass that stores question files,
verdicts.jsonl, external-results.json and ready.json as .gz and drops the plain copy).
A plain file is still read when no .gz sibling exists, so a checkout that has not been
compressed keeps working.

A missing expected file raises MissingInput. Callers that used to swallow that and
treat it as an empty object now fail instead of quietly doing nothing.
"""
import glob, gzip, json, pathlib, sys


class MissingInput(FileNotFoundError):
    """The expected input is not on disk as this path or this path plus .gz."""


def _pair(path):
    """(plain path, gz path) for a logical path or a path that already ends in .gz."""
    p = pathlib.Path(path)
    s = str(p)
    if s.endswith('.gz'):
        return pathlib.Path(s[:-3]), p
    return p, pathlib.Path(s + '.gz')


def resolve_any(path):
    """The file to open: path+'.gz' when it exists, otherwise path. A path that already
    ends in .gz is used as-is when that file exists."""
    plain, gz = _pair(path)
    if gz.is_file():
        return gz
    return plain


def exists_any(path):
    """True when path or path+'.gz' is a file. .gz counts, so an exists() check on the
    plain name does not miss a gz-only checkout."""
    return resolve_any(path).is_file()


def _read(path):
    if str(path).endswith('.gz'):
        with gzip.open(path, 'rt', encoding='utf-8') as fh:
            return json.load(fh)
    with open(path, encoding='utf-8') as fh:
        return json.load(fh)


def load_json_any(path):
    """JSON from path or path+'.gz'. .gz wins when both exist. Missing raises MissingInput
    (it is not an empty object)."""
    plain, gz = _pair(path)
    p = gz if gz.is_file() else plain
    if not p.is_file():
        raise MissingInput(f'{plain} is not on disk as that path or {gz.name}')
    return _read(p)


def iter_jsonl_any(path):
    """JSON objects, one per line, from path or path+'.gz'. Blank and broken lines are skipped.
    A missing file raises MissingInput instead of looking like an empty log."""
    plain, gz = _pair(path)
    p = gz if gz.is_file() else plain
    if not p.is_file():
        raise MissingInput(f'{plain} is not on disk as that path or {gz.name}')
    opener = gzip.open if str(p).endswith('.gz') else open
    with opener(p, 'rt', encoding='utf-8') as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except ValueError:
                continue


def glob_json_any(pattern):
    """Glob a logical pattern such as 'data/waiting/questions/*.json'.

    Also matches the .gz form. Returns one logical path (no .gz suffix) per file, .gz preferred
    when both copies exist, so Path(p).stem stays the name the readers already use.
    """
    found = {}
    for hit in glob.glob(pattern) + glob.glob(pattern + '.gz'):
        logical = hit[:-3] if hit.endswith('.gz') else hit
        if logical not in found or hit.endswith('.gz'):
            found[logical] = logical
    return [found[k] for k in sorted(found)]


def materialize(path):
    """Write the preferred bytes to the plain path and return that path.

    .gz wins when both exist (the plain file in a throwaway checkout is replaced).
    A plain-only file is left as it is. Neither file raises MissingInput.

    For a reader whose source is part of a key rules hash and so cannot grow a gzip
    open of its own (kpc_ca_hardlook.py). The workflow calls this, then the reader
    opens the plain path it already knows.
    """
    plain, gz = _pair(path)
    if gz.is_file():
        plain.parent.mkdir(parents=True, exist_ok=True)
        plain.write_bytes(gzip.decompress(gz.read_bytes()))
        return plain
    if plain.is_file():
        return plain
    raise MissingInput(f'{plain} is not on disk as that path or {gz.name}')


def main(argv):
    if len(argv) == 3 and argv[1] == '--materialize':
        try:
            p = materialize(argv[2])
        except MissingInput as e:
            print(f'::error title=Data file::{e}')
            return 1
        print(f'materialized {p}')
        return 0
    print('usage: kpc_json_any.py --materialize <path>', file=sys.stderr)
    return 2


if __name__ == '__main__':
    sys.exit(main(sys.argv))
