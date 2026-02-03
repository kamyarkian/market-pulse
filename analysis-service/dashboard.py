import streamlit as st
import pandas as pd
import time
import plotly.graph_objects as go
import yfinance as yf
import requests
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from dotenv import load_dotenv

# ==========================================
# 1. SECURITY & INFRA UPLINK 🔐
# ==========================================
current_dir = Path.cwd()
env_path = current_dir / 'infra' / '.env'
load_dotenv(dotenv_path=env_path)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
SYSTEM_PASSWORD = os.getenv('SYSTEM_PASSWORD')

# ==========================================
# 2. SYSTEM CONFIGURATION (WALL STREET)
# ==========================================
SYSTEM_NAME = "YAMIN"
VERSION = "v19.1 (SECURED / WALL STREET)"
AUTHOR = "KAMYAR KIAN . IO"

# INSTITUTIONAL COLOR PALETTE
ICE_WHITE = "#FFFFFF"
ACCENT_CYAN = "#00E5FF" 
DEEP_BLUE = "#2962FF"
BG_VOID = "#050608"

# WALL STREET CLASSIC GREEN & RED
WS_GREEN = "#089981" 
WS_RED = "#F23645"   

# ==========================================
# 3. UI ARCHITECTURE (CSS)
# ==========================================
st.set_page_config(page_title=f"YAMIN | {AUTHOR}", page_icon="🐺", layout="wide", initial_sidebar_state="collapsed")

st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;700&family=Rajdhani:wght@500;700;800&display=swap');
    
    .stApp {{ background-color: {BG_VOID}; font-family: 'Rajdhani', sans-serif; overflow: hidden; }}
    
    /* YAMIN CENTERED TITLE */
    .title-flex-container {{
        display: flex; align-items: center; justify-content: center;
        margin-top: 5px; margin-bottom: 20px;
    }}
    h1 {{
        font-family: 'Rajdhani', sans-serif; font-weight: 800; font-size: 85px !important;
        letter-spacing: 12px; color: {ICE_WHITE}; margin: 0; line-height: 1;
        text-shadow: 0 0 50px rgba(255, 255, 255, 0.4);
    }}

    .pulse-y {{
        height: 25px; width: 25px; background-color: {ACCENT_CYAN}; border-radius: 50%;
        box-shadow: 0 0 0 0 rgba(0, 229, 255, 0.7);
        animation: pulse 1.5s infinite; margin-right: 20px;
    }}
    @keyframes pulse {{
        0% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 229, 255, 0.7); }}
        70% {{ transform: scale(1); box-shadow: 0 0 0 20px rgba(0, 229, 255, 0); }}
        100% {{ transform: scale(0.95); box-shadow: 0 0 0 0 rgba(0, 229, 255, 0); }}
    }}

    /* LIQUIDITY CLOCKS */
    .vertical-clocks {{
        position: absolute; top: 5px; right: 15px; display: flex; flex-direction: column;
        gap: 8px; font-family: 'JetBrains Mono'; font-size: 14px; color: #444; 
        text-align: right; z-index: 100; background: rgba(0,0,0,0.4); padding: 12px 18px;
        border-right: 3px solid {ACCENT_CYAN}; border-radius: 4px; box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }}
    .market-open {{ color: #888; }}
    .market-open b {{ color: {WS_GREEN}; font-weight: 800; font-size: 16px; margin-left: 10px; text-shadow: 0 0 10px rgba(8, 153, 129, 0.5); }}
    .market-closed {{ color: #444; }}
    .market-closed b {{ color: #555; font-weight: 800; font-size: 16px; margin-left: 10px; }}

    /* CHARTS CONTAINER */
    div.stPlotlyChart {{
        background: rgba(15, 20, 25, 0.8); border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px; transition: 0.3s ease; padding: 5px;
    }}
    div.stPlotlyChart:hover {{ border: 1px solid {ACCENT_CYAN}; box-shadow: 0 0 20px rgba(0, 229, 255, 0.1); }}
    
    /* METRICS */
    div[data-testid="stMetric"] {{
        background: rgba(255, 255, 255, 0.02); border-left: 3px solid {DEEP_BLUE};
        border-radius: 6px; padding: 10px;
    }}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 4. SECURITY GATE (AUTHENTICATION - FIXED UI)
# ==========================================
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    # Using Native Streamlit Columns to Center the Login
    _, col_center, _ = st.columns([1, 1, 1])
    
    with col_center:
        st.markdown("<br><br><br><br>", unsafe_allow_html=True) # Spacer
        st.markdown(f"""
            <div style='text-align: center;'>
                <span style='font-size: 60px;'>🐺</span>
                <h1 style='font-size: 45px !important; letter-spacing: 5px;'>{SYSTEM_NAME} CORE</h1>
                <p style='color: {ACCENT_CYAN}; font-family: JetBrains Mono; margin-bottom: 20px;'>SECURE NETWORK CONNECTION REQUIRED</p>
            </div>
        """, unsafe_allow_html=True)
        
        pwd = st.text_input("COMMAND CODE", type="password", label_visibility="collapsed", placeholder="ENTER COMMAND CODE...")
        
        if st.button("INITIALIZE UPLINK", use_container_width=True):
            if pwd == SYSTEM_PASSWORD:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("ACCESS DENIED. INTRUDER LOGGED.")
    
    st.stop() # HALT ALL EXECUTION HERE UNTIL AUTHENTICATED

# ==========================================
# 5. BACKEND LOGIC (Market Liquidity Hours)
# ==========================================
def get_market_clocks():
    utc = datetime.now(timezone.utc)
    tz_syd = utc + timedelta(hours=11)
    tz_tyo = utc + timedelta(hours=9)
    tz_lon = utc
    tz_nyc = utc - timedelta(hours=5)

    def is_open(tz_time, open_h, close_h):
        return open_h <= tz_time.hour < close_h and tz_time.weekday() < 5 # Mon-Fri

    return [
        {"name": "SYDNEY", "time": tz_syd.strftime("%I:%M"), "open": is_open(tz_syd, 10, 16)},
        {"name": "TOKYO", "time": tz_tyo.strftime("%I:%M"), "open": is_open(tz_tyo, 9, 15)},
        {"name": "LONDON", "time": tz_lon.strftime("%I:%M"), "open": is_open(tz_lon, 8, 16)},
        {"name": "NEW YORK", "time": tz_nyc.strftime("%I:%M"), "open": is_open(tz_nyc, 9, 16)} 
    ]

def broadcast_signal(msg, token, chat_id):
    if not token or not chat_id: return
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        requests.post(url, json={"chat_id": chat_id, "text": msg, "parse_mode": "Markdown"})
    except: pass

@st.cache_data(ttl=30)
def fetch_market_data():
    try:
        df = yf.download("BTC-CAD", period="3d", interval="15m", progress=False)
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        df = df.reset_index().rename(columns={"Datetime": "time", "Date": "time", "Close": "price", "Open": "open", "High": "high", "Low": "low"})
        df['price'] = df['price'].astype(float)
        
        delta = df['price'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        df['rsi'] = 100 - (100 / (1 + (gain / loss)))
        df['macd'] = df['price'].ewm(span=12).mean() - df['price'].ewm(span=26).mean()
        df['macd_h'] = df['macd'] - df['macd'].ewm(span=9).mean()
        return df.tail(80) 
    except: return pd.DataFrame()

# ==========================================
# 6. TITAN INTERFACE (PRO EDITION)
# ==========================================

df = fetch_market_data()
current_price = df.iloc[-1]['price'] if not df.empty else 0

# --- SIDEBAR ---
with st.sidebar:
    st.markdown("### 🐺 NEURAL LINK")
    st.caption("TELEGRAM BROADCAST SYSTEM")
    
    active_token = TELEGRAM_TOKEN
    active_chat = TELEGRAM_CHAT_ID

    if active_token and active_chat:
        st.success("SECURE UPLINK ESTABLISHED")
    else:
        st.error("ENV KEYS MISSING")

    if st.button("📡 TEST CONNECTION"):
        if active_token and active_chat:
            try:
                msg = f"🐺 *YAMIN LIVE FEED*\nSystem Online.\nBTC/CAD: ${current_price:,.2f}"
                requests.post(f"https://api.telegram.org/bot{active_token}/sendMessage", json={"chat_id": active_chat, "text": msg, "parse_mode": "Markdown"})
                st.toast("UPLINK SUCCESS", icon="✅")
            except: st.error("NETWORK ERROR")

    if st.button("🔒 LOGOUT", use_container_width=True):
        st.session_state.authenticated = False
        st.rerun()

# --- SMART LIQUIDITY CLOCKS ---
clks = get_market_clocks()
clock_html = "<div class='vertical-clocks'>"
for city in clks:
    status_class = "market-open" if city["open"] else "market-closed"
    clock_html += f"<div class='{status_class}'>{city['name']} <b>{city['time']}</b></div>"
clock_html += "</div>"
st.markdown(clock_html, unsafe_allow_html=True)

# --- PERFECT CENTERED TITLE ---
st.markdown(f"""
    <div class='title-flex-container'>
        <div class='pulse-y'></div><h1>{SYSTEM_NAME}</h1>
    </div>
""", unsafe_allow_html=True)

# --- METRICS & DECISION ROW ---
c_met1, c_met2, c_sig = st.columns([3, 3, 4])

if not df.empty:
    last = df.iloc[-1]
    
    decision = "HOLD"; dec_color = "#444"
    if last['rsi'] < 35: 
        decision = "BUY"; dec_color = WS_GREEN
        if active_token: broadcast_signal(f"🐺 **YAMIN ALERT**\n🟢 Signal: BUY\nPrice: ${last['price']:,.2f}", active_token, active_chat)
    elif last['rsi'] > 65: 
        decision = "SELL"; dec_color = WS_RED

    with c_met1:
        st.metric("EQUITY", f"$10,000.00")
        st.metric("RSI STRENGTH", f"{last['rsi']:.1f}")
    
    with c_met2:
        st.metric("BTC PRICE", f"${last['price']:,.0f}")
        st.metric("AI SENTIMENT", "BULLISH" if last['macd_h'] > 0 else "BEARISH")

    with c_sig:
        st.markdown(f"""
            <div style='border: 2px solid {dec_color}; border-radius: 8px; text-align: center; padding: 15px; background: rgba(0,0,0,0.6); box-shadow: 0 0 30px {dec_color}30; margin-top: 15px;'>
                <div style='color:#888; font-size:12px; font-family:JetBrains Mono;'>DECISION MATRIX</div>
                <div style='color:{dec_color}; font-size:40px; font-weight:800; letter-spacing:2px;'>{decision}</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # --- PERFECT FIT CHARTS ---
    fig_p = go.Figure(data=[go.Candlestick(x=df['time'], open=df['open'], high=df['high'], low=df['low'], close=df['price'], increasing_line_color=WS_GREEN, decreasing_line_color=WS_RED)])
    fig_p.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#666'), margin=dict(t=0, b=0, l=0, r=0), xaxis=dict(showgrid=False, rangeslider_visible=False, visible=False), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'), height=400)
    st.plotly_chart(fig_p, use_container_width=True)

    col_l, col_r = st.columns(2)
    with col_l:
        fig_r = go.Figure(go.Scatter(x=df['time'], y=df['rsi'], line=dict(color=ICE_WHITE, width=1.5)))
        fig_r.add_hrect(y0=65, y1=100, fillcolor=WS_RED, opacity=0.1, line_width=0)
        fig_r.add_hrect(y0=0, y1=35, fillcolor=WS_GREEN, opacity=0.1, line_width=0)
        fig_r.add_hline(y=65, line_dash="dash", line_color=WS_RED, line_width=1)
        fig_r.add_hline(y=35, line_dash="dash", line_color=WS_GREEN, line_width=1)
        fig_r.update_layout(title="RSI", title_font=dict(color='#666', size=10), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=25, b=0, l=0, r=0), height=200, xaxis=dict(showgrid=False, visible=False), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)', range=[0, 100]))
        st.plotly_chart(fig_r, use_container_width=True)

    with col_r:
        fig_m = go.Figure(go.Bar(x=df['time'], y=df['macd_h'], marker_color=[WS_GREEN if v >= 0 else WS_RED for v in df['macd_h']]))
        fig_m.update_layout(title="MACD", title_font=dict(color='#666', size=10), plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', margin=dict(t=25, b=0, l=0, r=0), height=200, xaxis=dict(showgrid=False, visible=False), yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.05)'))
        st.plotly_chart(fig_m, use_container_width=True)
else:
    st.error("UPLINK INTERRUPTED.")