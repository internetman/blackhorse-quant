# 黑马自选 FastAPI 后端（v1.2）

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

## API 接口（v1.2）

除 `POST /api/auth/login/` 外，其它业务接口均需 `Authorization: Bearer <token>`。

### 认证
- `POST /api/auth/login/` - 登录并返回 token
- `GET /api/auth/me/` - 当前用户信息
- `POST /api/auth/logout/` - 退出登录

### 我的关注
- `GET /api/watchlist/` - 获取当前用户关注列表
- `POST /api/watchlist/` - 添加关注
- `DELETE /api/watchlist/{symbol}` - 取消关注
- `GET /api/stocks/search?q=xxx&limit=20` - 股票联想搜索（代码/名称/首字母/拼音）

### 首页数据
- `GET /api/recommendations/` - 首页聚合（建议 + 行情 + 新闻）
- `GET /api/quote/?symbol=600519.SH` - 单股行情（支持 `600519` 自动归一化）
- `GET /api/news/?symbol=600519.SH&limit=10` - 单股新闻

### 复盘
- `GET /api/reviews/` - 复盘记录
- `GET /api/reviews/stats/` - 复盘统计

### 用户管理（管理员）
- `GET /api/admin/members/` - 成员列表
- `POST /api/admin/users/` - 添加用户
- `PATCH /api/admin/members/{user_id}` - 变更角色

### 废弃接口
- `/api/positions/*` - v1.2 已废弃，统一返回 `410 Gone`
