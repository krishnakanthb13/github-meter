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

# 2. Check Python dependencies
echo "[SYSTEM] Checking Python dependencies..."
$PYTHON_CMD -c "import dotenv" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "[SYSTEM] Installing required packages..."
    $PYTHON_CMD -m pip install python-dotenv
fi

# 3. Check for .env file
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

# 4. Kill any existing server on port 8090
if command -v lsof &> /dev/null; then
    lsof -ti :8090 | xargs kill -9 2>/dev/null
elif command -v fuser &> /dev/null; then
    fuser -k 8090/tcp 2>/dev/null
fi

# 5. Start Background Server with logging
echo "[SYSTEM] Starting API server on port 8090..."
$PYTHON_CMD "$APP_DIR/server.py" > /tmp/github-meter-server.log 2>&1 &
SERVER_PID=$!

# Trap signals to clean up the background server on exit
cleanup() {
    echo "[SYSTEM] Shutting down background server (PID: $SERVER_PID)..."
    kill "$SERVER_PID" 2>/dev/null
}
trap cleanup EXIT INT TERM

# 6. Wait until server is actually ready (poll instead of fixed sleep)
echo "[SYSTEM] Waiting for server..."
for i in $(seq 1 30); do
    if curl -s -o /dev/null http://localhost:8090/api/config 2>/dev/null; then
        echo "[SYSTEM] Server is ready."
        break
    fi
    if ! ps -p $SERVER_PID > /dev/null 2>&1; then
        echo "[ERROR] Server failed to start. Check log: /tmp/github-meter-server.log"
        cat /tmp/github-meter-server.log 2>/dev/null
        exit 1
    fi
    sleep 0.5
done

# 6. Launch URL details
APP_URL="http://localhost:8090/github-meter.html"
WIDTH=930
HEIGHT=310

# 7. Launch Chrome/Edge in App Mode if available
echo "[SYSTEM] Launching widget window..."

if [ "$(uname)" == "Darwin" ]; then
    # macOS Specific Chrome Launch
    if [ -d "/Applications/Google Chrome.app" ]; then
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
            --app="$APP_URL" \
            --window-size="$WIDTH","$HEIGHT" \
            --user-data-dir="/tmp/GithubMeterProfile" \
            --disable-extensions \
            --no-first-run
        exit 0
    fi
fi

# Linux Chrome/Chromium in app mode
if command -v google-chrome &> /dev/null; then
    google-chrome --app="$APP_URL" \
        --window-size="$WIDTH","$HEIGHT" \
        --user-data-dir="/tmp/GithubMeterProfile" \
        --disable-extensions \
        --no-first-run
    exit 0
elif command -v chromium-browser &> /dev/null; then
    chromium-browser --app="$APP_URL" \
        --window-size="$WIDTH","$HEIGHT" \
        --user-data-dir="/tmp/GithubMeterProfile" \
        --disable-extensions \
        --no-first-run
    exit 0
elif command -v chromium &> /dev/null; then
    chromium --app="$APP_URL" \
        --window-size="$WIDTH","$HEIGHT" \
        --user-data-dir="/tmp/GithubMeterProfile" \
        --disable-extensions \
        --no-first-run
    exit 0
elif command -v microsoft-edge &> /dev/null; then
    microsoft-edge --app="$APP_URL" \
        --window-size="$WIDTH","$HEIGHT" \
        --user-data-dir="/tmp/GithubMeterProfile" \
        --disable-extensions \
        --no-first-run
    exit 0
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
