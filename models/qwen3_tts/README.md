# Qwen3-TTS 日本語音声生成スタジオ

Alibaba Cloud のオープンソース多言語音声合成モデル [Qwen3-TTS](https://github.com/QwenLM/Qwen3-TTS) を用いた日本語音声生成環境。Google Cloud（NVIDIA L4 GPU）上で高速推論および音声合成を行う。

---

## 1. モデル仕様と推奨インフラ環境

| 項目 | 仕様・推奨値 |
| :--- | :--- |
| **対象モデル** | `Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice`（1.7B, 12Hz コーデック） |
| **推奨アクセラレータ** | NVIDIA L4 (24GB VRAM) / G2シリーズ (`g2-standard-4`) |
| **Attention実装** | `sdpa` (PyTorch Native Scaled Dot Product Attention) |
| **データ型** | `torch.bfloat16`（L4ネイティブ対応） |
| **サンプリングレート** | 24,000 Hz |
| **推論速度 (L4)** | 10秒の音声に対し約 20〜25秒生成 (RTF: ~2.2) |

> **T4 (16GB) との比較検証結果**:
> - T4でもVRAM（16GB）には収まるが、FlashAttention-2非対応かつハードウェアレベルでのbfloat16非対応のため、`float16` への切り替えと `sdpa` 指定が必要となる。
> - L4（G2シリーズ）は公式推奨の `bfloat16` がネイティブに動作し、環境構築のトラブルが最も少なく推論も高速である。

---

## 2. 利用可能なスピーカー（Speaker ID）と検証結果

日本語の発話において、プリセット話者ごとの声質や語尾の余韻特性を検証済みである。

| Speaker ID | 特徴・声質 | 日本語の自然さ・余韻 | 推奨用途 |
| :--- | :--- | :--- | :--- |
| **`ono_anna`** | 落ち着いた自然な日本語女性ボイス | 非常にクリア。語尾パディングと相性が良い | **公式推奨・標準話者** |
| **`serena`** | 温かみのある柔らかい女性ボイス | **発話テンポがゆったりしており、余韻が最も自然** | **物語朗読・ナレーション推奨** |
| **`sohee`** | クールで落ち着いたトーンの女性ボイス | 歯切れが良く聞き取りやすい | 案内・アシスタント向き |
| **`uncle_fu`** | 渋く深みのある低音男性ボイス | 語尾までしっかり発音される | ドキュメンタリー・男性ナレーション |
| **`ryan`** | 明るく爽やかな青年男性ボイス | 快活で聞き取りやすい | プレゼンテーション・会話 |

---

## 3. 重要：末尾途切れ（ぶつ切り感）の防止と余韻確保

LLMベースの音声自己回帰モデル特有の現象として、**「文末直後に早期に終了トークン（EOS）が出力され、最後の母音や減衰音がカットされる問題」**、および **「音声終了直後のプレーヤー停止によるギリギリ感」** がある。

### 検証から得られたベストプラクティス（3段防御）

1. **三点リーダーによる余白確保**:
   テキスト末尾を `rstrip("。") + "……。"` と変換することで、モデルに文末の減衰トークンを物理的に生成させる。
2. **語尾プロンプト指示（`instruct`）**:
   `instruct="語尾の余韻を大切に、優しく落ち着いた日本語で話してください"` を与えることで、文末の急なテンポアップを抑える。
3. **波形末尾の無音パディング（Zero Padding） 【標準実装】**:
   生成されたオーディオ波形の末尾に **0.5秒の無音マージン（`--pad_silence 0.5`）** を自動付加して保存する。再生終了時のぶつ切り感が完全に解消される。

---

## 4. 実行手順

### ① ローカルの Windows PowerShell からクラウド自動実行（推奨）

ローカルの Windows PowerShell から、GCP VM の起動確認・スクリプト転送・音声生成・成果物（wav）の [outputs/](../../outputs) へのダウンロード・VM停止（課金ストップ）までを 1 コマンドで実行できる。

```powershell
# 基本実行 (デフォルト話者: ono_anna、末尾自動保護 + 0.5sパディング、完了後VM停止)
.\models\qwen3_tts\gcp\run_cloud.ps1 -Text "初めまして。Qwen3-TTSの日本語音声モデル検証へようこそ。"

# 話者を serena（余韻が自然な女性話者）に変更し、ファイル名を指定する場合
.\models\qwen3_tts\gcp\run_cloud.ps1 `
    -Text "明日の天気は晴れ時々曇りでしょう。" `
    -Speaker "serena" `
    -Instruct "ニュースキャスターのように落ち着いた明瞭なトーンで" `
    -OutputFilename "weather_report.wav"

# 連続生成のためVMを停止させずに起動維持する場合
.\models\qwen3_tts\gcp\run_cloud.ps1 -Text "テスト音声です。" -KeepRunning
```

### ② VM上で直接実行する場合

VMにSSH接続して実行する手順：

```bash
# 1. SSH接続
gcloud compute ssh qwen3-tts-vm --zone=asia-northeast1-b

# 2. 環境アクティベート
conda activate qwen3-tts

# 3. 音声生成スクリプト実行
python generate.py \
    --text "初めまして。Qwen3-TTSの日本語音声モデル検証へようこそ。" \
    --speaker ono_anna \
    --instruct "優しく自然な日本語で話してください" \
    --pad_silence 0.5 \
    --output outputs/my_audio.wav
```

### ③ 各種オプション一覧 (`generate.py`)

- `--text`: 発話させるテキスト
- `--speaker`: 話者ID（`ono_anna`, `serena`, `sohee`, `uncle_fu`, `ryan` 等）
- `--instruct`: 話し方やトーンのプロンプト指示
- `--temperature`: サンプリング温度（デフォルト: `0.9`）
- `--pad_silence`: 末尾に追加する無音秒数（デフォルト: `0.5` 秒）
- `--no_tail_padding`: 自動の末尾三点リーダー変換を無効化する場合に指定
- `--output`: 出力ファイルパス（デフォルト: `outputs/<timestamp>_qwen3_tts_<speaker>.wav`）

---

## 5. 出力先

生成された音声ファイル（.wav）はすべて、リポジトリルート直下の [outputs/](../../outputs) ディレクトリに保存される。
