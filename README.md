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
├── tools/                        # ポストプロダクション & 演出支援ツール
│   ├── align_lyrics.py           # Whisperによる実発声タイムスタンプ抽出 & JIZURA用LRC自動生成
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
│   │   ├── 10deg_jizura_lyrics.lrc # JIZURA演出タグ・ミリ秒同期済みLRC
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

## 🎬 JIZURA 向けリリックビデオ作成パイプライン

楽曲生成から歌詞のミリ秒同期、演出タグの付与、[JIZURA](https://github.com/852wa/JIZURA/) での文字PV書き出し、SNS向け動画編集までの一連の流れです。

```text
[YuE2 生成音源 (.flac)] ──> [WAV変換] ──> [tools/align_lyrics.py] ──> [下書きLRC / JSON]
                                                    │
                                                    ▼
[JIZURA スタジオ] <── [演出タグ編集 (*強調*, !, /)] <──┘
       │
       ▼
 [MP4 書き出し] ──> [SNS向け90秒編集 (ffmpeg / tools)] ──> [X/Twitter投稿用 MP4]
```

### Step 1: 音源の準備（WAV変換）
JIZURA はブラウザの Web Audio API を使用するため、非圧縮 WAV 形式の音源を用意します。

```powershell
# soundfile を用いて FLAC から WAV へ高速変換
python -c "import soundfile as sf; d, sr = sf.read('outputs/10deg_take3_expressive.flac'); sf.write('outputs/10deg_take3_expressive.wav', d, sr)"
```

### Step 2: `tools/align_lyrics.py` によるボーカル検出 & LRC 自動生成
AI（Whisper）を用いて、ボーカルの実発声タイミングをミリ秒単位で自動検出し、タイムスタンプ付き LRC ファイルおよび詳細な JSON を出力します。

* **特徴**: `soundfile` + `scipy` を直接利用して 16kHz リサンプリングを行うため、**Windows 環境への ffmpeg インストール不要** でスタンドアロン動作します。

```powershell
# 基本実行: 音声解析 & 下書きLRCの自動生成
python tools/align_lyrics.py `
    --audio outputs/10deg_take3_expressive.wav `
    --lrc outputs/draft_lyrics.lrc `
    --output outputs/whisper_alignment.json `
    --model base
```

#### 主な引数オプション
| オプション | デフォルト値 | 説明 |
| :--- | :--- | :--- |
| `--audio` | `outputs/10deg_take3_expressive.wav` | 入力音声ファイル（WAV または FLAC） |
| `--lrc` | `None` | 出力する LRC ファイルのパス。指定すると下書きLRCを書き出す |
| `--output` | `outputs/whisper_alignment.json` | 単語・セグメント単位の詳細タイムスタンプ JSON 保存先 |
| `--model` | `base` | 使用する Whisper モデル（`tiny`, `base`, `small`, `medium`） |
| `--language`| `ja` | 認識対象言語コード |

### Step 3: 演出タグの付与とキメ同期の微調整
自動生成された LRC をテキストエディタで開き、JIZURA 固有の演出タグ（強調・画面揺れ・カット分割）を追加します。

#### JIZURA 演出記法リファレンス
* `[mm:ss.xx]` : 表示開始タイミング（ミリ秒精度）。
* `/` : **カット分割**。1行の歌詞を複数の画面切り替えに分割する。
* `*単語*` : **強調表示**。対象の単語が巨大化・ハイライトされる。
* `!` : **画面アクション**。強い揺れやフラッシュが発生する（キメ・サビに最適）。

#### 💡 音ズレを解消するプロの調整テクニック
Whisper は「歌声（母音）」の立ち上がりを検出するため、**イントロのキメ（ドラムの頭）** と **歌い出し** に数秒のブランクがある場合、ドラムインと歌詞表示がズレて感じられます。
このような箇所は、**ドラムイン（例: 24.00秒）** と **歌唱（例: 27.18秒）** にカットを分割します。

```text
# 例: examples/lyrics/10deg_jizura_lyrics.lrc
[00:24.00]! *10℃* / 冷え切った風の中
[00:27.18]街並みが / *白く* 滲んでいく
```
* `[00:24.00]! *10℃*` : 24.00秒のバンド炸裂に合わせて画面がフラッシュし、「10℃」が画面いっぱいに表示される。
* `[00:27.18]` : 実際の歌い出しと完全にシンクロして次のカットへ進む。

### Step 4: JIZURA スタジオで動画を作成・書き出し
1. `start_jizura.bat` をダブルクリック（またはブラウザで `tools/jizura/index.html` を開く）。
2. **曲**: 作成した WAV ファイル（`outputs/10deg_take3_expressive.wav`）をドロップ。
3. **歌詞**: 調整した LRC ファイル（`examples/lyrics/10deg_jizura_lyrics.lrc`）の内容を貼り付け。
4. **演出生成**: キーボードの `R` キー（または「おまかせで作る」）を押す。押すたびに配色・フォント・カメラ演出がランダム生成される。
5. **書き出し**: 気に入ったスタイルが決まったら「MP4 を書き出す」をクリック。

### Step 5: Twitter (X) 向け尺編集（90秒 / 2分フェードアウト）
JIZURA から書き出した MP4（`outputs/jizura.mp4`）を、Twitter(X) のプレビューで最も魅力的に見える 1分30秒（90秒）に切り出し、音声・映像のフェードアウトを適用します。

```powershell
# 1分30秒でカットし、ラスト2秒で黒フェード＆音声フェードアウト
ffmpeg -y -ss 00:00:00 -i outputs/jizura.mp4 -t 90 `
  -vf "fade=t=out:st=88:d=2" `
  -af "afade=t=out:st=88:d=2" `
  -c:v libx264 -pix_fmt yuv420p -c:a aac -b:a 192k `
  outputs/jizura_twitter_90s.mp4
```

---

## 📜 クレジット & 謝辞

* **YuE2 (YuE2-3B)**: [m-a-p/YuE2-3B](https://huggingface.co/m-a-p/YuE2-3B)
* **SheetSage2**: 楽曲採譜および ABC 記譜変換
* **Original Work (10℃)**: しゃろう (Sharou) 様
