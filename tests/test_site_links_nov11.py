#!/usr/bin/env python3
"""Site link check (Nov 11 2026, site review package F). Offline, no network: reads the repo's own files only.

Every same-site reference in the PUBLIC root pages (*.html, *.js, *.css at the repo root) must point at a file that is in
this tree, with the exact letter case (GitHub Pages is case-sensitive):
  - HTML: href= / src= / srcset= / poster= / action= / <link href> / <script src> (?v=... cache tags included: the file must exist)
  - JS:   fetch('...'), new Worker('...'), importScripts('...'), serviceWorker.register('...'), s.src = '...', a.href = '...',
          location.href = '...', and plain 'name.html' / 'name.js' / 'name.css' string literals
  - CSS:  url(...)
  - the site search index (kpc-search.js TOOLS) and the service-worker list (kpc-offline.js FILES)
Also reported (not failed): #anchors to an id that the target page does not have, and pages nothing links to (orphans).

Paths read through KPC.dataUrl(...) may live in the KPC-Data repo (it is tried first), so they are listed, not failed.
Paths under data/ that the bots write at run time are not failed either when the page reads them through KPC.dataUrl.

ALLOW below = references this check reports but that cannot be fixed in a page patch (another package's file, or a file a bot
writes). Each entry: 'page|target'. An ALLOW entry that is no longer needed fails the test (so the list cannot rot).

  python3 tests/test_site_links_nov11.py            PASS / FAIL lines, exit 1 on any FAIL
  python3 tests/test_site_links_nov11.py --list     also print every warning (anchors, orphans, dataUrl paths)
"""
import os, re, sys
from urllib.parse import unquote

ROOT = os.environ.get('LINKS') or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LIST = '--list' in sys.argv

ALLOW = {
    # filled in from the Nov 11 review: see out/site/F/REPORT.md
}

EXT = re.compile(r'^(?:[a-z][a-z0-9+.-]*:|//|#|\{|\$)', re.I)
FILEISH = re.compile(r'^[\w./%-]+\.(?:html?|js|mjs|css|json|geojson|png|jpe?g|gif|svg|webp|ico|pdf|vcf|txt|xml|webmanifest|mp3|mp4|wav|gz|csv|kml|gpx)$', re.I)


def rd(p):
    with open(os.path.join(ROOT, p), encoding='utf-8', errors='replace') as fh: return fh.read()


def tree():
    out = set()
    for dp, dn, fn in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in ('.git', 'node_modules')]
        for f in fn:
            out.add(os.path.relpath(os.path.join(dp, f), ROOT).replace(os.sep, '/'))
    return out


def clean(ref):
    ref = ref.strip()
    if not ref or EXT.match(ref) or '${' in ref or "'+" in ref or '"+' in ref or '+' in ref.split('?')[0]: return None
    if re.match(r'^(mailto|tel|sms|javascript|data|blob|about):', ref, re.I): return None
    path, _, frag = ref.partition('#')
    path = path.split('?')[0]
    if not path: return None
    if path.startswith('/KPC-Links/'): path = path[len('/KPC-Links/'):]
    elif path.startswith('/'): return None    # an absolute path outside this site (another repo on the same host)
    if path.startswith('./'): path = path[2:]
    path = unquote(path)
    if path.endswith('/'): path += 'index.html'
    return path, frag


def norm(p):
    parts = []
    for s in p.split('/'):
        if s == '..':
            if parts: parts.pop()
            else: return None
        elif s and s != '.': parts.append(s)
    return '/'.join(parts)


def refs_html(txt):
    for m in re.finditer(r'''\b(href|src|poster|action|data-src)\s*=\s*(["'])(.*?)\2''', txt, re.I | re.S):
        yield m.group(3), m.start(), 'html-' + m.group(1).lower()
    for m in re.finditer(r'''\bsrcset\s*=\s*(["'])(.*?)\1''', txt, re.I | re.S):
        for part in m.group(2).split(','):
            u = part.strip().split(' ')[0]
            if u: yield u, m.start(), 'html-srcset'


JS_CALLS = re.compile(r'''(?:\bfetch|\bnew\s+Worker|\bimportScripts|\.register|\bnew\s+URL)\s*\(\s*(['"`])([^'"`$]+?)\1''')
JS_ASSIGN = re.compile(r'''\.(?:src|href)\s*=\s*(['"`])([^'"`$]+?)\1''')
JS_LIT = re.compile(r'''(['"`])([\w./-]+\.(?:html|js|css))(?:[?#][^'"`]*)?\1''')
DATAURL = re.compile(r'''dataUrl\s*\(\s*(['"`])([^'"`$]+?)\1''')


def refs_js(txt):
    for rx, kind in ((JS_CALLS, 'js-call'), (JS_ASSIGN, 'js-assign'), (JS_LIT, 'js-literal')):
        for m in rx.finditer(txt):
            yield m.group(2), m.start(), kind


def refs_css(txt):
    txt = re.sub(r'/\*.*?\*/', lambda m: re.sub(r'[^\n]', ' ', m.group(0)), txt, flags=re.S)   # comments hold examples
    for m in re.finditer(r'''url\(\s*(['"]?)([^'")]+)\1\s*\)''', txt):
        yield m.group(2), m.start(), 'css-url'


def strip_comments_js(txt):
    # keep offsets: replace comment bodies with spaces (good enough for /* */ and // at line start)
    txt = re.sub(r'/\*.*?\*/', lambda m: re.sub(r'[^\n]', ' ', m.group(0)), txt, flags=re.S)
    return re.sub(r'(?m)^\s*//.*$', lambda m: ' ' * len(m.group(0)), txt)


def ids_of(txt):
    s = set(re.findall(r'''\b(?:id|name)\s*=\s*["']([^"']+)["']''', txt))
    s |= set(re.findall(r'''\.id\s*=\s*['"]([^'"]+)['"]''', txt))   # ids set by the page's own script
    return s


def scripts_of(txt):
    return re.findall(r'''<script[^>]+src\s*=\s*["']([^"'?#]+)''', txt, re.I)


def main():
    T = tree()
    root_files = sorted(f for f in T if '/' not in f and re.search(r'\.(html?|js|css)$', f))
    html_files = [f for f in root_files if re.search(r'\.html?$', f)]
    missing, anchors, dataurl, linked = [], [], [], set()
    ids = {}
    for f in html_files:
        t = rd(f)
        own = ids_of(t)
        for s in scripts_of(t):          # ids that the page's own scripts create count as the page's ids
            p = norm(s)
            if p in T and p.endswith('.js'):
                own |= ids_of(rd(p))
        ids[f] = own
    for f in root_files:
        t = rd(f)
        if f.endswith('.js'): gen = refs_js(strip_comments_js(t))
        elif f.endswith('.css'): gen = refs_css(t)
        else:
            gen = list(refs_html(t)) + list(refs_css(t))
            for m in re.finditer(r'<script\b[^>]*>(.*?)</script>', t, re.I | re.S):
                gen += [(u, m.start(1) + o, k) for u, o, k in refs_js(strip_comments_js(m.group(1)))]
        for m in DATAURL.finditer(t):
            c = clean(m.group(2))
            if c and norm(c[0]) not in T: dataurl.append((f, c[0]))
        seen = set()
        for ref, off, kind in gen:
            c = clean(ref)
            if not c: continue
            path, frag = c
            if kind == 'js-literal' and '/' not in path and not re.search(r'\.(html|js|css)$', path): continue
            if not FILEISH.match(path): continue
            p = norm(path)
            if p is None: continue
            line = t.count('\n', 0, off) + 1
            ltxt = t.split('\n')[line - 1] if p not in T else ''
            if p not in T and 'dataUrl(' in ltxt: dataurl.append((f, p)); continue        # KPC-Data first, this repo second
            if p not in T and p in ('leaflet.css', 'leaflet.js') and 'unpkg.com/leaflet@' in t: continue   # CDN file names joined to the CDN prefix
            key = (p, frag)
            if key in seen: continue
            seen.add(key)
            if p.endswith('.html'): linked.add(p)
            if p not in T:
                # a data/ path that the page also reads through KPC.dataUrl is served by KPC-Data first
                if p.startswith('data/') and re.search(r'dataUrl', t): dataurl.append((f, p)); continue
                missing.append((f, line, kind, p))
            elif frag and p.endswith('.html') and p in ids and not re.search(r'[=&/]', frag) and frag not in ids[p] and frag != 'top':
                anchors.append((f, line, p, frag))
    # the search index and the offline list: same check, named in the output so a broken entry is easy to find
    srch = rd('kpc-search.js')
    for m in re.finditer(r'\["([\w.-]+\.html)(#[\w-]+)?"\s*,', srch):
        if m.group(1) not in T: missing.append(('kpc-search.js', srch.count('\n', 0, m.start()) + 1, 'search-index', m.group(1)))
        linked.add(m.group(1))
    orphans = sorted(f for f in html_files if f not in linked and f not in ('index.html', '404.html'))

    fails = 0
    allow_used = set()
    for f, line, kind, p in missing:
        k = f + '|' + p
        if k in ALLOW:
            allow_used.add(k); print('PASS allowed (reported): %s:%d %s -> %s (%s)' % (f, line, kind, p, ALLOW[k])); continue
        fails += 1
        print('FAIL missing file: %s:%d %s -> %s' % (f, line, kind, p))
    for k in sorted(set(ALLOW) - allow_used):
        fails += 1; print('FAIL stale allow-list entry (the reference is fixed or gone, remove it): ' + k)
    if not missing: print('PASS every same-site reference in %d root files points at a file in the tree' % len(root_files))
    print('INFO %d missing (%d allowed), %d anchors without a target id, %d orphan pages, %d KPC-Data-first paths'
          % (len(missing), len(allow_used), len(anchors), len(orphans), len(dataurl)))
    if LIST:
        for a in anchors: print('WARN anchor: %s:%d -> %s#%s (no such id)' % a)
        for o in orphans: print('WARN orphan (nothing links to it): ' + o)
        for d in sorted(set(dataurl)): print('INFO KPC-Data-first path (not in this repo): %s -> %s' % d)
    print('SOME FAILED' if fails else 'ALL PASSED')
    return 1 if fails else 0


if __name__ == '__main__':
    sys.exit(main())
