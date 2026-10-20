# KPC Trip Planner how-to video
import sys; sys.path.insert(0, '/tmp/claude-0/-home-claude/90e24643-b9af-59bf-86a9-9c6206df7c06/scratchpad/kit')
from kit import *
D = '/tmp/claude-0/-home-claude/90e24643-b9af-59bf-86a9-9c6206df7c06/scratchpad/live/'
URL = 'kentuckyportableclub.github.io/KPC-Links/kpc-planner.html'
P = {k: page(D + f'tp-{k}-d.png') for k in ['1-start', '2-town', '8-route']}
R5 = load(D + 'tp-5-trip-d.png'); MAP = R5[170:808, 142:766]; LIST = R5[505:900, 820:1306]; TOOLS = R5[148:305, 808:1320]
R9 = load(D + 'tp-9-routemap-d.png'); RMAP = R9[131:770, 142:766]; RLIST = R9[467:900, 820:1306]

def bscene(key, label, l1, l2, det, i, scroll=0):
    left = i % 2 == 0
    def fn(t, L):
        f = backdrop(t + i * 3, L + 12)
        bx = 680 if left else 60
        browser(f, P[key], URL, scroll, int(bx + 60 * (1 - ease(t / .8)) * (1 if left else -1)), 170, ease(t / .6))
        caption(f, t, L, 90 if left else 1280, label, l1, l2, det, size=62)
        return f
    return fn

def two(a, b, label, l1, l2, det, i):
    def fn(t, L):
        f = backdrop(t + i * 3, L + 12)
        panel(f, a, 1010, 540, 620, 640, ease(t / .6), 1 + .04 * smooth(t / L))
        k = ease((t - .7) / .7); panel(f, b, 1590, 560 + 30 * (1 - k), 470, 600, k)
        caption(f, t, L, 90, label, l1, l2, det, size=60, width=24)
        return f
    return fn

def intro(t, L):
    f = kenburns(LAKE, t / L, 1.0, 1.1, .5, .56) * .42
    put(f, LOGO_S, W / 2, 290 + 20 * (1 - ease(t / 1)), ease((t - .1) / .8))
    put(f, text('KPC HOW-TO', F(SANS, 30), GOLD, 10), W / 2, 460, inout(t, .6, L + 1))
    put(f, text('KPC Trip Planner', F(SERIF, 120), CREAM, 0), W / 2, 580, inout(t, .9, L + 1, .8))
    put(f, text('Plan a radio trip in a few taps.', F(SERIFB, 54), GOLD, 0), W / 2, 705, inout(t, 1.4, L + 1, .8))
    return f

def tools(t, L):
    f = backdrop(t + 20, L)
    panel(f, TOOLS, 1250, 540, 1000, 500, ease(t / .6), 1 + .03 * smooth(t / L))
    caption(f, t, L, 90, 'TAKE IT WITH YOU', 'Send it to', 'Google Maps', 'Share the trip, get a GPX file, or save it for places with no signal.', size=62, width=26)
    return f

def end(t, L):
    f = cv2.GaussianBlur(kenburns(LAKE, t / L, 1.12, 1.2, .6, .64) * .38, (0, 0), 5)
    put(f, LOGO_S, W / 2, 250, ease(t / .8))
    put(f, text('Plan your next radio trip.', F(SERIF, 88), CREAM, 0), W / 2, 450, inout(t, .3, L + 1, .8))
    put(f, text('KPC Trip Planner  ·  for club members', F(SANSM, 40), GOLD, 1), W / 2, 570, inout(t, .7, L + 1, .8))
    put(f, text('Join at kentuckyportableclub.github.io/KPC-Links', F(SANSM, 32), CREAM, 1), W / 2, 660, inout(t, 1.1, L + 1, .8))
    put(f, text('Maps are guides. Always check the official map. KPC is an independent ham radio club, not part of Parks on the Air®, SOTA or WWFF.', F(SANSR, 22), (190, 186, 176), 0, False), W / 2, 1010, inout(t, 1.5, L + 1))
    return f

SCENES = [(intro, 4.4),
          (bscene('1-start', 'START HERE', 'Pick a start,', 'pick a distance', 'A town, a park or your GPS. Then how far you want to drive.', 0), 4.6),
          (bscene('2-town', 'FROM A TOWN', 'Type where', 'you’ll start', 'Every POTA park, SOTA summit and KFF reference in range shows up.', 1, 260), 4.6),
          (two(MAP, LIST, 'SEE WHAT’S CLOSE', 'Parks, summits', 'and 2-fers', 'Distances in miles. Possible 2-fers flagged in gold.', 2), 5.2),
          (two(RMAP, RLIST, 'ALONG A ROUTE', 'Driving', 'somewhere?', 'Louisville to Lexington: parks along the way with the mile marker for each.', 4), 5.4),
          (tools, 4.8), (end, 6.2)]
render(SCENES, D + 'KPC-Trip-Planner.mp4', preview=D + 'prev_tp.jpg' if len(sys.argv) > 1 else None)
