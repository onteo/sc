"""
Konuşan kişi Reels'i için ses: temizlenmiş konuşma + alçak müzik (konuşmada kısılır) + senkron efektler.
Zamanlar edit.html'deki animasyonlarla aynı (kesilmiş zaman çizelgesi).
Kullanım: python3 music.py -> work/mix.wav
"""
import os
import sys
import numpy as np
from scipy.io import wavfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'animation'))
import synth  # noqa: E402
synth.set_duration(25.0)
from synth import *  # noqa: E402,F401,F403

DUR, N, SR = synth.DUR, synth.N, synth.SR
HERE = os.path.dirname(__file__)
t_all = np.arange(N) / SR
music, sfx, send = Bus(), Bus(), Bus()

# ---- konuşma ----
sr, v = wavfile.read(os.path.join(HERE, 'work', 'voice.wav'))
v = v.astype(np.float64) / 32768.0
if v.ndim > 1:
    v = v.mean(axis=1)
if sr != SR:
    v = np.interp(np.arange(int(len(v) * SR / sr)) / SR, np.arange(len(v)) / sr, v)
voice = np.zeros(N)
voice[:min(N, len(v))] = v[:N]
act = voice[np.abs(voice) > 0.01]
voice *= 0.2 / (np.sqrt(np.mean(act ** 2)) + 1e-9)   # konuşma seviyesini sabitle

# konuşma zarfı → müzik kısma (ducking)
env = np.abs(voice)
k = int(0.12 * SR)
env = np.convolve(env, np.ones(k) / k, mode='same')
duck = 1 - 0.72 * np.clip(env / 0.05, 0, 1)
duck = np.convolve(duck, np.ones(k) / k, mode='same')

# ---- müzik (120 BPM, sakin pop) ----
BEAT = 0.5
PROG = [([48, 55, 59, 64], 36), ([45, 52, 55, 60], 33), ([41, 48, 52, 57], 29), ([43, 50, 55, 59], 31)]
for bar in range(12):
    a = bar * 2.0
    if a >= 23.5:
        break
    ch, root = PROG[bar % 4]
    b = min(a + 2.0, 23.5)
    p = pad(ch, b - a + .3, cutoff=2200, a=.05 if bar else 1.0, r=.3)
    music.add(p, a, gain=.3)
    send.add(p, a, gain=.15)
    kk = a
    while kk < b - 1e-6:
        music.add(bass(root, .2), kk + .25, gain=.35)
        kk += BEAT
    notes = [ch[0] + 12, ch[2] + 12, ch[3] + 12, ch[1] + 24, ch[3] + 12, ch[2] + 12, ch[1] + 12, ch[2] + 12]
    kk, j = a, 0
    while kk < b - 1e-6:
        pl = pluck(notes[j % 8], .26, bright=.7)
        music.add(pl, kk, gain=.07, pan=.4 * np.sin(j * .8))
        send.add(pl, kk, gain=.04)
        kk += BEAT / 4
        j += 1
drums = Bus()
for bt in np.arange(0, 50) * BEAT:
    if 1.0 <= bt < 23.4:
        drums.add(kick(), bt, gain=.55)
        if int(round(bt / BEAT)) % 2 == 1:
            drums.add(clap(), bt, gain=.25)
        drums.add(hat(), bt + .25, gain=.3, pan=.25)
fin = pad([48, 52, 55, 59, 62], 1.6, cutoff=3200, a=.02, r=1.0)
music.add(fin, 23.55, gain=.45)
send.add(fin, 23.55, gain=.4)
music.add(bass(24, 1.4), 23.55, gain=.5)

# ---- efektler ----
def pop(t0, f=900, g=.22):
    b = blip(f, f * 1.6, .08)
    sfx.add(b, t0, gain=g)
    send.add(b, t0, gain=g * .5)


def mclick(t0, g=.5):
    sfx.add(tick(), t0, gain=.4 * g)
    sfx.add(np.sin(2 * np.pi * 180 * tt(.03)) * np.exp(-tt(.03) * 150), t0, gain=.35 * g)


def swish(t0, d=.3, f0=600, f1=5000, g=.3):
    w = whoosh(d, f0, f1, gain=g)
    sfx.add(w, t0, gain=1)
    send.add(w, t0, gain=.4)


def keys(a, b, n, g=.2, seed=1):
    r = np.random.default_rng(seed)
    for i in range(n):
        tp = a + i * (b - a) / n + r.uniform(-.01, .01)
        sfx.add(tick(), tp, gain=g * r.uniform(.7, 1.1), pan=r.uniform(-.2, .2))
        sfx.add(np.sin(2 * np.pi * 240 * tt(.02)) * np.exp(-tt(.02) * 200), tp, gain=g * .8)


# giriş: yanan sayfa çıtırtısı + zoom
d = 1.3
r = np.random.default_rng(5)
cr = np.zeros(int(d * SR))
for _ in range(260):
    i = r.integers(0, len(cr) - 400)
    cr[i:i + 300] += filt(r.standard_normal(300), 'bandpass', [1500, 7000]) * np.exp(-np.arange(300) / 40) * r.uniform(.2, 1)
env_c = np.sin(np.pi * np.clip(tt(d) / d, 0, 1)) ** 1.5
rumble = filt(noise(d), 'lowpass', 400) * .5 + sweep(noise(d), 300, 2500, 'bandpass', .5) * .4
sfx.add((cr * .5 + rumble) * env_c, 0.0, gain=.35)
send.add(cr * env_c, 0.0, gain=.15)
swish(.02, .45, 300, 4000, .35)
sfx.add(impact(.35), .5, gain=.25)
swish(1.5, .5, 4000, 300, .28)
# arka dev yazılar
for t0 in (.1, .36, 3.86, 4.62, 5.1, 12.02):
    swish(t0 - .05, .28, 800, 6000, .22)
    sfx.add(np.sin(2 * np.pi * 70 * tt(.25)) * np.exp(-tt(.25) * 14), t0 + .12, gain=.35)
# vurgulu kelimeler
for t0 in (1.16, 3.45, 7.0, 8.85, 11.6, 13.75):
    pop(t0, 1100, .14)
# soru işaretleri, Aa, renkler, ızgara
for t0, f in ((2.12, 700), (2.55, 900), (3.2, 800)):
    pop(t0, f, .25)
pop(3.95, 600, .22)
for i in range(5):
    pop(4.66 + i * .05, 500 + i * 120, .2)
swish(5.12, .35, 2000, 9000, .15)
mclick(5.25)
# editör
swish(5.9, .35, 300, 5000, .35)
mclick(6.55)
mclick(7.0)
keys(7.05, 7.75, 13, .22)
pop(7.9, 800, .18)
# portfolyo
swish(8.25, .35, 300, 5000, .35)
swish(8.62, .3, 1500, 4000, .2)
swish(9.08, .35, 400, 5000, .3)
for i in range(3):
    pop(9.85 + i * .1, 600 + i * 200, .2)
swish(10.72, .3, 5000, 400, .3)
# sertifika + damga
pop(11.15, 500, .25)
for i, m in enumerate([84, 88, 91]):
    c = chime(m, 1.0)
    sfx.add(c, 11.4 + i * .06, gain=.12)
    send.add(c, 11.4 + i * .06, gain=.18)
sfx.add(impact(.6), 13.72, gain=.4)
sfx.add(snap(), 13.72, gain=.4)
swish(13.85, .5, 3000, 10000, .12)
# yorum baloncuğu
pop(15.9, 700, .25)
keys(16.0, 16.7, 14, .18, seed=3)
pop(17.06, 1000, .2)
# Instagram akışı
swish(17.5, .4, 5000, 500, .3)
for t0 in (18.1, 18.8, 20.3, 21.45):
    mclick(t0, .6)
swish(18.2, .35, 400, 3000, .25)
swish(18.85, .3, 400, 2500, .18)
keys(19.2, 20.15, 14, .2, seed=7)
sw = sweep(noise(.3), 800, 6000, 'bandpass', .35) * np.sin(np.pi * tt(.3) / .3)
sfx.add(sw, 20.33, gain=.35)
pop(20.42, 900, .2)
for t0, m in ((20.92, 88), (21.04, 93)):
    c = chime(m, .9)
    sfx.add(c, t0, gain=.2)
    send.add(c, t0, gain=.2)
swish(21.48, .35, 400, 4000, .28)
for t0 in (21.95, 22.35, 22.85, 23.1):
    b = blip(784, 1046, .1)
    sfx.add(b, t0, gain=.2)
    send.add(b, t0, gain=.12)
# final
swish(23.5, .45, 300, 4000, .3)
for i, m in enumerate([72, 76, 79, 84, 88, 91]):
    c = chime(m, 1.2)
    sfx.add(c, 23.75 + i * .09, gain=.08, pan=-.4 + i * .16)
    send.add(c, 23.75 + i * .09, gain=.15)
swish(24.2, .5, 2000, 8000, .1)

# ---- miks ----
music_gain = np.where(t_all < 17.55, .9, 1.7)          # konuşma bitince müzik biraz açılır
music_gain = np.convolve(music_gain, np.ones(int(.4 * SR)) / int(.4 * SR), mode='same')
bed = (music.x + drums.x * .8) * duck * music_gain * .35
wet = reverb(send.x, 1.8)
mix = bed + sfx.x * .9 + wet * .35
mix[0] += voice
mix[1] += voice
mix = filt(mix, 'highpass', 30)
mix *= np.clip((DUR - t_all) / .5, 0, 1)
mix = np.tanh(mix * 1.2) / np.tanh(1.2)
mix /= np.max(np.abs(mix)) / .93
wavfile.write(os.path.join(HERE, 'work', 'mix.wav'), SR, (mix.T * 32767).astype(np.int16))
print('ok')
