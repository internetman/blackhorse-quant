# FastAPI 后端集成完成总结

## ✅ 已完成的工作

### 1. FastAPI 后端创建
- ✅ 创建完整的 FastAPI 项目结构
- ✅ 设计 API 接口（严格对齐前端数据结构）
- ✅ 实现 Mock 数据存储
- ✅ 配置 CORS 支持前端跨域访问
- ✅ 创建后端引擎（模拟数据实时更新）

### 2. 前端集成
- ✅ 创建 API 客户端 (`lib/api.ts`)
- ✅ 更新 Store 使用 API 而不是本地数据
- ✅ 更新所有组件从 API 获取数据
- ✅ 添加自动刷新机制

## 📁 文件结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用 + 引擎启动
│   ├── models.py            # Pydantic 数据模型
│   ├── mock_data.py         # 初始 Mock 数据
│   ├── store.py             # 内存存储（单例）
│   ├── engine.py            # 后端引擎（后台任务）
│   └── api/
│       ├── positions.py     # 持仓接口
│       ├── trades.py        # 交易记录接口
│       ├── status.py        # 系统状态接口
│       ├── stats.py         # 统计数据接口
│       └── config.py         # 配置参数接口
├── requirements.txt
├── run.sh
└── README.md

前端更新：
├── lib/
│   ├── api.ts              # API 客户端（新增）
│   └── store.ts            # 更新为使用 API
└── components/
    └── ...                  # 更新为从 API 获取数据
```

## 🚀 启动步骤

### 1. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 启动 FastAPI 服务

```bash
# 方式一：使用脚本
./run.sh

# 方式二：直接命令
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3. 启动前端（新终端）

```bash
npm run dev
```

## 📡 API 接口列表

### 持仓
- `GET /api/positions` - 获取持仓列表
- `PUT /api/positions/{id}` - 更新持仓
- `DELETE /api/positions` - 清空持仓

### 交易
- `GET /api/trades?limit=100` - 获取交易记录
- `POST /api/trades` - 创建交易记录

### 状态
- `GET /api/status` - 获取系统状态
- `POST /api/status` - 设置系统状态

### 统计
- `GET /api/stats` - 获取统计数据（实时计算）

### 配置
- `GET /api/config` - 获取配置
- `PATCH /api/config` - 更新配置

## 🔄 数据流

1. **后端引擎**（每秒运行）：
   - 更新持仓价格（±1% 随机波动）
   - 计算盈亏
   - 每5秒生成新交易（running 状态）

2. **前端轮询**：
   - Dashboard：每2秒刷新持仓和统计
   - Trades：每3秒刷新交易记录

3. **状态同步**：
   - 前端设置状态 → POST /api/status
   - 后端引擎响应状态变化

## 🎯 测试验证

### 1. 检查后端服务
```bash
curl http://localhost:8000/health
# 应该返回: {"status":"healthy"}

curl http://localhost:8000/api/positions
# 应该返回持仓列表
```

### 2. 检查前端连接
- 打开 http://localhost:3000/dashboard
- 查看浏览器 Network 标签
- 应该看到对 `/api/positions` 和 `/api/stats` 的请求

### 3. 测试实时更新
- 观察持仓价格是否每秒更新
- 观察交易记录是否每5秒新增（running 状态）
- 切换状态（running/paused/kill）测试

## ⚙️ 配置

### 修改 API 地址

前端环境变量（`.env.local`）：
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### 修改后端端口

修改 `run.sh` 或启动命令：
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

## 📝 注意事项

1. **数据持久化**：当前使用内存存储，重启服务会重置数据
2. **引擎线程**：后端引擎在独立线程运行，不影响 API 响应
3. **CORS 配置**：已配置允许 localhost:3000 访问
4. **数据格式**：所有接口严格对齐前端 TypeScript 类型

## 🔧 故障排查

### 后端无法启动
- 检查 Python 版本（需要 3.8+）
- 检查依赖是否安装：`pip list | grep fastapi`
- 检查端口是否被占用：`lsof -i :8000`

### 前端无法连接
- 检查后端是否运行：`curl http://localhost:8000/health`
- 检查 CORS 配置
- 查看浏览器控制台错误

### 数据不更新
- 检查后端控制台是否有 "✅ 引擎已启动"
- 检查前端 Network 标签是否有请求
- 检查浏览器控制台是否有错误
