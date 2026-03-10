#!/usr/bin/env bash
#
# Start the Industrial Dashboard — backend and frontend in one command.
# Usage: ./start.sh
#
# Installs dependencies if needed, initializes the database, and
# starts both servers. Press Ctrl+C to stop everything.

set -e

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
BACKEND_DIR="$PROJECT_DIR/backend"
FRONTEND_DIR="$PROJECT_DIR/frontend"
VENV_DIR="$PROJECT_DIR/venv"

# Cleanup child processes on exit
cleanup() {
    echo ""
    echo "Shutting down..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    echo "Done."
}
trap cleanup EXIT INT TERM

# --- Backend setup ---
echo "==> Setting up backend..."

if [ ! -d "$VENV_DIR" ]; then
    echo "    Creating Python virtual environment..."
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install -q -r "$BACKEND_DIR/requirements.txt"

echo "    Starting FastAPI server on http://localhost:8000"
echo "    API docs at http://localhost:8000/docs"
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload &
BACKEND_PID=$!

# --- Frontend setup ---
echo "==> Setting up frontend..."

if [ ! -d "$FRONTEND_DIR/node_modules" ]; then
    echo "    Installing Node dependencies..."
    (cd "$FRONTEND_DIR" && npm install)
fi

echo "    Starting Vite dev server on http://localhost:5173"
(cd "$FRONTEND_DIR" && npm run dev) &
FRONTEND_PID=$!

echo ""
echo "==> Dashboard ready!"
echo "    Frontend: http://localhost:5173"
echo "    Backend:  http://localhost:8000"
echo "    API Docs: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop."

# Wait for either process to exit
wait
