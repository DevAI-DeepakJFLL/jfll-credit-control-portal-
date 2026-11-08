#!/usr/bin/env bash
set -e

echo "=========================================================="
echo " Starting Jet Freight Logistics Credit Control CRM"
echo "=========================================================="

# Ensure directories exist
mkdir -p backend/storage/memos backend/storage/uploads

# Activate Python virtual environment if present
if [ -f "backend/venv/bin/activate" ]; then
  source backend/venv/bin/activate
fi

BACKEND_PORT="${PORT:-8001}"
FRONTEND_PORT="${FRONTEND_PORT:-3000}"

# 1. Start Backend in background
echo "-> Starting FastAPI Backend on http://localhost:${BACKEND_PORT}..."
python3 -m uvicorn backend.app.main:app --host 0.0.0.0 --port "${BACKEND_PORT}" &
BACKEND_PID=$!

# Trap signals to kill processes on exit
trap "kill $BACKEND_PID 2>/dev/null || true; exit" SIGINT SIGTERM EXIT

# 2. Start Frontend
echo "-> Starting React TypeScript Frontend on http://localhost:${FRONTEND_PORT}..."
cd frontend
npm run dev -- --host 0.0.0.0 --port "${FRONTEND_PORT}"

wait $BACKEND_PID
