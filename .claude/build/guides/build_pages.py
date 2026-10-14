"""Rebuild kpc-guide-sota.html, kpc-guide-wwff.html and kpc-guide-pota.html from the sources in .claude/build/guides/src/.
Run from the repo root:  python3 .claude/build/guides/build_pages.py
src/guide-css.html  shared page CSS for both guides (screen + print touches; kpc-guide-print.css is linked after it)
src/sota-body.html, src/wwff-body.html, src/pota-body.html  page bodies. @@DISCLAIM@@ is filled with the disclaimer box copied from kpc-sota.html.
The main file is written to a temp folder and passed to .claude/build/assemble.py (header, menu and footer from news.html).
The page JavaScript lives in kpc-guide-sota.js / kpc-guide-wwff.js / kpc-guide-pota.js (bump ?v= in the body files when it changes)."""
import os, re, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
PAGES = [
    ('sota-body.html', 'kpc-guide-sota.html', 'Kentucky SOTA Field Resource (W4K) | KPC',
     'Every Kentucky SOTA summit (association W4K) on one page: points, elevation, GPS, weather, POTA and KFF parks within 3 miles, nearby summits and regional maps. Search it, or print it as the KPC field guide.'),
    ('wwff-body.html', 'kpc-guide-wwff.html', 'Kentucky WWFF Field Resource (KFF) | KPC',
     'Every Kentucky WWFF (KFF) reference on one page: official maps, websites, POTA matches, entrances, access points, camping, nearby parks and regional maps. Search it, or print it as the KPC field guide.'),
    ('pota-body.html', 'kpc-guide-pota.html', 'Kentucky POTA Field Resource | KPC',
     'Every Kentucky POTA park on one page, numerical or A-Z: official maps, websites, entrances, access points, camping, 2-fers and 3-fers, Wild River corridors, nearby parks and regional maps. Search it, or print it as the KPC field guide.'),
]

def disclaimer():
    html = open(os.path.join(REPO, 'kpc-sota.html'), encoding='utf-8').read()
    m = re.search(r'<aside class="kpc-disclaim".*?</aside>', html, re.S)
    if not m:
        raise SystemExit('disclaimer box not found in kpc-sota.html')
    return m.group(0)

def main():
    only = sys.argv[1:]
    css = open(os.path.join(HERE, 'src', 'guide-css.html'), encoding='utf-8').read()
    dis = disclaimer()
    tmp = tempfile.mkdtemp(prefix='kpc-guides-')
    for body, out, title, desc in PAGES:
        if only and out not in only:
            continue
        main_html = '@@CSS@@\n' + css + open(os.path.join(HERE, 'src', body), encoding='utf-8').read().replace('@@DISCLAIM@@', dis)
        mf = os.path.join(tmp, out.replace('.html', '-main.html'))
        open(mf, 'w', encoding='utf-8').write(main_html)
        subprocess.run([sys.executable, os.path.join(REPO, '.claude', 'build', 'assemble.py'), mf, out, title, desc], cwd=REPO, check=True)

if __name__ == '__main__':
    main()
