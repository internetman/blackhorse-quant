# A股武器库 - 原型使用指南

## 📦 已完成功能

### ✅ 核心框架
- [x] 三层模块化架构（数据层/业务层/交互层）
- [x] 三大数据源适配器（akshare/efinance/baostock）
- [x] 智能路由和自动降级
- [x] 缓存管理系统
- [x] SQLite存储
- [x] 日志系统
- [x] 配置管理

### ✅ 5个核心功能
1. **涨停板预测** - 综合评分预测明日涨停股
2. **智能选股器** - 多条件筛选优质股票
3. **游资席位跟踪** - 跟踪知名游资动向
4. **买入信号** - 综合分析买入时机
5. **跌停板预警** - 预警跌停风险

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

**注意：**
- 如果只想用efinance（推荐）：`pip install efinance rich pyyaml loguru`
- 如果想用全部数据源：`pip install akshare efinance baostock`

### 2. 运行程序

```bash
python src/main.py
```

### 3. 使用示例

启动后会看到菜单：
```
┌─────────────────────────────────┐
│     🎯 A股武器库 v1.0           │
├─────────────────────────────────┤
│  1. 💰 涨停板预测               │
│  2. 🎯 智能选股器               │
│  3. 💸 游资席位跟踪             │
│  4. 📈 买入信号                 │
│  5. ⚠️  跌停板预警              │
│  0. 退出                        │
└─────────────────────────────────┘

请选择功能 (0-5):
```

输入数字即可执行对应功能。

## ⚠️ 重要提示

### 数据源问题

**推荐只用efinance！**

原因：
1. **efinance** - 东方财富官方数据，稳定免费，无需注册
2. **akshare** - 数据最全但部分接口需要积分
3. **baostock** - 适合历史数据，实时性差

### 安装顺序

```bash
# 最小安装（推荐）
pip install efinance rich pyyaml loguru pandas

# 或安装requirements.txt（可能有问题）
pip install -r requirements.txt
```

### 已知问题

1. **talib安装困难** - requirements.txt中的talib-binary可能装不上，可以先跳过
2. **akshare限制** - 部分接口需要token或积分
3. **市场时间** - 非交易时间数据可能为空或延迟

## 🔧 故障排查

### 问题1: ImportError

```bash
# 解决：安装对应数据源
pip install efinance
```

### 问题2: 数据为空

- 检查是否在交易时间（周一至周五 9:30-15:00）
- 非交易时间使用历史数据测试

### 问题3: 编码错误

```bash
# 设置环境变量
export PYTHONIOENCODING=utf-8
```

## 📝 下一步开发

### 短期优化
- [ ] 修复efinance_adapter的语法错误
- [ ] 完善错误处理
- [ ] 添加单元测试
- [ ] 优化输出格式

### 中期扩展
- [ ] 其余15个功能模块
- [ ] Web界面（FastAPI + Vue）
- [ ] 数据回测功能
- [ ] 策略分享社区

### 长期目标
- [ ] 机器学习预测模型
- [ ] 微信/Telegram通知
- [ ] 云端部署
- [ ] 移动端APP

## 💡 使用建议

1. **先测试单个功能** - 选择"1"测试涨停预测
2. **查看日志** - logs/目录下的日志文件
3. **自定义配置** - 复制config/user.yaml.example为user.yaml

## 📞 反馈

如有问题，请查看：
- logs/stock_arsenal.log - 运行日志
- logs/stock_arsenal_error.log - 错误日志

---

**祝投资顺利！记住：风险控制第一！**
