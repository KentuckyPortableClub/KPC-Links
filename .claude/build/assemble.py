"""Build a KPC page from news.html's head/nav/footer plus a main-content file.
usage (from the repo root): python3 .claude/build/assemble.py <main.html> <out.html> "<title>" "<description>"
The main file may use @@CSS@@ (page-css.html), @@COMPARE@@ (compare.html, the POTA/SOTA/WWFF table),
@@HEADER@@ and @@FOOTER@@. Write main files somewhere outside the repo (a scratch folder)."""
import sys, os
here = os.path.dirname(os.path.abspath(__file__))
repo = os.path.abspath(os.path.join(here, '..', '..')) + '/'
mainf, out, title, desc = sys.argv[1:5]
L = open(repo + 'news.html', encoding='utf-8').read().split('\n')
head = '\n'.join(L[:105]); nav_css = '\n'.join(L[120:122])
hs = next(i for i,l in enumerate(L) if l.lstrip().startswith('<header'))
he = next(i for i,l in enumerate(L) if i>hs and l.rstrip().endswith('</header>'))
header = '\n'.join(L[hs:he+1]).replace(' aria-current="page"', '')
footer = '\n'.join(L[next(i for i,l in enumerate(L) if l.startswith('<footer')):])
assert header.startswith('<header') and header.rstrip().endswith('</header>')
t = title.replace('&', '&amp;')
for a, b in [('<title>News &amp; Field Tips | KPC</title>', f'<title>{t}</title>'),
             ('content="News &amp; Field Tips | KPC"', f'content="{t}"'),
             ('news.html"', out + '"')]:
    assert a in head, a
    head = head.replace(a, b)
d = "Kentucky Portable Club news, activation reports and field tips — coming soon. Read the KPC guides available now."
assert head.count(d) == 2
head = head.replace(d, desc.replace('"', '&quot;'))
main = open(mainf, encoding='utf-8').read()
foot_html = footer.split('<script src="kpc-search.js')[0].rstrip()
tail = '<script src="kpc-search.js' + footer.split('<script src="kpc-search.js', 1)[1]
tail_scripts = tail.rsplit('</body></html>', 1)[0]
main = main.replace('@@CSS@@', open(os.path.join(here,'page-css.html'),encoding='utf-8').read()).replace('@@COMPARE@@', open(os.path.join(here,'compare.html'),encoding='utf-8').read())
main = main.replace('@@HEADER@@', header).replace('@@FOOTER@@', foot_html)
open(repo + out, 'w', encoding='utf-8').write(head + '\n' + nav_css + '\n' + main.rstrip() + '\n' + tail_scripts.rstrip() + '\n</body></html>\n')
print('wrote', out)
