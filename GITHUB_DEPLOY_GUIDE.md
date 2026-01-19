# GitHub 自动部署到 Vercel 完整指南

有两种方式可以实现提交代码到 GitHub 后自动部署到 Vercel：

## 🎯 方式一：使用 Vercel GitHub 集成（推荐，最简单）

这是最简单的方式，无需配置 GitHub Secrets，Vercel 会自动处理一切。

### 步骤：

1. **登录 Vercel**
   - 访问 [https://vercel.com](https://vercel.com)
   - 使用 GitHub 账号登录

2. **导入 GitHub 仓库**
   - 在 Vercel Dashboard 点击 "Add New Project"
   - 选择 "Import Git Repository"
   - 选择你的 `blackhorse-quant` 仓库
   - 点击 "Import"

3. **配置项目**
   - Framework Preset: Next.js（会自动检测）
   - Root Directory: `./`（默认）
   - Build Command: `npm run build`（默认）
   - Output Directory: `.next`（默认）
   - Install Command: `npm install`（默认）

4. **环境变量（如果需要）**
   - 在项目设置中添加环境变量
   - 点击 "Deploy"

5. **完成！**
   - 部署完成后，Vercel 会自动：
     - 监听 GitHub 仓库的 push 事件
     - 每次推送到 main/master 分支时自动部署
     - 创建 Pull Request 时自动创建预览环境

### 验证自动部署：

```bash
# 1. 修改代码
echo "// 测试自动部署" >> app/page.tsx

# 2. 提交并推送
git add .
git commit -m "测试自动部署"
git push origin main

# 3. 在 Vercel Dashboard 查看部署状态
# 几秒钟后就会看到新的部署开始
```

---

## 🔧 方式二：使用 GitHub Actions（已配置）

如果你想要更多控制，可以使用已配置的 GitHub Actions 工作流。

### 前置步骤：

1. **获取 Vercel Token**
   ```bash
   # 访问 https://vercel.com/account/tokens
   # 点击 "Create Token"
   # 复制生成的 Token
   ```

2. **获取 Vercel 项目信息**
   ```bash
   # 在项目根目录运行
   npm install -g vercel
   vercel login
   vercel link
   
   # 或者查看 .vercel/project.json 文件
   cat .vercel/project.json
   ```

3. **配置 GitHub Secrets**
   - 进入 GitHub 仓库
   - 点击 Settings → Secrets and variables → Actions
   - 点击 "New repository secret"
   - 添加以下三个 Secrets：
     
     **VERCEL_TOKEN**
     - Name: `VERCEL_TOKEN`
     - Value: 从步骤1获取的 Token
     
     **VERCEL_ORG_ID**
     - Name: `VERCEL_ORG_ID`
     - Value: 从 `.vercel/project.json` 中的 `orgId`
     
     **VERCEL_PROJECT_ID**
     - Name: `VERCEL_PROJECT_ID`
     - Value: 从 `.vercel/project.json` 中的 `projectId`

4. **推送代码触发部署**
   ```bash
   git add .
   git commit -m "配置自动部署"
   git push origin main
   ```

5. **查看部署状态**
   - 在 GitHub 仓库点击 "Actions" 标签
   - 查看工作流执行状态
   - 部署成功后，在 Vercel Dashboard 可以看到新部署

---

## 📋 两种方式对比

| 特性 | Vercel GitHub 集成 | GitHub Actions |
|------|-------------------|----------------|
| 设置难度 | ⭐ 非常简单 | ⭐⭐⭐ 需要配置 Secrets |
| 自动化程度 | ✅ 完全自动 | ✅ 完全自动 |
| 自定义控制 | ⚠️ 有限 | ✅ 完全控制 |
| 预览环境 | ✅ 自动创建 | ✅ 自动创建 |
| 构建日志 | ✅ Vercel Dashboard | ✅ GitHub Actions |
| 推荐场景 | 大多数项目 | 需要自定义构建流程 |

---

## 🚀 快速开始（推荐方式一）

### 1. 确保代码已推送到 GitHub

```bash
# 如果还没有初始化 Git
git init
git add .
git commit -m "Initial commit"

# 在 GitHub 创建仓库后
git remote add origin https://github.com/YOUR_USERNAME/blackhorse-quant.git
git branch -M main
git push -u origin main
```

### 2. 在 Vercel 导入项目

1. 访问 [https://vercel.com/new](https://vercel.com/new)
2. 选择 "Import Git Repository"
3. 选择你的仓库
4. 点击 "Deploy"

### 3. 完成！

现在每次你执行：
```bash
git push origin main
```

Vercel 会自动检测到代码变更并开始部署。

---

## 🔍 验证自动部署是否工作

### 方法一：查看 Vercel Dashboard
1. 访问 [Vercel Dashboard](https://vercel.com/dashboard)
2. 进入你的项目
3. 查看 "Deployments" 标签
4. 每次推送后应该看到新的部署

### 方法二：查看 GitHub
1. 在 GitHub 仓库页面
2. 点击 "Actions" 标签（如果使用方式二）
3. 查看工作流执行历史

### 方法三：测试推送
```bash
# 做一个小的修改
echo "// Auto deploy test $(date)" >> app/page.tsx
git add .
git commit -m "测试自动部署"
git push origin main

# 等待 1-2 分钟，然后检查 Vercel Dashboard
```

---

## ⚙️ 高级配置

### 自定义部署分支

默认情况下，只有 `main` 或 `master` 分支会触发生产部署。

**Vercel GitHub 集成方式：**
- 在 Vercel 项目设置 → Git → Production Branch
- 可以修改为其他分支

**GitHub Actions 方式：**
- 编辑 `.github/workflows/deploy-vercel.yml`
- 修改 `branches` 配置

### 环境变量管理

1. **在 Vercel Dashboard 配置**
   - 项目 → Settings → Environment Variables
   - 可以为不同环境（Production、Preview、Development）设置不同变量

2. **使用 .env 文件（本地开发）**
   ```bash
   # 创建 .env.local（已加入 .gitignore）
   echo "NEXT_PUBLIC_API_URL=https://api.example.com" > .env.local
   ```

### 部署通知

Vercel 支持多种通知方式：
- Email
- Slack
- Discord
- Webhook

在项目设置 → Notifications 中配置。

---

## 🐛 常见问题

### Q: 推送代码后没有自动部署？

**检查清单：**
1. ✅ 确认代码已推送到 `main` 或 `master` 分支
2. ✅ 检查 Vercel 项目是否已连接 GitHub 仓库
3. ✅ 查看 Vercel Dashboard 的 Deployments 页面
4. ✅ 检查 GitHub 仓库设置中的 Webhooks（Vercel 集成方式）

### Q: 部署失败怎么办？

1. **查看部署日志**
   - Vercel Dashboard → 项目 → Deployments → 点击失败的部署
   - 查看详细的错误信息

2. **常见错误：**
   - 构建错误：检查 `npm run build` 是否在本地成功
   - 依赖问题：确保 `package.json` 和 `package-lock.json` 已提交
   - 环境变量缺失：检查是否所有必需的环境变量都已配置

### Q: 如何回滚到之前的版本？

1. 在 Vercel Dashboard → Deployments
2. 找到之前的成功部署
3. 点击 "..." → "Promote to Production"

### Q: Pull Request 预览环境不工作？

- 确保在 Vercel 项目设置中启用了 "Preview Deployments"
- 检查 GitHub 仓库的 Webhooks 配置

---

## 📚 相关资源

- [Vercel 文档](https://vercel.com/docs)
- [Next.js 部署文档](https://nextjs.org/docs/app/building-your-application/deploying)
- [GitHub Actions 文档](https://docs.github.com/en/actions)

---

## ✅ 总结

**推荐使用方式一（Vercel GitHub 集成）**，因为：
- ✅ 设置最简单，只需 2 分钟
- ✅ 无需配置 GitHub Secrets
- ✅ Vercel 自动处理所有部署逻辑
- ✅ 自动创建预览环境
- ✅ 内置 CI/CD 功能

只需在 Vercel 导入 GitHub 仓库，之后每次 `git push` 就会自动部署！
