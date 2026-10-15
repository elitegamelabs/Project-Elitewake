"""Make a draft ambience loop seamless: the last few seconds are cross-faded (equal power) into the first, so the
end runs straight into the start. Writes <name>-v2.wav beside <name>-v1.wav; the v1 source is kept unchanged.
    python Scripts/Art/make_audio_loops.py
"""
import math
import struct
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LOOPS = ['Art/Audio/Ambience/AMB_OceanSurf-v1.wav', 'Art/Audio/Ambience/AMB_WinterWind-v1.wav']
FADE_SECONDS = 3.0


def make_loop(source):
    with wave.open(str(source)) as w:
        channels, width, rate, frames = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        assert width == 2, 'expects 16-bit audio'
        data = struct.unpack(f'<{frames * channels}h', w.readframes(frames))
    fade = int(FADE_SECONDS * rate)
    body = frames - fade
    out = list(data[:body * channels])
    for i in range(fade):
        t = i / fade
        rise, fall = math.sin(t * math.pi / 2), math.cos(t * math.pi / 2)
        for c in range(channels):
            head = data[i * channels + c]
            tail = data[(body + i) * channels + c]
            out[i * channels + c] = max(-32768, min(32767, round(head * rise + tail * fall)))
    target = source.with_name(source.name.replace('-v1.wav', '-v2.wav'))
    with wave.open(str(target), 'wb') as w:
        w.setnchannels(channels)
        w.setsampwidth(width)
        w.setframerate(rate)
        w.writeframes(struct.pack(f'<{len(out)}h', *out))
    return target, body / rate


if __name__ == '__main__':
    for loop in LOOPS:
        target, seconds = make_loop(ROOT / loop)
        print(f'{target.relative_to(ROOT).as_posix()}: {seconds:.2f} s')
