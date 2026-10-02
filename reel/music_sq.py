"""
KARE web sürümü (edit_sq.html, 20 sn): music2.py ile aynı müzik/efektler; konuşma "kayıtlar açık"ta (14.47 sn) biter,
Instagram yorum/DM efektleri yok, kapanışta program çipleri ve "kayıtlar açık" efektleri.
Kullanım: python3 music_sq.py -> work/mix_sq.wav

Kaynak — KOYU tema sürümü: karanlık minör beat (808), yoğun efektler (glitch, bas darbesi, yükselen gerilim).
Konuşan kişi Reels'i için ses: temizlenmiş konuşma + alçak müzik (konuşmada kısılır) + senkron efektler.
Zamanlar edit.html'deki animasyonlarla aynı (kesilmiş zaman çizelgesi).
Kullanım: python3 music2.py -> work/mix2.wav
"""
import os
import sys
import numpy as np
from scipy.io import wavfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'animation'))
import synth  # noqa: E402
synth.set_duration(20.0)
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
VEND = 14.47
voice *= np.clip((VEND - t_all) / .04, 0, 1)        # "yorumlara yaz" bölümü web'de yok
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
PROG = [([45, 52, 57, 60], 33), ([41, 48, 53, 57], 29), ([38, 45, 50, 53], 26), ([40, 47, 52, 56], 28)]
MEND = 18.0                                        # müzik bitişi → son akor
for bar in range(12):
    a = bar * 2.0
    if a >= MEND:
        break
    ch, root = PROG[bar % 4]
    b = min(a + 2.0, MEND)
    p = pad(ch, b - a + .3, cutoff=1400, a=.05 if bar else 1.0, r=.3)
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


def k808(root, d=.9):
    t = tt(d)
    f = mtof(root) * (1 + 1.5 * np.exp(-t * 40))
    return np.tanh(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2) * 2.2) * .8


for bar in range(12):
    a = bar * 2.0
    if a >= MEND - .1:
        break
    root = PROG[bar % 4][1] - 12
    for off, g in ((0, 1), (.75, .7), (1.25, .8)):
        if a + off < MEND - .1:
            drums.add(k808(root), a + off, gain=.55 * g)
            drums.add(kick(), a + off, gain=.45 * g)
    for off in (.5, 1.5):
        drums.add(clap(), a + off, gain=.35)
        drums.add(snap(), a + off, gain=.15)
    r = np.random.default_rng(bar)
    k = a
    while k < min(a + 2, MEND - .1) - 1e-6:
        roll = (k - a) in (1.75,)
        step = .0625 if roll else .125
        drums.add(hat(), k, gain=.18 + .08 * r.random(), pan=.2)
        k += step
fin = pad([48, 52, 55, 59, 62], 1.6, cutoff=3200, a=.02, r=1.0)
music.add(fin, MEND, gain=.45)
send.add(fin, MEND, gain=.4)
music.add(bass(24, 1.4), MEND, gain=.5)

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
# kapanış: marka + programlar + kayıtlar açık
FIN = 14.45
swish(FIN, .45, 300, 4000, .3)
for i, m in enumerate([72, 76, 79, 84, 88, 91]):
    c = chime(m, 1.2)
    sfx.add(c, FIN + .15 + i * .09, gain=.08, pan=-.4 + i * .16)
    send.add(c, FIN + .15 + i * .09, gain=.15)
swish(FIN + .6, .5, 2000, 8000, .1)
for i in range(3):
    pop(FIN + 1.37 + i * .25, 700 + i * 180, .24)
# ---- koyu tema ek efektleri ----
def boom(t0, g=.5):
    tb = tt(1.2)
    f = 55 * (1 + .8 * np.exp(-tb * 18))
    sfx.add(np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-tb * 3.5), t0, gain=g)
    send.add(filt(noise(.4), 'lowpass', 3000) * np.exp(-tt(.4) * 10), t0, gain=g * .3)


def zap(t0, g=.35):
    d = .18
    tz = tt(d)
    sq = np.sign(np.sin(2 * np.pi * (300 + 2500 * np.random.default_rng(int(t0 * 100)).random()) * tz))
    cr = filt(noise(d), 'bandpass', [2000, 9000]) * (np.random.default_rng(int(t0 * 50)).random(len(tz)) > .6)
    sfx.add((sq * .25 + cr) * np.exp(-tz * 12), t0, gain=g)


def riser(t0, d, g=.3):
    tr_ = tt(d)
    x = sweep(noise(d), 400, 9000, 'bandpass', .3) * (tr_ / d) ** 2
    x += np.sin(2 * np.pi * np.cumsum(150 * 6 ** (tr_ / d)) / SR) * (tr_ / d) ** 3 * .15
    sfx.add(x, t0, gain=g)
    send.add(x, t0, gain=g * .4)


def slam(t0, g=.18):
    ts = tt(.12)
    sfx.add(np.sin(2 * np.pi * 110 * ts) * np.exp(-ts * 35) + filt(noise(.12), 'highpass', 3000) * np.exp(-ts * 60) * .4, t0, gain=g)


for t0 in (3.8, 5.95, 8.28, 10.87, 12.0, 14.5):   # glitch anları
    zap(t0)
for t0 in (.75, 1.85, 3.1, 6.0, 8.38, 10.95, 13.2):  # cümle başları
    boom(t0, .45)
riser(5.2, .75)
riser(7.6, .68, .22)
riser(16.4, .55, .2)
# her altyazı kelimesi çarpınca hafif vuruş
WORD_T = [0.12, 0.77, 1.16, 1.87, 2.09, 2.43, 3.11, 3.45, 6.04, 6.45, 7.0, 7.3, 7.65, 8.42, 8.85, 9.72, 10.3, 11.01, 11.6, 13.25, 13.75]
for t0 in WORD_T:
    slam(t0)

# kayıtlar açık rozeti
boom(FIN + 2.55, .4)
slam(FIN + 2.55, .25)
swish(FIN + 3.1, .4, 3000, 9000, .1)

# ---- miks ----
music_gain = np.where(t_all < VEND + .05, 1.0, 1.8)          # konuşma bitince müzik biraz açılır
music_gain = np.convolve(music_gain, np.ones(int(.4 * SR)) / int(.4 * SR), mode='same')
bed = (music.x + drums.x * .8) * duck * music_gain * .35
wet = reverb(send.x, 1.8)
mix = bed + sfx.x * 1.05 + wet * .4
mix[0] += voice
mix[1] += voice
mix = filt(mix, 'highpass', 30)
mix *= np.clip((DUR - t_all) / .5, 0, 1)
mix = np.tanh(mix * 1.2) / np.tanh(1.2)
mix /= np.max(np.abs(mix)) / .93
wavfile.write(os.path.join(HERE, 'work', 'mix_sq.wav'), SR, (mix.T * 32767).astype(np.int16))
print('ok')
