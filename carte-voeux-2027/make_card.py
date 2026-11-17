"""Carte de voeux EDLC 2027 - v2 (style épuré)."""
import math, os, sys
from PIL import Image, ImageDraw, ImageFont

BASE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(BASE, '..', 'images')
OUT = os.path.join(BASE, 'frames_v2')
os.makedirs(OUT, exist_ok=True)

W, SS = 1080, 2
S = W * SS
FPS = 25
T_TOTAL = 8.0
N = int(T_TOTAL * FPS)

RED, ORANGE, YELLOW = (0xEF, 0x3F, 0x34), (0xF8, 0x94, 0x10), (0xFF, 0xCB, 0x1F)
BLUE, GREEN, PINK = (0x26, 0x40, 0x8F), (0x36, 0xB9, 0x95), (0xF5, 0x97, 0xB8)
WHITE = (255, 255, 255)

FD = '/usr/share/fonts/opentype/inter/'
f_year = ImageFont.truetype(FD + 'InterDisplay-Black.otf', 290 * SS)
f_kick = ImageFont.truetype(FD + 'Inter-SemiBold.otf', 32 * SS)
f_sub = ImageFont.truetype(FD + 'Inter-Medium.otf', 31 * SS)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, a, b): return clamp((t - a) / (b - a))
def eoc(x): return 1 - (1 - x) ** 3
def eoq(x): return 1 - (1 - x) ** 5
def eio(x): return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def eob(x, s=1.70158): return 1 + (s + 1) * (x - 1) ** 3 + s * (x - 1) ** 2
def lerp(a, b, x): return a + (b - a) * x
def lerpc(c1, c2, x): return tuple(int(round(lerp(a, b, x))) for a, b in zip(c1, c2))

# ---------- logo (white version, pictogram redrawn as vector) ----------
logo = Image.open(os.path.join(IMG, '3.png')).convert('RGBA')
lp = logo.load()
for y in range(logo.height):
    for x in range(logo.width):
        r, g, b, a = lp[x, y]
        lp[x, y] = (255, 255, 255, 0 if (x < 213 and y < 262) else a)
LOGO_W = 400
ls = LOGO_W / logo.width
LOGO_H = round(logo.height * ls)
LOGO_X = (W - LOGO_W) / 2
LOGO_Y = W - LOGO_H - 58
logo_s = logo.resize((LOGO_W * SS, LOGO_H * SS), Image.LANCZOS)

P_CX, P_CY, P_R, P_r, P_HEAD, P_LEGS = 123, 82, 77, 45, 36, 158
PF_R, PF_CX, PF_CY = P_R * ls, LOGO_X + P_CX * ls, LOGO_Y + P_CY * ls
PI_R = 165
PI_CX, PI_CY = W / 2, W / 2 - 0.79 * PI_R - 10
PIC_MID = (PI_CX, PI_CY + 0.79 * PI_R)   # visual centre of the big pictogram

def draw_picto(layer, cx, cy, R, arms, legs, head, color):
    cx, cy, R = cx * SS, cy * SS, R * SS
    r, hr, dy = R * P_r / P_R, R * P_HEAD / P_R, R * P_LEGS / P_R
    m = Image.new('L', layer.size, 0)
    d = ImageDraw.Draw(m)
    def half_ring(cx, cy, mid, e):
        if e <= 0.001: return
        a0, a1 = mid - 90 * e, mid + 90 * e
        d.pieslice([cx - R, cy - R, cx + R, cy + R], a0, a1, fill=255)
        d.pieslice([cx - r, cy - r, cx + r, cy + r], a0 - 1, a1 + 1, fill=0)
    half_ring(cx, cy, 90, arms)
    half_ring(cx, cy + dy, 270, legs)
    if head > 0.001:
        h = hr * head
        d.ellipse([cx - h, cy - h, cx + h, cy + h], fill=255)
    layer.paste(Image.new('RGBA', layer.size, color + (255,)), (0, 0), m)

# ---------- text ----------
def sprite(txt, font, color, spacing=0):
    widths = [font.getlength(c) for c in txt]
    tw = int(sum(widths) + spacing * (len(txt) - 1)) + 8
    asc, desc = font.getmetrics()
    im = Image.new('RGBA', (tw, asc + desc + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 4
    for c, w in zip(txt, widths):
        d.text((x, 4), c, font=font, fill=color + (255,))
        x += w + spacing
    return im.crop(im.getbbox())

kicker = sprite('MEILLEURS VŒUX', f_kick, WHITE, spacing=11 * SS)
sub = sprite('Que 2027 donne de l’élan à tous vos projets.', f_sub, WHITE)

DIG = '2027'
dsp = [sprite(c, f_year, WHITE) for c in DIG]
adv = [f_year.getlength(c) for c in DIG]
trk = -4 * SS
YEAR_CY = 488
ytop = YEAR_CY * SS - max(s.height for s in dsp) // 2
dh = max(s.height for s in dsp)
tot = sum(adv) + trk * 3
dxs, x = [], S / 2 - tot / 2
for i, c in enumerate(DIG):
    dxs.append(x + f_year.getbbox(c)[0]); x += adv[i] + trk

KICK_Y, BAR_Y, SUB_Y = 300, 655, 724

def faded(sp, a):
    s = sp.copy(); s.putalpha(s.getchannel('A').point(lambda v: int(v * a))); return s

# ---------- frame ----------
IRIS = [YELLOW, ORANGE, PINK, GREEN, RED, BLUE]
IRIS_T0, IRIS_STEP, IRIS_DUR = 1.30, 0.11, 0.95
RMAX = math.hypot(W, W) * 0.62

def render(t):
    img = Image.new('RGBA', (S, S), WHITE + (255,))
    d = ImageDraw.Draw(img)
    cx0, cy0 = PIC_MID
    # colour iris: concentric discs in brand colours, ending on brand blue
    for i, col in enumerate(IRIS):
        p = prog(t, IRIS_T0 + i * IRIS_STEP, IRIS_T0 + i * IRIS_STEP + IRIS_DUR)
        if p <= 0: continue
        rr = eio(p) * RMAX * (1.0 if col == BLUE else 1.02)
        d.ellipse([(cx0 - rr) * SS, (cy0 - rr) * SS, (cx0 + rr) * SS, (cy0 + rr) * SS], fill=col)

    # decorative brand arcs (half rings) in corners, slowly turning
    deco = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    dd = ImageDraw.Draw(deco)
    for (ax, ay, R, r, col, a0, spd, ts) in [
            (W + 40, -40, 300, 205, GREEN, 90, 5, 2.75),
            (-40, W + 40, 250, 170, ORANGE, 270, 5, 2.9),
            (W + 10, W - 210, 95, 62, PINK, 180, -7, 3.05),
            (60, 170, 54, 34, YELLOW, 0, -8, 3.15)]:
        p = eoc(prog(t, ts, ts + 0.9))
        if p <= 0: continue
        ang = a0 + spd * (t - ts)
        e = 180 * p
        box = [(ax - R) * SS, (ay - R) * SS, (ax + R) * SS, (ay + R) * SS]
        ibox = [(ax - r) * SS, (ay - r) * SS, (ax + r) * SS, (ay + r) * SS]
        m = Image.new('L', (S, S), 0); md = ImageDraw.Draw(m)
        md.pieslice(box, ang, ang + e, fill=255)
        md.pieslice(ibox, ang - 2, ang + e + 2, fill=0)
        deco.paste(Image.new('RGBA', (S, S), col + (255,)), (0, 0), m)
    img.alpha_composite(deco)

    # pictogram: drawing (kept from v1), turns white, travels into the logo
    arms = eio(prog(t, 0.30, 0.95))
    legs = eio(prog(t, 0.60, 1.25))
    head = eob(prog(t, 0.05, 0.55), 2.2)
    col = lerpc(RED, WHITE, eio(prog(t, 1.75, 2.15)))
    m = eio(prog(t, 2.15, 3.0))
    pl = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    draw_picto(pl, lerp(PI_CX, PF_CX, m), lerp(PI_CY, PF_CY, m), lerp(PI_R, PF_R, m),
               arms, legs, head, col)
    img.alpha_composite(pl)

    # white wordmark wipe
    w = eoc(prog(t, 2.8, 3.5))
    if w > 0:
        lw = int(logo_s.width * w)
        if lw > 0:
            img.alpha_composite(logo_s.crop((0, 0, lw, logo_s.height)), (int(LOGO_X * SS), int(LOGO_Y * SS)))

    # kicker
    p = eoc(prog(t, 2.45, 3.1))
    if p > 0:
        img.alpha_composite(faded(kicker, p), (int((S - kicker.width) / 2),
                            int((KICK_Y + (1 - p) * 18) * SS - kicker.height / 2)))
    # year: masked rise
    clip = ytop + dh + 4 * SS
    for i, sp in enumerate(dsp):
        p = prog(t, 2.55 + i * 0.09, 2.55 + i * 0.09 + 0.85)
        if p <= 0: continue
        y = int(ytop + (1 - eoq(p)) * dh * 1.05)
        vis = int(clip - y)
        if vis > 0:
            img.alpha_composite(sp.crop((0, 0, sp.width, min(sp.height, vis))), (int(dxs[i]), y))
    # palette bar, drawn left to right
    BW, BH, GAP = 330, 8, 6
    seg = (BW - GAP * 5) / 6
    for i, c in enumerate([RED, ORANGE, YELLOW, GREEN, PINK, WHITE]):
        p = eoc(prog(t, 3.15 + i * 0.07, 3.15 + i * 0.07 + 0.35))
        if p <= 0: continue
        x0 = W / 2 - BW / 2 + i * (seg + GAP)
        d.rounded_rectangle([x0 * SS, (BAR_Y - BH / 2) * SS, (x0 + seg * p) * SS, (BAR_Y + BH / 2) * SS],
                            radius=BH / 2 * SS, fill=c)
    # subtitle
    p = eoc(prog(t, 3.45, 4.1))
    if p > 0:
        img.alpha_composite(faded(sub, p * 0.92), (int((S - sub.width) / 2),
                            int((SUB_Y + (1 - p) * 14) * SS - sub.height / 2)))

    # subtle light sweep across the year during the hold
    out = img.convert('RGB').resize((W, W), Image.LANCZOS)
    f = prog(t, T_TOTAL - 0.5, T_TOTAL)
    if f > 0:
        out = Image.blend(out, Image.new('RGB', out.size, WHITE), eio(f))
    return out

if __name__ == '__main__':
    if len(sys.argv) > 1:
        for ts in sys.argv[1:]:
            render(float(ts)).save(os.path.join(BASE, f'v2_{ts}.png'))
    else:
        for i in range(N):
            render(i / FPS).save(os.path.join(OUT, f'f{i:04d}.png'))
        print('frames', N)
