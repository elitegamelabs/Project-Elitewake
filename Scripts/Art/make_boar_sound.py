"""Synthesize the wild boar's placeholder sounds (Phase 1 slice 4; owner audition pending). Plain Python with numpy, nothing
sampled or downloaded, so the sounds are original. Writes Art/Audio/Fauna/, each 48 kHz, 24-bit, mono (positional one-shots,
CLAUDE.md section 10), peaking at -1.5 dBFS:
  - SFX_BoarGrunt-v1, -v1b, -v1c: three takes of a low, rough two- or three-pulse grunt; its warning call when it turns on a
    survivor, and now and then while it roots about;
  - SFX_BoarCharge-v1: a sharp nasal snort over a short grunt, as it gores;
  - SFX_BoarDeath-v1: a falling squeal breaking into a last grunt.
Each voice is a rough pulse train (the vocal folds) with breath noise, shaped by three resonances (the throat and snout).
Every pitch, length and level is tuning.
    python Scripts/Art/make_boar_sound.py
"""
import wave
from pathlib import Path

import numpy as np

RATE = 48000
OUT = Path(__file__).resolve().parents[2] / 'Art' / 'Audio' / 'Fauna'
rng = np.random.default_rng(1749)


def resonate(x, freq, bandwidth):
    """A two-pole resonance at freq Hz."""
    r = np.exp(-np.pi * bandwidth / RATE)
    c1, c2 = 2 * r * np.cos(2 * np.pi * freq / RATE), -r * r
    y = np.zeros_like(x)
    a = b = 0.0
    for i, v in enumerate(x):
        a, b = v + c1 * a + c2 * b, a
        y[i] = a
    return y * (1 - r)


def voice(seconds, f0_start, f0_end, formants, breath=.25, rough=.08):
    """One vocal sound: pulses from f0_start to f0_end Hz, jittered (rough), with breath noise, through the formants."""
    n = int(seconds * RATE)
    f0 = np.linspace(f0_start, f0_end, n) * (1 + rough * one_noise(n, 40.0))
    phase = np.cumsum(f0 / RATE)
    pulses = np.diff(np.floor(phase), prepend=0.0)                     # one click per cycle
    source = np.convolve(pulses, np.exp(-np.arange(200) / 30.0))[:n]  # each click a decaying glottal pulse
    source += breath * rng.standard_normal(n) * .3
    out = sum(gain * resonate(source, f, bw) for f, bw, gain in formants)
    attack, release = int(.015 * RATE), int(min(.08, seconds * .4) * RATE)
    env = np.ones(n)
    env[:attack] = np.linspace(0, 1, attack)
    env[-release:] = np.linspace(1, 0, release) ** 1.5
    return out * env


def one_noise(n, rate):
    """Slow random wobble, -1..1, changing about rate times a second."""
    k = max(2, int(n / RATE * rate) + 2)
    return np.interp(np.arange(n), np.linspace(0, n, k), rng.uniform(-1, 1, k))


GRUNT = ((320, 140, 1.0), (950, 260, .45), (2400, 400, .12))


def grunt_call(pulses, base):
    parts = []
    for k in range(pulses):
        length = rng.uniform(.14, .26)
        f0 = base * rng.uniform(.9, 1.1)
        parts.append(voice(length, f0, f0 * .82, GRUNT, breath=.35, rough=.12) * rng.uniform(.75, 1.0))
        parts.append(np.zeros(int(rng.uniform(.07, .14) * RATE)))
    return np.concatenate(parts + [np.zeros(int(.15 * RATE))])


def charge():
    n = int(.22 * RATE)
    snort = rng.standard_normal(n) * np.exp(-np.arange(n) / (.06 * RATE))
    snort = resonate(snort, 1400, 900) + .5 * resonate(snort, 3200, 1200)
    return np.concatenate([snort * 3.0, np.zeros(int(.03 * RATE)), voice(.2, 135, 105, GRUNT, .4, .15),
                           np.zeros(int(.15 * RATE))])


def death():
    squeal = voice(.85, 620, 330, ((1250, 300, 1.0), (2900, 500, .5), (4200, 700, .15)), breath=.2, rough=.06)
    return np.concatenate([squeal, np.zeros(int(.12 * RATE)), voice(.35, 105, 70, GRUNT, .5, .18) * .8, np.zeros(int(.25 * RATE))])


def write(name, sound):
    sound = sound - sound.mean()                                        # no DC offset
    sound *= 10 ** (-1.5 / 20) / np.max(np.abs(sound))
    data = np.clip(sound * (2 ** 23 - 1), -(2 ** 23), 2 ** 23 - 1).astype('<i4')
    raw = np.frombuffer(data.tobytes(), dtype=np.uint8).reshape(-1, 4)[:, :3].tobytes()   # little-endian 24-bit
    OUT.mkdir(parents=True, exist_ok=True)
    with wave.open(str(OUT / f'{name}.wav'), 'wb') as w:
        w.setnchannels(1)
        w.setsampwidth(3)
        w.setframerate(RATE)
        w.writeframes(raw)
    print(f'{name}.wav: {len(sound) / RATE:.2f} s, peak {20 * np.log10(np.max(np.abs(sound))):.1f} dBFS')


def main():
    write('SFX_BoarGrunt-v1', grunt_call(2, 118))
    write('SFX_BoarGrunt-v1b', grunt_call(3, 104))
    write('SFX_BoarGrunt-v1c', grunt_call(2, 128))
    write('SFX_BoarCharge-v1', charge())
    write('SFX_BoarDeath-v1', death())


if __name__ == '__main__':
    main()
