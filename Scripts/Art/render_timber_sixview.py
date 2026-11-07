"""Builds the six orthographic reference views of a short timber section (Oak, Birch, Ash, Palm, Spruce wood) in code, no AI image service.
A round log section (bark on the side, sawn flat ends with the species' end grain) is ray-marched from six exact orthographic directions, so every view is the same piece.
Usage: python render_timber_sixview.py <oak|birch|ash|palm|spruce> <output folder> [size]"""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

PRESETS = {
    # bark base, bark dark, wood (early), wood (late), ridge count, ridge depth, radius
    'oak':    dict(bark=(.26, .21, .17), dark=(.10, .08, .07), wood=(.66, .48, .28), ring=(.46, .30, .15), rf=11, rd=.040, R=.46, pores=True),
    'birch':  dict(bark=(.92, .91, .86), dark=(.58, .56, .50), wood=(.86, .76, .58), ring=(.74, .62, .44), rf=5, rd=.010, R=.40, lenticel=True),
    'ash':    dict(bark=(.40, .37, .33), dark=(.16, .14, .12), wood=(.80, .66, .44), ring=(.64, .50, .30), rf=9, rd=.030, R=.44, diamond=True),
    'palm':   dict(bark=(.45, .36, .26), dark=(.20, .15, .10), wood=(.40, .28, .17), ring=(.26, .17, .10), rf=6, rd=.020, R=.42, fibrous=True),
    'spruce': dict(bark=(.50, .30, .22), dark=(.28, .15, .11), wood=(.88, .78, .56), ring=(.76, .60, .38), rf=7, rd=.020, R=.38, resin=True),
}
NAME = sys.argv[1] if len(sys.argv) > 1 else 'oak'
P = PRESETS[NAME]
SIZE = int(sys.argv[3]) if len(sys.argv) > 3 else 768
HALF = 0.62                                              # half the length along x


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


def bark_ridges(p):
    ang = np.arctan2(p[..., 2], p[..., 1])                 # angle round the x axis
    u = np.stack([ang * P['rf'] / 3.14159 * 2.0, p[..., 0] * 1.6, np.zeros_like(ang)], -1)
    v = np.stack([ang * P['rf'] * 0.9, p[..., 0] * 3.0, np.zeros_like(ang)], -1)
    return fbm(u + 7, 3) + 0.4 * (vnoise(v) - 0.5)


def sdf(p, detail=True):
    r = np.hypot(p[..., 1], p[..., 2])
    ang = np.arctan2(p[..., 2], p[..., 1])
    wob = 1 + 0.05 * np.sin(p[..., 0] * 2.3 + 0.7) + 0.03 * np.sin(ang * 3 + p[..., 0] * 1.1)       # slightly irregular trunk
    dr = r - P['R'] * wob
    if detail:
        dr = dr + P['rd'] * bark_ridges(p)
    dx = np.abs(p[..., 0] + 0.03 * p[..., 1]) - HALF                                                  # sawn ends, a touch off square
    return np.maximum(dr, dx)


def normal(p, e=0.005):
    g = np.stack([sdf(p + np.array(v) * e) - sdf(p - np.array(v) * e) for v in ((1, 0, 0), (0, 1, 0), (0, 0, 1))], -1)
    return g / (np.linalg.norm(g, axis=-1, keepdims=True) + 1e-9)


def albedo(p, n):
    ang = np.arctan2(p[..., 2], p[..., 1])
    end = (np.abs(n[..., 0]) > 0.8)[..., None]
    # end grain: concentric rings round a slightly off-centre pith, with radial checks (cracks)
    rr = np.hypot(p[..., 1] - 0.04, p[..., 2] + 0.03)
    if NAME == 'palm':                                     # no concentric rings: fibrous dots over a darker core
        dots = np.clip((vnoise(p * 30.0) - 0.62) * 6, 0, 1)
        rings = np.clip(0.35 + 0.5 * dots + 0.3 * fbm(p * 8, 2), 0, 1)
    else:
        rings = 0.5 + 0.5 * np.sin(rr * 38 + 2.0 * fbm(p * 4.0, 2))
    heart = np.array(P['wood']); late = np.array(P['ring'])
    endc = heart * rings[..., None] + late * (1 - rings[..., None])
    if P.get('pores'):
        endc = endc * (1 - 0.35 * np.clip((vnoise(p * 55) - 0.7) * 5, 0, 1))[..., None]
    crack = np.clip(1 - np.abs(np.sin(ang * 5 + 2 * fbm(p * 2, 2))) * 30 * rr, 0, 1)
    endc = endc * (1 - 0.5 * (crack * (rr > 0.06) * (rr < P['R'] * 0.9))[..., None])
    if P.get('resin'):
        endc = endc + np.array([.80, .55, .15]) * (np.clip((vnoise(p * 9 + 3) - 0.78) * 9, 0, 1))[..., None]
    # bark
    ridge = np.clip(0.5 + 1.4 * bark_ridges(p), 0, 1)[..., None]
    bark = np.array(P['bark']) * ridge + np.array(P['dark']) * (1 - ridge)
    if P.get('lenticel'):                                  # birch: dark horizontal marks on white papery bark
        marks = np.clip((vnoise(np.stack([p[..., 0] * 7, ang * 6, ang * 0], -1)) - 0.72) * 9, 0, 1) * np.clip(1 - np.abs(np.sin(p[..., 0] * 11 + ang * 2)) * 3, 0, 1)
        bark = bark * (1 - marks[..., None]) + np.array([.06, .055, .05]) * marks[..., None]
        bark = bark * (0.92 + 0.12 * fbm(p * 12, 2))[..., None]
    if P.get('diamond'):                                   # ash: interlacing diamond ridges
        d = np.abs(np.sin(ang * 6 + p[..., 0] * 5)) * np.abs(np.sin(ang * 6 - p[..., 0] * 5))
        bark = bark * (0.7 + 0.5 * d)[..., None]
    if P.get('fibrous'):                                   # palm: ring scars from old leaf bases and shaggy fibre
        scar = np.clip(np.sin(p[..., 0] * 14) * 3, -1, 1) * 0.5 + 0.5
        bark = bark * (0.7 + 0.4 * scar)[..., None] * (0.9 + 0.2 * vnoise(p * 40))[..., None]
    if NAME == 'spruce':                                   # thin scaly plates
        plates = np.clip((vnoise(np.stack([p[..., 0] * 9, ang * 5, ang * 0], -1)) - 0.45) * 3, 0, 1)
        bark = bark * (0.65 + 0.5 * plates)[..., None]
    return np.clip(np.where(end, endc, bark), 0, 1)


VIEWS = {   # name: (look, up, right)
    'front': ((0, 1, 0), (0, 0, 1), (1, 0, 0)),
    'back': ((0, -1, 0), (0, 0, 1), (-1, 0, 0)),
    'left': ((1, 0, 0), (0, 0, 1), (0, -1, 0)),       # looks along +x: the end cap
    'right': ((-1, 0, 0), (0, 0, 1), (0, 1, 0)),
    'top': ((0, 0, -1), (0, 1, 0), (1, 0, 0)),
    'underside': ((0, 0, 1), (0, 1, 0), (1, 0, 0)),
}


def render(name):
    look, up, right = (np.array(v, float) for v in VIEWS[name])
    u = np.linspace(-1.1, 1.1, SIZE); v = np.linspace(1.1, -1.1, SIZE)
    U, V = np.meshgrid(u, v)
    origin = -look * 2.5 + U[..., None] * right + V[..., None] * up
    t = np.zeros(U.shape); hit = np.zeros(U.shape, bool)
    active = np.ones(U.shape, bool)
    for _ in range(80):
        idx = np.nonzero(active.ravel())[0]
        if idx.size == 0:
            break
        pp = origin.reshape(-1, 3)[idx] + t.ravel()[idx][:, None] * look
        d = sdf(pp, detail=False)
        done = d < 0.002
        hit.ravel()[idx[done]] = True
        t.ravel()[idx] += np.maximum(d, 0.003) * 0.9
        active.ravel()[idx[done | (t.ravel()[idx] > 5)]] = False
    p = origin + t[..., None] * look
    n = normal(p); a = albedo(p, n)
    cam_light = -look * 0.55 + (-right * 0.55 + up * 0.62); cam_light /= np.linalg.norm(cam_light)
    lam = np.clip((n * cam_light).sum(-1), 0, 1); fill = np.clip((n * (-look)).sum(-1), 0, 1)
    shade = 0.34 + 0.62 * lam + 0.2 * fill
    ao = np.clip(0.8 + 0.7 * fbm(p * 9.0, 2), 0.6, 1.0)
    color = np.clip(a * shade[..., None] * ao[..., None], 0, 1) ** (1 / 1.1)
    img = np.where(hit[..., None] & (t[..., None] < 5), color, np.full(color.shape, 0.5))
    return (img * 255).astype(np.uint8)


if __name__ == '__main__':
    out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
    imgs = {}
    for name in VIEWS:
        imgs[name] = render(name); Image.fromarray(imgs[name]).save(out / f'{name}.png'); print(name)
    order = ['front', 'back', 'left', 'right', 'top', 'underside']
    sheet = np.vstack([np.hstack([imgs[n] for n in order[:3]]), np.hstack([imgs[n] for n in order[3:]])])
    Image.fromarray(sheet).save(out / 'SixView-Sheet-v2.png')
