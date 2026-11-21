# Format rehberi: Doodle-kollaj anlatım videoları

Bu dosya, formatı yeni bir oturumda (insan ya da Claude) hemen kullanabilmek için yazıldı.
Kurulum için `setup.sh`, teknik detaylar için `README.md` dosyasına bak.

## 1. Tarz (değişmeyen kurallar)
- **Görsel:** lacivert yıldızlı fon (`space`); gece için `night`, şok anları için kırmızı `alert`,
  geçmiş ya da hikâye için `dawn`, alıntı ve belge için `paper`. Her şey Paint'te çizilmiş gibi
  titrek çizgilerle, beyaz kâğıt kenarlı kesik figürlerle ve el yazısı (Caveat) etiketlerle yapılır.
- **Hareket:** her öğe sahneye bir animasyonla girer (`pop`, `stamp`, `slide_l/r/u`, `drop`, `grow`, `fade`).
  Önemli rakamlar `stamp` ile ekrana "çakılır" (ekran sarsılır ve ses efekti çalar).
- **Anlatım:** eğlenceli, arkadaşına anlatır gibi. Kısa cümleler kurulur, her sahnede tek fikir ve
  1–3 yeni görsel olur. Şaka olur ama bilgi doğru kalır.
- **Ses:** `voxcpm` + `eglenceli_anlatici`, müzik `fun`. Gizemli ton için `gizemli_anlatici` + `sneaky` kullanılır.
- **Altyazı:** kelime kelime sarı vurgulu, otomatik.

## 2. Senaryo kalıbı (Shorts, 50–70 sn, 12–15 sahne)
1. **Kanca (alert):** soru ya da şok cümlesi + büyük yazı/mühür. ("Maaşın neden ayın 15'inde bitiyor?")
2. **Kurulum:** izleyiciyi hikâyeye sok ("Diyelim ki asgari ücretlisin...").
3. **3–6 adım açıklama:** her adımda bir rakam veya bir benzetme ("merdivenle asansörün yarışı").
4. **Ters köşe veya şok rakam** (alert fonu).
5. **Özet** + akılda kalan bir isim ("cüzdan erimesi").
6. **Bağlantı/kapanış:** tarihî bir söz ya da gizem ("Machiavelli 500 yıl önce demiş ki...").
7. **CTA:** "Takip et" mührü veya "Yorumlara yaz: gemi mi, kaya mı?"

Uzun hikâye sürümü (2–4 dk, ~30 sahne) aynı kalıpla yapılır; sadece adımlar çoğalır.

## 3. Doğruluk ve hassasiyet
- Her rakam güncel bir kaynaktan gelmeli; kaynaklar `meta.description` içine yazılmalı.
- Kanıtlanmamış iddialar "iddia" diye anlatılmalı ve karşı görüş de verilmeli (bkz. Nuh'un Gemisi bölümü).
- Peygamberler yüzlü çizilmez; `light` öğesiyle (ışık) temsil edilir.
- Siyasi içerikte kişiler hedef alınmaz, mekanizma anlatılır.

## 4. Metin kuralları
- `text`: ekrandaki altyazı (rakamlar rakamla yazılabilir).
- `say`: seslendirilecek metin, isteğe bağlı. Rakamlar `normalizer-tr` ile otomatik okunur. Yabancı isimleri
  ve kısaltmaları okunuşuyla yaz ("Makyavelli", "Apofis") ya da ses klasöründeki `ses.json` içindeki
  `okunus` sözlüğüne ekle.
- Cümleyi "..." ile başlatma (ses takılıyor). Cümle içinde "..." kullanılabilir.

## 5. Yerleşim (1080×1920)
- Üstte seri başlığı y≈160'ta durur. Altyazı y≈1470'te olur. Shorts arayüzü alttaki ~350 px'i kapatır.
- Ana görseller x 150–930, y 380–1300 aralığında olmalı.
- Su kullanılan sahnelerde sıra şöyle olmalı: `ground`/`mountain` → `water` → gemi/karakter → `rain`.

## 6. Öğe kataloğu (özet)
Uzay: sun, earth, moon, planet, comet, asteroid, blackhole, stream, aurora, orbit
Doğa/hikâye: ground, mountain, water, rain, ark, animal (lion/elephant/giraffe/sheep/dove), light
İnsanlar: person (kind: scientist, miner, operator, agent, caveman, king, kid, plain, renaissance)
Eşyalar: telescope, pole, drill, eiffel, hammer, planks, calendar, frame, icon (satellite, gps, bulb, wifi,
phone, card, plane, tower, skull, clock, book, bomb)
Para: coin (melt), banknote, cart, pricetag, house, printer, wallet, simit
Efekt/yazı: spark, burst, cross, check, label (arrow, underline), bigtext, stamp
Yüz ifadeleri: angry, evil, scared, shocked, smug, sleepy, happy, neutral

Yeni öğe gerekiyorsa `elements.py` içinde `@element("ad")` ile eklenir. Önce bir test kâğıdına
(sheet) çizdirip bakılmalı.

## 7. Üretim
```bash
python3 -m doodle_explainer episodes/cuzdan_01_fakirlesme.json -o output/cuzdan_01.mp4 --preview
```
CPU'da 1 dakikalık video yaklaşık 15–25 dakika sürer (çoğu VoxCPM2 seslendirmesi). Hızlı bir deneme için
JSON'da `"tts": "edge"` (Microsoft Ahmet, internet gerekir) ya da `"tts": "ema"` (EMA Lightning) kullanılabilir.

## 8. Mevcut bölümler
- `episodes/01_carrington.json`: Kıyamet Dosyaları #1, 1859 Güneş fırtınası
- `episodes/02_nuhun_gemisi_short.json`: Nuh'un Gemisi Shorts sürümü
- `episodes/02_nuhun_gemisi.json`: Nuh'un Gemisi uzun hikâye sürümü (~3 dk)
- `episodes/03_apophis.json`: Apophis 2029
- `episodes/cuzdan_01_fakirlesme.json`: Cüzdan Dosyaları #1, fakirleşme + Machiavelli
- `KONULAR.md`: konu havuzu
