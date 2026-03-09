"""
股票搜索/联想 API（v1.2）
支持代码前缀、名称前缀、拼音首字母模糊匹配。
"""
from fastapi import APIRouter, Query

router = APIRouter()

# 静态股票列表：symbol, name, 拼音首字母（用于联想）
STOCK_LIST: list[tuple[str, str, str]] = [
    ("600519.SH", "贵州茅台", "GZMT"),
    ("300750.SZ", "宁德时代", "NDSD"),
    ("601318.SH", "中国平安", "ZGPA"),
    ("600036.SH", "招商银行", "ZSYH"),
    ("000858.SZ", "五粮液", "WLY"),
    ("601012.SH", "隆基绿能", "LJLN"),
    ("002594.SZ", "比亚迪", "BYD"),
    ("600900.SH", "长江电力", "CJDL"),
    ("000001.SZ", "平安银行", "PAYH"),
    ("600030.SH", "中信证券", "ZXZQ"),
    ("601166.SH", "兴业银行", "XYYH"),
    ("000333.SZ", "美的集团", "MDJT"),
    ("600276.SH", "恒瑞医药", "HRYY"),
    ("000651.SZ", "格力电器", "GLDQ"),
    ("300059.SZ", "东方财富", "DFCF"),
]


def _match(q: str, symbol: str, name: str, pinyin: str) -> bool:
    q = q.strip().upper()
    if not q:
        return False
    code = symbol.replace(".SH", "").replace(".SZ", "")
    if q.isdigit():
        return code.startswith(q) or q in code
    if q in name:
        return True
    if pinyin.upper().startswith(q) or q in pinyin.upper():
        return True
    return False


@router.get("/search")
async def search_stocks(
    q: str = Query(..., min_length=0),
    limit: int = Query(20, ge=1, le=50),
):
    """股票搜索/联想。q 长度 < 2 时返回空列表。"""
    if len(q.strip()) < 2:
        return []
    results = []
    for symbol, name, pinyin in STOCK_LIST:
        if _match(q, symbol, name, pinyin):
            results.append({"symbol": symbol, "name": name})
            if len(results) >= limit:
                break
    return results
