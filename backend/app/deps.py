from fastapi import Header, HTTPException
from app.models import User
from app.store import store


async def get_current_user(authorization: str = Header(None)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未登录")
    token = authorization[7:]
    user = store.get_user_by_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    return user
