#!/usr/bin/env bash

# This file is a sample of a host command to be executed after a device is
# locked and updated, but before any actual commands are executed within the
# device.
# You can however use whatever, doesn't need to be bash, as long as it's
# callable (on the PATH) for Aval, it works.

echo "This is standard output"
echo "This is standard error" >&2

if [ -z "$1" ]; then
  echo "Usage: $0 <json_file>"
  exit 1
fi

json_file="$1"

if [ ! -f "$json_file" ]; then
  echo "File not found: $json_file"
  exit 1
fi

deviceUuid=$(jq -r '.deviceUuid' "$json_file")
localIpV4=$(jq -r '.localIpV4' "$json_file")
hostname=$(jq -r '.hostname' "$json_file")
macAddress=$(jq -r '.macAddress' "$json_file")

echo "Device UUID: $deviceUuid"
echo "Local IPv4: $localIpV4"
echo "Hostname: $hostname"
echo "MAC Address: $macAddress"
