# Railway 设置根目录详细步骤

## 重要提示

**根目录（Root Directory）设置在服务（Service）级别，不在项目（Project）设置中！**

## 正确步骤

### 步骤 1：进入服务（Service）设置

1. 在 Railway Dashboard 中，你当前看到的是 **Project Settings**（项目设置）
2. 需要先进入 **Service**（服务）设置：
   - 在左侧导航栏或顶部，找到你的服务名称（可能是 `blackhorse-quant-production` 或类似名称）
   - **或者** 点击项目名称旁边的下拉菜单，选择服务
   - **或者** 在项目概览页面，点击具体的服务卡片

### 步骤 2：找到服务设置

进入服务后：
1. 点击服务页面顶部的 **Settings** 标签
2. 在服务设置页面中，你会看到不同的设置选项

### 步骤 3：设置根目录

在服务设置页面中，找到以下选项之一：

**选项 A：在 "Source" 或 "Build" 部分**
- 查找 **Root Directory** 或 **Root Dir** 字段
- 输入：`backend`
- 保存

**选项 B：在 "Deploy" 部分**
- 查找 **Root Directory** 设置
- 输入：`backend`
- 保存

**选项 C：如果找不到 Root Directory 选项**

1. 查看是否有 **"Variables"** 标签
2. 或者查看 **"Deploy"** 标签下的设置
3. 或者尝试以下方法：

### 替代方法：使用 railway.json 配置文件

如果界面中找不到 Root Directory 设置，可以：

1. **确保 `backend/railway.json` 文件已提交到 GitHub**
   - 文件路径：`backend/railway.json`
   - 内容应该包含根目录配置

2. **在服务设置中查找 "Source" 或 "Git" 相关设置**
   - 可能需要重新连接 GitHub 仓库
   - 在连接时指定根目录为 `backend`

### 步骤 4：设置启动命令

在同一个服务设置页面中：

1. 找到 **Start Command** 或 **Command** 字段
2. 设置为：`uvicorn app.main:app --host 0.0.0.0 --port $PORT`
3. 保存

### 步骤 5：重新部署

1. 进入 **Deployments** 标签
2. 点击 **Redeploy** 或等待自动重新部署

## 如果仍然找不到

### 方法 1：检查服务类型

确保你选择的是正确的服务：
- 应该是一个 **Web Service**（不是 Database 或其他类型）
- 服务名称可能包含 "production" 或 "backend"

### 方法 2：使用 Railway CLI

如果界面找不到设置，可以使用命令行：

```bash
# 安装 Railway CLI
npm i -g @railway/cli

# 登录
railway login

# 进入 backend 目录
cd backend

# 初始化（如果还没有）
railway init

# 设置根目录（通过环境变量或配置）
railway variables
```

### 方法 3：删除并重新创建服务

如果配置混乱，可以：

1. 在项目设置中删除当前服务
2. 创建新服务：
   - 点击 **+ New** → **GitHub Repo**
   - 选择你的仓库
   - **在创建时**，会有一个选项让你设置根目录
   - 设置为 `backend`
   - 设置启动命令：`uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## 界面导航提示

Railway 的界面结构：
```
Project (项目)
  └── Service (服务) ← 在这里设置根目录
      ├── Deployments (部署)
      ├── Metrics (指标)
      ├── Logs (日志)
      └── Settings (设置) ← 根目录在这里
          ├── Source (源代码)
          ├── Build (构建)
          ├── Deploy (部署)
          └── Variables (变量)
```

## 快速检查

- [ ] 已进入服务（Service）页面，不是项目（Project）页面
- [ ] 在服务设置中找到了 Root Directory 字段
- [ ] 已设置为 `backend`
- [ ] 已设置启动命令
- [ ] 已重新部署

## 需要帮助？

如果仍然找不到，请告诉我：
1. 你在 Railway 界面中看到的标签页有哪些？
2. 服务设置页面显示了哪些选项？
3. 是否有 "Source"、"Build"、"Deploy" 等标签？

我可以根据你看到的界面提供更具体的指导。
