# KPC website announcement video: 1920x1080, 30 fps, about 40 s.
import subprocess, sys, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
REPO = '/home/claude/kpc-links/'
S = '/tmp/claude-0/-home-claude/90e24643-b9af-59bf-86a9-9c6206df7c06/scratchpad/web/'
OUT = S + (sys.argv[1] if len(sys.argv) > 1 else 'KPC-Website.mp4')
PREVIEW = len(sys.argv) > 2

GOLD = (240, 201, 107); CREAM = (250, 244, 228); SUB = (196, 190, 176)
SERIF = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc'
SERIFB = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
SANS = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
SANSM = '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'
SANSR = '/usr/share/fonts/truetype/google-fonts/Poppins-Regular.ttf'
def F(p, s): return ImageFont.truetype(p, s)
def load(p):
    im = cv2.imread(p, cv2.IMREAD_COLOR); return cv2.cvtColor(im, cv2.COLOR_BGR2RGB).astype(np.float32)

def kenburns(img, t, z0, z1, cx0, cx1, cy0=.5, cy1=.5):
    h, w = img.shape[:2]; e = t * t * (3 - 2 * t)
    z = z0 + (z1 - z0) * e; cx = cx0 + (cx1 - cx0) * e; cy = cy0 + (cy1 - cy0) * e
    cover = max(W / w, H / h) * z; cw, ch = W / cover, H / cover
    x0 = min(max(cx * w - cw / 2, 0), w - cw); y0 = min(max(cy * h - ch / 2, 0), h - ch)
    M = np.array([[cover, 0, -x0 * cover], [0, cover, -y0 * cover]], np.float32)
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

_cache = {}
def text(s, font, fill, track=0, shadow=True):
    k = (s, font.path, font.size, fill, track, shadow)
    if k in _cache: return _cache[k]
    d0 = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    widths = [d0.textlength(ch, font=font) for ch in s]
    tw = int(sum(widths) + track * (len(s) - 1)) + 40; asc, desc = font.getmetrics(); th = asc + desc + 40
    im = Image.new('RGBA', (tw, th), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 20
    for ch, cw in zip(s, widths): d.text((x, 20), ch, font=font, fill=fill); x += cw + track
    if shadow:
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel('A').filter(ImageFilter.GaussianBlur(9)).point(lambda a: int(a * .75)))
        base = Image.new('RGBA', im.size, (0, 0, 0, 0)); base.alpha_composite(sh, (0, 4)); base.alpha_composite(im); im = base
    arr = np.asarray(im).astype(np.float32); _cache[k] = arr; return arr

def put(frame, arr, x, y, a=1.0, anchor='c'):
    if a <= 0: return
    h, w = arr.shape[:2]; x0 = int(x - w / 2) if anchor == 'c' else int(x) - 20; y0 = int(y - h / 2)
    xa, ya = max(0, x0), max(0, y0); xb, yb = min(W, x0 + w), min(H, y0 + h)
    if xb <= xa or yb <= ya: return
    sub = arr[ya - y0:yb - y0, xa - x0:xb - x0]
    if sub.shape[2] == 4: al = sub[..., 3:4] / 255 * a; rgb = sub[..., :3]
    else: al = a; rgb = sub
    frame[ya:yb, xa:xb] = frame[ya:yb, xa:xb] * (1 - al) + rgb * al

def ease(t): t = min(max(t, 0), 1); return 1 - (1 - t) ** 3
def smooth(t): t = min(max(t, 0), 1); return t * t * (3 - 2 * t)
def inout(t, a, b, fi=.6, fo=.5): return min(ease((t - a) / fi), 1 - ease((t - (b - fo)) / fo)) if a <= t <= b else 0
def rule(frame, x0, y, w, a):
    if a <= 0 or w <= 0: return
    frame[y:y + 2, int(x0):int(x0 + w)] = frame[y:y + 2, int(x0):int(x0 + w)] * (1 - a) + np.array(GOLD, np.float32) * a

def rrect_mask(w, h, r):
    m = np.zeros((h, w), np.uint8); cv2.rectangle(m, (r, 0), (w - r, h), 255, -1); cv2.rectangle(m, (0, r), (w, h - r), 255, -1)
    for cx, cy in [(r, r), (w - r - 1, r), (r, h - r - 1), (w - r - 1, h - r - 1)]: cv2.circle(m, (cx, cy), r, 255, -1, cv2.LINE_AA)
    return (m.astype(np.float32) / 255)[..., None]

BG = load(REPO + 'bg-lodge.jpg'); LAKE = load(REPO + 'hero-lake-camp.jpg')
LOGO = np.asarray(Image.open(REPO + 'KPC-logo.png').convert('RGBA').resize((300, 300), Image.LANCZOS)).astype(np.float32)
LOGO_S = np.asarray(Image.open(REPO + 'KPC-logo.png').convert('RGBA').resize((200, 200), Image.LANCZOS)).astype(np.float32)

# ---------- browser window ----------
BW, BH, BAR = 1180, 740, 44
WIN_MASK = rrect_mask(BW, BH, 16)
def page(name):
    im = load(S + name + '-d.png'); sc = BW / im.shape[1]
    return cv2.resize(im, (BW, int(im.shape[0] * sc)), interpolation=cv2.INTER_AREA)
def browser(frame, pg, url, scroll, x0, y0, a):
    if a <= 0: return
    win = np.zeros((BH, BW, 3), np.float32); win[:] = (24, 27, 33)
    win[:BAR] = (36, 40, 48)
    for i, c in enumerate([(237, 106, 94), (245, 191, 79), (98, 197, 84)]): cv2.circle(win, (26 + i * 22, BAR // 2), 7, c, -1, cv2.LINE_AA)
    cv2.rectangle(win, (110, 9), (BW - 30, BAR - 9), (20, 22, 27), -1)
    u = text(url, F(SANSR, 18), (200, 204, 212), 0, False); uh, uw = u.shape[:2]
    sub = u[(uh - (BAR - 18)) // 2:(uh - (BAR - 18)) // 2 + (BAR - 18), :min(uw, BW - 170)]
    al = sub[..., 3:4] / 255; win[9:BAR - 9, 120:120 + sub.shape[1]] = win[9:BAR - 9, 120:120 + sub.shape[1]] * (1 - al) + sub[..., :3] * al
    vh = BH - BAR; sy = int(min(scroll, max(0, pg.shape[0] - vh)))
    win[BAR:] = pg[sy:sy + vh] if pg.shape[0] - sy >= vh else np.pad(pg[sy:], ((0, vh - (pg.shape[0] - sy)), (0, 0), (0, 0)), constant_values=24)
    # shadow
    sh = np.zeros((H, W, 1), np.float32); sh[max(0, y0 + 24):min(H, y0 + BH + 24), max(0, x0 + 10):min(W, x0 + BW + 10)] = .6
    sh = cv2.GaussianBlur(sh, (0, 0), 26)[..., None]; frame *= (1 - sh * a)
    m = WIN_MASK * a; ya, yb = max(0, y0), min(H, y0 + BH)
    frame[ya:yb, x0:x0 + BW] = frame[ya:yb, x0:x0 + BW] * (1 - m[ya - y0:yb - y0]) + win[ya - y0:yb - y0] * m[ya - y0:yb - y0]
    # gold hairline
    cv2.rectangle(frame, (x0, y0), (x0 + BW - 1, y0 + BH - 1), tuple(v * a + 0 for v in (150, 120, 60)), 1, cv2.LINE_AA)

def backdrop(t, L, img=None):
    f = kenburns(BG if img is None else img, t / L, 1.05, 1.12, .4, .6)
    f = cv2.GaussianBlur(f, (0, 0), 7) * .32
    return f

PAGES = [  # name, url, label, title line 1, line 2, detail, max scroll (px of scaled page)
    ('index', '', 'START HERE', 'Get outside.', 'Get on the air.', 'Who we are, what we do and how to join in.', 700),
    ('campoutHOLD', 'campout.html', '2027 KYPOTA CAMPOUT', 'Everything for', 'the campout', 'Countdown, group tent sites, local guides and the flyer.', 900),
    ('eventsHOLD', 'events.html', 'EVENTS', 'Mark your', 'calendar', 'Club events, Support Your Parks weekends and Kentucky contests.', 900),
    ('kentucky-parks', 'kentucky-parks.html', 'KENTUCKY PARKS', 'Kentucky parks,', 'one place', 'Parks, forests and wildlife areas, with maps and park resources.', 800),
    ('kpc-community', 'kpc-community.html', 'COMMUNITY', 'Share your', 'setup', 'Station setups, antenna builds, field tips and activation stories.', 500),
    ('kpc-park-notes', 'kpc-park-notes.html', 'PARK NOTES', 'Tips from folks', 'who’ve been there', 'Parking, where to set up, noise, cell signal. Share yours.', 700),
    ('kpc-campgrounds', 'kpc-campgrounds.html', 'CAMPGROUNDS & CABINS', 'Stay the', 'whole weekend', 'Campgrounds, cabins and lodges inside Kentucky parks.', 700),
    ('kpc-guide-pota', 'kpc-guide-pota.html', 'GUIDES', 'New to it?', 'Start here', 'Plain-language guides for POTA, WWFF and SOTA.', 800),
]
LOADED = {}
def pscene(i):
    name, url, label, l1, l2, det, maxs = PAGES[i]
    left = i % 2 == 0  # caption left, browser right
    def fn(t, L):
        if name not in LOADED: LOADED[name] = page(name)
        f = backdrop(t + i * 3, L + 12)
        bx = 680 if left else 60; by = 170
        slide = 60 * (1 - ease(t / .8)) * (1 if left else -1)
        browser(f, LOADED[name], 'kentuckyportableclub.github.io/KPC-Links/' + url, maxs * smooth((t - 1.5) / (L - 2.0)), int(bx + slide), by, ease(t / .6))
        cx = 90 if left else 1280
        put(f, text(label, F(SANS, 26), GOLD, 8), cx, 400, inout(t, .3, L + 1), 'l')
        rule(f, cx, 438, 120 * ease((t - .5) / .8), inout(t, .5, L + 1))
        put(f, text(l1, F(SERIF, 64), CREAM, 0), cx, 510, inout(t, .5, L + 1, .7), 'l')
        put(f, text(l2, F(SERIF, 64), GOLD, 0), cx, 590, inout(t, .7, L + 1, .7), 'l')
        # detail, wrapped to 2 lines
        words, lines, cur = det.split(), [], ''
        for w_ in words:
            if len(cur + ' ' + w_) > 30 and cur: lines.append(cur); cur = w_
            else: cur = (cur + ' ' + w_).strip()
        lines.append(cur)
        for j, ln in enumerate(lines): put(f, text(ln, F(SANSR, 28), SUB, 0), cx, 680 + j * 44, inout(t, 1.0, L + 1, .7), 'l')
        return f
    return fn

def s_intro(t, L):
    f = kenburns(LAKE, t / L, 1.0, 1.1, .5, .56) * .42
    put(f, LOGO, W / 2, 330 + 20 * (1 - ease(t / 1)), ease((t - .1) / .8))
    put(f, text('KENTUCKY PORTABLE CLUB', F(SANS, 30), GOLD, 10), W / 2, 545, inout(t, .7, L + 1))
    put(f, text('Our website is', F(SERIF, 96), CREAM, 0), W / 2, 660, inout(t, 1.0, L + 1, .8))
    put(f, text('open to everyone.', F(SERIF, 96), GOLD, 0), W / 2, 780, inout(t, 1.4, L + 1, .8))
    return f

PH = [load(S + n + '-m.png') for n in ['index', 'kentucky-parks', 'kpc-park-notes']]
PW_, PH_ = 330, 714; PMASK = rrect_mask(PW_ + 20, PH_ + 20, 44)
def phone(frame, img, x0, y0, a):
    if a <= 0: return
    sc = cv2.resize(img, (PW_, int(img.shape[0] * PW_ / img.shape[1])), interpolation=cv2.INTER_AREA)[:PH_]
    body = np.zeros((PH_ + 20, PW_ + 20, 3), np.float32); body[:] = (14, 15, 18); body[10:10 + sc.shape[0], 10:10 + PW_] = sc
    sh = np.zeros((H, W, 1), np.float32); sh[y0 + 30:y0 + PH_ + 50, x0 + 10:x0 + PW_ + 30] = .65
    sh = cv2.GaussianBlur(sh, (0, 0), 24)[..., None]; frame *= (1 - sh * a)
    m = PMASK * a; frame[y0:y0 + PH_ + 20, x0:x0 + PW_ + 20] = frame[y0:y0 + PH_ + 20, x0:x0 + PW_ + 20] * (1 - m) + body * m
def s_phone(t, L):
    f = backdrop(t, L)
    put(f, text('ON YOUR PHONE', F(SANS, 26), GOLD, 8), 90, 400, inout(t, .3, L + 1), 'l')
    put(f, text('Made for', F(SERIF, 64), CREAM, 0), 90, 490, inout(t, .5, L + 1, .7), 'l')
    put(f, text('the field', F(SERIF, 64), GOLD, 0), 90, 570, inout(t, .7, L + 1, .7), 'l')
    for j, ln in enumerate(['Every page works on a phone,', 'right from the picnic table.']):
        put(f, text(ln, F(SANSR, 28), SUB, 0), 90, 660 + j * 44, inout(t, 1.0, L + 1, .7), 'l')
    for k, img in enumerate(PH):
        a = ease((t - .3 - k * .35) / .7); phone(f, img, 720 + k * 390, int(170 + 40 * (1 - a) - (k == 1) * 20), a)
    return f

def s_end(t, L):
    f = kenburns(LAKE, t / L, 1.12, 1.2, .6, .64) * .38
    f = cv2.GaussianBlur(f, (0, 0), 5)
    put(f, LOGO_S, W / 2, 250, ease(t / .8))
    put(f, text('Come take a look.', F(SERIF, 92), CREAM, 0), W / 2, 450, inout(t, .3, L + 1, .8))
    put(f, text('kentuckyportableclub.github.io/KPC-Links', F(SANSM, 46), GOLD, 1), W / 2, 570, inout(t, .7, L + 1, .8))
    put(f, text('Campout  ·  Events  ·  Parks  ·  Park Notes  ·  Guides  ·  Join the club', F(SANSM, 30), CREAM, 2), W / 2, 670, inout(t, 1.1, L + 1, .8))
    put(f, text('Kentucky Portable Club is an independent ham radio club, not part of Parks on the Air®, SOTA or WWFF.', F(SANSR, 22), (190, 186, 176), 0, False), W / 2, 1010, inout(t, 1.5, L + 1))
    return f

SCENES = [(s_intro, 4.6)] + [(pscene(i), 4.0) for i in range(len(PAGES))] + [(s_phone, 4.6), (s_end, 6.5)]
XF = .6
total = sum(L for _, L in SCENES) - XF * (len(SCENES) - 1)
starts = []; acc = 0
for fn, L in SCENES: starts.append(acc); acc += L - XF

def frame_at(T):
    out = None
    for (fn, L), st in zip(SCENES, starts):
        if st <= T < st + L:
            fr = fn(T - st, L); w = 1.0 if T - st >= XF or st == 0 else (T - st) / XF
            out = fr if out is None else out * (1 - w) + fr * w
    if T < .6: out = out * (T / .6)
    if T > total - .8: out = out * max(0, (total - T) / .8)
    return np.clip(out, 0, 255).astype(np.uint8)

if PREVIEW:
    ts = [3.5] + [starts[i + 1] + 2.6 for i in range(len(PAGES))] + [starts[-2] + 3, starts[-1] + 3.5]
    ims = [Image.fromarray(frame_at(T)).resize((640, 360), Image.LANCZOS) for T in ts]
    sheet = Image.new('RGB', (1920, 360 * ((len(ims) + 2) // 3)))
    for i, im in enumerate(ims): sheet.paste(im, ((i % 3) * 640, (i // 3) * 360))
    sheet.save(S + 'sheet2.jpg', quality=82); print(round(total, 1)); sys.exit()

n = int(total * FPS)
p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                      '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-shortest',
                      '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for i in range(n): p.stdin.write(frame_at(i / FPS).tobytes())
p.stdin.close(); p.wait(); print('done', OUT, round(total, 1), 's')
