"""Make a draft ambience loop seamless: the last few seconds are cross-faded (equal power) into the first, so the
end runs straight into the start. Writes <name>-v2.wav beside <name>-v1.wav; the v1 source is kept unchanged.
    python Scripts/Art/make_audio_loops.py
"""
import math
import struct
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# Loop -> (seconds cross-faded, gain). The cave take came back very quiet, so it is raised here.
LOOPS = {
    'Art/Audio/Ambience/AMB_OceanSurf-v1.wav': (3.0, 1.0),
    'Art/Audio/Ambience/AMB_WinterWind-v1.wav': (3.0, 1.0),
    'Art/Audio/Ambience/AMB_NightInsects-v1.wav': (2.0, 1.0),
    'Art/Audio/Ambience/AMB_CaveDrips-v1.wav': (2.0, 8.0),
    'Art/Audio/Ships/AMB_HullCreak-v1.wav': (2.0, 1.0),
    'Art/Audio/Ships/AMB_Rigging-v1.wav': (2.0, 1.0),
}


def make_loop(source, fade_seconds, gain):
    with wave.open(str(source)) as w:
        channels, width, rate, frames = w.getnchannels(), w.getsampwidth(), w.getframerate(), w.getnframes()
        assert width == 2, 'expects 16-bit audio'
        data = struct.unpack(f'<{frames * channels}h', w.readframes(frames))
    fade = int(fade_seconds * rate)
    body = frames - fade
    out = [max(-32768, min(32767, round(v * gain))) for v in data[:body * channels]]
    for i in range(fade):
        t = i / fade
        rise, fall = math.sin(t * math.pi / 2), math.cos(t * math.pi / 2)
        for c in range(channels):
            head = data[i * channels + c]
            tail = data[(body + i) * channels + c]
            out[i * channels + c] = max(-32768, min(32767, round((head * rise + tail * fall) * gain)))
    target = source.with_name(source.name.replace('-v1.wav', '-v2.wav'))
    with wave.open(str(target), 'wb') as w:
        w.setnchannels(channels)
        w.setsampwidth(width)
        w.setframerate(rate)
        w.writeframes(struct.pack(f'<{len(out)}h', *out))
    return target, body / rate


if __name__ == '__main__':
    for loop, (fade_seconds, gain) in LOOPS.items():
        target, seconds = make_loop(ROOT / loop, fade_seconds, gain)
        print(f'{target.relative_to(ROOT).as_posix()}: {seconds:.2f} s')
