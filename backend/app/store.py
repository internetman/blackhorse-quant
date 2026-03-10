import os
import uuid
import hashlib
import secrets
from datetime import date, datetime
from app.models import User, Circle, WatchItem, Review, PrivatePosition
from app.market_data import normalize_symbol
from app import persistence


def _hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    h = hashlib.sha256((salt + password).encode()).hexdigest()
    return f"{salt}:{h}"


def _verify_password(password: str, stored: str) -> bool:
    salt, h = stored.split(":", 1)
    return hashlib.sha256((salt + password).encode()).hexdigest() == h


def _seed_users(admin_username: str, admin_password: str) -> tuple[list[User], dict[str, str]]:
    users = [
        User(id="u1", username="laowang", nickname="老王", role="leader", joinedAt="2026-02-10"),
        User(id="u2", username="dali", nickname="大李", role="member", joinedAt="2026-02-15"),
        User(id="u3", username="xiaozhang", nickname="小张", role="member", joinedAt="2026-02-18"),
        User(id="u4", username="aqiang", nickname="阿强", role="member", joinedAt="2026-03-01"),
        User(id="u5", username="laozhao", nickname="老赵", role="member", joinedAt="2026-03-03"),
        User(id="u6", username=admin_username, nickname="管理员", role="admin", joinedAt="2026-02-10"),
    ]
    hashes = {
        "u1": _hash_password("laowang123"),
        "u2": _hash_password("dali123"),
        "u3": _hash_password("xiaozhang123"),
        "u4": _hash_password("aqiang123"),
        "u5": _hash_password("laozhao123"),
        "u6": _hash_password(admin_password),
    }
    return users, hashes


def _seed_watchlist() -> list[WatchItem]:
    return [
        WatchItem(id="w1", userId="u1", symbol="600519.SH", name="贵州茅台", reason="白酒龙头，长期底仓候选", addedAt="2026-02-15"),
        WatchItem(id="w2", userId="u2", symbol="300750.SZ", name="宁德时代", reason="新能源龙头，跟踪产能扩张", addedAt="2026-02-18"),
        WatchItem(id="w3", userId="u1", symbol="601318.SH", name="中国平安", reason="低估值金融，分红考虑", addedAt="2026-02-20"),
        WatchItem(id="w4", userId="u3", symbol="600036.SH", name="招商银行", reason="银行股代表，观察经济复苏", addedAt="2026-03-01"),
        WatchItem(id="w5", userId="u1", symbol="000858.SZ", name="五粮液", reason="白酒第二梯队，估值修复", addedAt="2026-03-02"),
        WatchItem(id="w6", userId="u4", symbol="601012.SH", name="隆基绿能", reason="光伏龙头，行业触底判断", addedAt="2026-03-05"),
        WatchItem(id="w7", userId="u1", symbol="002594.SZ", name="比亚迪", reason="新能源车龙头，出海逻辑", addedAt="2026-02-16"),
        WatchItem(id="w8", userId="u5", symbol="600900.SH", name="长江电力", reason="红利资产，防御配置", addedAt="2026-03-06"),
    ]


class Store:
    def __init__(self):
        admin_username = os.environ.get("ADMIN_USERNAME", "admin")
        admin_password = os.environ.get("ADMIN_PASSWORD", "heimaq123")

        self.circle = Circle(id="circle_001", name="老王的黑马圈", memberCount=0)
        self.users = persistence.load_users()
        self.password_hashes = persistence.load_password_hashes()
        if not self.users:
            self.users, self.password_hashes = _seed_users(admin_username, admin_password)
            self.circle.memberCount = len(self.users)
            persistence.save_users(self.users, self.password_hashes)
        else:
            self.circle.memberCount = len(self.users)

        self.tokens: dict[str, str] = {}

        self.watchlist = persistence.load_watchlist()
        if not self.watchlist:
            self.watchlist = _seed_watchlist()
            persistence.save_watchlist(self.watchlist)

        self.reviews = persistence.load_reviews()

        self.positions: list[PrivatePosition] = [
            PrivatePosition(id="pp1", userId="u3", symbol="600519.SH", name="贵州茅台", level="轻仓", costPrice=1688, notes="2/15 首次建仓，等回调加仓", updatedAt="2026-02-15"),
            PrivatePosition(id="pp2", userId="u3", symbol="002594.SZ", name="比亚迪", level="中仓", costPrice=275, notes="看好出海逻辑，分两批买入", updatedAt="2026-03-05"),
            PrivatePosition(id="pp3", userId="u3", symbol="600036.SH", name="招商银行", level="空仓", costPrice=None, notes="观察中，等待突破 38 再考虑", updatedAt="2026-03-01"),
        ]

    def authenticate(self, username: str, password: str) -> User | None:
        for u in self.users:
            if u.username == username and u.isActive:
                stored = self.password_hashes.get(u.id)
                if stored and _verify_password(password, stored):
                    return u
        return None

    def create_token(self, user_id: str) -> str:
        token = secrets.token_urlsafe(32)
        self.tokens[token] = user_id
        return token

    def get_user_by_token(self, token: str) -> User | None:
        user_id = self.tokens.get(token)
        if not user_id:
            return None
        for u in self.users:
            if u.id == user_id and u.isActive:
                return u
        return None

    def remove_token(self, token: str) -> None:
        self.tokens.pop(token, None)

    def add_user_by_admin(self, username: str, password: str, nickname: str, role: str) -> User | None:
        for u in self.users:
            if u.username == username:
                return None
        user = User(
            id=f"u_{uuid.uuid4().hex[:8]}",
            username=username,
            nickname=nickname,
            role=role,
            joinedAt=date.today().isoformat(),
        )
        self.users.append(user)
        self.password_hashes[user.id] = _hash_password(password)
        self.circle.memberCount = len(self.users)
        persistence.save_users(self.users, self.password_hashes)
        return user

    def get_watchlist(self, user_id: str) -> list[WatchItem]:
        return [w for w in self.watchlist if w.userId == user_id and w.isActive]

    def add_watch_item(self, user_id: str, symbol: str, name: str, reason: str = "") -> WatchItem | None:
        symbol_norm = normalize_symbol(symbol)
        for w in self.watchlist:
            if w.userId == user_id and w.symbol == symbol_norm and w.isActive:
                return None
        item = WatchItem(
            id=f"w_{uuid.uuid4().hex[:8]}",
            userId=user_id,
            symbol=symbol_norm,
            name=name.strip() or symbol_norm,
            reason=reason.strip(),
            addedAt=date.today().isoformat(),
        )
        self.watchlist.append(item)
        persistence.save_watchlist(self.watchlist)
        return item

    def remove_watch_item(self, user_id: str, symbol: str) -> bool:
        before = len(self.watchlist)
        symbol_norm = normalize_symbol(symbol)
        self.watchlist = [w for w in self.watchlist if not (w.userId == user_id and w.symbol == symbol_norm)]
        if len(self.watchlist) < before:
            persistence.save_watchlist(self.watchlist)
        return len(self.watchlist) < before


store = Store()
