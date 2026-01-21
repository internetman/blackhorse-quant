# Railway 后端部署修复指南

## 问题

访问 `https://blackhorse-quant-production.up.railway.app/health` 返回 404，且显示的是前端界面，说明 Railway 部署了前端代码而不是后端。

## 解决方案

### 方法 1：在 Railway 中重新配置（推荐）

1. **进入 Railway 项目设置**
   - 登录 [Railway Dashboard](https://railway.app)
   - 选择你的项目

2. **检查服务配置**
   - 点击服务（Service）
   - 进入 **Settings**（设置）

3. **设置根目录（Root Directory）**
   - 找到 **Root Directory** 设置
   - 设置为：`backend`
   - 保存

4. **设置启动命令（Start Command）**
   - 找到 **Start Command** 设置
   - 设置为：`uvicorn app.main:app --host 0.0.0.0 --port $PORT`
   - 保存

5. **设置构建命令（Build Command）**
   - 找到 **Build Command** 设置
   - 设置为：`pip install -r requirements.txt`
   - 或者留空（Railway 会自动检测）

6. **重新部署**
   - 在 **Deployments** 页面
   - 点击 **Redeploy**（重新部署）

### 方法 2：创建新的后端服务

如果当前服务配置混乱，可以：

1. **删除当前服务**（可选）
   - 在 Railway 项目中删除当前服务

2. **创建新服务**
   - 点击 **+ New** → **GitHub Repo**
   - 选择你的仓库
   - **重要**：在配置时设置：
     - **Root Directory**: `backend`
     - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

### 方法 3：使用 Railway CLI

```bash
# 安装 Railway CLI
npm i -g @railway/cli

# 登录
railway login

# 在 backend 目录中初始化
cd backend
railway init

# 设置变量（如果需要）
railway variables set PORT=8000

# 部署
railway up
```

## 验证部署

部署完成后，访问：

```
https://blackhorse-quant-production.up.railway.app/health
```

应该返回：
```json
{"status": "healthy"}
```

访问 API 文档：
```
https://blackhorse-quant-production.up.railway.app/docs
```

应该看到 Swagger UI 界面。

## 检查清单

- [ ] Railway 服务根目录设置为 `backend`
- [ ] 启动命令设置为 `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- [ ] 构建命令设置为 `pip install -r requirements.txt`（或自动检测）
- [ ] 服务已重新部署
- [ ] `/health` 端点返回 `{"status": "healthy"}`
- [ ] `/docs` 可以访问 Swagger UI

## 常见问题

### Q: 仍然显示前端界面
A: 确保 Root Directory 设置为 `backend`，不是项目根目录。

### Q: 端口错误
A: Railway 使用 `$PORT` 环境变量，确保启动命令使用 `--port $PORT`。

### Q: 依赖安装失败
A: 检查 `backend/requirements.txt` 是否存在且包含所有依赖。

## 下一步

修复后：
1. ✅ 后端正确部署在 Railway
2. ✅ `/health` 端点正常工作
3. ✅ 在 Vercel 配置 `NEXT_PUBLIC_API_URL` 环境变量
4. ✅ 前端可以正常连接后端
