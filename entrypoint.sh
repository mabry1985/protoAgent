#!/bin/bash
# protoAgent — container entrypoint
# Secrets should be injected by `infisical run` (or similar) wrapping
# this script. See the deployment stack for the exact invocation.

set -e

AGENT_NAME="${AGENT_NAME:-protoagent}"

echo "[entrypoint] Starting ${AGENT_NAME}"

# tmpfs home — create dirs inside it
mkdir -p /home/sandbox/.local

# Persistent volume dirs (mounted by the stack)
mkdir -p /sandbox/audit /sandbox/knowledge

# Copy persona into workspace if one is shipped
if [ -f /opt/protoagent/config/SOUL.md ]; then
    cp /opt/protoagent/config/SOUL.md /sandbox/SOUL.md
fi

exec python /opt/protoagent/server.py
