# Shorts stili: "First Spark" formatı

Kanal: **So The Story Goes**. Bu klasör, "First Spark" Short'unda oturttuğumuz tarzın ve iş akışının kaydı.
Yeni Short fikirleri bu kalıba göre üretilir.

## Format özeti

| Özellik | Kural |
|---|---|
| Süre | 20–30 sn, dikey 1080x1920, 30 fps |
| Anlatım | **Seslendirme yok, ekranda yazı yok.** Hikâyeyi müzik + görüntü + 1 ikonik gerçek ses (ör. Armstrong) anlatır |
| Müzik | **YouTube Shorts "Resmi müzik"** sekmesindeki lisanslı bir şarkı (sanatçı adı resmi olmalı; "slowed", cover, kullanıcı remiksi YOK → Content ID engeli). Ya da YouTube Ses Kitaplığı'ndan telifsiz şarkı (o zaman müziği videoya gömeriz) |
| Senkron | Her kesme şarkının vuruşuna (beat) veya vokal girişine denk gelir. Vuruşlar librosa ile, vokal girişleri faster-whisper kelime zamanlarıyla ölçülür (sözler değil, sadece zaman) |
| Açılış | 1 tek **AI üretimi (Wan 2.1) sinematik sahne**: karanlık, gerçekçi, tek karakter, tek "keşif anı" (kıvılcım). İlk ~3 sn el değmeden, müziksiz; müzik keşif anında girer |
| Dönüşüm | Keşif anında **ışık patlaması + matematik formülleri** (MathOverlay / LightBurst / BeatMath), gözlere zoom → beyne dalış (BrainRewind) |
| Montaj | Sonra **gerçek arşiv görüntüleri** (NASA, ABD hükümeti, kamu malı / Wikimedia Commons) vuruşlarla hızlı kesilir: savaş → atom bombası → Ay → roket |
| Final | Mesajı kapatan sembolik son sahne (ekranda küçülen Dünya → ekran CRT gibi kapanır) + ikonik sesin ikinci yarısı reverb'lü |
| Tema | "Bir kıvılcımdan buraya": insanlığın zekâ ve teknolojiyle geldiği hem muhteşem hem korkutucu nokta |
| Kalite çıtası | Senaryo/kurgu Short maker değerlendirmesinde **86+**, görsel seçimi **90+** |

## Kesinleşen zaman çizelgesi (First Spark, v12)

Şarkı zamanları (song time). Video, şarkının `T0 = MUSIC_IN - PRE` saniyesine karşılık gelerek başlar.

| Zaman | Olay |
|---|---|
| video 0.0–2.9 | Wan maymun sahnesi, el değmemiş, müzik yok; 0.35'te "That's one small step for man" |
| şarkı 13.0 | Müzik girer (PRE = 2.9 sn sonra) |
| 13.6 | Kıvılcım (vuruş) + sıcak flaş |
| 14.37 | Gözler parlar → LightBurst, formüller başlar; ağır çekim + gözlere zoom |
| 15.12 / 15.85 / 16.6 | Her vuruşta büyük formül (BeatMath) |
| 16.56 | Beyne dalış (BrainRewind) |
| 17.34 | Montaj başlar: nuke → salvo → planes → tank → Ivy Mike (vuruşlarla) |
| 23.46 | Vokal girişi: Ay'da bayrak (Apollo 14) |
| 25.50 | Roket (Artemis I) |
| 27.30 | Son sahne: ekranda küçülen Dünya (MESSENGER), 28.1'de "One giant leap for mankind" (reverb) |
| ~32.6 | Ekran CRT gibi kapanır (çizgi → nokta → karanlık) |

> Not: Bu zamanlar "Little Dark Age (Slowed)" için ölçüldü; o sürüm Sony tarafından engellendi.
> Resmi "Little Dark Age (Ghost Vision Remix) – MGMT" için vuruşlar yeniden ölçülüp kaydırılacak.

## İş akışı

1. **Fikir**: "X'in ilk anı → bugün nereye geldi" kalıbı. Short maker'a puanlat (86+).
2. **Şarkı**: Shorts → Sesler → **Resmi müzik** sekmesinden seç. Telefon ekran kaydıyla (sesli, başlangıç 0:00) bize gönder → vuruş/vokal ölçümü.
3. **Açılış sahnesi (Wan 2.1 T2V 1.3B, Kaggle T4)**: `wan/` içindeki notebook'lardan biri şablon.
   480x832, 81 kare (≈5 sn, 16 fps), 30 adım, guidance 5. Her seed ≈ 39 dk. 3 seed üret, en iyisini seç.
   Prompt kalıbı: *ortam + ışık* → *karakter (iri, ciddi, hafif ilk-insan yüzlü)* → *eylem* → *kaza/keşif* → *tepki (şaşkınlık)* → *gerçekçilik/film terimleri*.
   Negatif: cartoon, CGI, fireworks, magic sparkles, campfire, blue tint, glowing eyes…
4. **Renk**: Wan çıktısı fazla mavi olur → `colorchannelmixer=rr=1.1:bb=0.8:gg=0.98,eq=saturation=0.7:contrast=1.15:brightness=-0.04,curves=all='0/0 0.5/0.42 1/1'`.
   Ağır çekim için önce `minterpolate=fps=48:mi_mode=mci`.
5. **Arşiv görüntüleri**: Wikimedia Commons API (`filetype:video`), transcoded VP9 720p/1080p; kamu malı olanlar. Kaynakları `credits/` gibi JSON'a yaz.
6. **Kurgu**: `remotion/src/Short.tsx` (SHOTS listesi = [dosya, süre, offset, zoomFrom, zoomTo]). Render:
   `npx remotion render src/index.ts Short out/x.mp4 --gl=angle` (+ `--props='{"music":false}'` sessiz sürüm).
7. **Teslim**: iki sürüm: şarkılı (kontrol) + sessiz (yükleme; ikonik ses içinde). Shorts'ta şarkıyı doğru saniyeden başlat.
8. **Yükleme**: Kategori **Eğitim**, "Değiştirilmiş/yapay içerik: Evet", açıklamada kaynaklar, başlık + açıklama çevirileri (Studio → Altyazılar).

## Dersler

- Shorts'ta kullanıcı remiksleri/slowed sürümler "Sesler"de görünse de **lisanslı değil** → dünya genelinde engel.
- YouTube Shorts editörü şarkıyı videonun ortasından başlatamaz; sessiz bir giriş istiyorsak müziği gömmek gerekir (sadece telifsiz müzikle).
- Apollo 11 ilk adım TV görüntüsü çok bulanık; net Ay sahnesi için Apollo 14/15/16 16 mm film kullan.
- Wan robot eli yapay duruyor; insan/robot eli yerine nesne (monitör) + efekt (CRT kapanma) daha inandırıcı.
- Kaggle: proxy sadece header enjekte ettiği için `wan/kaggle_cli_wrapper.py` token introspection'ı atlar.

## Klasör

- `first-spark/remotion/` – kurgu kodu (medya dosyaları hariç; `public/` arşivden yeniden indirilir)
- `first-spark/wan/` – Kaggle Wan notebook şablonları
- `first-spark/credits/` – kullanılan arşiv görüntülerinin lisans/kaynak kayıtları
- `first-spark/assets/` – seçilen Wan klibi (seed 7), monitör arka planı, Armstrong ses parçaları (NASA, kamu malı)
