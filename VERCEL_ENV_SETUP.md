# Vercel 环境变量配置指南

## API 地址两种模式（避免误导）

- **本地开发**：未设置 `NEXT_PUBLIC_API_URL` 时，前端默认使用 localhost 作为 API 地址。
- **生产/线上**：必须设置 `NEXT_PUBLIC_API_URL` 为实际后端地址（如下方 Railway URL），保存后**重新部署** Vercel，否则生产环境无数据。

## Railway 后端地址

你的 Railway 后端地址：`blackhorse-quant-production.up.railway.app`

**完整 URL**：`https://blackhorse-quant-production.up.railway.app`

## 在 Vercel 中配置环境变量

### 步骤 1：进入 Vercel 项目设置

1. 登录 [Vercel Dashboard](https://vercel.com/dashboard)
2. 选择你的项目 `blackhorse-quant`
3. 点击 **Settings**（设置）
4. 在左侧菜单选择 **Environment Variables**（环境变量）

### 步骤 2：添加环境变量

点击 **Add New**（添加新变量），填写：

- **Name（名称）**：`NEXT_PUBLIC_API_URL`
- **Value（值）**：`https://blackhorse-quant-production.up.railway.app`
- **Environment（环境）**：选择所有环境
  - ✅ Production（生产环境）
  - ✅ Preview（预览环境）
  - ✅ Development（开发环境，可选）

### 步骤 3：保存并重新部署

1. 点击 **Save**（保存）
2. 进入 **Deployments**（部署）页面
3. 找到最新的部署，点击 **⋯**（三个点）
4. 选择 **Redeploy**（重新部署）

或者直接推送代码到 GitHub，Vercel 会自动重新部署。

## 验证配置

部署完成后，访问你的 Vercel 网站：

1. 打开浏览器开发者工具（F12）
2. 查看 **Console**（控制台）标签
3. 如果看到连接错误，检查：
   - 环境变量是否正确设置
   - Railway 后端是否正在运行
   - 网络请求是否指向正确的 URL

## 测试后端连接

在浏览器中直接访问：
```
https://blackhorse-quant-production.up.railway.app/health
```

应该返回：
```json
{"status": "healthy"}
```

## 本地开发

本地开发时，确保：

1. FastAPI 后端运行在 `http://localhost:8000`
2. 或者创建 `.env.local` 文件：
   ```
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

## 故障排除

### 问题：仍然无法连接

1. **检查环境变量**：确保 `NEXT_PUBLIC_API_URL` 已正确设置
2. **检查 Railway 状态**：确保后端服务正在运行
3. **检查 CORS**：后端已配置允许所有来源
4. **检查 URL 格式**：确保 URL 以 `https://` 开头，没有尾随斜杠

### 问题：CORS 错误

后端已配置允许所有来源，如果仍有 CORS 错误：
- 检查 Railway 日志
- 确认后端服务正常运行

## 下一步

配置完成后：
1. ✅ Vercel 前端可以连接到 Railway 后端
2. ✅ 数据会正常显示
3. ✅ 所有功能正常工作
