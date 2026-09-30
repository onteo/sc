"""
Render sonrası kare taraması: tek karelik konum/ölçek/opaklık/renk sıçramalarını bulur.
Her kareyi küçültüp ardışık farkları hesaplar; komşularına göre ani ve yalnız kalan (bir kare sonra geri dönen)
tepe noktalarını "sıçrama" olarak raporlar.
Kullanım: python3 scan.py ../videos/infoakademi-tek-plan-dongu-2048x1080.mp4
"""
import subprocess
import sys
import numpy as np
import imageio_ffmpeg

path = sys.argv[1]
w, h = 256, 135
cmd = [imageio_ffmpeg.get_ffmpeg_exe(), '-loglevel', 'error', '-i', path, '-vf', f'scale={w}:{h},format=gray', '-f', 'rawvideo', '-']
raw = subprocess.run(cmd, capture_output=True, check=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, h, w).astype(np.float32)
n = len(fr)
d = np.abs(np.diff(fr, axis=0)).mean(axis=(1, 2))          # d[i] = fark(i, i+1)
# tek karelik sıçrama: i. kare hem öncekinden hem sonrakinden çok farklı, ama i-1 ile i+1 birbirine benziyor
pops = []
for i in range(1, n - 1):
    a, b2 = d[i - 1], d[i]
    around = np.abs(fr[i + 1] - fr[i - 1]).mean()
    if a > 2.0 and b2 > 2.0 and around < .35 * min(a, b2):
        pops.append((i, i / 60, a, b2, around))
# ani büyük değişimler (kesme benzeri) — tek plan kuralı için
local = np.array([np.median(d[max(0, i - 15):i + 15]) for i in range(len(d))])
cuts = [(i, i / 60, d[i], local[i]) for i in range(len(d)) if d[i] > 12 and d[i] > 6 * (local[i] + .5)]
print(f'{n} kare tarandı')
print('tek karelik sıçramalar:', len(pops))
for p in pops[:40]:
    print('  kare %d (%.3f sn)  önce %.2f  sonra %.2f  çevre %.2f' % p)
print('kesme benzeri ani değişimler:', len(cuts))
for c in cuts[:40]:
    print('  kare %d (%.3f sn)  fark %.2f  yerel %.2f' % c)
# döngü: ilk ve son kare
print('ilk ↔ son kare farkı: %.3f' % np.abs(fr[0] - fr[-1]).mean())
