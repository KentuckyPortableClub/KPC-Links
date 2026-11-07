#!/usr/bin/env python3
"""Nov 7: every map dot that used to have no popup/tooltip now says what it is (see out/map-dots.md section 5).
String checks on the line that creates each marker; also that each changed script has the same ?v= on every page that loads it.
Non-interactive markers (sun, route ends, search point) get role=img + aria-label + title instead, so clicks still reach the map."""
import pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ok = True


def check(msg, cond):
    global ok
    ok &= bool(cond)
    print(('PASS ' if cond else 'FAIL ') + msg)


def line_with(fname, needle):
    lines = [l for l in (ROOT / fname).read_text(encoding='utf-8').splitlines() if needle in l and not l.lstrip().startswith(('.', '#', '/'))]
    lines = [l for l in lines if 'L.marker' in l or 'circleMarker' in l or fname == 'kpc-live.html' and '.lv-sunpin{' not in l] or lines
    return lines[0] if lines else ''


# (file, text that finds the marker call, text that must be on that same line)
TIPS = [
    ('kpc-maprep-check.js', "title: 'Dropped pin'", ".bindTooltip('Dropped pin (drag to move)')"),
    ('kpc-in-park.js', "radius: 9, color: '#fff', weight: 3, fillColor: '#1378ff'", ".bindTooltip('You are here')"),
    ('kpc-sota-az.js', "meMark = L.circleMarker(me", ".bindTooltip('You are here')"),
    ('kpc-foxhunt.js', "radius: 3, color: '#7fd39a'", ".bindTooltip('Fox track point')"),
    ('kpc-foxhunt.js', "meMark = L.circleMarker(me", ".bindTooltip('You are here')"),
    ('kpc-overlap-finder.js', "radius: 5, color: '#d55e00'", ".bindTooltip('Measure point')"),
    ('kpc-overlap-finder.js', "radius: 7, color: '#fff', weight: 3, fillColor: '#1e78ff'", ".bindTooltip('You are here')"),
    ('gis-overlays.js', "hereMark=L.circleMarker", ".bindTooltip('You are here')"),
    ('kpc-live.html', 'lv-sunpin', 'aria-label="Sun position"'),
    ('kpc-live.html', 'lv-sunpin', 'title="Sun position"'),
    ('kpc-band-maps.js', 'kb-sun', 'aria-label="Sun position"'),
    ('kpc-planner.js', 'class="rt-end"', "'Route start':'Route end'"),
    ('kpc-us-planner.js', 'class="rt-end"', "'Route start':'Route end'"),
    ('kpc-us-planner.js', 'ctr-us', 'aria-label="Search point"'),
]
for f, find, need in TIPS:
    check(f'{f}: {find[:40]!r} labeled with {need[:40]}', need in line_with(f, find) and line_with(f, find))

# already labeled (the 3 uncertain ones + two the doc listed): make sure they stay labeled
KEEP = [
    ('kpc-live.js', "fillColor:'#1f6fd1'", ".bindTooltip('Your spot')"),
    ('kpc-logger-ft8.js', "className: 'f8-star'", '.bindTooltip('),
    ('kpc-overlap-finder.js', 'border-radius:50% 50% 50% 0', ''),
    ('kpc-radar-plus.js', 'rainMk=L.marker', 'title:label'),
]
for f, find, need in KEEP:
    ln = line_with(f, find)
    if f == 'kpc-overlap-finder.js':  # dropped pin popup is on the next line
        src = (ROOT / f).read_text(encoding='utf-8')
        check(f'{f}: dropped pin still has a popup', re.search(r"border-radius:50% 50% 50% 0.{0,600}?\.bindPopup\(\$\('ovGps'\)", src, re.S))
    else:
        check(f'{f}: already labeled ({need})', ln and need in ln)
src = (ROOT / '.claude/build/access-finder/main-classic.html').read_text(encoding='utf-8')
check('classic Access Finder access markers already have bindPopup', "L.marker([p.lat,p.lon],{icon,bubblingMouseEvents:false}).bindPopup(popup)" in src)

# ?v= must agree on every page (including build sources) that loads a changed script
changed = ['gis-overlays', 'kpc-band-maps', 'kpc-foxhunt', 'kpc-in-park', 'kpc-maprep-check',
           'kpc-overlap-finder', 'kpc-planner', 'kpc-sota-az', 'kpc-us-planner']
pages = [p for p in list(ROOT.glob('*.html')) + list(ROOT.glob('.claude/build/**/*.html'))]
for name in changed:
    vs = {}
    for p in pages:
        for m in re.finditer(r'src="' + re.escape(name) + r'\.js(\?v=[^"]*)?"', p.read_text(encoding='utf-8', errors='replace')):
            vs.setdefault(m.group(1), []).append(p.name)
    check(f'{name}.js loaded with one ?v= on every page: {sorted(vs)} ({sum(len(x) for x in vs.values())} tags)',
          len(vs) == 1 and None not in vs and all(k >= '?v=20261107a' for k in vs))

print('ALL PASS' if ok else 'SOME FAILED')
sys.exit(0 if ok else 1)
