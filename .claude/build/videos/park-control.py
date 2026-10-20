# KPC Park Control how-to video
import sys; sys.path.insert(0, '/tmp/claude-0/-home-claude/90e24643-b9af-59bf-86a9-9c6206df7c06/scratchpad/kit')
from kit import *
D = '/tmp/claude-0/-home-claude/90e24643-b9af-59bf-86a9-9c6206df7c06/scratchpad/live/'
URL = 'kentuckyportableclub.github.io/KPC-Links/kpc-park-control.html'
P = {k: page(D + f'pc-{k}-d.png') for k in ['1-start', '2-map', '3-suggest', '4-park', '5-info', '9-pad']}
RAW4 = load(D + 'pc-4-park-d.png'); OUTL = RAW4[262:900, 117:1325]
RAW9 = load(D + 'pc-9-pad-d.png'); NEAR = RAW9[262:650, 117:1325]
RAW10 = load(D + 'pc-10-trip-d.png'); TOOLS = RAW10[98:545, 945:1325]

def bscene(key, label, l1, l2, det, i, scroll=0):
    left = i % 2 == 0
    def fn(t, L):
        f = backdrop(t + i * 3, L + 12)
        bx = 680 if left else 60
        browser(f, P[key], URL, scroll, int(bx + 60 * (1 - ease(t / .8)) * (1 if left else -1)), 170, ease(t / .6))
        caption(f, t, L, 90 if left else 1280, label, l1, l2, det, size=62)
        return f
    return fn

def intro(t, L):
    f = kenburns(LAKE, t / L, 1.0, 1.1, .5, .56) * .42
    put(f, LOGO_S, W / 2, 290 + 20 * (1 - ease(t / 1)), ease((t - .1) / .8))
    put(f, text('KPC HOW-TO', F(SANS, 30), GOLD, 10), W / 2, 460, inout(t, .6, L + 1))
    put(f, text('Kentucky Park Control', F(SERIF, 112), CREAM, 0), W / 2, 580, inout(t, .9, L + 1, .8))
    put(f, text('Every park, summit and reference on one map.', F(SERIFB, 50), GOLD, 0), W / 2, 705, inout(t, 1.4, L + 1, .8))
    return f

def pan(img, label, l1, l2, det, i, mw=1180, mh=760):
    def fn(t, L):
        f = backdrop(t + i * 3, L + 12)
        panel(f, img, 1260, 540, mw, mh, ease(t / .6), 1 + .05 * smooth(t / L))
        caption(f, t, L, 90, label, l1, l2, det, size=62, width=26)
        return f
    return fn

def tools(t, L):
    f = backdrop(t + 20, L)
    panel(f, TOOLS, 1250, 540, 700, 820, ease(t / .6), 1 + .03 * smooth(t / L))
    caption(f, t, L, 90, 'MADE FOR HUNTERS TOO', 'New to you?', 'Plan the day', 'Type your call to see parks new to you, then send your trip to Google Maps.', size=62, width=28)
    return f

def end(t, L):
    f = cv2.GaussianBlur(kenburns(LAKE, t / L, 1.12, 1.2, .6, .64) * .38, (0, 0), 5)
    put(f, LOGO_S, W / 2, 250, ease(t / .8))
    put(f, text('Find your next park.', F(SERIF, 92), CREAM, 0), W / 2, 450, inout(t, .3, L + 1, .8))
    put(f, text(URL, F(SANSM, 40), GOLD, 1), W / 2, 570, inout(t, .7, L + 1, .8))
    put(f, text('Free to use  ·  Works on your phone  ·  Kentucky Portable Club', F(SANSM, 30), CREAM, 2), W / 2, 670, inout(t, 1.1, L + 1, .8))
    put(f, text('Outlines are guides. Always check the official map. KPC is an independent ham radio club, not part of Parks on the Air®, SOTA or WWFF.', F(SANSR, 22), (190, 186, 176), 0, False), W / 2, 1010, inout(t, 1.5, L + 1))
    return f

SCENES = [(intro, 4.4),
          (bscene('2-map', 'ONE MAP', 'POTA, KFF', 'and SOTA', 'Every Kentucky park, KFF reference and summit. Turn layers on or off.', 0), 4.6),
          (bscene('3-suggest', 'SEARCH', 'Name, number', 'or town', 'Start typing and pick the park from the list.', 1), 4.2),
          (pan(OUTL, 'THE OUTLINE', 'See the real', 'boundary', 'State park land and Army Corps land, each in its own color.', 2), 5.0),
          (bscene('5-info', 'PARKING & ACCESS', 'Know where', 'to park', 'Trailhead and access points, each with one-tap directions.', 3), 4.6),
          (pan(NEAR, 'NEAR ME', 'What’s close', 'to you?', 'Uses your phone’s GPS to list the nearest parks with miles.', 4), 4.8),
          (tools, 5.0), (end, 6.2)]
render(SCENES, D + 'KPC-Park-Control.mp4', preview=D + 'prev_pc.jpg' if len(sys.argv) > 1 else None)
