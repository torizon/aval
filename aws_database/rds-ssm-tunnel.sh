#!/bin/sh

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

set -e

echo "==> Validating required environment variables..."

# List of required environment variables
REQUIRED_VARS="AWS_INSTANCE_ID AWS_RDS_HOST REMOTE_PORT LOCAL_PORT"

for VAR in $REQUIRED_VARS; do
    VALUE=$(eval echo "\$$VAR")
    if [ -z "$VALUE" ]; then
        echo "ERROR: Environment variable '$VAR' is not set or is empty."
        exit 1
    fi
done

echo "==> All required variables are set."

# Look for an existing process using the same target/host/port combination
SSM_PID=$(pgrep -f "aws ssm start-session.*$AWS_INSTANCE_ID.*$AWS_RDS_HOST.*$REMOTE_PORT" 2>/dev/null | head -n 1 || true)

# Check if a process already exists or if the local port is in use
if [ -n "$SSM_PID" ] || lsof -i :$LOCAL_PORT >/dev/null 2>&1; then
    echo "ERROR: Cannot start tunnel. Local port $LOCAL_PORT is in use."
    echo "Debug info:"
    lsof -i :$LOCAL_PORT
    echo "A previous AVAL execution may have left the SSM tunnel open."
    echo "To recover and continue working, run:"
    echo "  ./aws_database/kill-ssm-tunnels.sh"
    exit 1
fi

# Local port is free → create tunnel
echo "==> Starting new tunnel..."

nohup aws ssm start-session \
  --target "$AWS_INSTANCE_ID" \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters "{\"host\":[\"$AWS_RDS_HOST\"],\"portNumber\":[\"$REMOTE_PORT\"],\"localPortNumber\":[\"$LOCAL_PORT\"]}" \
  > /tmp/ssm-tunnel.log 2>&1 < /dev/null &

SSM_PID=$!
export SSM_PID

echo "==> Waiting for tunnel to stabilize..."

# Loop until the local port is in use by a process (i.e., tunnel is ready)
while true; do
    if command -v lsof >/dev/null 2>&1 && lsof -i :$LOCAL_PORT >/dev/null 2>&1; then
        break
    fi
    sleep 1
done

echo "==> Tunnel started (PID: $SSM_PID)"
echo "==> Done!"
