#!/bin/bash

# ==========================================================
# GitHub Contribution Meter Launcher (Unix / macOS / Linux)
# ==========================================================

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "[SYSTEM] Running pre-flight checks..."

# 1. Check Python installation
if ! command -v python3 &> /dev/null; then
    if ! command -v python &> /dev/null; then
        echo "[ERROR] Python was not found in your PATH."
        echo "Please install Python 3.12+ and try again."
        exit 1
    else
        PYTHON_CMD="python"
    fi
else
    PYTHON_CMD="python3"
fi

# 2. Check for .env file
if [ ! -f "$APP_DIR/.env" ]; then
    if [ -f "$APP_DIR/.env.example" ]; then
        echo "[SYSTEM] Creating .env from .env.example..."
        cp "$APP_DIR/.env.example" "$APP_DIR/.env"
        echo "[WARNING] Please update the GITHUB_PROFILE value in your .env file."
    else
        echo "[ERROR] .env.example not found. Manual .env creation needed."
        exit 1
    fi
fi

# 3. Start Background Server
echo "[SYSTEM] Starting API server on port 8090..."
$PYTHON_CMD "$APP_DIR/server.py" > /dev/null 2>&1 &
SERVER_PID=$!

# Trap signals to clean up the background server on exit
cleanup() {
    echo "[SYSTEM] Shutting down background server (PID: $SERVER_PID)..."
    kill "$SERVER_PID" 2>/dev/null
}
trap cleanup EXIT INT TERM

# 4. Let the server spin up for 2 seconds
sleep 2

# 5. Launch URL details
APP_URL="http://localhost:8090/github-meter.html"
WIDTH=930
HEIGHT=310

# 6. Launch Chrome/Edge in App Mode if available
echo "[SYSTEM] Launching widget window..."

if [ "$(uname)" == "Darwin" ]; then
    # macOS Specific Chrome Launch
    if [ -d "/Applications/Google Chrome.app" ]; then
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
            --app="$APP_URL" \
            --window-size="$WIDTH","$HEIGHT" \
            --user-data-dir="/tmp/GithubMeterProfile" \
            --disable-extensions \
            --no-first-run &
        # Keep launcher running in foreground to capture cleanup trap
        wait
        exit 0
    fi
fi

# Fallback default browser launch
if command -v xdg-open &> /dev/null; then
    xdg-open "$APP_URL"
elif command -v open &> /dev/null; then
    open "$APP_URL"
else
    echo "[SYSTEM] Please open $APP_URL in your browser."
fi

# Wait for background process
wait
