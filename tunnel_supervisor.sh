#!/bin/bash
# Tunnel Supervisor: Keeps the Serveo tunnel connected with auto-restart
KEY_PATH="$(dirname "$0")/tunnel_key"

while true; do
    echo "[$(date)] Starting tunnel connection..."
    ssh -i "$KEY_PATH" \
        -o StrictHostKeyChecking=no \
        -o ServerAliveInterval=15 \
        -o ServerAliveCountMax=4 \
        -o ExitOnForwardFailure=yes \
        -R 80:localhost:8501 \
        serveo.net >> "$(dirname "$0")/tunnel.log" 2>&1
    
    echo "[$(date)] Tunnel disconnected, reconnecting in 2 seconds..."
    sleep 2
done
