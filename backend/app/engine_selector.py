from app.engine import engine_loop
from app.real_engine import engine_loop as real_engine_loop
import os

# 决定使用哪个引擎逻辑
# 如果在 Vercel 环境下，强制使用模拟引擎以确保界面显示正常
IS_VERCEL = os.getenv("VERCEL") == "1"
USE_REAL_DATA = os.getenv("USE_REAL_DATA", "true").lower() == "true"

def get_engine_loop():
    if IS_VERCEL:
        print("💡 Vercel environment detected - Forcing SIMULATED engine loop for UI stability")
        return engine_loop
    elif USE_REAL_DATA:
        print("💡 Using REAL DATA engine loop")
        return real_engine_loop
    else:
        print("💡 Using SIMULATED engine loop")
        return engine_loop
