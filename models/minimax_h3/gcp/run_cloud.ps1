# MiniMax H3 Google Cloud L4 Spot Generation Script
# Usage: .\run_cloud.ps1 [-Image path] [-Prompt "text" | -PromptFile path] [-Length 360] [-KeepRunning]

param (
    [string]$InstanceName = "minimax-h3-l4-spot",
    [string]$Zone = "asia-east1-b",
    [string]$MachineType = "g2-standard-8",
    [string]$BootDiskSize = "150GB",
    [string]$ImageFamily = "pytorch-2-9-cu129-ubuntu-2204-nvidia-580",
    [string]$ImageProject = "deeplearning-platform-release",
    [string]$Image = "examples/images/hoshimi_miyabi.png",
    [string]$Audio = "",
    [string]$Prompt = "",
    [string]$PromptFile = "",
    [int]$Width = 640,
    [int]$Height = 640,
    [int]$Length = 360,
    [switch]$KeepRunning,
    [switch]$SetupOnly
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ModelRoot = (Resolve-Path "$PSScriptRoot\..").Path
$RepoRoot = (Resolve-Path "$ModelRoot\..\..").Path
$EnvFile = "$RepoRoot\.env"

if (Test-Path $EnvFile) {
    Write-Host "Loading configuration from .env..." -ForegroundColor Cyan
    Get-Content $EnvFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $parts = $line.Split("=", 2)
            [System.Environment]::SetEnvironmentVariable($parts[0].Trim(), $parts[1].Trim(), "Process")
        }
    }
}

Write-Host "==========================================================" -ForegroundColor Green
Write-Host " MiniMax H3 Cloud Generation Studio (NVIDIA L4 Spot)      " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Instance   : $InstanceName (Zone: $Zone, Type: $MachineType)"
Write-Host "Resolution : ${Width}x${Height}, Length: $Length frames ($([math]::Round($Length / 24, 1))s)"
Write-Host "Image      : $Image"
if ($Audio) { Write-Host "Audio      : $Audio" } else { Write-Host "Audio      : (None - Native Audio Synthesis)" }
Write-Host "==========================================================" -ForegroundColor Green

# 1. Check or Create Instance
Write-Host "`n=== 1. Checking / Starting Spot Instance ($InstanceName) ===" -ForegroundColor Cyan
$existing = gcloud compute instances list --filter="name=$InstanceName AND zone:$Zone" --format="value(status)" 2>$null

$needsSetup = $false

if (-not $existing) {
    Write-Host "Creating new Spot instance: $InstanceName in $Zone with $MachineType (32GB RAM, L4 GPU)..." -ForegroundColor Yellow
    gcloud compute instances create $InstanceName `
        --zone=$Zone `
        --machine-type=$MachineType `
        --provisioning-model=SPOT `
        --instance-termination-action=STOP `
        --image-family=$ImageFamily `
        --image-project=$ImageProject `
        --boot-disk-size=$BootDiskSize `
        --boot-disk-type=pd-balanced `
        --metadata="install-nvidia-driver=True"
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create instance."
        exit $LASTEXITCODE
    }
    $needsSetup = $true
} else {
    Write-Host "Instance $InstanceName exists with status: $existing" -ForegroundColor Green
    if ($existing -ne "RUNNING") {
        Write-Host "Starting instance $InstanceName..." -ForegroundColor Yellow
        gcloud compute instances start $InstanceName --zone=$Zone
    }
}

# 2. Wait for SSH & GPU Ready
Write-Host "`n=== 2. Waiting for SSH and Driver to be Ready ===" -ForegroundColor Cyan
$ready = $false
for ($i = 0; $i -lt 20; $i++) {
    Write-Host "Testing SSH connection and NVIDIA GPU status (attempt $($i+1))..."
    $test = gcloud compute ssh $InstanceName --zone=$Zone --command="nvidia-smi --query-gpu=name,memory.total --format=csv,noheader" 2>$null
    if ($LASTEXITCODE -eq 0 -and $test -match "L4") {
        Write-Host "NVIDIA L4 GPU is ready: $test" -ForegroundColor Green
        $ready = $true
        break
    }
    Start-Sleep -Seconds 10
}

if (-not $ready) {
    Write-Error "Instance did not become ready in time."
    exit 1
}

$remoteUser = (gcloud compute ssh $InstanceName --zone=$Zone --command="whoami" 2>$null).Trim()
$remoteHome = "/home/$remoteUser/minimax-h3"
Write-Host "Remote user: $remoteUser, Remote directory: $remoteHome" -ForegroundColor Cyan

# 3. Setup ComfyUI and Models if needed
Write-Host "`n=== 3. Checking Environment Setup ===" -ForegroundColor Cyan
gcloud compute ssh $InstanceName --zone=$Zone --command="mkdir -p $remoteHome/outputs"

# Normalize line endings for shell scripts
Get-ChildItem -Path "$PSScriptRoot\*.sh" | ForEach-Object {
    $content = (Get-Content $_.FullName -Raw) -replace "`r`n", "`n"
    [System.IO.File]::WriteAllText($_.FullName, $content, [System.Text.UTF8Encoding]::new($false))
}

$setupCmd = 'F1=/home/' + $remoteUser + '/ComfyUI/models/diffusion_models/minimax_h3_ref2va_pruned_int8_convrot.safetensors; F2=/home/' + $remoteUser + '/ComfyUI/models/vae/minimax_h3_audio_vae_fp32.safetensors; if [ -f "$F1" ] && [ -s "$F1" ] && [ -f "$F2" ] && [ -s "$F2" ]; then echo "READY"; else echo "NEEDS_SETUP"; fi'
$setupCheck = gcloud compute ssh $InstanceName --zone=$Zone --command="$setupCmd" 2>$null

if ($setupCheck -notmatch "READY" -or $needsSetup) {
    Write-Host "Setting up ComfyUI and downloading MiniMax H3 models on VM..." -ForegroundColor Yellow
    $LocalSetupSh = Join-Path $PSScriptRoot "setup.sh"
    gcloud compute scp $LocalSetupSh "${InstanceName}:/home/${remoteUser}/setup.sh" --zone=$Zone
    gcloud compute ssh $InstanceName --zone=$Zone --command="chmod +x /home/${remoteUser}/setup.sh; /home/${remoteUser}/setup.sh"
} else {
    Write-Host "MiniMax H3 environment is already verified and ready." -ForegroundColor Green
    # Ensure ComfyUI is running
    gcloud compute ssh $InstanceName --zone=$Zone --command="curl -s http://127.0.0.1:8188/system_stats >/dev/null || nohup python3 /home/${remoteUser}/ComfyUI/main.py --listen 127.0.0.1 --port 8188 > /home/${remoteUser}/comfyui.log 2>&1 &"
}

if ($SetupOnly) {
    Write-Host "SetupOnly requested. Stopping here." -ForegroundColor Cyan
    exit 0
}

# 4. Sync Files
Write-Host "`n=== 4. Syncing Scripts and Input Assets ===" -ForegroundColor Cyan
$LocalGen = Join-Path $ModelRoot "generate.py"
$LocalRemoteSh = Join-Path $PSScriptRoot "run_remote.sh"
$LocalImage = if ([System.IO.Path]::IsPathRooted($Image)) { $Image } else { Join-Path $RepoRoot $Image }

gcloud compute scp $LocalGen "${InstanceName}:${remoteHome}/generate.py" --zone=$Zone
gcloud compute scp $LocalRemoteSh "${InstanceName}:${remoteHome}/run_remote.sh" --zone=$Zone
gcloud compute scp $LocalImage "${InstanceName}:${remoteHome}/$(Split-Path $LocalImage -Leaf)" --zone=$Zone

$RemoteAud = ""
if ($Audio) {
    $LocalAudio = if ([System.IO.Path]::IsPathRooted($Audio)) { $Audio } else { Join-Path $RepoRoot $Audio }
    if (Test-Path $LocalAudio) {
        gcloud compute scp $LocalAudio "${InstanceName}:${remoteHome}/$(Split-Path $LocalAudio -Leaf)" --zone=$Zone
        $RemoteAud = "${remoteHome}/$(Split-Path $LocalAudio -Leaf)"
    }
}

# Sync prompt file
if ($PromptFile -and (Test-Path $PromptFile)) {
    gcloud compute scp $PromptFile "${InstanceName}:${remoteHome}/prompt.txt" --zone=$Zone
} elseif ($Prompt) {
    $TmpPrompt = [System.IO.Path]::GetTempFileName()
    [System.IO.File]::WriteAllText($TmpPrompt, $Prompt, [System.Text.Encoding]::UTF8)
    gcloud compute scp $TmpPrompt "${InstanceName}:${remoteHome}/prompt.txt" --zone=$Zone
    Remove-Item $TmpPrompt -Force
}

# 5. Execute Generation
Write-Host "`n=== 5. Running MiniMax H3 Generation on VM ===" -ForegroundColor Cyan
$RemoteImg = "${remoteHome}/$(Split-Path $LocalImage -Leaf)"
$RemotePromptFile = "${remoteHome}/prompt.txt"

$Cmd = "chmod +x ${remoteHome}/run_remote.sh; ${remoteHome}/run_remote.sh '$RemoteImg' '$RemoteAud' '' '$RemotePromptFile' $Width $Height $Length"
gcloud compute ssh $InstanceName --zone=$Zone --command=$Cmd

# 6. Download Outputs
Write-Host "`n=== 6. Downloading Generated Video to local outputs/ ===" -ForegroundColor Cyan
$LocalOutDir = Join-Path $RepoRoot "outputs"
New-Item -ItemType Directory -Force -Path $LocalOutDir | Out-Null
gcloud compute scp "${InstanceName}:${remoteHome}/outputs/*" $LocalOutDir --zone=$Zone

# 7. Stop Instance
if (-not $KeepRunning) {
    Write-Host "`n=== 7. Stopping Instance to Save Costs ===" -ForegroundColor Yellow
    gcloud compute instances stop $InstanceName --zone=$Zone
    Write-Host "Instance $InstanceName stopped successfully." -ForegroundColor Green
} else {
    Write-Host "`n=== 7. Instance Kept RUNNING (-KeepRunning specified) ===" -ForegroundColor Cyan
}

Write-Host "`nAll tasks completed successfully!" -ForegroundColor Green
