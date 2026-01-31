import streamlit as st
import pandas as pd
import psycopg2
import time
import altair as alt
import os
from datetime import datetime

# --- 1. CONFIGURATION (The Rules) ---
# YAMIN Core Rules: Precision & Protection
STOP_LOSS_PCT = 0.02   # 2% Max Loss (Wolf Survival Instinct)
TAKE_PROFIT_PCT = 0.04 # 4% Target Profit (Wolf Hunt)
RSI_BUY = 30.0         # Sniper Entry
RSI_SELL = 70.0        # Sniper Exit

# --- 2. BRANDING IDENTITY ---
SYSTEM_NAME = "YAMIN Core"
NODE_NAME = "Sentinel Node"
ICON = "🐺"

st.set_page_config(page_title=f"{SYSTEM_NAME} | {NODE_NAME}", page_icon=ICON, layout="wide")

# --- 3. SESSION STATE ---
if 'balance' not in st.session_state:
    st.session_state.balance = 50000.00
if 'position' not in st.session_state:
    st.session_state.position = None 
if 'trades' not in st.session_state:
    st.session_state.trades = []

# --- 4. LOGIC: RSI Algorithm ---
def calculate_rsi(data, period=14):
    delta = data['price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# --- 5. DATA FETCH (SECURE) ---
@st.cache_data(ttl=1)
def get_data():
    # Credentials from Environment or Default
    db_user = os.getenv('DB_USER', 'admin')
    db_password = os.getenv('DB_PASSWORD', 'adminpassword')
    
    conn = psycopg2.connect(
        host="postgres", 
        database="market_db", 
        user=db_user, 
        password=db_password
    )
    query = "SELECT * FROM market_prices ORDER BY timestamp DESC LIMIT 300"
    df = pd.read_sql(query, conn)
    conn.close()
    df = df.sort_values(by="timestamp")
    df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['price'] = df['price'].astype(float)
    df['rsi'] = calculate_rsi(df)
    return df

# --- 6. UI LAYOUT ---
# Header Area
c1, c2 = st.columns([1, 6])
with c1:
    st.title(ICON)
with c2:
    st.title(f"{SYSTEM_NAME}: {NODE_NAME}")
    st.caption(f"Identity: The Right Hand (Wolf Algorithm) | Strategy: RSI ({RSI_BUY}/{RSI_SELL}) | Risk Shield: Active")

metric_ph = st.empty()
st.markdown("---")
chart_ph = st.empty()

# --- 7. TRADING ENGINE ---
while True:
    try:
        df = get_data()

        if not df.empty:
            latest = df.iloc[-1]
            current_price = latest['price']
            current_rsi = latest['rsi']
            timestamp = latest['time']

            trade_action = "HOLD"
            trade_amount = 0.5 

            # --- A. RISK MANAGEMENT (High Priority) ---
            if st.session_state.position is not None:
                entry = st.session_state.position['entry_price']
                pct_change = (current_price - entry) / entry
                
                # STOP LOSS
                if pct_change <= -STOP_LOSS_PCT:
                    revenue = current_price * st.session_state.position['amount']
                    profit = revenue - (entry * st.session_state.position['amount'])
                    st.session_state.balance += revenue
                    st.session_state.position = None
                    st.session_state.trades.append({
                        "Time": timestamp, "Type": "🛑 STOP LOSS", "Price": current_price, "PnL": profit
                    })
                    trade_action = "EMERGENCY EXIT"
                
                # TAKE PROFIT
                elif pct_change >= TAKE_PROFIT_PCT:
                    revenue = current_price * st.session_state.position['amount']
                    profit = revenue - (entry * st.session_state.position['amount'])
                    st.session_state.balance += revenue
                    st.session_state.position = None
                    st.session_state.trades.append({
                        "Time": timestamp, "Type": "💰 TAKE PROFIT", "Price": current_price, "PnL": profit
                    })
                    trade_action = "TARGET HIT"

            # --- B. STANDARD ENTRY/EXIT LOGIC ---
            if trade_action == "HOLD":
                # BUY
                if current_rsi < RSI_BUY and st.session_state.position is None:
                    cost = current_price * trade_amount
                    if st.session_state.balance >= cost:
                        st.session_state.position = {'entry_price': current_price, 'amount': trade_amount}
                        st.session_state.balance -= cost
                        st.session_state.trades.append({
                            "Time": timestamp, "Type": "🔵 BUY", "Price": current_price, "PnL": 0
                        })
                        trade_action = "OPEN BUY"

                # SELL
                elif current_rsi > RSI_SELL and st.session_state.position is not None:
                    entry = st.session_state.position['entry_price']
                    revenue = current_price * st.session_state.position['amount']
                    profit = revenue - (entry * st.session_state.position['amount'])
                    st.session_state.balance += revenue
                    st.session_state.position = None 
                    st.session_state.trades.append({
                        "Time": timestamp, "Type": "🟠 SELL", "Price": current_price, "PnL": profit
                    })
                    trade_action = "CLOSE SELL"

            # --- C. UPDATE UI ---
            equity = st.session_state.balance
            unrealized_pnl = 0.0
            pnl_pct = 0.0
            
            if st.session_state.position:
                current_value = st.session_state.position['amount'] * current_price
                entry_cost = st.session_state.position['amount'] * st.session_state.position['entry_price']
                unrealized_pnl = current_value - entry_cost
                equity += current_value
                pnl_pct = (unrealized_pnl / entry_cost) * 100

            with metric_ph.container():
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("💰 YAMIN Equity", f"${equity:,.2f}", delta=f"{unrealized_pnl:,.2f}")
                
                if st.session_state.position:
                    m2.metric("PnL %", f"{pnl_pct:.2f}%", f"Entry: ${st.session_state.position['entry_price']:,.0f}")
                else:
                    m2.metric("PnL %", "0.00%", "Flat")

                m3.metric("System Status", "PROTECTED", f"SL: -2% | TP: +4%")

                rsi_val = f"{current_rsi:.1f}"
                if current_rsi < RSI_BUY: m4.error(f"RSI: {rsi_val} (HUNT)")
                elif current_rsi > RSI_SELL: m4.success(f"RSI: {rsi_val} (EXIT)")
                else: m4.metric("RSI", rsi_val)

            with chart_ph.container():
                base = alt.Chart(df).encode(x=alt.X('time:T', axis=alt.Axis(format='%H:%M', title='')))
                price = base.mark_line(color='#00FFAA').encode(y=alt.Y('price:Q', scale=alt.Scale(zero=False))).properties(height=300, title=f"BTC: ${current_price:,.2f}")
                rsi = base.mark_line(color='#FFAA00').encode(y=alt.Y('rsi:Q', scale=alt.Scale(domain=[0, 100]))).properties(height=150, title="RSI Momentum")
                line_70 = alt.Chart(pd.DataFrame({'y': [RSI_SELL]})).mark_rule(color='red').encode(y='y')
                line_30 = alt.Chart(pd.DataFrame({'y': [RSI_BUY]})).mark_rule(color='green').encode(y='y')

                st.altair_chart(price & (rsi + line_70 + line_30), use_container_width=True)

                if st.session_state.trades:
                    st.subheader("📜 YAMIN Trade Ledger")
                    trade_df = pd.DataFrame(st.session_state.trades)
                    st.dataframe(trade_df.style.format({"Price": "${:,.2f}", "PnL": "${:,.2f}"}), use_container_width=True)

        time.sleep(1)

    except Exception as e:
        st.warning("Establishing Link to YAMIN Core...")
        time.sleep(2)