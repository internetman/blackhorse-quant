#!/bin/bash

# Vercel 自动化部署快速设置脚本

echo "🚀 Vercel 自动化部署设置向导"
echo "================================"
echo ""

# 检查是否已安装 Vercel CLI
if ! command -v vercel &> /dev/null; then
    echo "📦 正在安装 Vercel CLI..."
    npm install -g vercel@latest
else
    echo "✅ Vercel CLI 已安装"
fi

echo ""
echo "🔐 请登录 Vercel 账户..."
vercel login

echo ""
echo "🔗 正在链接项目到 Vercel..."
vercel link

echo ""
echo "📋 获取项目信息..."
echo ""
echo "请将以下信息添加到 GitHub Secrets:"
echo "================================"
echo ""

# 尝试从 .vercel/project.json 读取信息
if [ -f ".vercel/project.json" ]; then
    ORG_ID=$(cat .vercel/project.json | grep -o '"orgId":"[^"]*"' | cut -d'"' -f4)
    PROJECT_ID=$(cat .vercel/project.json | grep -o '"projectId":"[^"]*"' | cut -d'"' -f4)
    
    echo "VERCEL_ORG_ID: $ORG_ID"
    echo "VERCEL_PROJECT_ID: $PROJECT_ID"
    echo ""
fi

echo "VERCEL_TOKEN: 请在 https://vercel.com/account/tokens 创建并复制"
echo ""
echo "📝 配置步骤:"
echo "1. 访问 https://github.com/YOUR_USERNAME/YOUR_REPO/settings/secrets/actions"
echo "2. 点击 'New repository secret'"
echo "3. 添加上述三个 Secrets"
echo ""
echo "✅ 设置完成！现在可以推送代码到 main 分支触发自动部署了。"
echo ""
