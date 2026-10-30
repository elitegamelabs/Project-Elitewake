"""Synthesize Saltreach Freeport's placeholder town sounds (owner, October 30: free placeholder sounds until paid audio). Plain Python
with numpy, nothing sampled or downloaded, so every sound is original. Writes 44.1 kHz stereo WAVs to Art/Audio/Town/:
  AMB_TavernMurmur-v1.wav  a room of voices talking (no words: synthetic vowels and consonants), mugs clinking, a warm room   (loop)
  AMB_MarketMurmur-v1.wav  fewer voices out of doors, further off, a cart's creak now and then                              (loop)
  AMB_ShipyardWork-v1.wav  mallets on timber in bursts and a hand saw's strokes, with pauses                                 (loop)
  AMB_PierLapping-v1.wav   water slapping softly against piles                                                              (loop)
  SFX_HarborBell-v1.wav    a ship's bell struck twice
Loops are rendered long and cross-faded end into start, so no seam is heard. Every level and rate is tuning.
    python Scripts/Art/make_town_sounds.py
"""
import wave
from pathlib import Path

import numpy as np

RATE = 44100
OUT = Path(__file__).resolve().parents[2] / 'Art' / 'Audio' / 'Town'
rng = np.random.default_rng(30)

VOWELS = [  # (F1, F2, F3) Hz
    (730, 1090, 2440), (530, 1840, 2480), (270, 2290, 3010), (570, 840, 2410), (300, 870, 2240), (660, 1720, 2410), (490, 1350, 1690)]


def write(name, stereo):
    OUT.mkdir(parents=True, exist_ok=True)
    peak = np.max(np.abs(stereo)) or 1.0
    data = (stereo / peak * .89 * 32767).astype(np.int16)
    with wave.open(str(OUT / name), 'wb') as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes(data.reshape(-1).tobytes())
    print(name, f'{len(stereo) / RATE:.1f} s')


def spectral(signal, gain_of):
    """Filter by shaping the whole signal's spectrum: gain_of(freqs) -> gains."""
    spectrum = np.fft.rfft(signal)
    freqs = np.fft.rfftfreq(len(signal), 1 / RATE)
    return np.fft.irfft(spectrum * gain_of(freqs), len(signal))


def lowpass(signal, cutoff):
    return spectral(signal, lambda f: 1 / np.sqrt(1 + (f / cutoff) ** 4))


def highpass(signal, cutoff):
    return spectral(signal, lambda f: 1 / np.sqrt(1 + (cutoff / np.maximum(f, 1)) ** 4))


def bandpass(signal, low, high):
    return highpass(lowpass(signal, high), low)


def reverb(stereo, seconds, wet):
    """A room: convolution with decaying noise, a little different in each ear."""
    n = int(seconds * RATE)
    t = np.arange(n) / RATE
    out = []
    for ch in range(2):
        ir = rng.standard_normal(n) * np.exp(-6.9 * t / seconds)
        ir = lowpass(ir, 4500)
        ir /= np.sqrt(np.sum(ir ** 2))
        dry = stereo[:, ch]
        conv = np.fft.irfft(np.fft.rfft(dry, len(dry) + n) * np.fft.rfft(ir, len(dry) + n))[:len(dry)]
        out.append(dry * (1 - wet) + conv * wet * 3)
    return np.stack(out, axis=1)


def loop(stereo, fade):
    """Cross-fade the tail into the head: the result loops without a seam."""
    n = int(fade * RATE)
    head, body, tail = stereo[:n], stereo[n:-n], stereo[-n:]
    ramp = np.linspace(0, 1, n)[:, None]
    return np.concatenate([tail * (1 - ramp) + head * ramp, body], axis=0)


def pan(mono, position):
    """position -1 (left) .. 1 (right), equal power."""
    angle = (position + 1) * np.pi / 4
    return np.stack([mono * np.cos(angle), mono * np.sin(angle)], axis=1)


def voice(seconds, f0, talkative):
    """One speaker: phrases of syllables on a glottal buzz shaped by vowel formants, with consonant noise; silent between phrases."""
    n = int(seconds * RATE)
    t = np.arange(n) / RATE
    # When they speak: phrases and pauses.
    speaking = np.zeros(n)
    syll_env = np.zeros(n)
    vowel_track = np.zeros((n, 3))
    consonant = np.zeros(n)
    pos = rng.uniform(0, 2)
    while pos < seconds:
        length = rng.uniform(.8, 3.5) if rng.random() < talkative else rng.uniform(.3, 1.0)
        a, b = int(pos * RATE), min(n, int((pos + length) * RATE))
        speaking[a:b] = 1
        s = pos
        while s < pos + length:
            d = rng.uniform(.14, .28)
            sa, sb = int(s * RATE), min(n, int((s + d) * RATE))
            if sa >= n:
                break
            k = np.arange(sb - sa)
            syll_env[sa:sb] = np.sin(np.pi * k / max(1, len(k))) ** .7 * rng.uniform(.6, 1.0)
            vowel_track[sa:sb] = VOWELS[rng.integers(len(VOWELS))]
            c = min(sb, sa + int(rng.uniform(.02, .06) * RATE))
            consonant[sa:c] = rng.uniform(.2, .6) if rng.random() < .6 else 0
            s += d
        pos += length + rng.exponential(1.6 / talkative)
    # Pitch: a slow wander and a fall through each phrase.
    pitch = f0 * (1 + .12 * np.sin(2 * np.pi * rng.uniform(.15, .4) * t + rng.uniform(0, 6)) + .05 * np.sin(2 * np.pi * 3.1 * t))
    phase = np.cumsum(pitch / RATE)
    buzz = (phase % 1.0) * 2 - 1                      # a sawtooth buzz, rich in harmonics
    buzz = lowpass(buzz, 3500)
    # Formants, frame by frame (overlap-add), following the vowel track.
    frame, hop = 1024, 512
    window = np.hanning(frame)
    freqs = np.fft.rfftfreq(frame, 1 / RATE)
    out = np.zeros(n + frame)
    for start in range(0, n - frame, hop):
        seg = buzz[start:start + frame] * window
        f1, f2, f3 = vowel_track[start + hop]
        if f1 == 0:
            continue
        g = (np.exp(-((freqs - f1) / 90) ** 2) + .7 * np.exp(-((freqs - f2) / 120) ** 2) + .35 * np.exp(-((freqs - f3) / 160) ** 2) + .02)
        out[start:start + frame] += np.fft.irfft(np.fft.rfft(seg) * g, frame)
    voiced = out[:n] * syll_env * speaking
    noise = highpass(rng.standard_normal(n), 2500) * consonant * speaking * .25
    return voiced + noise


def clink(n_samples, at, pitch=1.0):
    """A pewter mug knocked on another: a few high, quickly dying partials."""
    out = np.zeros(n_samples)
    length = int(.5 * RATE)
    t = np.arange(length) / RATE
    tone = sum(a * np.sin(2 * np.pi * f * pitch * t) * np.exp(-t * d) for f, a, d in ((1850, 1, 14), (3020, .6, 20), (4610, .4, 30), (6100, .2, 40)))
    a = int(at * RATE)
    b = min(n_samples, a + length)
    out[a:b] += tone[:b - a]
    return out


def murmur(seconds, voices, distance_cut, room, clinks, name):
    n = int(seconds * RATE)
    mix = np.zeros((n, 2))
    for k in range(voices):
        f0 = rng.choice([rng.uniform(95, 140), rng.uniform(170, 230)])
        v = voice(seconds, f0, rng.uniform(.45, .9))
        v = lowpass(v, distance_cut * rng.uniform(.6, 1.0)) * rng.uniform(.35, 1.0)
        mix += pan(v, rng.uniform(-.8, .8))
    for _ in range(clinks):
        c = clink(n, rng.uniform(0, seconds - 1), rng.uniform(.85, 1.2)) * rng.uniform(.15, .4)
        mix += pan(c, rng.uniform(-.7, .7))
    mix = reverb(mix, room, .35)
    write(name, loop(mix, 2.0))


def mallet(pitch=1.0):
    """A wooden mallet on a timber: a click, then the timber's body ringing briefly."""
    length = int(.4 * RATE)
    t = np.arange(length) / RATE
    body = sum(a * np.sin(2 * np.pi * f * pitch * t + rng.uniform(0, 6)) * np.exp(-t * d)
               for f, a, d in ((190, 1, 26), (430, .7, 34), (780, .45, 45), (1310, .3, 60), (2150, .15, 80)))
    click = highpass(rng.standard_normal(length), 1500) * np.exp(-t * 400) * .8
    return body + click


def saw_stroke(seconds):
    """One push and pull of a hand saw: rasping band of noise, louder in the middle of each stroke, its teeth chattering."""
    n = int(seconds * RATE)
    t = np.arange(n) / RATE
    rasp = bandpass(rng.standard_normal(n), 1100, 4200)
    teeth = 1 + .5 * np.sin(2 * np.pi * 95 * t)
    env = np.sin(np.pi * (t % (seconds / 2)) / (seconds / 2)) ** 1.5
    return rasp * teeth * env * .18


def shipyard(seconds, name):
    n = int(seconds * RATE)
    mix = np.zeros((n, 2))
    pos = .5
    while pos < seconds - 3:
        if rng.random() < .6:
            # A burst of mallet blows: steady strokes, one worker at one spot.
            where, pitch = rng.uniform(-.6, .6), rng.uniform(.85, 1.15)
            for k in range(rng.integers(4, 9)):
                m = mallet(pitch * rng.uniform(.97, 1.03)) * rng.uniform(.7, 1.0)
                a = int((pos + k * rng.uniform(.5, .62)) * RATE)
                b = min(n, a + len(m))
                mix[a:b] += pan(m[:b - a], where)
            pos += 8 * .56 + rng.uniform(.8, 2.5)
        else:
            # A cut with the saw: a run of strokes.
            strokes = rng.integers(4, 9)
            s = saw_stroke(strokes * .7)
            a = int(pos * RATE)
            b = min(n, a + len(s))
            mix[a:b] += pan(s[:b - a], rng.uniform(-.5, .5))
            pos += strokes * .7 + rng.uniform(1.0, 3.0)
    mix = reverb(mix, .9, .25)
    write(name, loop(mix, 1.5))


def pier_lapping(seconds, name):
    n = int(seconds * RATE)
    t = np.arange(n) / RATE
    swell = .6 + .4 * np.sin(2 * np.pi * t / 5.3) * np.sin(2 * np.pi * t / 2.1 + 1)
    base = lowpass(rng.standard_normal(n), 600) * swell * .5
    mix = pan(base, 0) * 1.0
    # Slaps against the piles: short, hollow, falling plops.
    pos = rng.uniform(0, .5)
    while pos < seconds - 1:
        length = int(rng.uniform(.12, .3) * RATE)
        k = np.arange(length) / RATE
        f = rng.uniform(140, 260) * np.exp(-k * 6)
        plop = np.sin(2 * np.pi * np.cumsum(f) / RATE) * np.exp(-k * 18)
        splash = lowpass(highpass(rng.standard_normal(length), 700), 3000) * np.exp(-k * 25) * .5
        a = int(pos * RATE)
        mix[a:a + length] += pan((plop + splash) * rng.uniform(.3, .9), rng.uniform(-.8, .8))
        pos += rng.uniform(.4, 1.8)
    mix = reverb(mix, .5, .2)
    write(name, loop(mix, 2.0))


def bell(name):
    """A ship's bronze bell struck twice: a bell's inharmonic partials, the hum lasting longest."""
    seconds = 6.0
    n = int(seconds * RATE)
    t = np.arange(n) / RATE
    f0 = 523.0
    partials = ((.5, .5, .35), (1.0, 1.0, .6), (1.19, .55, .8), (1.51, .45, 1.0), (2.0, .4, 1.3), (2.51, .3, 1.7), (2.66, .25, 1.9), (3.01, .2, 2.2), (4.1, .12, 3.0))
    strike = lambda tt: sum(a * np.sin(2 * np.pi * f0 * r * tt) * np.exp(-np.maximum(tt, 0) * d) * (tt >= 0) for r, a, d in partials)
    mono = strike(t - .05) + .9 * strike(t - .62)
    clang = highpass(rng.standard_normal(n), 3000) * (np.exp(-np.maximum(t - .05, 0) * 120) * (t >= .05) + np.exp(-np.maximum(t - .62, 0) * 120) * (t >= .62)) * .3
    mix = pan(mono + clang, 0)
    write(name, reverb(mix, 1.4, .3))


if __name__ == '__main__':
    murmur(26, 10, 2600, .7, 14, 'AMB_TavernMurmur-v1.wav')
    murmur(26, 6, 1700, .35, 0, 'AMB_MarketMurmur-v1.wav')
    shipyard(30, 'AMB_ShipyardWork-v1.wav')
    pier_lapping(24, 'AMB_PierLapping-v1.wav')
    bell('SFX_HarborBell-v1.wav')
