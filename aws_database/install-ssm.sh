#!/bin/sh
set -e

# Helper function to run commands with sudo if available,
# allowing usage both inside containers or on the host system
run_as_root() {
    if command -v sudo >/dev/null 2>&1; then
        sudo "$@"
    else
        "$@"
    fi
}

echo "==> Installing AWS CLI if not present..."
if ! command -v aws >/dev/null 2>&1; then
    curl -sSL "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip -q awscliv2.zip
    run_as_root ./aws/install
    rm -rf awscliv2.zip aws
else
    echo "AWS CLI already installed"
fi

echo "==> Installing Session Manager Plugin if not present..."
if ! command -v session-manager-plugin >/dev/null 2>&1; then
    curl -sSL "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/ubuntu_64bit/session-manager-plugin.deb" -o "session-manager-plugin.deb"
    run_as_root dpkg -i session-manager-plugin.deb
    rm -f session-manager-plugin.deb
else
    echo "Session Manager Plugin already installed"
fi

if command -v aws >/dev/null 2>&1; then
    echo "==> AWS CLI is ready!"
else
    echo "ERROR: AWS CLI installation failed!"
    exit 1
fi

if command -v session-manager-plugin >/dev/null 2>&1; then
    echo "==> Session Manager Plugin is ready!"
else
    echo "ERROR: Session Manager Plugin installation failed!"
    exit 1
fi
