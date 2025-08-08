@echo off
chcp 65001 >nul 2>&1

echo ========================================
echo AI SVN Code Review Tool - Setup  
echo ========================================

REM Check Python environment
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python not found
    echo Please install Python 3.7+ and add to PATH
    pause
    exit /b 1
)

echo Python environment OK

REM Check config file
if not exist "config\config.yaml" (
    echo.
    echo WARNING: config.yaml not found
    echo Creating from example...
    copy "config\config.example.yaml" "config\config.yaml" >nul
    echo Config file created. Please edit config\config.yaml
    echo.
    echo Required settings:
    echo   - svn.repository_url
    echo   - svn.username  
    echo   - svn.password
    echo   - ai.api_key
    echo   - dingtalk.webhook_url
    echo.
    set /p continue="Edit config now? (y/n): "
    if /i "%continue%"=="y" (
        notepad "config\config.yaml"
    )
)

REM Data migration
echo.
echo Checking data migration...
if exist "data\processed_commits.json" (
    echo Found old data file, migrating...
    python migrate_data.py
    if %errorlevel% neq 0 (
        echo Data migration failed
        pause
        exit /b 1
    )
) else (
    echo No migration needed
)

REM Install dependencies
echo.
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Dependency installation failed
    pause
    exit /b 1
)

echo Dependencies installed

REM Create directories
echo.
echo Creating directories...
if not exist "data" mkdir data
if not exist "data\cache" mkdir "data\cache"
if not exist "logs" mkdir logs

echo Directories created

REM Show options
echo.
echo Setup complete! Choose startup mode:
echo.
echo 1. Enhanced mode (recommended) - webhook + state management
echo 2. Traditional mode - polling only
echo 3. Show help
echo 4. Exit
echo.

set /p choice="Choose (1-4): "

if "%choice%"=="1" (
    echo.
    echo Starting enhanced mode...
    echo TIP: Configure SVN post-commit hook, see hooks\post-commit.bat
    echo.
    python src\main.py --enhanced
) else if "%choice%"=="2" (
    echo.
    echo Starting traditional mode...
    echo.
    python src\main.py --traditional
) else if "%choice%"=="3" (
    echo.
    python src\main.py --help
    pause
) else if "%choice%"=="4" (
    echo Goodbye
    exit /b 0
) else (
    echo Invalid choice
    pause
    exit /b 1
)

pause
