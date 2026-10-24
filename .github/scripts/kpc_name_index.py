#!/usr/bin/env python3
"""A name search for every WWFF area and SOTA summit in the world (Opus Oct 24 2026; Brandon: 'make sure searches
include more then ky ...this is world page'). Built from our weekly world copies (data/wwff/<PFX>.json and
data/sota/t/*.json) into data/names/<c>.json, one file per first letter of each word in a name (a-z, '0' for digits):
[[ref, name, lat, lon], ...]. A page searching 'black mountain' loads only the file for 'b' (its first word) and
filters it. POTA names come from POTA's own lookup, so they are not here. Never fails."""
import glob
import json
import pathlib
import re
import sys
import unicodedata

OUT = pathlib.Path('data/names')
SKIP = {'the', 'of', 'and', 'de', 'la', 'le', 'du', 'des', 'di', 'del', 'da', 'von', 'der', 'van', 'mount', 'mt'}


def fold(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()


def main():
    rows = []
    for f in sorted(glob.glob('data/wwff/*.json')):
        try:
            for r in json.load(open(f, encoding='utf-8')):
                if r and len(r) >= 4 and r[2] is not None:
                    rows.append([r[0], r[1], round(float(r[2]), 4), round(float(r[3]), 4)])
        except (OSError, ValueError, TypeError):
            pass
    for f in sorted(glob.glob('data/sota/t/*.json')):
        try:
            for r in json.load(open(f, encoding='utf-8')):
                if r and len(r) >= 6 and r[1] and r[1] != r[0]:
                    rows.append([r[0], r[1], round(float(r[4]), 4), round(float(r[5]), 4)])
        except (OSError, ValueError, TypeError):
            pass
    if len(rows) < 50000:
        print(f'::notice title=Name index::only {len(rows)} names, kept the old files'); return
    by = {}
    for r in rows:
        keys = set()
        for w in re.findall(r'[a-z0-9]+', fold(str(r[1]))):
            if len(w) < 2 or w in SKIP:
                continue
            keys.add('0' if w[0].isdigit() else w[0])
        for k in keys:
            by.setdefault(k, []).append(r)
    OUT.mkdir(parents=True, exist_ok=True)
    for k, L in by.items():
        (OUT / f'{k}.json').write_text(json.dumps(L, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(f'::notice title=Name index::{len(rows)} WWFF + SOTA names in {len(by)} files')


if __name__ == '__main__':
    try:
        main()
    except Exception as e:  # noqa: BLE001
        print(f'::notice title=Name index::stopped early: {e}')
    sys.exit(0)
