#!/bin/bash
# Restart Menu Knowledge API
# Author: terminal-developer
# Date: 2026-02-19

echo "Stopping existing API process..."
pkill -f "uvicorn main:app.*port 8001"
sleep 3

echo "Starting API on port 8001..."
cd ~/menu-knowledge/app/backend
source venv/bin/activate
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8001 --workers 2 > ~/menu-api.log 2>&1 &

sleep 2
echo "Checking if API is running..."
pgrep -fa "uvicorn.*8001" || echo "ERROR: API did not start"

echo "Done! Check logs: tail -f ~/menu-api.log"
