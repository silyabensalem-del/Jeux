import math, random, os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = os.path.dirname(os.path.abspath(__file__))
IMG = os.path.join(BASE, '..', 'images')
OUT = os.path.join(BASE, 'frames')
os.makedirs(OUT, exist_ok=True)

W = 1080            # output size
SS = 2              # supersampling
S = W * SS
FPS = 25
T_TOTAL = 7.6
N = int(T_TOTAL * FPS)

RED, ORANGE, YELLOW = (0xEF, 0x3F, 0x34), (0xF8, 0x94, 0x10), (0xFF, 0xCB, 0x1F)
BLUE, GREEN, PINK = (0x26, 0x40, 0x8F), (0x36, 0xB9, 0x95), (0xF5, 0x97, 0xB8)
PALETTE = [RED, ORANGE, YELLOW, BLUE, GREEN, PINK]
INK = (0x1D, 0x1D, 0x1B)
GREY = (0x55, 0x57, 0x5E)
BG = (255, 255, 255)

FD = '/usr/share/fonts/opentype/inter/'
f_black = ImageFont.truetype(FD + 'InterDisplay-Black.otf', 255 * SS)
f_title = ImageFont.truetype(FD + 'InterDisplay-SemiBold.otf', 64 * SS)
f_sub = ImageFont.truetype(FD + 'Inter-Medium.otf', 29 * SS)

def clamp(x, a=0.0, b=1.0): return max(a, min(b, x))
def prog(t, a, b): return clamp((t - a) / (b - a))
def ease_out_cubic(x): return 1 - (1 - x) ** 3
def ease_in_out(x): return 4 * x ** 3 if x < .5 else 1 - (-2 * x + 2) ** 3 / 2
def ease_out_back(x, s=1.70158):
    c3 = s + 1
    return 1 + c3 * (x - 1) ** 3 + s * (x - 1) ** 2
def lerp(a, b, x): return a + (b - a) * x

# ---------------- assets ----------------
logo = Image.open(os.path.join(IMG, '3.png')).convert('RGBA')
# erase pictogram from the logo (we redraw it as vector)
lp = logo.load()
for y in range(0, 262):
    for x in range(0, 213):
        lp[x, y] = (0, 0, 0, 0)
LOGO_W = 430
lscale = LOGO_W / logo.width
LOGO_H = round(logo.height * lscale)
LOGO_X = (W - LOGO_W) / 2
LOGO_Y = 62
logo_s = logo.resize((LOGO_W * SS, LOGO_H * SS), Image.LANCZOS)

crowd = Image.open(os.path.join(IMG, '4.png')).convert('RGBA')
CROWD_W = 660
CROWD_H = round(crowd.height * CROWD_W / crowd.width)
crowd_s = crowd.resize((CROWD_W * SS, CROWD_H * SS), Image.LANCZOS)

# pictogram geometry measured on the logo file (px of 3.png)
P_CX, P_CY, P_R, P_r, P_HEAD, P_LEGS = 123, 82, 77, 45, 36, 158
# final placement (output px)
PF_R = P_R * lscale
PF_CX = LOGO_X + P_CX * lscale
PF_CY = LOGO_Y + P_CY * lscale
# initial big placement
PI_R = 165
PI_CX = W / 2
PI_CY = W / 2 - 0.79 * PI_R - 10

def draw_picto(layer, cx, cy, R, arms, legs, head, color, alpha=255):
    """vector pictogram; arms/legs in [0,1] sweep, head in [0,..] scale"""
    cx, cy, R = cx * SS, cy * SS, R * SS
    r = R * P_r / P_R
    hr = R * P_HEAD / P_R
    dy = R * P_LEGS / P_R
    m = Image.new('L', layer.size, 0)
    d = ImageDraw.Draw(m)
    col = color + (alpha,)
    def half_ring(cx, cy, mid, e):
        if e <= 0.001: return
        a0, a1 = mid - 90 * e, mid + 90 * e
        d.pieslice([cx - R, cy - R, cx + R, cy + R], a0, a1, fill=255)
        d.pieslice([cx - r, cy - r, cx + r, cy + r], a0 - 1, a1 + 1, fill=0)
        # rounded tips while drawing look nicer: none (brand has flat tips)
    half_ring(cx, cy, 90, arms)
    half_ring(cx, cy + dy, 270, legs)
    if head > 0.001:
        h = hr * head
        d.ellipse([cx - h, cy - h, cx + h, cy + h], fill=255)
    solid = Image.new('RGBA', layer.size, col)
    layer.paste(solid, (0, 0), m)

# ---------------- text sprites ----------------
def text_sprite(txt, font, color):
    l, t, r, b = font.getbbox(txt)
    im = Image.new('RGBA', (r - l + 4, b - t + 4), (0, 0, 0, 0))
    ImageDraw.Draw(im).text((2 - l, 2 - t), txt, font=font, fill=color + (255,))
    return im

DIGITS = list('2027')
DCOL = [BLUE, GREEN, ORANGE, RED]
dsprites = [text_sprite(c, f_black, col) for c, col in zip(DIGITS, DCOL)]
# kerning by advance
adv = [f_black.getlength(c) for c in DIGITS]
track = -6 * SS
total_w = sum(adv) + track * 3
YEAR_CY = 462
digit_h = max(s.height for s in dsprites)
YEAR_TOP = YEAR_CY * SS - digit_h // 2
dx = []
x = S / 2 - total_w / 2
for i, c in enumerate(DIGITS):
    l = f_black.getbbox(c)[0]
    dx.append(x + l)
    x += adv[i] + track

title = text_sprite('Meilleurs vœux', f_title, INK)
sub1 = text_sprite('Que 2027 donne de l’élan à tous vos projets.', f_sub, GREY)
sub2 = text_sprite('Toute l’équipe d’Entrepreneurs de la Cité vous souhaite une belle année.', f_sub, GREY)

# ---------------- particles ----------------
rng = random.Random(2027)
BURST_T = 2.55
BX, BY = W / 2, YEAR_CY
burst = []
for i in range(150):
    ang = rng.uniform(0, 2 * math.pi)
    sp = rng.uniform(500, 1500) * (0.6 if rng.random() < .3 else 1)
    burst.append(dict(
        ang=ang, sp=sp, k=rng.uniform(2.6, 3.6), g=rng.uniform(140, 260),
        col=rng.choice(PALETTE), shape=rng.choice(['dot', 'dot', 'arc', 'strip', 'strip']),
        size=rng.uniform(7, 17), rot0=rng.uniform(0, 360), rotv=rng.uniform(-360, 360),
        life=rng.uniform(2.8, 4.2), delay=rng.uniform(0, 0.12)))
rain = []
for i in range(46):
    rain.append(dict(
        t0=rng.uniform(3.0, 7.0), x=rng.uniform(30, W - 30), v=rng.uniform(110, 190),
        sw=rng.uniform(10, 30), sf=rng.uniform(0.6, 1.4), ph=rng.uniform(0, 6.28),
        col=rng.choice(PALETTE), shape=rng.choice(['dot', 'arc', 'strip', 'strip']),
        size=rng.uniform(7, 14), rot0=rng.uniform(0, 360), rotv=rng.uniform(-200, 200)))

def rot_pts(pts, cx, cy, a):
    ca, sa = math.cos(math.radians(a)), math.sin(math.radians(a))
    return [((cx + px * ca - py * sa) * SS, (cy + px * sa + py * ca) * SS) for px, py in pts]

ARC_PTS = None
def shape_pts(shape, size):
    if shape == 'strip':
        w, h = size * 1.5, size * 0.55
        return [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
    if shape == 'arc':  # mini half ring = brand motif
        R, r = size, size * 0.55
        out = [(R * math.cos(math.radians(a)), R * math.sin(math.radians(a))) for a in range(0, 181, 15)]
        inn = [(r * math.cos(math.radians(a)), r * math.sin(math.radians(a))) for a in range(180, -1, -15)]
        return out + inn
    return None

def draw_confetti(d, x, y, p, rot, alpha, scale=1.0):
    col = p['col'] + (int(255 * alpha),)
    s = p['size'] * scale
    if p['shape'] == 'dot':
        rr = s * 0.5 * SS
        d.ellipse([x * SS - rr, y * SS - rr, x * SS + rr, y * SS + rr], fill=col)
    else:
        # 3D flip illusion: squash one axis
        pts = shape_pts(p['shape'], s)
        sq = abs(math.cos(math.radians(rot * 1.7)))
        pts = [(px, py * (0.25 + 0.75 * sq)) for px, py in pts]
        d.polygon(rot_pts(pts, x, y, rot), fill=col)

# ---------------- frame ----------------
def render(t):
    img = Image.new('RGBA', (S, S), BG + (255,))
    fx = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    d = ImageDraw.Draw(fx)

    # shock rings
    for j, col in enumerate([ORANGE, PINK, GREEN]):
        p = prog(t, BURST_T + j * 0.09, BURST_T + j * 0.09 + 1.0)
        if 0 < p < 1:
            rr = ease_out_cubic(p) * (430 + j * 70)
            a = int(255 * (1 - p) ** 1.5)
            wdt = max(1, int((4.5 - 3 * p) * SS))
            d.ellipse([(BX - rr) * SS, (BY - rr) * SS, (BX + rr) * SS, (BY + rr) * SS],
                      outline=col + (a,), width=wdt)
    # burst
    for p in burst:
        tt = t - BURST_T - p['delay']
        if tt <= 0 or tt > p['life']: continue
        k = p['k']
        dist = p['sp'] / k * (1 - math.exp(-k * tt))
        x = BX + math.cos(p['ang']) * dist
        y = BY + math.sin(p['ang']) * dist + 0.5 * p['g'] * tt * tt
        a = 1 - prog(tt, p['life'] - 0.8, p['life'])
        sc = 0.4 + 0.6 * prog(tt, 0, 0.15)
        draw_confetti(d, x, y, p, p['rot0'] + p['rotv'] * tt, a, sc)
    # gentle rain
    for p in rain:
        tt = t - p['t0']
        if tt <= 0: continue
        y = -30 + p['v'] * tt
        if y > W + 30: continue
        x = p['x'] + p['sw'] * math.sin(p['sf'] * tt * 2 + p['ph'])
        a = prog(tt, 0, 0.3)
        draw_confetti(d, x, y, p, p['rot0'] + p['rotv'] * tt, a * 0.95)
    img.alpha_composite(fx)

    # pictogram: draw (0-1.4s) then travel to logo (1.4-2.2s)
    arms = ease_in_out(prog(t, 0.30, 0.95))
    legs = ease_in_out(prog(t, 0.60, 1.25))
    head = ease_out_back(prog(t, 0.05, 0.55), 2.2)
    m = ease_in_out(prog(t, 1.55, 2.35))
    cx, cy, R = lerp(PI_CX, PF_CX, m), lerp(PI_CY, PF_CY, m), lerp(PI_R, PF_R, m)
    pl = Image.new('RGBA', (S, S), (0, 0, 0, 0))
    draw_picto(pl, cx, cy, R, arms, legs, head, RED)
    img.alpha_composite(pl)

    # logo wordmark wipe
    w = ease_out_cubic(prog(t, 2.05, 2.75))
    if w > 0:
        lw = int(logo_s.width * w)
        if lw > 0:
            crop = logo_s.crop((0, 0, lw, logo_s.height))
            ox = int(LOGO_X * SS + (1 - w) * -20 * SS)
            img.alpha_composite(crop, (int(LOGO_X * SS), int(LOGO_Y * SS)))

    # title
    p = ease_out_cubic(prog(t, 2.45, 3.05))
    if p > 0:
        s = title.copy()
        s.putalpha(s.getchannel('A').point(lambda v: int(v * p)))
        img.alpha_composite(s, (int((S - s.width) / 2), int(292 * SS - s.height / 2 + (1 - p) * 24 * SS)))

    # year digits: masked rise with overshoot
    clip_bottom = YEAR_TOP + digit_h + 6 * SS
    for i, sp in enumerate(dsprites):
        p = prog(t, 2.6 + i * 0.11, 2.6 + i * 0.11 + 0.7)
        if p <= 0: continue
        off = (1 - ease_out_back(p, 1.3)) * digit_h
        y = int(YEAR_TOP + off)
        vis = int(clip_bottom - y)
        if vis <= 0: continue
        crop = sp.crop((0, 0, sp.width, min(sp.height, vis)))
        img.alpha_composite(crop, (int(dx[i]), y))

    # subtitles
    for j, (sp, yy) in enumerate([(sub1, 622), (sub2, 662)]):
        p = ease_out_cubic(prog(t, 3.35 + j * 0.15, 3.95 + j * 0.15))
        if p <= 0: continue
        s = sp.copy()
        s.putalpha(s.getchannel('A').point(lambda v: int(v * p)))
        img.alpha_composite(s, (int((S - s.width) / 2), int((yy + (1 - p) * 16) * SS - s.height / 2)))

    # crowd rises from bottom
    p = ease_out_cubic(prog(t, 3.55, 4.45))
    if p > 0:
        y = W - CROWD_H * p + 2
        img.alpha_composite(crowd_s, (int((S - crowd_s.width) / 2), int(y * SS)))

    out = img.convert('RGB').resize((W, W), Image.LANCZOS)
    # fade to white at the end (loop point)
    f = prog(t, T_TOTAL - 0.45, T_TOTAL)
    if f > 0:
        out = Image.blend(out, Image.new('RGB', out.size, BG), ease_in_out(f))
    return out

if __name__ == '__main__':
    if len(sys.argv) > 1:
        for ts in sys.argv[1:]:
            render(float(ts)).save(os.path.join(BASE, f'preview_{ts}.png'))
    else:
        for i in range(N):
            render(i / FPS).save(os.path.join(OUT, f'f{i:04d}.png'))
        print('frames', N)
