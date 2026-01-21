# 黑马量化 FastAPI 后端

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

或者使用 Python 直接运行：

```bash
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 接口

### 持仓相关
- `GET /api/positions` - 获取持仓列表
- `GET /api/positions/{id}` - 获取单个持仓
- `PUT /api/positions/{id}` - 更新持仓
- `DELETE /api/positions` - 清空所有持仓

### 交易记录
- `GET /api/trades` - 获取交易记录列表
- `GET /api/trades/{id}` - 获取单个交易记录
- `POST /api/trades` - 创建新交易记录

### 系统状态
- `GET /api/status` - 获取系统状态
- `POST /api/status` - 设置系统状态

### 统计数据
- `GET /api/stats` - 获取统计数据

### 配置参数
- `GET /api/config` - 获取配置参数
- `PUT /api/config` - 更新配置参数
- `PATCH /api/config` - 部分更新配置参数

## 数据结构

所有接口返回的数据结构严格对齐前端 TypeScript 类型定义。
