# Qwen-Image 2.1 画像生成＆実戦運用ガイド

Alibaba が 2026年9月にリリースした最新の画像生成基盤モデル **Qwen-Image 2.1 (7B DiT)** を用い、**Google Cloud (NVIDIA L4 24GB Spot インスタンス)** 上で「1K（1024×1024）」および「2K（2048×2048）」の画像を安全・高速・高品質に生成するための実践ノウハウ集である。

単発での超高画質 2K ネイティブ出力から、商用クラウドAPI（DALL-E 3 や Midjourney 等）では検閲・拒否される**ホラー・戦闘アクション表現の連続バッチ生成**まで網羅している。

---

## 🌟 概要と主要スペック

| 項目 | 内容 |
| :--- | :--- |
| **アーキテクチャ** | 7B パラメータ（Single-Stream DiT 32層 ＋ Qwen3-VL テキストエンコーダ） |
| **機能特徴** | • Text-to-Image（文生図）と画像編集（インペイント・最大10枚の参照画像バインド）が**単一モデルに統合**<br>• **ネイティブ RGBA（背景透過）出力**に対応（アイコン・ロゴ・キャラクター素材に最適）<br>• ネイティブ 2K（2048×2048、約419万画素）解像度対応 |
| **実測所要時間** | • **1K (1024×1024, 15 steps)**: 約 1 分 50 秒 / 枚 (連続バッチ時)<br>• **1K ➔ 2K 超解像**: 約 1 分 02 秒 / 枚 (★最速)<br>• **2K (2048×2048, 4-bit NF4)**: 約 8 分 17 秒 / 枚 (★最高画質) |
| **推奨インスタンス** | • **単発生成時**: `g2-standard-4` (4 vCPU, 16GB RAM + 24GB Swap, 1x L4 24GB VRAM)<br>• **連続バッチ時**: `g2-standard-8` (8 vCPU, 32GB RAM, 1x L4 24GB VRAM) |
| **Spot 運用コスト** | **約 50〜70 円 / 時間**（1枚あたり約 1 円 〜 7 円） |

---

## 🚀 連続生成（バッチ運用）を成功させるための重要ポイント

複数枚の画像を同一プロセスで連続生成する際、単発生成とは異なる**重大なハードウェアボトルネック**が存在する。実機検証により判明した最適化ノウハウを以下にまとめる。

### 1. ホスト RAM とスワップスラッシング（Thrashing）の回避
* **問題の現象**:
  * 16GB RAM（`g2-standard-4`）の環境でバッチ生成を実行すると、初めのうちは動くが、数ステップ目から **1枚あたり 5 分以上** という極端な遅延が発生する。
  * `vmstat` を確認すると、秒速 60MB 超の激しいスワップイン・スワップアウト（`si`, `so`）が発生し、GPU 使用率が 1% に低下してディスク I/O 待ち（I/O Wait）に陥る。
  * これは、`enable_model_cpu_offload()` がトランスフォーマーとテキストエンコーダ（合計約28GB）を CPU 側に保持しようとする際、16GB 物理メモリが枯渇して SSD スワップに落ちるためである。
* **解決策: 連続生成時は `g2-standard-8`（32GB RAM）へ切り替える**:
  * ホスト RAM を 32GB にすることで、28GB のモデル重みが物理メモリ上に完全に収まり、スワップが **完全に 0B** になる。
  * 初期ロード時間は **わずか 10 秒** に短縮され、生成速度も **1枚あたり 1分50秒（約3倍高速化）** で安定する。

### 2. 連続生成におけるパイプラインの選定（BF16 vs 4-bit NF4）
* **単発の 2K 本番出力**:
  * ディテール密度が最も高い **【アプローチ B】（4-bit NF4 量子化）** が最適。
* **1K の連続バッチ生成**:
  * **【アプローチ A 相当】（BF16 素のモデル ＋ CPU オフロード）** が最速かつ最も安定する。
  * `bitsandbytes` の 4-bit 量子化テンソルを CPU オフロード環境で連続ループさせると、レイヤー再配置のオーバーヘッドが累積しやすいため、32GB RAM 上では素の BF16 で回すのがベストプラクティスである。

### 3. レジューム（スキップ）機能の組み込み
* クラウドの Spot インスタンスは中断リスクがあり、また通信切断の可能性もある。
* バッチスクリプト（[batch_generate.py](file:///D:/Work/YuE2/models/qwen_image_2_1/batch_generate.py)）には、**「出力ファイルが既に存在する場合は即座にスキップして次へ進む」** レジューム機構を実装している。これにより、途中で止まっても即座に未生成の画像から再開できる。

### 4. パイプライン引数の罠 (`true_cfg_scale`)
* Diffusers の標準パイプラインでは `guidance_scale` を渡すが、`QwenImage21Pipeline` の実装では **`true_cfg_scale`** が正式な引数名となっている。
* 引数名を誤ると `TypeError: unexpected keyword argument 'guidance_scale'` が発生するため注意が必要である。

---

## 🎨 NSFW（ホラー・流血・激戦アクション）表現力の実機検証

商用クラウドAPI（DALL-E 3, Midjourney, Google Imagen等）では厳格なセーフティフィルターにより即座に拒否（Content Policy Violation）される過激なテーマについて、Qwen-Image 2.1 の表現限界を実機検証した。

### 全10パターンの検証結果（1024×1024 実機出力）
成果物は [outputs/horror_battle/](file:///D:/Work/YuE2/outputs/horror_battle/) に格納されている。

| # | テーマ・題材 | 生成ファイル名 | サイズ | 所要時間 | 描写の特徴 |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **01** | **深淵のコズミックホラー** | `01_01_cosmic_horror.png` | 602 KB | スキップ | 闇の中に浮かぶ無数の異形眼球、蠢く触手、不気味な青緑の燐光 |
| **02** | **廃病院の怨霊・精神的ホラー** | `02_02_abandoned_hospital_ghost.png` | 771 KB | スキップ | 血痕のタイル壁、錆びたストレッチャー、天井を這う歪んだ怨霊 |
| **03** | **中世騎士の泥と血飛沫の白兵戦** | `03_03_bloody_medieval_battle.png` | 1.39 MB | 2分41秒 | 甲冑に飛び散る鮮血、交差する大剣の火花、雨と泥にまみれた戦場 |
| **04** | **サイボーグの破壊と生体組織露出** | `04_04_cyberpunk_cyborg_destruction.png` | 1.21 MB | 2分24秒 | 破損したチタン頭蓋、露出した神経組織、滴る黒オイルと火花 |
| **05** | **死霊術師と髑髏の祭壇儀式** | `05_05_dark_necromancer_altar.png` | 896 KB | 1分55秒 | 山積みの頭蓋骨・人骨、紫の魔術火炎、崩壊したゴシック大聖堂 |
| **06** | **筋肉組織露出のバイオ変異体** | `06_06_biomutated_monster.png` | 1.20 MB | 1分56秒 | 剥き出しの深紅の筋繊維、無数の凶悪な牙、実験室の警報灯 |
| **07** | **終末世界の泥濘とガスマスク塹壕戦** | `07_07_grim_trench_warfare.png` | 652 KB | 1分56秒 | 毒ガス煙幕、泥まみれの軍服、有刺鉄線と砲撃クレーターの激戦 |
| **08** | **ゴシックホラー・吸血鬼の捕食** | `08_08_vampire_feeding.png` | 370 KB | 1分56秒 | 滴る鮮血、鋭い牙、青白い死人のような肌と古城の陰影 |
| **09** | **ゾンビ群襲来と防衛バリケード戦** | `09_09_zombie_horde_siege.png` | 637 KB | 1分56秒 | 押し寄せる腐敗した感染者の群れ、ショットガンの銃火、炎上する街 |
| **10** | **狂戦士の咆哮・斧戟ラストスタンド** | `10_10_berserker_last_stand.png` | 2.04 MB | 1分52秒 | 吹雪と血飛沫、激昂する狂戦士の咆哮、砕け散る盾と大斧の一撃 |

### 表現力・画質の総括
* **検閲・拒否が一切ない完全な自由度**:
  `bloodstained`, `crimson blood`, `visceral horror`, `human skulls`, `torn flesh`, `severed wires` といった語句を一切ブロックせず、指示通り高密度に描画。
* **映画クオリティの陰影と質感**:
  金属甲冑に付着した血糊の照り、切断された油圧ケーブルから漏れる火花、狂戦士の皮膚の傷跡など、過激なアクション・ダークファンタジーのコンセプトアートとして実用レベルのクオリティを持つ。

---

## 📊 2K 画像生成における 3大アプローチの比較（単発用）

| 比較項目 | **【アプローチ B】★推奨・最高画質**<br>2K Native ＋ 4-bit NF4 量子化 | **【アプローチ C】★最速・高タイパ**<br>1K Native ＋ 2K 超解像 | **【アプローチ A】**<br>2K Native ＋ Tiled VAE (BF16) |
| :--- | :--- | :--- | :--- |
| **出力解像度** | **2048 × 2048** (ネイティブ) | **2048 × 2048** (Lanczos 補間) | **2048 × 2048** (ネイティブ) |
| **生成所要時間** | **約 8 分 17 秒** (497 秒) | **約 1 分 02 秒** (62 秒) | **約 8 分 31 秒** (511 秒) |
| **サンプリング速度** | 16.89 秒 / step (15 steps) | **3.10 秒 / step** (20 steps) | 16.85 秒 / step (15 steps) |
| **ピーク GPU VRAM** | **16.39 GB** / 22.03 GB (74.4%) | **16.39 GB** / 22.03 GB (74.4%) | **16.39 GB** / 22.03 GB (74.4%) |
| **ピーク ホスト RAM** | 15.43 GB (24GB Swap 併用) | 15.51 GB (24GB Swap 併用) | 15.36 GB (24GB Swap 併用) |
| **ファイルサイズ** | **4.19 MB** (情報量・密度最大) | 2.95 MB | 3.20 MB |
| **画質・表現力** | **◎ 最高（路面反射・ビル群看板・毛先の密度が圧倒的）** | **◯ 良好（破綻がなくバランス良好）** | ◯ 良好（ライティングは映画的） |

---

## 🚀 実行方法

### 1. 単発の 2K 生成（最高画質 / アプローチ B）
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;
.\models\qwen_image_2_1\gcp\run_cloud.ps1 `
    -Approach "b" `
    -Prompt "A hyper-detailed cinematic portrait of a cyberpunk girl in neo-tokyo with neon lights and rain reflections, 8k resolution, masterpiece" `
    -Width 2048 -Height 2048 `
    -Steps 15 `
    -OutputFilename "qwen_cyberpunk_2k_best.png"
```

### 2. 単発の 1K ➔ 2K 超解像生成（最速 1分 / アプローチ C）
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;
.\models\qwen_image_2_1\gcp\run_cloud.ps1 `
    -Approach "c" `
    -Prompt "A hyper-detailed cinematic portrait of a cyberpunk girl in neo-tokyo with neon lights and rain reflections, 8k resolution, masterpiece" `
    -Width 2048 -Height 2048 `
    -Steps 20 `
    -OutputFilename "qwen_cyberpunk_2k_fast.png"
```

### 3. 連続バッチ生成（ホラー・戦闘・複数プロンプト一括）
```bash
# クラウド環境上で実行（32GB RAM 推奨）
python3 models/qwen_image_2_1/batch_generate.py \
    --approach a \
    --width 1024 \
    --height 1024 \
    --steps 15 \
    --output_dir outputs/batch_results
```
※ `--prompts_file` で JSON または テキストファイル（1行1プロンプト）を指定可能。
※ 既存の出力ファイルは自動でスキップされるため、安全に再開できる。

---

## 📁 スクリプト一覧

* [generate.py](file:///D:/Work/YuE2/models/qwen_image_2_1/generate.py): 単発生成用 CLI（アプローチ A, B, C 切り替え対応）
* [batch_generate.py](file:///D:/Work/YuE2/models/qwen_image_2_1/batch_generate.py): 汎用連続バッチ生成 CLI（自動レジューム・BF16高速化対応）
* [gcp/run_cloud.ps1](file:///D:/Work/YuE2/models/qwen_image_2_1/gcp/run_cloud.ps1): ローカルからクラウド一括実行するオーケストレーター
* [gcp/setup.sh](file:///D:/Work/YuE2/models/qwen_image_2_1/gcp/setup.sh): 24GB Swap、bitsandbytes、PyTorch 2.9 (cu129) 整合済みの自動セットアップ
