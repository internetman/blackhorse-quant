# 验证部署和环境变量

## API 地址两种模式（避免误导）

- **本地开发**：未设置 `NEXT_PUBLIC_API_URL` 时，前端默认使用 localhost 作为 API 地址。
- **生产/线上**：必须设置 `NEXT_PUBLIC_API_URL` 为实际后端地址，并在 Vercel 保存后**重新部署**，否则生产环境仍会走默认 localhost。

## ✅ Vercel 部署成功

从日志看，部署已完成：
- ✅ 构建成功
- ✅ 所有页面生成成功
- ✅ 部署完成

## 🔍 现在需要验证环境变量是否生效

### 步骤 1：访问你的 Vercel 网站

访问你的 Vercel 部署地址（通常是 `https://blackhorse-quant.vercel.app` 或你的自定义域名）

### 步骤 2：打开浏览器开发者工具

按 **F12** 打开开发者工具

### 步骤 3：检查 Console 标签

你应该看到类似这样的日志：
```
🔗 API Base URL: https://blackhorse-quant-production.up.railway.app
🔗 Environment Variable: https://blackhorse-quant-production.up.railway.app
```

**如果看到**：
- ✅ `https://blackhorse-quant-production.up.railway.app` = 环境变量已生效
- ❌ `http://localhost:8000` = 环境变量未生效

### 步骤 4：检查 Network 标签

1. 刷新页面（F5 或 Ctrl+R）
2. 在 Network 标签中，查找对 `blackhorse-quant-production.up.railway.app` 的请求
3. 查看请求状态：
   - **200 OK** = 成功连接
   - **CORS error** = CORS 配置问题
   - **Failed** = 网络错误
   - **404** = 路径错误

### 步骤 5：测试 API 连接

在浏览器控制台（Console）运行：

```javascript
// 测试健康检查
fetch('https://blackhorse-quant-production.up.railway.app/health')
  .then(r => r.json())
  .then(data => {
    console.log('✅ 后端健康检查:', data);
  })
  .catch(err => {
    console.error('❌ 后端连接失败:', err);
  });

// 测试获取持仓
fetch('https://blackhorse-quant-production.up.railway.app/api/positions')
  .then(r => r.json())
  .then(data => {
    console.log('✅ 持仓数据:', data);
  })
  .catch(err => {
    console.error('❌ 获取持仓失败:', err);
  });
```

## 🎯 预期结果

如果一切正常：
- ✅ 页面不再显示黄色的连接错误提示
- ✅ 能看到持仓数据（如果有）
- ✅ 能看到统计数据（总盈亏、今日盈亏等）
- ✅ 控制台没有错误信息

## ❌ 如果仍然有问题

### 问题 1：环境变量未生效

**症状**：控制台显示 `API Base URL: http://localhost:8000`

**解决**：
1. 检查 Vercel 环境变量设置：
   - 变量名必须是 `NEXT_PUBLIC_API_URL`（注意大小写）
   - 必须选择 **Production** 环境
2. 再次重新部署

### 问题 2：CORS 错误

**症状**：Network 标签显示 CORS 错误

**解决**：
- 后端已配置允许所有来源
- 检查 Railway 日志，确认后端正常运行

### 问题 3：404 错误

**症状**：请求返回 404

**解决**：
- 检查 API 路径是否正确
- 确认后端路由配置

## 📝 请告诉我

1. **控制台显示的 API Base URL 是什么？**
2. **页面是否还显示连接错误提示？**
3. **Network 标签中的请求状态是什么？**
4. **运行测试代码后，控制台显示什么？**

这样我可以帮你进一步诊断问题。
