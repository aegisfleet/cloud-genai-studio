# Google Cloud (NVIDIA L4 Spot) による YuE2 音楽生成 再現手順書

本書は、Google Cloud の Compute Engine 上に **NVIDIA L4 GPU (24GB VRAM)** を備えた **Spot インスタンス** を作成し、音楽生成モデル **YuE2 (YuE2-3B)** のセットアップから楽曲生成、生成成果物のローカル `outputs/` への取得、およびインスタンス管理までを再現するための完全な手順書である。

---

## 1. 構成概要

* **クラウドプロバイダ**: Google Cloud Platform (GCP)
* **リージョン / ゾーン**: 東京 (`asia-northeast1-b`)
* **インスタンス名**: `yue2-l4-spot`
* **マシンタイプ**: `g2-standard-8` (8 vCPU, 32GB RAM, 1x NVIDIA L4 24GB VRAM)
* **プロビジョニング**: `SPOT` (大幅に安価なプリエンプティブル料金体系)
* **OSイメージ**: Deep Learning VM (`deeplearning-platform-release` / `pytorch-2-9-cu129-ubuntu-2204-nvidia-580`)
* **成果物出力先**: ローカルの `outputs/`

---

## 2. 事前準備（クォータとCLI確認）

PowerShell にて実行する。文字化け防止のため、セッション開始時にエンコーディングを設定する。

```powershell
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;
```

### 2.1 GCP プロジェクトの設定
```powershell
# 使用するプロジェクトを設定
gcloud config set project cloud-execution-environment
gcloud config set compute/region asia-northeast1
gcloud config set compute/zone asia-northeast1-b
```

### 2.2 東京リージョンの L4 Spot クォータ確認
```powershell
gcloud compute regions describe asia-northeast1 --format="yaml(quotas)" | Select-String -Pattern "NVIDIA_L4" -Context 1,3
```
* `PREEMPTIBLE_NVIDIA_L4_GPUS` の `limit` が 1 以上、`usage` が 0 であることを確認する。

---

## 3. インスタンスの作成

### 3.1 Spot インスタンスの新規作成コマンド
```powershell
gcloud compute instances create yue2-l4-spot `
    --zone=asia-northeast1-b `
    --machine-type=g2-standard-8 `
    --provisioning-model=SPOT `
    --instance-termination-action=STOP `
    --image-family=pytorch-2-9-cu129-ubuntu-2204-nvidia-580 `
    --image-project=deeplearning-platform-release `
    --boot-disk-size=100GB `
    --boot-disk-type=pd-balanced `
    --metadata="install-nvidia-driver=True"
```

### 3.2 起動確認と GPU 認識チェック
インスタンス起動完了後（約 30 秒〜 1 分後）、SSH 経由で GPU を確認する。
```powershell
gcloud compute ssh yue2-l4-spot --zone=asia-northeast1-b --command="nvidia-smi"
```
* `NVIDIA L4` (24GB VRAM) が表示されれば正常。

---

## 4. 環境構築とファイル転送

### 4.1 リモート側の作業ディレクトリ作成
```powershell
gcloud compute ssh yue2-l4-spot --zone=asia-northeast1-b --command="mkdir -p ~/yue2/outputs"
```

### 4.2 ローカルファイルの転送 (SCP)
ローカルのリポジトリルートから必要なファイルを転送する。
```powershell
# 依存定義、生成コード、Wheelパッケージ、シェルスクリプト、サンプルの転送
gcloud compute scp requirements.txt generate.py packages/yue2_infer-0.1.5-py3-none-any.whl gcp/run_remote.sh gcp/run_10deg.sh gcp/run_nier.sh examples/lyrics/lyrics_10deg.txt examples/scores/10deg.abc yue2-l4-spot:~/yue2/ --zone=asia-northeast1-b
```
*(※ `~/yue2/` を指定することで、ログインユーザーのホームディレクトリ配下に自動配置される)*

### 4.3 依存ライブラリのインストールと競合回避
> [!IMPORTANT]
> Deep Learning VM の初期状態に含まれる `torchvision` は PyTorch 2.9 / 2.10 と ABI 競合（`operator torchvision::nms does not exist`）を起こすため、事前にアンインストールする。YuE2 は音声生成モデルのため torchvision は不要。

```powershell
# torchvision アンインストールと依存パッケージの導入
gcloud compute ssh yue2-l4-spot --zone=asia-northeast1-b --command="sudo pip3 uninstall -y torchvision 2>/dev/null; pip3 uninstall -y torchvision 2>/dev/null; cd ~/yue2 && pip3 install yue2_infer-0.1.5-py3-none-any.whl && pip3 install -r requirements.txt"
```

---

## 5. 楽曲生成の実行

### 5.1 NieR風楽曲（「遺サレタ場所」イメージ）を生成する場合
歌詞ファイル `lyrics_nier_ruins.txt` とスタイルタグを指定して実行する。

```powershell
gcloud compute ssh yue2-l4-spot --zone=asia-northeast1-b --command="bash ~/yue2/run_nier.sh"
```

**【シェルスクリプト `run_nier.sh` の内容】**
```bash
#!/bin/bash
set -e
cd ~/yue2

python3 generate.py \
  --style "ethereal female vocal, acoustic guitar arpeggio, melancholic piano, sweeping strings, desolate ruin, cinematic NieR Automata style, haunting emotional vocalise, ambient neoclassical, 84 bpm" \
  --lyrics-file "lyrics_nier_ruins.txt" \
  --cot "full" \
  --seed 42 \
  --output "outputs/nier_city_ruins.flac"
```

### 5.2 任意のスタイル・歌詞で生成する場合
```powershell
gcloud compute ssh yue2-l4-spot --zone=asia-northeast1-b --command="cd ~/yue2 && python3 generate.py --style 'J-Pop, emotional female vocal, dynamic piano' --output 'outputs/my_song.flac'"
```

---

## 6. 生成成果物の取得（ローカル `outputs/` へのダウンロード）

生成された FLAC 音源および ABC 楽譜ファイルをローカルの `outputs/` フォルダへ転送する。

```powershell
# ローカル outputs フォルダへダウンロード
gcloud compute scp --recurse yue2-l4-spot:~/yue2/outputs/* outputs/ --zone=asia-northeast1-b
```

ダウンロード後の確認:
```powershell
Get-ChildItem outputs
```

---

## 7. インスタンス管理と課金停止（必須）

Spot インスタンスは時間課金のため、作業終了後は速やかに停止または削除を行う。

### 7.1 インスタンスの停止（再開可能・推奨）
モデルファイル（約 10GB）やセットアップ環境を保持したまま、GPU 稼働課金を止める。
```powershell
gcloud compute instances stop yue2-l4-spot --zone=asia-northeast1-b
```

### 7.2 次回作業時の再開
停止したインスタンスは以下のコマンドですぐに起動できる。モデルの再ダウンロードや環境構築は不要。
```powershell
# 起動
gcloud compute instances start yue2-l4-spot --zone=asia-northeast1-b

# 起動後の生成実行
gcloud compute ssh yue2-l4-spot --zone=asia-northeast1-b --command="bash ~/yue2/run_nier.sh"
```

### 7.3 インスタンスの完全削除（不要になった場合）
ブートディスクも含め完全にクリーンアップする場合に実行する。
```powershell
gcloud compute instances delete yue2-l4-spot --zone=asia-northeast1-b --quiet
```

---

## 8. 自動化スクリプトによる一括実行

起動からファイル取得、停止までを自動で行う PowerShell スクリプトを用意している。

```powershell
# デフォルト（起動 -> 生成 -> outputs/ にダウンロード -> インスタンス自動停止）
.\gcp\run_cloud_generation.ps1

# 任意のスタイルを指定して実行
.\gcp\run_cloud_generation.ps1 -Style "cyberpunk synthwave, aggressive bass, 130 bpm"

# 生成後もインスタンスを停止せず維持する場合
.\gcp\run_cloud_generation.ps1 -KeepRunning
```
