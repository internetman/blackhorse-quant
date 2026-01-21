# Mixed Content 错误修复

## 问题诊断

Network 标签显示所有请求都被 `(blocked:mixed-content)` 阻止。

**Mixed Content 错误**：浏览器阻止了从 HTTPS 页面（Vercel）到 HTTP 资源的请求。

## 可能的原因

1. **环境变量中的 URL 是 HTTP 而不是 HTTPS**
   - 检查 Vercel 环境变量 `NEXT_PUBLIC_API_URL`
   - 确保值是 `https://blackhorse-quant-production.up.railway.app`（注意是 `https://`）

2. **代码中硬编码了 HTTP URL**

## 解决方案

### 步骤 1：检查 Vercel 环境变量

在 Vercel 项目设置 → Environment Variables 中：

1. 找到 `NEXT_PUBLIC_API_URL`
2. **确认值以 `https://` 开头**：
   - ✅ 正确：`https://blackhorse-quant-production.up.railway.app`
   - ❌ 错误：`http://blackhorse-quant-production.up.railway.app`

### 步骤 2：如果环境变量是 HTTP，修改为 HTTPS

1. 编辑环境变量
2. 将 `http://` 改为 `https://`
3. 保存
4. 重新部署 Vercel

### 步骤 3：验证修复

修复后，Network 标签中的请求应该：
- ✅ 状态不再是 `(blocked:mixed-content)`
- ✅ 应该显示 `200 OK` 或其他正常状态码

## 快速检查

在浏览器控制台运行：

```javascript
// 检查环境变量值
console.log('API URL:', process.env.NEXT_PUBLIC_API_URL);

// 检查 URL 协议
const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
console.log('协议:', apiUrl.startsWith('https://') ? 'HTTPS ✅' : 'HTTP ❌');
```

## 如果环境变量已经是 HTTPS

如果环境变量已经是 HTTPS，但仍然有 mixed-content 错误，可能是：

1. **浏览器缓存了旧的 HTTP URL**
   - 清除浏览器缓存
   - 硬刷新：`Ctrl+Shift+R` (Windows) 或 `Cmd+Shift+R` (Mac)

2. **Vercel 部署的代码使用了旧的 URL**
   - 确认代码已更新
   - 重新部署 Vercel
