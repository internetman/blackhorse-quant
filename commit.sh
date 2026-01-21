#!/bin/bash
# 提交脚本

cd "$(dirname "$0")"

echo "添加所有文件..."
git add .

echo "提交代码..."
git commit -m "添加 FastAPI 后端并集成到前端

- 创建完整的 FastAPI 后端项目结构
- 实现所有 API 接口（持仓、交易、状态、统计、配置）
- 创建后端引擎实现实时数据更新（每秒更新价格，每5秒生成交易）
- 前端集成：创建 API 客户端，更新 Store 使用 API
- 所有组件已连接后端，支持实时数据刷新
- 添加后端文档（FASTAPI_SETUP.md, BACKEND_INTEGRATION.md）
- 配置 CORS 支持前端跨域访问
- 数据结构严格对齐前端 TypeScript 类型"

echo "提交完成！"
echo "请执行: git push origin main"
