# Vercel 自动化部署指南

本项目已配置自动化部署到 Vercel，支持以下部署方式：

## 🚀 部署方式

### 1. 自动部署（推荐）

#### GitHub Actions 自动部署

当代码推送到 `main` 或 `master` 分支时，会自动触发生产环境部署。

**配置步骤：**

1. **获取 Vercel Token**
   - 访问 [Vercel Account Settings](https://vercel.com/account/tokens)
   - 创建一个新的 Token
   - 复制 Token 值

2. **获取 Vercel 项目信息**
   - 在项目根目录运行：`vercel link`
   - 或者访问项目设置页面获取：
     - `VERCEL_ORG_ID`: 组织 ID
     - `VERCEL_PROJECT_ID`: 项目 ID

3. **配置 GitHub Secrets**
   - 进入 GitHub 仓库 → Settings → Secrets and variables → Actions
   - 添加以下 Secrets：
     - `VERCEL_TOKEN`: Vercel API Token
     - `VERCEL_ORG_ID`: Vercel 组织 ID
     - `VERCEL_PROJECT_ID`: Vercel 项目 ID

4. **推送代码**
   ```bash
   git push origin main
   ```
   - 推送后会自动触发部署
   - 查看部署状态：GitHub Actions 标签页

#### Pull Request 预览部署

当创建 Pull Request 时，会自动部署预览环境，方便代码审查。

### 2. 手动部署

#### 使用 Vercel CLI

```bash
# 安装 Vercel CLI（如果未安装）
npm install -g vercel

# 登录 Vercel
vercel login

# 部署到生产环境
npm run deploy

# 部署预览环境
npm run deploy:preview
```

#### 使用 Vercel Dashboard

1. 访问 [Vercel Dashboard](https://vercel.com/dashboard)
2. 点击 "Add New Project"
3. 导入 GitHub 仓库
4. 配置项目设置
5. 点击 "Deploy"

## 📋 部署配置说明

### vercel.json

项目根目录的 `vercel.json` 文件包含以下配置：

- **构建命令**: `npm run build`
- **开发命令**: `npm run dev`
- **安装命令**: `npm install`
- **框架**: Next.js
- **区域**: 香港 (hkg1)
- **安全头**: 已配置 XSS 防护、内容类型保护等

### GitHub Actions 工作流

#### 生产部署 (`deploy-vercel.yml`)
- 触发条件：推送到 main/master 分支
- 执行步骤：
  1. 代码检出
  2. Node.js 环境设置
  3. 依赖安装
  4. 代码检查（lint）
  5. 项目构建
  6. Vercel 部署

#### 预览部署 (`deploy-preview.yml`)
- 触发条件：创建 Pull Request
- 执行步骤：同生产部署，但部署到预览环境

## 🔧 环境变量配置

如果需要配置环境变量：

1. **在 Vercel Dashboard 配置**
   - 进入项目 → Settings → Environment Variables
   - 添加所需的环境变量

2. **在 GitHub Secrets 配置**
   - 如果需要在构建时使用，添加到 GitHub Secrets
   - 在 workflow 文件中引用：`${{ secrets.VARIABLE_NAME }}`

## 📊 部署状态检查

- **GitHub Actions**: 查看 `.github/workflows/` 下的工作流执行状态
- **Vercel Dashboard**: 查看部署历史和状态
- **部署日志**: 在 Vercel Dashboard 中查看详细的构建和部署日志

## 🐛 故障排查

### 部署失败常见原因

1. **构建错误**
   - 检查 `npm run build` 是否在本地成功
   - 查看 GitHub Actions 日志中的错误信息

2. **环境变量缺失**
   - 确保所有必需的环境变量已在 Vercel 中配置

3. **依赖安装失败**
   - 检查 `package.json` 中的依赖版本
   - 确保 `package-lock.json` 已提交

4. **Vercel Token 无效**
   - 重新生成 Token 并更新 GitHub Secrets

### 查看日志

```bash
# 使用 Vercel CLI 查看日志
vercel logs

# 查看特定部署的日志
vercel logs [deployment-url]
```

## 🔄 回滚部署

如果部署出现问题，可以在 Vercel Dashboard 中：

1. 进入项目 → Deployments
2. 找到之前的成功部署
3. 点击 "..." → "Promote to Production"

## 📝 注意事项

- 确保 `.gitignore` 中已包含 `.vercel` 目录
- 生产环境部署前建议先在预览环境测试
- 定期更新依赖以保持安全性
- 监控部署状态和性能指标

## 🎯 快速开始

1. 配置 GitHub Secrets（见上方步骤）
2. 推送代码到 main 分支
3. 等待自动部署完成
4. 访问部署的 URL

---

如有问题，请查看 [Vercel 文档](https://vercel.com/docs) 或提交 Issue。
