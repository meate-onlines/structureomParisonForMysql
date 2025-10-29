# 数据库表结构比较工具

这是一个用于比较多个数据库中相同表结构的Python工具。它可以指定一个模板数据库，并基于该模板自动生成其他数据库的表修改语句。

## 功能特性

- 🔍 **多数据库支持**: 支持MySQL、PostgreSQL和SQLite数据库
- 📊 **结构比较**: 详细比较表的列结构、数据类型、约束等
- 🛠️ **自动生成SQL**: 基于模板数据库自动生成ALTER语句
- 📝 **详细报告**: 生成JSON格式的详细比较报告
- 🚀 **批量处理**: 支持同时比较多个表和多个数据库
- 📋 **日志记录**: 完整的操作日志记录

## 支持的数据库类型

| 数据库类型 | 版本要求 | 连接器 |
|-----------|---------|--------|
| MySQL | 5.7+ | mysql-connector-python |
| PostgreSQL | 9.6+ | psycopg2 |
| SQLite | 3.0+ | sqlite3 (内置) |

## 安装方法

### 方法一：使用安装脚本（推荐）

```bash
# 克隆或下载项目文件
# 运行安装脚本
./install.sh
```

### 方法二：手动安装

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
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
- **tables_to_compare**: 需要比较的表名列表，支持以下格式：
  - 指定表名列表：`["users", "products", "orders"]`
  - 使用通配符对比所有表：`"*"` 或 `["*"]`

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
-- 添加列
ALTER TABLE `table_name` ADD COLUMN `new_column` VARCHAR(255) NOT NULL DEFAULT 'default_value' COMMENT '列注释';

-- 修改列
ALTER TABLE `table_name` MODIFY COLUMN `column_name` INT(11) NOT NULL DEFAULT 0;

-- 删除列（注释形式，需手动确认）
-- ALTER TABLE `table_name` DROP COLUMN `old_column`; -- 谨慎删除
```

### PostgreSQL
```sql
-- 添加列
ALTER TABLE "table_name" ADD COLUMN "new_column" VARCHAR(255) DEFAULT 'default_value' NOT NULL;
COMMENT ON COLUMN "table_name"."new_column" IS '列注释';

-- 修改列类型
ALTER TABLE "table_name" ALTER COLUMN "column_name" TYPE INTEGER;

-- 修改NULL约束
ALTER TABLE "table_name" ALTER COLUMN "column_name" SET NOT NULL;
```

### SQLite
```sql
-- 添加列（SQLite限制较多）
ALTER TABLE "table_name" ADD COLUMN "new_column" TEXT DEFAULT 'default_value';

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

### 示例3：对比所有表

使用通配符对比模板数据库中的所有表：

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
    }
  },
  "tables_to_compare": "*"
}
```

或者使用数组形式：

```json
{
  "tables_to_compare": ["*"]
}
```

使用通配符时，工具会自动获取模板数据库中的所有表名，并与目标数据库进行对比。这在以下场景特别有用：
- 数据库有大量表需要对比
- 不确定具体有哪些表需要对比
- 想要确保所有表结构都保持一致

## 安全注意事项

⚠️ **重要提醒**：

1. **备份数据**: 执行任何ALTER语句前，请先备份目标数据库
2. **测试环境**: 建议先在测试环境中验证生成的SQL语句
3. **权限控制**: 确保数据库用户具有适当的权限
4. **密码安全**: 配置文件包含敏感信息，请妥善保管

## 故障排除

### 常见问题

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