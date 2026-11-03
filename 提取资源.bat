@echo off
chcp 65001 >nul
cd /d "%~dp0"
if "%~1"=="" (
    python cli.py
) else (
    python cli.py "%~1"
)
echo.
echo 提取结束，按任意键关闭窗口。
pause >nul
