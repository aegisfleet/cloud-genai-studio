# YuE2 Music Generation Studio

音楽生成基盤モデル **YuE2 (YuE2-3B)** を活用し、ローカル環境（RTX 3060 12GB）および **Google Cloud (NVIDIA L4 GPU Spot インスタンス)** で高品質な楽曲を生成・編集・動画化するためのオールインワン作業環境です。

---

## 🌟 主な特徴

1. **Google Cloud (NVIDIA L4 Spot) 最適化**:
   * **高速生成**: CUDA Graph (`backend="torch"`)、CPUオフロード廃止 (`offload_ar=False`)、VAEタイル拡大 (`vae_core_frames=1024`) により、3分の楽曲を約2分〜3分で高速生成。
   * **超低コスト & 最小メモリ構成**: `g2-standard-4` (4 vCPU, 16GB RAM + 8GB Swap, 1x L4 24GB VRAM) の Spot インスタンスを採用。1曲あたりのクラウド費用は約数円。
   * **完全自動化ワンコマンド**: PowerShell スクリプト 1本で「インスタンス作成/起動 -> 環境構築 -> 楽曲生成 -> ローカル outputs/ へ回収 -> インスタンス自動停止」まで完全自動完結。
2. **ABC 楽譜プロンプト対応**:
   * SheetSage2 などで採譜したメロディやコード進行の ABC 楽譜ファイル（`.abc`）を直接読み込み、既存楽曲のアレンジや耳コピ音源を生成可能。
3. **Twitter / SNS 投稿用ポストプロダクションツール**:
   * **尺トリミング & フェードアウト**: 2分00秒のフェードアウト処理と5MB以下への軽量化（MP3/FLAC）。
   * **波形ビジュアライザー MP4 生成**: 楽曲再生に合わせて脈動するクリーンなリアルタイム音声波形とタイトルジャケットを合成した MP4 動画の自動出力。

---

## 📁 ディレクトリ構成

```text
YuE2/
├── README.md                     # 本ドキュメント
├── GCP_SETUP_GUIDE.md            # Google Cloud (L4 Spot) 完全再現手順書
├── requirements.txt              # 必要依存パッケージ
│
├── generate.py                   # L4最適化 CLI 楽曲生成スクリプト (CUDA Graph / ABC対応)
│
├── tools/                        # SNS投稿向けポストプロダクションツール
│   ├── edit_for_twitter.py       # 2分フェードアウト・5MB以下MP3変換ツール
│   └── create_waveform_video.py  # リアルタイム波形付きMP4動画作成ツール
│
├── gcp/                          # Google Cloud 自動化スクリプト
│   ├── run_cloud_generation.ps1  # インスタンス起動〜生成〜取得〜停止の一括自動化
│   ├── run_remote.sh             # リモート汎用生成スクリプト
│   ├── run_10deg.sh              # 10℃ (J-Rock Arrange) 生成スクリプト
│   └── run_nier.sh               # NieR「遺サレタ場所」風生成スクリプト
│
├── examples/                     # プロンプト・歌詞・楽譜のサンプル集
│   ├── lyrics/
│   │   ├── lyrics_10deg.txt      # しゃろう「10℃」アレンジ用歌詞 (UTF-8)
│   │   └── lyrics_nier_ruins.txt # NieR風造語歌詞
│   └── scores/
│       └── 10deg.abc             # SheetSage2採譜・コード付与済みABC楽譜
│
├── packages/                     # 配布用 Wheel パッケージ
│   └── yue2_infer-0.1.5-py3-none-any.whl
│
└── outputs/                      # 生成された音声・動画成果物 (Git除外)
    └── .gitkeep
```

---

## 🚀 クラウド自動生成の実行手順

PowerShell を開き、ワンコマンドで生成を実行します。

```powershell
# 基本実行 (自動起動 -> 生成 -> outputs/ へダウンロード -> 自動停止)
.\gcp\run_cloud_generation.ps1

# 任意のスタイルタグを指定して実行
.\gcp\run_cloud_generation.ps1 -Style "cyberpunk synthwave, aggressive bass, 130 bpm"
```

詳細な手動構築コマンドやクォータ確認方法については、[GCP_SETUP_GUIDE.md](GCP_SETUP_GUIDE.md) を参照してください。

---

## 🎬 Twitter / SNS 投稿向けツールの使い方

### 1. 音声の 2分カット & フェードアウト (5MB以下 MP3化)
```bash
python tools/edit_for_twitter.py --input "outputs/10deg_song.flac" --output "outputs/10deg_song_twitter.mp3"
```
* きっかり 2分00秒（120秒）にトリミングし、末尾5秒間に自然なコサインカーブフェードアウトを適用します。
* Twitter の共有制限（5MB以下）を満たす高品質 MP3 を出力します。

### 2. リアルタイム波形アニメーション付き MP4 動画の生成
```bash
python tools/create_waveform_video.py \
  --audio "outputs/10deg_song_twitter.mp3" \
  --output "outputs/10deg_song_twitter.mp4" \
  --title "10 ℃" \
  --subtitle "しゃろう「10℃」- J-Rock Arrangement -" \
  --credits "Original: しゃろう (Sharou) | Arrangement & AI Vocal: YuE2"
```
* 音声波形（`showwaves`）を合成し、Twitter/X 推奨仕様（720p HD, H.264, AAC）で 5MB 以下の MP4 動画を生成します。

---

## 📜 クレジット & 謝辞

* **YuE2 (YuE2-3B)**: [m-a-p/YuE2-3B](https://huggingface.co/m-a-p/YuE2-3B)
* **SheetSage2**: 楽曲採譜および ABC 記譜変換
* **Original Work (10℃)**: しゃろう (Sharou) 様
