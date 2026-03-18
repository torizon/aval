$ErrorActionPreference = "Stop"

function Download-File($url, $output) {
    Write-Host "Downloading $url → $output"
    Invoke-WebRequest -Uri $url -OutFile $output -MaximumRedirection 5 -UseBasicParsing -ErrorAction Stop | Out-Null
    Write-Host "Downloaded $output"
}

Write-Host "==> Installing AWS CLI if not present..."

if (-not (Get-Command aws -ErrorAction SilentlyContinue)) {
    Write-Host "Installing AWS CLI silently..."

    $url = "https://awscli.amazonaws.com/AWSCLIV2.msi"
    $output = "$env:TEMP\AWSCLIV2.msi"

    Download-File $url $output

    # Install silently and wait for completion
    Start-Process msiexec.exe -Wait -ArgumentList "/i `"$output`" /qr"
    Remove-Item -Force $output

    Write-Host "==> AWS CLI installed. You may need to open a new terminal for it to take effect."
} else {
    Write-Host "AWS CLI already installed"
}

Write-Host "==> Installing Session Manager Plugin if not present..."

if (-not (Get-Command session-manager-plugin -ErrorAction SilentlyContinue)) {
    Write-Host "Installing Session Manager Plugin..."

    $url = "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/windows/SessionManagerPluginSetup.exe"
    $output = "$env:TEMP\SessionManagerPluginSetup.exe"

    Download-File $url $output

    Start-Process -FilePath $output -ArgumentList "/quiet" -Wait
    Remove-Item -Force $output

    Write-Host "==> Session Manager Plugin installed. You may need to open a new terminal for it to take effect."
} else {
    Write-Host "Session Manager Plugin already installed"
}

Write-Host "==> Verifying AWS CLI and Session Manager Plugin..."

$awsReady = Get-Command aws -ErrorAction SilentlyContinue
$pluginReady = Get-Command session-manager-plugin -ErrorAction SilentlyContinue

if ($awsReady -and $pluginReady) {
    Write-Host "==> AWS CLI and Session Manager Plugin are ready!"
} else {
    Write-Host "ERROR: AWS CLI or Session Manager Plugin not found!"
    if (-not $awsReady) { Write-Host "-> AWS CLI missing" }
    if (-not $pluginReady) { Write-Host "-> Session Manager Plugin missing" }
    exit 1
}
