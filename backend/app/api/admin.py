from fastapi import APIRouter, HTTPException, Depends
from app.models import User, RoleUpdateRequest, CreateUserRequest
from app.store import store
from app.deps import get_current_user

router = APIRouter()


def _require_admin(current_user: User) -> None:
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="需要管理员权限")


@router.get("/members/", response_model=list[User])
async def get_members(current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    return store.users


@router.post("/users/", response_model=User)
async def create_user(req: CreateUserRequest, current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    if not req.username.strip() or not req.password.strip() or not req.nickname.strip():
        raise HTTPException(status_code=400, detail="用户名、密码、昵称不能为空")
    user = store.add_user_by_admin(req.username.strip(), req.password, req.nickname.strip(), req.role)
    if not user:
        raise HTTPException(status_code=409, detail=f"用户名 {req.username} 已存在")
    return user


@router.patch("/members/{user_id}", response_model=User)
async def update_role(user_id: str, req: RoleUpdateRequest, current_user: User = Depends(get_current_user)):
    _require_admin(current_user)
    for i, u in enumerate(store.users):
        if u.id == user_id:
            updated = u.model_copy(update={"role": req.role})
            store.users[i] = updated
            return updated
    raise HTTPException(status_code=404, detail="用户不存在")
