@echo off
chcp 65001 >nul
echo 启动数据库配置工具...
echo.

REM 检查虚拟环境
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
) else (
    echo 警告: 未找到虚拟环境，使用系统Python
)

REM 运行GUI
python config_gui.py

pause

