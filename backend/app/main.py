import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import recommendations, watchlist, reviews, positions, auth, admin, stocks, quote, news

app = FastAPI(
    title="黑马自选 API",
    description="我的关注 + AI 买卖建议与复盘（v1.2）",
    version="1.2.0",
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
app.include_router(watchlist.router, prefix="/api/watchlist", tags=["我的关注"])
app.include_router(stocks.router, prefix="/api/stocks", tags=["股票"])
app.include_router(quote.router, prefix="/api/quote", tags=["行情"])
app.include_router(news.router, prefix="/api/news", tags=["新闻"])
app.include_router(reviews.router, prefix="/api/reviews", tags=["复盘"])
app.include_router(positions.router, prefix="/api/positions", tags=["持仓-deprecated"])
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(admin.router, prefix="/api/admin", tags=["用户管理"])


@app.get("/")
async def root():
    return {"message": "黑马自选 API 服务运行中", "version": "1.2.0"}


@app.get("/health")
async def health():
    return {"status": "healthy"}
