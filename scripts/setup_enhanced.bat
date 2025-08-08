@echo off
chcp 65001 >nul 2>&1
REM AI SVN代码审查工具 - 增强模式快速设置脚本

REM 切换到项目根目录
cd /d "%~dp0.."

echo.
echo ========================================
echo AI SVN代码审查工具 - 增强模式设置
echo ========================================
echo.

REM 检查Python环境
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 错误: 未找到Python环境
    echo 请确保Python 3.7+ 已正确安装并添加到PATH
    pause
    exit /b 1
)

echo ✅ Python环境检查通过

REM 检查配置文件
if not exist "config\config.yaml" (
    echo.
    echo ⚠️  警告: 未找到配置文件 config\config.yaml
    echo 正在从示例配置创建...
    copy "config\config.example.yaml" "config\config.yaml" >nul
    echo ✅ 配置文件已创建，请编辑 config\config.yaml 填入正确的配置
    echo.
    echo 主要需要配置的项目:
    echo   - svn.repository_url: SVN仓库地址
    echo   - svn.username: SVN用户名
    echo   - svn.password: SVN密码
    echo   - ai.api_key: AI API密钥
    echo   - dingtalk.webhook_url: 钉钉webhook地址
    echo.
    set /p continue="是否现在编辑配置文件? (y/n): "
    if /i "%continue%"=="y" (
        notepad "config\config.yaml"
    )
)

REM 数据迁移
echo.
echo 🔄 检查是否需要数据迁移...
if exist "data\processed_commits.json" (
    echo 发现旧版本数据文件，正在迁移到新格式...
    python migrate_data.py
    if %errorlevel% neq 0 (
        echo ❌ 数据迁移失败
        pause
        exit /b 1
    )
) else (
    echo ℹ️  无需数据迁移
)

REM 安装依赖
echo.
echo 📦 检查并安装依赖包...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ❌ 依赖安装失败
    pause
    exit /b 1
)

echo ✅ 依赖安装完成

REM 创建必要目录
echo.
echo 📁 创建必要目录...
if not exist "data" mkdir data
if not exist "data\cache" mkdir "data\cache"
if not exist "logs" mkdir logs

echo ✅ 目录创建完成

REM 显示启动选项
echo.
echo 🚀 设置完成! 请选择启动模式:
echo.
echo 1. 增强模式 (推荐) - 支持webhook和更好的状态管理
echo 2. 传统模式 - 定时轮询检查
echo 3. 显示帮助信息
echo 4. 退出
echo.

set /p choice="请选择 (1-4): "

if "%choice%"=="1" (
    echo.
    echo 🔥 启动增强模式...
    echo 💡 提示: SVN post-commit hook配置请参考 hooks\post-commit.bat
    echo.
    python src\main.py --enhanced
) else if "%choice%"=="2" (
    echo.
    echo 📊 启动传统模式...
    echo.
    python src\main.py --traditional
) else if "%choice%"=="3" (
    echo.
    python src\main.py --help
    pause
) else if "%choice%"=="4" (
    echo 👋 退出设置
    exit /b 0
) else (
    echo ❌ 无效选择
    pause
    exit /b 1
)

pause
