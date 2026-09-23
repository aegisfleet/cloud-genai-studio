# YuE2 Music Generation Studio

音楽生成基盤モデル **YuE2 (YuE2-3B)** を活用し、ローカル環境（RTX 3060 12GB）および **Google Cloud (NVIDIA L4 GPU Spot インスタンス)** で高品質な楽曲を生成・編集・動画化するためのオールインワン作業環境です。

---

## 🌟 主な特徴

1. **デュアル実行環境**:
   * **ローカル (RTX 3060 12GB)**: メモリバジェット・VAEタイル最適化により 12GB VRAM で安定動作。Gradio Web UI 完備。
   * **クラウド (Google Cloud L4 Spot)**: 24GB VRAM のモダン GPU を安価な Spot インスタンスで自動プロビジョニング。1曲約2分〜3分で高速生成。
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
├── start_webui.bat               # Windows向け WebUI ワンクリック起動
│
├── generate.py                   # CLI 楽曲生成スクリプト (ABC対応, UTF-8対応)
├── webui.py                      # Gradio Web UI アプリケーション
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

## 🚀 クイックスタート (ローカル環境)

### 1. 環境構築
Python 3.10+ 環境で仮想環境を作成し、依存関係をインストールします。

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install packages/yue2_infer-0.1.5-py3-none-any.whl
```

### 2. Web UI の起動
Windows では `start_webui.bat` をダブルクリック、または以下を実行します。
```bash
python webui.py
```
ブラウザで `http://127.0.0.1:7860` を開きます。

### 3. コマンドラインからの生成 (CLI)
```bash
# 基本的な生成
python generate.py \
  --style "J-Pop, emotional female vocal, dynamic piano, upbeat anime opening" \
  --output "outputs/my_song.flac"

# 歌詞ファイルと ABC 楽譜を指定した生成
python generate.py \
  --style "energetic modern J-Rock, powerful passionate female vocal, 160 bpm" \
  --lyrics-file "examples/lyrics/lyrics_10deg.txt" \
  --abc-file "examples/scores/10deg.abc" \
  --output "outputs/10deg_song.flac"
```

---

## ☁️ Google Cloud (NVIDIA L4 Spot) での高速生成

東京リージョン (`asia-northeast1-b`) の Spot インスタンスを活用し、高速かつ低コストで生成できます。

```powershell
# 自動化スクリプトの実行 (起動 -> 生成 -> outputs/ へダウンロード -> 自動停止)
.\gcp\run_cloud_generation.ps1

# スタイルを指定して実行
.\gcp\run_cloud_generation.ps1 -Style "cyberpunk synthwave, aggressive bass, 130 bpm"
```

詳細な手動構築コマンドやクォータ確認方法については、[GCP_SETUP_GUIDE.md](file:///d:/Work/YuE2/GCP_SETUP_GUIDE.md) を参照してください。

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
