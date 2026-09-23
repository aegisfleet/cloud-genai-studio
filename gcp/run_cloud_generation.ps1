# YuE2 Google Cloud L4 Spot Generation Script
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

$ProjectRoot = (Resolve-Path "$PSScriptRoot\..").Path

param (
    [string]$InstanceName = "yue2-l4-spot",
    [string]$Zone = "asia-northeast1-b",
    [string]$MachineType = "g2-standard-8",
    [string]$BootDiskSize = "100GB",
    [string]$ImageFamily = "pytorch-2-9-cu129-ubuntu-2204-nvidia-580",
    [string]$ImageProject = "deeplearning-platform-release",
    [string]$Style = "J-Pop, emotional female vocal, dynamic piano, upbeat anime opening",
    [string]$OutputDir = "$ProjectRoot\outputs",
    [switch]$KeepRunning
)

Write-Host "=== 1. Checking / Creating Spot Instance ($InstanceName) ===" -ForegroundColor Cyan
$existing = gcloud compute instances list --filter="name=$InstanceName AND zone:$Zone" --format="value(status)" 2>$null

if (-not $existing) {
    Write-Host "Creating new Spot instance: $InstanceName in $Zone with $MachineType..." -ForegroundColor Yellow
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

# Get remote user name
$remoteUser = (gcloud compute ssh $InstanceName --zone=$Zone --command="whoami").Trim()
$remoteHome = "/home/$remoteUser/yue2"

Write-Host "`n=== 3. Uploading Code, Shell Script, and Wheel to Instance ($remoteHome) ===" -ForegroundColor Cyan
gcloud compute ssh $InstanceName --zone=$Zone --command="mkdir -p $remoteHome/outputs"

# Convert line endings of shell scripts to LF before uploading
$shPath = "$PSScriptRoot\run_remote.sh"
if (Test-Path $shPath) {
    $shContent = (Get-Content $shPath -Raw) -replace "`r`n", "`n"
    [System.IO.File]::WriteAllText($shPath, $shContent, [System.Text.UTF8Encoding]::new($false))
}

$wheelPath = "$ProjectRoot\packages\yue2_infer-0.1.5-py3-none-any.whl"
$reqPath = "$ProjectRoot\requirements.txt"
$genPath = "$ProjectRoot\generate.py"

gcloud compute scp $reqPath $genPath $wheelPath $shPath "${InstanceName}:${remoteHome}/" --zone=$Zone

Write-Host "`n=== 4. Setting Up Dependencies and Generating Music on L4 GPU ===" -ForegroundColor Cyan
# Ensure torchvision conflict is resolved, then run script
gcloud compute ssh $InstanceName --zone=$Zone --command="sudo pip3 uninstall -y torchvision 2>/dev/null; pip3 uninstall -y torchvision 2>/dev/null; cd $remoteHome && pip3 install -q yue2_infer-0.1.5-py3-none-any.whl && pip3 install -q -r requirements.txt && bash run_remote.sh"

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
