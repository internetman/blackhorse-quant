"""
JSON 文件持久化：users、watchlist、reviews。
数据目录为 backend/data/，读写 data/users.json、data/watchlist.json、data/reviews.json。
"""
import json
import os
from pathlib import Path

from app.models import User, WatchItem, Review

# backend/app/persistence.py -> backend/data
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
USERS_PATH = _DATA_DIR / "users.json"
WATCHLIST_PATH = _DATA_DIR / "watchlist.json"
REVIEWS_PATH = _DATA_DIR / "reviews.json"


def _ensure_data_dir() -> None:
    _DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_users() -> list[User]:
    """从 data/users.json 加载用户列表；文件不存在或空则返回空列表。"""
    data = _load_user_data()
    return data["users"]


def load_password_hashes() -> dict[str, str]:
    """从 data/users.json 加载 password_hashes；文件不存在或空则返回空字典。"""
    data = _load_user_data()
    return data["password_hashes"]


def _load_user_data() -> dict:
    if not USERS_PATH.exists():
        return {"users": [], "password_hashes": {}}
    try:
        raw = json.loads(USERS_PATH.read_text(encoding="utf-8"))
        if isinstance(raw, dict):
            users = [User.model_validate(o) for o in raw.get("users", [])]
            hashes = dict(raw.get("password_hashes", {}))
            return {"users": users, "password_hashes": hashes}
        return {"users": [], "password_hashes": {}}
    except Exception:
        return {"users": [], "password_hashes": {}}


def save_users(users: list[User], password_hashes: dict[str, str]) -> None:
    _ensure_data_dir()
    payload = {
        "users": [u.model_dump(mode="json") for u in users],
        "password_hashes": password_hashes,
    }
    USERS_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def load_watchlist() -> list[WatchItem]:
    """从 data/watchlist.json 加载自选列表；文件不存在或空则返回空列表。"""
    if not WATCHLIST_PATH.exists():
        return []
    try:
        raw = json.loads(WATCHLIST_PATH.read_text(encoding="utf-8"))
        return [WatchItem.model_validate(o) for o in (raw if isinstance(raw, list) else [])]
    except Exception:
        return []


def save_watchlist(watchlist: list[WatchItem]) -> None:
    _ensure_data_dir()
    WATCHLIST_PATH.write_text(
        json.dumps([w.model_dump(mode="json") for w in watchlist], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def load_reviews() -> list[Review]:
    """从 data/reviews.json 加载复盘列表；文件不存在或空则返回空列表。"""
    if not REVIEWS_PATH.exists():
        return []
    try:
        raw = json.loads(REVIEWS_PATH.read_text(encoding="utf-8"))
        return [Review.model_validate(o) for o in (raw if isinstance(raw, list) else [])]
    except Exception:
        return []


def save_reviews(reviews: list[Review]) -> None:
    _ensure_data_dir()
    REVIEWS_PATH.write_text(
        json.dumps([r.model_dump(mode="json") for r in reviews], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
