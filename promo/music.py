"""
infoakademi uygulama tanıtımı — 21 sn özgün müzik + arayüz sesleri (sentez, telifsiz).
120 BPM, C majör; her dokunuş, bildirim, yoklama onayı ve mesaj animasyonla senkron.
Kullanım: python3 music.py -> ../audio/infoakademi-app-music.wav
"""
import os
import sys
import numpy as np
from scipy.io import wavfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'animation'))
import synth  # noqa: E402
synth.set_duration(21.0)
from synth import *  # noqa: E402,F401,F403

DUR = synth.DUR
N = synth.N
BEAT = 0.5

drums, music, sfx, send = Bus(), Bus(), Bus(), Bus()

# 2 sn'lik ölçüler: I – I – vi – IV – V – I – vi – IV – V – (final) I
BARS = [
    ([48, 55, 59, 64], 36), ([48, 55, 59, 64], 36), ([45, 52, 55, 60], 33), ([41, 48, 52, 57], 29),
    ([43, 50, 55, 59], 31), ([48, 55, 59, 64], 36), ([45, 52, 55, 60], 33), ([41, 48, 52, 57], 29),
    ([43, 50, 55, 62], 31),
]
for i, (ch, root) in enumerate(BARS):
    a, b = i * 2.0, i * 2.0 + 2.0
    if a >= 18.0:
        break
    b = min(b, 17.9)
    intro = a < 3.0
    p = pad(ch, b - a + 0.3, cutoff=1100 if intro else 2800, a=0.8 if i == 0 else 0.04, r=0.3)
    music.add(p, a, gain=0.5 if intro else 0.36)
    send.add(p, a, gain=0.22)
    if intro:
        t = tt(b - a)
        music.add(np.sin(2 * np.pi * mtof(root) * t) * np.minimum(1, t / 1.0) * 0.28, a)
    k = max(a, 3.0)
    while k < b - 1e-6:
        music.add(bass(root, 0.2), k + 0.25, gain=0.5)
        music.add(bass(root, 0.12), k, gain=0.25)
        k += BEAT
    # arpej
    notes = [ch[0] + 12, ch[2] + 12, ch[3] + 12, ch[1] + 24, ch[3] + 12, ch[2] + 12, ch[1] + 12, ch[2] + 12]
    k, j = a, 0
    while k < b - 1e-6:
        g = (0.1 + 0.05 * min(1, k / 3)) if intro else 0.12
        pl = pluck(notes[j % 8], 0.3, bright=0.6 if intro else 0.85)
        pan = 0.4 * np.sin(j * 0.8)
        music.add(pl, k, gain=g * (1.2 if j % 4 == 0 else 1), pan=pan)
        send.add(pl, k, gain=g * 0.45, pan=pan)
        k += BEAT / 4
        j += 1
# final
fp = pad([48, 52, 55, 59, 62], 3.0, cutoff=3400, a=0.02, r=1.4)
music.add(fp, 18.0, gain=0.5)
send.add(fp, 18.0, gain=0.5)
music.add(bass(24, 2.0), 18.0, gain=0.6)

# davul
for bt in np.arange(0, 42) * BEAT:
    if 3.0 <= bt < 17.5:
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
    elif 1.5 <= bt < 3.0:
        drums.add(hat(), bt + 0.25, gain=0.25, pan=0.2)
k, i = 17.5, 0
while k < 17.95:
    c = clap()
    g = 0.15 + 0.35 * (k - 17.5) / 0.45
    drums.add(c, k, gain=g, pan=0.15 * (-1) ** i)
    k += BEAT / 4 if k < 17.75 else BEAT / 8
    i += 1

# ---------- arayüz sesleri ----------
def tap(t0, g=1.0):
    sfx.add(tick(), t0, gain=0.35 * g)
    b = blip(1900, 1300, 0.05)
    sfx.add(b, t0, gain=0.14 * g)
    send.add(b, t0, gain=0.05 * g)


# intro: logo, kelime, uçuş, telefon
c = chime(84, 1.4)
sfx.add(c, 0.12, gain=0.2)
send.add(c, 0.12, gain=0.25)
sfx.add(blip(500, 1000, 0.12), 0.1, gain=0.25)
for i, m in enumerate([76, 79, 84]):
    sfx.add(chime(m, 0.8), 0.5 + i * 0.08, gain=0.06, pan=-0.3 + i * 0.3)
sfx.add(whoosh(0.8, 200, 3000, gain=0.35), 1.9)
send.add(whoosh(0.8, 200, 3000, gain=0.2), 1.9)
sfx.add(impact(0.5), 3.0, gain=0.3)
sfx.add(whoosh(0.35, 3000, 800, gain=0.15), 3.1)

TAPS = [3.75, 5.6, 7.95, 9.3, 10.05, 10.95, 12.35, 14.2, 15.0, 16.0, 17.05]
for t0 in TAPS:
    tap(t0)

# bildirim (iki notalı çan)
for t0, m in [(4.42, 88), (4.54, 93)]:
    c = chime(m, 1.0)
    sfx.add(c, t0, gain=0.22)
    send.add(c, t0, gain=0.2)
# modal aç/kapa
sfx.add(whoosh(0.45, 300, 2500, gain=0.3), 5.7)
sfx.add(whoosh(0.4, 2500, 300, gain=0.22), 9.4)
# konum sinyali
for t0 in (6.2, 7.5, 8.8):
    p = np.sin(2 * np.pi * 1318 * tt(0.6)) * np.exp(-tt(0.6) * 9)
    sfx.add(p, t0, gain=0.07)
    send.add(p, t0, gain=0.1)
# yoklama onayı: arpej + ışıltı
for i, m in enumerate([72, 76, 79, 84, 88]):
    c = chime(m, 1.4)
    sfx.add(c, 8.1 + i * 0.055, gain=0.16, pan=-0.4 + i * 0.2)
    send.add(c, 8.1 + i * 0.055, gain=0.2)
sfx.add(whoosh(0.9, 4000, 11000, gain=0.12), 8.15)
# sohbet
sfx.add(whoosh(0.4, 400, 3000, gain=0.28), 10.2)
rng2 = np.random.default_rng(3)
MSG_LEN = 30
for i in range(MSG_LEN):
    t0 = 11.15 + i * (1.0 / MSG_LEN) + rng2.uniform(-0.01, 0.01)
    sfx.add(tick(), t0, gain=0.12 + rng2.uniform(0, 0.06), pan=rng2.uniform(-0.2, 0.2))
sw = sweep(noise(0.25), 800, 5000, 'bandpass', 0.35) * np.sin(np.pi * tt(0.25) / 0.25)
sfx.add(sw, 12.4, gain=0.35)
sfx.add(blip(900, 1400, 0.08), 12.47, gain=0.2)
for t0, (a, b) in [(13.6, (784, 784)), (13.7, (1046, 1046))]:
    c = blip(a, b, 0.12)
    sfx.add(c, t0, gain=0.2)
    send.add(c, t0, gain=0.15)
# geri, videolar, sayfa
sfx.add(whoosh(0.4, 2500, 400, gain=0.22), 14.3)
sfx.add(whoosh(0.4, 400, 3000, gain=0.25), 15.1)
sfx.add(whoosh(0.45, 300, 2200, gain=0.25), 16.1)
for i in range(3):
    sfx.add(tick(), 16.5 + i * 0.09, gain=0.2)
c = chime(91, 1.0)
sfx.add(c, 17.55, gain=0.2)
send.add(c, 17.55, gain=0.2)
# yükselen gerilim + outro
rd = 1.0
rt = tt(rd)
riser = sweep(noise(rd), 500, 10000, 'bandpass', 0.3) * (rt / rd) ** 2
sfx.add(riser, 16.95, gain=0.3)
send.add(riser, 16.95, gain=0.15)
sfx.add(whoosh(0.5, 3000, 200, gain=0.25), 18.0)
im = impact(0.9)
sfx.add(im, 18.0, gain=0.5)
send.add(im, 18.0, gain=0.3)
sfx.add(kick(), 18.0, gain=0.7)
for t0, m in [(18.3, 84), (18.5, 88), (19.22, 91), (19.34, 96)]:
    c = chime(m, 1.4)
    sfx.add(c, t0, gain=0.14)
    send.add(c, t0, gain=0.2)

# ---------- miks ----------
t_all = np.arange(N) / synth.SR
sc = np.ones(N)
for bt in np.arange(0, 42) * BEAT:
    if 3.0 <= bt < 17.5:
        m = t_all >= bt
        sc[m] *= 1 - 0.5 * np.exp(-(t_all[m] - bt) / 0.11)
music.x *= sc
wet = reverb(send.x, 2.2)
mix = drums.x * 0.85 + music.x + sfx.x + wet * 0.55
mix = filt(mix, 'highpass', 28)
mix *= np.clip((DUR - t_all) / 0.8, 0, 1) ** 1.5
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
mix /= np.max(np.abs(mix)) / 0.93

outp = os.path.join(os.path.dirname(__file__), '..', 'audio', 'infoakademi-app-music.wav')
wavfile.write(outp, synth.SR, (mix.T * 32767).astype(np.int16))
print('ok', outp)
