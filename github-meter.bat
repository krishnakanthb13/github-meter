@echo off
title GitHub Contribution Meter
setlocal enabledelayedexpansion

:: ==========================================================
:: GitHub Contribution Meter Launcher
:: ==========================================================

echo [SYSTEM] Running pre-flight checks...

:: 1. Check Python installation
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [ERROR] Python was not found in your PATH.
    echo Please install Python 3.12+ and ensure "Add Python to PATH" is checked.
    pause
    exit /b 1
)

:: 2. Check Python dependencies
echo [SYSTEM] Checking Python dependencies...
python -c "import selenium, dotenv" 2>nul
if %errorlevel% neq 0 (
    echo [SYSTEM] Installing required packages...
    python -m pip install selenium python-dotenv webdriver-manager
)

:: 3. Check for .env file
if not exist "%~dp0.env" (
    if exist "%~dp0.env.example" (
        echo [SYSTEM] Creating .env from .env.example...
        copy "%~dp0.env.example" "%~dp0.env" >nul
        echo [WARNING] Please update the GITHUB_PROFILE value in your .env file.
    ) else (
        echo [ERROR] .env.example not found. Manual .env creation needed.
        pause
        exit /b 1
    )
)

:: 4. Start Background Python API & Web Server
echo [SYSTEM] Starting API server on port 8090...
start /min "GitHub Meter Server" python "%~dp0server.py"

:: 5. Wait until server is ready
echo [SYSTEM] Waiting for server...
set "READY=0"
for /l %%i in (1,1,20) do (
    if "!READY!"=="0" (
        powershell -Command "$r = try { (Invoke-WebRequest -Uri 'http://localhost:8090/api/config' -UseBasicParsing -TimeoutSec 1).StatusCode } catch { 0 }; if ($r -eq 200) { exit 0 } else { exit 1 }" 2>nul
        if !errorlevel! equ 0 (
            echo [SYSTEM] Server is ready.
            set "READY=1"
        ) else (
            timeout /t 1 /nobreak >nul
        )
    )
)
if "!READY!"=="0" (
    echo [ERROR] Server failed to start within 20 seconds.
    pause
    exit /b 1
)

:: 6. Configure window dimensions & screen placement
set WIDTH=930
set HEIGHT=310
set MARGIN=40

:: 7. Detect screen resolution via PowerShell
echo [SYSTEM] Optimizing window placement...
for /f "delims=" %%a in ('powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Width"') do set "SCR_W=%%a"
for /f "delims=" %%a in ('powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Screen]::PrimaryScreen.Bounds.Height"') do set "SCR_H=%%a"

:: Defaults if detection fails
if "%SCR_W%"=="" set "SCR_W=1920"
if "%SCR_H%"=="" set "SCR_H=1080"

:: Calculate position (Bottom Right Corner)
set /a POS_X=%SCR_W% - %WIDTH% - %MARGIN%
set /a POS_Y=%SCR_H% - %HEIGHT% - %MARGIN% - 40

:: 8. Set App URL
set "APP_URL=http://localhost:8090/github-meter.html"

:: 9. Launch Arguments
set "ARGS=--app="%APP_URL%" --window-size=%WIDTH%,%HEIGHT% --window-position=%POS_X%,%POS_Y% --user-data-dir="%TEMP%\GithubMeterProfile" --disable-extensions --no-first-run"

:: 10. Launch the Browser (Chrome preferred, Edge fallback)
echo [SYSTEM] Launching widget window...

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" %ARGS%
    exit /b
)
if exist "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe" %ARGS%
    exit /b
)
if exist "C:\Program Files\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files\Microsoft\Edge\Application\msedge.exe" %ARGS%
    exit /b
)
if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" %ARGS%
    exit /b
)

:: Final Fallback to default browser
start "" "%APP_URL%"
exit /b
