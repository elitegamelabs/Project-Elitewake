"""Synthesize the campfire's placeholder loop (Phase 1 slice 3; owner audition pending). Plain Python with numpy, nothing
sampled or downloaded, so the sound is original. Writes Art/Audio/World/AMB_CampfireLoop-v1.wav: 48 kHz, 24-bit, mono (a
positional emitter, CLAUDE.md section 10), 12 s, its last 2 s cross-faded into its start so no seam is heard, peaking at
-1.5 dBFS. Layers: a low, slowly breathing roar of burning wood; sparse small crackles; now and then a sharper pop as sap
bursts; a faint airy hiss. Every rate and level is tuning.
    python Scripts/Art/make_fire_sound.py
"""
import wave
from pathlib import Path

import numpy as np

RATE = 48000
SECONDS, FADE = 12.0, 2.0
OUT = Path(__file__).resolve().parents[2] / 'Art' / 'Audio' / 'World'
rng = np.random.default_rng(31)


def one_pole(x, cutoff, high=False):
    """A gentle one-pole filter, low-pass (or high-pass) at cutoff Hz."""
    a = np.exp(-2 * np.pi * cutoff / RATE)
    y = np.empty_like(x)
    acc = 0.0
    for i, v in enumerate(x):
        acc = (1 - a) * v + a * acc
        y[i] = acc
    return x - y if high else y


def burst(length, low, high, decay):
    """A short band-limited noise burst that dies away: one crackle."""
    n = max(8, int(length * RATE))
    noise = rng.standard_normal(n)
    band = one_pole(one_pole(noise, high), low, high=True)
    return band * np.exp(-np.arange(n) / (decay * RATE))


def render(seconds):
    n = int(seconds * RATE)
    t = np.arange(n) / RATE
    roar = one_pole(one_pole(rng.standard_normal(n), 520.0), 70.0, high=True)
    roar *= .55 + .25 * np.sin(2 * np.pi * .23 * t + 1.1) + .15 * np.sin(2 * np.pi * .61 * t)
    hiss = one_pole(rng.standard_normal(n), 3500.0, high=True) * .05
    out = roar * .9 + hiss
    for rate, level, (low, high), (length, decay) in ((9.0, .35, (1800, 6500), (.012, .004)),     # small crackles
                                                      (.6, 1.0, (900, 5000), (.035, .012))):       # sap pops
        k = rng.poisson(rate * seconds)
        for at in rng.uniform(0, seconds - .06, k):
            b = burst(length, low, high, decay) * level * rng.uniform(.3, 1.0)
            i = int(at * RATE)
            out[i:i + len(b)] += b
    return out


def main():
    body = render(SECONDS + FADE)
    loop = body[:int(SECONDS * RATE)].copy()
    f = int(FADE * RATE)
    ramp = np.linspace(0, 1, f)
    loop[:f] = loop[:f] * ramp + body[-f:] * (1 - ramp)      # the tail runs into the head
    loop -= loop.mean()                                        # no DC offset
    loop *= 10 ** (-1.5 / 20) / np.max(np.abs(loop))
    OUT.mkdir(parents=True, exist_ok=True)
    data = np.clip(loop * (2 ** 23 - 1), -(2 ** 23), 2 ** 23 - 1).astype('<i4')
    raw = np.frombuffer(data.tobytes(), dtype=np.uint8).reshape(-1, 4)[:, :3].tobytes()   # little-endian 24-bit
    with wave.open(str(OUT / 'AMB_CampfireLoop-v1.wav'), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(3)
        w.setframerate(RATE)
        w.writeframes(raw)
    print(f'AMB_CampfireLoop-v1.wav: {SECONDS:.0f} s, peak {20 * np.log10(np.max(np.abs(loop))):.1f} dBFS')


if __name__ == '__main__':
    main()
