# 黑马自选 部署指南

**👉 一步步操作请看：[DEPLOY_CHECKLIST.md](./DEPLOY_CHECKLIST.md)**

## 架构

- 前端: Next.js, 部署在 Vercel
- 后端: FastAPI, 部署在 Railway

## 环境变量

### 前端 (Vercel)
- `NEXT_PUBLIC_API_URL`: 后端 API 地址 (如 https://blackhorse-quant-production.up.railway.app)
  - 未设置时默认使用 localhost
  - 生产环境必须设置并重新部署

### 后端 (Railway)
- `ALLOW_FORCE_CLOSE`: 是否允许强制清仓 (true/false)

**👉 按步骤操作请直接看：[DEPLOY_CHECKLIST.md](./DEPLOY_CHECKLIST.md)**

## 部署要点

### 后端 (Railway)
- 从 GitHub 部署时，**Root Directory** 必须设为 `backend`
- 启动命令已写在 `backend/railway.json`，一般无需改

### 前端 (Vercel)
- 导入仓库后 **Root Directory** 保持仓库根目录（不要选 backend）
- 必须配置 `NEXT_PUBLIC_API_URL` 为 Railway 后端域名
- 之后每次 push 到 main 会自动部署
