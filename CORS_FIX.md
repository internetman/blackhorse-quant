# CORS 问题排查和修复

## 当前问题

URL 已正确（无双斜杠），但出现 "Failed to fetch" 错误，这通常是：
1. CORS 配置问题
2. Railway 后端未正常运行
3. 网络连接问题

## 排查步骤

### 1. 测试后端是否可访问

在浏览器中直接访问：

```
https://blackhorse-quant-production.up.railway.app/health
```

**预期结果**：
- ✅ 返回 `{"status":"healthy"}` = 后端正常运行
- ❌ 无法访问或超时 = 后端可能未运行

### 2. 检查 CORS 配置

后端应该允许所有来源，但需要确认：

1. **检查 Railway 日志**：
   - 进入 Railway Dashboard
   - 查看服务的 **Logs** 标签
   - 查看是否有 CORS 相关错误

2. **测试 API 端点**：
   在浏览器控制台运行：
   ```javascript
   fetch('https://blackhorse-quant-production.up.railway.app/api/positions', {
     method: 'GET',
     headers: {
       'Content-Type': 'application/json',
     }
   })
   .then(r => r.json())
   .then(data => console.log('✅ 成功:', data))
   .catch(err => console.error('❌ 失败:', err));
   ```

### 3. 检查 Network 标签

在浏览器开发者工具的 **Network** 标签中：
1. 刷新页面
2. 查找对 `blackhorse-quant-production.up.railway.app` 的请求
3. 查看请求详情：
   - **Status**: 如果是 CORS 错误，会显示 "CORS policy" 相关错误
   - **Headers**: 查看响应头中是否有 `Access-Control-Allow-Origin`

## 可能的解决方案

### 方案 1：确认后端 CORS 配置

后端应该已经配置了允许所有来源，但需要确认代码已部署。

### 方案 2：检查 Railway 服务状态

1. 进入 Railway Dashboard
2. 检查服务状态是否为 **Running**
3. 查看日志，确认没有错误

### 方案 3：重新部署后端

如果 CORS 配置有更新，可能需要重新部署后端。
