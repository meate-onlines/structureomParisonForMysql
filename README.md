# 数据库表结构比较工具

这是一个用于比较多个数据库中相同表结构的Python工具。它可以指定一个模板数据库，并基于该模板自动生成其他数据库的表修改语句。

## 功能特性

- 🔍 **多数据库支持**: 支持MySQL、PostgreSQL和SQLite数据库
- 📊 **结构比较**: 详细比较表的列结构、数据类型、约束等
- 🛠️ **自动生成SQL**: 基于模板数据库自动生成ALTER语句
- 📝 **详细报告**: 生成JSON格式的详细比较报告
- 🚀 **批量处理**: 支持同时比较多个表和多个数据库
- 📋 **日志记录**: 完整的操作日志记录
- 🆕 **表存在性检查**: 自动检测缺失和多余的表
- 🏗️ **建表语句生成**: 为缺失的表生成完整的CREATE TABLE语句
- 🔄 **表重命名**: 为多余的表生成重命名语句（添加_del后缀）

## 支持的数据库类型

| 数据库类型 | 版本要求 | 连接器 |
|-----------|---------|--------|
| MySQL | 5.7+ | mysql-connector-python |
| PostgreSQL | 9.6+ | psycopg2 |
| SQLite | 3.0+ | sqlite3 (内置) |

## 安装方法

### 方法一：使用安装脚本（推荐）

**Linux/macOS:**
```bash
# 克隆或下载项目文件
# 运行安装脚本
./install.sh
```

**Windows:**
```cmd
# 克隆或下载项目文件
# 运行安装脚本
install.bat
```

### 方法二：手动安装

**Linux/macOS:**
```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

**Windows:**
```cmd
# 创建虚拟环境
python -m venv venv
venv\Scripts\activate.bat

# 安装依赖（如果requirements.txt安装失败，请分步安装）
pip install mysql-connector-python==8.2.0
pip install psycopg2-binary --only-binary=all
pip install typing-extensions==4.8.0
```

## 配置文件

复制配置模板并修改：

```bash
cp config_template.json my_config.json
```

配置文件结构：

```json
{
  "template_database": {
    "name": "template_db",
    "type": "mysql",
    "host": "localhost",
    "port": 3306,
    "user": "username",
    "password": "password",
    "database": "template_database_name"
  },
  "target_databases": {
    "production_db": {
      "name": "production_db",
      "type": "mysql",
      "host": "prod-server.example.com",
      "port": 3306,
      "user": "prod_user",
      "password": "prod_password",
      "database": "production_database_name"
    },
    "staging_db": {
      "name": "staging_db",
      "type": "postgresql",
      "host": "staging-server.example.com",
      "port": 5432,
      "user": "staging_user",
      "password": "staging_password",
      "database": "staging_database_name"
    }
  },
  "tables_to_compare": [
    "users",
    "products",
    "orders"
  ]
}
```

### 配置说明

- **template_database**: 作为标准的模板数据库配置
- **target_databases**: 需要与模板比较的目标数据库列表
- **tables_to_compare**: 需要比较的表名列表，支持通配符 `"*"` 来比较所有表

## 使用方法

### 基本用法

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行比较
python database_schema_comparator.py config.json
```

### 指定输出目录

```bash
python database_schema_comparator.py config.json -o /path/to/output
```

### 命令行参数

- `config`: 配置文件路径（必需）
- `-o, --output`: 输出目录（可选，默认为'output'）

## 输出文件

工具会在输出目录中生成以下文件：

1. **详细比较报告**: `schema_comparison_YYYYMMDD_HHMMSS.json`
   - 包含所有表的详细比较结果
   - JSON格式，便于程序处理

2. **SQL修改语句**: `alter_statements_[数据库名]_YYYYMMDD_HHMMSS.sql`
   - 每个目标数据库生成一个SQL文件
   - 包含所有需要执行的ALTER语句

3. **操作日志**: `schema_comparison.log`
   - 详细的操作日志
   - 包含错误信息和调试信息

## 比较内容

工具会比较以下表结构元素：

### 列属性
- ✅ 列名
- ✅ 数据类型
- ✅ 是否允许NULL
- ✅ 默认值
- ✅ 字符长度限制
- ✅ 数值精度和小数位数
- ✅ 列注释
- ✅ **字段位置**（新增：新增字段会按照模板库的位置顺序添加）

### 约束和索引
- ✅ 主键
- ✅ 索引
- ✅ 外键
- ✅ 唯一约束

### 表属性
- ✅ 表注释

## 生成的SQL语句类型

### MySQL
```sql
-- 创建表
CREATE TABLE `table_name` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL COMMENT '名称',
  `created_at` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='表注释';

-- 添加列（支持AFTER子句指定位置）
ALTER TABLE `table_name` ADD COLUMN `new_column` VARCHAR(255) NOT NULL DEFAULT 'default_value' COMMENT '列注释' AFTER `existing_column`;

-- 修改列
ALTER TABLE `table_name` MODIFY COLUMN `column_name` INT(11) NOT NULL DEFAULT 0;

-- 重命名表
RENAME TABLE `old_table` TO `old_table_del`;

-- 删除列（注释形式，需手动确认）
-- ALTER TABLE `table_name` DROP COLUMN `old_column`; -- 谨慎删除
```

### PostgreSQL
```sql
-- 创建表
CREATE TABLE "table_name" (
  "id" SERIAL PRIMARY KEY,
  "name" VARCHAR(100) NOT NULL,
  "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 添加列
ALTER TABLE "table_name" ADD COLUMN "new_column" VARCHAR(255) DEFAULT 'default_value' NOT NULL;
COMMENT ON COLUMN "table_name"."new_column" IS '列注释';

-- 修改列类型
ALTER TABLE "table_name" ALTER COLUMN "column_name" TYPE INTEGER;

-- 修改NULL约束
ALTER TABLE "table_name" ALTER COLUMN "column_name" SET NOT NULL;

-- 重命名表
ALTER TABLE "old_table" RENAME TO "old_table_del";
```

### SQLite
```sql
-- 创建表
CREATE TABLE "table_name" (
  "id" INTEGER PRIMARY KEY,
  "name" TEXT NOT NULL,
  "created_at" TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 添加列（SQLite限制较多）
ALTER TABLE "table_name" ADD COLUMN "new_column" TEXT DEFAULT 'default_value';

-- 重命名表
ALTER TABLE "old_table" RENAME TO "old_table_del";

-- 注意：SQLite不支持直接修改或删除列，需要重建表
```

## 使用示例

### 示例1：比较电商系统数据库

```bash
# 1. 准备配置文件
cp example_config.json ecommerce_config.json

# 2. 编辑配置文件，设置正确的数据库连接信息
vim ecommerce_config.json

# 3. 运行比较
python database_schema_comparator.py ecommerce_config.json

# 4. 查看结果
ls output/
# schema_comparison_20231201_143022.json
# alter_statements_production_20231201_143022.sql
# alter_statements_staging_20231201_143022.sql
```

### 示例2：只比较特定表

修改配置文件中的`tables_to_compare`：

```json
{
  "tables_to_compare": [
    "users",
    "orders"
  ]
}
```

### 示例4：表存在性检查

工具会自动检测表的存在性并生成相应的SQL语句：

```bash
# 运行比较
python database_schema_comparator.py config.json

# 输出示例：
# === 比较结果摘要 ===
# 
# 数据库: production
#   表 new_table: 需要创建
#   表 old_table: 需要重命名为 old_table_del
#   表 users: 存在差异，需要修改
#   表 products: 结构一致
# 
#   统计信息:
#     需要创建的表: 1
#     需要修改的表: 1
#     需要重命名的表: 1
#     结构一致的表: 1
```

生成的SQL文件会按操作类型分类：
```sql
-- ============================================
-- 1. 创建缺失的表
-- ============================================

-- 创建表 new_table
CREATE TABLE `new_table` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- ============================================
-- 2. 修改现有表的结构
-- ============================================

-- 修改表 users
ALTER TABLE `users` ADD COLUMN `email` VARCHAR(255) NOT NULL AFTER `username`;

-- ============================================
-- 3. 重命名多余的表（添加_del后缀）
-- ============================================

-- 重命名表 old_table -> old_table_del
RENAME TABLE `old_table` TO `old_table_del`;
```

## 安全注意事项

⚠️ **重要提醒**：

1. **备份数据**: 执行任何ALTER语句前，请先备份目标数据库
2. **测试环境**: 建议先在测试环境中验证生成的SQL语句
3. **权限控制**: 确保数据库用户具有适当的权限
4. **密码安全**: 配置文件包含敏感信息，请妥善保管

## 故障排除

### 常见问题

**Q: Windows上安装psycopg2-binary失败**
```
A: 解决方案：
   - 使用预编译版本: pip install psycopg2-binary --only-binary=all
   - 或者分步安装: pip install mysql-connector-python==8.2.0
   - 然后: pip install psycopg2-binary --only-binary=all
   - 最后: pip install typing-extensions==4.8.0
```

**Q: PowerShell中运行脚本报错**
```
A: PowerShell执行策略问题，解决方法：
   - 临时允许: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   - 或者使用cmd运行: cmd /c install.bat
   - 或者手动激活虚拟环境: venv\Scripts\activate.bat
```

**Q: 连接数据库失败**
```
A: 检查以下项目：
   - 网络连接是否正常
   - 数据库服务是否启动
   - 用户名和密码是否正确
   - 端口号是否正确
   - 防火墙设置
```

**Q: 表不存在错误**
```
A: 确认：
   - 表名拼写是否正确
   - 表是否存在于指定数据库中
   - 用户是否有访问该表的权限
```

**Q: 字符编码问题**
```
A: 确保：
   - 数据库连接使用UTF-8编码
   - 配置文件保存为UTF-8格式
   - 系统环境支持中文字符
```

### 日志分析

查看详细日志：

```bash
tail -f schema_comparison.log
```

日志级别：
- `INFO`: 正常操作信息
- `WARNING`: 警告信息
- `ERROR`: 错误信息

## 开发和扩展

### 添加新的数据库类型

1. 继承`DatabaseConnector`基类
2. 实现`connect()`和`get_table_info()`方法
3. 在`create_connector()`方法中添加新类型的处理

### 自定义比较逻辑

修改`compare_columns()`方法来添加自定义的比较规则。

### 扩展SQL生成

为新的数据库类型添加对应的`generate_*_alter_statements()`方法。

## 版本历史

- **v1.2.0** (2025-10-29)
  - **新增表存在性检查**：自动检测模板库和目标库中表的差异
  - **新增建表语句生成**：为缺失的表生成完整的CREATE TABLE语句
  - **新增表重命名功能**：为多余的表生成重命名语句（添加_del后缀）
  - **改进SQL文件结构**：按操作类型分类生成SQL语句
  - **增强摘要报告**：显示各种操作的统计信息

- **v1.1.0** (2025-10-29)
  - 新增通配符支持：`tables_to_compare` 设置为 `"*"` 时可比较所有表
  - **新增字段位置支持**：新增字段会按照模板库的位置顺序添加，MySQL支持AFTER子句
  - 修复Windows系统安装问题
  - 添加Windows安装脚本 `install.bat`
  - 改进PostgreSQL连接器安装方式
  - 完善故障排除文档

- **v1.0.0** (2023-12-01)
  - 初始版本
  - 支持MySQL、PostgreSQL、SQLite
  - 基本的表结构比较功能
  - 自动生成ALTER语句

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个工具。

## 联系方式

如有问题或建议，请通过以下方式联系：

- 提交Issue: [项目地址]
- 邮箱: [联系邮箱]

---

**免责声明**: 本工具生成的SQL语句可能会修改数据库结构，使用前请务必备份数据并在测试环境中验证。