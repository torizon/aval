$ErrorActionPreference = "Stop"

Write-Host "==> Looking for active SSM sessions..."

# Search for active SSM and session-manager-plugin processes
$ssmProcesses = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "aws ssm start-session" }
$pluginProcesses = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "session-manager-plugin" }

if (-not $ssmProcesses -and -not $pluginProcesses) {
    Write-Host "==> No SSM sessions found."
    exit 0
}

Write-Host "==> Killing SSM processes..."

if ($ssmProcesses) {
    Write-Host "-> Killing aws ssm start-session:"
    $ssmProcesses | ForEach-Object { Write-Host $_.ProcessId }
    $ssmProcesses | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

if ($pluginProcesses) {
    Write-Host "-> Killing session-manager-plugin:"
    $pluginProcesses | ForEach-Object { Write-Host $_.ProcessId }
    $pluginProcesses | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
}

# Small delay to ensure all processes are terminated
Start-Sleep -Seconds 1

Write-Host "==> Verifying remaining SSM processes..."

$remainingSSM = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "aws ssm start-session" }
$remainingPlugin = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "session-manager-plugin" }

if ($remainingSSM -or $remainingPlugin) {
    Write-Host "ERROR: Some SSM processes are still alive:"
    if ($remainingSSM) {
        Write-Host "aws ssm start-session: $($remainingSSM | ForEach-Object { $_.ProcessId } | Out-String)"
    }
    if ($remainingPlugin) {
        Write-Host "session-manager-plugin: $($remainingPlugin | ForEach-Object { $_.ProcessId } | Out-String)"
    }
    Write-Error "Cannot proceed because some SSM sessions are still running."
    exit 1
} else {
    Write-Host "All SSM sessions terminated."
}

Write-Host "==> Done!"
