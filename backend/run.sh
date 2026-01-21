#!/bin/bash
# FastAPI 启动脚本

cd "$(dirname "$0")"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
