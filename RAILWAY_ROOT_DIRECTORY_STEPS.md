# Railway 设置根目录 - 详细步骤

## 你现在的位置

你在 Railway Service Settings 的 **Deploy** 页面。

## 找到根目录设置

### 方法 1：查看 "Source" 页面（最可能的位置）

1. **在右侧导航栏中，点击 "Source"**
   - 这是最可能包含根目录设置的地方

2. **在 Source 页面中查找：**
   - 查找 **"Root Directory"** 或 **"Root Dir"** 字段
   - 或者查找 **"Working Directory"** 字段
   - 输入：`backend`
   - 保存

### 方法 2：查看 "Build" 页面

如果 Source 页面没有，尝试：

1. **在右侧导航栏中，点击 "Build"**
2. **在 Build 页面中查找：**
   - 查找 **"Root Directory"** 字段
   - 输入：`backend`
   - 保存

### 方法 3：使用 Config-as-code（如果找不到 UI 设置）

如果 Source 和 Build 页面都没有根目录设置，可以使用配置文件：

1. **点击右侧导航栏的 "Config-as-code"**
2. **查看是否显示 "Railway Config File"**
3. **确保 `backend/railway.json` 文件已提交到 GitHub**

## 同时需要设置的启动命令

在 **Deploy** 页面（你当前所在的位置）：

1. **找到 "Custom Start Command" 部分**
2. **点击 "+ Start Command" 按钮**
3. **输入：** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. **保存**

## 完整操作流程

1. ✅ 点击右侧导航栏的 **"Source"**
2. ✅ 查找并设置 **Root Directory** 为 `backend`
3. ✅ 返回 **"Deploy"** 页面
4. ✅ 在 "Custom Start Command" 中添加启动命令
5. ✅ 保存所有更改
6. ✅ 等待自动重新部署

## 如果仍然找不到

请告诉我：
- 在 "Source" 页面看到了哪些选项？
- 是否有 "Root Directory" 或类似的字段？

或者我们可以使用配置文件方法（更简单）。
