# 数据不跳动问题排查

## 问题分析

数据能正常显示，但不跳动（不更新），可能的原因：

1. **后端引擎未运行**
2. **前端刷新间隔太长**
3. **数据更新了但前端没有正确显示**

## 检查步骤

### 1. 检查后端引擎是否运行

在 Railway Dashboard 中：
1. 进入服务页面
2. 查看 **Logs** 标签
3. 查找是否有 "✅ 引擎已启动" 的日志

如果没有看到这个日志，说明引擎可能没有启动。

### 2. 测试后端数据是否在更新

在浏览器控制台运行：

```javascript
// 第一次获取
fetch('https://blackhorse-quant-production.up.railway.app/api/positions/')
  .then(r => r.json())
  .then(data => {
    console.log('第一次:', data);
    
    // 3秒后再次获取
    setTimeout(() => {
      fetch('https://blackhorse-quant-production.up.railway.app/api/positions/')
        .then(r => r.json())
        .then(data2 => {
          console.log('3秒后:', data2);
          console.log('价格是否变化:', data[0]?.currentPrice !== data2[0]?.currentPrice);
        });
    }, 3000);
  });
```

如果价格没有变化，说明后端引擎没有运行。

### 3. 检查前端刷新逻辑

前端每2秒刷新一次，应该能看到数据变化。如果看不到，可能是：
- 后端引擎没有运行
- 或者刷新间隔需要调整

## 解决方案

### 方案 1：确认后端引擎运行

如果 Railway 日志中没有 "✅ 引擎已启动"，需要：
1. 检查 Railway 服务是否正常运行
2. 查看是否有错误日志
3. 可能需要重新部署后端

### 方案 2：优化前端刷新频率

可以缩短刷新间隔，让数据更新更明显。

### 方案 3：添加数据更新提示

可以在界面上显示最后更新时间，确认数据是否在刷新。
