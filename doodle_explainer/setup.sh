#!/usr/bin/env bash
# Doodle Explainer kurulumu (Linux/macOS, Python 3.11-3.13, ffmpeg gerekli)
# Kullanım: bash doodle_explainer/setup.sh            -> hepsi
#           bash doodle_explainer/setup.sh --hafif    -> sadece edge/piper sesleri (torch yok)
set -euo pipefail

command -v ffmpeg >/dev/null || { echo "ffmpeg bulunamadı: sudo apt install ffmpeg  /  brew install ffmpeg"; exit 1; }

# 1) Ana ortam: render + altyazı hizalama + hafif ses motorları
python3 -m pip install -q pillow numpy fonttools faster-whisper edge-tts piper-tts

if [[ "${1:-}" == "--hafif" ]]; then
  echo "Hafif kurulum tamam. JSON'da \"tts\": \"edge\" veya \"piper\" kullan."; exit 0
fi

# 2) Torch ortamı (VoxCPM2 tasarlanmış sesler + EMA Lightning). Ayrı venv: ~3-5 GB
VENV="${DOODLE_TORCH_VENV:-$HOME/.cache/doodle_explainer/cbx}"
python3 -m venv "$VENV"
if [[ "$(uname)" == "Linux" ]] && ! command -v nvidia-smi >/dev/null; then
  # NVIDIA yoksa CPU torch (indirme küçük). Bu adres engelliyse PyPI'deki varsayılan torch kurulur.
  "$VENV/bin/pip" install -q torch torchaudio --index-url https://download.pytorch.org/whl/cpu || true
fi
"$VENV/bin/pip" install -q voxcpm ema-lightning soundfile "setuptools<81"
echo "Kurulum tamam. Torch python: $VENV/bin/python3  (başka yerdeyse: export DOODLE_TORCH_PY=...)"
echo "İlk çalıştırmada VoxCPM2 modeli (~5 GB) HuggingFace'ten indirilir."
