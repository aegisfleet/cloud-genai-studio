# MiniMax H3 Cloud Runner (PowerShell)
# Usage: .\run_cloud.ps1 [-KeepRunning] [-Image path] [-Audio path] [-Width 640] [-Height 640]

param (
    [string]$InstanceName = "minimax-h3-l4-spot",
    [string]$Zone = "asia-northeast1-a",
    [string]$Image = "examples/images/sample_portrait.jpg",
    [string]$Audio = "examples/audios/sample_japanese_speech.mp3",
    [string]$Prompt = "<Picture 1> <Audio 1> A professional Japanese woman talking naturally and looking directly at the camera.",
    [int]$Width = 640,
    [int]$Height = 640,
    [int]$Length = 124,
    [switch]$KeepRunning
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ModelRoot = (Resolve-Path "$PSScriptRoot\..").Path
$RepoRoot = (Resolve-Path "$ModelRoot\..\..").Path

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "  MiniMax H3 Cloud Generation Workflow   " -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

# 1. Check & Start Instance
Write-Host "[1/5] Checking instance status ($InstanceName)..." -ForegroundColor Yellow
$Status = (gcloud compute instances describe $InstanceName --zone=$Zone --format="value(status)" 2>$null)

if ($Status -ne "RUNNING") {
    Write-Host "Starting instance $InstanceName..." -ForegroundColor Green
    gcloud compute instances start $InstanceName --zone=$Zone
    Write-Host "Waiting 15 seconds for SSH to become ready..."
    Start-Sleep -Seconds 15
} else {
    Write-Host "Instance is already RUNNING." -ForegroundColor Green
}

# 2. Sync Files
Write-Host "[2/5] Uploading script and assets to VM..." -ForegroundColor Yellow
gcloud compute ssh $InstanceName --zone=$Zone --command="mkdir -p ~/minimax-h3/outputs"

$LocalGen = Join-Path $ModelRoot "generate.py"
$LocalRemoteSh = Join-Path $PSScriptRoot "run_remote.sh"
$LocalImage = if ([System.IO.Path]::IsPathRooted($Image)) { $Image } else { Join-Path $RepoRoot $Image }
$LocalAudio = if ([System.IO.Path]::IsPathRooted($Audio)) { $Audio } else { Join-Path $RepoRoot $Audio }

gcloud compute scp $LocalGen "${InstanceName}:~/minimax-h3/generate.py" --zone=$Zone
gcloud compute scp $LocalRemoteSh "${InstanceName}:~/minimax-h3/run_remote.sh" --zone=$Zone
gcloud compute scp $LocalImage "${InstanceName}:~/minimax-h3/$(Split-Path $LocalImage -Leaf)" --zone=$Zone
gcloud compute scp $LocalAudio "${InstanceName}:~/minimax-h3/$(Split-Path $LocalAudio -Leaf)" --zone=$Zone

# 3. Execute
Write-Host "[3/5] Running MiniMax H3 generation on VM..." -ForegroundColor Yellow
$RemoteImg = "~/minimax-h3/$(Split-Path $LocalImage -Leaf)"
$RemoteAud = "~/minimax-h3/$(Split-Path $LocalAudio -Leaf)"

$Cmd = "chmod +x ~/minimax-h3/run_remote.sh; ~/minimax-h3/run_remote.sh '$RemoteImg' '$RemoteAud' '$Prompt' $Width $Height $Length"
gcloud compute ssh $InstanceName --zone=$Zone --command=$Cmd

# 4. Download Outputs
Write-Host "[4/5] Downloading generated videos to local outputs/ ..." -ForegroundColor Yellow
$LocalOutDir = Join-Path $RepoRoot "outputs"
New-Item -ItemType Directory -Force -Path $LocalOutDir | Out-Null
gcloud compute scp "${InstanceName}:~/minimax-h3/outputs/*" $LocalOutDir --zone=$Zone

# 5. Stop Instance
if (-not $KeepRunning) {
    Write-Host "[5/5] Stopping instance to save costs..." -ForegroundColor Yellow
    gcloud compute instances stop $InstanceName --zone=$Zone
    Write-Host "Instance stopped successfully." -ForegroundColor Green
} else {
    Write-Host "[5/5] Instance kept RUNNING (-KeepRunning specified)." -ForegroundColor Cyan
}

Write-Host "All tasks completed!" -ForegroundColor Green
