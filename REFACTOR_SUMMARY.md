# 重构总结：Next.js App Router 工程化改造

## 📁 完成后的文件树

```
blackhorse-quant/
├── app/
│   ├── dashboard/
│   │   └── page.tsx              # 交易面板页面
│   ├── config/
│   │   └── page.tsx              # 量化策略配置页面
│   ├── trades/
│   │   └── page.tsx              # 成交日志页面
│   ├── layout.tsx                # 根布局（包含 AppLayout）
│   ├── page.tsx                  # 首页（重定向到 /dashboard）
│   └── globals.css               # 全局样式
├── components/
│   ├── AppLayout.tsx             # 应用主布局（Sidebar + Header + Content）
│   ├── Sidebar.tsx               # 侧边栏导航
│   ├── Header.tsx                # 顶部标题栏
│   ├── BlackHorseLogo.tsx        # Logo 组件
│   ├── ConfigSection.tsx         # 配置区块组件
│   ├── FormField.tsx             # 表单字段组件
│   ├── Switch.tsx                # 开关组件
│   ├── PositionsTable.tsx        # 持仓表格组件
│   └── TradesTable.tsx           # 交易记录表格组件
├── lib/
│   ├── store.ts                  # Zustand 状态管理
│   ├── engine.ts                 # 假引擎（模拟数据更新）
│   └── mock.ts                   # Mock 数据
├── public/
│   └── logo.png                  # Logo 图片（已存在）
├── package.json                  # 添加了 zustand 依赖
└── tsconfig.json                 # 路径别名配置（@/*）
```

## 🔧 主要修改点

### 1. 目录结构（App Router）

#### 新增文件：
- `app/dashboard/page.tsx` - 交易面板路由
- `app/config/page.tsx` - 策略配置路由
- `app/trades/page.tsx` - 成交日志路由
- `app/page.tsx` - 首页，重定向到 `/dashboard`

#### 修改文件：
- `app/layout.tsx` - 添加了 `AppLayout` 组件包装

### 2. 组件拆分

#### 新增组件文件：
- `components/AppLayout.tsx` - 主布局容器，包含 Sidebar 和 Header
- `components/Sidebar.tsx` - 侧边栏导航，使用 Next.js Link 进行路由
- `components/Header.tsx` - 顶部栏，显示系统状态和盈亏
- `components/BlackHorseLogo.tsx` - Logo 组件（从原 page.tsx 提取）
- `components/ConfigSection.tsx` - 配置区块组件（从原 page.tsx 提取）
- `components/FormField.tsx` - 表单字段组件（从原 page.tsx 提取）
- `components/Switch.tsx` - 开关组件（从原 page.tsx 提取）
- `components/PositionsTable.tsx` - 持仓表格，使用 store 获取数据
- `components/TradesTable.tsx` - 交易记录表格，使用 store 获取数据

### 3. 状态管理（Zustand）

#### `lib/store.ts`：
- 使用 `zustand` 创建全局状态管理
- 状态包括：
  - `sysStatus`: 'running' | 'paused' | 'kill'
  - `positions[]`: 持仓数组
  - `trades[]`: 交易记录数组
  - `configParams`: 配置参数对象
  - `totalPnl`: 总盈亏
  - `todayPnl`: 今日盈亏
- 提供 actions：`setSysStatus`, `setPositions`, `updatePosition`, `addTrade`, `updateConfigParams`, `setTotalPnl`, `setTodayPnl`

### 4. 假引擎（Engine）

#### `lib/engine.ts`：
- `startEngine()`: 启动引擎
  - 每秒更新持仓价格和盈亏（随机变化）
  - 每 5 秒生成一条新交易记录（仅在 running 状态）
- `stopEngine()`: 停止引擎，清理定时器
- `setupStatusListener()`: 监听状态变化
  - 当状态变为 'kill' 时，自动强平所有持仓
- 价格变化：±1% 随机波动
- 盈亏计算：根据方向（多/空）和价格变化计算

### 5. Mock 数据

#### `lib/mock.ts`：
- 定义了 `Position` 和 `Trade` 接口
- 导出 `MOCK_POSITIONS` 和 `MOCK_TRADES`
- 在 `store.ts` 初始化时加载

### 6. 图片路径

#### 已修正：
- `components/BlackHorseLogo.tsx` 中使用 `/logo.png`
- 图片文件位于 `public/logo.png`（已存在）

### 7. 路由系统

#### 使用 Next.js App Router：
- `/` → 重定向到 `/dashboard`
- `/dashboard` → 交易面板
- `/config` → 策略配置
- `/trades` → 成交日志

#### 导航：
- `components/Sidebar.tsx` 使用 `next/link` 进行客户端路由
- 使用 `usePathname()` 高亮当前路由

## 🚀 功能特性

### 实时数据更新：
1. **价格更新**：每秒更新持仓价格（±1% 随机波动）
2. **盈亏计算**：自动计算每个持仓的盈亏百分比和金额
3. **交易生成**：每 5 秒生成一条新交易记录（仅在 running 状态）
4. **状态控制**：
   - `running`: 正常交易，生成新交易记录
   - `paused`: 暂停交易，不生成新交易，但更新价格
   - `kill`: 强平所有持仓，清空持仓列表

### 响应式设计：
- 移动端和桌面端都已优化
- 表格在移动端自动切换为卡片式布局

## 📦 依赖变更

### 新增依赖：
```json
"zustand": "^5.0.2"
```

### 安装命令：
```bash
npm install zustand
```

## ✅ 测试清单

### 路由测试：
- [x] `/` 重定向到 `/dashboard`
- [x] `/dashboard` 显示交易面板
- [x] `/config` 显示策略配置
- [x] `/trades` 显示成交日志

### 功能测试：
- [x] 引擎启动后，持仓价格实时更新
- [x] 盈亏自动计算并显示
- [x] running 状态下每 5 秒生成新交易
- [x] paused 状态下不生成新交易
- [x] kill 状态下强平所有持仓
- [x] 侧边栏导航正常工作
- [x] 移动端菜单正常显示/隐藏

## 🎯 运行命令

```bash
# 安装依赖（如果还没有安装 zustand）
npm install

# 启动开发服务器
npm run dev

# 访问
# http://localhost:3000 → 自动重定向到 /dashboard
# http://localhost:3000/dashboard
# http://localhost:3000/config
# http://localhost:3000/trades
```

## 📝 注意事项

1. **引擎启动**：引擎在 `AppLayout` 组件挂载时自动启动，卸载时自动停止
2. **状态持久化**：当前状态不持久化，刷新页面会重置（可以后续添加 localStorage）
3. **数据模拟**：所有数据都是模拟的，不连接真实后端
4. **性能优化**：交易记录最多保留 100 条，避免内存溢出

## 🔄 后续优化建议

1. 添加状态持久化（localStorage）
2. 添加更多配置参数
3. 添加图表展示（如 K 线图）
4. 添加数据导出功能
5. 添加更多交易策略模拟
