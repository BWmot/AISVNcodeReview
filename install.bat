@echo off
echo.
echo ========================================
echo    AI SVN Code Review Tool - Installer
echo ========================================
echo.

echo [1/4] Checking Python environment...
python --version >nul 2^&1
if errorlevel 1 (
    echo ERROR: Python not found, please install Python 3.7+
    echo Download: https://www.python.org/downloads/
    pause
    exit /b 1
)

python --version
echo Python environment check passed

echo.
echo [2/4] Upgrading pip...
python -m pip install --upgrade pip
if errorlevel 1 (
    echo WARNING: pip upgrade failed, continuing...
)

echo.
echo [3/4] Installing Python dependencies...
echo Installing: pyyaml requests schedule...

python -m pip install pyyaml requests schedule -i https://pypi.tuna.tsinghua.edu.cn/simple/
if errorlevel 1 (
    echo Mirror failed, trying official source...
    python -m pip install pyyaml requests schedule
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies!
        echo Please run manually: pip install pyyaml requests schedule
        pause
        exit /b 1
    )
)

echo Dependencies installed successfully

echo.
echo [4/4] Setting up configuration files...
if not exist "config\config.yaml" (
    if exist "config\config.example.yaml" (
        copy "config\config.example.yaml" "config\config.yaml" >nul
        echo Created config file: config\config.yaml
        echo WARNING: Please edit config\config.yaml
    ) else (
        echo WARNING: Config template not found
    )
) else (
    echo Config file already exists
)

if not exist "config\user_mapping.yaml" (
    if exist "config\user_mapping.example.yaml" (
        copy "config\user_mapping.example.yaml" "config\user_mapping.yaml" >nul
        echo Created user mapping file
    )
) else (
    echo User mapping file already exists
)

echo.
echo ========================================
echo           Installation Complete!
echo ========================================
echo.
echo Next steps:
echo   1. Edit config: notepad config\config.yaml
echo   2. Test: python batch\simple_batch_review.py --help
echo   3. Run: python batch\simple_batch_review.py 1
echo.
echo For help: see INSTALL_GUIDE.md
echo.

pause
