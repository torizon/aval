#!/usr/bin/env bash

function GetDeviceID() {
    cat "${SYSROOT_PATH_PREFIX}"/etc/hostname
}

function RegisterDevice() {

  echo "== Registering device (deviceID: ${DEVICE_ID}) in system, and downloading credentials."
  cd "$(mktemp -d)" || exit 1
  http_code=$(curl -s -w '%{http_code}' --max-time 30 -X POST -H "Authorization: Bearer $PROVISIONING_TOKEN" "$AUTOPROV_URL" -d "{\"device_id\": \"${DEVICE_ID}\", \"device_name\": \"${DEVICE_NAME}\", \"hibernated\": ${HIBERNATED}}" -o device.zip)

  if [[ ! $http_code -eq 200 ]]; then
    # if we failed, device.zip will be a text file with the errors
    echo -e "${RED}"
    echo "Failed to download token :("
    echo "HTTP ERROR ${http_code}"
    cat device.zip
    echo -e "${NC}"
    exit 1
  fi
}

function BackupOldCredentials() {
  echo "== Backing up any existing ota device creds"
  ### move/backup any existing ota device creds
  #BACKUP_DIR=$SOTA_DIR/backup/$(date +"%Y-%m-%d_%Hh%Mm%Ss")
  BACKUP_DIR="$SOTA_DIR"/backup/$(jq -r .deviceUuid "$SOTA_DIR"/import/info.json)-$(jq -r .registeredName "$SOTA_DIR"/import/info.json)
  mkdir -p "$BACKUP_DIR"

  ### If it doesn't already exist
  mkdir -p "$SOTA_DIR"/import

  # WE don't care about failures here since there might not be any data
  mv "$SOTA_DIR"/import/* "$BACKUP_DIR"/ &> /dev/null
  mv "$SOTA_DIR"/sql.db "$BACKUP_DIR"/ &> /dev/null
  for secondary_dir in $(ls -d "${SOTA_DIR}"/storage/*/); do
    mkdir -p "$BACKUP_DIR"/storage/$(basename ${secondary_dir})
    mv ${secondary_dir}/sql.db "$BACKUP_DIR"/storage/$(basename ${secondary_dir})
    mv ${secondary_dir}/sec.private "$BACKUP_DIR"/storage/$(basename ${secondary_dir})
    mv ${secondary_dir}/sec.public "$BACKUP_DIR"/storage/$(basename ${secondary_dir})
  done &> /dev/null
}

function IsRacEnabled() {
  ENABLED=$(systemctl is-enabled remote-access)
  ACTIVE=$(systemctl is-active remote-access)
  [ "$ENABLED" == "enabled" ] && ([ "$ACTIVE" == "active" ] || [ "$ACTIVE" == "activating" ])
}

function ConsiderRemoteAccess() {
  echo "Removing RAC files..."
  rm -rf /home/torizon/run/rac
  if IsRacEnabled; then
    echo "Restarting RAC..."
    systemctl restart remote-access || {
      ERRNO=$?
      echo "Failed to restart remote-access service"
      exit "$ERRNO"
    }
  fi
}

function WriteCredentials() {
  echo "== Extracing device credentials from archive"
  unzip device.zip -d "$SOTA_DIR"/import/ || {
    echo "Failed to extract zip file"
    exit 1
  }

  # Delete the sql.db in case aktualizr re-created it?
  rm "$SOTA_DIR"/sql.db &> /dev/null && sync && sleep 3

  ### WriteOut gateway.url
  if [ -n "$GW_URL" ]; then
    echo "== Overriding gateway.url to be: $GW_URL"
    echo "$GW_URL" > "$SOTA_DIR"/import/gateway.url || {
      echo "Failed to create gateway.url"
      exit 1
    }
  fi

  echo ""
  echo "== Success!"
  echo "Device has been registered with the system and credentials are in place!"
  echo -e "${GREEN}"
  jq . "$SOTA_DIR"/import/info.json
  echo -e "${NC}"

}

function EnableDeviceMetrics() {
  if [ -d "/som_sysroot" ]; then
    # if we're in a container, we can't actually run aktualizr, so instead we just run strings. Ugly, but it works.
    strings "${SYSROOT_PATH_PREFIX}"/usr/bin/aktualizr-torizon | grep -q "enable-data-proxy" || DISABLE_DEVICE_METRICS=1
  else
    aktualizr-torizon --help | grep -q "enable-data-proxy" || DISABLE_DEVICE_METRICS=1
  fi

  ### Create (or delete) fluent-bit enabling file
  if [ -z "$DISABLE_DEVICE_METRICS" ]; then
      touch "${SYSROOT_PATH_PREFIX}"/etc/fluent-bit/enabled
  else
      rm "${SYSROOT_PATH_PREFIX}"/etc/fluent-bit/enabled &> /dev/null
  fi

}

function AddPID() {
  if [[ -z $PID ]]; then
    PID=$(cat /proc/device-tree/toradex,product-id)
    if [[ $? -ne 0 ]]; then
      echo "${RED}WARNING: Couldn't get device PID${NC}"
      return
    fi
  fi

  echo "== Adding device (deviceID: ${DEVICE_ID}) PID (PID: $PID)."

  http_code=$(curl -s -w '%{http_code}' --max-time 30 -X PUT -H "Authorization: Bearer $PROVISIONING_TOKEN" "${APIV2_URL}/devices/notes/${DEVICE_ID}" -d "\"$PID\"")

  if [[ $http_code -ne 200 ]]; then
    echo "${RED}Failed to add PID: HTTP ERROR ${http_code}${NC}"
  fi
}

function StartServices() {
  echo "== Restarting services..."

  echo "Restarting aktualizr..."
  systemctl restart aktualizr

  if [ -z "$DISABLE_DEVICE_METRICS" ]; then
    echo "Restarting fluent-bit..."
    systemctl restart fluent-bit
  else
    echo ""
    echo "Skipping fluent-bit because device metrics are disabled..."
  fi
}

function CheckDependencies() {
  echo "Checking dependencies..."

  missing_dependencies=0
  for i in "jq" "curl" "unzip"; do
    if ! which "$i" 1>/dev/null; then
      echo -e "You don't have ${RED}$i${NC} installed. Make sure to install it before running the provision device script"
      missing_dependencies=1
    fi
  done

  if [ "$missing_dependencies" == 1 ]; then
    exit 1
  fi
}

function usage {
  cat <<EOF
  usage: $0 -u <provisioning url> -g <device gateway url> -t <provisioning token> -d <device_id> -n <device_name> -i <device_pid>

    Optional arguments:
      -u <provisioning url>    URL of provisioning endpoint
      -g <device gateway url>  URL of device gateway
      -d <device_id>           A device ID to use. If not set, will be generated based on /etc/hostname
      -n <device_name>         A device Name to use. If not set, it will be autogenerated on the server side
      -i                       A device PID to use. If not set, the script will use /proc/device-tree/toradex,product-id
      -p                       Opt out of sending device metrics
      -z                       Provision the device in hibernation mode

    Required arguments:
      -t <provisioning token>  Your secret token, provided by the OTA server

    Prerequisites: curl, jq, unzip
EOF
}

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'

NC='\033[0m' # No Color

# check if we're running in the provisioning container with the SOM sysroot mounted at the expected location
if [ -d "/som_sysroot" ]; then
  SYSROOT_PATH_PREFIX=/som_sysroot
fi

# set default values unless environment variables are set
[ -z "$AUTOPROV_URL" ] && AUTOPROV_URL=https://app.torizon.io/api/accounts/devices
[ -z "$DEVICE_ID" ] && DEVICE_ID=$(GetDeviceID)
[ -z "$DEVICE_NAME" ] && DEVICE_NAME=''
[ -z "$HIBERNATED" ] && HIBERNATED="false"

APIV2_URL=https://app.torizon.io/api/v2beta
SOTA_DIR="${SYSROOT_PATH_PREFIX}"/var/sota

while getopts ":hpu:g:t:d:n:z:i" opt; do
  case $opt in
    h)
      usage
      exit 0
      ;;
    p)
      DISABLE_DEVICE_METRICS=1
      ;;
    u)
      AUTOPROV_URL=$OPTARG
      ;;
    g)
      GW_URL=$OPTARG
      ;;
    t)
      PROVISIONING_TOKEN=$OPTARG
      ;;
    d)
      DEVICE_ID=$OPTARG
      ;;
    n)
      DEVICE_NAME=$OPTARG
      ;;
    z)
      HIBERNATED="true"
      ;;
    i)
      PID=$OPTARG
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      exit 1
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      exit 1
      ;;
  esac
done

if [ -z "$PROVISIONING_TOKEN" ]; then
	echo "Error: provisioning token not provided" >&2
  echo ""
  usage
  exit 1
fi

CheckDependencies
RegisterDevice
BackupOldCredentials
WriteCredentials
EnableDeviceMetrics
AddPID
if [ -d "/som_sysroot" ]; then
  echo "Running in a container, not restarting services..."
else
  StartServices
  ConsiderRemoteAccess
fi

echo ""
echo -e "    Aktualizr should automatically connect with the server. For logs run: ${YELLOW}sudo journalctl -f -u aktualizr*${NC}"
echo ""
