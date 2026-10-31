"""Synthesize placeholder creature sounds (owner: free placeholder sounds until paid audio; M5: species-appropriate vocal and attack audio).
Plain Python with numpy, nothing sampled or downloaded. Writes 44.1 kHz stereo WAVs to Art/Audio/Fauna/:
  SFX_SpiderChitter-v1.wav  the cave spider's call: dry rapid clicking in bursts, a faint rasp under it
  SFX_SpiderHiss-v1.wav     its attack: a sharp rising hiss, then the mandibles snapping shut
  SFX_SpiderDeath-v1.wav    its death: a broken, slowing chitter that falls in pitch, and the body dropping
Every level is tuning; whether they sound right is for the owner's ear.
    python Scripts/Art/make_creature_sounds.py
"""
from pathlib import Path

import numpy as np

from make_town_sounds import RATE, bandpass, highpass, lowpass, pan, reverb, write as write_town

OUT = Path(__file__).resolve().parents[2] / 'Art' / 'Audio' / 'Fauna'
rng = np.random.default_rng(31)


def write(name, stereo):
    import make_town_sounds
    make_town_sounds.OUT = OUT
    write_town(name, stereo)


def click(length=.006, pitch=4200.0):
    """One chitin click: a tiny burst of bright noise with a short ring."""
    n = int(length * RATE)
    t = np.arange(n) / RATE
    burst = highpass(rng.standard_normal(n), 2500) * np.exp(-t * 900)
    ring = np.sin(2 * np.pi * pitch * t) * np.exp(-t * 1400) * .6
    return burst + ring


def place(track, sound, at):
    a = int(at * RATE)
    b = min(len(track), a + len(sound))
    if a < len(track):
        track[a:b] += sound[:b - a]


def chitter():
    seconds = 1.1
    track = np.zeros(int(seconds * RATE))
    pos = .03
    for burst in range(3):
        rate = rng.uniform(55, 80)          # clicks a second
        for k in range(int(rng.uniform(8, 14))):
            place(track, click(pitch=rng.uniform(3200, 5200)) * rng.uniform(.5, 1.0), pos + k / rate + rng.uniform(-.002, .002))
        pos += rng.uniform(.25, .35)
    rasp = bandpass(rng.standard_normal(len(track)), 1500, 4000) * .05 * (np.abs(track) > .05).astype(float)
    return reverb(pan(track + lowpass(rasp, 5000), 0), .25, .15)


def hiss():
    seconds = .75
    n = int(seconds * RATE)
    t = np.arange(n) / RATE
    env = np.clip(t / .12, 0, 1) * np.exp(-np.maximum(t - .35, 0) * 18)
    noise = bandpass(rng.standard_normal(n), 2000, 9000)
    sweep = 1 + .6 * np.clip(t / .3, 0, 1)
    breathy = noise * env * (.6 + .4 * np.sin(2 * np.pi * 34 * t * sweep))
    track = breathy * .55
    # The snap: two quick hard clicks as the fangs close.
    for at in (.36, .39):
        place(track, click(.01, 2400) * 1.4, at)
    return reverb(pan(track, 0), .2, .12)


def death():
    seconds = 1.6
    n = int(seconds * RATE)
    track = np.zeros(n)
    pos, gap = .02, 1 / 70
    while pos < 1.0:
        pitch = 4600 * (1 - pos * .55)
        place(track, click(pitch=pitch) * (1 - pos * .6) * rng.uniform(.5, 1.0), pos)
        gap *= rng.uniform(1.03, 1.09)        # slowing as it fails
        pos += gap
    # The body settles: a soft thump and legs scraping.
    t = np.arange(int(.4 * RATE)) / RATE
    thump = np.sin(2 * np.pi * 70 * t) * np.exp(-t * 18) * .8 + lowpass(rng.standard_normal(len(t)), 900) * np.exp(-t * 25) * .5
    place(track, thump, 1.05)
    scrape = bandpass(rng.standard_normal(int(.35 * RATE)), 1200, 3500) * np.linspace(.25, 0, int(.35 * RATE))
    place(track, scrape, 1.12)
    return reverb(pan(track, 0), .3, .15)


if __name__ == '__main__':
    write('SFX_SpiderChitter-v1.wav', chitter())
    write('SFX_SpiderHiss-v1.wav', hiss())
    write('SFX_SpiderDeath-v1.wav', death())
