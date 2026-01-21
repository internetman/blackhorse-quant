# CORS 问题测试和修复

## 当前状态

✅ `/health` 端点可以访问 → 后端正常运行
❌ API 端点返回 "Failed to fetch" → 可能是 CORS 问题

## 测试 CORS

在浏览器控制台运行以下代码，测试 CORS 是否正常：

```javascript
// 测试 API 端点的 CORS
fetch('https://blackhorse-quant-production.up.railway.app/api/positions', {
  method: 'GET',
  headers: {
    'Content-Type': 'application/json',
  },
  mode: 'cors'
})
.then(r => {
  console.log('✅ 响应状态:', r.status);
  console.log('✅ CORS 头:', r.headers.get('Access-Control-Allow-Origin'));
  return r.json();
})
.then(data => console.log('✅ 数据:', data))
.catch(err => {
  console.error('❌ 错误详情:', err);
  console.error('❌ 错误类型:', err.name);
  console.error('❌ 错误消息:', err.message);
});
```

## 如果看到 CORS 错误

需要确认后端 CORS 配置已正确部署。检查：

1. **确认 `backend/app/main.py` 中的 CORS 配置**：
   ```python
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["*"],  # 允许所有来源
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

2. **如果配置正确但仍有问题，可能需要重新部署后端**：
   ```bash
   git add backend/app/main.py
   git commit -m "确保 CORS 配置正确"
   git push
   ```

## 其他可能的原因

### 1. 预检请求（OPTIONS）失败

浏览器会先发送 OPTIONS 请求检查 CORS。如果 OPTIONS 请求失败，也会导致 "Failed to fetch"。

### 2. Railway 部署的代码版本

确认 Railway 部署的是最新版本的代码，包含正确的 CORS 配置。
