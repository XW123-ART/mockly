# SmartDataGen - 接口测试数据生成工具

## 项目简介

SmartDataGen 是一款专注于**接口测试**的智能数据生成工具，基于 LLM 技术自动生成覆盖边界值、异常场景的测试数据，解决手工准备测试数据效率低下、覆盖不全的痛点。

### 核心测试理念

不同于简单的随机数据生成，SmartDataGen 基于测试设计方法论：

- **等价类划分**：自动生成正常数据、边界数据、异常数据三类测试数据
- **边界值分析**：针对数值范围（min/max）、字符串长度等约束，自动生成边界值-1、边界值、边界值+1
- **变异测试**：智能生成类型变异、空值、特殊字符等异常场景
- **覆盖率驱动**：实时评估字段覆盖率、枚举值覆盖率、边界覆盖率

### 解决的测试痛点

| 传统方式 | SmartDataGen |
|---------|-------------|
| 手工编写 100 条测试数据需 2 小时 | 5 分钟自动生成 |
| 容易遗漏边界场景（如 age=999） | 自动识别约束，生成边界值 |
| 枚举值覆盖不全（只测了 2/5 个状态） | 强制覆盖所有枚举值 |
| 异常数据难以构造（特殊字符注入） | LLM 自动生成异常场景 |

## 功能特性

### 🧪 测试数据生成

- **Schema 驱动生成**：输入 JSON Schema，自动生成符合约束的测试数据
- **顺序生成策略**：ID 从 1 递增，枚举值按顺序轮换，确保覆盖完整
- **智能边界生成**：自动识别 minimum/maximum/minLength/maxLength，生成边界值
- **多样化数据**：基于 LLM 生成真实业务数据（姓名、邮箱、地址等）

### 🔀 变异测试支持

自动生成以下异常场景：
- **类型变异**：字符串变数字、布尔值变字符串
- **空值测试**：null、空字符串、缺失字段
- **边界溢出**：最大值+1、最小值-1、超长字符串
- **特殊字符**：emoji、SQL 注入、XSS payload
- **格式错误**：无效邮箱、错误日期格式

### 📊 覆盖率评估

生成详细的覆盖率报告：
- **字段覆盖率**：哪些字段生成了数据
- **枚举值覆盖率**：枚举类型是否全部覆盖
- **边界值覆盖率**：约束边界是否被测试
- **类型覆盖率**：各数据类型是否都被覆盖

### 🔧 测试工具集成

- **JSON 格式**：直接导入 Postman、Apifox 进行接口测试
- **CSV 格式**：JMeter Data Set Config 参数化测试
- **SQL 格式**：初始化数据库测试数据
- **OpenAPI 支持**：上传 Swagger 文档，批量生成所有接口测试数据

## 安装指南

### 环境要求
- Python 3.8+
- DeepSeek API 密钥（或其他 OpenAI 兼容的 LLM）

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置 API 密钥

```bash
# 修改 smartdatagen/llm.py 中的 api_key
api_key="your_api_key_here"
```

## 使用方法

### 1. 基本数据生成

生成符合 Schema 的正常测试数据：

```bash
python main.py --schema examples/user.json --count 5
```

输出示例：
```json
[
  {"id": 1, "name": "张三", "age": 25, "email": "zhangsan@test.com"},
  {"id": 2, "name": "李四", "age": 30, "email": "lisi@test.com"},
  ...
]
```

### 2. 生成变异数据（异常场景测试）

生成边界值和异常数据：

```bash
python main.py --schema examples/user.json --count 5 --mutate
```

输出示例：
```json
[
  {"id": "abc", "name": null, "age": -1},      // 类型错误、空值、边界溢出
  {"id": 1, "name": "<script>alert(1)</script>", "age": 99999},  // XSS 注入、超长数值
  ...
]
```

### 3. JMeter 性能测试集成

生成 CSV 格式数据，用于 JMeter 参数化：

```bash
python main.py --schema examples/user.json --count 1000 --format csv --output users.csv
```

在 JMeter 中使用：
1. 添加 "CSV Data Set Config"
2. 选择生成的 users.csv 文件
3. 在 HTTP 请求中使用 `${id}`, `${name}` 等变量

### 4. Postman 接口测试

生成 JSON 后导入 Postman：

```bash
python main.py --schema examples/login.json --count 10 --output login_data.json
```

配合 Postman Collection Runner 进行批量接口测试。

### 5. OpenAPI 文档批量处理

上传 Swagger/OpenAPI 文档，自动生成所有接口的测试数据：

```bash
python main.py --openapi petstore.yaml --count 3 --output ./test_data/
```

自动为每个接口生成：
- 正常请求数据
- 边界值测试数据
- 异常场景数据

### 6. 生成覆盖率报告

评估测试数据质量：

```bash
python main.py --schema examples/user.json --count 10 --report
```

输出示例：
```
=== 覆盖率报告 ===
字段覆盖: 100% (5/5)
枚举覆盖: 100% (3/3)
边界覆盖: 80% (4/5)
详细信息:
  - id: 已覆盖
  - status: 已覆盖 (active, inactive, pending)
  - age: 边界值未完全覆盖 (缺少 maximum 测试)
```

## 项目结构

```
smartdatagen/
├── __init__.py
├── schema.py         # Schema 解析与约束提取
├── prompt.py         # 测试用例提示词生成（等价类/边界值/变异）
├── llm.py            # LLM 调用
├── generator.py      # 变异算法（类型变异、边界变异、空值变异）
├── openapi_parser.py # OpenAPI 文档解析
├── coverage.py       # 覆盖率统计（字段/枚举/边界）
├── utils.py          # 数据格式转换（JSON/CSV/SQL）
└── examples/         # 测试 Schema 示例
    ├── user.json     # 用户数据 Schema
    └── order.json    # 订单数据 Schema
```

## 技术原理

### 1. 测试设计驱动

不是简单随机生成，而是基于测试设计方法论：

```python
# 对于字段 age: {type: integer, minimum: 18, maximum: 60}
# 自动生成以下测试数据：
- 正常值: 25, 30, 45                    # 等价类内
- 边界值: 18, 19, 59, 60               # 边界值分析
- 异常值: 17, 61, -1, null, "abc"      # 边界溢出、类型错误
```

### 2. 顺序生成策略

确保覆盖完整：
- **ID 顺序递增**：从 1 开始，便于跟踪和复现
- **枚举值轮换**：按顺序遍历所有枚举值，避免遗漏
- **边界值覆盖**：针对每个约束生成边界值测试

### 3. LLM 增强

利用 LLM 的创造性生成真实业务数据：
- 生成真实姓名（不是 user1, user2）
- 生成有效邮箱格式
- 理解业务上下文（如电商订单、用户画像）

## 测试场景示例

### 场景 1：登录接口测试

```bash
python main.py --schema examples/login.json --count 6 --mutate
```

自动生成：
1. 正常数据：正确用户名 + 正确密码
2. 边界值：用户名最小长度、最大长度
3. 空值测试：用户名为空、密码为空
4. 类型错误：用户名传数字、密码传布尔值
5. 特殊字符：SQL 注入尝试 `' OR 1=1 --`
6. 超长字符串：用户名 1000 个字符

### 场景 2：订单状态流转测试

Schema 中 status 字段为枚举类型：`["created", "paid", "shipped", "completed"]`

生成 4 条数据，确保每个状态都被覆盖：
```json
[
  {"order_id": 1, "status": "created"},
  {"order_id": 2, "status": "paid"},
  {"order_id": 3, "status": "shipped"},
  {"order_id": 4, "status": "completed"}
]
```

### 场景 3：压力测试数据准备

生成 10 万条用户数据，导入数据库：

```bash
python main.py --schema examples/user.json --count 100000 --format sql --table users --output users.sql
```

## 扩展建议

- **测试用例模板**：支持导入 CSV 模板，固定某些字段，变化特定字段
- **预期结果映射**：支持定义预期输出，生成完整测试用例（输入+预期）
- **CI/CD 集成**：与 Jenkins/GitHub Actions 集成，自动化生成测试数据
- **可视化界面**：Web 界面配置 Schema、预览数据、导出报告
- **更多变异规则**：添加 SQL 注入、XSS、路径遍历等安全测试变异

## 面试常见问题

**Q: 怎么体现测试思维？**

A: 项目实现了测试设计方法论：
- 等价类划分：正常/边界/异常三类数据分开生成
- 边界值分析：自动识别约束生成边界值
- 变异测试：类型变异、空值、特殊字符注入
- 覆盖率评估：字段/枚举/边界三层覆盖度量

**Q: 和传统数据生成工具的区别？**

A: 传统工具（如 Mock.js）是随机生成，数据质量不可控。本项目：
- 基于 LLM 生成真实业务数据
- 强制覆盖所有枚举值和边界值
- 自动生成异常场景（安全测试）
- 提供覆盖率报告评估数据质量

**Q: 怎么和 JMeter 配合使用？**

A: 生成 CSV 格式 → JMeter CSV Data Set Config 读取 → 参数化 HTTP 请求。适合：
- 数据驱动测试（Data-Driven Testing）
- 压力测试（生成海量真实数据）
- 参数化回归测试

## 许可证

MIT License
