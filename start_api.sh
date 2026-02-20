#!/bin/bash
cd ~/menu-knowledge/app/backend
source venv/bin/activate
nohup python -m uvicorn main:app --host 0.0.0.0 --port 8001 --workers 2 > ~/menu-api.log 2>&1 &
sleep 3
pgrep -fa "uvicorn.*8001"
