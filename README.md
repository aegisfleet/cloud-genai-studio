# YuE2 Music Generation Studio

音楽生成基盤モデル **YuE2 (YuE2-3B)** を活用し、ローカル環境（RTX 3060 12GB）および **Google Cloud (NVIDIA L4 GPU Spot インスタンス)** で高品質な楽曲を生成・編集・動画化するためのオールインワン作業環境です。

---

## 🌟 主な特徴

1. **Google Cloud (NVIDIA L4 Spot) 最適化**:
   * **超高速生成**: CUDA Graph (`backend="torch"`)、CPUオフロード廃止 (`offload_ar=False`)、VAEタイル拡大 (`vae_core_frames=1024`) により、2分〜3分の楽曲を約1分半〜2分で高速生成。
   * **超低コスト & 最小構成**: `g2-standard-4` (4 vCPU, 16GB RAM + 8GB Swap, 1x L4 24GB VRAM) の Spot インスタンスを採用。1曲あたりのクラウド費用は約数円。
   * **完全自動化ワンコマンド**: PowerShell スクリプト 1本で「インスタンス起動 -> 環境構築 -> 楽曲生成（単曲 or 複数テイク一括） -> ローカル `outputs/` へ回収 -> インスタンス自動停止」まで完全自動完結。
2. **ABC 楽譜プロンプト対応**:
   * SheetSage2 などで採譜したメロディやコード進行の ABC 楽譜ファイル（`.abc`）を直接読み込み、既存楽曲のアレンジや耳コピ音源を高精度に生成可能。
3. **リリックビデオ作成パイプライン (JIZURA 連携)**:
   * **Git Submodule 統合**: タイポグラフィ動画生成スタジオ [JIZURA](https://github.com/852wa/JIZURA/) をサブモジュールとして内包し、常に最新バージョンに安全追従。
   * **Whisper 自動アライメント**: 歌声の実発声タイミングをミリ秒単位で検出し、演出タグ付き LRC を自動生成。
4. **SNS 投稿用ポストプロダクションツール**:
   * **尺トリミング & フェードアウト**: 2分00秒のフェードアウト処理と5MB以下への軽量化（MP3/FLAC）。
   * **波形ビジュアライザー MP4 生成**: リアルタイム音声波形とタイトルジャケットを合成した MP4 動画の自動出力。

---

## 📁 ディレクトリ構成

```text
YuE2/
├── README.md                     # 本ドキュメント
├── GCP_SETUP_GUIDE.md            # Google Cloud (L4 Spot) 完全再現手順書
├── requirements.txt              # 必要依存パッケージ
├── start_jizura.bat              # JIZURA 自動更新＆起動ランチャー
├── start_webui.bat               # ローカル Gradio Web UI 起動ランチャー
│
├── generate.py                   # 楽曲生成コア CLI (L4 / RTX 3060 両対応)
│
├── gcp/                          # Google Cloud 自動化スクリプト
│   ├── run_cloud_generation.ps1  # インスタンス起動〜生成〜取得〜停止の一括自動化オーケストレーター
│   ├── run_remote.sh             # リモート汎用生成スクリプト
│   ├── run_10deg.sh              # しゃろう「10℃」生成レシピ
│   ├── run_weight_of_the_world.sh        # NieR「Weight of the World」単曲生成レシピ
│   └── run_weight_of_the_world_suite.sh  # NieR「静かで壮大」3テイク一括生成レシピ
│
├── tools/                        # 演出・ポストプロダクション支援ツール
│   ├── jizura/                   # [Git Submodule] JIZURA 本体のリポジトリ
│   ├── align_lyrics.py           # Whisperによる実発声タイムスタンプ抽出 & JIZURA用LRC自動生成
│   ├── edit_for_twitter.py       # 2分フェードアウト・5MB以下MP3変換ツール
│   └── create_waveform_video.py  # リアルタイム波形付きMP4動画作成ツール
│
├── examples/                     # プロンプト・歌詞・楽譜のサンプル集
│   ├── lyrics/
│   │   ├── lyrics_10deg.txt              # しゃろう「10℃」歌詞
│   │   ├── 10deg_jizura_lyrics.lrc       # 10℃ JIZURA演出タグ付きLRC
│   │   ├── lyrics_weight_of_the_world.txt # NieR 最適化済み歌詞 (平仮名・ブレス調整版)
│   │   └── weight_of_the_world_jizura.lrc # NieR JIZURA演出タグ付きLRC
│   └── scores/
│       ├── 10deg.abc                     # 10℃ ABC楽譜
│       └── weight_of_the_world_part1.abc # NieR 2分10秒最適化済みABC楽譜
│
├── packages/                     # 配布用 Wheel パッケージ
│   └── yue2_infer-0.1.5-py3-none-any.whl
│
└── outputs/                      # 生成された音声・動画成果物 (Git除外)
    └── .gitkeep
```

---

## 🚀 クラウド自動生成の実行手順

PowerShell を開き、ワンコマンドで実行します（インスタンスの起動から生成、ローカルへのダウンロード、自動停止まで全自動で行われます）。

### 1. 単曲生成（カスタムパラメータ）
```powershell
# 任意のスタイル・歌詞・楽譜を指定して実行
.\gcp\run_cloud_generation.ps1 `
    -Style "celtic ethereal fantasy, sacred and majestic, pure crystal female vocal, delicate irish tin whistle, acoustic harp, acoustic fingerstyle guitar, soaring orchestral strings, timeless folklore, grand emotional anime soundtrack, 74 bpm" `
    -LyricsFile "examples\lyrics\lyrics_weight_of_the_world.txt" `
    -AbcFile "examples\scores\weight_of_the_world_part1.abc" `
    -Temperature 0.85 `
    -CfgScale 1.25 `
    -Seed 777 `
    -OutputFilename "weight_of_the_world_celtic_sacred.flac"
```

### 2. スイート（複数テイク一括生成）
複数のアレンジやパラメータを連続生成し、インスタンス1回の起動でまとめて成果物を回収します。

```powershell
# NieR:Automata「静かで壮大」3テイク一括生成スイートを実行
.\gcp\run_cloud_generation.ps1 -SuiteScript "gcp\run_weight_of_the_world_suite.sh"
```

---

## 🧠 YuE2 楽曲生成＆アライメントのベストプラクティス・実践ノウハウ

既存曲の ABC 楽譜（SheetSage2 採譜など）と歌詞を組み合わせる際、AI が思い通りに歌唱し、タイミングのズレや音節の脱落（歌唱抜け）を防ぐための**必須ノウハウ**です。

### 1. 歌詞の「改行位置」と楽譜の「休符（ブレス）」を一致させる（最重要）

YuE2 のシンボリック・プランニング（CoT）では、**歌詞の改行が音楽的なフレーズ区切り**として強く認識されます。

#### ❌ ズレが発生する典型例（「ああ」が抜ける・タイミングが遅れる原因）
原曲のメロディ構造：
```abc
小節1: "Am7"   c2 c2 B2 c4 g4 g8     z6       B4 |
        そ  う  ぼ く ら はーー (休符ブレス)  い
小節2: "Fmaj7" c2 c2 B2 c4 g4 g4 a2 g4 z4 c2 d2 |
        ま  あ  あ  む か ち で も  ...
```
誤った歌詞表記：
```text
そう ぼくらは いま     ← 「いま」を前の行に入れてしまう
ああ むかちでも さけぶ  ← 「ああ」から行を始めてしまう
```
* **問題**: 小節1の末尾にある `z6`（休符ブレス）の手前に「いま」を無理やり詰め込もうとしてリズムが崩れ、小節2の先頭（本来「ま」の音符）に「ああ」が割り当てられて音符とシラブルが玉突き衝突を起こし、「ああ」がスキップされます。

#### ⭕ 正しい解決策：原曲の息継ぎに合わせた行分割
```text
そう ぼくらは
いま ああ むかちでも さけぶ
あの こわれた せかいの うた
```
* **効果**: `そう ぼくらは` で小節1の休符（ブレス）で綺麗に着地し、休符後の弱起（アウフタクト）から `いま ああ むかちでも さけぶ` と1行で歌い出すことで、**すべての音符と音節が 1対1 で完全に同期**します。

---

### 2. 日本語歌唱の誤読を 100% 防止する「平仮名化＋分かち書き」

日本語の漢字は多音性（音読み・訓読みの多義性）があるため、プロンプト歌詞は**完全平仮名化**を推奨します。

1. **多音・難読漢字の誤読防止**:
   * `抱く` → 原曲は3音節（`い・だ・く`）であるため、「**い だ く**」と表記（漢字のままだと2音節「だく」と解釈されリズムが狂う）。
   * `穢れた` → 「**け が れ た**」
   * `贖い` → 「**あ が な い**」
   * `体` → 「**か ら だ**」（「たい」と読まれるのを防止）
2. **助詞の「は」は音素通りの「わ」へ置換**:
   * 平仮名表記の「えがお は」は、AI が硬い子音「ha（は）」として発音し不自然になることがあります。
   * 歌声として自然に「wa」と発音させたい場合は、「**えがお わ**」と記述します。

---

### 3. プロンプト追従性を高めるサンプリングパラメータ

歌詞の脱落やメロディからの逸脱を防ぐため、以下のパラメータチューニングが極めて有効です。

| パラメータ | 推奨値 | 役割と効果 |
| :--- | :--- | :--- |
| **`--cfg-scale`** | **`1.25 〜 1.35`** | **Classifier-Free Guidance Scale**。<br>楽譜（ABC）および歌詞テキストへの追従性を大幅に高め、歌唱抜けや勝手なメロディ変更を抑制する。 |
| **`--temperature`**| **`0.80 〜 0.88`** | **サンプリング温度**。<br>デフォルト（1.0）よりわずかに下げることで、ピッチ・リズムのブレを抑え、安定した発声を促進する。 |
| **`--top-p`** | **`0.90 〜 0.95`** | 核サンプリング閾値。 |

---

## 🎬 JIZURA 向けリリックビデオ作成パイプライン

### Step 1: 音源の準備（WAV変換）
JIZURA はブラウザの Web Audio API を使用するため、非圧縮 WAV 形式の音源を用意します。

```powershell
python -c "import soundfile as sf; d, sr = sf.read('outputs/weight_of_the_world_celtic_sacred.flac'); sf.write('outputs/weight_of_the_world_celtic_sacred.wav', d, sr)"
```

### Step 2: `tools/align_lyrics.py` によるボーカル検出 & LRC 自動生成
Whisper AI を用いて、実発声タイミングをミリ秒単位で自動検出し、タイムスタンプ付き LRC ファイルを出力します（Windows 環境への ffmpeg 不要）。

```powershell
python tools/align_lyrics.py `
    --audio outputs/weight_of_the_world_celtic_sacred.wav `
    --lrc outputs/celtic_raw.lrc `
    --model base
```

### Step 3: JIZURA 演出タグの付与
JIZURA 独自の演出タグを追加し、タイポグラフィアニメーションを強化します。
* `[mm:ss.xx]` : 表示開始タイミング（ミリ秒精度）。
* `/` : **カット分割**。1行の歌詞を画面遷移で分割。
* `*単語*` : **強調表示**。対象単語が巨大化・ハイライト。
* `!` : **画面アクション**。強い揺れやフラッシュ（キメやサビに最適）。

```lrc
[00:53.18]これが*僕の呪い*
[01:01.56]犯した*罪*の深さが!
[01:07.68]君の*願い*
[01:13.94]穢れた魂/*抱く*
[01:19.67]贖いだけど...

[01:23.60]そう/僕らは今
[01:26.51]ああ/*無価値でも叫ぶ*!
[01:29.46]あの*壊れた世界*の/歌
```

### Step 4: JIZURA スタジオで動画作成
1. `start_jizura.bat` をダブルクリック（自動で最新版へ更新されブラウザが起動）。
2. 作成した WAV ファイル（`outputs/weight_of_the_world_celtic_sacred.wav`）をドロップ。
3. LRC ファイル（`examples/lyrics/weight_of_the_world_jizura.lrc`）の内容を貼り付け。
4. キーボードの `R` キー（または「おまかせで作る」）でお好みの演出を選び、MP4 を書き出し。

### 🔄 JIZURA サブモジュールの更新管理
本リポジトリでは JIZURA を Git Submodule として管理しています。JIZURA 側の最新アップデートを取り込む場合は以下のコマンドを実行します：

```bash
# サブモジュールの最新コミットを取得して更新
git submodule update --remote tools/jizura
git add tools/jizura
git commit -m "JIZURAサブモジュールを最新コミットに更新"
```

---

## 📜 クレジット & 謝辞

* **YuE2 (YuE2-3B)**: [m-a-p/YuE2-3B](https://huggingface.co/m-a-p/YuE2-3B)
* **JIZURA**: [852wa/JIZURA](https://github.com/852wa/JIZURA) (リリックモーションスタジオ)
* **SheetSage2**: 楽曲採譜および ABC 記譜変換
* **Original Works**:
  * 「Weight of the World / 壊レタ世界ノ歌」: 岡部啓一 (MONACA) 様 / NieR:Automata (SQUARE ENIX)
  * 「10℃」: しゃろう (Sharou) 様
