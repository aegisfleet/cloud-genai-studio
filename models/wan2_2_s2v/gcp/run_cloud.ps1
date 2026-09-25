# Wan2.2-S2V Google Cloud L4 Spot Audio-Driven Video Generation Script
param (
    [string]$InstanceName = "wan2-s2v-l4-spot",
    [string]$Zone = "asia-northeast1-a",
    [string]$MachineType = "g2-standard-8",
    [string]$BootDiskSize = "150GB",
    [string]$ImageFamily = "pytorch-2-9-cu129-ubuntu-2204-nvidia-580",
    [string]$ImageProject = "deeplearning-platform-release",
    [string]$InputImage = "",
    [string]$InputAudio = "",
    [string]$Prompt = "A professional Japanese woman talking naturally and articulately, synchronized with the audio, highly expressive, subtle head nod, photorealistic 8k",
    [string]$NegativePrompt = "色调艳丽，过曝，静态，细节模糊不清，字幕，风格，作品，画作，画面，静止，整体发灰，最差质量，低质量，JPEG压缩残留，丑陋的，残缺的，多余の手指，画得不好的手部，画得不好的脸部，畸形的，毁容的，形态畸形的肢体，手指融合，静止不动的画面，杂乱的背景，三条腿，背景人很多，倒着走",
    [int]$Width = 640,
    [int]$Height = 640,
    [int]$NumChunks = 1,
    [int]$Fps = 16,
    [int]$SkipFirstFrames = 4,
    [string]$Lora = "lightning4",
    [int]$Steps = 0,
    [float]$Cfg = 0.0,
    [int]$Seed = 42,
    [string]$OutputFilename = "wan2_2_s2v_output.mp4",
    [string]$OutputDir = "",
    [switch]$KeepRunning,
    [switch]$SetupOnly
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ModelRoot = (Resolve-Path "$PSScriptRoot\..").Path
$RepoRoot = (Resolve-Path "$ModelRoot\..\..").Path
$EnvFile = "$RepoRoot\.env"
if (-not $OutputDir) { $OutputDir = "$RepoRoot\outputs" }
if (-not $InputImage) { $InputImage = "$RepoRoot\examples\images\sample_portrait.jpg" }
if (-not $InputAudio) { $InputAudio = "$RepoRoot\examples\audios\sample_speech.wav" }

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

# Override from environment variables if set in .env
if ($env:GCP_INSTANCE_NAME -and $InstanceName -eq "wan2-s2v-l4-spot") { $InstanceName = $env:GCP_INSTANCE_NAME }
if ($env:GCP_ZONE -and $Zone -eq "asia-northeast1-a") { $Zone = $env:GCP_ZONE }
if ($env:GCP_MACHINE_TYPE -and $MachineType -eq "g2-standard-8") { $MachineType = $env:GCP_MACHINE_TYPE }
if ($env:GCP_DISK_SIZE -and $BootDiskSize -eq "150GB") { $BootDiskSize = $env:GCP_DISK_SIZE }

Write-Host "==========================================================" -ForegroundColor Green
Write-Host " Wan2.2-S2V Cloud Audio-to-Video Orchestrator (NVIDIA L4) " -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
Write-Host "Instance : $InstanceName (Zone: $Zone, Type: $MachineType)"
Write-Host "Disk Size: $BootDiskSize"
Write-Host "Image    : $InputImage"
Write-Host "Audio    : $InputAudio"
Write-Host "Prompt   : $Prompt"
Write-Host "Chunks   : $NumChunks ($($NumChunks * 77) frames, $([math]::Round(($NumChunks * 77) / $Fps, 1))s)"
Write-Host "Mode     : $Lora"
Write-Host "Output   : $OutputDir\$OutputFilename"
Write-Host "==========================================================`n"

# 1. Check or Create Instance
Write-Host "=== 1. Checking / Creating Spot Instance ($InstanceName) ===" -ForegroundColor Cyan
$existing = gcloud compute instances list --filter="name=$InstanceName AND zone:$Zone" --format="value(status)" 2>$null

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
$remoteHome = "/home/$remoteUser/minimax-h3"

# 3. Code & Asset Synchronization
Write-Host "`n=== 3. Uploading Code and Configuration to Instance ($remoteHome) ===" -ForegroundColor Cyan
gcloud compute ssh $InstanceName --zone=$Zone --command="mkdir -p $remoteHome/outputs $remoteHome/examples/images $remoteHome/examples/audios $remoteHome/gcp"

# Normalize line endings of shell scripts
Get-ChildItem -Path "$PSScriptRoot\*.sh" | ForEach-Object {
    $content = (Get-Content $_.FullName -Raw) -replace "`r`n", "`n"
    [System.IO.File]::WriteAllText($_.FullName, $content, [System.Text.UTF8Encoding]::new($false))
}

# Upload files
gcloud compute scp "$RepoRoot\requirements.txt" "${InstanceName}:${remoteHome}/" --zone=$Zone
gcloud compute scp "$ModelRoot\generate.py" "${InstanceName}:${remoteHome}/" --zone=$Zone
gcloud compute scp --recurse "$PSScriptRoot\*.sh" "${InstanceName}:${remoteHome}/gcp/" --zone=$Zone
if (Test-Path "$RepoRoot\examples") {
    gcloud compute scp --recurse "$RepoRoot\examples\*" "${InstanceName}:${remoteHome}/examples/" --zone=$Zone
}

# Make scripts executable
gcloud compute ssh $InstanceName --zone=$Zone --command="chmod +x $remoteHome/gcp/*.sh"

# 4. First-time setup check
Write-Host "`n=== 4. Checking Dependencies on VM ===" -ForegroundColor Cyan
$modelCheck = (gcloud compute ssh $InstanceName --zone=$Zone --command="test -f /home/$remoteUser/ComfyUI/models/diffusion_models/wan2.2_s2v_14B_fp8_scaled.safetensors && echo 'OK'" 2>$null) | Out-String
if ($modelCheck.Trim() -ne "OK" -or $SetupOnly) {
    Write-Host "Running Wan2.2-S2V environment and model setup on VM (setup.sh)..." -ForegroundColor Yellow
    gcloud compute ssh $InstanceName --zone=$Zone --command="bash $remoteHome/gcp/setup.sh"
    if ($SetupOnly) {
        Write-Host "Setup-only flag specified. Environment ready." -ForegroundColor Green
        if (-not $KeepRunning) {
            gcloud compute instances stop $InstanceName --zone=$Zone
        }
        exit 0
    }
} else {
    Write-Host "Wan2.2-S2V ComfyUI environment and models already present." -ForegroundColor Green
}

if (-not (Test-Path $InputImage)) {
    Write-Error "Input image not found: $InputImage"
    exit 1
}
if (-not (Test-Path $InputAudio)) {
    Write-Error "Input audio not found: $InputAudio"
    exit 1
}

# Upload local image
$imgLeaf = Split-Path $InputImage -Leaf
Write-Host "Uploading reference image ($imgLeaf)..." -ForegroundColor Cyan
gcloud compute scp $InputImage "${InstanceName}:${remoteHome}/examples/images/$imgLeaf" --zone=$Zone
$remoteImage = "$remoteHome/examples/images/$imgLeaf"

# Upload local audio
$audioLeaf = Split-Path $InputAudio -Leaf
Write-Host "Uploading audio track ($audioLeaf)..." -ForegroundColor Cyan
gcloud compute scp $InputAudio "${InstanceName}:${remoteHome}/examples/audios/$audioLeaf" --zone=$Zone
$remoteAudio = "$remoteHome/examples/audios/$audioLeaf"

# 5. Execute Generation
Write-Host "`n=== 5. Executing Generation on Cloud Instance ===" -ForegroundColor Cyan
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$remoteOutput = "$remoteHome/outputs/$OutputFilename"
$stepArg = if ($Steps -gt 0) { "--steps $Steps" } else { "" }
$cfgArg = if ($Cfg -gt 0.0) { "--cfg $Cfg" } else { "" }
$extraParams = "--width $Width --height $Height --num_chunks $NumChunks --fps $Fps --skip_first_frames $SkipFirstFrames --lora $Lora $stepArg $cfgArg --seed $Seed"

$cmd = "bash $remoteHome/gcp/run_remote_s2v.sh '$remoteImage' '$remoteAudio' '$remoteOutput' '$Prompt' $extraParams"
Write-Host "Running remote command: $cmd" -ForegroundColor Gray
gcloud compute ssh $InstanceName --zone=$Zone --command="$cmd"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Remote generation failed with exit code $LASTEXITCODE." -ForegroundColor Red
} else {
    Write-Host "`n=== 6. Downloading Generated Video to Local outputs/ ===" -ForegroundColor Cyan
    gcloud compute scp "${InstanceName}:${remoteOutput}" "$OutputDir\$OutputFilename" --zone=$Zone
    if (Test-Path "$OutputDir\$OutputFilename") {
        Write-Host "SUCCESS! Video saved to: $OutputDir\$OutputFilename" -ForegroundColor Green
    }
}

# 7. Stop Instance unless requested to keep running
if ($KeepRunning) {
    Write-Host "`n[Notice] --KeepRunning specified. Instance $InstanceName remains RUNNING." -ForegroundColor Yellow
} else {
    Write-Host "`n=== 7. Stopping Cloud Instance to Save Cost ===" -ForegroundColor Cyan
    gcloud compute instances stop $InstanceName --zone=$Zone
    Write-Host "Instance stopped. Spot billing halted (only disk storage preserved)." -ForegroundColor Green
}
