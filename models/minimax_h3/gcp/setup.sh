#!/bin/bash
set -e

echo "=== [1/4] Setting up ComfyUI and Dependencies for MiniMax H3 ==="
sudo apt-get update -y
sudo apt-get install -y git python3-pip python3-venv ffmpeg

COMFY_DIR="$HOME/ComfyUI"
if [ ! -d "$COMFY_DIR" ]; then
    echo "Cloning ComfyUI..."
    git clone https://github.com/comfyanonymous/ComfyUI.git "$COMFY_DIR"
fi

cd "$COMFY_DIR"
pip install --upgrade pip
pip install -r requirements.txt
pip install huggingface_hub "torch>=2.4.0" torchvision torchaudio --extra-index-url https://download.pytorch.org/whl/cu124
# 鬯ｯ・ｯ繝ｻ・ｮ郢晢ｽｻ繝ｻ・ｮ鬮｣蛹・ｽｽ・ｳ郢晢ｽｻ繝ｻ・ｻ鬮ｫ・ｴ繝ｻ・ｯ驕ｶ荳橸ｽ｣・ｹ郢晢ｽｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｨ: flash-attn 鬯ｯ・ｯ繝ｻ・ｩ髫ｰ・ｳ繝ｻ・ｾ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｵ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｺ鬯ｩ蟷｢・ｽ・｢髫ｴ雜｣・ｽ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｻ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｮ鬯ｯ・ｯ繝ｻ・ｩ髯晢ｽｷ繝ｻ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・｢鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｧ鬯ｩ蟷｢・ｽ・｢髫ｴ雜｣・ｽ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｻ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ鬯ｯ・ｯ繝ｻ・ｩ髯晢ｽｷ繝ｻ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・｢鬯ｮ・ｫ繝ｻ・ｴ鬮ｮ諛ｶ・ｽ・｣郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・｢鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｼ鬯ｯ・ｯ繝ｻ・ｩ髯晢ｽｷ繝ｻ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・｢鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｧ鬯ｩ蟷｢・ｽ・｢髫ｴ雜｣・ｽ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｻ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｹ鬯ｯ・ｯ繝ｻ・ｩ髯晢ｽｷ繝ｻ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・｢鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｧ鬯ｩ蟷｢・ｽ・｢髫ｴ雜｣・ｽ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｻ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｳ鬯ｯ・ｯ繝ｻ・ｩ髯晢ｽｷ繝ｻ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・｢鬯ｮ・ｫ繝ｻ・ｴ鬮ｮ諛ｶ・ｽ・｣郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・｢鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｳ鬯ｯ・ｯ繝ｻ・ｩ髯晢ｽｷ繝ｻ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・｢鬯ｮ・ｫ繝ｻ・ｴ髣包ｽｵ陷会ｽｱ郢晢ｽｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｻ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・｣鬯ｯ・ｩ隰ｳ・ｾ繝ｻ・ｽ繝ｻ・ｵ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｺ鬯ｩ蟷｢・ｽ・｢髫ｴ雜｣・ｽ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｻ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｹ鬯ｮ・ｫ繝ｻ・ｴ鬮ｮ諛ｶ・ｽ・｣郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・｢鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｫ鬯ｯ・ｯ繝ｻ・ｩ髫ｰ・ｳ繝ｻ・ｾ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｵ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｺ鬯ｩ蟷｢・ｽ・｢髫ｴ雜｣・ｽ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｻ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｯ鬯ｯ・ｯ繝ｻ・ｮ郢晢ｽｻ繝ｻ・｣鬮ｯ蜈ｷ・ｽ・ｹ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｽ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｳ鬯ｯ・ｮ繝ｻ・ｯ髫ｴ雜｣・ｽ・｢郢晢ｽｻ繝ｻ・｣郢晢ｽｻ繝ｻ・ｰ鬯ｯ・ｮ繝ｻ・ｮ髫ｲ蟷｢・ｽ・ｶ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・｣鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｦ鬯ｯ・ｩ陝ｷ・｢繝ｻ・ｽ繝ｻ・｢鬮ｫ・ｴ髮懶ｽ｣繝ｻ・ｽ繝ｻ・｢驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｻ鬯ｩ蟷｢・ｽ・｢髫ｴ雜｣・ｽ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｻ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｼ鬯ｯ・ｩ陝ｷ・｢繝ｻ・ｽ繝ｻ・｢鬮ｫ・ｴ髮懶ｽ｣繝ｻ・ｽ繝ｻ・｢驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｻyTorch 2.9+ 鬯ｯ・ｯ繝ｻ・ｩ髯晢ｽｷ繝ｻ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・｢鬯ｮ・ｫ繝ｻ・ｴ髯ｷ・ｿ陷ｴ繝ｻ・ｽ・ｽ繝ｻ・ｨ鬮ｮ蜈ｷ・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｺ鬩幢ｽ｢繝ｻ・ｧ髣費ｽｨ陞滂ｽｲ繝ｻ・ｽ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｸ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｺ鬯ｩ蟷｢・ｽ・｢髫ｴ雜｣・ｽ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｻ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｹ鬯ｮ・ｫ繝ｻ・ｴ髫ｰ・ｫ繝ｻ・ｾ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｴ鬯ｩ蟷｢・ｽ・｢髫ｴ雜｣・ｽ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｻ鬯ｯ・ｩ隰ｳ・ｾ繝ｻ・ｽ繝ｻ・ｵ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｺ鬯ｩ蟷｢・ｽ・｢髫ｴ雜｣・ｽ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｻ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｹ鬯ｮ・ｫ繝ｻ・ｴ髫ｰ・ｫ繝ｻ・ｾ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｴ鬯ｩ蟷｢・ｽ・｢髫ｴ雜｣・ｽ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｻSDPA 鬯ｯ・ｯ繝ｻ・ｩ髫ｰ・ｳ繝ｻ・ｾ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｵ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｺ鬯ｯ・ｩ陝ｷ・｢繝ｻ・ｽ繝ｻ・｢鬮ｫ・ｴ髮懶ｽ｣繝ｻ・ｽ繝ｻ・｢驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｻFlashAttention2 鬯ｯ・ｯ繝ｻ・ｮ郢晢ｽｻ繝ｻ・｣鬯ｮ・ｮ陷茨ｽｷ繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・｣驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｰ鬯ｯ・ｮ繝ｻ・ｯ郢晢ｽｻ繝ｻ・ｷ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｻ鬯ｯ・ｨ繝ｻ・ｾ鬮ｮ諛ｶ・ｽ・｣郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｯ鬯ｮ・ｯ繝ｻ・ｷ鬮｣魃会ｽｽ・ｨ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｱ鬯ｯ・ｯ繝ｻ・ｩ髫ｰ・ｳ繝ｻ・ｾ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｵ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｺ鬯ｩ蟷｢・ｽ・｢髫ｴ雜｣・ｽ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｻ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｧ鬯ｯ・ｯ繝ｻ・ｮ郢晢ｽｻ繝ｻ・ｯ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｷ鬯ｮ・ｯ繝ｻ・ｷ郢晢ｽｻ繝ｻ・･驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｲ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｩ鬯ｩ蟷｢・ｽ・｢郢晢ｽｻ繝ｻ・ｧ鬮ｫ・ｰ郢晢ｽｻ遶乗ｧｭ繝ｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｽ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ鬯ｯ・ｮ繝ｻ・ｫ郢晢ｽｻ繝ｻ・ｲ鬮ｯ譎｢・ｽ・ｶ髯晢ｽｷ繝ｻ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｲ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｩ鬯ｩ蟷｢・ｽ・｢髫ｴ雜｣・ｽ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｻ鬯ｯ・ｯ繝ｻ・ｩ髯晢ｽｷ繝ｻ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・｢鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｧ鬯ｯ・ｮ繝ｻ・｣髯具ｽｹ郢晢ｽｻ繝ｻ・ｽ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｵ鬯ｮ・ｫ繝ｻ・ｴ髫ｰ・ｫ繝ｻ・ｾ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｶ鬯ｯ・ｮ繝ｻ・ｯ髫ｶ蜴・ｽｽ・ｸ郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｺ鬯ｯ・ｯ繝ｻ・ｩ髯晢ｽｷ繝ｻ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・｢鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｧ鬯ｯ・ｩ陝ｷ・｢繝ｻ・ｽ繝ｻ・｢鬮ｫ・ｴ髮懶ｽ｣繝ｻ・ｽ繝ｻ・｢驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｻ鬯ｩ蟷｢・ｽ・｢髫ｴ雜｣・ｽ・｢郢晢ｽｻ繝ｻ・ｽ郢晢ｽｻ繝ｻ・ｻ鬩幢ｽ｢隴趣ｽ｢繝ｻ・ｽ繝ｻ・ｻ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｼ鬯ｯ・ｩ陝ｷ・｢繝ｻ・ｽ繝ｻ・｢鬮ｫ・ｴ髮懶ｽ｣繝ｻ・ｽ繝ｻ・｢驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｽ驛｢譎｢・ｽ・ｻ郢晢ｽｻ繝ｻ・ｻ
echo "=== [2/4] Downloading MiniMax H3 Quantized Models ==="
python3 - << 'EOF'
import os
import shutil
from huggingface_hub import hf_hub_download

repo = "Comfy-Org/MiniMax-H3"
comfy_home = os.path.expanduser("~/ComfyUI")

models_to_download = [
    ("vae/minimax_h3_video_vae_int8_convrot.safetensors", "models/vae/minimax_h3_video_vae_int8_convrot.safetensors"),
    ("vae/minimax_h3_audio_vae_fp32.safetensors", "models/vae/minimax_h3_audio_vae_fp32.safetensors"),
    ("diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors", "models/diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors"),
    ("text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "models/text_encoders/qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors"),
    ("loras/minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors", "models/loras/minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors"),
]

for remote_file, local_rel in models_to_download:
    dest = os.path.join(comfy_home, local_rel)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest) and os.path.getsize(dest) > 1024 * 1024:
        print(f"[Exists] {dest} ({os.path.getsize(dest)/(1024*1024):.1f} MB)")
        continue
    if os.path.islink(dest) or os.path.lexists(dest):
        os.remove(dest)
    print(f"[Resolving] {remote_file} -> {dest} ...")
    downloaded_path = hf_hub_download(
        repo_id=repo,
        filename=remote_file,
    )
    real_path = os.path.realpath(downloaded_path)
    if not os.path.exists(dest):
        try:
            os.link(real_path, dest)
        except OSError:
            shutil.copy2(real_path, dest)
    print(f"[Ready] {dest} -> {real_path} ({os.path.getsize(dest)/(1024*1024):.1f} MB)")

print("MiniMax H3 Ref2VA models download complete!")
EOF

echo "=== [3/4] Verifying Model Files ==="
ls -lh "$COMFY_DIR/models/diffusion_models/"
ls -lh "$COMFY_DIR/models/text_encoders/"
ls -lh "$COMFY_DIR/models/vae/"
ls -lh "$COMFY_DIR/models/loras/"

echo "=== [4/4] Starting ComfyUI Server ==="
pkill -f 'python3 main.py' || true
nohup python3 "$COMFY_DIR/main.py" --listen 127.0.0.1 --port 8188 > "$HOME/comfyui.log" 2>&1 &
echo "ComfyUI running in background. Waiting for startup..."
sleep 8
curl -s http://127.0.0.1:8188/system_stats || true
echo "Setup complete!"
