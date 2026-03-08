# 黑马自选 部署清单

按顺序完成下面步骤即可上线。**需要你提供的内容**在每一步里会写明。

---

## 准备（先确认这些）

- [ ] 代码已推送到 **GitHub**：<https://github.com/internetman/blackhorse-quant>
- [ ] 有 **Vercel** 账号（[vercel.com](https://vercel.com) 用 GitHub 登录即可）
- [ ] 有 **Railway** 账号（[railway.app](https://railway.app) 用 GitHub 登录即可）

**不需要提前准备**：域名、信用卡（Vercel/Railway 免费额度够用）

**若你以前已经连过 Vercel**：仓库已绑定的话，**每次 push 到 main 都会自动部署前端**，无需再“导入项目”。你只需要在 Vercel 里确认/设置好环境变量 `NEXT_PUBLIC_API_URL`（见第二步），以及把**后端**部署到 Railway（第一步）。

---

## 第一步：部署后端（Railway）

1. 打开 [Railway](https://railway.app) → 登录 → **New Project**
2. 选 **Deploy from GitHub repo**，选中你的 `blackhorse-quant` 仓库（若未列出，先点 **Configure GitHub App** 授权）
3. 部署成功后，在项目里选中刚创建的服务 → **Settings**：
   - **Root Directory** 设为：`backend`
   - **Start Command** 可留空（已用 `railway.json` 配置）或填：  
     `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. 在 **Settings** → **Networking** → **Generate Domain**，生成一个公网地址，例如：  
   `https://blackhorse-quant-production.up.railway.app`
5. 浏览器访问：  
   `https://你的域名/health`  
   应看到 `{"status":"healthy"}`

**请把上面第 4 步里的「你的后端域名」记下来**，下一步要填到 Vercel。

---

## 第二步：部署前端（Vercel）

**若你已连过 Vercel（push 即自动部署）**：  
→ 打开 Vercel 里该项目的 **Settings** → **Environment Variables**，添加或修改：
- **Name**: `NEXT_PUBLIC_API_URL`
- **Value**: 第一步里记下的后端地址（**不要带末尾斜杠**）  
保存后到 **Deployments** 里对最新一次部署点 **Redeploy**，让新环境变量生效。

**若是第一次用 Vercel 部署这个仓库**：
1. 打开 [Vercel](https://vercel.com) → **Add New** → **Project**
2. 从 GitHub 选中 `internetman/blackhorse-quant`
3. **Root Directory** 保持默认（不要改成 backend）
4. 在 **Environment Variables** 里添加：`NEXT_PUBLIC_API_URL` = 你的后端地址（无尾斜杠）
5. 点击 **Deploy**，之后每次 push 到 main 都会自动部署

---

## 第三步：验证

1. 打开 Vercel 给你的前端地址
2. 应跳转到「加入圈子」页，邀请码填 `HM2026A`，昵称随意，点「加入圈子」
3. 能进入「每日建议」页面并看到 8 只股票建议 → 说明前后端已打通

若前端报错「无法连接后端」或一直加载：
- 检查 Vercel 环境变量 `NEXT_PUBLIC_API_URL` 是否等于 Railway 的后端域名（无尾斜杠）
- 检查后重新 **Redeploy** 一次前端

---

## 可选：自定义域名

- **Vercel**：在项目 **Settings** → **Domains** 里添加你的域名并按提示解析
- **Railway**：一般用默认域名即可；若后端要绑域名，在 **Settings** → **Networking** 里配置

---

## 需要我提供什么？（汇总）

| 步骤 | 你需要提供 |
|------|------------|
| 准备 | GitHub 仓库已存在且代码已 push；Vercel、Railway 已注册 |
| 第一步 | 无（按上面操作即可）；完成后**把后端域名发给我**（若需要我帮你检查） |
| 第二步 | 把后端的**完整域名**填到 Vercel 的 `NEXT_PUBLIC_API_URL`（例如 `https://xxx.up.railway.app`） |
| 第三步 | 无（自己点一点验证） |

部署过程中任何一步报错，把**报错截图或文案**发给我即可。
