from app.engine import engine_loop
from app.real_engine import engine_loop as real_engine_loop
import os

# 决定使用哪个引擎逻辑
USE_REAL_DATA = os.getenv("USE_REAL_DATA", "true").lower() == "true"

def get_engine_loop():
    if USE_REAL_DATA:
        print("💡 Using REAL DATA engine loop")
        return real_engine_loop
    else:
        print("💡 Using SIMULATED engine loop")
        return engine_loop
