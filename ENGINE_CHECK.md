# 后端引擎检查指南

## 问题

数据不跳动，可能是后端引擎没有正常运行。

## 检查步骤

### 1. 检查 Railway 日志

在 Railway Dashboard 中：
1. 进入服务页面
2. 查看 **Logs** 标签
3. 查找是否有 "✅ 引擎已启动" 的日志

**如果没有看到这个日志**：
- 引擎可能没有启动
- 需要检查启动逻辑

### 2. 测试后端数据是否在更新

在浏览器控制台运行：

```javascript
// 第一次获取
let firstPrice = null;
fetch('https://blackhorse-quant-production.up.railway.app/api/positions/')
  .then(r => r.json())
  .then(data => {
    firstPrice = data[0]?.currentPrice;
    console.log('第一次价格:', firstPrice);
    
    // 3秒后再次获取
    setTimeout(() => {
      fetch('https://blackhorse-quant-production.up.railway.app/api/positions/')
        .then(r => r.json())
        .then(data2 => {
          const secondPrice = data2[0]?.currentPrice;
          console.log('3秒后价格:', secondPrice);
          console.log('价格是否变化:', firstPrice !== secondPrice);
          
          if (firstPrice === secondPrice) {
            console.warn('⚠️ 价格没有变化，后端引擎可能没有运行');
          } else {
            console.log('✅ 价格在变化，后端引擎正常运行');
          }
        });
    }, 3000);
  });
```

### 3. 检查系统状态

确保系统状态是 "running"：
- 如果状态是 "paused" 或 "kill"，引擎不会更新数据
- 检查前端显示的系统状态

## 解决方案

### 如果引擎没有运行

1. **检查 Railway 日志**，查看是否有错误
2. **重新部署后端**，确保引擎启动代码被执行
3. **检查系统状态**，确保是 "running"

### 如果引擎运行但数据不更新

1. **检查前端刷新频率**（已优化为每秒刷新）
2. **检查数据是否正确显示**（可能需要添加动画效果）
