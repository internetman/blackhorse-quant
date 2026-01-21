# 连接问题排查指南

## 当前问题

前端显示 "无法连接到后端服务"，但：
- ✅ Railway 后端正常运行（/health 返回正常）
- ✅ Vercel 环境变量已添加

## 可能的原因和解决方案

### 1. Vercel 还没有重新部署（最常见）

**问题**：环境变量添加后，需要重新部署才能生效。

**解决**：
1. 进入 Vercel Dashboard → 你的项目
2. 点击 **Deployments** 标签
3. 找到最新部署，点击 **⋯** → **Redeploy**
4. 等待部署完成（通常 1-2 分钟）

### 2. 环境变量配置错误

**检查**：
1. 进入 Vercel 项目设置 → **Environment Variables**
2. 确认：
   - **变量名**：`NEXT_PUBLIC_API_URL`（注意大小写，必须是 `NEXT_PUBLIC_` 开头）
   - **变量值**：`https://blackhorse-quant-production.up.railway.app`（没有尾随斜杠）
   - **环境**：已选择 **Production**（必须选择）

### 3. 检查浏览器控制台

按 F12 打开开发者工具，查看：

**Console 标签**：
- 应该看到 `🔗 API Base URL: https://blackhorse-quant-production.up.railway.app`
- 如果看到 `http://localhost:8000`，说明环境变量没有生效

**Network 标签**：
- 刷新页面
- 查找对 `blackhorse-quant-production.up.railway.app` 的请求
- 查看请求状态：
  - **200 OK** = 成功
  - **CORS error** = CORS 配置问题
  - **Failed** = 网络错误

### 4. 验证环境变量是否生效

在浏览器控制台（F12）运行：

```javascript
// 检查环境变量
console.log('API URL:', process.env.NEXT_PUBLIC_API_URL);

// 测试后端连接
fetch('https://blackhorse-quant-production.up.railway.app/health')
  .then(r => r.json())
  .then(data => {
    console.log('✅ 后端连接成功:', data);
  })
  .catch(err => {
    console.error('❌ 后端连接失败:', err);
  });
```

### 5. CORS 问题

如果看到 CORS 错误：

1. **检查后端 CORS 配置**：
   - 后端已配置允许所有来源
   - 如果仍有问题，检查 Railway 日志

2. **检查请求头**：
   - 在 Network 标签中查看请求
   - 确认请求包含正确的 headers

### 6. 清除浏览器缓存

有时浏览器缓存了旧的环境变量：

1. 硬刷新：`Ctrl+Shift+R` (Windows) 或 `Cmd+Shift+R` (Mac)
2. 或者清除浏览器缓存

## 快速诊断步骤

### 步骤 1：确认 Vercel 已重新部署
- [ ] 在 Vercel Dashboard 确认最新部署时间
- [ ] 如果环境变量是刚添加的，必须重新部署

### 步骤 2：检查环境变量
- [ ] 变量名正确：`NEXT_PUBLIC_API_URL`
- [ ] 变量值正确：`https://blackhorse-quant-production.up.railway.app`
- [ ] 已选择 Production 环境

### 步骤 3：检查浏览器控制台
- [ ] 打开 F12 → Console
- [ ] 查看 API Base URL 显示的值
- [ ] 查看是否有错误信息

### 步骤 4：测试后端连接
- [ ] 直接访问：`https://blackhorse-quant-production.up.railway.app/health`
- [ ] 应该返回：`{"status":"healthy"}`

### 步骤 5：检查网络请求
- [ ] 打开 F12 → Network
- [ ] 刷新页面
- [ ] 查看对后端 API 的请求状态

## 如果仍然无法解决

请提供以下信息：

1. **浏览器控制台的完整错误信息**（截图或复制文本）
2. **Network 标签中的请求详情**（特别是失败的请求）
3. **Vercel 部署日志**（如果有错误）
4. **Railway 日志**（如果有错误）
