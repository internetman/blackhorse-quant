"""
简单身份验证模块
提供基础的用户名/密码校验，用于保护 API 路由
"""
import os
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from dotenv import load_dotenv

load_dotenv()

# 从环境变量读取，默认给个简单值以防万一
AUTH_USER = os.getenv("AUTH_USER", "admin")
AUTH_PASS = os.getenv("AUTH_PASS", "heimaq123")

security = HTTPBasic()

def verify_auth(credentials: HTTPBasicCredentials = Depends(security)):
    """校验用户名和密码"""
    if credentials.username != AUTH_USER or credentials.password != AUTH_PASS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
