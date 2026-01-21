# Railway 后端部署验证指南

## 已完成的设置

✅ Root Directory 设置为 `backend`
✅ 重新连接了 GitHub 仓库

## 验证步骤

### 1. 检查部署状态

在 Railway Dashboard 中：

1. 进入你的服务页面
2. 查看 **Deployments** 标签
3. 确认最新部署状态：
   - ✅ **Success**（绿色） = 部署成功
   - ⏳ **Building** = 正在构建
   - ❌ **Failed** = 部署失败（需要查看日志）

### 2. 检查启动命令

在 **Deploy** 页面确认：
- Start Command 已设置为：`uvicorn app.main:app --host 0.0.0.0 --port $PORT`

如果没有设置，请添加。

### 3. 测试后端端点

部署成功后，在浏览器中访问：

#### 健康检查
```
https://blackhorse-quant-production.up.railway.app/health
```
**预期结果**：`{"status": "healthy"}`

#### API 文档
```
https://blackhorse-quant-production.up.railway.app/docs
```
**预期结果**：显示 Swagger UI 界面

#### 根路径
```
https://blackhorse-quant-production.up.railway.app/
```
**预期结果**：`{"message": "黑马量化 API 服务运行中", "version": "1.0.0"}`

### 4. 检查日志（如果部署失败）

在 Railway 服务页面：
1. 点击 **Logs** 标签
2. 查看错误信息
3. 常见问题：
   - 端口错误：确保使用 `$PORT` 环境变量
   - 依赖安装失败：检查 `requirements.txt`
   - 模块找不到：确保根目录设置为 `backend`

## 如果部署失败

### 问题 1：端口错误
**解决**：确保启动命令使用 `--port $PORT`

### 问题 2：找不到模块
**解决**：确认 Root Directory 设置为 `backend`

### 问题 3：依赖安装失败
**解决**：检查 `backend/requirements.txt` 文件是否存在

## 部署成功后的下一步

一旦后端部署成功并验证通过：

1. **在 Vercel 配置环境变量**
   - 进入 Vercel 项目设置 → Environment Variables
   - 添加：`NEXT_PUBLIC_API_URL` = `https://blackhorse-quant-production.up.railway.app`
   - 选择所有环境（Production, Preview, Development）
   - 保存并重新部署

2. **验证前端连接**
   - 访问你的 Vercel 网站
   - 应该能看到数据，不再显示连接错误提示

## 快速检查清单

- [ ] Railway 部署状态为 Success
- [ ] `/health` 端点返回 `{"status": "healthy"}`
- [ ] `/docs` 可以访问 Swagger UI
- [ ] 在 Vercel 设置了 `NEXT_PUBLIC_API_URL` 环境变量
- [ ] Vercel 已重新部署
- [ ] 前端可以正常显示数据
