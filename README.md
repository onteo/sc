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

---

# infoakademi — uygulama tanıtım videosu (21 sn)

Uygulamanın gerçek ekran görüntüleri (`promo/app/`) telefon çerçevesinde, dokunma animasyonlarıyla canlandırılır:
logo → açılış ekranı · ana sayfa · ders hatırlatma bildirimi · konumla yoklama ("Ben geldim" → onay) ·
sohbet (yaz, gönder, cevap) · online dersler · ders materyalleri · App Store / Google Play kapanışı.

| Dosya | Boyut | Kullanım |
|---|---|---|
| `videos/infoakademi-app-reels-1080x1920.mp4` | 1080×1920, 60 fps | Reels / TikTok / Shorts |
| `videos/infoakademi-app-yatay-1920x1080.mp4` | 1920×1080, 60 fps | X, YouTube, web sitesi |
| `videos/infoakademi-app-store-preview-886x1920.mp4` | 886×1920, 30 fps | App Store önizleme (iPhone 6.5"/6.7") |

```bash
cd promo
python3 music.py        # ../audio/infoakademi-app-music.wav
node render.mjs         # üç format + müzik
```
