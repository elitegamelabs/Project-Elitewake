"""Builds the six orthographic reference views of the Stone resource in code (no AI image service).
One signed-distance rock (chipped, faceted, granular) is ray-marched from six exact directions, so every view is the same stone.
Usage: python render_stone_sixview.py <output folder> [size]    Writes front/back/left/right/top/underside.png and SixView-Sheet-v2.png."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image

SIZE = int(sys.argv[2]) if len(sys.argv) > 2 else 768
rng = np.random.default_rng(11)
RADII = np.array([1.0, 0.74, 0.55])      # a long, flat-ish pebble: x long, z short
N = rng.normal(size=(9, 3)); N /= np.linalg.norm(N, axis=1, keepdims=True)
# each chip plane sits just inside the ellipsoid surface in its own direction
SURF = 1.0 / np.linalg.norm(N / RADII, axis=1)
OFF = SURF * rng.uniform(0.74, 0.90, 9)


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
    k = 0.028                                           # smooth maximum: chipped edges are slightly rounded
    for n, o in zip(N, OFF):
        c = p @ n - o
        h = np.clip(0.5 + 0.5 * (c - d) / k, 0, 1)
        d = d * (1 - h) + c * h + k * h * (1 - h)
    d = d + 0.06 * fbm(p * 1.8, 3)
    if detail: d = d + 0.010 * fbm(p * 11.0, 2)
    return d


def normal(p, e=0.006):
    g = np.stack([sdf(p + np.array(v) * e) - sdf(p - np.array(v) * e) for v in ((1, 0, 0), (0, 1, 0), (0, 0, 1))], -1)
    return g / (np.linalg.norm(g, axis=-1, keepdims=True) + 1e-9)


def albedo(p):
    base = 0.50 + 0.12 * fbm(p * 2.6, 3)
    grain = fbm(p * 34.0, 2) + 0.5 * (vnoise(p * 80.0) - 0.5)
    pale = np.clip((grain - 0.10) * 5, 0, 1); dark = np.clip((-0.12 - grain) * 5, 0, 1)
    tone = base + 0.30 * pale - 0.20 * dark
    stain = np.clip(vnoise(p * 2.0 + 9) - 0.52, 0, 1) * 1.8
    rgb = np.stack([tone + 0.08 * stain, tone * 0.985 + 0.045 * stain, tone * 0.95 - 0.01 * stain], -1)
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
    color = np.clip(a * shade[..., None] * ao[..., None], 0, 1) ** (1 / 1.1)
    bg = np.full(color.shape, 0.5)
    img = np.where(hit[..., None] & (t[..., None] < 5), color, bg)
    return (img * 255).astype(np.uint8)


if __name__ == '__main__':
    out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
    imgs = {}
    for name in VIEWS:
        imgs[name] = render(name); Image.fromarray(imgs[name]).save(out / f'{name}.png'); print(name)
    order = ['front', 'back', 'left', 'right', 'top', 'underside']
    sheet = np.vstack([np.hstack([imgs[n] for n in order[:3]]), np.hstack([imgs[n] for n in order[3:]])])
    Image.fromarray(sheet).save(out / 'SixView-Sheet-v2.png')
