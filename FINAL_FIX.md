# 最终修复：Failed to fetch 错误

## 问题分析

"Failed to fetch" 错误通常由以下原因引起：

1. **CORS 配置问题**（最可能）
2. **后端服务未运行**
3. **网络连接问题**

## 立即检查步骤

### 1. 测试后端是否可访问

在浏览器中直接访问：
```
https://blackhorse-quant-production.up.railway.app/health
```

**如果无法访问**：
- Railway 后端可能未运行
- 检查 Railway Dashboard → 服务状态

**如果可以访问**：
- 后端正常运行，问题可能是 CORS

### 2. 检查 CORS 配置

后端代码已经配置了允许所有来源，但需要确认：

1. **检查 Railway 部署的代码版本**：
   - 确认 `backend/app/main.py` 中的 CORS 配置已部署
   - 如果最近更新了 CORS 配置，需要重新部署后端

2. **测试 CORS**：
   在浏览器控制台运行：
   ```javascript
   fetch('https://blackhorse-quant-production.up.railway.app/api/positions', {
     method: 'GET',
     headers: {
       'Content-Type': 'application/json',
     }
   })
   .then(r => r.json())
   .then(data => console.log('✅ CORS 正常:', data))
   .catch(err => console.error('❌ CORS 错误:', err));
   ```

### 3. 检查 Network 标签详情

在浏览器开发者工具中：
1. 打开 **Network** 标签
2. 刷新页面
3. 找到失败的请求（红色）
4. 点击查看详情：
   - **Headers** → 查看响应头
   - **Console** → 查看具体错误信息

## 解决方案

### 方案 1：重新部署后端（如果 CORS 配置有更新）

如果最近更新了 `backend/app/main.py` 中的 CORS 配置：

1. 提交并推送代码：
   ```bash
   git add backend/app/main.py
   git commit -m "更新 CORS 配置"
   git push
   ```

2. Railway 会自动重新部署

### 方案 2：检查 Railway 服务状态

1. 进入 Railway Dashboard
2. 检查服务状态是否为 **Running**
3. 查看 **Logs** 标签，确认没有错误

### 方案 3：验证 CORS 配置

确认 `backend/app/main.py` 中的 CORS 配置：

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 快速诊断

请告诉我：

1. **直接访问 `/health` 端点是否成功？**
   - 访问：`https://blackhorse-quant-production.up.railway.app/health`

2. **Network 标签中的错误详情是什么？**
   - 是否有 "CORS policy" 相关错误？
   - 请求状态是什么？

3. **Railway 服务状态是什么？**
   - 是否显示为 Running？

根据这些信息，我可以提供更精确的解决方案。
