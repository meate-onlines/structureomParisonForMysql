#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库表结构比较工具
支持比较多个数据库中相同表的结构，并基于模板数据库生成修改语句
"""

import json
import logging
import argparse
import sys
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
from datetime import datetime
import mysql.connector
import psycopg2
import sqlite3


@dataclass
class ColumnInfo:
    """列信息数据类"""
    name: str
    data_type: str
    is_nullable: bool
    default_value: Optional[str]
    character_maximum_length: Optional[int]
    numeric_precision: Optional[int]
    numeric_scale: Optional[int]
    column_key: str = ""
    extra: str = ""
    comment: str = ""
    ordinal_position: int = 0


@dataclass
class TableInfo:
    """表信息数据类"""
    name: str
    columns: List[ColumnInfo]
    primary_keys: List[str]
    indexes: List[Dict[str, Any]]
    foreign_keys: List[Dict[str, Any]]
    comment: str = ""


class DatabaseConnector:
    """数据库连接器基类"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.connection = None
        
    def connect(self):
        """连接数据库"""
        raise NotImplementedError
        
    def disconnect(self):
        """断开数据库连接"""
        if self.connection:
            self.connection.close()
            
    def get_table_info(self, table_name: str) -> TableInfo:
        """获取表结构信息"""
        raise NotImplementedError
        
    def execute_query(self, query: str) -> List[Tuple]:
        """执行查询"""
        cursor = self.connection.cursor()
        cursor.execute(query)
        result = cursor.fetchall()
        cursor.close()
        return result
        
    def get_all_tables(self) -> List[str]:
        """获取数据库中的所有表名"""
        raise NotImplementedError


class MySQLConnector(DatabaseConnector):
    """MySQL数据库连接器"""
    
    def connect(self):
        """连接MySQL数据库"""
        try:
            self.connection = mysql.connector.connect(
                host=self.config['host'],
                port=self.config.get('port', 3306),
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database']
            )
            logging.info(f"已连接到MySQL数据库: {self.config['database']}")
        except Exception as e:
            logging.error(f"连接MySQL数据库失败: {e}")
            raise
            
    def get_all_tables(self) -> List[str]:
        """获取MySQL数据库中的所有表名"""
        query = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
        """
        cursor = self.connection.cursor()
        cursor.execute(query, (self.config['database'],))
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables
            
    def get_table_info(self, table_name: str) -> TableInfo:
        """获取MySQL表结构信息"""
        # 获取列信息
        columns_query = """
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            COLUMN_DEFAULT,
            CHARACTER_MAXIMUM_LENGTH,
            NUMERIC_PRECISION,
            NUMERIC_SCALE,
            COLUMN_KEY,
            EXTRA,
            COLUMN_COMMENT,
            ORDINAL_POSITION
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
        """
        
        cursor = self.connection.cursor()
        cursor.execute(columns_query, (self.config['database'], table_name))
        column_rows = cursor.fetchall()
        
        columns = []
        for row in column_rows:
            columns.append(ColumnInfo(
                name=row[0],
                data_type=row[1],
                is_nullable=(row[2] == 'YES'),
                default_value=row[3],
                character_maximum_length=row[4],
                numeric_precision=row[5],
                numeric_scale=row[6],
                column_key=row[7] or "",
                extra=row[8] or "",
                comment=row[9] or "",
                ordinal_position=row[10]
            ))
        
        # 获取主键信息
        pk_query = """
        SELECT COLUMN_NAME 
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s AND CONSTRAINT_NAME = 'PRIMARY'
        ORDER BY ORDINAL_POSITION
        """
        cursor.execute(pk_query, (self.config['database'], table_name))
        primary_keys = [row[0] for row in cursor.fetchall()]
        
        # 获取索引信息
        index_query = """
        SELECT 
            INDEX_NAME,
            COLUMN_NAME,
            NON_UNIQUE,
            INDEX_TYPE
        FROM INFORMATION_SCHEMA.STATISTICS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        ORDER BY INDEX_NAME, SEQ_IN_INDEX
        """
        cursor.execute(index_query, (self.config['database'], table_name))
        index_rows = cursor.fetchall()
        
        indexes = {}
        for row in index_rows:
            index_name = row[0]
            if index_name not in indexes:
                indexes[index_name] = {
                    'name': index_name,
                    'columns': [],
                    'unique': row[2] == 0,
                    'type': row[3]
                }
            indexes[index_name]['columns'].append(row[1])
        
        # 获取外键信息
        fk_query = """
        SELECT 
            CONSTRAINT_NAME,
            COLUMN_NAME,
            REFERENCED_TABLE_NAME,
            REFERENCED_COLUMN_NAME
        FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s 
        AND REFERENCED_TABLE_NAME IS NOT NULL
        """
        cursor.execute(fk_query, (self.config['database'], table_name))
        fk_rows = cursor.fetchall()
        
        foreign_keys = []
        for row in fk_rows:
            foreign_keys.append({
                'name': row[0],
                'column': row[1],
                'referenced_table': row[2],
                'referenced_column': row[3]
            })
        
        # 获取表注释
        table_comment_query = """
        SELECT TABLE_COMMENT 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        """
        cursor.execute(table_comment_query, (self.config['database'], table_name))
        table_comment_row = cursor.fetchone()
        table_comment = table_comment_row[0] if table_comment_row else ""
        
        cursor.close()
        
        return TableInfo(
            name=table_name,
            columns=columns,
            primary_keys=primary_keys,
            indexes=list(indexes.values()),
            foreign_keys=foreign_keys,
            comment=table_comment
        )


class PostgreSQLConnector(DatabaseConnector):
    """PostgreSQL数据库连接器"""
    
    def connect(self):
        """连接PostgreSQL数据库"""
        try:
            self.connection = psycopg2.connect(
                host=self.config['host'],
                port=self.config.get('port', 5432),
                user=self.config['user'],
                password=self.config['password'],
                database=self.config['database']
            )
            logging.info(f"已连接到PostgreSQL数据库: {self.config['database']}")
        except Exception as e:
            logging.error(f"连接PostgreSQL数据库失败: {e}")
            raise
            
    def get_all_tables(self) -> List[str]:
        """获取PostgreSQL数据库中的所有表名"""
        query = """
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
        ORDER BY table_name
        """
        cursor = self.connection.cursor()
        cursor.execute(query)
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables
            
    def get_table_info(self, table_name: str) -> TableInfo:
        """获取PostgreSQL表结构信息"""
        # 获取列信息
        columns_query = """
        SELECT 
            c.column_name,
            c.data_type,
            c.is_nullable,
            c.column_default,
            c.character_maximum_length,
            c.numeric_precision,
            c.numeric_scale,
            CASE WHEN pk.column_name IS NOT NULL THEN 'PRI' ELSE '' END as column_key,
            CASE WHEN c.column_default LIKE 'nextval%' THEN 'auto_increment' ELSE '' END as extra,
            COALESCE(pgd.description, '') as comment,
            c.ordinal_position
        FROM information_schema.columns c
        LEFT JOIN (
            SELECT ku.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage ku ON tc.constraint_name = ku.constraint_name
            WHERE tc.constraint_type = 'PRIMARY KEY' 
            AND tc.table_name = %s
            AND tc.table_schema = 'public'
        ) pk ON c.column_name = pk.column_name
        LEFT JOIN pg_catalog.pg_statio_all_tables st ON c.table_name = st.relname
        LEFT JOIN pg_catalog.pg_description pgd ON pgd.objoid = st.relid 
        AND pgd.objsubid = c.ordinal_position
        WHERE c.table_name = %s AND c.table_schema = 'public'
        ORDER BY c.ordinal_position
        """
        
        cursor = self.connection.cursor()
        cursor.execute(columns_query, (table_name, table_name))
        column_rows = cursor.fetchall()
        
        columns = []
        for row in column_rows:
            columns.append(ColumnInfo(
                name=row[0],
                data_type=row[1],
                is_nullable=(row[2] == 'YES'),
                default_value=row[3],
                character_maximum_length=row[4],
                numeric_precision=row[5],
                numeric_scale=row[6],
                column_key=row[7] or "",
                extra=row[8] or "",
                comment=row[9] or "",
                ordinal_position=row[10]
            ))
        
        # 获取主键信息
        pk_query = """
        SELECT ku.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage ku ON tc.constraint_name = ku.constraint_name
        WHERE tc.constraint_type = 'PRIMARY KEY' 
        AND tc.table_name = %s
        AND tc.table_schema = 'public'
        ORDER BY ku.ordinal_position
        """
        cursor.execute(pk_query, (table_name,))
        primary_keys = [row[0] for row in cursor.fetchall()]
        
        # 获取索引信息
        index_query = """
        SELECT 
            i.relname as index_name,
            a.attname as column_name,
            NOT ix.indisunique as non_unique,
            am.amname as index_type
        FROM pg_class t
        JOIN pg_index ix ON t.oid = ix.indrelid
        JOIN pg_class i ON i.oid = ix.indexrelid
        JOIN pg_attribute a ON a.attrelid = t.oid AND a.attnum = ANY(ix.indkey)
        JOIN pg_am am ON i.relam = am.oid
        WHERE t.relname = %s
        AND t.relkind = 'r'
        ORDER BY i.relname, a.attnum
        """
        cursor.execute(index_query, (table_name,))
        index_rows = cursor.fetchall()
        
        indexes = {}
        for row in index_rows:
            index_name = row[0]
            if index_name not in indexes:
                indexes[index_name] = {
                    'name': index_name,
                    'columns': [],
                    'unique': not row[2],
                    'type': row[3]
                }
            indexes[index_name]['columns'].append(row[1])
        
        # 获取外键信息
        fk_query = """
        SELECT 
            tc.constraint_name,
            kcu.column_name,
            ccu.table_name AS foreign_table_name,
            ccu.column_name AS foreign_column_name
        FROM information_schema.table_constraints AS tc
        JOIN information_schema.key_column_usage AS kcu ON tc.constraint_name = kcu.constraint_name
        JOIN information_schema.constraint_column_usage AS ccu ON ccu.constraint_name = tc.constraint_name
        WHERE tc.constraint_type = 'FOREIGN KEY' 
        AND tc.table_name = %s
        AND tc.table_schema = 'public'
        """
        cursor.execute(fk_query, (table_name,))
        fk_rows = cursor.fetchall()
        
        foreign_keys = []
        for row in fk_rows:
            foreign_keys.append({
                'name': row[0],
                'column': row[1],
                'referenced_table': row[2],
                'referenced_column': row[3]
            })
        
        # 获取表注释
        table_comment_query = """
        SELECT obj_description(c.oid) 
        FROM pg_class c 
        WHERE c.relname = %s AND c.relkind = 'r'
        """
        cursor.execute(table_comment_query, (table_name,))
        table_comment_row = cursor.fetchone()
        table_comment = table_comment_row[0] if table_comment_row and table_comment_row[0] else ""
        
        cursor.close()
        
        return TableInfo(
            name=table_name,
            columns=columns,
            primary_keys=primary_keys,
            indexes=list(indexes.values()),
            foreign_keys=foreign_keys,
            comment=table_comment
        )


class SQLiteConnector(DatabaseConnector):
    """SQLite数据库连接器"""
    
    def connect(self):
        """连接SQLite数据库"""
        try:
            self.connection = sqlite3.connect(self.config['database'])
            logging.info(f"已连接到SQLite数据库: {self.config['database']}")
        except Exception as e:
            logging.error(f"连接SQLite数据库失败: {e}")
            raise
            
    def get_all_tables(self) -> List[str]:
        """获取SQLite数据库中的所有表名"""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        tables = [row[0] for row in cursor.fetchall()]
        cursor.close()
        return tables
            
    def get_table_info(self, table_name: str) -> TableInfo:
        """获取SQLite表结构信息"""
        cursor = self.connection.cursor()
        
        # 获取列信息
        cursor.execute(f"PRAGMA table_info({table_name})")
        column_rows = cursor.fetchall()
        
        columns = []
        primary_keys = []
        
        for row in column_rows:
            cid, name, data_type, not_null, default_value, pk = row
            
            columns.append(ColumnInfo(
                name=name,
                data_type=data_type,
                is_nullable=not not_null,
                default_value=default_value,
                character_maximum_length=None,
                numeric_precision=None,
                numeric_scale=None,
                column_key='PRI' if pk else '',
                extra='',
                comment='',
                ordinal_position=cid
            ))
            
            if pk:
                primary_keys.append(name)
        
        # 获取索引信息
        cursor.execute(f"PRAGMA index_list({table_name})")
        index_list = cursor.fetchall()
        
        indexes = []
        for index_row in index_list:
            seq, name, unique, origin, partial = index_row
            cursor.execute(f"PRAGMA index_info({name})")
            index_columns = [col[2] for col in cursor.fetchall()]
            
            indexes.append({
                'name': name,
                'columns': index_columns,
                'unique': bool(unique),
                'type': 'btree'
            })
        
        # 获取外键信息
        cursor.execute(f"PRAGMA foreign_key_list({table_name})")
        fk_rows = cursor.fetchall()
        
        foreign_keys = []
        for row in fk_rows:
            id, seq, table, from_col, to_col, on_update, on_delete, match = row
            foreign_keys.append({
                'name': f'fk_{table_name}_{from_col}',
                'column': from_col,
                'referenced_table': table,
                'referenced_column': to_col
            })
        
        cursor.close()
        
        return TableInfo(
            name=table_name,
            columns=columns,
            primary_keys=primary_keys,
            indexes=indexes,
            foreign_keys=foreign_keys,
            comment=''
        )


class DatabaseSchemaComparator:
    """数据库表结构比较器"""
    
    def __init__(self, config_file: str):
        """初始化比较器"""
        with open(config_file, 'r', encoding='utf-8') as f:
            self.config = json.load(f)
        
        self.template_db = self.config['template_database']
        self.target_databases = self.config['target_databases']
        self.tables_to_compare = self.config['tables_to_compare']
        
        # 设置日志
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('schema_comparison.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
    
    def create_connector(self, db_config: Dict[str, Any]) -> DatabaseConnector:
        """创建数据库连接器"""
        db_type = db_config['type'].lower()
        
        if db_type == 'mysql':
            return MySQLConnector(db_config)
        elif db_type == 'postgresql':
            return PostgreSQLConnector(db_config)
        elif db_type == 'sqlite':
            return SQLiteConnector(db_config)
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")
    
    def compare_columns(self, template_columns: List[ColumnInfo], target_columns: List[ColumnInfo]) -> Dict[str, Any]:
        """比较列结构"""
        template_col_dict = {col.name: col for col in template_columns}
        target_col_dict = {col.name: col for col in target_columns}
        
        differences = {
            'missing_columns': [],
            'extra_columns': [],
            'modified_columns': []
        }
        
        # 检查缺失的列，按位置排序
        missing_cols = []
        for col_name in template_col_dict:
            if col_name not in target_col_dict:
                missing_cols.append(template_col_dict[col_name])
        
        # 按ordinal_position排序
        missing_cols.sort(key=lambda x: x.ordinal_position)
        differences['missing_columns'] = missing_cols
        
        # 检查多余的列
        for col_name in target_col_dict:
            if col_name not in template_col_dict:
                differences['extra_columns'].append(target_col_dict[col_name])
        
        # 检查修改的列
        for col_name in template_col_dict:
            if col_name in target_col_dict:
                template_col = template_col_dict[col_name]
                target_col = target_col_dict[col_name]
                
                if (template_col.data_type != target_col.data_type or
                    template_col.is_nullable != target_col.is_nullable or
                    template_col.default_value != target_col.default_value or
                    template_col.character_maximum_length != target_col.character_maximum_length):
                    
                    differences['modified_columns'].append({
                        'name': col_name,
                        'template': template_col,
                        'target': target_col
                    })
        
        return differences
    
    def generate_mysql_alter_statements(self, table_name: str, differences: Dict[str, Any], template_columns: List[ColumnInfo], target_columns: List[ColumnInfo]) -> List[str]:
        """生成MySQL ALTER语句"""
        statements = []
        
        # 创建目标表列名集合，用于快速查找
        target_col_names = {col.name for col in target_columns}
        
        # 添加缺失的列，按位置顺序
        for col in differences['missing_columns']:
            null_clause = "NOT NULL" if not col.is_nullable else "NULL"
            default_clause = f"DEFAULT '{col.default_value}'" if col.default_value else ""
            length_clause = f"({col.character_maximum_length})" if col.character_maximum_length else ""
            comment_clause = f"COMMENT '{col.comment}'" if col.comment else ""
            
            # 找到应该插入的位置（在哪个字段之后）
            after_clause = ""
            current_pos = col.ordinal_position
            
            # 查找在当前字段之前且目标表中存在的字段
            for template_col in template_columns:
                if template_col.ordinal_position < current_pos and template_col.name in target_col_names:
                    after_clause = f"AFTER `{template_col.name}`"
            
            stmt = f"ALTER TABLE `{table_name}` ADD COLUMN `{col.name}` {col.data_type}{length_clause} {null_clause} {default_clause} {comment_clause} {after_clause};"
            statements.append(stmt.strip())
        
        # 修改列
        for mod_col in differences['modified_columns']:
            col = mod_col['template']
            null_clause = "NOT NULL" if not col.is_nullable else "NULL"
            default_clause = f"DEFAULT '{col.default_value}'" if col.default_value else ""
            length_clause = f"({col.character_maximum_length})" if col.character_maximum_length else ""
            comment_clause = f"COMMENT '{col.comment}'" if col.comment else ""
            
            stmt = f"ALTER TABLE `{table_name}` MODIFY COLUMN `{col.name}` {col.data_type}{length_clause} {null_clause} {default_clause} {comment_clause};"
            statements.append(stmt.strip())
        
        # 删除多余的列（可选，需要谨慎）
        for col in differences['extra_columns']:
            stmt = f"-- ALTER TABLE `{table_name}` DROP COLUMN `{col.name}`; -- 谨慎删除"
            statements.append(stmt)
        
        return statements
    
    def generate_postgresql_alter_statements(self, table_name: str, differences: Dict[str, Any], template_columns: List[ColumnInfo], target_columns: List[ColumnInfo]) -> List[str]:
        """生成PostgreSQL ALTER语句"""
        statements = []
        
        # 创建目标表列名集合，用于快速查找
        target_col_names = {col.name for col in target_columns}
        
        # 添加缺失的列，按位置顺序
        for col in differences['missing_columns']:
            null_clause = "NOT NULL" if not col.is_nullable else ""
            default_clause = f"DEFAULT '{col.default_value}'" if col.default_value else ""
            
            stmt = f'ALTER TABLE "{table_name}" ADD COLUMN "{col.name}" {col.data_type} {default_clause} {null_clause};'
            statements.append(stmt.strip())
            
            if col.comment:
                comment_stmt = f'COMMENT ON COLUMN "{table_name}"."{col.name}" IS \'{col.comment}\';'
                statements.append(comment_stmt)
        
        # 修改列
        for mod_col in differences['modified_columns']:
            col = mod_col['template']
            
            # 修改数据类型
            stmt = f'ALTER TABLE "{table_name}" ALTER COLUMN "{col.name}" TYPE {col.data_type};'
            statements.append(stmt)
            
            # 修改NULL约束
            if col.is_nullable:
                stmt = f'ALTER TABLE "{table_name}" ALTER COLUMN "{col.name}" DROP NOT NULL;'
            else:
                stmt = f'ALTER TABLE "{table_name}" ALTER COLUMN "{col.name}" SET NOT NULL;'
            statements.append(stmt)
            
            # 修改默认值
            if col.default_value:
                stmt = f'ALTER TABLE "{table_name}" ALTER COLUMN "{col.name}" SET DEFAULT \'{col.default_value}\';'
            else:
                stmt = f'ALTER TABLE "{table_name}" ALTER COLUMN "{col.name}" DROP DEFAULT;'
            statements.append(stmt)
        
        # 删除多余的列（可选，需要谨慎）
        for col in differences['extra_columns']:
            stmt = f'-- ALTER TABLE "{table_name}" DROP COLUMN "{col.name}"; -- 谨慎删除'
            statements.append(stmt)
        
        return statements
    
    def generate_sqlite_alter_statements(self, table_name: str, differences: Dict[str, Any], template_columns: List[ColumnInfo], target_columns: List[ColumnInfo]) -> List[str]:
        """生成SQLite ALTER语句"""
        statements = []
        
        # SQLite的ALTER TABLE功能有限，主要支持添加列
        for col in differences['missing_columns']:
            default_clause = f"DEFAULT '{col.default_value}'" if col.default_value else ""
            stmt = f'ALTER TABLE "{table_name}" ADD COLUMN "{col.name}" {col.data_type} {default_clause};'
            statements.append(stmt.strip())
        
        # SQLite不支持直接修改列，需要重建表
        if differences['modified_columns'] or differences['extra_columns']:
            statements.append(f"-- SQLite不支持直接修改或删除列，需要重建表 {table_name}")
            statements.append("-- 请手动执行以下步骤：")
            statements.append("-- 1. 创建新表结构")
            statements.append("-- 2. 复制数据到新表")
            statements.append("-- 3. 删除旧表")
            statements.append("-- 4. 重命名新表")
        
        return statements
    
    def generate_mysql_create_table(self, table_name: str, template_table: TableInfo) -> List[str]:
        """生成MySQL CREATE TABLE语句"""
        statements = []
        
        # 开始CREATE TABLE语句
        create_sql = f"CREATE TABLE `{table_name}` (\n"
        
        # 添加列定义
        column_definitions = []
        for col in template_table.columns:
            col_def = f"  `{col.name}` {col.data_type}"
            
            # 添加长度限制
            if col.character_maximum_length:
                col_def += f"({col.character_maximum_length})"
            elif col.numeric_precision and col.numeric_scale:
                col_def += f"({col.numeric_precision},{col.numeric_scale})"
            elif col.numeric_precision:
                col_def += f"({col.numeric_precision})"
            
            # 添加NULL约束
            if not col.is_nullable:
                col_def += " NOT NULL"
            
            # 添加默认值
            if col.default_value:
                col_def += f" DEFAULT '{col.default_value}'"
            
            # 添加AUTO_INCREMENT
            if col.extra and 'auto_increment' in col.extra.lower():
                col_def += " AUTO_INCREMENT"
            
            # 添加注释
            if col.comment:
                col_def += f" COMMENT '{col.comment}'"
            
            column_definitions.append(col_def)
        
        create_sql += ",\n".join(column_definitions)
        
        # 添加主键
        if template_table.primary_keys:
            pk_columns = ", ".join([f"`{pk}`" for pk in template_table.primary_keys])
            create_sql += f",\n  PRIMARY KEY ({pk_columns})"
        
        # 添加索引
        for index in template_table.indexes:
            if index['name'] != 'PRIMARY':  # 跳过主键
                index_type = "UNIQUE" if index['unique'] else "INDEX"
                index_columns = ", ".join([f"`{col}`" for col in index['columns']])
                create_sql += f",\n  {index_type} `{index['name']}` ({index_columns})"
        
        # 添加外键
        for fk in template_table.foreign_keys:
            create_sql += f",\n  CONSTRAINT `{fk['name']}` FOREIGN KEY (`{fk['column']}`) REFERENCES `{fk['referenced_table']}` (`{fk['referenced_column']}`)"
        
        create_sql += "\n)"
        
        # 添加表注释
        if template_table.comment:
            create_sql += f" COMMENT='{template_table.comment}'"
        
        # 添加存储引擎和字符集
        create_sql += " ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;"
        
        statements.append(create_sql)
        return statements
    
    def generate_postgresql_create_table(self, table_name: str, template_table: TableInfo) -> List[str]:
        """生成PostgreSQL CREATE TABLE语句"""
        statements = []
        
        # 开始CREATE TABLE语句
        create_sql = f'CREATE TABLE "{table_name}" (\n'
        
        # 添加列定义
        column_definitions = []
        for col in template_table.columns:
            col_def = f'  "{col.name}" {col.data_type}'
            
            # 添加长度限制
            if col.character_maximum_length:
                col_def += f"({col.character_maximum_length})"
            elif col.numeric_precision and col.numeric_scale:
                col_def += f"({col.numeric_precision},{col.numeric_scale})"
            elif col.numeric_precision:
                col_def += f"({col.numeric_precision})"
            
            # 添加NULL约束
            if not col.is_nullable:
                col_def += " NOT NULL"
            
            # 添加默认值
            if col.default_value:
                col_def += f" DEFAULT '{col.default_value}'"
            
            column_definitions.append(col_def)
        
        create_sql += ",\n".join(column_definitions)
        create_sql += "\n);"
        
        statements.append(create_sql)
        
        # 添加主键
        if template_table.primary_keys:
            pk_columns = ", ".join([f'"{pk}"' for pk in template_table.primary_keys])
            pk_sql = f'ALTER TABLE "{table_name}" ADD CONSTRAINT "{table_name}_pkey" PRIMARY KEY ({pk_columns});'
            statements.append(pk_sql)
        
        # 添加索引
        for index in template_table.indexes:
            if index['name'] != 'PRIMARY':
                index_type = "UNIQUE" if index['unique'] else "INDEX"
                index_columns = ", ".join([f'"{col}"' for col in index['columns']])
                index_sql = f'CREATE {index_type} "{index["name"]}" ON "{table_name}" ({index_columns});'
                statements.append(index_sql)
        
        # 添加外键
        for fk in template_table.foreign_keys:
            fk_sql = f'ALTER TABLE "{table_name}" ADD CONSTRAINT "{fk["name"]}" FOREIGN KEY ("{fk["column"]}") REFERENCES "{fk["referenced_table"]}" ("{fk["referenced_column"]}");'
            statements.append(fk_sql)
        
        # 添加表注释
        if template_table.comment:
            comment_sql = f'COMMENT ON TABLE "{table_name}" IS \'{template_table.comment}\';'
            statements.append(comment_sql)
        
        # 添加列注释
        for col in template_table.columns:
            if col.comment:
                comment_sql = f'COMMENT ON COLUMN "{table_name}"."{col.name}" IS \'{col.comment}\';'
                statements.append(comment_sql)
        
        return statements
    
    def generate_sqlite_create_table(self, table_name: str, template_table: TableInfo) -> List[str]:
        """生成SQLite CREATE TABLE语句"""
        statements = []
        
        # 开始CREATE TABLE语句
        create_sql = f'CREATE TABLE "{table_name}" (\n'
        
        # 添加列定义
        column_definitions = []
        for col in template_table.columns:
            col_def = f'  "{col.name}" {col.data_type}'
            
            # 添加NULL约束
            if not col.is_nullable:
                col_def += " NOT NULL"
            
            # 添加默认值
            if col.default_value:
                col_def += f" DEFAULT '{col.default_value}'"
            
            # 添加主键约束
            if col.column_key == 'PRI':
                col_def += " PRIMARY KEY"
            
            column_definitions.append(col_def)
        
        create_sql += ",\n".join(column_definitions)
        create_sql += "\n);"
        
        statements.append(create_sql)
        
        # 添加索引
        for index in template_table.indexes:
            if index['name'] != 'PRIMARY':
                index_type = "UNIQUE" if index['unique'] else "INDEX"
                index_columns = ", ".join([f'"{col}"' for col in index['columns']])
                index_sql = f'CREATE {index_type} "{index["name"]}" ON "{table_name}" ({index_columns});'
                statements.append(index_sql)
        
        return statements
    
    def generate_rename_table_statements(self, table_name: str, db_type: str) -> List[str]:
        """生成重命名表语句"""
        statements = []
        new_name = f"{table_name}_del"
        
        if db_type == 'mysql':
            statements.append(f"RENAME TABLE `{table_name}` TO `{new_name}`;")
        elif db_type == 'postgresql':
            statements.append(f'ALTER TABLE "{table_name}" RENAME TO "{new_name}";')
        elif db_type == 'sqlite':
            statements.append(f'ALTER TABLE "{table_name}" RENAME TO "{new_name}";')
        
        return statements
    
    def compare_and_generate_sql(self) -> Dict[str, Any]:
        """比较数据库并生成SQL语句"""
        results = {}
        
        # 连接模板数据库
        template_connector = self.create_connector(self.template_db)
        template_connector.connect()
        
        try:
            # 检查是否使用通配符对比所有表
            tables_to_compare = self.tables_to_compare
            if tables_to_compare == "*" or (isinstance(tables_to_compare, list) and len(tables_to_compare) == 1 and tables_to_compare[0] == "*"):
                tables_to_compare = template_connector.get_all_tables()
                logging.info(f"检测到通配符，将对比所有表，共 {len(tables_to_compare)} 个表")
                logging.info(f"表列表: {', '.join(tables_to_compare)}")
            
            # 获取模板表结构
            template_tables = {}
            for table_name in tables_to_compare:
                try:
                    template_tables[table_name] = template_connector.get_table_info(table_name)
                    logging.info(f"已获取模板表结构: {table_name}")
                except Exception as e:
                    logging.error(f"获取模板表 {table_name} 结构失败: {e}")
                    continue
            
            # 比较每个目标数据库
            for db_name, db_config in self.target_databases.items():
                logging.info(f"开始比较数据库: {db_name}")
                results[db_name] = {}
                
                target_connector = self.create_connector(db_config)
                target_connector.connect()
                
                try:
                    # 获取目标数据库的所有表
                    target_tables = target_connector.get_all_tables()
                    logging.info(f"目标数据库 {db_name} 共有 {len(target_tables)} 个表")
                    
                    # 检查表存在性
                    missing_tables = []  # 模板库有但目标库没有的表
                    extra_tables = []    # 目标库有但模板库没有的表
                    common_tables = []   # 两个库都有的表
                    
                    for table_name in tables_to_compare:
                        if table_name in target_tables:
                            common_tables.append(table_name)
                        else:
                            missing_tables.append(table_name)
                    
                    for table_name in target_tables:
                        if table_name not in tables_to_compare:
                            extra_tables.append(table_name)
                    
                    logging.info(f"缺失表: {missing_tables}")
                    logging.info(f"多余表: {extra_tables}")
                    logging.info(f"共同表: {len(common_tables)} 个")
                    
                    # 处理缺失的表（生成CREATE TABLE语句）
                    for table_name in missing_tables:
                        if table_name in template_tables:
                            template_table = template_tables[table_name]
                            db_type = db_config['type'].lower()
                            
                            if db_type == 'mysql':
                                create_statements = self.generate_mysql_create_table(table_name, template_table)
                            elif db_type == 'postgresql':
                                create_statements = self.generate_postgresql_create_table(table_name, template_table)
                            elif db_type == 'sqlite':
                                create_statements = self.generate_sqlite_create_table(table_name, template_table)
                            else:
                                create_statements = []
                            
                            results[db_name][table_name] = {
                                'action': 'create_table',
                                'create_statements': create_statements,
                                'template_table': template_table
                            }
                            logging.info(f"生成表 {table_name} 的CREATE语句")
                    
                    # 处理多余的表（生成RENAME TABLE语句）
                    for table_name in extra_tables:
                        db_type = db_config['type'].lower()
                        rename_statements = self.generate_rename_table_statements(table_name, db_type)
                        
                        results[db_name][table_name] = {
                            'action': 'rename_table',
                            'rename_statements': rename_statements
                        }
                        logging.info(f"生成表 {table_name} 的RENAME语句")
                    
                    # 处理共同存在的表（原有的列比较逻辑）
                    for table_name in common_tables:
                        if table_name not in template_tables:
                            continue
                            
                        try:
                            target_table = target_connector.get_table_info(table_name)
                            template_table = template_tables[table_name]
                            
                            # 比较列结构
                            column_differences = self.compare_columns(
                                template_table.columns, 
                                target_table.columns
                            )
                            
                            # 生成ALTER语句
                            db_type = db_config['type'].lower()
                            if db_type == 'mysql':
                                alter_statements = self.generate_mysql_alter_statements(
                                    table_name, column_differences, template_table.columns, target_table.columns
                                )
                            elif db_type == 'postgresql':
                                alter_statements = self.generate_postgresql_alter_statements(
                                    table_name, column_differences, template_table.columns, target_table.columns
                                )
                            elif db_type == 'sqlite':
                                alter_statements = self.generate_sqlite_alter_statements(
                                    table_name, column_differences, template_table.columns, target_table.columns
                                )
                            else:
                                alter_statements = []
                            
                            results[db_name][table_name] = {
                                'action': 'alter_table',
                                'differences': column_differences,
                                'alter_statements': alter_statements,
                                'has_differences': bool(
                                    column_differences['missing_columns'] or
                                    column_differences['extra_columns'] or
                                    column_differences['modified_columns']
                                )
                            }
                            
                            if results[db_name][table_name]['has_differences']:
                                logging.info(f"发现表 {table_name} 在数据库 {db_name} 中存在差异")
                            else:
                                logging.info(f"表 {table_name} 在数据库 {db_name} 中结构一致")
                                
                        except Exception as e:
                            logging.error(f"比较表 {table_name} 失败: {e}")
                            results[db_name][table_name] = {
                                'action': 'error',
                                'error': str(e)
                            }
                            
                finally:
                    target_connector.disconnect()
                    
        finally:
            template_connector.disconnect()
        
        return results
    
    def save_results(self, results: Dict[str, Any], output_dir: str = "output"):
        """保存比较结果"""
        import os
        
        # 创建输出目录
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存详细结果到JSON文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = os.path.join(output_dir, f"schema_comparison_{timestamp}.json")
        
        # 转换结果为可序列化的格式
        serializable_results = {}
        for db_name, db_results in results.items():
            serializable_results[db_name] = {}
            for table_name, table_result in db_results.items():
                if table_result.get('action') == 'error':
                    serializable_results[db_name][table_name] = table_result
                elif table_result.get('action') == 'create_table':
                    serializable_results[db_name][table_name] = {
                        'action': 'create_table',
                        'create_statements': table_result['create_statements'],
                        'template_table': {
                            'name': table_result['template_table'].name,
                            'columns': [asdict(col) for col in table_result['template_table'].columns],
                            'primary_keys': table_result['template_table'].primary_keys,
                            'indexes': table_result['template_table'].indexes,
                            'foreign_keys': table_result['template_table'].foreign_keys,
                            'comment': table_result['template_table'].comment
                        }
                    }
                elif table_result.get('action') == 'rename_table':
                    serializable_results[db_name][table_name] = {
                        'action': 'rename_table',
                        'rename_statements': table_result['rename_statements']
                    }
                elif table_result.get('action') == 'alter_table':
                    serializable_results[db_name][table_name] = {
                        'action': 'alter_table',
                        'has_differences': table_result['has_differences'],
                        'alter_statements': table_result['alter_statements'],
                        'differences': {
                            'missing_columns': [asdict(col) for col in table_result['differences']['missing_columns']],
                            'extra_columns': [asdict(col) for col in table_result['differences']['extra_columns']],
                            'modified_columns': [
                                {
                                    'name': mod['name'],
                                    'template': asdict(mod['template']),
                                    'target': asdict(mod['target'])
                                } for mod in table_result['differences']['modified_columns']
                            ]
                        }
                    }
                else:
                    serializable_results[db_name][table_name] = table_result
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(serializable_results, f, ensure_ascii=False, indent=2)
        
        logging.info(f"详细结果已保存到: {json_file}")
        
        # 为每个数据库生成SQL文件
        for db_name, db_results in results.items():
            sql_file = os.path.join(output_dir, f"schema_statements_{db_name}_{timestamp}.sql")
            
            with open(sql_file, 'w', encoding='utf-8') as f:
                f.write(f"-- 数据库 {db_name} 的表结构同步语句\n")
                f.write(f"-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"-- 基于模板数据库: {self.template_db['database']}\n\n")
                
                # 分类处理不同类型的操作
                create_tables = []
                alter_tables = []
                rename_tables = []
                error_tables = []
                
                for table_name, table_result in db_results.items():
                    if table_result.get('action') == 'create_table':
                        create_tables.append((table_name, table_result))
                    elif table_result.get('action') == 'alter_table':
                        alter_tables.append((table_name, table_result))
                    elif table_result.get('action') == 'rename_table':
                        rename_tables.append((table_name, table_result))
                    elif table_result.get('action') == 'error':
                        error_tables.append((table_name, table_result))
                
                # 1. 创建缺失的表
                if create_tables:
                    f.write("-- ============================================\n")
                    f.write("-- 1. 创建缺失的表\n")
                    f.write("-- ============================================\n\n")
                    for table_name, table_result in create_tables:
                        f.write(f"-- 创建表 {table_name}\n")
                        for stmt in table_result['create_statements']:
                            f.write(f"{stmt}\n")
                        f.write("\n")
                
                # 2. 修改现有表的结构
                if alter_tables:
                    f.write("-- ============================================\n")
                    f.write("-- 2. 修改现有表的结构\n")
                    f.write("-- ============================================\n\n")
                    for table_name, table_result in alter_tables:
                        if table_result.get('has_differences', False):
                            f.write(f"-- 修改表 {table_name}\n")
                            for stmt in table_result['alter_statements']:
                                f.write(f"{stmt}\n")
                            f.write("\n")
                        else:
                            f.write(f"-- 表 {table_name} 结构一致，无需修改\n\n")
                
                # 3. 重命名多余的表
                if rename_tables:
                    f.write("-- ============================================\n")
                    f.write("-- 3. 重命名多余的表（添加_del后缀）\n")
                    f.write("-- ============================================\n\n")
                    for table_name, table_result in rename_tables:
                        f.write(f"-- 重命名表 {table_name} -> {table_name}_del\n")
                        for stmt in table_result['rename_statements']:
                            f.write(f"{stmt}\n")
                        f.write("\n")
                
                # 4. 错误信息
                if error_tables:
                    f.write("-- ============================================\n")
                    f.write("-- 4. 处理失败的表\n")
                    f.write("-- ============================================\n\n")
                    for table_name, table_result in error_tables:
                        f.write(f"-- 表 {table_name} 处理失败: {table_result['error']}\n\n")
            
            logging.info(f"数据库 {db_name} 的SQL语句已保存到: {sql_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='数据库表结构比较工具')
    parser.add_argument('config', help='配置文件路径')
    parser.add_argument('-o', '--output', default='output', help='输出目录 (默认: output)')
    
    args = parser.parse_args()
    
    try:
        # 创建比较器
        comparator = DatabaseSchemaComparator(args.config)
        
        # 执行比较
        logging.info("开始数据库表结构比较...")
        results = comparator.compare_and_generate_sql()
        
        # 保存结果
        comparator.save_results(results, args.output)
        
        # 输出摘要
        print("\n=== 比较结果摘要 ===")
        for db_name, db_results in results.items():
            print(f"\n数据库: {db_name}")
            
            # 统计各种操作
            create_count = 0
            alter_count = 0
            rename_count = 0
            error_count = 0
            consistent_count = 0
            
            for table_name, table_result in db_results.items():
                action = table_result.get('action', 'unknown')
                if action == 'create_table':
                    create_count += 1
                    print(f"  表 {table_name}: 需要创建")
                elif action == 'alter_table':
                    if table_result.get('has_differences', False):
                        alter_count += 1
                        print(f"  表 {table_name}: 存在差异，需要修改")
                    else:
                        consistent_count += 1
                        print(f"  表 {table_name}: 结构一致")
                elif action == 'rename_table':
                    rename_count += 1
                    print(f"  表 {table_name}: 需要重命名为 {table_name}_del")
                elif action == 'error':
                    error_count += 1
                    print(f"  表 {table_name}: 错误 - {table_result['error']}")
            
            # 输出统计信息
            print(f"\n  统计信息:")
            print(f"    需要创建的表: {create_count}")
            print(f"    需要修改的表: {alter_count}")
            print(f"    需要重命名的表: {rename_count}")
            print(f"    结构一致的表: {consistent_count}")
            if error_count > 0:
                print(f"    处理失败的表: {error_count}")
        
        logging.info("数据库表结构比较完成！")
        
    except Exception as e:
        logging.error(f"程序执行失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()