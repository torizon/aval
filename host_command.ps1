param (
    [string]$jsonFile
)

# This file is a sample of a host command to be executed after a device is
# locked and updated, but before any actual commands are executed within the
# device.
# You can however use whatever, doesn't need to be bash, as long as it's
# callable (on the PATH) for Aval, it works.

Write-Output "This is standard output"
Write-Error "This is standard error"

if (-not $jsonFile) {
    $scriptName = $MyInvocation.MyCommand.Name
    Write-Output "Usage: .\$scriptName <json_file>"
    exit 1
}

if (-not (Test-Path $jsonFile)) {
    Write-Output "File not found: $jsonFile"
    exit 1
}

# Read and parse the JSON
$json = Get-Content $jsonFile | ConvertFrom-Json

$deviceUuid = $json.deviceUuid
$localIpV4 = $json.localIpV4
$hostname = $json.hostname
$macAddress = $json.macAddress

Write-Output "Device UUID: $deviceUuid"
Write-Output "Local IPv4: $localIpV4"
Write-Output "Hostname: $hostname"
Write-Output "MAC Address: $macAddress"
