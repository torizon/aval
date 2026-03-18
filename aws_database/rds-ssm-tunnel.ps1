# NOTE:
# This script exists because the Python boto3 SDK currently does NOT support
# starting SSM sessions using the "AWS-StartPortForwardingSessionToRemoteHost"
# document.
#
# There is an open feature request tracking this limitation:
# https://github.com/boto/boto3/issues/3555
#
# Ideally, this should be implemented directly in Python using boto3,
# which would simplify the architecture and remove the need for external scripts.
#
# If boto3 gains support for this feature in the future, it is highly recommended
# to replace this script with a native Python implementation.

$ErrorActionPreference = "Stop"

Write-Host "==> Validating required environment variables..."

# List of required environment variables
$requiredVars = @("AWS_INSTANCE_ID", "AWS_RDS_HOST", "REMOTE_PORT", "LOCAL_PORT")

foreach ($var in $requiredVars) {
    $value = [System.Environment]::GetEnvironmentVariable($var)
    if ([string]::IsNullOrEmpty($value)) {
        Write-Error "ERROR: Environment variable '$var' is not set or is empty."
        exit 1
    }
}

Write-Host "==> All required variables are set."

$AWS_INSTANCE_ID = $env:AWS_INSTANCE_ID
$AWS_RDS_HOST    = $env:AWS_RDS_HOST
$REMOTE_PORT     = $env:REMOTE_PORT
$LOCAL_PORT      = $env:LOCAL_PORT

Write-Host "==> Checking local port availability..."

# Check if the local port is already in use
$portInUse = Get-NetTCPConnection -LocalPort $LOCAL_PORT -ErrorAction SilentlyContinue

if ($portInUse) {
    Write-Error "ERROR: Cannot start tunnel. Local port $LOCAL_PORT is in use."
    Write-Host "Debug info:"
    Get-NetTCPConnection -LocalPort $LOCAL_PORT -ErrorAction SilentlyContinue
    Write-Host "A previous AVAL execution may have left the SSM tunnel open."
    Write-Host "To recover and continue working, run:"
    Write-Host "  .\aws_database\kill-ssm-tunnels.ps1"
    exit 1
}

Write-Host "==> Starting new SSM tunnel..."

# Paths for separate log files
$logOut = "$env:TEMP\ssm-tunnel.out.log"
$logErr = "$env:TEMP\ssm-tunnel.err.log"

# Construct the parameter string as it would be in the terminal
$params = "host=`"$AWS_RDS_HOST`",portNumber=`"$REMOTE_PORT`",localPortNumber=`"$LOCAL_PORT`""

# Path to the AWS CLI executable
$awsExe = (Get-Command aws -ErrorAction Stop).Source

# Start the process in the background
$process = Start-Process -FilePath $awsExe `
    -ArgumentList @(
        "ssm", "start-session",
        "--target", $AWS_INSTANCE_ID,
        "--document-name", "AWS-StartPortForwardingSessionToRemoteHost",
        "--parameters", $params
    ) `
    -RedirectStandardOutput $logOut `
    -RedirectStandardError  $logErr `
    -PassThru

$env:SSM_PID = $process.Id

Write-Host "==> Waiting for tunnel to stabilize..."

# Wait until the local port is actually being used by a process (tunnel ready)
while ($true) {
    try {
        $conn = Get-NetTCPConnection -LocalPort $LOCAL_PORT -ErrorAction SilentlyContinue
        if ($conn) { break }
    } catch {}
    Start-Sleep -Seconds 1
}

Write-Host "==> Tunnel started (PID: $($process.Id))"
Write-Host "==> Done!"
Write-Host "==> Logs:"
Write-Host "  StdOut: $logOut"
Write-Host "  StdErr: $logErr"

Write-Host "==> Printing log contents..."

if (Test-Path $logOut) {
    Write-Host "---- StdOut ----"
    Get-Content $logOut -Raw
} else {
    Write-Host "StdOut log not found: $logOut"
}

if (Test-Path $logErr) {
    Write-Host "---- StdErr ----"
    Get-Content $logErr -Raw
} else {
    Write-Host "StdErr log not found: $logErr"
}
