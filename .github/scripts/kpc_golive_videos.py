"""Go-live step for the Videos page (Brandon Oct 20: make it public at 5 PM Oct 21 with the go-live).
Adds videos.html to PUBLIC in kpc-gate.js, removes its noindex line, and bumps kpc-gate.js?v= on every page.
Does NOT add a Videos menu link (that waits for N4KPC). Safe to run twice."""
import glob, re
g = open('kpc-gate.js', encoding='utf-8').read()
if "'videos.html'" in g.split('var PUBLIC', 1)[1].split(']', 1)[0]:
    print('videos.html already public'); raise SystemExit
g = g.replace("var PUBLIC = ['index.html',", "var PUBLIC = ['index.html', 'videos.html',", 1)
assert "'videos.html'" in g
open('kpc-gate.js', 'w', encoding='utf-8').write(g)
v = open('videos.html', encoding='utf-8').read()
v = re.sub(r'\s*<meta name="robots" content="noindex,nofollow">', '', v, count=1)
open('videos.html', 'w', encoding='utf-8').write(v)
n = 0
for f in glob.glob('*.html'):
    t = open(f, encoding='utf-8').read()
    u = re.sub(r'kpc-gate\.js\?v=[0-9a-z]+', 'kpc-gate.js?v=20261021v', t)
    if u != t: open(f, 'w', encoding='utf-8').write(u); n += 1
print(f'Videos page public; gate version bumped on {n} pages')
