# YuE2 Google Cloud L4 Spot Generation Script
param (
    [string]$InstanceName = "yue2-l4-spot",
    [string]$Zone = "asia-northeast1-b",
    [string]$MachineType = "g2-standard-4",
    [string]$BootDiskSize = "100GB",
    [string]$ImageFamily = "pytorch-2-9-cu129-ubuntu-2204-nvidia-580",
    [string]$ImageProject = "deeplearning-platform-release",
    [string]$Style = "energetic modern J-Rock, powerful passionate female vocal, roaring overdrive electric guitar riffs, expressive guitar solo, punchy driving drums, dynamic slap bass, emotional rich strings and bright piano, explosive anime rock style, rich layered arrangement, full band production, exciting climax, 160 bpm",
    [string]$LyricsFile = "",
    [string]$AbcFile = "",
    [string]$Cot = "full",
    [int]$OdeSteps = 32,
    [double]$Temperature = 0.85,
    [double]$CfgScale = 1.3,
    [int]$Seed = 100,
    [string]$OutputFilename = "10deg_song.flac",
    [string]$OutputDir = "",
    [string]$SuiteScript = "",
    [switch]$KeepRunning
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$ModelRoot = (Resolve-Path "$PSScriptRoot\..").Path
$RepoRoot = (Resolve-Path "$ModelRoot\..\..").Path

if (-not $LyricsFile) { $LyricsFile = "$RepoRoot\examples\yue2\lyrics\lyrics_10deg.txt" }
if (-not $AbcFile) { $AbcFile = "$RepoRoot\examples\yue2\scores\10deg.abc" }
if (-not $OutputDir) { $OutputDir = "$RepoRoot\outputs" }

Write-Host "=== 1. Checking / Creating Spot Instance ($InstanceName) ===" -ForegroundColor Cyan
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

# Remote user name & directory
$remoteUser = (gcloud compute ssh $InstanceName --zone=$Zone --command="whoami").Trim()
$remoteHome = "/home/$remoteUser/yue2"

Write-Host "`n=== 3. Uploading Code and Assets to Instance ($remoteHome) ===" -ForegroundColor Cyan
gcloud compute ssh $InstanceName --zone=$Zone --command="mkdir -p $remoteHome/outputs $remoteHome/examples/lyrics $remoteHome/examples/scores $remoteHome/gcp"

# Normalize line endings of shell scripts
Get-ChildItem -Path "$PSScriptRoot\*.sh" | ForEach-Object {
    $content = (Get-Content $_.FullName -Raw) -replace "`r`n", "`n"
    [System.IO.File]::WriteAllText($_.FullName, $content, [System.Text.UTF8Encoding]::new($false))
}

$wheelPath = "$ModelRoot\packages\yue2_infer-0.1.5-py3-none-any.whl"
$reqPath = "$RepoRoot\requirements.txt"
$genPath = "$ModelRoot\generate.py"

gcloud compute scp $reqPath $genPath $wheelPath "${InstanceName}:${remoteHome}/" --zone=$Zone
gcloud compute scp --recurse "$PSScriptRoot\*.sh" "${InstanceName}:${remoteHome}/gcp/" --zone=$Zone
gcloud compute scp --recurse "$RepoRoot\examples\yue2\*" "${InstanceName}:${remoteHome}/examples/" --zone=$Zone

$lyricsLeaf = Split-Path $LyricsFile -Leaf
$abcLeaf = Split-Path $AbcFile -Leaf

# Upload specific lyrics and abc score if provided
if (Test-Path $LyricsFile) {
    gcloud compute scp $LyricsFile "${InstanceName}:${remoteHome}/examples/lyrics/$lyricsLeaf" --zone=$Zone
}
if (Test-Path $AbcFile) {
    gcloud compute scp $AbcFile "${InstanceName}:${remoteHome}/examples/scores/$abcLeaf" --zone=$Zone
}

Write-Host "`n=== 4. Setting Up Swap, Dependencies, and Running Generation ===" -ForegroundColor Cyan

if ($SuiteScript) {
    $suiteLeaf = Split-Path $SuiteScript -Leaf
    Write-Host "Running custom suite script: $suiteLeaf on L4 GPU..." -ForegroundColor Yellow
    # Ensure script is uploaded
    if (Test-Path $SuiteScript) {
        gcloud compute scp $SuiteScript "${InstanceName}:${remoteHome}/gcp/$suiteLeaf" --zone=$Zone
    }
    gcloud compute ssh $InstanceName --zone=$Zone --command="bash $remoteHome/gcp/$suiteLeaf"
} else {
    # Create remote job script locally to completely avoid shell quote stripping
    $localJobScript = "$PSScriptRoot\run_cloud_job.sh"
    $jobScriptContent = @"
#!/bin/bash
set -e
export LANG=C.UTF-8
export LC_ALL=C.UTF-8

if [ ! -f /swapfile ]; then
    echo 'Creating 8GB Swapfile...'
    sudo fallocate -l 8G /swapfile 2>/dev/null || sudo dd if=/dev/zero of=/swapfile bs=1M count=8192
    sudo chmod 600 /swapfile
    sudo mkswap /swapfile
    sudo swapon /swapfile
fi
sudo pip3 uninstall -y torchvision 2>/dev/null || true
pip3 uninstall -y torchvision 2>/dev/null || true

cd $remoteHome
pip3 install -q yue2_infer-0.1.5-py3-none-any.whl
pip3 install -q -r requirements.txt

echo 'Starting L4 optimized generation...'
python3 generate.py \
  --style "$Style" \
  --lyrics-file "$remoteHome/examples/lyrics/$lyricsLeaf" \
  --abc-file "$remoteHome/examples/scores/$abcLeaf" \
  --cot "$Cot" \
  --ode-steps $OdeSteps \
  --temperature $Temperature \
  --cfg-scale $CfgScale \
  --seed $Seed \
  --output "$remoteHome/outputs/$OutputFilename"
"@

    # Normalize LF
    $jobScriptContent = $jobScriptContent.Replace("`r`n", "`n")
    [System.IO.File]::WriteAllText($localJobScript, $jobScriptContent, [System.Text.UTF8Encoding]::new($false))
    gcloud compute scp $localJobScript "${InstanceName}:${remoteHome}/gcp/run_cloud_job.sh" --zone=$Zone

    # Execute remote script
    gcloud compute ssh $InstanceName --zone=$Zone --command="bash $remoteHome/gcp/run_cloud_job.sh"

    # Clean up local temporary job script
    Remove-Item -LiteralPath $localJobScript -Force -ErrorAction SilentlyContinue
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Music generation failed."
    exit $LASTEXITCODE
}

Write-Host "`n=== 5. Fetching Generated Files to Local $OutputDir ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null
gcloud compute scp --recurse "${InstanceName}:${remoteHome}/outputs/*" "$OutputDir/" --zone=$Zone

Write-Host "`nGeneration output files:" -ForegroundColor Green
Get-ChildItem -Path $OutputDir

if (-not $KeepRunning) {
    Write-Host "`n=== 6. Stopping Instance to Prevent Extra Charges ===" -ForegroundColor Cyan
    gcloud compute instances stop $InstanceName --zone=$Zone
    Write-Host "Instance stopped. You can start it again or delete it with:" -ForegroundColor Yellow
    Write-Host "gcloud compute instances delete $InstanceName --zone=$Zone" -ForegroundColor Yellow
} else {
    Write-Host "`nInstance kept running as requested (-KeepRunning)." -ForegroundColor Yellow
}
