# FastAPI 后端设置指南

## 📁 项目结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── models.py            # Pydantic 数据模型
│   ├── mock_data.py         # Mock 数据
│   ├── store.py             # 内存存储（模拟数据库）
│   ├── engine.py            # 后端引擎（模拟数据更新）
│   └── api/
│       ├── __init__.py
│       ├── positions.py     # 持仓相关接口
│       ├── trades.py        # 交易记录接口
│       ├── status.py        # 系统状态接口
│       ├── stats.py         # 统计数据接口
│       └── config.py        # 配置参数接口
├── requirements.txt         # Python 依赖
├── run.sh                   # 启动脚本
└── README.md
```

## 🚀 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动服务

```bash
# 方式一：使用启动脚本
./run.sh

# 方式二：直接使用 uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 方式三：Python 模块方式
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 验证服务

- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health
- 根路径：http://localhost:8000/

## 📡 API 接口

### 持仓相关
- `GET /api/positions` - 获取持仓列表
- `GET /api/positions/{id}` - 获取单个持仓
- `PUT /api/positions/{id}` - 更新持仓
- `DELETE /api/positions` - 清空所有持仓（强平）

### 交易记录
- `GET /api/trades?limit=100` - 获取交易记录列表
- `GET /api/trades/{id}` - 获取单个交易记录
- `POST /api/trades` - 创建新交易记录

### 系统状态
- `GET /api/status` - 获取系统状态
- `POST /api/status` - 设置系统状态（body: `{"status": "running"|"paused"|"kill"}`）

### 统计数据
- `GET /api/stats` - 获取统计数据（实时计算）

### 配置参数
- `GET /api/config` - 获取配置参数
- `PUT /api/config` - 更新配置参数
- `PATCH /api/config` - 部分更新配置参数

## 🔄 后端引擎

后端引擎在服务启动时自动运行：
- **每秒**：更新所有持仓的价格和盈亏
- **每5秒**：生成一条新交易记录（仅在 running 状态）
- **kill 状态**：自动强平所有持仓

## 🔗 前端连接

前端已配置为连接 `http://localhost:8000`，可通过环境变量修改：

```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## 📊 数据结构

所有接口返回的数据结构严格对齐前端 TypeScript 类型：

- `Position`: 持仓数据
- `Trade`: 交易记录
- `SysStatus`: 系统状态
- `Stats`: 统计数据
- `ConfigParams`: 配置参数

## 🐛 故障排查

### 端口被占用
```bash
# 修改端口
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

### CORS 错误
检查 `main.py` 中的 `allow_origins` 配置，确保包含前端地址。

### 引擎未运行
检查控制台是否有 "✅ 引擎已启动" 消息。
