"""Builds the six orthographic reference views of the Stone resource in code (no AI image service).
One signed-distance rock (chipped, faceted, granular) is ray-marched from six exact directions, so every view is the same stone.
Usage: python render_rock_sixview.py <preset> <output folder> [size]    Presets: stone flint coal iron_ore copper_ore sulfur_ore sandstone bog_iron clay salt ice amber dark_gem green_gem peat. Writes front/back/left/right/top/underside.png and SixView-Sheet-v2.png."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

PRESETS = {
    # seed, radii, chip count, chip depth range, chip smoothing, lump size, pit depth, base tone, flecks, tint, vein kind/colour, banding
    'stone':      dict(seed=11, radii=(1.0, .74, .55), chips=9,  depth=(.74, .90), k=.028, lump=.06, pit=0.0,  tone=.50, fleck=.30, tint=(0.0, 0.0, 0.0), gloss=0.0),
    'flint':      dict(seed=23, radii=(.9, .7, .6),   chips=16, depth=(.70, .88), k=.012, lump=.03, pit=0.0,  tone=.16, fleck=.06, tint=(-.01, .0, .02), gloss=.35, cortex=(.62, .58, .46)),
    'coal':       dict(seed=31, radii=(.95, .78, .62), chips=13, depth=(.66, .86), k=.010, lump=.035, pit=0.0, tone=.065, fleck=.035, tint=(0, 0, .004), gloss=.55),
    'iron_ore':   dict(seed=41, radii=(.95, .75, .62), chips=11, depth=(.72, .90), k=.02, lump=.05, pit=0.0,  tone=.11, fleck=.07, tint=(0, 0, 0), gloss=.1, bands=((.50, .27, .11), 6.5)),
    'copper_ore': dict(seed=53, radii=(1.0, .78, .6),  chips=10, depth=(.72, .90), k=.025, lump=.06, pit=0.0,  tone=.38, fleck=.2, tint=(0, 0, 0), gloss=.0, patches=((.20, .48, .40), (.46, .28, .12))),
    'sulfur_ore': dict(seed=67, radii=(1.0, .8, .62),  chips=10, depth=(.72, .90), k=.022, lump=.06, pit=0.0,  tone=.40, fleck=.2, tint=(0, 0, 0), gloss=.0, veins=(.86, .74, .12)),
    'sandstone':  dict(seed=79, radii=(1.0, .8, .6),   chips=7,  depth=(.80, .93), k=.05, lump=.035, pit=0.0, tone=.62, fleck=.12, tint=(.07, .0, -.07), gloss=0.0, strata=((.74, .60, .40), (.52, .38, .24), 11.0)),
    'clay':       dict(seed=101, radii=(.95, .72, .6), chips=3, depth=(.86, .95), k=.10, lump=.11, pit=0.0, tone=.5, fleck=0, tint=(0, 0, 0), gloss=.12, color=(.62, .36, .24), mottle=.14, cracks=(.30, .16, .10)),
    'salt':       dict(seed=103, radii=(.9, .75, .65), chips=14, depth=(.70, .88), k=.014, lump=.04, pit=0.0, tone=.5, fleck=0, tint=(0, 0, 0), gloss=.3, color=(.90, .89, .86), mottle=.07),
    'ice':        dict(seed=107, radii=(.9, .8, .7), chips=15, depth=(.70, .88), k=.012, lump=.025, pit=0.0, tone=.5, fleck=0, tint=(0, 0, 0), gloss=.8, color=(.74, .88, .97), mottle=.06),
    'amber':      dict(seed=109, radii=(.85, .72, .6), chips=12, depth=(.74, .90), k=.012, lump=.03, pit=0.0, tone=.5, fleck=0, tint=(0, 0, 0), gloss=.7, color=(.86, .50, .08), mottle=.16),
    'dark_gem':   dict(seed=113, radii=(.8, .7, .62), chips=13, depth=(.70, .88), k=.010, lump=.02, pit=0.0, tone=.5, fleck=0, tint=(0, 0, 0), gloss=.6, color=(.17, .15, .22), mottle=.22),
    'green_gem':  dict(seed=127, radii=(.8, .68, .62), chips=13, depth=(.70, .88), k=.010, lump=.02, pit=0.0, tone=.5, fleck=0, tint=(0, 0, 0), gloss=.65, color=(.16, .50, .30), mottle=.2),
    'peat':       dict(seed=131, radii=(.95, .78, .62), chips=3, depth=(.86, .95), k=.10, lump=.12, pit=.02, tone=.5, fleck=0, tint=(0, 0, 0), gloss=0.0, color=(.20, .13, .08), mottle=.30, fibres=True),
    'bog_iron':   dict(seed=97, radii=(.9, .8, .7),    chips=4,  depth=(.86, .95), k=.09, lump=.10, pit=.055, tone=.20, fleck=.1, tint=(.05, .0, -.03), gloss=0.0, rust=((.42, .22, .10), (.24, .13, .07))),
}
PRESET_NAME = sys.argv[1] if len(sys.argv) > 1 else 'stone'
P = PRESETS[PRESET_NAME]
SIZE = int(sys.argv[3]) if len(sys.argv) > 3 else 768
rng = np.random.default_rng(P['seed'])
RADII = np.array(P['radii'])      # a long, flat-ish pebble: x long, z short
N = rng.normal(size=(P['chips'], 3)); N /= np.linalg.norm(N, axis=1, keepdims=True)
# each chip plane sits just inside the ellipsoid surface in its own direction
SURF = 1.0 / np.linalg.norm(N / RADII, axis=1)
OFF = SURF * rng.uniform(P['depth'][0], P['depth'][1], P['chips'])


def hash3(i):
    x = (i[..., 0] * 73856093) ^ (i[..., 1] * 19349663) ^ (i[..., 2] * 83492791)
    x = x.astype(np.int64) & 0xFFFFFFFF
    x = ((x >> 13) ^ x) * 1274126177 & 0xFFFFFFFF
    x = ((x >> 16) ^ x) & 0xFFFF
    return x / 65535.0


def vnoise(p):
    i = np.floor(p); f = p - i; f = f * f * f * (f * (f * 6 - 15) + 10); r = 0
    ii = i.astype(np.int64)
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = (f[..., 0] if dx else 1 - f[..., 0]) * (f[..., 1] if dy else 1 - f[..., 1]) * (f[..., 2] if dz else 1 - f[..., 2])
                r = r + w * hash3(ii + np.array([dx, dy, dz]))
    return r


def fbm(p, octaves=3):
    s, a, tot = 1.0, 0.5, 0
    for _ in range(octaves):
        tot = tot + a * (vnoise(p * s) - 0.5); s *= 2.07; a *= 0.5
    return tot


def sdf(p, detail=True):
    q = p / RADII
    d = (np.linalg.norm(q, axis=-1) - 1.0) * RADII.min()
    k = P['k']                                          # smooth maximum: chipped edges are slightly rounded
    for n, o in zip(N, OFF):
        c = p @ n - o
        h = np.clip(0.5 + 0.5 * (c - d) / k, 0, 1)
        d = d * (1 - h) + c * h + k * h * (1 - h)
    d = d + P['lump'] * fbm(p * 1.8, 3)
    if P['pit']: d = d + P['pit'] * np.clip(vnoise(p * 7.0) - 0.45, 0, 1) * 2.2          # bog iron: porous pits
    if detail: d = d + 0.010 * fbm(p * 11.0, 2)
    return d


def normal(p, e=0.006):
    g = np.stack([sdf(p + np.array(v) * e) - sdf(p - np.array(v) * e) for v in ((1, 0, 0), (0, 1, 0), (0, 0, 1))], -1)
    return g / (np.linalg.norm(g, axis=-1, keepdims=True) + 1e-9)


def albedo(p):
    if 'color' in P:                                      # plain coloured materials (clay, salt, ice, gems, peat): mottled colour, optional cracks and fibres
        m = 1 + P['mottle'] * 2.2 * fbm(p * 4.0, 3)
        rgb = np.array(P['color']) * m[..., None]
        if 'cracks' in P:
            c = np.clip(1 - np.abs(fbm(p * 3.2 + 5, 3)) / 0.02, 0, 1)[..., None]
            rgb = rgb * (1 - c) + np.array(P['cracks']) * c
        if P.get('fibres'):
            f = np.clip(vnoise(np.stack([p[..., 0] * 40, p[..., 1] * 6, p[..., 2] * 40], -1)) - 0.5, 0, 1)[..., None] * 1.2
            rgb = rgb * (1 - 0.5 * f) + np.array([.34, .24, .14]) * 0.5 * f
        rgb = rgb * (0.85 + 0.3 * vnoise(p * 30))[..., None]
        return np.clip(rgb, 0, 1)
    base = P['tone'] + 0.12 * fbm(p * 2.6, 3) * (P['tone'] / 0.5) ** 0.5
    grain = fbm(p * 34.0, 2) + 0.5 * (vnoise(p * 80.0) - 0.5)
    pale = np.clip((grain - 0.10) * 5, 0, 1); dark = np.clip((-0.12 - grain) * 5, 0, 1)
    f = P['fleck']
    tone = base + f * pale - 0.66 * f * dark
    stain = np.clip(vnoise(p * 2.0 + 9) - 0.52, 0, 1) * 1.8
    t = P['tint']
    rgb = np.stack([tone + 0.08 * stain + t[0], tone * 0.985 + 0.045 * stain + t[1], tone * 0.95 - 0.01 * stain + t[2]], -1)
    if 'cortex' in P:                                     # flint: pale chalky rind in patches
        m = np.clip((vnoise(p * 2.6 + 3) - 0.60) * 7, 0, 1)[..., None]
        rgb = rgb * (1 - m) + np.array(P['cortex']) * (0.8 + 0.4 * fbm(p * 20, 2))[..., None] * m
    if 'bands' in P:                                      # iron ore: rusty ochre bands across the dark rock
        col, freq = P['bands']
        w = np.clip(np.sin(p[..., 2] * freq + 3 * fbm(p * 2.0, 2) * 4) * 1.6 - 0.2, 0, 1)[..., None]
        rgb = rgb * (1 - 0.75 * w) + np.array(col) * (0.75 + 0.5 * fbm(p * 15, 2))[..., None] * 0.75 * w
    if 'patches' in P:                                    # copper ore: green oxidised patches with a few orange-brown spots
        green, rust = P['patches']
        m = np.clip((vnoise(p * 3.3 + 5) - 0.60) * 6, 0, 1)[..., None]
        r = np.clip((vnoise(p * 6.0 + 17) - 0.70) * 8, 0, 1)[..., None]
        rgb = rgb * (1 - m) + np.array(green) * (0.8 + 0.5 * fbm(p * 18, 2))[..., None] * m
        rgb = rgb * (1 - r) + np.array(rust) * r
    if 'veins' in P:                                      # sulfur ore: yellow inclusions following thin cracks
        crack = np.abs(fbm(p * 2.8 + 11, 3))
        m = np.clip(1 - crack / 0.022, 0, 1)[..., None] ** 0.7
        rgb = rgb * (1 - m) + np.array(P['veins']) * (0.85 + 0.3 * vnoise(p * 30))[..., None] * m
    if 'strata' in P:                                     # sandstone: wavy tan layers
        a_, b_, freq = P['strata']
        w = (0.5 + 0.5 * np.sin(p[..., 2] * freq * 2 + 3.0 * fbm(p * 1.2, 2)))[..., None]
        rgb = np.array(a_) * w + np.array(b_) * (1 - w)
        rgb = rgb * (0.85 + 0.3 * (fbm(p * 40, 2) + 0.5))[..., None]
    if 'rust' in P:                                       # bog iron: earthy brown with darker pits
        a_, b_ = P['rust']
        m = np.clip(0.5 + 2.0 * fbm(p * 5.0, 3), 0, 1)[..., None]
        rgb = np.array(a_) * m + np.array(b_) * (1 - m)
        rgb = rgb * (0.8 + 0.4 * (vnoise(p * 28)))[..., None]
    return np.clip(rgb, 0, 1)


VIEWS = {  # name: (view direction the camera looks along, screen-up, screen-right)
    'front': ((0, 1, 0), (0, 0, 1), (1, 0, 0)),
    'back': ((0, -1, 0), (0, 0, 1), (-1, 0, 0)),
    'left': ((1, 0, 0), (0, 0, 1), (0, -1, 0)),
    'right': ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
    'top': ((0, 0, -1), (0, 1, 0), (1, 0, 0)),
    'underside': ((0, 0, 1), (0, 1, 0), (1, 0, 0)),
}
LIGHT = np.array([-0.5, -0.6, 0.65]); LIGHT /= np.linalg.norm(LIGHT)


def render(name):
    look, up, right = (np.array(v, float) for v in VIEWS[name])
    u = np.linspace(-1.25, 1.25, SIZE); v = np.linspace(1.25, -1.25, SIZE)
    U, V = np.meshgrid(u, v)
    origin = -look * 2.5 + U[..., None] * right + V[..., None] * up
    t = np.zeros(U.shape); hit = np.zeros(U.shape, bool)
    active = (np.hypot(U, V) < 1.4)
    for _ in range(70):
        idx = np.nonzero(active.ravel())[0]
        if idx.size == 0: break
        p = origin.reshape(-1, 3)[idx] + t.ravel()[idx][:, None] * look
        d = sdf(p, detail=False)
        done = d < 0.002
        hit.ravel()[idx[done]] = True
        t.ravel()[idx] += np.maximum(d, 0.003) * 0.9
        active.ravel()[idx[done | (t.ravel()[idx] > 5)]] = False
    p = origin + t[..., None] * look
    n = normal(p); a = albedo(p)
    # headlight-relative key light so every view is lit the same way from the camera's upper left
    cam_light = -look * 0.55 + (-right * 0.55 + up * 0.62)
    cam_light /= np.linalg.norm(cam_light)
    lam = np.clip((n * cam_light).sum(-1), 0, 1)
    fill = np.clip((n * (-look)).sum(-1), 0, 1)
    shade = 0.34 + 0.62 * lam + 0.2 * fill
    ao = np.clip(0.75 + 0.9 * fbm(p * 9.0, 2), 0.6, 1.0)
    spec = 0.0
    if P['gloss']:
        half = cam_light + (-look); half /= np.linalg.norm(half)
        spec = P['gloss'] * np.clip((n * half).sum(-1), 0, 1) ** 28
    color = np.clip(a * shade[..., None] * ao[..., None] + np.asarray(spec)[..., None] * 0.7, 0, 1) ** (1 / 1.1)
    bg = np.full(color.shape, 0.5)
    img = np.where(hit[..., None] & (t[..., None] < 5), color, bg)
    return (img * 255).astype(np.uint8)


if __name__ == '__main__':
    out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    imgs = {}
    for name in VIEWS:
        imgs[name] = render(name); Image.fromarray(imgs[name]).save(out / f'{name}.png'); print(name)
    order = ['front', 'back', 'left', 'right', 'top', 'underside']
    sheet = np.vstack([np.hstack([imgs[n] for n in order[:3]]), np.hstack([imgs[n] for n in order[3:]])])
    Image.fromarray(sheet).save(out / 'SixView-Sheet-v2.png')
