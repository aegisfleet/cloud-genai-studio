# MiniMax H3 音声・画像駆動動画生成 (Ref2VA / I2V / T2V) ガイド

MiniMax H3 (Hailuo 02/03 アーキテクチャ) を用いて、静止画と音声から自然なリップシンク・表情・頭部モーションを持つ高品質な動画（640x640 / 768p / 1080p、最大15秒）を生成するガイドである。

---

## 1. 特徴とアーキテクチャ

| 項目 | 内容 |
| :--- | :--- |
| **アーキテクチャ** | DiT (Diffusion Transformer) + Dual-VAE (Video VAE + Audio VAE) + Qwen3VL |
| **主要モデル (Ref2VA)** | `minimax_h3_ref2va_pruned_int8_convrot.safetensors` (約20GB, Reference-to-Video) |
| **主要モデル (FL2VA)** | `minimax_h3_fl2va_pruned_int8_convrot.safetensors` (約20GB, First-Last-Frame / I2V) |
| **テキスト/画像エンコーダ** | `qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors` (約15GB, NVFP4 AWQ) |
| **高速化 LoRA** | `minimax_h3_ref2v_turbo_4step_v0.1_comfyui_bf16.safetensors` (4-step Turbo) |
| **対応タスク** | **Ref2VA (キャラクター参照 -> 15秒動画+自律音響合成)**、Image-to-Video、Text-to-Video |
| **アテンション最適化** | **PyTorch 2.9+ ネイティブ SDPA** (FlashAttention2 互換、**ソースコンパイル不要**) |
| **必要 VRAM** | 24GB VRAM (NVIDIA L4 / A10G で動作可能、ホストRAM 32GB 推奨) |

---

## 2. 環境構築に関する重要事項（FlashAttention コンパイル不要）

> [!NOTE]
> **FlashAttention のソースコンパイルは不要である。**
> 
> クラウド VM（`pytorch-2-9-cu129-ubuntu-2204-nvidia-580` 等）環境には、PyTorch 2.9 (cu129) が事前インストールされている。PyTorch 2.x の `torch.nn.functional.scaled_dot_product_attention` (SDPA) には NVIDIA Ada Lovelace / Hopper 向けに最適化された FlashAttention2 / Memory-Efficient Attention 実装がすでにバイナリとして組み込まれている。
> 
> ComfyUI は SDPA を最優先で自動適用するため、スタンドアロンの `flash-attn` パッケージをソースビルド（1,100以上の CUDA カーネルのコンパイル、約30〜60分）する必要はない。これにより、セットアップ時間は従来の約40分から **約3〜5分（モデルダウンロード時間のみ）** へ劇的に短縮される。

---

## 3. ディレクトリ構成

- `generate.py`: ComfyUI REST API と連携する MiniMax H3 Ref2VA 生成 CLI（複数画像リファレンス、プロンプトタグ自動整形、任意音声対応）
- `gcp/run_cloud.py`: **（推奨）** OS 非依存のネイティブ Python クラウドオーケストレータ（複数参照・画像リストファイル対応、自動起動・回収・停止）
- `gcp/run_cloud.ps1`: Windows PowerShell 版クラウド実行スクリプト
- `gcp/run_remote.sh`: VM 上での生成実行ラッパー（ComfyUI 応答待機ループ内蔵）
- `gcp/setup.sh`: ComfyUI および MiniMax H3 量子化モデル（約35GB）の高速自動セットアップ

---

## 4. プロンプト記法と高品質化ノウハウ (Ref2VA)

### 複数リファレンス（Multi-Reference）による視点・カット割り改善
単一の全身立ち絵のみを入力すると、背面やアングル変化の情報を補間しきれず、**被写体がその場で360度ぐるぐる回転するような縮退モーション**になりやすい。

**推奨手法**:
全身立ち絵（`<Picture 1>`）に加えて、Gemini（Imagen 3）等で生成した主要パーツ画像を複数用意し、プロンプト内の各ショットに対応付ける：
- `<Picture 1>`: メイン全身立ち絵
- `<Picture 2>`: 足元・ハイヒールブーツ（ローアングル・ステップ）
- `<Picture 3>`: 手元・刀の柄や鍔（抜刀・アクション）
- `<Picture 4>`: 横顔・獣耳・鋭い眼光（クローズアップ・表情）

プロンプト内では各ショットに対応するタグを記述する：
```text
Shot 1: Tight low-angle close-up of feet and lower legs <Picture 2>...
Shot 5: Rapid tracking shot of hand drawing sword hilt <Picture 3>...
Shot 8: Intense profile close-up on eyes and face <Picture 4>...
Shot 10: First full head-to-toe hero reveal <Picture 1>...
```

### 音響（Audio）品質と効果音（SFX）特化のベストプラクティス
- **サンプラーとステップ数**: 4-step Turbo + `res_multistep` は映像生成には高速だが、Audio VAE の潜在空間が収束せずホワイトノイズや音割れを起こしやすい。**`euler` サンプラー + 8 steps** を推奨する。
- **BGM を排除し効果音のみを生成する場合**: プロンプト冒頭で `NO background music, NO melody` と明示的に禁止し、各カットに具体的な物理音（金属の抜刀音、電撃スパーク音、ヒールの足音、風切り音など）を指定する。

---

## 5. 実行方法

### クラウド一発実行 (Python オーケストレータ `run_cloud.py` 推奨)

複数画像参照リスト（`examples/images/miyabi_reveal_images.txt`）を用いた 15秒動画生成：
```bash
python models/minimax_h3/gcp/run_cloud.py \
    --image_file examples/images/miyabi_reveal_images.txt \
    --prompt_file examples/prompts/miyabi_reveal_sfx_multi.txt \
    --steps 8 \
    --sampler euler \
    --length 360
```
※ 完了後、成果物は `outputs/` に自動ダウンロードされ、インスタンスは自動で停止（TERMINATED）する。

PowerShell から実行する場合は `run_cloud.ps1` も利用可能：
```powershell
.\models\minimax_h3\gcp\run_cloud.ps1 `
    -ImageFile "examples/images/miyabi_reveal_images.txt" `
    -PromptFile "examples/prompts/miyabi_reveal_sfx_multi.txt" `
    -Steps 8 -Sampler "euler" -Length 360
```

### VM 内での直接実行 (`generate.py`)
```bash
python3 minimax_h3/generate.py \
    --images /path/to/img1.png /path/to/img2.png \
    --prompt_file /path/to/prompt.txt \
    --width 640 \
    --height 640 \
    --length 360 \
    --steps 8 \
    --sampler euler \
    --output_dir ./outputs
```

---

## 6. 実測ベンチマーク (NVIDIA L4 24GB VRAM / 640x640)

- **高速 4-step Turbo (360 frames / 15秒)**: 所要時間 **約 10 〜 12 分**
- **高品質 8-step Euler (360 frames / 15秒)**: 所要時間 **約 26 分**
  - Qwen3VL + DiT 初期化: 約 3 分 20 秒
  - サンプリング (8 steps): 約 21 分 10 秒（1ステップあたり約 155〜160 秒）
  - Video & Audio VAE デコード: 約 1 〜 2 分
  - VRAM 使用量: ピーク約 22.3 GB / 23.0 GB（L4 の容量内で安定稼働）
- **品質所見**:
  - 4枚のマルチアングル参照画像と 8-step Euler により、被写体回転の縮退が解消され、10カットの明確なアングル遷移と精緻な SFX（抜刀・風切り音）の同期が達成される。

