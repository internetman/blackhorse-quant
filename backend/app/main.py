from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import positions, trades, status, stats, config
from app.auth import verify_auth
from fastapi import Depends
import threading
import asyncio
from app.engine_selector import get_engine_loop

app = FastAPI(
    title="黑马量化 API",
    description="量化交易策略平台后端 API",
    version="1.0.0"
)

# 配置 CORS
# 允许所有来源（生产环境可以通过环境变量限制）
import os
allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    # 如果设置了环境变量，使用指定的来源
    allowed_origins = [origin.strip() for origin in allowed_origins_env.split(",")]
else:
    # 否则允许所有来源（方便开发和部署）
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由 - 统一添加权限校验
# 只有根路径和健康检查不校验，其他业务接口全部校验
app.include_router(positions.router, prefix="/api/positions", tags=["持仓"], dependencies=[Depends(verify_auth)])
app.include_router(trades.router, prefix="/api/trades", tags=["交易"], dependencies=[Depends(verify_auth)])
app.include_router(status.router, prefix="/api/status", tags=["状态"], dependencies=[Depends(verify_auth)])
app.include_router(stats.router, prefix="/api/stats", tags=["统计"], dependencies=[Depends(verify_auth)])
app.include_router(config.router, prefix="/api/config", tags=["配置"], dependencies=[Depends(verify_auth)])

@app.get("/")
async def root():
    return {"message": "黑马量化 API 服务运行中", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """启动时运行引擎"""
    import sys
    print("🚀 App Startup: Preparing engine...", file=sys.stderr)
    def run_engine():
        print("🧵 Engine Thread: Starting...", file=sys.stderr)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        engine_func = get_engine_loop()
        print(f"⚙️ Running engine function: {engine_func.__name__}", file=sys.stderr)
        loop.run_until_complete(engine_func())
    
    thread = threading.Thread(target=run_engine, daemon=True)
    thread.start()
    print("✅ 引擎启动线程已派出", file=sys.stderr)
