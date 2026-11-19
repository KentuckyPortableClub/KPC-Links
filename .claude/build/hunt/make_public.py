#!/usr/bin/env python3
"""Nov 19 2026 (Brandon: 'both pages should be a carbon copy of each other ... just vip has more features digi and the star
bookmark the badges etc'). kpc-hunt.html (VIP) is the ONE master. This writes the public Hunters Lounge (kpc-hunters.html)
from it: only the page's name/description, the members-only lock lines, the menu's lit link and data-public="1" change.
What guests do not get is switched off by data-public="1" (kpc-hunt.css: .mem-only / .pub-only, kpc-hunt.js: PUB).
So: edit kpc-hunt.html only, then run   python3 .claude/build/hunt/make_public.py        (--check = test, writes nothing)
"""
import re, sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
DESC = "Live POTA, WWFF and SOTA spots with the parks you've already worked tucked away, so the new-to-you ones light up."
def one(s, a, b):
    n = s.count(a)
    if n != 1: sys.exit('make_public: expected one %r, found %d' % (a[:60], n))
    return s.replace(a, b)
def build(v):
    v = one(v, '<meta name="robots" content="noindex,nofollow">\n', '')
    v = one(v, '<script src="kpc-vip.js?v=20261018d"></script>\n', '')
    v = one(v, '<title>VIP Hunters Lounge | KPC</title>', '<title>Hunters Lounge | KPC</title>')
    v = one(v, '<meta property="og:title" content="VIP Hunters Lounge | KPC">', '<meta property="og:title" content="Hunters Lounge | KPC">')
    v, n1 = re.subn(r'<meta property="og:description" content="[^"]*">', '<meta property="og:description" content="%s">' % DESC, v)
    v, n2 = re.subn(r'<meta name="description" content="[^"]*">', '<meta name="description" content="%s">' % DESC, v)
    if (n1, n2) != (1, 1): sys.exit('make_public: description lines not found once')
    v = one(v, 'content="https://kentuckyportableclub.github.io/KPC-Links/kpc-hunt.html"', 'content="https://kentuckyportableclub.github.io/KPC-Links/kpc-hunters.html"')
    v = one(v, '<a href="kpc-hunters.html" role="menuitem">', '<a href="kpc-hunters.html" aria-current="page" role="menuitem">')
    v = one(v, '<main id="hl" data-keep-light data-theme="lodge">', '<main id="hl" data-keep-light data-theme="lodge" data-public="1">')
    return v
if __name__ == '__main__':
    vip = open(os.path.join(ROOT, 'kpc-hunt.html'), encoding='utf-8').read()
    out = build(vip); pub = os.path.join(ROOT, 'kpc-hunters.html')
    if '--check' in sys.argv:
        same = open(pub, encoding='utf-8').read() == out
        print('kpc-hunters.html is a carbon copy of kpc-hunt.html' if same else 'DIFFERENT: run make_public.py'); sys.exit(0 if same else 1)
    open(pub, 'w', encoding='utf-8').write(out); print('wrote kpc-hunters.html')
