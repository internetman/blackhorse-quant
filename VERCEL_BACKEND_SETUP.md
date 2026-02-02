# Vercel 部署后端配置指南

## API 地址两种模式（避免误导）

- **本地开发**：未设置 `NEXT_PUBLIC_API_URL` 时，前端默认使用 localhost 作为 API 地址（如 `http://localhost:8000`）。本地跑 FastAPI 时可不配置该变量。
- **生产/线上**：必须设置 `NEXT_PUBLIC_API_URL` 为实际后端地址（如 Railway 的 URL），并在 Vercel 中保存后**重新部署**，否则前端仍会使用默认 localhost，导致生产环境无数据。

## 问题说明

Vercel 部署的前端无法访问本地 `localhost:8000` 的 FastAPI 后端，导致生产环境没有数据。

## 解决方案

### 方案 1：部署 FastAPI 到云服务（推荐）

#### 选项 A：Railway（最简单）

1. **注册 Railway**
   - 访问 https://railway.app
   - 使用 GitHub 登录

2. **部署后端**
   ```bash
   # 在 Railway 中创建新项目
   # 连接 GitHub 仓库
   # 选择 backend 目录作为根目录
   ```

3. **配置环境变量**
   - Railway 会自动生成 URL，例如：`https://your-app.railway.app`
   - 复制这个 URL

4. **在 Vercel 设置环境变量**
   - 进入 Vercel 项目设置
   - 添加环境变量：
     ```
     NEXT_PUBLIC_API_URL=https://your-app.railway.app
     ```
   - 重新部署前端

#### 选项 B：Render

1. **注册 Render**
   - 访问 https://render.com
   - 使用 GitHub 登录

2. **创建 Web Service**
   - 连接 GitHub 仓库
   - 根目录设置为 `backend`
   - 构建命令：`pip install -r requirements.txt`
   - 启动命令：`uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - 环境变量：`PORT` (Render 自动设置)

3. **获取 URL 并配置 Vercel**
   - Render 会提供 URL，例如：`https://your-app.onrender.com`
   - 在 Vercel 设置 `NEXT_PUBLIC_API_URL`

#### 选项 C：Fly.io

1. **安装 Fly CLI**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **在 backend 目录创建 fly.toml**
   ```toml
   app = "your-app-name"
   primary_region = "hkg"

   [build]

   [http_service]
     internal_port = 8000
     force_https = true
     auto_stop_machines = true
     auto_start_machines = true
     min_machines_running = 0
     processes = ["app"]

   [[vm]]
     memory_mb = 256
     cpu_kind = "shared"
     cpus = 1
   ```

3. **部署**
   ```bash
   cd backend
   fly launch
   fly deploy
   ```

4. **配置 Vercel**
   - 获取 Fly.io URL：`https://your-app.fly.dev`
   - 在 Vercel 设置 `NEXT_PUBLIC_API_URL`

### 方案 2：使用 Vercel Serverless Functions（临时方案）

如果暂时不想部署独立后端，可以使用 Vercel Serverless Functions 作为 API 代理。

**注意**：这需要将 FastAPI 代码转换为 Next.js API Routes，工作量较大。

## 快速检查清单

- [ ] FastAPI 后端已部署到云服务
- [ ] 获取后端 URL（如 `https://your-app.railway.app`）
- [ ] 在 Vercel 项目设置中添加环境变量 `NEXT_PUBLIC_API_URL`
- [ ] 重新部署 Vercel 前端
- [ ] 测试生产环境数据加载

## 环境变量配置

在 Vercel 项目设置中：

1. 进入 **Settings** → **Environment Variables**
2. 添加：
   - **Name**: `NEXT_PUBLIC_API_URL`
   - **Value**: 你的后端 URL（如 `https://your-app.railway.app`）
   - **Environment**: Production, Preview, Development（根据需要选择）
3. 保存并重新部署

## 验证部署

部署后，检查浏览器控制台：
- 如果看到 API 请求失败，检查 `NEXT_PUBLIC_API_URL` 是否正确
- 如果看到 CORS 错误，需要在 FastAPI 后端配置 CORS（应该已经配置了）

## 本地开发

本地开发时，确保：
- FastAPI 运行在 `http://localhost:8000`
- 未设置 `NEXT_PUBLIC_API_URL` 时前端会自动使用该默认地址；也可在 `.env.local` 中显式设置：
  ```
  NEXT_PUBLIC_API_URL=http://localhost:8000
  ```
