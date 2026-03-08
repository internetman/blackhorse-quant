from fastapi import APIRouter, HTTPException, Depends, Header
from app.models import LoginRequest, User
from app.store import store
from app.deps import get_current_user

router = APIRouter()


@router.post("/login/")
async def login(req: LoginRequest):
    user = store.authenticate(req.username, req.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = store.create_token(user.id)
    return {"user": user, "token": token}


@router.get("/me/", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user


@router.post("/logout/")
async def logout(authorization: str = Header(None)):
    if authorization and authorization.startswith("Bearer "):
        store.remove_token(authorization[7:])
    return {"message": "已退出"}
