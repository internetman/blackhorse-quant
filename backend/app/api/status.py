from fastapi import APIRouter
from app.models import SysStatus
from app.store import store

router = APIRouter()

@router.get("/", response_model=SysStatus)
async def get_status():
    """获取系统状态"""
    return SysStatus(status=store.get_status())

@router.post("/", response_model=SysStatus)
async def set_status(status: SysStatus):
    """设置系统状态"""
    store.set_status(status.status)
    return SysStatus(status=store.get_status())
