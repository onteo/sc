"""Bitiş ekranı sesi: alçak seviyede müzik + animasyona kilitli efektler (6 sn, 120 BPM).
Zamanlar end.html ile aynı. Kullanım: python3 sound.py -> audio.wav"""
import os
import sys
import numpy as np
from scipy.io import wavfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'animation'))
import synth  # noqa: E402
synth.set_duration(6.0)
from synth import *  # noqa: E402,F401,F403

SR, N = synth.SR, synth.N
music, sfx, send = Bus(), Bus(), Bus()
t_all = np.arange(N) / SR

# ---- alçak müzik: Cmaj7 → Am7 → Fmaj7 → G, yumuşak pluck + hafif davul ----
CH = [([48, 55, 59, 64], 36), ([45, 52, 55, 60], 33), ([41, 48, 52, 57], 29), ([43, 50, 55, 62], 31)]
for i, (ch, root) in enumerate(CH):
    a = i * 1.5
    p = pad(ch, 1.8, cutoff=2400, a=.3 if i == 0 else .05, r=.4)
    music.add(p, a, gain=.3)
    send.add(p, a, gain=.2)
    music.add(bass(root, .4), a, gain=.35)
    notes = [ch[0] + 12, ch[2] + 12, ch[3] + 12, ch[1] + 24]
    for j in range(6):
        pl = pluck(notes[j % 4], .3, bright=.75)
        music.add(pl, a + j * .25, gain=.06, pan=.3 * np.sin(j))
        send.add(pl, a + j * .25, gain=.04)
fin = pad([48, 52, 55, 59, 62], 1.2, cutoff=3000, a=.02, r=.8)
music.add(fin, 4.1, gain=.28)
drums = Bus()
for bt in np.arange(1.0, 5.5, .5):
    drums.add(kick(), bt, gain=.35)
    drums.add(hat(), bt + .25, gain=.18, pan=.2)
    if int(round(bt / .5)) % 2 == 1:
        drums.add(clap(), bt, gain=.15)

# ---- efektler ----
# logo: süzülme + darbe + çan
sfx.add(whoosh(.35, 400, 5000, gain=.3), -.1)
im = impact(.55)
sfx.add(im, .15, gain=.35)
send.add(im, .15, gain=.2)
c = chime(84, 1.4)
sfx.add(c, .18, gain=.22)
send.add(c, .18, gain=.3)
# yazı logonun arkasından kayar
sw = whoosh(.6, 600, 7000, gain=.3)
sfx.add(sw, .5)
send.add(sw, .5, gain=.25)
for i in range(11):
    sfx.add(tick(), .62 + i * .03, gain=.06)
# butonlar beliriyor
for i in range(3):
    b = blip(700 + i * 150, 1100 + i * 150, .07)
    sfx.add(b, 1.58 + i * .12, gain=.18)
# imleç gelişi
sfx.add(whoosh(.45, 300, 2000, gain=.12), 2.0)
# tıklamalar: klik + yükselen çan (adım adım)
for T, m in zip((2.5, 3.1, 3.7), (79, 84, 88)):
    sfx.add(tick(), T, gain=.5)
    sfx.add(np.sin(2 * np.pi * 180 * tt(.03)) * np.exp(-tt(.03) * 150), T, gain=.35)
    c = chime(m, 1.0)
    sfx.add(c, T + .03, gain=.2)
    send.add(c, T + .03, gain=.25)
    sfx.add(whoosh(.4, 1500, 4000, gain=.07), T + .08)     # ilerleme çizgisi dolar
# seviye yükselten: yukarı arpej
for i, m in enumerate([72, 76, 79, 84, 88, 91]):
    c = chime(m, .9)
    sfx.add(c, 4.12 + i * .06, gain=.1, pan=-.3 + i * .12)
    send.add(c, 4.12 + i * .06, gain=.15)
# logo parıltısı
sfx.add(whoosh(.6, 5000, 12000, gain=.1), 4.9)
c = chime(96, .8)
sfx.add(c, 5.2, gain=.06)
send.add(c, 5.2, gain=.12)

wet = reverb(send.x, 1.6)
mix = (music.x + drums.x * .8) * .45 + sfx.x + wet * .4
mix = filt(mix, 'highpass', 30)
mix *= np.clip((6.0 - t_all) / .5, 0, 1)
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
mix /= np.max(np.abs(mix)) / .9
wavfile.write(os.path.join(os.path.dirname(__file__), 'audio.wav'), SR, (mix.T * 32767).astype(np.int16))
print('ok')
