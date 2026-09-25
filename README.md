# infoakademi — 15 sn hareketli grafik

Online grafik tasarım eğitimi tanıtım animasyonu. Font: **Inter** (variable, OFL).

| Dosya | Boyut | Kullanım |
|---|---|---|
| `videos/infoakademi-reels-1080x1920.mp4` | 1080×1920, 60 fps, 15 sn | Instagram Reels / TikTok / Shorts |
| `videos/infoakademi-x-1920x1080.mp4` | 1920×1080, 60 fps, 15 sn | X (Twitter), YouTube, LinkedIn |

Akış (her sahne 2.5 sn = 120 BPM'de 5 vuruş; müzik eklerken kesmeler vuruşa oturur):
01 çizgi → 02 tipografi → 03 renk → 04 kompozisyon → 05 eğitim → infoakademi logo animasyonu.

## Yeniden render

```bash
pip install imageio-ffmpeg          # ffmpeg (libx264)
cd animation && node render.mjs     # playwright gerekir
```

`animation/infoakademi.html` tarayıcıda (http sunucusu üzerinden) açılırsa animasyonu canlı oynatır;
`?w=1920&h=1080` ile yatay sürüm. Renkler dosyanın başındaki `C` nesnesinden değiştirilebilir.
