@echo off
REM Windows 启动脚本
REM 正确设置 PYTHONPATH 并启动 FastAPI 服务器

cd /d "%~dp0"
echo 当前目录: %cd%

REM 设置 PYTHONPATH 包含项目根目录
set PYTHONPATH=%~dp0..;%PYTHONPATH%
echo PYTHONPATH: %PYTHONPATH%

REM 启动 Uvicorn
echo 启动 FastAPI 服务器...
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

pause
