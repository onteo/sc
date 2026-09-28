"""Kartvizit bölümü sesleri (müzik yok): başlık süzülmesi, kartvizit gelişi, her maddede tık + çan.
Zamanlar kartvizit.html ile aynı. Kullanım: python3 sfx.py -> sfx.wav"""
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

# başlık: yumuşak süzülme + kelime tıkları
sfx.add(whoosh(.5, 800, 6000, gain=.25), .05)
for i in range(5):
    sfx.add(tick(), .14 + i * .065, gain=.12)
# kartvizit gelişi: kağıt süzülmesi + yumuşak oturma
w = whoosh(.6, 250, 3500, gain=.45)
sfx.add(w, .5)
send.add(w, .5, gain=.3)
td = tt(.35)
thud = np.sin(2 * np.pi * np.cumsum(90 + 60 * np.exp(-td * 30)) / SR) * np.exp(-td * 14)
paper = filt(noise(.12), 'bandpass', [1500, 6000]) * np.exp(-tt(.12) * 40)
sfx.add(thud, 1.05, gain=.55)
sfx.add(paper, 1.05, gain=.3)
send.add(thud, 1.05, gain=.2)
# parıltı
sfx.add(whoosh(.55, 4000, 11000, gain=.1), 1.15)
c = chime(96, .9)
sfx.add(c, 1.35, gain=.06)
send.add(c, 1.35, gain=.1)
# maddeler: tık + yükselen çan (C E G A C)
for i, m in enumerate([84, 88, 91, 93, 96]):
    t0 = 2.0 + i * 2.4
    sfx.add(tick(), t0, gain=.45)
    sfx.add(np.sin(2 * np.pi * 220 * tt(.03)) * np.exp(-tt(.03) * 150), t0, gain=.3)
    c = chime(m, 1.1)
    sfx.add(c, t0 + .02, gain=.2, pan=-.2 + i * .1)
    send.add(c, t0 + .02, gain=.25)
    sfx.add(whoosh(.25, 1500, 5000, gain=.08), t0 + .05)

wet = reverb(send.x, 1.4)
mix = sfx.x + wet * .45
t_all = np.arange(N) / SR
mix *= np.clip((15.0 - t_all) / .25, 0, 1)
mix /= np.max(np.abs(mix)) / .9
wavfile.write(os.path.join(os.path.dirname(__file__), 'sfx.wav'), SR, (mix.T * 32767).astype(np.int16))
print('ok')
