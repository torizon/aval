#!/bin/sh
set -e

echo "==> Looking for active SSM sessions..."

# Search for active SSM processes
SSM_PROCESSES=$(pgrep -f "aws ssm start-session" || true)
PLUGIN_PROCESSES=$(pgrep -f "session-manager-plugin" || true)

if [ -z "$SSM_PROCESSES" ] && [ -z "$PLUGIN_PROCESSES" ]; then
    echo "==> No SSM sessions found."
    exit 0
fi

echo "==> Killing SSM processes..."

if [ -n "$SSM_PROCESSES" ]; then
    echo "-> Killing aws ssm start-session processes:"
    echo "$SSM_PROCESSES"
    pkill -f "aws ssm start-session" || true
fi

if [ -n "$PLUGIN_PROCESSES" ]; then
    echo "-> Killing session-manager-plugin processes:"
    echo "$PLUGIN_PROCESSES"
    pkill -f "session-manager-plugin" || true
fi

# Short delay to ensure all processes are terminated
sleep 1

echo "==> Verifying remaining SSM processes..."

REMAINING_SSM=$(pgrep -f "aws ssm start-session" || true)
REMAINING_PLUGIN=$(pgrep -f "session-manager-plugin" || true)

if [ -n "$REMAINING_SSM" ] || [ -n "$REMAINING_PLUGIN" ]; then
    echo "ERROR: Some SSM processes are still alive:"
    [ -n "$REMAINING_SSM" ] && echo "aws ssm start-session: $REMAINING_SSM"
    [ -n "$REMAINING_PLUGIN" ] && echo "session-manager-plugin: $REMAINING_PLUGIN"
    echo "Cannot proceed because some SSM sessions are still running."
    exit 1
else
    echo "All SSM sessions terminated."
fi

echo "==> Done!"
