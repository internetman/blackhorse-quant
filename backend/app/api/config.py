from fastapi import APIRouter
from app.models import ConfigParams
from app.store import store

router = APIRouter()

@router.get("/", response_model=ConfigParams)
async def get_config():
    """获取配置参数"""
    return store.get_config()

@router.put("/", response_model=ConfigParams)
async def update_config(config: ConfigParams):
    """更新配置参数"""
    store.update_config(**config.model_dump())
    return store.get_config()

@router.patch("/", response_model=ConfigParams)
async def patch_config(updates: dict):
    """部分更新配置参数"""
    current = store.get_config()
    updated = current.model_copy(update=updates)
    store.update_config(**updated.model_dump())
    return store.get_config()
