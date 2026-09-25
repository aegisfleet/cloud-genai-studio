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

- `generate.py`: ComfyUI REST API と連携する MiniMax H3 Ref2VA 生成 CLI（プロンプトタグ自動整形、任意音声対応）
- `gcp/setup.sh`: ComfyUI および MiniMax H3 量子化モデル（約35GB）の高速自動セットアップ
- `gcp/run_remote.sh`: VM 上での生成実行ラッパー（ComfyUI 応答待機ループ内蔵）
- `gcp/run_cloud.ps1`: ローカルから一発でインスタンス起動・生成・回収・停止を行うオーケストレータ

---

## 4. プロンプト記法 (Ref2VA)

MiniMax H3 の `MiniMaxH3ReferenceToVideo` ノードでは、入力リファレンスをプロンプト内で明示的にタグ付けしてバインドする：
- 画像: `<Picture 1>`
- 音声: `<Audio 1>` (オプション、指定なしの場合は効果音・BGMを自律生成)
- 動画: `<Video 1>`

※ 本リポジトリの `generate.py` では、SNS や Web UI で普及している **`@[character ref]` などのメンション記法を自動検出し、内部で `<Picture 1>` へバインド**する。タグが省略されている場合も自動で先頭に `<Picture 1>` を付与する。

**プロンプト例（SNS キャラクター公開カットイン演出）**:
```text
Create a fast, striking character reveal using @[character ref]. Preserve identity, proportions, outfit and original rendering style...
Use exactly 10 fast-cut shots progressing upward: feet, lower legs, knees/thighs, hips/waist, hand beside torso...
Sync editing, contour animation and graphic accents to character-appropriate music and precise sound details.
```

---

## 5. 実行方法

### ローカル PowerShell からクラウド一発実行 (`run_cloud.ps1`)

**15秒キャラクター動画生成 (640x640 / 360 frames)**:
```powershell
.\models\minimax_h3\gcp\run_cloud.ps1 `
    -Image "examples/images/hoshimi_miyabi.png" `
    -PromptFile "examples/prompts/miyabi_reveal.txt" `
    -Width 640 -Height 640 -Length 360
```
※ 完了後、成果物は `outputs/` に自動ダウンロードされ、インスタンスは自動で停止（TERMINATED）する。

### VM 内での直接実行 (`generate.py`)
```bash
python3 minimax_h3/generate.py \
    --image /path/to/character.png \
    --prompt_file /path/to/prompt.txt \
    --width 640 \
    --height 640 \
    --length 360 \
    --steps 4 \
    --output_dir ./outputs
```

---

## 6. 実測ベンチマーク (NVIDIA L4 24GB VRAM / 640x640)

- **短尺テスト (124 frames / 約5.17秒)**: 全体所要時間 **約 6 分 30 秒**
- **フル 15秒 (360 frames / 24fps)**: 全体所要時間 **約 10 〜 12 分**
  - Qwen3VL エンコード: 約 30 秒
  - DiT ロード & LoRA 適用: 約 30 秒
  - サンプリング (4 steps Turbo): 約 7 〜 8 分
  - Video & Audio VAE デコード: 約 2 〜 3 分
- **品質所見**:
  - 静止画から10カット以上の高速カメラワーク・カット割り・身体追従エフェクトラインを滑らかに補間生成。
  - キャラクターのプロポーションと服飾ディテールを極めて高い精度で維持。
