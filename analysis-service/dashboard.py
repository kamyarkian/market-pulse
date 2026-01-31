import streamlit as st
import pandas as pd
import psycopg2
import time
import altair as alt
import os
import urllib.parse
import urllib.request
import json
import google.generativeai as genai

# ==========================================
# 1. SYSTEM CONFIGURATION & CREDENTIALS
# ==========================================
# --- TRADING SETTINGS ---
STOP_LOSS_PCT = 0.02
TAKE_PROFIT_PCT = 0.04
RSI_PERIOD = 14
RSI_BUY = 35.0   # Buy Zone
RSI_SELL = 65.0  # Sell Zone

# --- MACD SETTINGS ---
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# --- TELEGRAM SECRETS (Hardcoded) ---
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID =os.getenv('TELEGRAM_CHAT_ID') 
if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
    print("⚠️ WARNING: Telegram keys are missing in .env file!")

# --- DATABASE CREDENTIALS ---
DB_HOST = "postgres"
DB_NAME = "market_db"
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASS = os.getenv('DB_PASSWORD', 'adminpassword')

# ==========================================
# 2. TELEGRAM MODULE (Standard Lib) 🔔
# ==========================================
def send_telegram_alert(message):
    """Sends a notification to your phone using standard Python libraries."""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        # Encode data and send request
        data_encoded = urllib.parse.urlencode(data).encode("utf-8")
        req = urllib.request.Request(url, data=data_encoded)
        with urllib.request.urlopen(req) as response:
            pass # Message sent successfully
    except Exception as e:
        print(f"Telegram Error: {e}")

# ==========================================
# 3. UI SETUP (PROFESSIONAL THEME)
# ==========================================
SYSTEM_NAME = "YAMIN Core"
NODE_NAME = "Sentinel Node"
ICON = "🐺"

st.set_page_config(page_title=SYSTEM_NAME, page_icon=ICON, layout="wide")
st.markdown("""
    <style>
        .stMetric {background-color: #0e1117; padding: 10px; border-radius: 5px; border: 1px solid #262730;}
        .stAlert {background-color: #1c2026; border: 1px solid #363b45; color: #ffffff;}
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 4. SESSION STATE MANAGEMENT
# ==========================================
if 'balance' not in st.session_state: st.session_state.balance = 50000.00
if 'position' not in st.session_state: st.session_state.position = None 
if 'trades' not in st.session_state: st.session_state.trades = []

# ==========================================
# 5. NEURAL LINK (AI CORE)
# ==========================================
def consult_neural_core(price, rsi, macd, macd_signal, balance):
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key: return False, "API Key Missing"
    genai.configure(api_key=api_key)
    
    # Priority: Flash 2.0 -> Lite -> Latest
    model_priority_list = ['gemini-2.0-flash', 'gemini-2.0-flash-lite', 'gemini-flash-latest']
    trend = "BULLISH" if macd > macd_signal else "BEARISH"
    
    for model_name in model_priority_list:
        try:
            model = genai.GenerativeModel(model_name)
            prompt = f"Act as YAMIN Trading AI. Market Data: Price=${price}, RSI={rsi:.1f}, Trend={trend}. Provide 1 concise tactical sentence."
            response = model.generate_content(prompt)
            return True, f"**[{model_name}]** {response.text}"
        except: continue 
    return False, "AI Systems Busy/Limit Reached."

# ==========================================
# 6. DATA ENGINE
# ==========================================
def get_data():
    try:
        conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS)
        query = "SELECT * FROM market_prices ORDER BY timestamp DESC LIMIT 300"
        df = pd.read_sql(query, conn)
        conn.close()
        
        df = df.sort_values(by="timestamp")
        df['price'] = df['price'].astype(float)
        df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # RSI Calculation
        delta = df['price'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(RSI_PERIOD).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(RSI_PERIOD).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        df['rsi'] = df['rsi'].fillna(50)

        # MACD Calculation
        ema12 = df['price'].ewm(span=MACD_FAST, adjust=False).mean()
        ema26 = df['price'].ewm(span=MACD_SLOW, adjust=False).mean()
        df['macd'] = ema12 - ema26
        df['macd_signal'] = df['macd'].ewm(span=MACD_SIGNAL, adjust=False).mean()
        
        return df
    except: return pd.DataFrame()

# ==========================================
# 7. MAIN DASHBOARD LOGIC
# ==========================================
# --- SIDEBAR ---
with st.sidebar:
    st.header(f"{ICON} Neural Link")
    st.caption("Mode: RSI + MACD Fusion")
    
    if st.button("🧠 Analyze Market", use_container_width=True):
        temp_df = get_data()
        if not temp_df.empty:
            last = temp_df.iloc[-1]
            success, msg = consult_neural_core(last['price'], last['rsi'], last['macd'], last['macd_signal'], st.session_state.balance)
            if success: st.info(msg)
            else: st.error(msg)
            
            # TELEGRAM CONNECTIVITY TEST
            try:
                send_telegram_alert(f"🐺 **YAMIN ALERT SYSTEM**\nConnectivity Check: **ONLINE**\nCurrent Price: ${last['price']:,.2f}")
                st.toast("Test Alert Sent to Telegram!", icon="✅")
            except:
                st.error("Telegram Connection Failed")
            
    st.markdown("---")
    st.metric("System Status", "ARMED & LISTENING")

# --- HEADER ---
col1, col2 = st.columns([1, 8])
with col1: st.title(ICON)
with col2: st.title(f"{SYSTEM_NAME}")
st.markdown("---")

# --- PLACEHOLDERS ---
metrics_ph = st.empty()
charts_ph = st.empty()
log_ph = st.empty()

# --- REAL-TIME LOOP ---
while True:
    df = get_data()
    if not df.empty and 'time' in df.columns:
        latest = df.iloc[-1]
        price = latest['price']
        rsi = latest['rsi']
        macd = latest['macd']
        signal = latest['macd_signal']
        timestamp = latest['time']

        # Logic Flags
        is_oversold = rsi < RSI_BUY
        is_bullish = macd > signal
        is_overbought = rsi > RSI_SELL
        is_bearish = macd < signal

        # --- EXECUTION LOGIC ---
        if st.session_state.position:
            entry = st.session_state.position['entry_price']
            pct = (price - entry) / entry
            
            # STOP LOSS
            if pct <= -STOP_LOSS_PCT:
                st.session_state.balance += price * 0.5
                st.session_state.position = None
                pnl = (price - entry)*0.5
                msg = f"🛑 **STOP LOSS EXECUTED**\nPrice: ${price:,.2f}\nPnL: ${pnl:.2f} ({pct*100:.2f}%)"
                st.session_state.trades.append({"Time": timestamp, "Type": "STOP LOSS", "Price": price, "PnL": pnl})
                send_telegram_alert(msg) 
            
            # TAKE PROFIT
            elif pct >= TAKE_PROFIT_PCT:
                st.session_state.balance += price * 0.5
                st.session_state.position = None
                pnl = (price - entry)*0.5
                msg = f"💰 **TAKE PROFIT EXECUTED**\nPrice: ${price:,.2f}\nPnL: +${pnl:.2f} (+{pct*100:.2f}%)"
                st.session_state.trades.append({"Time": timestamp, "Type": "TAKE PROFIT", "Price": price, "PnL": pnl})
                send_telegram_alert(msg)
        
        # ENTRY SIGNAL (Sniper Mode)
        if not st.session_state.position and is_oversold and is_bullish:
            if st.session_state.balance > (price*0.5):
                st.session_state.position = {'entry_price': price, 'amount': 0.5}
                st.session_state.balance -= (price*0.5)
                msg = f"🔵 **BUY SIGNAL DETECTED**\nEntry Price: ${price:,.2f}\nRSI: {rsi:.1f} | MACD: Bullish"
                st.session_state.trades.append({"Time": timestamp, "Type": "LONG ENTRY", "Price": price, "PnL": 0.0})
                send_telegram_alert(msg)
        
        # EXIT SIGNAL (Smart Exit)
        elif st.session_state.position and (is_overbought or is_bearish):
            entry = st.session_state.position['entry_price']
            st.session_state.balance += price * 0.5
            st.session_state.position = None
            pnl = (price - entry)*0.5
            msg = f"🟠 **SELL SIGNAL DETECTED**\nExit Price: ${price:,.2f}\nPnL: ${pnl:.2f}\nRSI: {rsi:.1f}"
            st.session_state.trades.append({"Time": timestamp, "Type": "MANUAL EXIT", "Price": price, "PnL": pnl})
            send_telegram_alert(msg)

        # --- RENDER UI ---
        with metrics_ph.container():
            m1, m2, m3, m4 = st.columns(4)
            equity = st.session_state.balance
            if st.session_state.position: equity += (0.5 * price - 0.5 * st.session_state.position['entry_price'])
            
            m1.metric("Total Equity", f"${equity:,.2f}")
            m2.metric("Market Trend", "BULLISH 🟢" if is_bullish else "BEARISH 🔴")
            m3.metric("RSI Momentum", f"{rsi:.1f}")
            m4.metric("Alert System", "ONLINE")

        with charts_ph.container():
            base = alt.Chart(df).encode(x=alt.X('time:T', axis=alt.Axis(format='%H:%M:%S', title='')))
            
            # Price Chart
            c1 = base.mark_line(color='#00FFAA').encode(y=alt.Y('price:Q', scale=alt.Scale(zero=False))).properties(height=250, title="Price Action")
            
            # RSI Chart
            c2 = base.mark_line(color='#FFAA00').encode(y=alt.Y('rsi:Q', scale=alt.Scale(domain=[0, 100]))).properties(height=120, title="RSI Index")
            line_buy = alt.Chart(pd.DataFrame({'y': [RSI_BUY]})).mark_rule(color='green', strokeDash=[5,5]).encode(y='y')
            line_sell = alt.Chart(pd.DataFrame({'y': [RSI_SELL]})).mark_rule(color='red', strokeDash=[5,5]).encode(y='y')

            # MACD Chart
            c3_macd = base.mark_line(color='#00AAFF').encode(y='macd:Q')
            c3_signal = base.mark_line(color='#FF5500').encode(y='macd_signal:Q')
            c3 = (c3_macd + c3_signal).properties(height=120, title="MACD Interceptor")

            st.altair_chart(c1 & (c2 + line_buy + line_sell) & c3, use_container_width=True)
        
        with log_ph.container():
            if st.session_state.trades:
                st.subheader("Transaction Log")
                tdf = pd.DataFrame(st.session_state.trades).sort_values(by="Time", ascending=False)
                st.dataframe(tdf.style.format({"Price": "${:,.2f}", "PnL": "${:,.2f}"}), use_container_width=True)

    time.sleep(1)