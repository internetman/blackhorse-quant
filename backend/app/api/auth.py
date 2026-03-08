from fastapi import APIRouter, HTTPException
from app.models import JoinRequest, User, Circle
from app.store import store

router = APIRouter()


@router.post("/join/")
async def join_circle(req: JoinRequest):
    user = store.add_user(req.nickname, req.inviteCode)
    if not user:
        raise HTTPException(status_code=400, detail="邀请码无效")
    return {"user": user, "circle": store.circle}


@router.get("/me/", response_model=User)
async def get_me():
    return store.users[0]
