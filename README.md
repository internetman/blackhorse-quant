# 黑马自选

> 私有股票小社群 · AI 辅助每日买卖建议与复盘

一个面向小圈子的自选股决策助手，围绕"圈内关注股票"提供结构化 AI 建议，并自动复盘验证建议效果。

## 核心功能

- **每日建议** — 对圈内自选股逐只输出结构化买卖建议（可交易 / 观望 / 风险升高）
- **圈子选股** — 圈子成员共同维护的关注股票列表，支持意见领袖标记
- **复盘记录** — T+1 / T+3 / T+5 自动追踪建议准确率
- **私有持仓** — 每人独立记录仓位，彼此不可见
- **圈子管理** — 邀请制加入、角色体系（管理员 / 意见领袖 / 成员）

## 技术栈

| 层 | 技术 |
|---|------|
| 前端 | Next.js 16 · React 19 · Tailwind CSS 4 · Zustand |
| 后端 | FastAPI · Pydantic · Python 3.11+ |
| 部署 | Vercel (前端) · Railway (后端) |

## 快速开始

```bash
# 前端
npm install
npm run dev          # http://localhost:3000

# 后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload   # http://localhost:8000
```

## 项目结构

```
app/                    # Next.js 页面
  recommendations/      # 每日建议（主页）
  watchlist/            # 圈子选股
  reviews/              # 复盘记录
  positions/            # 我的持仓
  admin/                # 圈子管理
  join/                 # 加入圈子
components/
  layout/               # 布局组件 (AppShell)
  stock/                # 股票卡片组件
lib/
  api.ts                # API 客户端
  store.ts              # Zustand 状态管理
  types.ts              # TypeScript 类型定义
  auth.ts               # 认证工具
  mock-data.ts          # 演示数据
backend/
  app/
    main.py             # FastAPI 入口
    models.py           # Pydantic 模型
    store.py            # 内存数据存储
    api/                # API 路由
docs/
  v1.1-product-plan.md  # 产品方案
  deployment-guide.md   # 部署指南
```

## 文档

- [v1.1 产品方案](docs/v1.1-product-plan.md) — 详细产品设计文档
- [部署指南](docs/deployment-guide.md) — Vercel + Railway 部署说明
