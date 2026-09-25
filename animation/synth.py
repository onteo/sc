"""Sentez motoru: enstrümanlar, efektler, reverb/delay (music.py ve promo/music.py kullanır)."""
import os
import numpy as np
from scipy.signal import butter, sosfilt, sosfilt_zi, fftconvolve
from scipy.io import wavfile

SR = 48000
DUR = 15.0
N = int(SR * DUR)


def set_duration(d):
    global DUR, N
    DUR = d
    N = int(SR * d)
BEAT = 0.5
rng = np.random.default_rng(11)


def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


def tt(d):
    return np.arange(int(d * SR)) / SR


def noise(d):
    return rng.standard_normal(int(d * SR))


def filt(x, kind, f, order=2):
    f = np.asarray(f, dtype=float)
    sos = butter(order, f / (SR / 2), btype=kind, output='sos')
    return sosfilt(sos, x)


def sweep(x, f0, f1, kind='bandpass', q=0.35, block=256):
    """zamanla değişen filtre (üstel frekans taraması)"""
    out = np.zeros_like(x)
    n = len(x)
    zi = None
    for i in range(0, n, block):
        p = i / max(1, n - 1)
        f = f0 * (f1 / f0) ** p
        if kind == 'bandpass':
            lo, hi = f * (1 - q), min(f * (1 + q), SR / 2 * 0.95)
            sos = butter(2, [lo / (SR / 2), hi / (SR / 2)], btype='bandpass', output='sos')
        else:
            sos = butter(2, min(f, SR / 2 * 0.95) / (SR / 2), btype=kind, output='sos')
        if zi is None or zi.shape[0] != sos.shape[0]:
            zi = sosfilt_zi(sos) * 0
        out[i:i + block], zi = sosfilt(sos, x[i:i + block], zi=zi)
    return out


class Bus:
    def __init__(self):
        self.x = np.zeros((2, N))

    def add(self, sig, t, gain=1.0, pan=0.0):
        i = int(round(t * SR))
        if i >= N or len(sig) == 0:
            return
        if i < 0:
            sig = sig[..., -i:]
            i = 0
        sig = sig[..., :N - i] * gain
        if sig.ndim == 1:
            a = (pan + 1) * np.pi / 4
            self.x[0, i:i + len(sig)] += sig * np.cos(a)
            self.x[1, i:i + len(sig)] += sig * np.sin(a)
        else:
            self.x[:, i:i + sig.shape[1]] += sig


# ---------------- enstrümanlar ----------------
def saw_add(f, d, kmax_hz=11000, decay=None, phase=None):
    t = tt(d)
    K = max(1, int(kmax_hz / f))
    out = np.zeros_like(t)
    ph = rng.uniform(0, 2 * np.pi) if phase is None else phase
    for k in range(1, K + 1):
        h = np.sin(2 * np.pi * k * f * t + ph * k) / k
        if decay is not None:
            h *= np.exp(-t * (decay[0] + decay[1] * k))
        out += h
    return out * 0.5


def adsr(d, a=0.01, r=0.1):
    t = tt(d)
    e = np.minimum(1, t / max(a, 1e-4))
    e *= np.clip((d - t) / max(r, 1e-4), 0, 1)
    return e


def kick(gain=1.0):
    t = tt(0.5)
    f = 44 + 120 * np.exp(-t * 30)
    s = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 7)
    s += filt(noise(0.5), 'highpass', 3000) * np.exp(-t * 400) * 0.25
    return np.tanh(s * 1.6) * gain


def clap():
    t = tt(0.4)
    n = filt(noise(0.4), 'bandpass', [900, 4000])
    e = np.zeros_like(t)
    for o in (0, .011, .022):
        e += np.where(t >= o, np.exp(-(t - o) * 90), 0)
    e += np.exp(-t * 16) * 0.55
    return n * e * 0.5


def hat(open_=False):
    d = 0.25 if open_ else 0.06
    t = tt(d)
    n = filt(noise(d), 'highpass', 7500)
    return n * np.exp(-t * (14 if open_ else 70)) * 0.35


def pluck(m, d=0.35, bright=1.0):
    f = mtof(m)
    s = saw_add(f, d, kmax_hz=9000 * bright, decay=(5.0, 2.6 / bright))
    t = tt(d)
    return s * np.minimum(1, t / 0.002)


def chime(m, d=1.6):
    f = mtof(m)
    t = tt(d)
    s = (np.sin(2 * np.pi * f * t) + 0.35 * np.sin(2 * np.pi * 2 * f * t) * np.exp(-t * 4)
         + 0.12 * np.sin(2 * np.pi * 3.01 * f * t) * np.exp(-t * 7))
    return s * np.exp(-t * 2.6) * np.minimum(1, t / 0.003)


def pad(notes, d, cutoff=2400, a=0.25, r=0.5):
    L = np.zeros(int(d * SR))
    R = np.zeros(int(d * SR))
    for m in notes:
        for j, det in enumerate((-9, 0, 9)):
            s = saw_add(mtof(m) * 2 ** (det / 1200), d, kmax_hz=min(8000, cutoff * 2.5))
            pan = (-0.6, 0, 0.6)[j]
            a_ = (pan + 1) * np.pi / 4
            L += s * np.cos(a_)
            R += s * np.sin(a_)
    env = adsr(d, a, r)
    L = filt(L, 'lowpass', cutoff) * env
    R = filt(R, 'lowpass', cutoff) * env
    return np.vstack([L, R]) / (len(notes) * 2.2)


def bass(m, d):
    f = mtof(m)
    t = tt(d)
    s = saw_add(f, d, kmax_hz=1800) * 0.6 + np.sin(2 * np.pi * f * t) * 0.9
    s = filt(s, 'lowpass', 900)
    return np.tanh(s * 1.4) * adsr(d, 0.004, 0.04) * np.exp(-t * 2.5)


def impact(big=1.0):
    d = 2.2
    t = tt(d)
    f = 30 + 60 * np.exp(-t * 6)
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 2.2)
    crash = filt(noise(d), 'bandpass', [400, 9000]) * np.exp(-t * 2.4) * 0.35
    return np.tanh((boom * 1.2 + crash) * big)


def whoosh(d, f0=300, f1=6000, gain=1.0, rev=False):
    t = tt(d)
    env = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 2
    env = env * (t / d) ** 0.6
    if rev:
        env = env[::-1]
    return sweep(noise(d), f0, f1, 'bandpass', 0.4) * env * gain


def blip(f0, f1, d=0.07):
    t = tt(d)
    f = f0 * (f1 / f0) ** (t / d)
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t * 45) * np.minimum(1, t / 0.001)


def tick():
    t = tt(0.03)
    return filt(noise(0.03), 'bandpass', [2500, 9000]) * np.exp(-t * 260) * 0.6


def snap():
    t = tt(0.12)
    return (filt(noise(0.12), 'highpass', 2000) * np.exp(-t * 180) * 0.7
            + np.sin(2 * np.pi * 110 * t) * np.exp(-t * 30) * 0.8)


def reverb(x, secs=2.2, damp=5000, pre=0.012):
    n = int(secs * SR)
    t = np.arange(n) / SR
    out = []
    for ch in range(2):
        ir = rng.standard_normal(n) * np.exp(-t * 6.9 / secs)
        ir = filt(ir, 'lowpass', damp)
        ir[:int(pre * SR)] = 0
        ir /= np.sqrt(np.sum(ir ** 2))
        out.append(fftconvolve(x[ch], ir)[:N])
    return np.vstack(out)


def delay(x, time=0.375, fb=0.38, n=5, lp=3500):
    out = x.copy()
    d = int(time * SR)
    cur = x
    for k in range(n):
        cur = np.vstack([filt(cur[1], 'lowpass', lp), filt(cur[0], 'lowpass', lp)]) * fb  # ping-pong
        sh = np.zeros_like(x)
        sh[:, d * (k + 1):] = cur[:, :N - d * (k + 1)]
        out += sh
    return out


