# KPC Kentucky POTA Field Guide video
import sys; sys.path.insert(0, '/tmp/claude-0/-home-claude/90e24643-b9af-59bf-86a9-9c6206df7c06/scratchpad/kit')
from kit import *
G = '/tmp/claude-0/-home-claude/90e24643-b9af-59bf-86a9-9c6206df7c06/scratchpad/guide/'
URL = 'kentuckyportableclub.github.io/KPC-Links/kpc-guide-pota.html'
HERO = page(G + 'hero.png'); FIND = load(G + 'find.png')
TILES = FIND[0:500]; LEGEND = FIND[615:1060]
SEARCH = load(G + 'search.png'); CARD = load(G + 'card.png'); NEAR = load(G + 'nearby.png')[:900]; OFF = load(G + 'official.png')

def intro(t, L):
    f = kenburns(LAKE, t / L, 1.0, 1.1, .5, .56) * .42
    put(f, LOGO_S, W / 2, 300 + 20 * (1 - ease(t / 1)), ease((t - .1) / .8))
    put(f, text('KPC FIELD GUIDE', F(SANS, 30), GOLD, 10), W / 2, 470, inout(t, .6, L + 1))
    put(f, text('Kentucky POTA', F(SERIF, 120), CREAM, 0), W / 2, 590, inout(t, .9, L + 1, .8))
    put(f, text('Every Kentucky park in one guide.', F(SERIFB, 54), GOLD, 0), W / 2, 720, inout(t, 1.4, L + 1, .8))
    return f

def sc_hero(t, L):
    f = backdrop(t, L)
    browser(f, HERO, URL, 0, int(680 + 60 * (1 - ease(t / .8))), 170, ease(t / .6))
    caption(f, t, L, 90, 'START HERE', '195 parks,', 'one page', 'Parks, forests, wildlife areas and trails. Sort by number or A to Z.')
    return f

def sc_tiles(t, L):
    f = backdrop(t + 4, L)
    panel(f, TILES, 1250, 540, 1120, 640, ease(t / .6), 1 + .04 * smooth(t / L))
    caption(f, t, L, 90, 'FIND A PARK', 'Jump by', 'park number', 'Tap a number range and go straight to those parks.', width=26)
    return f

def sc_card(t, L):
    f = backdrop(t + 8, L)
    panel(f, SEARCH, 1250, 250, 900, 120, ease(t / .6))
    a = ease((t - .8) / .7); panel(f, CARD, 1250, 600 + 30 * (1 - a), 1140, 520, a)
    caption(f, t, L, 90, 'EVERY PARK CARD', 'Search, then', 'tap and go', 'Official map, GPS directions, weather, camping and access points.', width=26)
    return f

def sc_legend(t, L):
    f = backdrop(t + 12, L)
    panel(f, LEGEND, 1250, 540, 1120, 700, ease(t / .6), 1 + .03 * smooth(t / L))
    caption(f, t, L, 90, 'HOW TO READ A CARD', 'Know every', 'button', 'A plain key for each link on the card.', width=26)
    return f

def sc_near(t, L):
    f = backdrop(t + 16, L)
    h = NEAR.shape[0]; sc = 1120 / NEAR.shape[1]; vis = int(640 / sc)
    y = int((h - vis) * smooth((t - 1) / (L - 1.6)))
    panel(f, NEAR[y:y + vis], 1250, 540, 1120, 640, ease(t / .6))
    caption(f, t, L, 90, 'NEARBY PARKS', 'What’s close', 'by?', 'Each park’s nearest neighbor and every park within 25 miles.', width=26)
    return f

def sc_off(t, L):
    f = backdrop(t + 20, L)
    panel(f, OFF, 1250, 540, 1140, 400, ease(t / .6))
    caption(f, t, L, 90, 'BEFORE YOU GO', 'Official map', 'first', 'Check the agency map for the boundary. Your activation is your call.', width=26)
    return f

def end(t, L):
    f = cv2.GaussianBlur(kenburns(LAKE, t / L, 1.12, 1.2, .6, .64) * .38, (0, 0), 5)
    put(f, LOGO_S, W / 2, 250, ease(t / .8))
    put(f, text('Plan your next park.', F(SERIF, 92), CREAM, 0), W / 2, 450, inout(t, .3, L + 1, .8))
    put(f, text(URL, F(SANSM, 40), GOLD, 1), W / 2, 570, inout(t, .7, L + 1, .8))
    put(f, text('Free to use  ·  Works on your phone  ·  Kentucky Portable Club', F(SANSM, 30), CREAM, 2), W / 2, 670, inout(t, 1.1, L + 1, .8))
    put(f, text('Kentucky Portable Club is an independent ham radio club, not part of Parks on the Air®, SOTA or WWFF.', F(SANSR, 22), (190, 186, 176), 0, False), W / 2, 1010, inout(t, 1.5, L + 1))
    return f

SCENES = [(intro, 4.4), (sc_hero, 4.4), (sc_tiles, 4.2), (sc_card, 5.0), (sc_legend, 4.2), (sc_near, 4.8), (sc_off, 4.6), (end, 6.0)]
render(SCENES, G + 'KPC-Kentucky-POTA-Guide.mp4', preview=G + 'prev.jpg' if len(sys.argv) > 1 else None, song=SONG)
