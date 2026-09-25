# Google Cloud (NVIDIA L4 Spot) 環境構築・運用完全ガイド

本ドキュメントは、Google Cloud Platform (GCP) 上で **NVIDIA L4 GPU (24GB VRAM)** の **Spot インスタンス** を立ち上げ、本リポジトリの生成AIモデル（YuE2, Wan2.2-S2V, MiniMax H3）を安全かつ圧倒的な低コストで実行するための共通セットアップ手順書である。

---

## 💡 なぜ GCP Spot インスタンスなのか？

最新の生成AIモデル（14B動画生成、3B音楽生成等）を実行するには **24GB以上のGPU VRAM** が必須である。
通常、これをクラウドでオンデマンド常時起動すると高額なコストが発生する。

| インスタンスタイプ | GPU構成 | 通常オンデマンド料金 | **Spot インスタンス料金** | 割引率 |
| :--- | :--- | :--- | :--- | :---: |
| **`g2-standard-4`** (YuE2向け) | 1x L4 (24GB), 4 vCPU, 16GB RAM | 約 $0.80 / 時 (約120円) | **約 $0.35 / 時 (約50円)** | **約 60% OFF** |
| **`g2-standard-8`** (動画モデル向け) | 1x L4 (24GB), 8 vCPU, 32GB RAM | 約 $1.00 / 時 (約150円) | **約 $0.45 / 時 (約70円)** | **約 55% OFF** |

本リポジトリのオーケストレーター（PowerShellスクリプト）は、**「生成開始時に起動 ➔ 生成完了後に即時自動停止」** を行うため、1曲（約2分生成）で約数円、5秒の高品質動画（約4〜6分生成）で約5〜10円程度しか発生しない。

---

## 📋 前提条件と初期セットアップ

### Step 1: Google Cloud SDK (`gcloud`) のインストール
ローカルPC（Windows）に Google Cloud CLI をインストールする。

* 公式インストーラー: [Google Cloud CLI Install](https://cloud.google.com/sdk/docs/install)
* インストール後、PowerShellで初期設定を行う：
  ```powershell
  gcloud auth login
  gcloud config set project YOUR_PROJECT_ID
  ```

---

### Step 2: GPU クォータ（割り当て）の申請
GCP で GPU インスタンスを起動するには、GPU クォータが割り当てられている必要がある（初期状態では 0 の場合が多い）。

1. [Google Cloud Console 割り当てページ](https://console.cloud.google.com/iam-admin/quotas) にアクセス。
2. 以下のいずれかのクォータを検索し、**上限を 1 以上**（推奨: 1）へ引き上げ申請する：
   * **`Compute Engine API / GPUS_ALL_REGIONS`**（全世界でのGPU総数クォータ。最も手軽）
   * または **`NVIDIA L4 GPUs`**（東京リージョン `asia-northeast1`）
3. 申請理由には「*Evaluating open-weight generative AI models (music and video generation) on Spot instances*」と記載する（通常数時間〜1営業日で承認される）。

---

### Step 3: ディスク容量とスワップ（メモリ不足防止）

* **ディスクサイズ**:
  * YuE2: **100GB**（pd-balanced 推奨）
  * 動画モデル (Wan2.2, MiniMax H3): **150GB**（モデル重みが20〜35GBあるため）
* **Swap メモリ**:
  * メインメモリ16GB（`g2-standard-4`）の場合、モデルロード時に瞬間的なメモリスパイク（OOM Killer）が発生するリスクがある。
  * 本リポジトリの起動スクリプトは、VM内で自動的に **8GB のスワップファイル (`/swapfile`)** を構成して OOM を回避する。

---

## 🔒 課金防止と運用のベストプラクティス

1. **自動停止の徹底**:
   * スクリプトはデフォルトで生成終了後に `gcloud compute instances stop` を発行する。
   * 手動でインスタンスに入って作業した場合は、作業終了後に必ず停止コマンドを実行すること：
     ```powershell
     gcloud compute instances stop <INSTANCE_NAME> --zone=<ZONE>
     ```
2. **予算アラートの設定**:
   * [GCP 課金アラート設定](https://console.cloud.google.com/billing/budgets) で、月額 1,000円〜3,000円の予算アラートを設定しておくことを強く推奨する。
3. **ディスク課金の注意**:
   * インスタンスを「停止（STOPPED）」している間は GPU や CPU の料金は一切発生しないが、ディスク領域（100GB〜150GBで月額約 1,000〜1,500円程度）の保管料のみ日割りで微小に発生する。
   * 長期間利用しない場合は、インスタンスを削除すれば完全無料となる：
     ```powershell
     gcloud compute instances delete <INSTANCE_NAME> --zone=<ZONE>
     ```

---

## 🚀 モデル別実行方法

準備が整ったら、各モデルのディレクトリ配下の PowerShell スクリプトを実行するだけでクラウド生成が可能となる。

* 🎵 **YuE2 (音楽)**: [models/yue2/README.md](file:///D:/Work/YuE2/models/yue2/README.md)
* 🗣️ **Wan2.2-S2V (音声駆動動画)**: [models/wan2_2_s2v/README.md](file:///D:/Work/YuE2/models/wan2_2_s2v/README.md)
* 🎥 **MiniMax H3 (超高品質動画)**: [models/minimax_h3/README.md](file:///D:/Work/YuE2/models/minimax_h3/README.md)
