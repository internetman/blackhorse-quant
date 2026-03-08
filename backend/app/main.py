import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import recommendations, watchlist, reviews, positions, auth, admin

app = FastAPI(
    title="黑马自选 API",
    description="私有股票圈子 AI 辅助决策系统",
    version="1.1.0",
)

allowed_origins_env = os.getenv("ALLOWED_ORIGINS", "")
if allowed_origins_env:
    allowed_origins = [o.strip() for o in allowed_origins_env.split(",")]
else:
    allowed_origins = ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommendations.router, prefix="/api/recommendations", tags=["建议"])
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["自选股"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["复盘"])
app.include_router(positions.router, prefix="/api/positions", tags=["持仓"])
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理"])


@app.get("/")
async def root():
    return {"message": "黑马自选 API 服务运行中", "version": "1.1.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/api/circle/")
async def get_circle():
    from app.store import store
    return store.circle
