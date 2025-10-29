@echo off
REM 数据库表结构比较工具安装脚本 (Windows版本)

echo 正在安装数据库表结构比较工具...

REM 检查Python版本
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python 3.7或更高版本
    pause
    exit /b 1
)

REM 创建虚拟环境
echo 创建虚拟环境...
python -m venv venv
if errorlevel 1 (
    echo 错误: 创建虚拟环境失败
    pause
    exit /b 1
)

REM 激活虚拟环境
echo 激活虚拟环境...
call venv\Scripts\activate.bat

REM 升级pip
echo 升级pip...
python -m pip install --upgrade pip

REM 安装MySQL连接器
echo 安装MySQL连接器...
pip install mysql-connector-python==8.2.0

REM 安装PostgreSQL连接器
echo 安装PostgreSQL连接器...
pip install psycopg2-binary --only-binary=all

REM 安装其他依赖
echo 安装其他依赖...
pip install typing-extensions==4.8.0

echo 安装完成！
echo.
echo 使用方法：
echo 1. 复制config_template.json为config.json并修改配置
echo 2. 激活虚拟环境: venv\Scripts\activate.bat
echo 3. 运行脚本: python database_schema_comparator.py config.json
echo.
echo 示例：
echo   copy config_template.json my_config.json
echo   REM 编辑my_config.json文件
echo   venv\Scripts\activate.bat
echo   python database_schema_comparator.py my_config.json
echo.
pause
