@echo off
REM SVN Post-Commit Hook Script for Windows
REM 在SVN提交后自动触发AI代码审查
REM
REM 使用方法：
REM 1. 将此脚本复制到SVN仓库的hooks目录下，命名为post-commit.bat
REM 2. 配置下面的REVIEW_TOOL_HOST和REVIEW_TOOL_PORT变量
REM 3. 确保curl命令可用（Windows 10+ 自带）

set REPOS=%1
set REV=%2

REM 配置审查工具的地址
set REVIEW_TOOL_HOST=localhost
set REVIEW_TOOL_PORT=8080

REM 日志文件
set LOG_FILE=C:\temp\svn-review-hook.log

REM 记录日志
echo [%date% %time%] SVN Post-Commit Hook 开始: %REPOS%, 版本 %REV% >> "%LOG_FILE%"

REM 获取提交信息
for /f "tokens=*" %%i in ('svnlook author -r %REV% "%REPOS%"') do set AUTHOR=%%i
for /f "tokens=*" %%i in ('svnlook log -r %REV% "%REPOS%"') do set MESSAGE=%%i

REM 转义消息中的引号和换行符
set MESSAGE=%MESSAGE:"=\"%
set MESSAGE=%MESSAGE:
=\n%

REM 构造JSON数据并保存到临时文件
set TEMP_JSON=%TEMP%\svn-hook-%REV%.json
(
echo {
echo   "revision": "%REV%",
echo   "author": "%AUTHOR%",
echo   "message": "%MESSAGE%",
echo   "repository": "%REPOS%",
echo   "timestamp": "%date% %time%"
echo }
) > "%TEMP_JSON%"

REM 发送POST请求
curl -X POST ^
     -H "Content-Type: application/json" ^
     -d @"%TEMP_JSON%" ^
     "http://%REVIEW_TOOL_HOST%:%REVIEW_TOOL_PORT%/svn-hook" ^
     --connect-timeout 10 ^
     --max-time 30 ^
     >> "%LOG_FILE%" 2>&1

if %errorlevel% equ 0 (
    echo [%date% %time%] Webhook发送成功: 版本 %REV% >> "%LOG_FILE%"
) else (
    echo [%date% %time%] Webhook发送失败: 版本 %REV% >> "%LOG_FILE%"
)

REM 清理临时文件
del "%TEMP_JSON%" 2>nul

echo [%date% %time%] SVN Post-Commit Hook 完成: 版本 %REV% >> "%LOG_FILE%"

exit /b 0
