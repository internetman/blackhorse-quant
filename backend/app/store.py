from datetime import date, datetime
from app.models import (
    User, Circle, WatchItem, Recommendation, DailySummary,
    RecommendationsResponse, Review, ReviewStats, PrivatePosition,
)
import uuid


class Store:
    def __init__(self):
        today = date.today().isoformat()

        self.circle = Circle(
            id="circle_001",
            name="老王的黑马圈",
            inviteCode="HM2026A",
            memberCount=6,
        )

        self.users: list[User] = [
            User(id="u1", nickname="老王", role="leader", joinedAt="2026-02-10"),
            User(id="u2", nickname="大李", role="member", joinedAt="2026-02-15"),
            User(id="u3", nickname="小张", role="member", joinedAt="2026-02-18"),
            User(id="u4", nickname="阿强", role="member", joinedAt="2026-03-01"),
            User(id="u5", nickname="老赵", role="member", joinedAt="2026-03-03"),
            User(id="u6", nickname="管理员", role="admin", joinedAt="2026-02-10"),
        ]

        self.watchlist: list[WatchItem] = [
            WatchItem(id="w1", symbol="600519.SH", name="贵州茅台", reason="白酒龙头，长期底仓候选", addedBy="u1", addedByName="老王", addedByRole="leader", addedAt="2026-02-15"),
            WatchItem(id="w2", symbol="300750.SZ", name="宁德时代", reason="新能源龙头，跟踪产能扩张", addedBy="u2", addedByName="大李", addedByRole="member", addedAt="2026-02-18"),
            WatchItem(id="w3", symbol="601318.SH", name="中国平安", reason="低估值金融，分红考虑", addedBy="u1", addedByName="老王", addedByRole="leader", addedAt="2026-02-20"),
            WatchItem(id="w4", symbol="600036.SH", name="招商银行", reason="银行股代表，观察经济复苏", addedBy="u3", addedByName="小张", addedByRole="member", addedAt="2026-03-01"),
            WatchItem(id="w5", symbol="000858.SZ", name="五粮液", reason="白酒第二梯队，估值修复", addedBy="u1", addedByName="老王", addedByRole="leader", addedAt="2026-03-02"),
            WatchItem(id="w6", symbol="601012.SH", name="隆基绿能", reason="光伏龙头，行业触底判断", addedBy="u4", addedByName="阿强", addedByRole="member", addedAt="2026-03-05"),
            WatchItem(id="w7", symbol="002594.SZ", name="比亚迪", reason="新能源车龙头，出海逻辑", addedBy="u1", addedByName="老王", addedByRole="leader", addedAt="2026-02-16"),
            WatchItem(id="w8", symbol="600900.SH", name="长江电力", reason="红利资产，防御配置", addedBy="u5", addedByName="老赵", addedByRole="member", addedAt="2026-03-06"),
        ]

        self.recommendations: list[Recommendation] = [
            Recommendation(id="rec_001_600519", symbol="600519.SH", name="贵州茅台", date=today, action="可交易", bias="偏低吸", confidence="高", pricePlan="关注 1680-1695 区间，止盈参考 1720-1750，跌破 1660 离场", summary="回落至支撑位附近，可轻仓低吸试错。", reasons=["短线回调幅度已足够，性价比回升", "量能温和缩小，恐慌抛压不大", "5日均线仍保持上升趋势"], risks=["大盘如继续走弱可能补跌"], invalidCondition="若强势放量站稳 1720，低吸结论转为突破跟随", reviewAt="T+1", generatedAt=datetime.now().isoformat()),
            Recommendation(id="rec_001_300750", symbol="300750.SZ", name="宁德时代", date=today, action="观望", bias="暂不参与", confidence="中", pricePlan="站上 165 确认突破再考虑跟随，下方支撑 148", summary="横盘震荡中，无明确方向，等待突破确认。", reasons=["均线缠绕，多空分歧较大", "成交量持续萎缩，市场观望情绪浓"], risks=["跌破 148 支撑则转为看空"], invalidCondition="放量突破 165 则观望转为可交易", reviewAt="T+1", generatedAt=datetime.now().isoformat()),
            Recommendation(id="rec_001_601318", symbol="601318.SH", name="中国平安", date=today, action="风险升高", bias="偏减仓", confidence="高", pricePlan="反弹至 44-45 可考虑减仓，跌破 42.5 需果断止损", summary="连续下跌后反弹乏力，风险信号增多。", reasons=["跌破 20 日均线且未收回", "资金面持续流出", "MACD 死叉形成"], risks=["若跌破 42.5 可能加速下行", "板块整体偏弱"], invalidCondition="若强势收复 45 并站稳，风险预警解除", reviewAt="T+1", generatedAt=datetime.now().isoformat()),
            Recommendation(id="rec_001_600036", symbol="600036.SH", name="招商银行", date=today, action="可交易", bias="偏突破", confidence="中", pricePlan="突破 38.5 可跟进，目标 40-41，跌破 37 止损", summary="放量测试前高，突破概率较大。", reasons=["连续三日温和放量", "站上所有短期均线"], risks=["银行板块整体估值已修复一轮"], invalidCondition="缩量回落至 37 以下则突破失败", reviewAt="T+1", generatedAt=datetime.now().isoformat()),
            Recommendation(id="rec_001_000858", symbol="000858.SZ", name="五粮液", date=today, action="观望", bias="暂不参与", confidence="中", pricePlan="等待回踩 135 支撑后再评估，追高性价比不足", summary="短线涨幅过大，追高风险升高，等待回调。", reasons=["近 5 日累计涨幅超 8%", "量价有背离迹象"], risks=["获利盘回吐压力较大"], invalidCondition="放量突破 150 则趋势加速", reviewAt="T+1", generatedAt=datetime.now().isoformat()),
            Recommendation(id="rec_001_601012", symbol="601012.SH", name="隆基绿能", date=today, action="观望", bias="暂不参与", confidence="低", pricePlan="底部区域震荡中，短期无明确信号", summary="行业基本面未见拐点，继续等待。", reasons=["光伏行业仍处于产能过剩阶段", "股价虽低但趋势未反转"], risks=["行业政策变化可能带来短期波动"], invalidCondition="若出现行业政策利好或业绩超预期", reviewAt="T+3", generatedAt=datetime.now().isoformat()),
            Recommendation(id="rec_001_002594", symbol="002594.SZ", name="比亚迪", date=today, action="可交易", bias="偏低吸", confidence="高", pricePlan="回踩 280-285 可分批建仓，目标 310+，跌破 270 止损", summary="出海数据持续超预期，回调即是机会。", reasons=["海外销量连续 3 月创新高", "技术面 60 日均线强支撑", "机构持续加仓"], risks=["短期涨幅偏大，注意节奏"], invalidCondition="若跌破 270 则中期趋势破坏", reviewAt="T+1", generatedAt=datetime.now().isoformat()),
            Recommendation(id="rec_001_600900", symbol="600900.SH", name="长江电力", date=today, action="观望", bias="暂不参与", confidence="中", pricePlan="高位横盘中，等待方向选择", summary="红利资产估值已充分，短期上行空间有限。", reasons=["股价处于历史高位区间", "股息率已降至 3% 以下"], risks=["利率上行可能压制红利资产估值"], invalidCondition="若市场风险偏好大幅下降", reviewAt="T+3", generatedAt=datetime.now().isoformat()),
        ]

        self.reviews: list[Review] = [
            Review(id="rev_001", recommendationId="rec_prev_600519", symbol="600519.SH", name="贵州茅台", reviewType="T+1", reviewDate=today, originalAction="观望", originalSummary="横盘震荡中，等待回调确认信号", priceAtRecommend=1705, priceAtReview=1710, priceChange="+0.3%", verdict="有效", explanation="观望正确，未出现明确买入信号，持续震荡", generatedAt=datetime.now().isoformat()),
            Review(id="rev_002", recommendationId="rec_prev_601318", symbol="601318.SH", name="中国平安", reviewType="T+1", reviewDate=today, originalAction="可交易", originalSummary="超跌反弹位，可试探性买入", priceAtRecommend=44.2, priceAtReview=43.7, priceChange="-1.1%", verdict="失效", explanation="判断超跌反弹但实际继续下跌，支撑位失守", generatedAt=datetime.now().isoformat()),
            Review(id="rev_003", recommendationId="rec_prev_002594", symbol="002594.SZ", name="比亚迪", reviewType="T+1", reviewDate=today, originalAction="可交易", originalSummary="出海逻辑强化，可低吸建仓", priceAtRecommend=282, priceAtReview=289, priceChange="+2.5%", verdict="有效", explanation="低吸建议有效，次日涨幅超 2%", generatedAt=datetime.now().isoformat()),
            Review(id="rev_004", recommendationId="rec_prev_600036", symbol="600036.SH", name="招商银行", reviewType="T+3", reviewDate=today, originalAction="观望", originalSummary="等待突破 38 后再跟进", priceAtRecommend=37.5, priceAtReview=38.2, priceChange="+1.9%", verdict="一般", explanation="观望期间缓慢上行，未追到最佳建仓点", generatedAt=datetime.now().isoformat()),
            Review(id="rev_005", recommendationId="rec_prev_000858", symbol="000858.SZ", name="五粮液", reviewType="T+3", reviewDate=today, originalAction="可交易", originalSummary="白酒板块轮动，可适当参与", priceAtRecommend=138, priceAtReview=142, priceChange="+2.9%", verdict="有效", explanation="板块轮动判断正确，3 日内涨幅近 3%", generatedAt=datetime.now().isoformat()),
        ]

        self.review_stats = ReviewStats(total=156, effective=98, neutral=38, ineffective=20, effectiveRate=0.63)

        self.positions: list[PrivatePosition] = [
            PrivatePosition(id="pp1", userId="u3", symbol="600519.SH", name="贵州茅台", level="轻仓", costPrice=1688, notes="2/15 首次建仓，等回调加仓", updatedAt="2026-02-15"),
            PrivatePosition(id="pp2", userId="u3", symbol="002594.SZ", name="比亚迪", level="中仓", costPrice=275, notes="看好出海逻辑，分两批买入", updatedAt="2026-03-05"),
            PrivatePosition(id="pp3", userId="u3", symbol="600036.SH", name="招商银行", level="空仓", costPrice=None, notes="观察中，等待突破 38 再考虑", updatedAt="2026-03-01"),
        ]

    def get_daily_summary(self) -> DailySummary:
        tradable = sum(1 for r in self.recommendations if r.action == "可交易")
        risky = sum(1 for r in self.recommendations if r.action in ("风险升高", "不建议交易"))
        watch = len(self.recommendations) - tradable - risky
        return DailySummary(total=len(self.recommendations), tradable=tradable, watch=watch, risky=risky)

    def add_user(self, nickname: str, invite_code: str) -> User | None:
        if invite_code != self.circle.inviteCode:
            return None
        user = User(
            id=f"u_{uuid.uuid4().hex[:8]}",
            nickname=nickname,
            role="member",
            joinedAt=date.today().isoformat(),
        )
        self.users.append(user)
        self.circle.memberCount = len(self.users)
        return user

    def add_watch_item(self, symbol: str, name: str, reason: str, user: User) -> WatchItem:
        item = WatchItem(
            id=f"w_{uuid.uuid4().hex[:8]}",
            symbol=symbol,
            name=name,
            reason=reason,
            addedBy=user.id,
            addedByName=user.nickname,
            addedByRole=user.role,
            addedAt=date.today().isoformat(),
        )
        self.watchlist.append(item)
        return item

    def remove_watch_item(self, item_id: str) -> bool:
        before = len(self.watchlist)
        self.watchlist = [w for w in self.watchlist if w.id != item_id]
        return len(self.watchlist) < before


store = Store()
