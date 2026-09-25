# Qwen3-TTS Google Cloud L4 Generation Automation Script
param (
    [string]$InstanceName = "qwen3-tts-vm",
    [string]$Zone = "asia-northeast1-b",
    [string]$MachineType = "g2-standard-4",
    [string]$Text = "初めまして。Qwen3-TTSの日本語音声モデル検証へようこそ。Google CloudのL4インスタンスで快適に動作しています。",
    [string]$Speaker = "ono_anna",
    [string]$Language = "Japanese",
    [string]$Instruct = "優しく自然な日本語で話してください",
    [float]$Temperature = 0.9,
    [float]$PadSilence = 0.5,
    [string]$OutputFilename = "",
    [switch]$NoTailPadding,
    [switch]$KeepRunning,
    [switch]$SetupOnly
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ModelRoot = (Resolve-Path "$PSScriptRoot\..").Path
$RepoRoot = (Resolve-Path "$ModelRoot\..\..").Path
$OutputDir = "$RepoRoot\outputs"
if (!(Test-Path $OutputDir)) { New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null }

Write-Host "==========================================================" -ForegroundColor Green
Write-Host " Qwen3-TTS Cloud Generation Studio (NVIDIA L4)            " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Instance   : $InstanceName (Zone: $Zone, Type: $MachineType)"
Write-Host "Speaker    : $Speaker (Language: $Language)"
Write-Host "Text       : $Text"
Write-Host "Instruct   : $Instruct"
Write-Host "Temp       : $Temperature"
Write-Host "Outputs    : $OutputDir"
Write-Host "==========================================================" -ForegroundColor Green

# 1. Check or Start Instance
Write-Host "`n=== 1. Checking Instance Status ($InstanceName) ===" -ForegroundColor Cyan
$existing = gcloud compute instances list --filter="name=$InstanceName AND zone:$Zone" --format="value(status)" 2>$null

if (-not $existing) {
    Write-Host "Creating instance $InstanceName in $Zone with $MachineType (L4 GPU)..." -ForegroundColor Yellow
    gcloud compute instances create $InstanceName `
        --zone=$Zone `
        --machine-type=$MachineType `
        --maintenance-policy=TERMINATE `
        --image-family=common-cu129-ubuntu-2204-nvidia-580 `
        --image-project=deeplearning-platform-release `
        --boot-disk-size=100GB `
        --boot-disk-type=pd-balanced `
        --metadata="install-nvidia-driver=False"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create instance."
        exit $LASTEXITCODE
    }
} else {
    Write-Host "Instance $InstanceName status: $existing" -ForegroundColor Green
    if ($existing -ne "RUNNING") {
        Write-Host "Starting instance $InstanceName..." -ForegroundColor Yellow
        gcloud compute instances start $InstanceName --zone=$Zone
    }
}

# 2. Wait for SSH readiness
Write-Host "`n=== 2. Checking SSH Connection ===" -ForegroundColor Cyan
$ready = $false
for ($i = 0; $i -lt 10; $i++) {
    $test = gcloud compute ssh $InstanceName --zone=$Zone --command="nvidia-smi --query-gpu=name --format=csv,noheader" 2>$null
    if ($LASTEXITCODE -eq 0 -and $test -match "L4") {
        Write-Host "GPU Ready: $test" -ForegroundColor Green
        $ready = $true
        break
    }
    Start-Sleep -Seconds 6
}

if (-not $ready) {
    Write-Error "Instance did not respond in time."
    exit 1
}

# 3. Setup if requested
if ($SetupOnly) {
    Write-Host "`n=== Setting up environment on VM ===" -ForegroundColor Cyan
    gcloud compute scp "$PSScriptRoot\setup.sh" "${InstanceName}:setup.sh" --zone=$Zone
    gcloud compute ssh $InstanceName --zone=$Zone --command="bash setup.sh"
    Write-Host "Setup finished." -ForegroundColor Green
    if (-not $KeepRunning) {
        gcloud compute instances stop $InstanceName --zone=$Zone
    }
    exit 0
}

# 4. Sync Script and Run Generation
Write-Host "`n=== 3. Running Audio Generation on VM ===" -ForegroundColor Cyan
gcloud compute scp "$ModelRoot\generate.py" "${InstanceName}:generate.py" --zone=$Zone

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$remoteOutName = if ($OutputFilename) { $OutputFilename } else { "${timestamp}_qwen3_tts_${Speaker}.wav" }
$remoteOutPath = "outputs/$remoteOutName"

$noTailFlag = if ($NoTailPadding) { "--no_tail_padding" } else { "" }

# Execute on remote VM
$cmd = "~/miniconda3/envs/qwen3-tts/bin/python generate.py --text `"$Text`" --speaker $Speaker --language $Language --instruct `"$Instruct`" --temperature $Temperature --pad_silence $PadSilence --output `"$remoteOutPath`" $noTailFlag"
gcloud compute ssh $InstanceName --zone=$Zone --command="$cmd"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Audio generation failed on remote VM."
    exit $LASTEXITCODE
}

# 5. Download Output File to local outputs
Write-Host "`n=== 4. Downloading Output to Local outputs/ ===" -ForegroundColor Cyan
$localDest = "$OutputDir\$remoteOutName"
gcloud compute scp "${InstanceName}:$remoteOutPath" "$localDest" --zone=$Zone

if (Test-Path $localDest) {
    Write-Host "Downloaded successfully: $localDest" -ForegroundColor Green
} else {
    Write-Warning "File was not downloaded properly."
}

# 6. Stop instance if not KeepRunning
if (-not $KeepRunning) {
    Write-Host "`n=== 5. Stopping VM to Save Costs ===" -ForegroundColor Yellow
    gcloud compute instances stop $InstanceName --zone=$Zone
    Write-Host "Instance $InstanceName stopped." -ForegroundColor Green
} else {
    Write-Host "`n[Notice] Instance $InstanceName remains RUNNING." -ForegroundColor Cyan
}
