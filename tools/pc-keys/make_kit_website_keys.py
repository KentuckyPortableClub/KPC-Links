#!/usr/bin/env python3
"""Batch 16 (25 Nov 2026): the website-copy list a PC kit brings (links/.kit-website-keys/), so the PC test can check its saved
website copies (key builder files\\originals) before it builds. Run from the KPC-Links repo root when making a kit:

  python3 tools/pc-keys/make_kit_website_keys.py <out folder> [--ref origin/main] [--copy US-MN.json US-NY.json ...]

Writes <out>/sha256.json = {'ref': <commit>, 'files': {name: sha256}} for every website key file at that commit (data/us-key/US-*.json,
data/ca-key/CA-*.json, data/ky-answer-key.json) and the layer prefix table (layers.json, always copied), and a copy of each file named after --copy (the states whose PC copy is wrong or
missing). Reads git only; writes only into <out>."""
import hashlib, json, pathlib, subprocess, sys


def main(argv):
    if not argv: sys.exit(__doc__)
    out = pathlib.Path(argv[0]); ref = 'origin/main'; copy = []
    rest = argv[1:]
    if '--ref' in rest: ref = rest[rest.index('--ref') + 1]
    if '--copy' in rest: copy = [x for x in rest[rest.index('--copy') + 1:] if not x.startswith('--')]
    commit = subprocess.check_output(['git', 'rev-parse', ref], text=True).strip()
    names = subprocess.check_output(['git', 'ls-tree', '--name-only', commit, 'data/us-key/', 'data/ca-key/', 'data/ky-answer-key.json'], text=True).split()
    files = {}
    out.mkdir(parents=True, exist_ok=True)
    for path in names:
        nm = pathlib.Path(path).name
        if not (nm.startswith(('US-', 'CA-')) and nm.endswith('.json')) and nm != 'ky-answer-key.json': continue
        b = subprocess.check_output(['git', 'show', f'{commit}:{path}'])
        files[nm] = hashlib.sha256(b).hexdigest()
        if nm in copy: (out / nm).write_bytes(b)
    # the layer prefix table (data/us-key/layers.json): a build writes it; every test starts from the website's (batch 16)
    b = subprocess.check_output(['git', 'show', f'{commit}:data/us-key/layers.json'])
    files['layers.json'] = hashlib.sha256(b).hexdigest(); (out / 'layers.json').write_bytes(b)
    (out / 'sha256.json').write_text(json.dumps({'ref': commit, 'files': files}, indent=1, sort_keys=True), encoding='utf-8')
    print(f'{len(files)} website key file(s) listed at {commit[:8]}; copies: {", ".join(c for c in copy if c in files) or "none"}')


if __name__ == '__main__':
    main(sys.argv[1:])
