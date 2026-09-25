# Qwen-Image-2.1 Google Cloud L4 Spot Generation & Benchmarking Script
param (
    [string]$InstanceName = "qwen-image-l4-spot",
    [string]$Zone = "asia-northeast1-a",
    [string]$MachineType = "g2-standard-4",
    [string]$BootDiskSize = "100GB",
    [string]$ImageFamily = "pytorch-2-9-cu129-ubuntu-2204-nvidia-580",
    [string]$ImageProject = "deeplearning-platform-release",
    [string]$Prompt = "A hyper-detailed cinematic portrait of a cyberpunk girl in neo-tokyo with neon lights and rain reflections, 8k resolution, masterpiece, intricate lighting",
    [string]$NegativePrompt = "worst quality, low quality, blurry, distorted, deformed, bad anatomy, text, watermark",
    [int]$Width = 2048,
    [int]$Height = 2048,
    [int]$Steps = 25,
    [float]$GuidanceScale = 4.0,
    [int]$Seed = 42,
    [string]$OutputFilename = "qwen_image_2k.png",
    [string]$OutputDir = "",
    [switch]$KeepRunning,
    [switch]$SetupOnly
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ModelRoot = (Resolve-Path "$PSScriptRoot\..").Path
$RepoRoot = (Resolve-Path "$ModelRoot\..\..").Path
$EnvFile = "$RepoRoot\.env"
if (-not $OutputDir) { $OutputDir = "$RepoRoot\outputs" }

# Load .env if present
if (Test-Path $EnvFile) {
    Write-Host "Loading configuration from .env..." -ForegroundColor Cyan
    Get-Content $EnvFile | ForEach-Object {
        $line = $_.Trim()
        if ($line -and -not $line.StartsWith("#") -and $line.Contains("=")) {
            $parts = $line.Split("=", 2)
            $k = $parts[0].Trim()
            $v = $parts[1].Trim()
            [System.Environment]::SetEnvironmentVariable($k, $v, "Process")
        }
    }
}

Write-Host "==========================================================" -ForegroundColor Green
Write-Host " Qwen-Image-2.1 Cloud Generation & Benchmark (NVIDIA L4)  " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Instance   : $InstanceName (Zone: $Zone, Type: $MachineType)"
Write-Host "Disk Size  : $BootDiskSize"
Write-Host "Resolution : ${Width}x${Height} ($([math]::Round(($Width * $Height) / (1024 * 1024), 1)) Megapixels)"
Write-Host "Steps      : $Steps (CFG: $GuidanceScale)"
Write-Host "Prompt     : $Prompt"
Write-Host "==========================================================" -ForegroundColor Green

# 1. Check or Create Instance
Write-Host "`n=== 1. Checking / Creating Spot Instance ($InstanceName) ===" -ForegroundColor Cyan
$existing = gcloud compute instances list --filter="name=$InstanceName AND zone:$Zone" --format="value(status)" 2>$null

if (-not $existing) {
    Write-Host "Creating new Spot instance: $InstanceName in $Zone with $MachineType (16GB RAM, L4 GPU)..." -ForegroundColor Yellow
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
} else {
    Write-Host "Instance $InstanceName exists with status: $existing" -ForegroundColor Green
    if ($existing -ne "RUNNING") {
        Write-Host "Starting instance $InstanceName..." -ForegroundColor Yellow
        gcloud compute instances start $InstanceName --zone=$Zone
    }
}

# 2. Wait for SSH & GPU readiness
Write-Host "`n=== 2. Waiting for SSH and Driver to be Ready ===" -ForegroundColor Cyan
$ready = $false
for ($i = 0; $i -lt 15; $i++) {
    Write-Host "Testing SSH connection and NVIDIA GPU status (attempt $($i+1))..."
    $test = gcloud compute ssh $InstanceName --zone=$Zone --command="nvidia-smi --query-gpu=name,memory.total --format=csv,noheader" 2>$null
    if ($LASTEXITCODE -eq 0 -and $test -match "L4") {
        Write-Host "GPU Detected: $test" -ForegroundColor Green
        $ready = $true
        break
    }
    Start-Sleep -Seconds 10
}

if (-not $ready) {
    Write-Error "Instance did not become ready with NVIDIA L4 GPU in time."
    exit 1
}

$remoteUser = (gcloud compute ssh $InstanceName --zone=$Zone --command="whoami").Trim()
$remoteHome = "/home/$remoteUser/qwen-image"

# 3. Code & Asset Synchronization
Write-Host "`n=== 3. Uploading Code and Scripts to Instance ($remoteHome) ===" -ForegroundColor Cyan
gcloud compute ssh $InstanceName --zone=$Zone --command="mkdir -p $remoteHome/outputs $remoteHome/gcp"

# Normalize line endings
Get-ChildItem -Path "$PSScriptRoot\*.sh" | ForEach-Object {
    $content = (Get-Content $_.FullName -Raw) -replace "`r`n", "`n"
    [System.IO.File]::WriteAllText($_.FullName, $content, [System.Text.UTF8Encoding]::new($false))
}

gcloud compute scp "$ModelRoot\generate.py" "${InstanceName}:${remoteHome}/" --zone=$Zone
gcloud compute scp --recurse "$PSScriptRoot\*.sh" "${InstanceName}:${remoteHome}/gcp/" --zone=$Zone
gcloud compute ssh $InstanceName --zone=$Zone --command="chmod +x $remoteHome/gcp/*.sh"

# 4. First-time setup check
Write-Host "`n=== 4. Checking / Setting Up Environment on VM ===" -ForegroundColor Cyan
$needsSetup = gcloud compute ssh $InstanceName --zone=$Zone --command="python3 -c 'import diffusers, torch' 2>/dev/null && echo 'READY' || echo 'NEEDS_SETUP'"
if ($needsSetup -notmatch "READY" -or $SetupOnly) {
    Write-Host "Running setup.sh on VM..." -ForegroundColor Yellow
    gcloud compute ssh $InstanceName --zone=$Zone --command="bash $remoteHome/gcp/setup.sh"
    if ($SetupOnly) {
        Write-Host "Setup completed (-SetupOnly specified)." -ForegroundColor Green
        exit 0
    }
} else {
    Write-Host "Environment is already configured and verified." -ForegroundColor Green
}

# 5. Execute Generation & Benchmark
Write-Host "`n=== 5. Running Qwen-Image-2.1 Benchmark Generation on L4 GPU ===" -ForegroundColor Cyan
$runCmd = @"
export PATH="/home/$remoteUser/.local/bin:`$PATH"
cd $remoteHome
python3 generate.py \
  --prompt "$Prompt" \
  --negative-prompt "$NegativePrompt" \
  --width $Width \
  --height $Height \
  --steps $Steps \
  --guidance-scale $GuidanceScale \
  --seed $Seed \
  --output "$remoteHome/outputs/$OutputFilename" \
  --benchmark
"@

$localJobScript = "$PSScriptRoot\run_cloud_job.sh"
$runCmdLF = $runCmd.Replace("`r`n", "`n")
[System.IO.File]::WriteAllText($localJobScript, $runCmdLF, [System.Text.UTF8Encoding]::new($false))
gcloud compute scp $localJobScript "${InstanceName}:${remoteHome}/gcp/run_cloud_job.sh" --zone=$Zone
Remove-Item -LiteralPath $localJobScript -Force -ErrorAction SilentlyContinue

gcloud compute ssh $InstanceName --zone=$Zone --command="bash $remoteHome/gcp/run_cloud_job.sh"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Generation job failed."
    exit $LASTEXITCODE
}

# 6. Fetch Generated Image
Write-Host "`n=== 6. Fetching Generated Output to Local $OutputDir ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
gcloud compute scp "${InstanceName}:${remoteHome}/outputs/$OutputFilename" "$OutputDir/" --zone=$Zone

Write-Host "Output successfully saved to: $OutputDir\$OutputFilename" -ForegroundColor Green

# 7. Stop Instance
if (-not $KeepRunning) {
    Write-Host "`n=== 7. Stopping Instance to Prevent Extra Charges ===" -ForegroundColor Cyan
    gcloud compute instances stop $InstanceName --zone=$Zone
    Write-Host "Instance stopped successfully." -ForegroundColor Green
} else {
    Write-Host "`nInstance kept running as requested (-KeepRunning)." -ForegroundColor Yellow
}
