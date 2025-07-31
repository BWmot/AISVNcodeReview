REM 安装和管理Windows服务的脚本

@echo off
chcp 65001
title AI Code Review Service Manager

echo ========================================
echo   AI代码审查服务管理工具
echo ========================================
echo.

if "%1"=="install" goto install
if "%1"=="uninstall" goto uninstall
if "%1"=="start" goto start_service
if "%1"=="stop" goto stop_service
if "%1"=="restart" goto restart_service

:menu
echo 请选择操作:
echo 1. 安装服务
echo 2. 卸载服务
echo 3. 启动服务
echo 4. 停止服务
echo 5. 重启服务
echo 6. 退出
echo.
set /p choice=请输入选择 (1-6): 

if "%choice%"=="1" goto install
if "%choice%"=="2" goto uninstall
if "%choice%"=="3" goto start_service
if "%choice%"=="4" goto stop_service
if "%choice%"=="5" goto restart_service
if "%choice%"=="6" goto exit
goto menu

:install
echo 🔧 正在安装AI代码审查服务...

REM 检查是否为管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 需要管理员权限
    echo 请以管理员身份运行此脚本
    pause
    goto exit
)

REM 安装依赖包
echo 📦 安装服务依赖包...
pip install pywin32

REM 安装服务
python service_wrapper.py install
if %errorlevel% equ 0 (
    echo ✅ 服务安装成功
) else (
    echo ❌ 服务安装失败
)
pause
goto menu

:uninstall
echo 🗑️ 正在卸载AI代码审查服务...

REM 检查管理员权限
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 需要管理员权限
    pause
    goto exit
)

REM 先停止服务
python service_wrapper.py stop

REM 卸载服务
python service_wrapper.py remove
if %errorlevel% equ 0 (
    echo ✅ 服务卸载成功
) else (
    echo ❌ 服务卸载失败
)
pause
goto menu

:start_service
echo 🚀 正在启动AI代码审查服务...
python service_wrapper.py start
if %errorlevel% equ 0 (
    echo ✅ 服务启动成功
) else (
    echo ❌ 服务启动失败
)
pause
goto menu

:stop_service
echo 🛑 正在停止AI代码审查服务...
python service_wrapper.py stop
if %errorlevel% equ 0 (
    echo ✅ 服务停止成功
) else (
    echo ❌ 服务停止失败
)
pause
goto menu

:restart_service
echo 🔄 正在重启AI代码审查服务...
python service_wrapper.py restart
if %errorlevel% equ 0 (
    echo ✅ 服务重启成功
) else (
    echo ❌ 服务重启失败
)
pause
goto menu

:exit
exit /b 0
