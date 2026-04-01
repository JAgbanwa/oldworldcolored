#!/usr/bin/env bash
# backend/start.sh  – Download models (if needed) then start the server
set -e
echo "=== OldWorldColored – Backend Setup ==="
python download_models.py
exec uvicorn main:app --host 0.0.0.0 --port 8000
