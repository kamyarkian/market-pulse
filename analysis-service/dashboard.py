import streamlit as st
import pandas as pd
import psycopg2
import time
import altair as alt
import os
import google.generativeai as genai

# ==========================================
# 1. SYSTEM CONFIGURATION
# ==========================================
STOP_LOSS_PCT = 0.02
TAKE_PROFIT_PCT = 0.04
RSI_PERIOD = 14
RSI_BUY = 30.0
RSI_SELL = 70.0

DB_HOST = "postgres"
DB_NAME = "market_db"
DB_USER = os.getenv('DB_USER', 'admin')
DB_PASS = os.getenv('DB_PASSWORD', 'adminpassword')

# ==========================================
# 2. UI CONFIGURATION
# ==========================================
SYSTEM_NAME = "YAMIN Core"
NODE_NAME = "Sentinel Node"
ICON = "🐺"

st.set_page_config(page_title=SYSTEM_NAME, page_icon=ICON, layout="wide")
st.markdown("""<style>.stMetric {background-color: #0e1117; padding: 10px; border-radius: 5px; border: 1px solid #262730;}</style>""", unsafe_allow_html=True)

# ==========================================
# 3. SESSION STATE
# ==========================================
if 'balance' not in st.session_state: st.session_state.balance = 50000.00
if 'position' not in st.session_state: st.session_state.position = None 
if 'trades' not in st.session_state: st.session_state.trades = []

# ==========================================
# 4. NEURAL LINK (EXACT LIST MATCHING) 🛡️
# ==========================================
def consult_neural_core(price, rsi, balance):
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key: return False, "❌ Error: API Key Missing"
    
    genai.configure(api_key=api_key)
    
    # ✅ UPDATED LIST BASED ON YOUR SCREENSHOT
    # We use explicit names available in your account.
    model_priority_list = [
        'gemini-2.0-flash',       # Primary (High Performance)
        'gemini-2.0-flash-lite',  # Backup 1 (Different Quota)
        'gemini-flash-latest'     # Backup 2 (Stable Alias)
    ]
    
    last_error = ""
    
    for model_name in model_priority_list:
        try:
            model = genai.GenerativeModel(model_name)
            
            prompt = f"""
            Act as YAMIN, a crypto trading AI.
            Data: Price=${price:,.2f}, RSI={rsi:.1f}, Balance=${balance:,.2f}.
            Task: Give 1 short, professional strategic advice.
            """
            
            response = model.generate_content(prompt)
            return True, f"**[{model_name}]** {response.text}"
            
        except Exception as e:
            last_error = str(e)
            continue # Try next model immediately
            
    return False, f"❌ AI Limit Reached. Last Error: {last_error}"

# ==========================================
# 5. DATA ENGINE
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
        
        delta = df['price'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        df['rsi'] = df['rsi'].fillna(50)
        return df
    except: return pd.DataFrame()

# ==========================================
# 6. LAYOUT
# ==========================================
with st.sidebar:
    st.header(f"{ICON} Neural Link")
    st.caption("Auto-Switch: 2.0 Flash -> Lite -> Latest")
    
    if st.button("🧠 Analyze Market", use_container_width=True):
        temp_df = get_data()
        if not temp_df.empty:
            p = temp_df.iloc[-1]['price']
            r = temp_df.iloc[-1]['rsi']
            b = st.session_state.balance
            
            with st.spinner("YAMIN is thinking..."):
                success, msg = consult_neural_core(p, r, b)
                if success: st.info(msg)
                else: st.error(msg)
        else:
            st.warning("No Data")
            
    st.markdown("---")
    st.metric("Status", "ARMED")

col1, col2 = st.columns([1, 8])
with col1: st.title(ICON)
with col2: st.title(f"{SYSTEM_NAME}: {NODE_NAME}")
st.markdown("---")

metrics_ph = st.empty()
charts_ph = st.empty()
log_ph = st.empty()

# ==========================================
# 7. MAIN LOOP
# ==========================================
while True:
    df = get_data()
    if not df.empty and 'time' in df.columns:
        latest = df.iloc[-1]
        price = latest['price']
        rsi = latest['rsi']
        timestamp = latest['time']

        # Trading Logic
        if st.session_state.position:
            entry = st.session_state.position['entry_price']
            pct = (price - entry) / entry
            if pct <= -STOP_LOSS_PCT:
                st.session_state.balance += price * st.session_state.position['amount']
                st.session_state.position = None
                st.session_state.trades.append({"Time": timestamp, "Type": "🛑 STOP LOSS", "Price": price, "PnL": (price - entry)*0.5})
            elif pct >= TAKE_PROFIT_PCT:
                st.session_state.balance += price * st.session_state.position['amount']
                st.session_state.position = None
                st.session_state.trades.append({"Time": timestamp, "Type": "💰 TAKE PROFIT", "Price": price, "PnL": (price - entry)*0.5})
        
        if not st.session_state.position and rsi < RSI_BUY:
            if st.session_state.balance > (price*0.5):
                st.session_state.position = {'entry_price': price, 'amount': 0.5}
                st.session_state.balance -= (price*0.5)
                st.session_state.trades.append({"Time": timestamp, "Type": "🔵 BUY", "Price": price, "PnL": 0.0})
        elif st.session_state.position and rsi > RSI_SELL:
            st.session_state.balance += price * st.session_state.position['amount']
            st.session_state.position = None
            st.session_state.trades.append({"Time": timestamp, "Type": "🟠 SELL", "Price": price, "PnL": (price - entry)*0.5})

        # Render
        with metrics_ph.container():
            m1, m2, m3, m4 = st.columns(4)
            equity = st.session_state.balance
            if st.session_state.position: equity += (0.5 * price - 0.5 * st.session_state.position['entry_price'])
            m1.metric("Equity", f"${equity:,.2f}")
            m2.metric("RSI", f"{rsi:.1f}", "OVERBOUGHT" if rsi>70 else "OVERSOLD" if rsi<30 else "NEUTRAL")
            m3.metric("Shield", "ON")
            m4.metric("AI", "READY")

        with charts_ph.container():
            base = alt.Chart(df).encode(x=alt.X('time:T', axis=alt.Axis(format='%H:%M:%S', title='')), tooltip=['time','price','rsi'])
            c1 = base.mark_line(color='#00FFAA').encode(y=alt.Y('price:Q', scale=alt.Scale(zero=False))).properties(height=250, title="Market Pulse")
            c2 = base.mark_line(color='#FFAA00').encode(y=alt.Y('rsi:Q', scale=alt.Scale(domain=[0, 100]))).properties(height=150, title="Momentum")
            st.altair_chart(c1 & c2, use_container_width=True)

        with log_ph.container():
            if st.session_state.trades:
                tdf = pd.DataFrame(st.session_state.trades).sort_values(by="Time", ascending=False)
                st.dataframe(tdf.style.format({"Price": "${:,.2f}", "PnL": "${:,.2f}"}), use_container_width=True)

    time.sleep(1)