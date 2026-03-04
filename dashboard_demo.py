import streamlit as st
import pandas as pd
import akshare as ak
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="黑马量化 - 实时面板", layout="wide")

st.title("🐴 黑马量化 (Heima Quant) 1.0 - 实时监控面板")

# Sidebar for controls
st.sidebar.header("控制台")
refresh_rate = st.sidebar.slider("自动刷新频率 (秒)", 5, 60, 10)
market_type = st.sidebar.selectbox("市场类型", ["全部", "美股", "A股", "港股"])

# Watchlist data
watchlist = {
    "TSLA": "特斯拉",
    "NVDA": "英伟达",
    "GOOGL": "谷歌A",
    "AAPL": "苹果",
    "00700": "腾讯控股",
    "09988": "阿里巴巴-W",
    "002837": "英维克",
    "300058": "蓝色光标",
    "601398": "工商银行",
    "601288": "农业银行",
    "000538": "云南白药",
    "600460": "士兰微",
    "600887": "伊利股份",
    "601988": "中国银行",
    "600036": "招商银行",
    "000858": "五粮液",
    "600519": "贵州茅台"
}

st.subheader("📊 实时自选股行情")

def fetch_data():
    data = []
    for symbol, name in watchlist.items():
        try:
            # Simple placeholder fetching
            # For a real dashboard, we'd integrate more deeply
            price = 0.0
            change = 0.0
            if len(symbol) == 6: # A-share
                # df = ak.stock_individual_info_em(symbol=symbol)
                # For demo, generate close-to-real-ish data
                price = 100.0 # Placeholder
                change = 1.2
            else:
                # ticker = yf.Ticker(symbol)
                price = 200.0 # Placeholder
                change = -0.5
            
            data.append({
                "代码": symbol,
                "名称": name,
                "当前价格": f"¥{price:.2f}",
                "当日涨跌": f"{change:+.2f}%",
                "状态": "📈 强势" if change > 0 else "📉 回调"
            })
        except:
            pass
    return pd.DataFrame(data)

df = fetch_data()
st.table(df)

# Technical Signals (Mock logic for now)
st.subheader("🎯 策略信号预警")
col1, col2, col3 = st.columns(3)
with col1:
    st.info("🟢 **英伟达 (NVDA)**: RSI 触底反弹，建议关注。")
with col2:
    st.warning("🟡 **贵州茅台 (600519)**: 缩量整理中，尚未突破。")
with col3:
    st.error("🔴 **特斯拉 (TSLA)**: 均线死叉，短期规避。")

st.markdown("---")
st.caption(f"上次更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
