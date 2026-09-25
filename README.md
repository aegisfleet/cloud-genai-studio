# Cloud GenAI Studio

**Google Cloud (NVIDIA L4 24GB Spot インスタンス)** を最大限に活用し、最新の重量級生成AIモデル（音楽・動画・音声）をローカル環境のような手軽さで検証・運用するための**実践的ノウハウ集＆自動化オーケストレーター**である。

---

## 🌟 リポジトリの目的・コアバリュー

最新のオープンウェイト生成AIモデル（14B動画モデル、3B音楽モデル、マルチモーダルDiTなど）は驚異的な表現力を誇る一方、**24GB以上のGPU VRAM** と **数十〜百GB超のディスク領域** を要求する。一般的なローカルPCやゲーミングGPUでは動作が難しく、クラウド常時起動では多額の費用が発生するという課題がある。

本リポジトリでは以下のアーキテクチャにより、**「極限の低コスト」** と **「ローカル作業のようなワンコマンド自動化」** を両立させるノウハウを蓄積・体系化している。

1. **GCP Spot インスタンスによる圧倒的低コスト運用**:
   - 通常料金の約 60〜70% 割引となる Spot インスタンス（NVIDIA L4 24GB VRAM）を活用（約 50〜70 円 / 時間）。
   - 1曲の音楽生成や1本の高品質動画生成にかかるクラウド費用は**わずか数円〜数十円**。
2. **完全自動化ワンコマンド・オーケストレーター**:
   - ローカルの PowerShell からワンコマンド実行するだけで、**「インスタンス起動 ➔ コード・素材転送 ➔ クラウドGPU生成 ➔ 成果物のローカル回収 ➔ インスタンス自動停止」** まで全自動で完結。
3. **実機検証に基づく実践ノウハウの体系化**:
   - 単にコードを動かすだけでなく、プロンプトのコツ、歌唱抜け・音ズレの防止法、リップシンク先行ディレイ補正、VRAM軽量化といった**実制作で必須となるノウハウ**を各モデルごとにドキュメント化。
4. **制作・ポストプロダクションパイプラインの統合**:
   - 音楽生成（YuE2） ➔ リリック動画化（JIZURA） / リップシンク動画化（Wan2.2, MiniMax H3） ➔ 超解像アップスケール ➔ SNS投稿用フォーマット変換まで一気通貫でサポート。

---

## 🎬 対応モデル概要 & 比較

| モデル | 種別 | 特徴・得意用途 | 生成所要時間 (L4 GPU) | ドキュメント |
| :--- | :--- | :--- | :--- | :--- |
| **YuE2-3B** | 🎵 音楽生成 | • ABC楽譜プロンプトによる既存曲アレンジ・耳コピ<br>• 歌詞改行と休符の一致による高精度歌唱<br>• CUDA Graph / 24GB VRAMフル活用 | 約 1分半 〜 2分 / 曲 (2〜3分尺) | [YuE2 ガイド](file:///D:/Work/YuE2/models/yue2/README.md) |
| **Wan2.2-S2V** | 🗣️ 音声駆動動画 | • 14B Scaled FP8 による高精度リップシンク<br>• 先頭4フレームスキップによるディレイ解消<br>• 77f単位マルチチャンクによる15秒超の長尺生成 | 約 4分 15秒 / 5秒動画 (640x640) | [Wan2.2 ガイド](file:///D:/Work/YuE2/models/wan2_2_s2v/README.md) |
| **MiniMax H3** | 🎥 超高品質動画 | • Ref2VA (Reference to Video+Audio) 準拠<br>• 歯並び・表情破綻ゼロの最高峰リアリズム<br>• DiT INT8 + Qwen3VL NVFP4 量子化 | 約 6分 30秒 / 5秒動画 (640x640) | [MiniMax H3 ガイド](file:///D:/Work/YuE2/models/minimax_h3/README.md) |
| **Qwen-Image 2.1** | 🎨 画像生成 (1K/2K) | • 7B DiT / 統合 Text-to-Image & 画像編集<br>• 2K (2048x2048) ネイティブ生成 & 超解像対応<br>• ホラー・戦闘の無検閲生成 & 連続バッチ生成対応 | 約 1分50秒 (1Kバッチ) / 約 8分17秒 (2K NF4) | [Qwen-Image ガイド](file:///D:/Work/YuE2/models/qwen_image_2_1/README.md) |

---

## 📁 ディレクトリ構成

モデルごとにディレクトリを完全に分離・自律化し、新しいモデルの追加にも柔軟に対応できる疎結合な構成を採用している。

```text
cloud-genai-studio/
├── README.md                      # 本ドキュメント（総合ガイド・モデル比較・クイックスタート）
├── GCP_SETUP_GUIDE.md             # GCP初期環境構築・クォータ申請・課金防止ガイド
├── requirements.txt               # 共通依存ライブラリ
├── .env.example                   # 環境変数設定テンプレート
│
├── models/                        # 【モデル別実装・自動化・ノウハウ】
│   ├── yue2/                      # 🎵 YuE2-3B (音楽生成)
│   │   ├── README.md              # 楽譜同期・平仮名化・サンプリングノウハウ
│   │   ├── generate.py            # 高速音楽生成 CLI
│   │   ├── packages/              # yue2_infer wheel 配布物
│   │   └── gcp/                   # GCP 自動化スクリプト (run_cloud_generation.ps1 等)
│   │
│   ├── wan2_2_s2v/                # 🗣️ Wan2.2-S2V (音声駆動・リップシンク・長尺動画)
│   │   ├── README.md              # リップシンク補正・マルチチャンク仕様
│   │   ├── generate.py            # Wan2.2 生成 CLI
│   │   ├── workflows/             # ComfyUI パイプライン定義 JSON
│   │   └── gcp/                   # GCP 自動化スクリプト (run_cloud.ps1, setup.sh 等)
│   │
│   ├── minimax_h3/                # 🎥 MiniMax H3 (超高品質 Ref2VA 動画)
│   │   ├── README.md              # プロンプト記法・ベンチマーク
│   │   ├── generate.py            # MiniMax H3 生成 CLI
│   │   └── gcp/                   # GCP 自動化スクリプト (run_cloud.ps1, setup.sh 等)
│   │
│   └── qwen_image_2_1/            # 🎨 Qwen-Image 2.1 (画像生成・2K・バッチ)
│       ├── README.md              # 3大アプローチ・連続生成ノウハウ・NSFW検証
│       ├── generate.py            # 単発画像生成 CLI (Approach A/B/C)
│       ├── batch_generate.py      # 汎用連続バッチ生成 CLI (自動レジューム)
│       └── gcp/                   # GCP 自動化スクリプト (run_cloud.ps1, setup.sh 等)
│
├── tools/                         # 【共通制作・ポストプロダクションツール】
│   ├── upscale.py                 # Real-ESRGAN / FFmpeg による超解像・4K化
│   ├── align_lyrics.py            # Whisper による歌声実発声タイミング自動検出 (LRC出力)
│   ├── create_waveform_video.py   # 音声波形ビジュアライザー MP4 自動生成
│   ├── edit_for_twitter.py        # SNS向け 2分フェードアウト・5MB以下軽量化
│   └── jizura/                    # [Git Submodule] リリックビデオ制作スタジオ
│
├── examples/                      # 【検証用サンプル素材】
│   ├── yue2/                      # 歌詞 (`lyrics/`)、ABC楽譜 (`scores/`)
│   ├── images/                    # ポートレート静止画 (`sample_portrait.jpg` 等)
│   ├── audios/                    # 音声素材 (`sample_japanese_speech.mp3` 等)
│   └── prompts/                   # プロンプトテキスト例
│
└── outputs/                       # 【生成成果物 格納ディレクトリ (Git除外)】
    └── .gitkeep
```

---

## 🚀 クイックスタート (ワンコマンド実行)

### 事前準備
1. Google Cloud SDK (`gcloud`) のインストールおよびログイン (`gcloud auth login`)。
2. Compute Engine API で **NVIDIA L4 GPU** または **GPUS_ALL_REGIONS** クォータが 1 以上であること（詳細は [GCP_SETUP_GUIDE.md](file:///D:/Work/YuE2/GCP_SETUP_GUIDE.md) 参照）。
3. 必要に応じて `.env.example` をコピーして `.env` を作成。

---

### 1. 🎵 YuE2 による音楽生成
インスタンスを起動し、指定したスタイル・歌詞・楽譜からフル楽曲（2〜3分）を生成してローカルにダウンロード後、インスタンスを自動停止する。

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;
.\models\yue2\gcp\run_cloud_generation.ps1 `
    -Style "energetic modern J-Rock, powerful female vocal, driving drums, rich strings, 160 bpm" `
    -LyricsFile "examples\yue2\lyrics\lyrics_10deg.txt" `
    -AbcFile "examples\yue2\scores\10deg.abc" `
    -OutputFilename "10deg_rock.flac"
```

---

### 2. 🗣️ Wan2.2-S2V による音声リップシンク動画生成
静止画ポートレートと音声ファイルを指定し、唇の動きが完全に同期した動画を生成する。

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;
.\models\wan2_2_s2v\gcp\run_cloud.ps1 `
    -InputImage "examples/images/sample_portrait.jpg" `
    -InputAudio "examples/audios/sample_japanese_speech.mp3" `
    -Width 640 -Height 640 `
    -OutputFilename "wan2_output.mp4"
```

---

### 3. 🎥 MiniMax H3 による超高品質ポートレート動画生成
画像と音声をバインドし、表情の細部までリアルな高精細動画を生成する。

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;
.\models\minimax_h3\gcp\run_cloud.ps1 `
    -Image "examples/images/sample_portrait.jpg" `
    -Audio "examples/audios/sample_japanese_speech.mp3" `
    -Prompt "<Picture 1> <Audio 1> A professional Japanese woman talking naturally and looking directly at the camera." `
    -Width 640 -Height 640
```

---

### 4. 🎨 Qwen-Image 2.1 による 1K / 2K 画像生成
最新の 7B DiT 基盤モデルを用い、高精細な 1K（1024×1024）および 2K（2048×2048）画像を高速生成する。

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;
.\models\qwen_image_2_1\gcp\run_cloud.ps1 `
    -Approach "b" `
    -Prompt "A hyper-detailed cinematic portrait of a cyberpunk girl in neo-tokyo with neon lights and rain reflections, 8k resolution, masterpiece" `
    -Width 2048 -Height 2048 -Steps 15 `
    -OutputFilename "qwen_cyberpunk_2k.png"
```

---

## 🛠️ 共通ポストプロダクションツール (`tools/`)

生成された音声や動画をさらにブラッシュアップするためのツール群を備えている。

### 1. 超解像アップスケール (`tools/upscale.py`)
生成された動画を高画質化（1080p / 4K）する。
```powershell
python tools/upscale.py --input outputs/wan2_output.mp4 --scale 2 --output outputs/wan2_output_1080p.mp4
```

### 2. Whisper による歌詞アライメント (`tools/align_lyrics.py`)
YuE2で生成した楽曲のボーカル発声位置をミリ秒精度で検出し、JIZURA用LRCファイルを自動生成する。
```powershell
python tools/align_lyrics.py --audio outputs/10deg_rock.flac --lrc outputs/10deg.lrc
```

### 3. JIZURA リリックビデオ制作スタジオ (`tools/jizura/`)
タイポグラフィ動画生成スタジオ JIZURA を Git Submodule として内包している。
```powershell
.\models\yue2\start_jizura.bat
```

### 4. SNS 向け最適化 (`tools/edit_for_twitter.py`)
X (旧Twitter) 向けに、音源の2分フェードアウトおよびファイルサイズの軽量化を行う。
```powershell
python tools/edit_for_twitter.py --input outputs/10deg_rock.flac --duration 120 --fade 5
```

---

## 📚 ドキュメント一覧

- [GCP 環境構築・クォータ申請・Spot運用ガイド](file:///D:/Work/YuE2/GCP_SETUP_GUIDE.md)
- [YuE2 音楽生成 詳細ノウハウ](file:///D:/Work/YuE2/models/yue2/README.md)
- [Wan2.2-S2V 音声駆動動画 詳細ノウハウ](file:///D:/Work/YuE2/models/wan2_2_s2v/README.md)
- [MiniMax H3 超高品質動画 詳細ノウハウ](file:///D:/Work/YuE2/models/minimax_h3/README.md)
- [Qwen-Image 2.1 画像生成＆2K実機検証ガイド](file:///D:/Work/YuE2/models/qwen_image_2_1/README.md)

---

## 📜 ライセンス & クレジット

各モデルおよびツールは、それぞれのオリジナルライセンスに準拠する。

- **YuE2-3B**: [m-a-p/YuE2-3B](https://huggingface.co/m-a-p/YuE2-3B)
- **Wan2.2-S2V**: [Wan-Video](https://github.com/Wan-Video/Wan2.1)
- **MiniMax H3**: [MiniMax](https://huggingface.co/MiniMax-AI)
- **JIZURA**: [852wa/JIZURA](https://github.com/852wa/JIZURA)
