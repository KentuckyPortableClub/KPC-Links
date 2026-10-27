"""STORAGE PLAN Stage 2 Step B (chat 1, Oct 27): adds the KPC.dataUrl(path) helper to every existing page's
<head>, right after kpc-gate.js. It tries https://kentuckyportableclub.github.io/KPC-Data/<path> first and
falls back to this site's own copy of the same path (same origin, so the browser never blocks it). news.html
already carries it by hand; assemble.py gives new pages the same copy automatically. Safe to run twice
(skipped when a page already has it, by its id="kpc-data-url").

  python3 .claude/build/data_url_helper.py            dry run
  python3 .claude/build/data_url_helper.py --apply    write
"""
import glob, os, re, sys

APPLY = '--apply' in sys.argv
MARK = 'id="kpc-data-url"'
SNIPPET = ('<script id="kpc-data-url">window.KPC=window.KPC||{};KPC.dataUrl=KPC.dataUrl||function(p,o){'
           "return fetch('https://kentuckyportableclub.github.io/KPC-Data/'+p,o).then(function(r){if(!r.ok)throw 0;return r})"
           ".catch(function(){return fetch(p,o)})};</script>")
GATE = re.compile(r'(<script src="kpc-gate\.js\?v=[^"]+"></script>)')

done, skip, miss = [], [], []
for f in sorted(glob.glob('*.html')):
    if f == 'news.html':
        skip.append(f); continue  # already hand-edited, the canonical copy
    s = open(f, encoding='utf-8').read()
    if MARK in s:
        skip.append(f); continue
    m = GATE.search(s)
    if not m:
        miss.append(f); continue  # no kpc-gate.js (redirect stubs: kentucky-parks.html, members.html)
    s2 = s[:m.end()] + SNIPPET + s[m.end():]
    if APPLY:
        open(f, 'w', encoding='utf-8').write(s2)
    done.append(f)

print(f"{'Added' if APPLY else 'Would add'} to {len(done)} pages, skipped {len(skip)} (already had it or is news.html), "
      f"{len(miss)} had no kpc-gate.js: {miss}")
if not APPLY:
    print('Re-run with --apply to write.')
