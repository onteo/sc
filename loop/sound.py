"""
Tek plan döngü videosu sesi (36 sn = 66 vuruş @110 BPM). Özgün, telifsiz sentez müzik + arayüz efektleri.
- Drop'a (vuruş 20 = play tıklaması) kadar müzik güçlü bir low-pass filtreden geçer (uzaktan gelir);
  tıklama anında filtre hızla tamamen açılır. Sonda filtre yeniden kapanır → döngü başa kusursuz bağlanır.
- Efekt zamanları loop.html'deki zaman çizelgesiyle aynı.
Kullanım: python3 sound.py -> audio.wav (ffmpeg loudnorm ile -14 LUFS'e getirilir)
"""
import os
import sys
import numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi
from scipy.io import wavfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'animation'))
import synth  # noqa: E402
B = 60 / 110
synth.set_duration(66 * B)
from synth import *  # noqa: E402,F401,F403

SR, N, DUR = synth.SR, synth.N, synth.DUR
b = lambda n: n * B
t_all = np.arange(N) / SR
DROP = b(20)
music, drums, sfx, send = Bus(), Bus(), Bus(), Bus()

# ---- müzik: I–V–vi–IV (C G Am F), ölçü = 4 vuruş ----
PROG = [([48, 55, 60, 64], 36), ([43, 50, 55, 59], 31), ([45, 52, 57, 60], 33), ([41, 48, 53, 57], 29)]
BAR = 4 * B
nbars = int(np.ceil(DUR / BAR))
for i in range(nbars):
    a = i * BAR
    ch, root = PROG[i % 4]
    full = DROP <= a < b(60)
    p = pad(ch, BAR + .25, cutoff=2600 if full else 1800, a=.08 if i else .6, r=.3)
    music.add(p, a, gain=.32)
    send.add(p, a, gain=.18)
    # bas: drop sonrası sekizlik vuruş arası
    if full:
        for k in range(8):
            music.add(bass(root, .18), a + k * B / 2 + B / 4 * 0, gain=.42 if k % 2 else .25)
    else:
        music.add(np.sin(2 * np.pi * mtof(root) * tt(BAR)) * adsr(BAR, .2, .3) * .22, a)
    # pluck arpej (16'lık)
    notes = [ch[0] + 12, ch[2] + 12, ch[3] + 12, ch[1] + 24, ch[3] + 12, ch[2] + 12, ch[1] + 12, ch[2] + 12]
    for k in range(16):
        pl = pluck(notes[k % 8], .26, bright=.8)
        music.add(pl, a + k * B / 4, gain=(.09 if full else .07) * (1.2 if k % 4 == 0 else 1), pan=.35 * np.sin(k * .7))
        send.add(pl, a + k * B / 4, gain=.04)
    # drop sonrası üst melodi (stab)
    if full:
        for k, off in enumerate([0, 1.5, 3]):
            s = pluck(ch[3] + 12 + [0, 2, 0][k], .35, bright=1.0)
            music.add(s, a + off * B, gain=.12)
            send.add(s, a + off * B, gain=.1)
# davul (drop'ta başlar, marka bölümünde biter)
for n in range(66):
    t0 = b(n)
    if DROP <= t0 < b(60):
        drums.add(kick(), t0, gain=.8)
        if n % 2 == 1:
            drums.add(clap(), t0, gain=.4)
            send.add(clap(), t0, gain=.12)
        drums.add(hat(), t0 + B / 2, gain=.32, pan=.2)
        drums.add(hat(), t0 + B / 4, gain=.1, pan=-.2)
        drums.add(hat(), t0 + 3 * B / 4, gain=.1, pan=-.2)
    elif t0 < DROP and n >= 8:
        drums.add(hat(), t0 + B / 2, gain=.08, pan=.2)
# drop öncesi yükselen gerilim + drop darbesi
rd = b(20) - b(17.5)
rt = tt(rd)
riser = sweep(noise(rd), 400, 9000, 'bandpass', .3) * (rt / rd) ** 2.2
sfx.add(riser, b(17.5), gain=.22)
send.add(riser, b(17.5), gain=.1)

# ---- low-pass otomasyonu (müzik + davul) ----
def cutoff(t):
    if t < DROP - .02:
        return 420.0
    if t < DROP + .06:
        return 420.0 * (18000 / 420) ** ((t - DROP + .02) / .08)
    if t < b(60):
        return 18000.0
    return 18000.0 * (420 / 18000) ** min(1, (t - b(60)) / (DUR - b(60) - .05))


def auto_lp(x, block=256):
    y = np.zeros_like(x)
    zi = None
    for i in range(0, x.shape[-1], block):
        f = min(cutoff(i / SR), SR / 2 * .95)
        sos = butter(2, f / (SR / 2), 'lowpass', output='sos')
        if zi is None:
            zi = np.stack([sosfilt_zi(sos) * 0 for _ in range(x.shape[0])])
        for c in range(x.shape[0]):
            y[c, i:i + block], zi[c] = sosfilt(sos, x[c, i:i + block], zi=zi[c])
    return y


# ---- arayüz efektleri ----
def click(t0, g=.5):
    sfx.add(tick(), t0, gain=.5 * g)
    sfx.add(np.sin(2 * np.pi * 190 * tt(.035)) * np.exp(-tt(.035) * 140), t0, gain=.45 * g)


def soft(t0, g=.18, f0=500, f1=3500, d=.4):
    w = whoosh(d, f0, f1, gain=g)
    sfx.add(w, t0)
    send.add(w, t0, gain=.3)


def bloop(t0, f=520, g=.2):
    tb = tt(.18)
    s = np.sin(2 * np.pi * np.cumsum(f * (1 + .6 * np.exp(-tb * 30))) / SR) * np.exp(-tb * 18)
    sfx.add(s, t0, gain=g)
    send.add(s, t0, gain=g * .4)


def chimes(t0, ms, g=.16, dt=.07):
    for i, m in enumerate(ms):
        c = chime(m, 1.1)
        sfx.add(c, t0 + i * dt, gain=g, pan=-.25 + i * .15)
        send.add(c, t0 + i * dt, gain=g * 1.2)


def typing(t0, n, dt):
    r = np.random.default_rng(int(t0 * 100))
    for i in range(n):
        tp = t0 + i * dt + r.uniform(-.02, .02)
        sfx.add(tick(), tp, gain=.12 * r.uniform(.7, 1.1), pan=r.uniform(-.15, .15))


# sahne 01
click(b(1))
soft(b(1.5), .16)
soft(b(3.5), .12, 800, 3000)
sfx.add(tick(), b(5) - .08, gain=.25)
chimes(b(5) + .3, [88, 91], .16, .09)                 # onay
for i, f in enumerate((440, 520, 620)):
    bloop(b(6.5) + .2 + i * .06, f, .14)               # üç nokta
# sahne 02: sohbet
bloop(b(8) + .25, 600, .16)
typing(b(8) + .55, 6, .22)
bloop(b(9.5) + .25, 480, .16)
typing(b(9.5) + .6, 9, .19)
soft(b(15), .12, 3000, 700)
bloop(b(16.5) + .55, 380, .18)                         # birleşme
soft(b(18), .14, 700, 4000)                            # play'e katlanma
# sahne 03: DROP — play tıklaması
click(DROP, 1.0)
im = impact(.9)
sfx.add(im, DROP, gain=.5)
send.add(im, DROP, gain=.25)
w = whoosh(.45, 200, 5000, gain=.35)
sfx.add(w, DROP + .02)
soft(b(21), .22, 4000, 400, .7)                        # kamera geri çekilir
click(b(23), .5)                                       # video oynar
for tt0 in (b(24.5), b(26), b(27.5), b(29)):
    soft(tt0, .1, 900, 5000, .5)                       # kart dönüşümleri
# sahne 05: sürükleme + kaydırma
click(b(31), .6)
dd = b(32) + .8 - b(31)
scrub = sweep(noise(dd), 300, 2400, 'bandpass', .25) * np.sin(np.pi * tt(dd) / dd) ** .6
sfx.add(scrub, b(31), gain=.18)
soft(b(32), .32, 300, 6000, .8)
# sahne 06: grafik
soft(b(33.5), .12, 600, 3000)
for i, n in enumerate((34, 35, 36, 37)):
    b2 = blip(900 + i * 180, 1200 + i * 180, .06)
    sfx.add(b2, b(n), gain=.18)
chimes(b(37) + .3, [84, 88, 91, 96], .14, .06)          # %100
click(b(38), .7)
soft(b(38) + .08, .28, 400, 7000, .8)                   # yeşil noktaya dalış
# sahne 07: başarı
chimes(b(39.5) + .35, [72, 76, 79, 84, 88], .13, .07)
sfx.add(filt(noise(.3), 'bandpass', [1500, 7000]) * np.exp(-tt(.3) * 12), b(39.5) + .5, gain=.2)  # sertifika açılır
for i, n in enumerate((41, 41.5, 42, 42.5, 43)):
    bloop(b(n) + .2, 500 + i * 60, .1)
chimes(b(44) + .4, [84, 91], .14, .08)                  # rozet
# sahne 08: kariyer anları
for i, n in enumerate((45.5, 47, 48.5, 50)):
    soft(b(n), .1, 800, 4000, .45)
    bloop(b(n) + .45, 440 + i * 70, .1)
soft(b(51.5), .14, 500, 3000, .7)
# sahne 09: CTA
soft(b(52), .12, 700, 3500)
click(b(53.5)); bloop(b(53.5) + .05, 700, .12)          # beğen
click(b(55)); chimes(b(55) + .1, [79, 84], .1, .06)     # abone ol
click(b(56.5)); soft(b(56.5) + .02, .08, 1500, 5000, .3)  # zil menüsü
click(b(57.5))
for k in range(2):                                      # zil onayı (tek hareket)
    c = chime(96, .7)
    sfx.add(c, b(57.5) + .12 + k * .09, gain=.08)
    send.add(c, b(57.5) + .12 + k * .09, gain=.12)
soft(b(58.5) - .3, .08, 600, 3000)
# sahne 10: marka
soft(b(60), .14, 3000, 500, .7)
chimes(b(61.5) + .4, [72, 79, 84, 88], .12, .08)
soft(b(63), .12, 3000, 600, .6)
td = tt(.3)
sfx.add(np.sin(2 * np.pi * np.cumsum(110 + 50 * np.exp(-td * 30)) / SR) * np.exp(-td * 12), b(64.5) + .4, gain=.3)

# ---- miks ----
mus = auto_lp(music.x + drums.x * .85)
wet = reverb(send.x, 1.8)
mix = mus * .8 + sfx.x + wet * .4
mix = filt(mix, 'highpass', 30)
mix = np.tanh(mix * 1.1) / np.tanh(1.1)
mix /= np.max(np.abs(mix)) / .9
wavfile.write(os.path.join(os.path.dirname(__file__), 'audio.wav'), SR, (mix.T * 32767).astype(np.int16))
print('ok', DUR)
