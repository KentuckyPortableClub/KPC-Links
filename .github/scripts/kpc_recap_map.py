#!/usr/bin/env python3
"""Picture for a member activation recap post (kpc_social.js task 'recaps').

  echo '{"call":"K4TEST","date":"Oct 16","qsos":23,"parks":[{"ref":"US-1271","name":"Taylorsville Lake SP","la":38.03,"lo":-85.24}]}' \
    | python3 .github/scripts/kpc_recap_map.py out.png

Draws Kentucky (Census county outlines from kpc-ky-counties-hd.json) with a glowing gold pin on each park,
the call sign, park name(s) and the contact count. 1200x630 (Facebook / Discord link size).
"""
import json, sys, math
from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 1200, 630
info = json.load(sys.stdin)
out = sys.argv[1]
counties = json.load(open('kpc-ky-counties-hd.json'))


def font(size, bold=True, mono=False):
    names = (['DejaVuSansMono-Bold.ttf', 'DejaVuSansMono.ttf'] if mono else ['DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf'])
    for n in names:
        for d in ('/usr/share/fonts/truetype/dejavu/', ''):
            try:
                return ImageFont.truetype(d + n, size)
            except Exception:
                pass
    return ImageFont.load_default()


# background: dark lodge-brown to night blue
img = Image.new('RGB', (W, H), '#120c07')
bg = ImageDraw.Draw(img)
for y in range(H):
    t = y / H
    bg.line([(0, y), (W, y)], fill=(int(24 - 10 * t), int(16 - 4 * t), int(10 + 18 * t)))

# map area on the right
mx0, my0, mx1, my1 = 430, 120, 1170, 560
lon0, lon1, lat0, lat1 = -89.6, -81.9, 36.45, 39.2
kx = math.cos(math.radians(37.8))
sx = (mx1 - mx0) / ((lon1 - lon0) * kx)
sy = (my1 - my0) / (lat1 - lat0)
s = min(sx, sy)
ox = mx0 + ((mx1 - mx0) - (lon1 - lon0) * kx * s) / 2
oy = my0 + ((my1 - my0) - (lat1 - lat0) * s) / 2


def pt(lo, la):
    return (ox + (lo - lon0) * kx * s, oy + (lat1 - la) * s)


layer = Image.new('RGBA', (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(layer)
for c in counties:
    for ring in c.get('r', []):
        if len(ring) > 2:
            d.polygon([pt(x, y) for x, y in ring], fill=(40, 52, 40, 255), outline=(240, 201, 107, 110))
img.paste(layer, (0, 0), layer)

# glowing pins
glow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
g = ImageDraw.Draw(glow)
pins = [p for p in info.get('parks', []) if p.get('la') and p.get('lo')]
for p in pins:
    x, y = pt(p['lo'], p['la'])
    g.ellipse([x - 34, y - 34, x + 34, y + 34], fill=(246, 213, 138, 150))
glow = glow.filter(ImageFilter.GaussianBlur(14))
img.paste(glow, (0, 0), glow)
d2 = ImageDraw.Draw(img)
for p in pins:
    x, y = pt(p['lo'], p['la'])
    d2.ellipse([x - 11, y - 11, x + 11, y + 11], fill='#f6d58a', outline='#2a1a05', width=3)

# words on the left
try:
    logo = Image.open('KPC-logo.png').convert('RGBA')
    logo.thumbnail((92, 92))
    img.paste(logo, (40, 34), logo)
except Exception:
    pass
d2.text((148, 48), 'KENTUCKY PORTABLE CLUB', font=font(22), fill='#f6d58a')
d2.text((148, 80), 'ACTIVATION RECAP', font=font(18, False), fill='#c9b48a')
d2.text((40, 170), info.get('call', ''), font=font(74, mono=True), fill='#ffffff')
d2.text((44, 262), f"{info.get('qsos', 0)} contacts", font=font(40), fill='#f6d58a')
d2.text((44, 316), info.get('date', ''), font=font(24, False), fill='#d9cdb4')
y = 370
for p in info.get('parks', [])[:4]:
    name = p.get('name', '')
    if len(name) > 30:
        name = name[:29].rstrip() + '…'
    d2.text((44, y), p.get('ref', ''), font=font(22, mono=True), fill='#f6d58a')
    d2.text((44, y + 28), name, font=font(22, False), fill='#ffffff')
    y += 66
d2.text((40, H - 46), 'kentuckyportableclub.github.io/KPC-Links', font=font(18, False), fill='#a8987a')
d2.rectangle([0, 0, W - 1, H - 1], outline='#d5a63a', width=4)
img.save(out, optimize=True)
print('saved', out)
