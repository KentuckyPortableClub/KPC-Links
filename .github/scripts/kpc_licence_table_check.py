#!/usr/bin/env python3
"""CI check for the coded licence-verdicts table (REPAIRS row 16 / R14).

The keeper uploads licence-verdicts.csv to the KPC-Links boundary-cache release, one row per layer,
columns:

    layer,key id,publish,licence class,credit line,date read

The layer column is the keeper's public code: 'sha256:' + 16 hex of the normalised address
(host + path lower case, no /query, no trailing slash, no query string). No layer address belongs
in this table or in any public file.

This script checks a table's columns and values, and can compare a repo copy to a release file of
the same format. It does not fetch the release (CI runs with gh logged out); pass --release PATH
when a copy is already on disk.

When data/outlines/licence-verdicts.csv is not in the tree yet (it lands with KPC-Links #313,
prep/nov20-one-licence-answer at 38ddad4c), a missing live file is a notice, not a failure. The
format tests still run against fixtures.

KPC owner, Nov 20 2026
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import re
import sys
import urllib.parse
from pathlib import Path

COLUMNS = ['layer', 'key id', 'publish', 'licence class', 'credit line', 'date read']
LAYER_CODE = re.compile(r'^sha256:[0-9a-f]{16}$')
PUBLISH = {'yes', 'no'}
# A cell that looks like a layer address (or a host/path of one) must never appear in this public table.
ADDRESS_RX = re.compile(
    r'(?i)(https?://|www\.|[a-z0-9.-]+\.(?:arcgis|googleapis|mapbox)\.com|/FeatureServer/|/MapServer/|/FeatureServer\b|/MapServer\b)'
)
DATE_RX = re.compile(r'^\d{4}-\d{2}-\d{2}$')
CODE_ID = re.compile(r'^[A-Za-z0-9:._~ -]{1,80}$')


def licence_code(url: str) -> str:
    """Same coding as KPC-Links kpc_master.licence_code / the keeper's public files."""
    sp = urllib.parse.urlsplit(str(url or '').replace('svc:', '', 1).split('|')[0].strip())
    path = re.sub(r'/query/?$', '', urllib.parse.unquote(sp.path or ''), flags=re.I).rstrip('/')
    host = (sp.hostname or '').lower().rstrip('.')
    try:
        port = sp.port
    except ValueError:
        port = -1
    if port not in (None, 443):
        host = f'{host}:{port}'
    return 'sha256:' + hashlib.sha256(f'{host}{path.lower()}'.encode('utf-8')).hexdigest()[:16]


def load_rows(path: Path, text: str | None = None):
    """Return (comment_lines, rows as dicts) or raise ValueError."""
    raw = text if text is not None else path.read_text(encoding='utf-8')
    lines = raw.splitlines()
    body = [x for x in lines if not x.startswith('#')]
    if not body:
        raise ValueError(f'{path}: empty (no header)')
    rdr = csv.DictReader(body)
    if rdr.fieldnames is None:
        raise ValueError(f'{path}: no header')
    got = [c.strip() for c in rdr.fieldnames]
    if got != COLUMNS:
        raise ValueError(f'{path}: header is {got}, want {COLUMNS}')
    rows = list(rdr)
    return [x for x in lines if x.startswith('#')], rows


def problems_in(path: Path, text: str | None = None) -> list[str]:
    """Plain-word problems in one table. Empty = the table is in the coded public form."""
    bad = []
    label = str(path)
    try:
        comments, rows = load_rows(path, text)
    except OSError as e:
        return [f'{label}: unreadable ({e})']
    except ValueError as e:
        return [str(e)]
    blob = (text if text is not None else path.read_text(encoding='utf-8'))
    # Whole-file address scan (comments included): no raw layer address in a public file.
    for i, line in enumerate(blob.splitlines(), 1):
        if ADDRESS_RX.search(line):
            bad.append(f'{label}:{i}: a layer address or host path is not allowed in this public file')
    seen = {}
    for n, r in enumerate(rows, start=2):
        layer = (r.get('layer') or '').strip()
        kid = (r.get('key id') or '').strip()
        pub = (r.get('publish') or '').strip().lower()
        klass = (r.get('licence class') or '').strip()
        date = (r.get('date read') or '').strip()
        where = f'{label} row {n}'
        if not LAYER_CODE.match(layer):
            bad.append(f'{where}: layer is not a sha256: plus 16 hex code')
        if layer in seen:
            bad.append(f'{where}: layer code repeats (also row {seen[layer]})')
        else:
            seen[layer] = n
        if not kid or not CODE_ID.match(kid):
            bad.append(f'{where}: key id missing or not a key id')
        if pub not in PUBLISH:
            bad.append(f"{where}: publish must be yes or no, not {r.get('publish')!r}")
        if not klass:
            bad.append(f'{where}: licence class is empty')
        if date and not DATE_RX.match(date):
            bad.append(f'{where}: date read is not YYYY-MM-DD')
        for col in COLUMNS:
            val = r.get(col) or ''
            if ADDRESS_RX.search(val):
                bad.append(f'{where} {col}: a layer address is not allowed')
    if not rows:
        bad.append(f'{label}: no data rows')
    return bad


def compare(repo_path: Path, release_path: Path) -> list[str]:
    """Problems when both tables exist: format of each, then publish answers that disagree."""
    bad = problems_in(repo_path) + problems_in(release_path)
    if bad:
        return bad
    _, a = load_rows(repo_path)
    _, b = load_rows(release_path)
    am = {(r.get('layer') or '').strip(): r for r in a}
    bm = {(r.get('layer') or '').strip(): r for r in b}
    for code in sorted(set(am) | set(bm)):
        if code not in am:
            bad.append(f'release has {code} ({bm[code].get("key id")}); the repo table does not')
        elif code not in bm:
            bad.append(f'repo has {code} ({am[code].get("key id")}); the release file does not')
        else:
            ap = (am[code].get('publish') or '').strip().lower()
            bp = (bm[code].get('publish') or '').strip().lower()
            if ap != bp:
                bad.append(f'{code} ({am[code].get("key id")}): repo publish={ap} but release publish={bp}')
            ac, bc = (am[code].get('licence class') or '').strip(), (bm[code].get('licence class') or '').strip()
            if ac != bc:
                bad.append(f'{code} ({am[code].get("key id")}): repo licence class={ac!r} but release {bc!r}')
    return bad


def default_repo_table(root: Path) -> Path:
    return root / 'data' / 'outlines' / 'licence-verdicts.csv'


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument('--root', default='.', help='KPC-Links root (default: cwd)')
    p.add_argument('--table', default='', help='repo table path (default: data/outlines/licence-verdicts.csv)')
    p.add_argument('--release', default='', help='optional release-file copy to compare (already on disk)')
    a = p.parse_args(argv)
    root = Path(a.root).resolve()
    table = Path(a.table) if a.table else default_repo_table(root)
    rel = Path(a.release) if a.release else None
    if not table.is_file():
        print(f'::notice title=Licence table::no {table.relative_to(root) if table.is_relative_to(root) else table} yet '
              '(it lands with KPC-Links #313 in the same coded form); format is checked in tests against fixtures')
        if rel and rel.is_file():
            bad = problems_in(rel)
            for b in bad:
                print(f'::error title=Licence table::{b}')
            return 0 if not bad else 1
        return 0
    if rel and rel.is_file():
        bad = compare(table, rel)
    else:
        bad = problems_in(table)
        if a.release:
            print(f'::error title=Licence table::--release {a.release} is not a file')
            return 1
    for b in bad:
        print(f'::error title=Licence table::{b}')
    if not bad:
        print(f'::notice title=Licence table::{table.name} is in the coded public form'
              + (f'; matches {rel.name}' if rel else ''))
    return 0 if not bad else 1


if __name__ == '__main__':
    sys.exit(main())
