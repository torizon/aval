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

get_architecture() {
    arch="$(uname -m)"
    case "$arch" in
        x86_64|amd64)
            echo "amd64"
            ;;
        aarch64|arm64)
            echo "arm64"
            ;;
        *)
            echo "Unsupported architecture: $arch" >&2
            exit 1
            ;;
    esac
}

ARCH="$(get_architecture)"

echo "==> Installing AWS CLI if not present..."
if ! command -v aws >/dev/null 2>&1; then
    case "$ARCH" in
        amd64)
            aws_cli_arch="x86_64"
            ;;
        arm64)
            aws_cli_arch="aarch64"
            ;;
    esac

    aws_cli_zip="awscliv2.zip"

    curl -sSL "https://awscli.amazonaws.com/awscli-exe-linux-${aws_cli_arch}.zip" -o "${aws_cli_zip}"
    unzip -q "${aws_cli_zip}"
    run_as_root ./aws/install
    rm -rf "${aws_cli_zip}" aws
else
    echo "AWS CLI already installed"
fi

echo "==> Installing Session Manager Plugin if not present..."
if ! command -v session-manager-plugin >/dev/null 2>&1; then
    case "$ARCH" in
        amd64)
            ssm_plugin_arch="ubuntu_64bit"
            ;;
        arm64)
            ssm_plugin_arch="ubuntu_arm64"
            ;;
    esac

    curl -sSL "https://s3.amazonaws.com/session-manager-downloads/plugin/latest/${ssm_plugin_arch}/session-manager-plugin.deb" -o "session-manager-plugin.deb"
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
