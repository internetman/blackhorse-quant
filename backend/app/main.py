from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import positions, trades, status, stats, config
import threading
import asyncio
from app.engine import engine_loop

app = FastAPI(
    title="黑马量化 API",
    description="量化交易策略平台后端 API",
    version="1.0.0"
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(positions.router, prefix="/api/positions", tags=["持仓"])
app.include_router(trades.router, prefix="/api/trades", tags=["交易"])
app.include_router(status.router, prefix="/api/status", tags=["状态"])
app.include_router(stats.router, prefix="/api/stats", tags=["统计"])
app.include_router(config.router, prefix="/api/config", tags=["配置"])

@app.get("/")
async def root():
    return {"message": "黑马量化 API 服务运行中", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}

@app.on_event("startup")
async def startup_event():
    """启动时运行引擎"""
    def run_engine():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(engine_loop())
    
    thread = threading.Thread(target=run_engine, daemon=True)
    thread.start()
    print("✅ 引擎已启动")
