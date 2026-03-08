from fastapi import APIRouter, HTTPException
from app.models import User, RoleUpdateRequest
from app.store import store

router = APIRouter()


@router.get("/members/", response_model=list[User])
async def get_members():
    return store.users


@router.patch("/members/{user_id}", response_model=User)
async def update_role(user_id: str, req: RoleUpdateRequest):
    for i, u in enumerate(store.users):
        if u.id == user_id:
            updated = u.model_copy(update={"role": req.role})
            store.users[i] = updated
            return updated
    raise HTTPException(status_code=404, detail="用户不存在")


@router.get("/invite/")
async def get_invite():
    return {"inviteCode": store.circle.inviteCode}
