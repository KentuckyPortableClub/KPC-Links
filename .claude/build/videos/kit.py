# KPC website announcement video: 1920x1080, 30 fps, about 40 s.
import subprocess, sys, numpy as np, cv2
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 1920, 1080, 30
REPO = '/home/claude/kpc-links/'

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


# ---------- browser window ----------
BW, BH, BAR = 1180, 740, 44
WIN_MASK = rrect_mask(BW, BH, 16)
def page(path):
    im = load(path); sc = BW / im.shape[1]
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
    f = kenburns(BGL if img is None else img, t / L, 1.05, 1.12, .4, .6)
    f = cv2.GaussianBlur(f, (0, 0), 7) * .32
    return f


def panel(frame, img, cx, cy, maxw, maxh, a, zoom=1.0, r=14):
    """floating screenshot card, fit inside maxw x maxh, centred at cx, cy"""
    if a <= 0: return
    h, w = img.shape[:2]; sc = min(maxw / w, maxh / h) * zoom
    nw, nh = int(w * sc), int(h * sc)
    im = cv2.resize(img, (nw, nh), interpolation=cv2.INTER_AREA if sc < 1 else cv2.INTER_CUBIC)
    x0, y0 = int(cx - nw / 2), int(cy - nh / 2)
    sh = np.zeros((H, W, 1), np.float32); sh[max(0, y0 + 22):min(H, y0 + nh + 22), max(0, x0 + 8):min(W, x0 + nw + 8)] = .6
    sh = cv2.GaussianBlur(sh, (0, 0), 24)[..., None]; frame *= (1 - sh * a)
    m = rrect_mask(nw, nh, r) * a
    xa, ya, xb, yb = max(0, x0), max(0, y0), min(W, x0 + nw), min(H, y0 + nh)
    frame[ya:yb, xa:xb] = frame[ya:yb, xa:xb] * (1 - m[ya - y0:yb - y0, xa - x0:xb - x0]) + im[ya - y0:yb - y0, xa - x0:xb - x0] * m[ya - y0:yb - y0, xa - x0:xb - x0]
    cv2.rectangle(frame, (x0, y0), (x0 + nw - 1, y0 + nh - 1), (150 * a, 120 * a, 60 * a), 1, cv2.LINE_AA)

def caption(f, t, L, cx, label, l1, l2, det, size=64, width=30):
    put(f, text(label, F(SANS, 26), GOLD, 8), cx, 400, inout(t, .3, L + 1), 'l')
    rule(f, cx, 438, 120 * ease((t - .5) / .8), inout(t, .5, L + 1))
    put(f, text(l1, F(SERIF, size), CREAM, 0), cx, 510, inout(t, .5, L + 1, .7), 'l')
    if l2: put(f, text(l2, F(SERIF, size), GOLD, 0), cx, 510 + size * 1.25, inout(t, .7, L + 1, .7), 'l')
    words, lines, cur = det.split(), [], ''
    for w_ in words:
        if len(cur + ' ' + w_) > width and cur: lines.append(cur); cur = w_
        else: cur = (cur + ' ' + w_).strip()
    lines.append(cur)
    y0 = 510 + size * 1.25 * (2 if l2 else 1) + 10
    for j, ln in enumerate(lines): put(f, text(ln, F(SANSR, 28), SUB, 0), cx, y0 + j * 44, inout(t, 1.0, L + 1, .7), 'l')

def ring(f, x, y, w, h, a, col=GOLD):
    if a <= 0: return
    ov = f.copy(); cv2.rectangle(ov, (int(x), int(y)), (int(x + w), int(y + h)), col, 4, cv2.LINE_AA); f[:] = f * (1 - a) + ov * a

def render(SCENES, OUT, preview=None, XF=.6, song=None, ss=0.0):
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
    if preview:
        ts = [st + min(L - .8, 2.6) for (fn, L), st in zip(SCENES, starts)]
        ims = [Image.fromarray(frame_at(T)).resize((640, 360), Image.LANCZOS) for T in ts]
        sheet = Image.new('RGB', (1920, 360 * ((len(ims) + 2) // 3)))
        for i, im in enumerate(ims): sheet.paste(im, ((i % 3) * 640, (i // 3) * 360))
        sheet.save(preview, quality=82); print(round(total, 1)); return
    n = int(total * FPS); tmp = OUT + '.silent.mp4'
    p = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', tmp], stdin=subprocess.PIPE)
    for i in range(n): p.stdin.write(frame_at(i / FPS).tobytes())
    p.stdin.close(); p.wait()
    d = n / FPS
    if '--novideo' in sys.argv: pass
    if song:
        subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-ss', f'{ss:.2f}', '-i', song, '-map', '0:v', '-map', '1:a', '-c:v', 'copy', '-af',
                        f'afade=t=in:st=0:d=0.4,afade=t=out:st={d - 2.8:.2f}:d=2.8,loudnorm=I=-14:TP=-1.5:LRA=11', '-c:a', 'aac', '-b:a', '192k', '-ar', '48000', '-t', f'{d:.2f}', '-movflags', '+faststart', OUT], check=True)
    print('done', OUT, round(d, 1))

SONG = '/root/.claude/uploads/90e24643-b9af-59bf-86a9-9c6206df7c06/9fa503b8-Get_Outside_Get_On_The_Air.mp3'
LAKE = load(REPO + 'hero-lake-camp.jpg'); BGL = load(REPO + 'bg-lodge.jpg')
LOGO = np.asarray(Image.open(REPO + 'KPC-logo.png').convert('RGBA').resize((300, 300), Image.LANCZOS)).astype(np.float32)
LOGO_S = np.asarray(Image.open(REPO + 'KPC-logo.png').convert('RGBA').resize((200, 200), Image.LANCZOS)).astype(np.float32)
