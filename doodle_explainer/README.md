# Doodle Explainer: "Kıyamet Dosyaları" tarzı Shorts üretici

"Conspiracy explainer" türünde dikey (1080×1920) Shorts üretir. Referans tarz şöyle:

- **Görsel:** lacivert yıldızlı fon, Paint'te çizilmiş gibi titrek çizgiler, beyaz kâğıt kenarlı
  kesik (cut-out) figürler, el yazısı etiketler ve oklar, kırmızı mühürler, stop-motion titremesi.
- **Anlatım:** coşkulu, "size kimsenin söylemediğini anlatıyorum" tonu, kısa cümleler, her sahnede yeni bir şok.
- **Kurgu:** sahne başına bir fikir, ani kesmeler ve punch-in zoom, pop/whoosh/mühür ses efektleri,
  karanlık synth altlığı, kelime kelime sarı vurgulu altyazı.

Bölümün tamamı bir JSON dosyasıdır; kod yazmadan yeni video üretilir.

```bash
python3 -m doodle_explainer doodle_explainer/episodes/01_carrington.json -o output/01_carrington.mp4
```

Çıktılar: `.mp4`, `_thumb.jpg` (kapak karesi), `_meta.txt` (başlık, açıklama, etiketler).

## Kurulum

```bash
pip install piper-tts faster-whisper pillow numpy fonttools   # temel + hizalama
# Daha doğal ve coşkulu Türkçe ses için (isteğe bağlı, ~3 GB):
python3 -m venv ~/.cache/doodle_explainer/cbx
~/.cache/doodle_explainer/cbx/bin/pip install chatterbox-tts "setuptools<81"
```

- `"tts": "piper"`: hızlıdır ve offline çalışır, ses biraz robotik (`tr_TR-dfki-medium`, ilk kullanımda indirilir).
- `"tts": "chatterbox"`: doğal ve duygulu ses verir. `exaggeration` coşku düzeyini ayarlar.
  Her sahne Whisper ile yazıya dökülür; metinle benzerliği `min_similarity` değerinin altında kalan sahne
  farklı bir seed ile yeniden üretilir (transkript kontrolü).
- Altyazılar faster-whisper kelime zaman damgalarıyla sese hizalanır.

## Bölüm JSON'u

```jsonc
{
  "series": "KIYAMET DOSYALARI", "episode": 1,
  "tts": "chatterbox", "chatterbox": {"exaggeration": 0.7, "cfg_weight": 0.35},
  "speed": 1.06,
  "scenes": [
    {
      "bg": "space",                       // space | night | alert | dawn | paper
      "text": "1 Eylül 1859...",           // ekrandaki altyazı
      "say":  "Bir Eylül, bin sekiz yüz...", // seslendirilen metin (sayıları yazıyla yaz)
      "elements": [
        {"type": "sun", "mood": "evil", "size": 470, "x": 330, "y": 640,
         "in": "pop", "at": 0.0, "loop": "pulse"}
      ]
    }
  ]
}
```

**Öğeler (`type`):** `sun`, `earth`, `moon`, `planet`, `comet`, `blackhole`, `person`
(`kind`: scientist / miner / operator / agent / caveman / king / kid / plain; `pose`: point / up / hold / down;
`prop`: pan / sign / phone / key), `telescope`, `pole`, `spark`, `burst`, `icon` (`what`: satellite / gps / bulb /
wifi / phone / card / plane / tower / skull / clock / book / bomb), `calendar`, `frame` (iğneli not),
`orbit`, `ground`, `cross`, `check`, `stream` (akan parçacıklar), `aurora`, `label` (el yazısı + `arrow`),
`bigtext`, `stamp`.

**Yüz ifadeleri (`mood`):** angry, evil, scared, shocked, smug, sleepy, happy, neutral.

**Giriş animasyonu (`in`):** pop, stamp (ekranı sarsar), slide_l, slide_r, slide_u, drop, fade, grow, none.
`at` değeri sahne süresinin oranıdır (0–1).
**Döngü (`loop`):** float, shake, pulse, wiggle, spin, bob (`loop_amp` ile şiddet ayarlanır).
Ayrıca `move: [x, y]` + `move_t`, `rot`, `scale`, `sfx` (pop / stamp / zap / boom / ding / whoosh) verilebilir.

Tuval 1080×1920 boyutundadır. Üstteki seri başlığı y≈160'ta, altyazı y≈1470'te durur.
Shorts arayüzü alttaki ~350 px'i kapattığı için ana görseller y 350–1250 arasına yerleştirilmeli.
