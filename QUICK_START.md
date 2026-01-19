# 🚀 快速开始：GitHub 自动部署到 Vercel

## 最简单的方式（3 步完成）

### 步骤 1: 确保代码在 GitHub

```bash
# 如果还没有推送到 GitHub
git init
git add .
git commit -m "Initial commit"
git remote add origin https://github.com/YOUR_USERNAME/blackhorse-quant.git
git branch -M main
git push -u origin main
```

### 步骤 2: 在 Vercel 导入项目

1. 访问 **[https://vercel.com/new](https://vercel.com/new)**
2. 使用 GitHub 账号登录
3. 点击 **"Import Git Repository"**
4. 选择你的 `blackhorse-quant` 仓库
5. 点击 **"Deploy"**（使用默认设置即可）

### 步骤 3: 完成！

现在每次你执行：
```bash
git push origin main
```

Vercel 会自动检测并部署你的应用！🎉

---

## 验证自动部署

```bash
# 做一个小的修改测试
echo "// 测试 $(date)" >> app/page.tsx
git add .
git commit -m "测试自动部署"
git push origin main

# 等待 1-2 分钟，然后访问 Vercel Dashboard 查看部署状态
```

---

## 查看部署

- **Vercel Dashboard**: [https://vercel.com/dashboard](https://vercel.com/dashboard)
- 每次部署后，Vercel 会给你一个 URL，例如：`https://blackhorse-quant.vercel.app`

---

## 需要帮助？

- 📖 详细指南：[GITHUB_DEPLOY_GUIDE.md](./GITHUB_DEPLOY_GUIDE.md)
- 🔧 高级配置：[DEPLOY.md](./DEPLOY.md)
