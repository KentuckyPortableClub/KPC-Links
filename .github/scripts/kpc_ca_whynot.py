#!/usr/bin/env python3
"""R-GC8 / R-G10 for CANADA (chat 2, Oct 30 2026 9:55 PM; HQ audit + Rule Sheet G Canada): a 'why not' tag for every Canada park with
NO outline in the Canada key, the way data/us-key/why-not.json does it for the US. Run after each Canada key build (kpc-ca-key.yml).
Tags: no-layer / picture-map-only / private / name-mismatch / needs-parcel / pin-doubt.
  - a person's word in the province's Fable file wins (a row naming the park with 'picture-map-only', 'private', 'needs-parcel', …)
  - the key held a same-place record for a check ('c')                 -> name-mismatch
  - the pin sits inside a bigger area with another name ('a')           -> needs-parcel   (R-G7: the park is part of a bigger area)
  - a site with no land of its own (historic site, heritage site, lighthouse, campground, recreation site, trail) -> no-layer
  - everything else                                                    -> no-layer
Writes data/ca-key/why-not.json {about, counts, parks: {ref: {st, tag, why}}}. No network. Exit 0 always.
"""
import collections, glob, json, pathlib, re, sys

TAGS = ('picture-map-only', 'private', 'needs-parcel', 'name-mismatch', 'pin-doubt', 'no-layer')


def main():
    book = {}
    for f in glob.glob('.claude/build/research/fable/CA-*.md'):
        for line in open(f, encoding='utf-8'):
            for ref in re.findall(r'\bCA-\d{4}\b', line):
                t = next((t for t in TAGS if re.search(r'\b' + t + r'\b', line, re.I)), None)
                if t: book[ref] = t
    out, cnt = {}, collections.Counter()
    for f in sorted(glob.glob('data/ca-key/CA-??.json')):
        st = pathlib.Path(f).stem[3:]
        for ref, p in ((json.load(open(f, encoding='utf-8')) or {}).get('parks') or {}).items():
            if not isinstance(p, dict) or p.get('m'): continue
            if ref in book: tag, why = book[ref], "the province's Fable file says so"
            elif p.get('c'): tag, why = 'name-mismatch', f"a record held for a person's check: {str(p['c'][0][1])[:60]}"
            elif p.get('a'): tag, why = 'needs-parcel', f"the pin is inside a bigger area: {str(p['a'][0][1])[:60]}"
            else: tag, why = 'no-layer', f"no official record found ({p.get('t') or 'park'})"
            out[ref] = {'st': st, 'tag': tag, 'why': why}; cnt[tag] += 1
    doc = {'about': "R-GC8 'why not' tag for every Canada park with NO outline in the current Canada key (kpc_ca_whynot.py, after each "
                    "Canada key build). Same tags as the US file: no-layer / picture-map-only / private / name-mismatch / needs-parcel / pin-doubt.",
           'counts': dict(cnt), 'parks': out}
    json.dump(doc, open('data/ca-key/why-not.json', 'w', encoding='utf-8'), indent=1, ensure_ascii=False)
    print(f"::notice title=Canada why-not::{len(out)} parks with no outline tagged: {dict(cnt)}")


if __name__ == '__main__':
    try: main()
    except Exception as e: print(f'::notice title=Canada why-not::stopped: {str(e)[:200]}')  # noqa: BLE001
    sys.exit(0)
