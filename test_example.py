#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库表结构比较工具测试示例
创建示例SQLite数据库用于测试
"""

import sqlite3
import os
import json

def create_template_database():
    """创建模板数据库"""
    if os.path.exists('template.db'):
        os.remove('template.db')
    
    conn = sqlite3.connect('template.db')
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(50) NOT NULL UNIQUE,
        email VARCHAR(100) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    )
    ''')
    
    # 创建产品表
    cursor.execute('''
    CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        price DECIMAL(10,2) NOT NULL,
        stock_quantity INTEGER DEFAULT 0,
        category_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建订单表
    cursor.execute('''
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total_amount DECIMAL(10,2) NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("模板数据库 template.db 创建完成")

def create_target_database():
    """创建目标数据库（有差异）"""
    if os.path.exists('target.db'):
        os.remove('target.db')
    
    conn = sqlite3.connect('target.db')
    cursor = conn.cursor()
    
    # 创建用户表（缺少updated_at列，多了phone列）
    cursor.execute('''
    CREATE TABLE users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(50) NOT NULL UNIQUE,
        email VARCHAR(100) NOT NULL,
        password_hash VARCHAR(255) NOT NULL,
        phone VARCHAR(20),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_active BOOLEAN DEFAULT 1
    )
    ''')
    
    # 创建产品表（price类型不同）
    cursor.execute('''
    CREATE TABLE products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name VARCHAR(100) NOT NULL,
        description TEXT,
        price REAL NOT NULL,
        stock_quantity INTEGER DEFAULT 0,
        category_id INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建订单表（相同）
    cursor.execute('''
    CREATE TABLE orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        total_amount DECIMAL(10,2) NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
    ''')
    
    conn.commit()
    conn.close()
    print("目标数据库 target.db 创建完成")

def create_test_config():
    """创建测试配置文件"""
    config = {
        "template_database": {
            "name": "template",
            "type": "sqlite",
            "database": "./template.db"
        },
        "target_databases": {
            "target": {
                "name": "target",
                "type": "sqlite",
                "database": "./target.db"
            }
        },
        "tables_to_compare": [
            "users",
            "products",
            "orders"
        ]
    }
    
    with open('test_config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    print("测试配置文件 test_config.json 创建完成")

def main():
    """主函数"""
    print("创建测试数据库和配置文件...")
    
    create_template_database()
    create_target_database()
    create_test_config()
    
    print("\n测试环境准备完成！")
    print("\n运行测试命令：")
    print("python database_schema_comparator.py test_config.json")
    print("\n预期结果：")
    print("- users表：缺少updated_at列，多了phone列")
    print("- products表：price列类型不同")
    print("- orders表：结构一致")

if __name__ == "__main__":
    main()