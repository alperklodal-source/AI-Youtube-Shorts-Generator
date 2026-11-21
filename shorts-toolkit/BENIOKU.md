# Shorts Araç Seti — So The Story Goes

Bu klasör, bu hesapta birlikte geliştirdiğimiz Shorts üretim tekniklerinin tamamını içerir.

## Başka hesapta nasıl kullanılır
1. Zip'i aç ve klasörü yeni hesaptaki Claude Code oturumuna yükle (ya da bir GitHub reposuna koy).
2. Claude'a şunu yaz: **"CLAUDE.md dosyasını oku, bu iş akışıyla yeni bir Short yapacağız."**
   CLAUDE.md, Claude için yazılmış talimat dosyasıdır: kalite çıtası (86+ / 90+), formatlar, ses ayarları,
   müzik seçenekleri, YouTube telif dersleri.
3. Kanal sesini klonlamak için kendi ses örneğini (10–20 sn temiz kayıt) ver; `cb_tts.py` bu referansla çalışır.
   (Kanal ses örneğini bu pakete koymadım; sende varsa ekle.)

## İçerik
| Klasör | Ne var |
|---|---|
| `CLAUDE.md` | Claude için tüm iş akışı ve kurallar (İngilizce) |
| `format-narrated-mystery/` | Lycurgus Kupası formatı: Remotion kodu (`Short.tsx`, `Cover.tsx`), seslendirme, senkron, müzik ve miksaj betikleri, örnek fotoğraflar, kapak |
| `format-music-montage/` | First Spark formatı (anlatımsız, müzikli montaj): stil rehberi, Remotion kodu, Wan 2.1 Kaggle not defterleri, kaynak kayıtları |
| `dodecahedron/` | İlk anlatımlı Short'un (Roma dodekahedronu) betikleri ve kodu |

## Pakete dahil edilmeyenler
- Telifli şarkı (Little Dark Age) ve büyük arşiv videoları (gerekince yeniden indirilir)
- `node_modules`, Python ortamları, TTS modelleri (kurulumda yeniden indirilir)
- Hiçbir şifre / API anahtarı (Kaggle, YouTube vb. — yeni hesapta kendi anahtarlarını kullan)

## Gerekli kurulumlar (yeni ortamda)
- Node 18+ → `npm install` (remotion klasöründe)
- Python 3.11+ → `pip install chatterbox-tts faster-whisper librosa soundfile scipy opencv-python-headless`
- ffmpeg
