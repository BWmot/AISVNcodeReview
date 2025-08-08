@echo off
chcp 65001
title AI SVN Code Review Tool

echo ========================================
echo   AI SVN 代码审查工具
echo ========================================
echo.

REM 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

REM 检查虚拟环境是否存在
if not exist "venv\" (
    echo 🔧 正在创建虚拟环境...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ❌ 创建虚拟环境失败
        pause
        exit /b 1
    )
)

REM 激活虚拟环境
echo 🚀 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo 📦 安装依赖包...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ 依赖包安装失败
    pause
    exit /b 1
)

REM 验证关键模块是否安装成功
echo 🔍 验证关键模块...
python -c "import schedule, requests, yaml" >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️ 关键模块验证失败，尝试重新安装...
    pip install schedule requests pyyaml --upgrade
    if %errorlevel% neq 0 (
        echo ❌ 模块安装失败，请检查网络连接和Python环境
        pause
        exit /b 1
    )
)

REM 检查配置文件
if not exist "config\config.yaml" (
    echo ⚙️ 配置文件不存在，正在创建...
    copy "config\config.example.yaml" "config\config.yaml"
    echo ⚠️ 请编辑 config\config.yaml 文件配置您的参数
    echo    配置完成后重新运行此脚本
    pause
    exit /b 0
)

REM 启动程序
echo 🎯 启动AI代码审查工具...
python src\main.py

REM 程序已结束
echo.
echo 程序已结束，按任意键关闭窗口...
pause
