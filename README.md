# infoakademi — 15 sn hareketli grafik

Online grafik tasarım eğitimi tanıtım animasyonu. Font: **Inter** (variable, OFL).

| Dosya | Boyut | Kullanım |
|---|---|---|
| `videos/infoakademi-reels-1080x1920.mp4` | 1080×1920, 60 fps, 15 sn | Instagram Reels / TikTok / Shorts |
| `videos/infoakademi-x-1920x1080.mp4` | 1920×1080, 60 fps, 15 sn | X (Twitter), YouTube, LinkedIn |

**Müzik:** `animation/music.py` ile sıfırdan sentezlenmiş özgün müzik + ses efektleri (telifsiz, 120 BPM, -14 LUFS).
Akorlar sahnelerle değişir (Fmaj7 · G6 · Am7 · Em7 · F→G · Cmaj9); kalem anchor'ları, renk kodları, afiş oturması,
logo noktalarının inişi gibi olaylara kare hassasiyetinde efekt bağlıdır. Ham ses: `audio/infoakademi-music.wav`.

Akış (her sahne 2.5 sn = 120 BPM'de 5 vuruş; müzik eklerken kesmeler vuruşa oturur):
01 çizgi → 02 tipografi → 03 renk → 04 kompozisyon → 05 eğitim → infoakademi logo animasyonu.

## Yeniden render

```bash
pip install imageio-ffmpeg numpy scipy
cd animation
python3 music.py                    # müzik -> ../audio/infoakademi-music.wav
node render.mjs                     # videolar + müzik (playwright gerekir)
node render.mjs mux                 # sadece müziği yeniden ekle
```

`animation/infoakademi.html` tarayıcıda (http sunucusu üzerinden) açılırsa animasyonu canlı oynatır;
`?w=1920&h=1080` ile yatay sürüm. Renkler dosyanın başındaki `C` nesnesinden değiştirilebilir.
