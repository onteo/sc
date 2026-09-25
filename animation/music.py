"""
infoakademi — 15 sn özgün müzik + ses efektleri (tamamen sentez, telifsiz).

120 BPM. Akorlar sahnelerle birlikte değişir (her sahne 2.5 sn = 5 vuruş):
  çizgi Fmaj7 · tipografi G6 · renk Am7 · kompozisyon Em7 · eğitim F → G · logo Cmaj9
Efektler animasyondaki olaylara kare hassasiyetinde bağlanmıştır.

Kullanım:  python3 music.py  ->  ../audio/infoakademi-music.wav (48 kHz, stereo)
"""
import os
import numpy as np
import synth
synth.set_duration(15.0)
from synth import *  # noqa: F401,F403
from scipy.io import wavfile

# ---------------- aranje ----------------
drums, music, sfx, send = Bus(), Bus(), Bus(), Bus()

# sahne akorları (MIDI)
SCENES = [
    (0.0, 2.5, [53, 57, 60, 64], 41),     # Fmaj7
    (2.5, 5.0, [55, 59, 62, 64], 43),     # G6
    (5.0, 7.5, [57, 60, 64, 67], 45),     # Am7
    (7.5, 10.0, [52, 55, 59, 62], 40),    # Em7
    (10.0, 11.25, [53, 57, 60, 64], 41),  # Fmaj7
    (11.25, 12.4, [55, 59, 62, 65], 43),  # G7
]
FINAL = [48, 55, 59, 62, 64]              # Cmaj9

for a, b, ch, root in SCENES:
    intro = a < 2.5
    p = pad(ch, b - a + 0.35, cutoff=900 if intro else 2600, a=0.6 if intro else 0.05, r=0.3)
    music.add(p, a, gain=0.55 if intro else 0.42)
    send.add(p, a, gain=0.25)
    # bas: 8'lik vuruş arası (kick'e yer açar), girişte uzun sub
    if intro:
        t = tt(b - a)
        sub = np.sin(2 * np.pi * mtof(root - 12) * t) * np.minimum(1, t / 1.2) * 0.35
        music.add(sub, a)
    else:
        k = a
        while k < b - 1e-6:
            music.add(bass(root - 12, 0.2), k + 0.25, gain=0.55)
            k += BEAT
    # arpej: 16'lık, akor sesleri + oktav
    arp_notes = [ch[0] + 12, ch[1] + 12, ch[2] + 12, ch[3] + 12, ch[2] + 24, ch[3] + 12, ch[1] + 12, ch[2] + 12]
    k, i = a, 0
    while k < b - 1e-6:
        g = 0.16 if intro else 0.13
        if intro:
            g *= min(1, 0.35 + k / 2.0)
        acc = 1.25 if i % 4 == 0 else 1.0
        pl = pluck(arp_notes[i % 8], 0.3, bright=0.55 if intro else 0.9)
        pan = 0.35 * np.sin(i * 0.9)
        music.add(pl, k, gain=g * acc, pan=pan)
        send.add(pl, k, gain=g * 0.5, pan=pan)
        k += BEAT / 4
        i += 1

# final: Cmaj9 + harf harf yükselen notalar
fp = pad(FINAL, 2.6, cutoff=3200, a=0.02, r=1.2)
music.add(fp, 12.5, gain=0.5)
send.add(fp, 12.5, gain=0.5)
music.add(bass(36, 1.8), 12.5, gain=0.7)
scale = [72, 74, 76, 79, 81, 84, 86, 88, 91, 93, 96]   # C pentatonik, 11 harf = 11 nota
for i, m in enumerate(scale):
    c = chime(m, 1.2)
    t0 = 12.5 + 0.22 + i * 0.045 + 0.06
    music.add(c, t0, gain=0.07, pan=-0.5 + i / 10)
    send.add(c, t0, gain=0.08)

# ---------------- davul ----------------
beats = np.arange(0, 30) * BEAT
for bt in beats:
    if 2.5 <= bt < 11.5:
        drums.add(kick(), bt, gain=0.9)
        idx = int(round(bt / BEAT))
        if idx % 2 == 1:
            c = clap()
            drums.add(c, bt, gain=0.55)
            send.add(c, bt, gain=0.25)
        drums.add(hat(), bt + 0.25, gain=0.55, pan=0.25)
        drums.add(hat(), bt + 0.125, gain=0.18, pan=-0.2)
        drums.add(hat(), bt + 0.375, gain=0.18, pan=-0.2)
        if idx % 4 == 3:
            drums.add(hat(True), bt + 0.25, gain=0.35, pan=0.3)
    elif 1.0 <= bt < 2.5:
        drums.add(hat(), bt, gain=0.25, pan=0.25)
        drums.add(hat(), bt + 0.25, gain=0.35, pan=-0.25)
# 11.5 – 12.4 clap rulosu
k, i = 11.5, 0
while k < 12.38:
    c = clap()
    g = 0.18 + 0.4 * (k - 11.5) / 0.9
    drums.add(c, k, gain=g, pan=0.15 * (-1) ** i)
    send.add(c, k, gain=g * 0.4)
    k += BEAT / 4 if k < 12.0 else BEAT / 8
    i += 1

# ---------------- efektler (animasyona senkron) ----------------
# S1 — ızgara + kalem anchor'ları
sfx.add(blip(1400, 700, 0.12), 0.0, gain=0.25)
for t0, m in zip([0.22, 0.79, 0.95, 1.55], [84, 88, 91, 96]):
    b = blip(mtof(m), mtof(m) * 0.98, 0.09)
    sfx.add(b, t0, gain=0.22, pan=-0.6 + t0 / 1.3)
    send.add(b, t0, gain=0.15)
sfx.add(sweep(noise(1.3) * np.sin(np.pi * tt(1.3) / 1.3) ** 2, 600, 3500, 'bandpass', 0.25), 0.25, gain=0.06)  # kalem sürtünmesi
# sahne geçişleri: whoosh + darbe
for cut, d, f0, f1 in [(2.5, 0.45, 250, 5000), (5.0, 0.5, 400, 8000), (7.5, 0.45, 200, 4000), (10.0, 0.5, 150, 7000)]:
    w = whoosh(d, f0, f1)
    sfx.add(w, cut - d, gain=0.5)
    send.add(w, cut - d, gain=0.25)
    im = impact(0.8)
    sfx.add(im, cut, gain=0.45)
    send.add(im, cut, gain=0.2)
    sfx.add(whoosh(0.5, f1, f0, rev=True), cut, gain=0.18)
# S2 — stil etiketleri
for i in range(4):
    sfx.add(tick(), 2.5 + 0.6 + i * 0.07, gain=0.35, pan=-0.4 + i * 0.25)
sfx.add(blip(900, 1300, 0.06), 2.95, gain=0.15)   # seçim kutusu
# S3 — örnek daireler + hex değişimi
for i in range(5):
    b = blip(mtof(79 + [0, 2, 4, 7, 9][i]) * 0.8, mtof(79 + [0, 2, 4, 7, 9][i]), 0.08)
    sfx.add(b, 5.45 + i * 0.06, gain=0.2, pan=-0.5 + i * 0.25)
for k in range(1, 5):
    for j in range(3):
        sfx.add(tick(), 5.45 + k * 0.33 + j * 0.035, gain=0.3, pan=0.3)
# S4 — afiş
sfx.add(blip(500, 900, 0.1), 7.5 + 0.22, gain=0.25)        # daire belirir
sfx.add(whoosh(0.45, 900, 2500, gain=0.35), 7.5 + 0.3)        # sürükleme
sfx.add(snap(), 7.5 + 0.88, gain=0.55)                        # yerine oturma
send.add(snap(), 7.5 + 0.88, gain=0.2)
sfx.add(blip(1200, 1600, 0.06), 7.5 + 0.9, gain=0.18)        # kılavuz
sfx.add(blip(700, 1100, 0.08), 7.5 + 0.72, gain=0.2, pan=-0.4)  # lime kare
sfx.add(filt(noise(0.2), 'lowpass', 600) * np.exp(-tt(0.2) * 20), 7.5 + 0.55, gain=0.5)  # blok
sfx.add(whoosh(0.5, 200, 9000, gain=0.35), 7.5 + 2.0)        # zoom
# S5 — özellik hapları
for i in range(4):
    sfx.add(blip(mtof(76 + [0, 3, 7, 12][i]), mtof(76 + [0, 3, 7, 12][i]) * 1.02, 0.08), 10.0 + 0.8 + i * 0.12, gain=0.2, pan=0.3)
    sfx.add(tick(), 10.0 + 0.58 + i * 0.12, gain=0.25, pan=-0.3)
# 11.2 – 12.4 yükselen gerilim
rd = 1.2
rt = tt(rd)
riser = sweep(noise(rd), 500, 11000, 'bandpass', 0.3) * (rt / rd) ** 2
riser += np.sin(2 * np.pi * np.cumsum(220 * 4 ** (rt / rd)) / SR) * (rt / rd) ** 3 * 0.12
sfx.add(riser, 11.2, gain=0.4)
send.add(riser, 11.2, gain=0.2)
# S6 — logo
im = impact(1.0)
sfx.add(im, 12.5, gain=0.6)
send.add(im, 12.5, gain=0.35)
sfx.add(kick(), 12.5, gain=0.8)
sfx.add(whoosh(0.5, 400, 2500, gain=0.3), 12.5)                      # nokta zıplar
for t0, m, pan in [(13.0, 84, -0.3), (13.24, 88, 0.35)]:            # nokta iniş (lime, mercan)
    c = chime(m, 1.6)
    sfx.add(c, t0, gain=0.3, pan=pan)
    send.add(c, t0, gain=0.3)
for t0, g in [(13.36, 0.12), (13.44, 0.06)]:                        # mercan noktanın sekmeleri
    sfx.add(chime(88, 0.5), t0, gain=g, pan=0.35)
sfx.add(whoosh(0.65, 2000, 9000, gain=0.12), 13.55)                  # alt çizgi
c = blip(900, 1500, 0.09)
sfx.add(c, 14.05, gain=0.3)                                           # kayıtlar açık
send.add(c, 14.05, gain=0.25)
c = chime(91, 1.0)
sfx.add(c, 14.1, gain=0.12)
send.add(c, 14.1, gain=0.15)

# ---------------- miks ----------------
# sidechain: kick vuruşlarında müzik "nefes alır"
sc = np.ones(N)
t_all = np.arange(N) / SR
for bt in beats:
    if 2.5 <= bt < 11.5:
        m = t_all >= bt
        sc[m] *= 1 - 0.55 * np.exp(-(t_all[m] - bt) / 0.11)
music.x *= sc

wet = reverb(send.x, 2.4)
mix = drums.x * 0.9 + music.x + sfx.x + wet * 0.6
mix = filt(mix, 'highpass', 28)
# yumuşak bitiş
fade = np.clip((DUR - t_all) / 0.6, 0, 1) ** 1.5
mix *= fade
# glue + limiter
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
mix /= np.max(np.abs(mix)) / 0.93

os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'audio'), exist_ok=True)
outp = os.path.join(os.path.dirname(__file__), '..', 'audio', 'infoakademi-music.wav')
wavfile.write(outp, SR, (mix.T * 32767).astype(np.int16))
print('ok', outp)
