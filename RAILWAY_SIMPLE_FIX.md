# Railway 根目录设置 - 最简单方法

## 问题

Railway 的 Source 页面没有 Root Directory 选项，无法通过 UI 设置。

## 解决方案：使用配置文件 + 重新连接仓库

### 方法 1：重新连接 GitHub 仓库（推荐）

这是最简单的方法，在重新连接时可以设置根目录：

1. **在 Railway Service Settings 的 Source 页面**
   - 找到 "Source Repo" 部分
   - 点击 **"Disconnect"** 按钮（断开当前连接）

2. **重新连接仓库**
   - 点击 **"+ New"** 或 **"Connect Repository"**
   - 选择你的 GitHub 仓库 `internetman/blackhorse-quant`
   - **重要**：在连接配置界面中，查找 **"Root Directory"** 或 **"Working Directory"** 选项
   - 设置为：`backend`
   - 完成连接

3. **设置启动命令**
   - 进入 **Deploy** 页面
   - 在 "Custom Start Command" 中添加：
     ```
     uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```

4. **等待自动部署**

### 方法 2：使用 nixpacks.toml 配置文件

如果方法 1 不行，创建 `nixpacks.toml` 文件：

1. **在项目根目录创建 `nixpacks.toml`**（不是 backend 目录）
2. **内容如下：**
   ```toml
   [phases.setup]
   nixPkgs = ["python311"]

   [phases.install]
   cmds = ["cd backend && pip install -r requirements.txt"]

   [start]
   cmd = "cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
   ```

3. **提交并推送：**
   ```bash
   git add nixpacks.toml
   git commit -m "添加 Railway nixpacks 配置"
   git push
   ```

### 方法 3：删除并重新创建服务（最彻底）

如果以上方法都不行：

1. **删除当前服务**
   - 在 Railway 项目页面
   - 找到当前服务，点击 **⋯** → **Delete**

2. **创建新服务**
   - 点击 **+ New** → **GitHub Repo**
   - 选择仓库 `internetman/blackhorse-quant`
   - **在配置界面中**，查找并设置：
     - **Root Directory**: `backend`
     - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

## 推荐操作顺序

1. ✅ 先尝试 **方法 1**（重新连接仓库）
2. ✅ 如果不行，尝试 **方法 2**（nixpacks.toml）
3. ✅ 最后尝试 **方法 3**（重新创建服务）

## 验证

部署完成后，访问：
- `https://blackhorse-quant-production.up.railway.app/health` → 应返回 `{"status": "healthy"}`
- `https://blackhorse-quant-production.up.railway.app/docs` → 应显示 Swagger UI
