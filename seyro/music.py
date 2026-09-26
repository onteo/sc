"""
Seyro tanıtımı — 23 sn özgün müzik + arayüz sesleri (sentez, telifsiz).
120 BPM. Karaoke satırlarında her kelimeye bir nota düşer (ekrandaki yeşil dolguyla senkron).
Kullanım: python3 music.py -> ../audio/seyro-music.wav
"""
import os
import sys
import numpy as np
from scipy.io import wavfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'animation'))
import synth  # noqa: E402
synth.set_duration(23.0)
from synth import *  # noqa: E402,F401,F403

DUR, N, SR = synth.DUR, synth.N, synth.SR
BEAT = 0.5
drums, music, sfx, send = Bus(), Bus(), Bus(), Bus()

# 2 sn'lik ölçüler: Am F | C G Am F C G Am | (düşüş) | C
BARS = [([45, 52, 57, 60], 33), ([41, 48, 53, 57], 29), ([48, 55, 60, 64], 36), ([43, 50, 55, 59], 31),
        ([45, 52, 57, 60], 33), ([41, 48, 53, 57], 29), ([48, 55, 60, 64], 36), ([43, 50, 55, 59], 31),
        ([45, 52, 57, 60], 33), ([41, 48, 53, 57], 29)]
DRUM_A, DRUM_B = 4.0, 19.7
for i, (ch, root) in enumerate(BARS):
    a, b = i * 2.0, min(i * 2.0 + 2.0, 19.9)
    if a >= b:
        break
    intro = a < DRUM_A
    p = pad(ch, b - a + 0.3, cutoff=1000 if intro else 2600, a=0.9 if i == 0 else 0.05, r=0.3)
    music.add(p, a, gain=0.5 if intro else 0.34)
    send.add(p, a, gain=0.22)
    t = tt(b - a)
    if intro:
        music.add(np.sin(2 * np.pi * mtof(root) * t) * np.minimum(1, t / .8) * 0.25, a)
    k = max(a, DRUM_A)
    while k < b - 1e-6:
        music.add(bass(root, 0.2), k + 0.25, gain=0.5)
        music.add(bass(root, 0.12), k, gain=0.22)
        k += BEAT
    notes = [ch[0] + 12, ch[2] + 12, ch[3] + 12, ch[1] + 24, ch[3] + 12, ch[2] + 12, ch[1] + 12, ch[2] + 12]
    k, j = a, 0
    while k < b - 1e-6:
        g = 0.08 if intro else 0.09
        if 9.4 <= k < 15.5:
            g *= 0.6                                 # karaoke'de melodiye yer aç
        pl = pluck(notes[j % 8], 0.28, bright=0.6 if intro else 0.85)
        pan = 0.4 * np.sin(j * 0.8)
        music.add(pl, k, gain=g, pan=pan)
        send.add(pl, k, gain=g * 0.45, pan=pan)
        k += BEAT / 4
        j += 1

# ---- melodi: sözlerin her kelimesine bir nota ----
LINES = [
    ('Sing it laud, sing it fri', [67, 67, 69, 67, 72, 71]),
    ('Evri vörd bilongz tu mi', [69, 69, 71, 72, 76]),
    ('Törn it ap end let it go', [72, 72, 74, 72, 71, 69, 67]),
    ('Nav aym singing on may ovn', [67, 69, 71, 72, 71, 69]),
    ('Fiil dı myuzik, fiil dı biit', [72, 72, 76, 74, 72, 71]),
    ('Densing davn dı siti striit', [69, 71, 72, 74, 72]),
]
L0, LD = 9.5, 1.0


def lead(m, d):
    t = tt(d)
    s = pluck(m, d, bright=1.0) * 0.7 + np.sin(2 * np.pi * mtof(m) * t) * np.exp(-t * 3) * 0.5
    return s * adsr(d, 0.004, 0.08)


for li, (line, mel) in enumerate(LINES):
    n = len(mel)
    for wi, m in enumerate(mel):
        t0 = L0 + li * LD + 0.08 + wi * 0.86 / n
        d = 0.86 / n * 0.95
        s = lead(m, d + 0.12)
        music.add(s, t0, gain=0.3, pan=0.05)
        send.add(s, t0, gain=0.25)
# kanca: İngilizce → okunuş dönüşümü, ikinci satırın melodisi
for i, m in enumerate(LINES[1][1]):
    s = lead(m, 0.3)
    music.add(s, 1.15 + i * 0.17, gain=0.26)
    send.add(s, 1.15 + i * 0.17, gain=0.3)

# final
fp = pad([48, 52, 55, 59, 62], 2.8, cutoff=3400, a=0.02, r=1.4)
music.add(fp, 20.2, gain=0.5)
send.add(fp, 20.2, gain=0.5)
music.add(bass(24, 2.0), 20.2, gain=0.6)
for i, m in enumerate([72, 76, 79, 84]):
    c = chime(m, 1.4)
    music.add(c, 20.55 + i * 0.09, gain=0.1)
    send.add(c, 20.55 + i * 0.09, gain=0.2)

# ---- davul ----
for bt in np.arange(0, 46) * BEAT:
    if DRUM_A <= bt < DRUM_B:
        drums.add(kick(), bt, gain=0.85)
        idx = int(round(bt / BEAT))
        if idx % 2 == 1:
            c = clap()
            drums.add(c, bt, gain=0.45)
            send.add(c, bt, gain=0.2)
        drums.add(hat(), bt + 0.25, gain=0.5, pan=0.25)
        drums.add(hat(), bt + 0.125, gain=0.15, pan=-0.2)
        drums.add(hat(), bt + 0.375, gain=0.15, pan=-0.2)
        if idx % 4 == 3:
            drums.add(hat(True), bt + 0.25, gain=0.3, pan=0.3)
    elif 2.5 <= bt < DRUM_A:
        drums.add(hat(), bt + 0.25, gain=0.22, pan=0.2)
k, i = 19.7, 0
while k < 20.15:
    c = clap()
    drums.add(c, k, gain=0.15 + 0.35 * (k - 19.7) / 0.45, pan=0.15 * (-1) ** i)
    k += BEAT / 4 if k < 19.95 else BEAT / 8
    i += 1

# ---- arayüz sesleri ----
def tap(t0):
    sfx.add(tick(), t0, gain=0.35)
    b = blip(1900, 1300, 0.05)
    sfx.add(b, t0, gain=0.14)


for t0 in (4.4, 5.6, 15.0, 15.35, 16.05, 18.2):
    tap(t0)
im = impact(0.5)
sfx.add(im, 2.3, gain=0.3)
send.add(im, 2.3, gain=0.2)
c = chime(84, 1.2)
sfx.add(c, 2.3, gain=0.18)
send.add(c, 2.3, gain=0.25)
sfx.add(whoosh(0.7, 200, 3000, gain=0.3), 2.95)
sfx.add(whoosh(0.4, 400, 3000, gain=0.25), 4.5)
sfx.add(whoosh(0.5, 300, 2500, gain=0.22), 5.9)
for t0 in (6.4, 7.1, 7.8):  # dinleme sinyali
    p = np.sin(2 * np.pi * 1318 * tt(0.5)) * np.exp(-tt(0.5) * 10)
    sfx.add(p, t0, gain=0.06)
    send.add(p, t0, gain=0.1)
for t0, m in [(8.02, 84), (8.12, 91)]:  # şarkı bulundu
    c = chime(m, 1.2)
    sfx.add(c, t0, gain=0.2)
    send.add(c, t0, gain=0.25)
sfx.add(whoosh(0.45, 300, 4000, gain=0.25), 8.85)
for i in range(12):
    sfx.add(tick(), 15.45 + i * 0.4 / 12, gain=0.14, pan=0.1)
rd = 1.1
rise = sweep(noise(rd), 800, 6000, 'bandpass', 0.3) * (tt(rd) / rd) ** 2
sfx.add(rise, 16.45, gain=0.1)
c = chime(88, 1.0)
sfx.add(c, 17.6, gain=0.18)
send.add(c, 17.6, gain=0.2)
for i in range(10):
    sfx.add(tick(), 18.55 + i * 0.1, gain=0.12 * (1 - i / 12))
rd = 0.9
rt = tt(rd)
riser = sweep(noise(rd), 500, 10000, 'bandpass', 0.3) * (rt / rd) ** 2
sfx.add(riser, 19.3, gain=0.3)
send.add(riser, 19.3, gain=0.15)
im = impact(0.9)
sfx.add(im, 20.2, gain=0.5)
send.add(im, 20.2, gain=0.3)
sfx.add(kick(), 20.2, gain=0.7)
sfx.add(whoosh(0.5, 3000, 200, gain=0.2), 20.2)
c = blip(900, 1500, 0.09)
sfx.add(c, 21.3, gain=0.25)
send.add(c, 21.3, gain=0.2)

# ---- miks ----
t_all = np.arange(N) / SR
sc = np.ones(N)
for bt in np.arange(0, 46) * BEAT:
    if DRUM_A <= bt < DRUM_B:
        m = t_all >= bt
        sc[m] *= 1 - 0.5 * np.exp(-(t_all[m] - bt) / 0.11)
music.x *= sc
wet = reverb(send.x, 2.2)
mix = drums.x * 0.85 + music.x + sfx.x + wet * 0.55
mix = filt(mix, 'highpass', 28)
mix *= np.clip((DUR - t_all) / 0.8, 0, 1) ** 1.5
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
mix /= np.max(np.abs(mix)) / 0.93
outp = os.path.join(os.path.dirname(__file__), '..', 'audio', 'seyro-music.wav')
wavfile.write(outp, SR, (mix.T * 32767).astype(np.int16))
print('ok', outp)
