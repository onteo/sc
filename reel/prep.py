"""Ham çekimi keser (sessizlikler çıkarılır), kareleri + ses izini ve kişi maskelerini üretir."""
import json, os, subprocess, sys
import numpy as np

SRC = sys.argv[1]
FF = __import__('imageio_ffmpeg').get_ffmpeg_exe()
OUT = os.path.join(os.path.dirname(__file__), 'work')
os.makedirs(f'{OUT}/frames', exist_ok=True)
os.makedirs(f'{OUT}/masks', exist_ok=True)

# konuşma bölümleri (silencedetect + 0.12 sn pay)
CLIPS = [(1.17, 4.95), (5.28, 9.80), (10.09, 12.68), (12.87, 13.95), (14.53, 20.13)]
json.dump(CLIPS, open(f'{OUT}/clips.json', 'w'))

v = ''.join(f'[0:v]trim={a}:{b},setpts=PTS-STARTPTS[v{i}];' for i, (a, b) in enumerate(CLIPS))
# kesimlerde tık sesi olmasın diye 15 ms'lik yumuşak geçiş
aud = ''.join(f'[0:a]atrim={a}:{b},asetpts=PTS-STARTPTS,afade=t=in:d=0.015,afade=t=out:st={b-a-0.015}:d=0.015[a{i}];' for i, (a, b) in enumerate(CLIPS))
n = len(CLIPS)
fc = v + aud + ''.join(f'[v{i}]' for i in range(n)) + f'concat=n={n}:v=1:a=0[v];' + ''.join(f'[a{i}]' for i in range(n)) + f'concat=n={n}:v=0:a=1[a]'
subprocess.run([FF, '-y', '-loglevel', 'error', '-i', SRC, '-filter_complex', fc, '-map', '[v]', '-r', '30',
                '-q:v', '2', f'{OUT}/frames/%05d.jpg', '-map', '[a]', '-ac', '1', '-ar', '48000', f'{OUT}/voice_raw.wav'], check=True)
# ses temizliği: gürültü azaltma, uğultu filtresi, hafif kompresör
subprocess.run([FF, '-y', '-loglevel', 'error', '-i', f'{OUT}/voice_raw.wav', '-af',
                'highpass=f=80,afftdn=nf=-30,acompressor=threshold=-20dB:ratio=3:attack=5:release=80,equalizer=f=3500:t=q:w=1:g=2',
                f'{OUT}/voice.wav'], check=True)

# kişi maskeleri
import cv2
import mediapipe as mp
seg = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=0)
files = sorted(os.listdir(f'{OUT}/frames'))
prev = None
for f in files:
    img = cv2.imread(f'{OUT}/frames/{f}')
    res = seg.process(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
    m = res.segmentation_mask.astype(np.float32)
    if prev is not None:
        m = 0.6 * m + 0.4 * prev          # zamansal yumuşatma (titremeyi azaltır)
    prev = m
    m = np.clip((m - 0.35) / 0.3, 0, 1)
    m = cv2.GaussianBlur(m, (0, 0), 2.5)
    a = (m * 255).astype(np.uint8)
    cv2.imwrite(f'{OUT}/masks/{f[:-4]}.png', np.dstack([np.full_like(a, 255)] * 3 + [a]))  # saydamlık = maske
print(len(files), 'frames')
