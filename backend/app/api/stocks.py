"""
股票搜索/联想 API（v1.2）
全 A 股列表启动时加载，支持代码前缀、名称前缀、拼音首字母搜索。
"""
from fastapi import APIRouter, Depends, Query
from app.models import User
from app.deps import get_current_user

router = APIRouter()

# 全 A 股：[(symbol, name, pinyin_initial)]，首次搜索时懒加载
_STOCK_LIST: list[tuple[str, str, str]] = []
_LOADED = False


def _ensure_stock_list() -> None:
    global _STOCK_LIST, _LOADED
    if _LOADED:
        return
    _LOADED = True
    try:
        import akshare as ak
        from pypinyin import lazy_pinyin, Style

        df = ak.stock_info_a_code_name()
        if df is None or df.empty:
            return
        # 列名可能是 code/name 或 代码/名称
        code_col = "code" if "code" in df.columns else "代码"
        name_col = "name" if "name" in df.columns else "名称"
        for _, row in df.iterrows():
            symbol = str(row[code_col]).strip()
            name = str(row[name_col]).strip()
            if not symbol or not name or symbol == "nan":
                continue
            # 拼音首字母
            py_list = lazy_pinyin(name, style=Style.FIRST_LETTER)
            pinyin_initial = "".join(py_list).upper() if py_list else ""
            _STOCK_LIST.append((symbol, name, pinyin_initial))
    except Exception:
        pass


def _match(q: str, symbol: str, name: str, pinyin_initial: str) -> bool:
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
    return False


@router.get("/search")
async def search_stocks(
    q: str = Query(..., min_length=0),
    limit: int = Query(20, ge=1, le=50),
    user: User = Depends(get_current_user),
):
    """股票搜索/联想。q 长度 < 2 时返回空列表。全 A 股列表首次请求时加载。"""
    _ = user
    if len(q.strip()) < 2:
        return []
    _ensure_stock_list()
    results = []
    for symbol, name, pinyin_initial in _STOCK_LIST:
        if _match(q, symbol, name, pinyin_initial):
            results.append({"symbol": symbol, "name": name})
            if len(results) >= limit:
                break
    return results
