# KPC 2nd Annual Campout announcement video: 1920x1080, 30 fps, about 34 s.
import subprocess, sys, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
REPO = '/home/claude/kpc-links/'
S = '/tmp/claude-0/-home-claude/90e24643-b9af-59bf-86a9-9c6206df7c06/scratchpad/camp/'
OUT = S + (sys.argv[1] if len(sys.argv) > 1 else 'KPC-2027-Campout.mp4')
PREVIEW = len(sys.argv) > 2  # write still frames only

GOLD = (240, 201, 107); GOLD2 = (213, 166, 58); CREAM = (250, 244, 228); GREEN = (16, 52, 38)
SERIF = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Black.ttc'
SERIFB = '/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc'
SCRIPT = '/usr/share/texmf/fonts/opentype/public/tex-gyre/texgyrechorus-mediumitalic.otf'
SANS = '/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf'
SANSM = '/usr/share/fonts/truetype/google-fonts/Poppins-Medium.ttf'
def F(p, s): return ImageFont.truetype(p, s)

def load(p):
    im = cv2.imread(p, cv2.IMREAD_COLOR); return cv2.cvtColor(im, cv2.COLOR_BGR2RGB).astype(np.float32)
LAKE = load(REPO + 'hero-lake-camp.jpg'); CAMP = load(REPO + 'campout.png'); CREW = load(REPO + 'hero-campfire-crew.jpg')
SITE = load(REPO + 'hero-campsite.jpg'); FLY = load(S + 'flyerhi-1.png')
LOGO = Image.open(REPO + 'KPC-logo.png').convert('RGBA')

def kenburns(img, t, z0, z1, cx0, cx1, cy0=.5, cy1=.5):
    """t 0..1: zoom from z0 to z1 (1 = cover), centre drifts."""
    h, w = img.shape[:2]; e = t * t * (3 - 2 * t)
    z = z0 + (z1 - z0) * e; cx = cx0 + (cx1 - cx0) * e; cy = cy0 + (cy1 - cy0) * e
    cover = max(W / w, H / h) * z
    cw, ch = W / cover, H / cover
    x0 = min(max(cx * w - cw / 2, 0), w - cw); y0 = min(max(cy * h - ch / 2, 0), h - ch)
    M = np.array([[cover, 0, -x0 * cover], [0, cover, -y0 * cover]], np.float32)
    return cv2.warpAffine(img, M, (W, H), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)

def shade(img, left=.0, bottom=.0, all_=.0):
    g = np.ones((H, W, 1), np.float32)
    if left: g *= (1 - left * np.clip(1 - np.linspace(0, 1, W) / .75, 0, 1) ** 1.4)[None, :, None]
    if bottom: g *= (1 - bottom * np.clip((np.linspace(0, 1, H) - .35) / .65, 0, 1) ** 1.3)[:, None, None]
    return img * g * (1 - all_)

_cache = {}
def text(s, font, fill, track=0, shadow=True, stroke=0):
    k = (s, font.path, font.size, fill, track, shadow, stroke)
    if k in _cache: return _cache[k]
    d0 = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
    widths = [d0.textlength(ch, font=font) for ch in s]
    tw = int(sum(widths) + track * (len(s) - 1)) + 40; asc, desc = font.getmetrics(); th = asc + desc + 40
    im = Image.new('RGBA', (tw, th), (0, 0, 0, 0)); d = ImageDraw.Draw(im); x = 20
    for ch, cw in zip(s, widths):
        d.text((x, 20), ch, font=font, fill=fill, stroke_width=stroke, stroke_fill=(20, 14, 6)); x += cw + track
    if shadow:
        sh = Image.new('RGBA', im.size, (0, 0, 0, 0)); sh.putalpha(im.getchannel('A').filter(ImageFilter.GaussianBlur(9)).point(lambda a: int(a * .75)))
        base = Image.new('RGBA', im.size, (0, 0, 0, 0)); base.alpha_composite(sh, (0, 4)); base.alpha_composite(im); im = base
    arr = np.asarray(im).astype(np.float32); _cache[k] = arr; return arr

def put(frame, arr, x, y, a=1.0, anchor='c'):
    """composite RGBA arr; x is centre (anchor c) or left (l); y = centre line."""
    if a <= 0: return
    h, w = arr.shape[:2]; x0 = int(x - w / 2) if anchor == 'c' else int(x) - 20; y0 = int(y - h / 2)
    xa, ya = max(0, x0), max(0, y0); xb, yb = min(W, x0 + w), min(H, y0 + h)
    if xb <= xa or yb <= ya: return
    sub = arr[ya - y0:yb - y0, xa - x0:xb - x0]; al = sub[..., 3:4] / 255 * a
    frame[ya:yb, xa:xb] = frame[ya:yb, xa:xb] * (1 - al) + sub[..., :3] * al

def ease(t): t = min(max(t, 0), 1); return 1 - (1 - t) ** 3
def inout(t, a, b, fi=.6, fo=.5):
    """alpha for an element shown from a to b (seconds, local)"""
    return min(ease((t - a) / fi), 1 - ease((t - (b - fo)) / fo)) if a <= t <= b else 0

def rule(frame, cx, y, w, a, col=GOLD):
    if a <= 0: return
    x0, x1 = int(cx - w / 2), int(cx + w / 2)
    frame[y:y + 2, x0:x1] = frame[y:y + 2, x0:x1] * (1 - a) + np.array(col, np.float32) * a

# ---------- scenes: (length s, function(frame-time t) -> frame) ----------
def s1(t, L):  # opener: lake at sunrise
    f = shade(kenburns(LAKE, t / L, 1.0, 1.12, .55, .62, .45, .5), bottom=.55, all_=.08)
    a = inout(t, .4, L + 1, .9)
    put(f, text('KENTUCKY  ·  OUTDOORS  ·  RADIO', F(SANS, 34), GOLD, 10), W / 2, 360, a)
    rule(f, W / 2, 400, int(620 * ease((t - .6) / 1.2)), a)
    put(f, text('2nd Annual', F(SCRIPT, 190), GOLD, 0), W / 2, 540 + 30 * (1 - ease((t - 1.2) / 1)), inout(t, 1.2, L + 1, 1))
    put(f, text('Kentucky Portable Club', F(SERIFB, 54), CREAM, 2), W / 2, 700, inout(t, 2.2, L + 1, .9))
    return f

def s2(t, L):  # title
    f = shade(kenburns(CAMP, t / L, 1.05, 1.15, .32, .4), left=.0, bottom=.6, all_=.32)
    k, y = text('KPC', F(SERIF, 250), CREAM, 4), text('2027', F(SERIF, 250), GOLD, 4)
    gap = 50; tw = k.shape[1] + y.shape[1] - 80 + gap; x0 = W / 2 - tw / 2
    put(f, k, x0 + (k.shape[1] - 40) / 2 + 20, 455, inout(t, .1, L + 1, .7))
    put(f, y, x0 + k.shape[1] - 40 + gap + (y.shape[1] - 40) / 2 + 20, 455, inout(t, .5, L + 1, .7))
    rule(f, W / 2, 615, int(1000 * ease((t - .9) / 1)), inout(t, .9, L + 1))
    put(f, text('KENTUCKY POTA CAMPOUT', F(SERIFB, 74), CREAM, 8), W / 2, 700, inout(t, 1.1, L + 1, .8))
    return f

def s3(t, L):  # when + where
    f = shade(kenburns(SITE, t / L, 1.0, 1.1, .3, .45), left=.8, all_=.05)
    put(f, text('SAVE THE DATE', F(SANS, 34), GOLD, 10), 150, 330, inout(t, .2, L + 1), 'l')
    put(f, text('September 24–26, 2027', F(SERIF, 112), CREAM, 1), 150, 450, inout(t, .5, L + 1, .8), 'l')
    rule(f, 150 + 380, 535, int(760 * ease((t - .9) / 1)), inout(t, .9, L + 1))
    put(f, text('Taylorsville Lake State Park', F(SERIFB, 68), CREAM, 1), 150, 620, inout(t, 1.2, L + 1, .8), 'l')
    put(f, text('Taylorsville, Kentucky  ·  US-1271', F(SANSM, 40), GOLD, 3), 150, 705, inout(t, 1.6, L + 1, .8), 'l')
    return f

ACTS = ['Meet & Greet', 'Fox Hunt', 'Park Activations', 'Community Meal', 'Challenges & Games', 'Group Photos']
def s4(t, L):  # what's happening, founders at the campfire
    f = shade(kenburns(CREW, t / L, 1.0, 1.08, .5, .45, .55, .5), bottom=.9, all_=.05)
    put(f, text('A WEEKEND OF', F(SANS, 34), GOLD, 10), W / 2, 800, inout(t, .2, L + 1))
    for row in range(2):
        items = [text(a, F(SERIFB, 58), CREAM, 1) for a in ACTS[row * 3:row * 3 + 3]]
        gap = 110; tw = sum(it.shape[1] - 40 for it in items) + gap * 2; x = W / 2 - tw / 2
        for j, it in enumerate(items):
            i = row * 3 + j; w = it.shape[1] - 40
            put(f, it, x + w / 2 + 20 - 20, 895 + row * 92 + 20 * (1 - ease((t - .6 - i * .45) / .7)), inout(t, .6 + i * .45, L + 1, .7))
            if j < 2: put(f, text('·', F(SERIFB, 58), GOLD, 0), x + w + gap / 2, 895 + row * 92, inout(t, .6 + i * .45, L + 1, .7))
            x += w + gap
    return f

def s5(t, L):  # camping
    f = shade(kenburns(CAMP, t / L, 1.12, 1.2, .82, .74, .6, .55), left=.92, all_=.08)
    put(f, text('CAMP WITH THE CLUB', F(SANS, 34), GOLD, 10), 150, 360, inout(t, .2, L + 1), 'l')
    put(f, text('Group tent sites', F(SERIF, 104), CREAM, 1), 150, 480, inout(t, .5, L + 1, .8), 'l')
    put(f, text('Spots available', F(SERIF, 104), GOLD, 1), 150, 600, inout(t, .9, L + 1, .8), 'l')
    put(f, text('RVs and private sites book with the park.', F(SANSM, 38), CREAM, 1), 150, 720, inout(t, 1.5, L + 1, .8), 'l')
    return f

FLYW = 600; _fly = cv2.resize(FLY, (FLYW, int(FLY.shape[0] * FLYW / FLY.shape[1])), interpolation=cv2.INTER_AREA)
_logo = np.asarray(LOGO.resize((230, 230), Image.LANCZOS)).astype(np.float32)
def s6(t, L):  # end card: flyer + link
    f = shade(kenburns(LAKE, t / L, 1.15, 1.22, .62, .66, .5, .5), all_=.62)
    f = cv2.GaussianBlur(f, (0, 0), 6)
    a = ease(t / .9); fh = _fly.shape[0]; y0 = int((H - fh) / 2 + 40 * (1 - a)); x0 = 1180
    if a > 0:
        sh = np.zeros((H, W, 1), np.float32); sh[max(0, y0 + 14):y0 + fh + 14, x0 + 14:x0 + FLYW + 14] = .5
        sh = cv2.GaussianBlur(sh, (0, 0), 18)[..., None]; f = f * (1 - sh * a)
        yy0, yy1 = max(0, y0), min(H, y0 + fh)
        f[yy0:yy1, x0:x0 + FLYW] = f[yy0:yy1, x0:x0 + FLYW] * (1 - a) + _fly[yy0 - y0:yy1 - y0] * a
    put(f, _logo, 120 + 115, 250, inout(t, .3, L + 1), 'l')
    put(f, text('Come for the campout.', F(SERIF, 76), CREAM, 1), 140, 470, inout(t, .5, L + 1, .8), 'l')
    put(f, text('Stay for the adventure.', F(SERIF, 76), GOLD, 1), 140, 570, inout(t, .9, L + 1, .8), 'l')
    put(f, text('DETAILS, GUIDES & GROUP SITES', F(SANS, 30), GOLD, 8), 140, 690, inout(t, 1.4, L + 1), 'l')
    put(f, text('kentuckyportableclub.github.io/KPC-Links/campout.html', F(SANSM, 34), CREAM, 0), 140, 745, inout(t, 1.4, L + 1), 'l')
    put(f, text('Kentucky Portable Club is an independent ham radio club. Not an official Parks on the Air® event.', F(SANSM, 22), (200, 196, 186), 0, False), 140, 1010, inout(t, 1.8, L + 1), 'l')
    return f

SCENES = [(s1, 5.0), (s2, 4.6), (s3, 5.2), (s4, 6.4), (s5, 4.8), (s6, 8.0)]
XF = .7  # crossfade
total = sum(L for _, L in SCENES) - XF * (len(SCENES) - 1)
starts = []; acc = 0
for fn, L in SCENES: starts.append(acc); acc += L - XF

def frame_at(T):
    out = None
    for (fn, L), st in zip(SCENES, starts):
        if st <= T < st + L:
            fr = fn(T - st, L)
            w = 1.0 if T - st >= XF or st == 0 else (T - st) / XF
            out = fr if out is None else out * (1 - w) + fr * w
    if T < .6: out = out * (T / .6)                # fade in from black
    if T > total - .8: out = out * max(0, (total - T) / .8)  # fade out
    return np.clip(out, 0, 255).astype(np.uint8)

if PREVIEW:
    for i, T in enumerate([3.8, 7.0, 12.0, 17.8, 21.5, 30.0]):
        Image.fromarray(frame_at(T)).resize((960, 540), Image.LANCZOS).save(S + f'prev{i}.jpg', quality=85)
    sys.exit()

n = int(total * FPS)
p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                      '-f', 'lavfi', '-i', 'anullsrc=r=48000:cl=stereo', '-shortest',
                      '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '128k', '-movflags', '+faststart', OUT], stdin=subprocess.PIPE)
for i in range(n):
    p.stdin.write(frame_at(i / FPS).tobytes())
p.stdin.close(); p.wait(); print('done', OUT, round(total, 1), 's')
