# MiniMax H3 音声・画像駆動動画生成 (Ref2VA / I2V / T2V) ガイド

MiniMax H3 (Hailuo 02/03 アーキテクチャ) を用いて、静止画と音声から自然なリップシンク・表情・頭部モーションを持つ高品質な動画（640x640 / 768p / 1080p）を生成するガイドである。

---

## 1. 特徴とアーキテクチャ

| 項目 | 内容 |
| :--- | :--- |
| **アーキテクチャ** | DiT (Diffusion Transformer) + Dual-VAE (Video VAE + Audio VAE) + Qwen3VL |
| **主要モデル** | `minimax_h3_fl2va_pruned_int8_convrot.safetensors` (約20GB, FLOW_AV) |
| **テキスト/画像エンコーダ** | `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` (約15GB, NVFP4 AWQ) |
| **高速化 LoRA** | `minimax_h3_fl2v_turbo_4step_v1.0_768p_comfyui_bf16.safetensors` (4-step Turbo) |
| **対応タスク** | **Ref2VA (画像+音声 -> 動画)**、Image-to-Video、Text-to-Video |
| **リップシンク精度** | **極めて高い**（顔の破綻がなく、歯並びや母音の口の動きが超リアル） |
| **必要 VRAM** | 24GB VRAM (NVIDIA L4 / A10G で動作可能) |

---

## 2. ディレクトリ構成

- `generate.py`: ComfyUI REST API と連携する MiniMax H3 Ref2VA 生成 CLI
- `gcp/setup.sh`: ComfyUI および MiniMax H3 量子化モデル（約34GB）の自動セットアップ
- `gcp/run_remote.sh`: VM 上での生成実行ラッパー
- `gcp/run_cloud.ps1`: ローカルから一発でインスタンス起動・生成・回収・停止を行うオーケストレータ

---

## 3. プロンプト記法 (Ref2VA)

MiniMax H3 の `MiniMaxH3ReferenceToVideo` ノードでは、入力リファレンスをプロンプト内で明示的にタグ付けしてバインドする：
- 画像: `<Picture 1>`
- 音声: `<Audio 1>`
- 動画: `<Video 1>`

**推奨プロンプト例**:
```text
<Picture 1> <Audio 1> A professional Japanese woman talking naturally and looking directly at the camera.
```

---

## 4. 実行方法

### ローカル PowerShell からクラウド一発実行 (`run_cloud.ps1`)
```powershell
.\models\minimax_h3\gcp\run_cloud.ps1 `
    -Image "examples/images/sample_portrait.jpg" `
    -Audio "examples/audios/sample_japanese_speech.mp3" `
    -Width 640 -Height 640 -Length 124
```
※ 完了後、インスタンスは自動で停止（TERMINATED）する。

### VM 内での直接実行 (`generate.py`)
```bash
python3 minimax_h3/generate.py \
    --image examples/images/sample_portrait.jpg \
    --audio examples/audios/sample_japanese_speech.mp3 \
    --prompt "<Picture 1> <Audio 1> A professional Japanese woman talking naturally and looking directly at the camera." \
    --width 640 \
    --height 640 \
    --length 124 \
    --steps 4 \
    --output_dir ./outputs
```

---

## 5. 実測ベンチマーク (NVIDIA L4 24GB VRAM / 640x640)

- **生成フレーム数**: 124 フレーム (24fps、約 5.17 秒)
- **全体所要時間**: **389.6 秒 (約 6 分 30 秒)**
  - Qwen3VL エンコード: 約 30 秒
  - DiT ロード & LoRA 適用: 約 30 秒
  - サンプリング (4 steps): 177 秒 (Step 1 初期化込 118s、以降 約 44s/step)
  - Video & Audio VAE デコード: 約 60 秒
- **品質所見**:
  - 音声トラックとの先頭同期ズレなし。
  - 発話時の歯の露出、舌・唇の動きが極めて自然。
