#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试通配符功能的脚本
"""

import sqlite3
import os
import json

def create_test_databases():
    """创建测试数据库"""
    # 创建模板数据库
    if os.path.exists('template_wildcard.db'):
        os.remove('template_wildcard.db')
    
    conn = sqlite3.connect('template_wildcard.db')
    cursor = conn.cursor()
    
    # 创建多个表
    cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(50) NOT NULL,
        email VARCHAR(100) NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        price DECIMAL(10,2) NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total_amount DECIMAL(10,2) NOT NULL
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(50) NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ 模板数据库创建完成 (4个表: users, products, orders, categories)")
    
    # 创建目标数据库（有差异）
    if os.path.exists('target_wildcard.db'):
        os.remove('target_wildcard.db')
    
    conn = sqlite3.connect('target_wildcard.db')
    cursor = conn.cursor()
    
    # users表缺少email列
    cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(50) NOT NULL
    )
    ''')
    
    # products表一致
    cursor.execute('''
    CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        price DECIMAL(10,2) NOT NULL
    )
    ''')
    
    # orders表类型不同
    cursor.execute('''
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total_amount REAL NOT NULL
    )
    ''')
    
    # categories表一致
    cursor.execute('''
    CREATE TABLE categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(50) NOT NULL
    )
    ''')
    
    conn.commit()
    conn.close()
    print("✓ 目标数据库创建完成 (有差异)")

def create_wildcard_config():
    """创建使用通配符的配置文件"""
    config = {
        "template_database": {
            "name": "template",
            "type": "sqlite",
            "database": "./template_wildcard.db"
        },
        "target_databases": {
            "target": {
                "name": "target",
                "type": "sqlite",
                "database": "./target_wildcard.db"
            }
        },
        "tables_to_compare": "*"
    }
    
    with open('test_wildcard_config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print("✓ 通配符配置文件创建完成")

def main():
    """主函数"""
    print("=" * 60)
    print("通配符功能测试准备")
    print("=" * 60)
    
    create_test_databases()
    create_wildcard_config()
    
    print("\n" + "=" * 60)
    print("测试环境准备完成！")
    print("=" * 60)
    print("\n运行测试命令：")
    print("  python database_schema_comparator.py test_wildcard_config.json")
    print("\n预期结果：")
    print("  - 将自动检测并对比所有4个表")
    print("  - users表：缺少email列")
    print("  - products表：结构一致")
    print("  - orders表：total_amount类型不同")
    print("  - categories表：结构一致")
    print("\n查看日志：")
    print("  tail -f schema_comparison.log")
    print("\n清理测试文件：")
    print("  rm template_wildcard.db target_wildcard.db test_wildcard_config.json")

if __name__ == "__main__":
    main()
