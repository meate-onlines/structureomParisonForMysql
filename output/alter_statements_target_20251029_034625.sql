-- 数据库 target 的表结构修改语句
-- 生成时间: 2025-10-29 03:46:25
-- 基于模板数据库: ./template.db

-- 表 orders 结构一致，无需修改

-- 表 products 的修改语句
-- SQLite不支持直接修改或删除列，需要重建表 products
-- 请手动执行以下步骤：
-- 1. 创建新表结构
-- 2. 复制数据到新表
-- 3. 删除旧表
-- 4. 重命名新表

-- 表 users 的修改语句
ALTER TABLE "users" ADD COLUMN "updated_at" TIMESTAMP DEFAULT 'CURRENT_TIMESTAMP';
-- SQLite不支持直接修改或删除列，需要重建表 users
-- 请手动执行以下步骤：
-- 1. 创建新表结构
-- 2. 复制数据到新表
-- 3. 删除旧表
-- 4. 重命名新表

