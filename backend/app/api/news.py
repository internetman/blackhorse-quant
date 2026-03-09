"""个股新闻接口 stub。正式可接 akshare stock_news_em。"""
from fastapi import APIRouter, Query

router = APIRouter()

# Mock 新闻：按 symbol 前缀匹配（如 600519 匹配 600519.SH）
MOCK_NEWS: list[tuple[str, str, str]] = [
    ("600519", "贵州茅台 2024 年经营稳健，渠道库存良性", "2025-01-20"),
    ("600519", "白酒板块估值修复，高端酒需求平稳", "2025-01-18"),
    ("300750", "宁德时代与某车企签署长期供货协议", "2025-01-19"),
    ("300750", "动力电池价格企稳，行业集中度提升", "2025-01-17"),
    ("601318", "中国平安披露年度业绩预告", "2025-01-20"),
    ("600036", "招商银行四季度净息差环比持平", "2025-01-19"),
    ("000858", "五粮液春节动销表现符合预期", "2025-01-18"),
    ("002594", "比亚迪 1 月新能源车销量同比大增", "2025-01-20"),
    ("601012", "隆基绿能发布新一代组件产品", "2025-01-17"),
    ("600900", "长江电力年度发电量创历史新高", "2025-01-19"),
]


@router.get("/")
async def get_news(
    symbol: str = Query(..., alias="symbol"),
    limit: int = Query(10, ge=1, le=20),
):
    symbol = (symbol or "").upper().strip()
    code = symbol.split(".")[0] if "." in symbol else symbol
    out = []
    for sym_prefix, title, pub_date in MOCK_NEWS:
        if sym_prefix == code:
            out.append({"title": title, "date": pub_date, "summary": ""})
            if len(out) >= limit:
                break
    if not out:
        out = [{"title": "暂无该股票相关新闻", "date": "", "summary": "接入 akshare 后可展示实时新闻"}]
    return out
