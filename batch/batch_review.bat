@echo off
chcp 65001 > nul
echo === SVN批量代码审查工具 ===
echo.

set /p days="请输入要审查的天数 (默认7天): "
if "%days%"=="" set days=7

echo 开始审查最近 %days% 天的SVN提交...
echo.

python simple_batch_review.py %days%

echo.
pause
