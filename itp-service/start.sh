#!/bin/bash
# Start ITP (Identical Twins Protocol) compression service
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if already running
if curl -sf http://localhost:8100/health > /dev/null 2>&1; then
    echo "ITP service already running on port 8100"
    exit 0
fi

echo "Starting ITP service on port 8100..."
nohup python itp_server.py > /tmp/itp-service.log 2>&1 &
echo $! > /tmp/itp-service.pid

# Wait for startup
for i in $(seq 1 10); do
    if curl -sf http://localhost:8100/health > /dev/null 2>&1; then
        echo "ITP service started (PID: $(cat /tmp/itp-service.pid))"
        exit 0
    fi
    sleep 0.5
done

echo "ERROR: ITP service failed to start. Check /tmp/itp-service.log"
exit 1
