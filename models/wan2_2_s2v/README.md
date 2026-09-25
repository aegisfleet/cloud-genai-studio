# Wan2.2-S2V 音声駆動動画生成 (Sound-to-Video) ガイド

参照画像（静止画1枚）とオーディオ音声（MP3/WAV）を入力し、音声のリズムや発話に自然に同期した口パク・表情・頭部の動きを持つ高品質な動画を生成する環境である。
[ComfyUI Wan2.2-S2V ワークフロー (02b3722db38c)](https://comfy.org/workflows/video_wan2_2_14B_s2v-02b3722db38c/) をベースに、CLI 完全自動化、先頭リップシンクズレの自動補正、マルチチャンク長尺生成を実装している。

---

## 1. 特徴とスペック

| 項目 | 内容 |
| :--- | :--- |
| **主用途** | **Sound-to-Video (画像 ＋ 音声 -> 音声同期動画)** |
| **主要モデル** | `wan2.2_s2v_14B_fp8_scaled.safetensors` (約16GB, 14B DiT) |
| **テキストエンコーダ** | `umt5_xxl_fp8_e4m3fn_scaled.safetensors` (約6.3GB) |
| **VAE** | `wan_2.1_vae.safetensors` (約240MB) |
| **高速化 LoRA** | `wan2.2_t2v_lightx2v_4steps_lora_v1.1_high_noise.safetensors` (4-step, CFG 1.0) |
| **VRAM 効率** | **14B FP8 Scaled により 24GB VRAM (NVIDIA L4) で余裕動作** |
| **長尺対応** | **チャンク分割（77フレーム / 約4.8秒 単位）で10秒〜20秒超の長尺動画に対応** |
| **リップシンク最適化** | **`--skip_first_frames 4` により先頭 190ms の口パク遅延を完全解消** |

---

## 2. ディレクトリ構成

- `generate.py`: ComfyUI REST API と連携する Wan2.2-S2V 生成 CLI
- `gcp/setup.sh`: ComfyUI および Wan2.2-S2V モデル（合計約 23.5GB）の自動セットアップ
- `gcp/run_remote.sh`: VM 上での生成実行ラッパー
- `gcp/run_cloud.ps1`: ローカルから一発でインスタンス起動・生成・回収・停止を行うオーケストレータ
- `workflows/video_wan2_2_14B_s2v.json`: ベースとなるワークフロー定義

---

## 3. 実測ベンチマーク (NVIDIA L4 24GB VRAM)

| 解像度 | チャンク数 / 生成長 | サンプリング時間 | 全体所要時間 |
| :--- | :--- | :--- | :--- |
| **1280×720 (720p)** | 1 chunk (81f / 約5.0秒) | 約 370 秒 (92s/step) | **567.9 秒 (約 9 分 28 秒)** |
| **640×640 (正方形)** | 1 chunk (81f / 約5.0秒) | 約 158 秒 (39.5s/step) | **255.4 秒 (約 4 分 15 秒)** |
| **832×480 (横長)** | 1 chunk (81f / 約5.0秒) | 約 154 秒 (38.5s/step) | **252.4 秒 (約 4 分 12 秒)** |
| **640×640 (長尺 3チャンク)** | 3 chunks (237f / 約14.8秒) | 約 485 秒 (約 8 分 05 秒) | **597.9 秒 (約 9 分 57 秒)** |

---

## 4. 実行方法

### ローカル PowerShell からクラウド一発実行 (`run_cloud.ps1`)

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;
.\models\wan2_2_s2v\gcp\run_cloud.ps1 `
    -InputImage "examples/images/sample_portrait.jpg" `
    -InputAudio "examples/audios/sample_japanese_speech.mp3" `
    -Width 640 -Height 640 `
    -SkipFirstFrames 4 `
    -OutputFilename "wan2_2_s2v_640x640_synced.mp4"
```

### 長尺動画を生成する場合 (例: 12秒音声に対して 3 チャンク生成)

```powershell
.\models\wan2_2_s2v\gcp\run_cloud.ps1 `
    -InputImage "examples/images/sample_portrait.jpg" `
    -InputAudio "examples/audios/sample_japanese_speech.mp3" `
    -Width 640 -Height 640 `
    -NumChunks 3 `
    -SkipFirstFrames 4 `
    -OutputFilename "wan2_2_s2v_12s_japanese.mp4"
```

### VM 内での直接実行 (`generate.py`)

```bash
python3 wan2_2_s2v/generate.py \
    --workflow wan2_2_s2v/workflows/video_wan2_2_14B_s2v.json \
    --image examples/images/sample_portrait.jpg \
    --audio examples/audios/sample_japanese_speech.mp3 \
    --width 640 \
    --height 640 \
    --num_chunks 1 \
    --skip_first_frames 4 \
    --lora lightx2v_4steps \
    --steps 4 \
    --output ./outputs/wan2_2_s2v_640x640.mp4
```

---

## 5. リップシンク同期の最適化ノウハウ

Wan2.2-S2V では先頭の数フレーム（約4フレーム / 190ms）において、静止画から動画へのトランジションによる過剰焼き込みや口の立ち上がり遅延が発生しやすい。
CLI に追加された `--skip_first_frames 4` オプションを有効にすることで、動画の先頭4フレームを自動クロップし、音声の開始位置とぴったり同期させることができる。
