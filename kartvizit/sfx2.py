"""Baskı özellikleri bölümü sesleri (müzik yok). Zamanlar baski.html ile aynı (maddeler 2.0 + i*1.95 sn).
Kullanım: python3 sfx2.py -> sfx2.wav"""
import os
import sys
import numpy as np
from scipy.io import wavfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'animation'))
import synth  # noqa: E402
synth.set_duration(15.0)
from synth import *  # noqa: E402,F401,F403

SR, N = synth.SR, synth.N
sfx, send = Bus(), Bus()
tI = lambda i: 2.0 + i * 1.95

# başlık + kartvizit gelişi (ilk bölümle aynı karakter)
sfx.add(whoosh(.5, 800, 6000, gain=.25), .05)
for i in range(4):
    sfx.add(tick(), .14 + i * .07, gain=.12)
w = whoosh(.65, 250, 3500, gain=.45)
sfx.add(w, .45)
send.add(w, .45, gain=.3)
td = tt(.35)
thud = np.sin(2 * np.pi * np.cumsum(90 + 60 * np.exp(-td * 30)) / SR) * np.exp(-td * 14)
sfx.add(thud, 1.1, gain=.5)
send.add(thud, 1.1, gain=.2)

# her madde: tık + yükselen çan
for i, m in enumerate([84, 86, 88, 91, 93, 96]):
    t0 = tI(i)
    sfx.add(tick(), t0, gain=.45)
    sfx.add(np.sin(2 * np.pi * 220 * tt(.03)) * np.exp(-tt(.03) * 150), t0, gain=.3)
    c = chime(m, 1.0)
    sfx.add(c, t0 + .02, gain=.17, pan=-.25 + i * .1)
    send.add(c, t0 + .02, gain=.22)

# 1) kısmi lak: parıltı
for k in range(2):
    sfx.add(whoosh(.5, 5000, 12000, gain=.14), tI(0) + .1 + k * 1.3)
    c = chime(103, .6)
    sfx.add(c, tI(0) + .35 + k * 1.3, gain=.05)
    send.add(c, tI(0) + .35 + k * 1.3, gain=.1)
# 2) özel kenar: köşelerde tıklar
for j in range(6):
    b = blip(1500 + j * 120, 1100 + j * 120, .05)
    sfx.add(b, tI(1) + j * .06, gain=.12, pan=-.5 + j * .2)
# 3) gofre: pres
tp = tt(.4)
press = np.sin(2 * np.pi * np.cumsum(70 + 40 * np.exp(-tp * 25)) / SR) * np.exp(-tp * 10)
sfx.add(press, tI(2) + .08, gain=.5)
sfx.add(filt(noise(.08), 'lowpass', 1200) * np.exp(-tt(.08) * 50), tI(2) + .08, gain=.35)
# 4) yaldız: parıltılı çanlar
for j, m in enumerate([96, 100, 103, 108]):
    c = chime(m, .8)
    sfx.add(c, tI(3) + .15 + j * .07, gain=.07, pan=-.3 + j * .2)
    send.add(c, tI(3) + .15 + j * .07, gain=.14)
sfx.add(whoosh(.7, 6000, 12000, gain=.1), tI(3) + .1)
# 5) selefon: uzun yumuşak süzülme
sw = whoosh(1.2, 400, 5000, gain=.25)
sfx.add(sw, tI(4) + .1)
send.add(sw, tI(4) + .1, gain=.2)
# 6) özel kâğıt: hışırtı
r = np.random.default_rng(4)
rd = .6
rus = filt(noise(rd), 'bandpass', [2000, 8000]) * (r.random(int(rd * SR)) > .7) * np.sin(np.pi * tt(rd) / rd)
sfx.add(rus, tI(5) + .05, gain=.25)

wet = reverb(send.x, 1.4)
mix = sfx.x + wet * .45
t_all = np.arange(N) / SR
mix *= np.clip((15.0 - t_all) / .25, 0, 1)
mix /= np.max(np.abs(mix)) / .9
wavfile.write(os.path.join(os.path.dirname(__file__), 'sfx2.wav'), SR, (mix.T * 32767).astype(np.int16))
print('ok')
