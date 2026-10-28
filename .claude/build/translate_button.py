"""Adds the 🌐 translate button to every page's header nav (right after the search icon),
bumps kpc-nav.css to the new version, and loads kpc-translate.js in the tail script block.
news.html included (it's the canonical source assemble.py copies the header from for new pages).
Safe to run twice (skipped when a page already has the button).

  python3 .claude/build/translate_button.py            dry run
  python3 .claude/build/translate_button.py --apply    write
"""
import glob, sys

APPLY = '--apply' in sys.argv
MARK = 'nav-translate'
SEARCH_A_VARIANTS = [
    '<a href="find.html" class="nav-search-icon">&#128269;</a>',
    '<a href="find.html" aria-current="page" class="nav-search-icon">&#128269;</a>',
]
TRANS_A = '<a href="#" class="nav-translate" aria-label="Translate this page" title="Translate (opens Google Translate)">\U0001F310</a>'
OLD_CSS = 'kpc-nav.css?v=20261015a'
NEW_CSS = 'kpc-nav.css?v=20261028a'
SEARCH_JS = '<script src="kpc-search.js?v=20261029b" defer></script>'
TRANS_JS = '<script src="kpc-translate.js?v=20261028a" defer></script>'

done, skip, miss = [], [], []
for f in sorted(glob.glob('*.html')):
    s = open(f, encoding='utf-8').read()
    if MARK in s:
        skip.append(f); continue
    hit = next((a for a in SEARCH_A_VARIANTS if a in s), None)
    if not hit or OLD_CSS not in s or SEARCH_JS not in s:
        miss.append(f); continue
    s2 = s.replace(hit, hit + TRANS_A, 1)
    s2 = s2.replace(OLD_CSS, NEW_CSS)
    s2 = s2.replace(SEARCH_JS, TRANS_JS + SEARCH_JS, 1)
    if APPLY:
        open(f, 'w', encoding='utf-8').write(s2)
    done.append(f)

print(f"{'Added' if APPLY else 'Would add'} to {len(done)} pages, skipped {len(skip)} (already had it), "
      f"{len(miss)} missing an expected anchor: {miss}")
if not APPLY:
    print('Re-run with --apply to write.')
