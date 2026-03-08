# A股武器库 - 故障排查指南

## 常见问题

### 1. ImportError: No module named 'efinance'

**原因：** 未安装依赖

**解决方案：**
```bash
# 方案1：运行安装脚本
python scripts/install_dependencies.py

# 方案2：手动安装
pip install efinance rich pyyaml loguru pandas
```

---

### 2. 数据为空或获取失败

**可能原因：**
1. 非交易时间（周末、节假日、收盘后）
2. 网络问题
3. 数据源限流

**解决方案：**
```bash
# 1. 检查网络
ping www.baidu.com

# 2. 查看日志
cat logs/stock_arsenal_error.log

# 3. 尝试不同时间段
# 交易时间：周一至周五 9:30-15:00
```

---

### 3. talib安装失败

**原因：** talib需要系统依赖，安装复杂

**解决方案：**
```bash
# 方案1：跳过talib（推荐）
# 原型版本不依赖talib，可以不安装

# 方案2：使用预编译版本
pip install talib-binary

# 方案3：使用conda安装
conda install -c conda-forge ta-lib
```

---

### 4. 编码错误（UnicodeEncodeError）

**症状：** 中文乱码或编码错误

**解决方案：**
```bash
# Linux/Mac
export PYTHONIOENCODING=utf-8

# Windows PowerShell
$env:PYTHONIOENCODING="utf-8"

# 然后运行
python src/main.py
```

---

### 5. 数据源连接失败

**症状：** Connection Error或Timeout

**解决方案：**
```bash
# 1. 检查网络连接
ping api.eastmoney.com

# 2. 尝试切换数据源
# 编辑 config/default.yaml，修改primary数据源

# 3. 如果akshare限流，临时只用efinance
pip install efinance rich
```

---

### 6. 脚本执行权限问题

**症状：** Permission denied

**解决方案：**
```bash
# 添加执行权限
chmod +x scripts/*.py

# 或直接用python执行
python scripts/analyze_limit_up.py
```

---

## 调试技巧

### 查看日志

```bash
# 运行日志
tail -f logs/stock_arsenal.log

# 错误日志
tail -f logs/stock_arsenal_error.log

# 查看最近100行
tail -n 100 logs/stock_arsenal_error.log
```

### 单独测试模块

```bash
# 测试涨停预测
python scripts/analyze_limit_up.py

# 测试智能选股
python scripts/stock_screener.py

# 测试买入信号
python scripts/check_buy_signal.py
```

### 检查Python版本

```bash
python --version
# 应该是 3.8 或更高
```

### 验证依赖安装

```bash
python -c "import efinance; print('efinance OK')"
python -c "import rich; print('rich OK')"
python -c "import pandas; print('pandas OK')"
```

---

## 性能问题

### 响应慢

**可能原因：**
1. 网络慢
2. 数据量大
3. API限流

**解决方案：**
```bash
# 1. 使用缓存（自动启用）
# 2. 减少分析股票数量
# 3. 避开高峰期使用
```

### 内存占用高

**解决方案：**
```bash
# 1. 清理缓存
rm -rf __pycache__
rm -rf .pytest_cache

# 2. 重启程序
```

---

## 获取帮助

### 查看文档

```bash
# 快速开始
cat QUICKSTART.md

# 详细指南
cat docs/PROTOTYPE_GUIDE.md

# 开发文档
cat docs/DEVELOPMENT.md
```

### 检查配置

```bash
# 查看默认配置
cat config/default.yaml

# 查看用户配置（如果有）
cat config/user.yaml
```

### 报告问题

收集以下信息：
1. 错误信息截图
2. logs/stock_arsenal_error.log
3. Python版本
4. 操作系统版本

---

## 最佳实践

1. **交易时间使用** - 数据更及时
2. **先测试小功能** - 验证安装
3. **查看日志** - 定期检查错误
4. **定期更新** - 更新依赖包
5. **备份数据** - 定期备份config和logs

---

## 常用命令

```bash
# 安装依赖
python scripts/install_dependencies.py

# 运行主程序
python src/main.py

# 运行单个功能
python scripts/analyze_limit_up.py
python scripts/stock_screener.py
python scripts/track_hot_money.py
python scripts/check_buy_signal.py
python scripts/check_limit_down_risk.py

# 查看日志
tail -f logs/stock_arsenal_error.log

# 清理缓存
rm -rf __pycache__
```

---

**如果问题仍未解决，请查看完整文档或提交Issue。**
