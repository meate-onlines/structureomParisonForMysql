#!/bin/bash
# 数据库表结构比较工具安装脚本

echo "正在安装数据库表结构比较工具..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | grep -oP '\d+\.\d+')
required_version="3.7"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" = "$required_version" ]; then
    echo "Python版本检查通过: $(python3 --version)"
else
    echo "错误: 需要Python 3.7或更高版本，当前版本: $(python3 --version)"
    exit 1
fi

# 创建虚拟环境
echo "创建虚拟环境..."
python3 -m venv venv

# 激活虚拟环境
echo "激活虚拟环境..."
source venv/bin/activate

# 升级pip
echo "升级pip..."
pip install --upgrade pip

# 安装依赖包
echo "安装依赖包..."
pip install -r requirements.txt

# 设置执行权限
chmod +x database_schema_comparator.py

echo "安装完成！"
echo ""
echo "使用方法："
echo "1. 复制config_template.json为config.json并修改配置"
echo "2. 激活虚拟环境: source venv/bin/activate"
echo "3. 运行脚本: python database_schema_comparator.py config.json"
echo ""
echo "示例："
echo "  cp config_template.json my_config.json"
echo "  # 编辑my_config.json文件"
echo "  source venv/bin/activate"
echo "  python database_schema_comparator.py my_config.json"