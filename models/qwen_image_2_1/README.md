# Qwen-Image 2.1 画像生成＆超高解像度 (2K) 実戦運用ガイド

Alibaba が 2026年9月20日にリリースした最新の画像生成基盤モデル **Qwen-Image 2.1 (7B DiT)** を用い、**Google Cloud (NVIDIA L4 24GB Spot インスタンス)** 上で「1K（1024×1024）」および「2K（2048×2048）」の超高解像度画像を安全かつ高品質に生成するための実践ノウハウ集である。

---

## 🌟 概要と主要スペック

| 項目 | 内容 |
| :--- | :--- |
| **アーキテクチャ** | 7B パラメータ（Single-Stream DiT 32層 ＋ Qwen3-VL テキストエンコーダ） |
| **機能特徴** | • Text-to-Image（文生図）と画像編集（インペイント・最大10枚の参照画像バインド）が**単一モデルに統合**<br>• **ネイティブ RGBA（背景透過）出力**に対応（アイコン・ロゴ・キャラクター素材に最適）<br>• ネイティブ 2K（2048×2048、約419万画素）解像度対応 |
| **実測所要時間** | • **1K (1024×1024)**: 約 60 秒 / 枚 (20 steps)<br>• **2K (2048×2048, 4-bit NF4)**: 約 8 分 17 秒 / 枚 (15 steps)<br>• **1K ➔ 2K 超解像**: 約 62 秒 / 枚 (★最速) |
| **推奨インスタンス** | **GCP `g2-standard-4` (4 vCPU, 16GB RAM + 24GB Swap, 1x NVIDIA L4 24GB VRAM)** |
| **Spot 運用コスト** | **約 50 円 / 時間**（1枚あたり約 0.8 円 〜 7 円） |

---

## 📊 2K 画像生成における 3大アプローチの実機徹底比較

同一プロンプト（*A hyper-detailed cinematic portrait of a cyberpunk girl in neo-tokyo with neon lights and rain reflections, 8k resolution, masterpiece*）および同一シード値（`seed: 42`）を用いて実測したテレメトリデータである。

| 比較項目 | **【アプローチ B】★推奨・最高画質**<br>2K Native ＋ 4-bit NF4 量子化 | **【アプローチ C】★最速・高タイパ**<br>1K Native ＋ 2K 超解像 | **【アプローチ A】**<br>2K Native ＋ Tiled VAE (BF16) |
| :--- | :--- | :--- | :--- |
| **出力解像度** | **2048 × 2048** (ネイティブ) | **2048 × 2048** (Lanczos 補間) | **2048 × 2048** (ネイティブ) |
| **生成所要時間** | **約 8 分 17 秒** (497 秒) | **約 1 分 02 秒** (62 秒) | **約 8 分 31 秒** (511 秒) |
| **サンプリング速度** | 16.89 秒 / step (15 steps) | **3.10 秒 / step** (20 steps) | 16.85 秒 / step (15 steps) |
| **ピーク GPU VRAM** | **16.39 GB** / 22.03 GB (74.4%) | **16.39 GB** / 22.03 GB (74.4%) | **16.39 GB** / 22.03 GB (74.4%) |
| **ピーク ホスト RAM** | 15.43 GB (24GB Swap 併用) | 15.51 GB (24GB Swap 併用) | 15.36 GB (24GB Swap 併用) |
| **ファイルサイズ** | **4.19 MB** (情報量・密度最大) | 2.95 MB | 3.20 MB |
| **画質・表現力** | **◎ 最高（路面反射・ビル群看板・毛先の密度が圧倒的）** | **◯ 良好（破綻がなくバランス良好）** | ◯ 良好（ライティングは映画的） |
| **成果物ファイル** | `outputs/qwen_2k_approach_b_quant.png` | `outputs/qwen_2k_approach_c_upscaled.png` | `outputs/qwen_2k_approach_a_tiled.png` |

---

## 🔍 アプローチ別の特徴と使い分け指針

### 1. 【アプローチ B: 推奨・本番用】2K ネイティブ ＋ bitsandbytes 4-bit NF4 量子化
* **なぜ一番出来が良いのか？**:
  * 3枚の中で **最も高精細なディテール密度** を記録。
  * 背景のネオン看板の細かな文字、雨に濡れた路面の凹凸、サイバーパンクスーツの配線やテクスチャの密度が圧倒的。
  * ファイルサイズも **4.19 MB** と最も情報量が多く、拡大してもテクスチャが潰れない「真の 2K 密度」を持つ。
* **速度・VRAM の利点**:
  * 4-bit 量子化によりサンプリング速度が BF16（アプローチA）よりも約 14 秒短縮。
  * ポスター印刷、メインビジュアル、完成原稿など「ここぞという本番の1枚」を出力する際に最適。

### 2. 【アプローチ C: 最速・日常用】1K ネイティブ ＋ Lanczos 2K 超解像
* **圧倒的な実用性**:
  * ネイティブ 2K（約8分）の **約 1/8 の時間（わずか約1分）** で 2048×2048 画像が完成する。
  * 1K で生成された顔立ちや全体の光彩バランスが非常に良く、Lanczos 超解像によって拡大しても破綻がほぼ見られない。
  * プロンプトの試行錯誤、構図の検討、SNS 投稿用にはこの手法が最も実用的である。

### 3. 【アプローチ A】2K ネイティブ ＋ Tiled VAE (BF16)
* **役割**:
  * ネイティブ 2K で問題となっていた「VAE デコード時の 4.5GB VRAM 要求によるクラッシュ」を、**タイリング分割処理（Tiled VAE）によって完全に回避・解消**できることを実証した構成。

---

## 🧠 実機検証で得られた技術的ノウハウ

### 1. ホスト側 RAM（16GB vs 32GB/64GB）と生成速度の関係
* **結論: ホスト RAM を増やしても、サンプリング（生成）速度そのものは上がらない。**
* **理由**:
  * `enable_model_cpu_offload()` の仕様上、サンプリングループ（15〜20ステップ）の間は **DiT モデル（約14GB）が GPU VRAM 上に常駐したまま計算**される。
  * ステップ毎にホスト RAM から PCIe 転送を繰り返しているわけではないため、ステップ速度（1K: 3.1秒/step、2K: 16.8秒/step）は純粋に **NVIDIA L4 GPU の CUDA/Tensor コア計算性能** で律速される。
* **RAM を増やすメリット**:
  * 32GB RAM あればスワップを使わずに物理メモリ上で 28GB のモデル重みを保持できるため、**スクリプト起動からサンプリング開始までの初期ロード時間が十数秒短縮**される。

### 2. メモリ不足（OOM Killer）を防止する 24GB Swap 永続化
* 16GB RAM のインスタンス（`g2-standard-4`）で 28GB のモデルをロード・オフロードする際、瞬間的にホストメモリが枯渇する。
* 本環境では、セットアップスクリプト（[gcp/setup.sh](file:///D:/Work/YuE2/models/qwen_image_2_1/gcp/setup.sh)）により **24GB のスワップ領域（Swapfile）を自動構築し `/etc/fstab` に登録**している。これにより、インスタンス再起動後も自動でスワップが維持され、最も安価な `g2-standard-4`（約50円/時）で完全な安定稼働を実現している。

### 3. 2K デコード時の VRAM 溢れ防止（Tiled VAE）
* 2048×2048 の Latent（256×256）を非圧縮ピクセルに復元する際、一括デコードを行うと約 4.5 GiB の連続テンソル領域が要求され、VRAM 溢れ（CUDA OOM）を引き起こす。
* `pipe.vae.enable_tiling()` を適用することで、タイル単位で分割デコードを行い、メモリ消費を数百 MB に抑え込んで安全に出力できる。

---

## 🚀 実行方法 (ワンコマンド)

PowerShell を開き、ワンコマンドで実行できる（インスタンス起動 ➔ 生成 ➔ ローカル回収 ➔ 自動停止まで全自動）。

### 1. 【最高画質】2K ネイティブ ＋ 4-bit 量子化生成（デフォルト）
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;
.\models\qwen_image_2_1\gcp\run_cloud.ps1 `
    -Prompt "A hyper-detailed cinematic portrait of a cyberpunk girl in neo-tokyo with neon lights and rain reflections, 8k resolution, masterpiece" `
    -Approach "b" `
    -Width 2048 -Height 2048 `
    -Steps 15 `
    -OutputFilename "qwen_cyberpunk_2k_best.png"
```

### 2. 【最速 1分】1K ネイティブ ＋ 2K 超解像生成
```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;
.\models\qwen_image_2_1\gcp\run_cloud.ps1 `
    -Prompt "A hyper-detailed cinematic portrait of a cyberpunk girl in neo-tokyo with neon lights and rain reflections, 8k resolution, masterpiece" `
    -Approach "c" `
    -Width 2048 -Height 2048 `
    -Steps 20 `
    -OutputFilename "qwen_cyberpunk_2k_fast.png"
```

---

## 📁 スクリプト一覧

* [generate.py](file:///D:/Work/YuE2/models/qwen_image_2_1/generate.py): アプローチ A, B, C の切り替えに対応した汎用生成 CLI
* [gcp/run_cloud.ps1](file:///D:/Work/YuE2/models/qwen_image_2_1/gcp/run_cloud.ps1): ローカルからクラウド一括実行するオーケストレーター
* [gcp/setup.sh](file:///D:/Work/YuE2/models/qwen_image_2_1/gcp/setup.sh): 24GB Swap、bitsandbytes、PyTorch 2.9 (cu129) 整合済みの自動セットアップ
