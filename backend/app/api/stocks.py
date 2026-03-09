"""
股票搜索/联想 API（v1.2）
支持代码前缀、名称前缀、拼音首字母模糊匹配。
"""
from fastapi import APIRouter, Depends, Query
from app.models import User
from app.deps import get_current_user

router = APIRouter()

# 静态股票列表：symbol, name, 拼音首字母, 拼音全拼（用于联想）
STOCK_LIST: list[tuple[str, str, str, str]] = [
    ("600519.SH", "贵州茅台", "GZMT", "GUIZHOUMAOTAI"),
    ("300750.SZ", "宁德时代", "NDSD", "NINGDESHIDAI"),
    ("601318.SH", "中国平安", "ZGPA", "ZHONGGUOPINGAN"),
    ("600036.SH", "招商银行", "ZSYH", "ZHAOSHANGYINHANG"),
    ("000858.SZ", "五粮液", "WLY", "WULIANGYE"),
    ("601012.SH", "隆基绿能", "LJLN", "LONGJILUNENG"),
    ("002594.SZ", "比亚迪", "BYD", "BIYADI"),
    ("600900.SH", "长江电力", "CJDL", "CHANGJIANGDIANLI"),
    ("000001.SZ", "平安银行", "PAYH", "PINGANYINHANG"),
    ("600030.SH", "中信证券", "ZXZQ", "ZHONGXINZHENGQUAN"),
    ("601166.SH", "兴业银行", "XYYH", "XINGYEYINHANG"),
    ("000333.SZ", "美的集团", "MDJT", "MEIDIJITUAN"),
    ("600276.SH", "恒瑞医药", "HRYY", "HENGRUIYIYAO"),
    ("000651.SZ", "格力电器", "GLDQ", "GELIDIANQI"),
    ("300059.SZ", "东方财富", "DFCF", "DONGFANGCAIFU"),
]


def _match(q: str, symbol: str, name: str, pinyin_initial: str, pinyin_full: str) -> bool:
    q = q.strip().upper()
    if not q:
        return False
    code = symbol.replace(".SH", "").replace(".SZ", "")
    if q.isdigit():
        return code.startswith(q) or q in code
    if q in name:
        return True
    if pinyin_initial.startswith(q) or q in pinyin_initial:
        return True
    if pinyin_full.startswith(q) or q in pinyin_full:
        return True
    return False


@router.get("/search")
async def search_stocks(
    q: str = Query(..., min_length=0),
    limit: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
):
    """股票搜索/联想。q 长度 < 2 时返回空列表。"""
    _ = user
    if len(q.strip()) < 2:
        return []
    results = []
    for symbol, name, pinyin_initial, pinyin_full in STOCK_LIST:
        if _match(q, symbol, name, pinyin_initial, pinyin_full):
            results.append({"symbol": symbol, "name": name})
            if len(results) >= limit:
                break
    return results
