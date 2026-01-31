import streamlit as st
import pandas as pd
import psycopg2
import time
import altair as alt
from datetime import datetime

# --- 1. Page Config ---
st.set_page_config(page_title="HCDS Prop-Trader | Paper Mode", page_icon="🏦", layout="wide")

# --- 2. SESSION STATE (The Virtual Wallet) ---
if 'balance' not in st.session_state:
    st.session_state.balance = 50000.00  # Start with $50k (Prop Firm Standard)
if 'position' not in st.session_state:
    st.session_state.position = None     # None or {'entry_price': 0.0, 'amount': 0.0}
if 'trades' not in st.session_state:
    st.session_state.trades = []         # History log

# --- 3. LOGIC: RSI Algorithm ---
def calculate_rsi(data, period=14):
    delta = data['price'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

# --- 4. DATA: Fetch from Postgres ---
@st.cache_data(ttl=1)
def get_data():
    conn = psycopg2.connect(
        host="postgres",
        database="market_db",
        user="admin",
        password="adminpassword"
    )
    query = "SELECT * FROM market_prices ORDER BY timestamp DESC LIMIT 300"
    df = pd.read_sql(query, conn)
    conn.close()
    
    df = df.sort_values(by="timestamp")
    df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
    df['price'] = df['price'].astype(float)
    df['rsi'] = calculate_rsi(df)
    return df

# --- 5. UI LAYOUT ---
st.title("🏦 HCDS Paper-Trading Terminal")
st.caption("Simulating a $50,000 Prop Firm Challenge based on RSI Logic.")

# Top Metrics Row (Wallet Status)
metric_ph = st.empty()

st.markdown("---")
chart_ph = st.empty()

# --- 6. TRADING ENGINE LOOP ---
while True:
    try:
        df = get_data()

        if not df.empty:
            latest = df.iloc[-1]
            current_price = latest['price']
            current_rsi = latest['rsi']
            timestamp = latest['time']

            # --- A. TRADING LOGIC (The Brain) ---
            trade_action = "HOLD"
            trade_amount = 0.5  # Fixed Lot Size (0.5 BTC)

            # 1. BUY SIGNAL (RSI < 30)
            if current_rsi < 30 and st.session_state.position is None:
                cost = current_price * trade_amount
                if st.session_state.balance >= cost:
                    st.session_state.position = {'entry_price': current_price, 'amount': trade_amount}
                    st.session_state.balance -= cost
                    
                    st.session_state.trades.append({
                        "Time": timestamp, "Type": "BUY", "Price": current_price, "PnL": 0
                    })
                    trade_action = "EXECUTED BUY"

            # 2. SELL SIGNAL (RSI > 70)
            elif current_rsi > 70 and st.session_state.position is not None:
                entry = st.session_state.position['entry_price']
                amount = st.session_state.position['amount']
                revenue = current_price * amount
                profit = revenue - (entry * amount)
                
                st.session_state.balance += revenue
                st.session_state.position = None # Close position
                
                st.session_state.trades.append({
                    "Time": timestamp, "Type": "SELL", "Price": current_price, "PnL": profit
                })
                trade_action = "EXECUTED SELL"

            # --- B. CALCULATE REAL-TIME EQUITY ---
            equity = st.session_state.balance
            unrealized_pnl = 0.0
            
            if st.session_state.position:
                # If we hold BTC, equity = Cash + Current Value of BTC
                current_value = st.session_state.position['amount'] * current_price
                entry_cost = st.session_state.position['amount'] * st.session_state.position['entry_price']
                unrealized_pnl = current_value - entry_cost
                equity += current_value

            # --- C. UPDATE UI ---
            with metric_ph.container():
                # Wallet Metrics
                m1, m2, m3, m4 = st.columns(4)
                m1.metric("💰 Account Equity", f"${equity:,.2f}", delta=f"{unrealized_pnl:,.2f}")
                m2.metric("💵 Cash Balance", f"${st.session_state.balance:,.2f}")
                
                # Position Status
                if st.session_state.position:
                    entry = st.session_state.position['entry_price']
                    m3.metric("OPEN POSITION", "0.5 BTC", f"Entry: ${entry:,.2f}")
                else:
                    m3.metric("OPEN POSITION", "NONE", "Waiting for Signal")

                # RSI Status
                rsi_state = "NEUTRAL"
                if current_rsi < 30: rsi_state = "OVERSOLD (BUY ZONE)"
                elif current_rsi > 70: rsi_state = "OVERBOUGHT (SELL ZONE)"
                m4.metric("RSI Indicator", f"{current_rsi:.1f}", rsi_state)

            with chart_ph.container():
                # Charts
                price_chart = alt.Chart(df).mark_line(color='#00FFAA').encode(
                    x=alt.X('time:T', axis=alt.Axis(format='%H:%M:%S')),
                    y=alt.Y('price:Q', scale=alt.Scale(zero=False)),
                ).properties(height=300, title=f"BTC Price: ${current_price:,.2f}")

                rsi_chart = alt.Chart(df).mark_line(color='#FFAA00').encode(
                    x=alt.X('time:T', axis=alt.Axis(labels=False)),
                    y=alt.Y('rsi:Q', scale=alt.Scale(domain=[0, 100])),
                ).properties(height=150, title="RSI Momentum")

                # Overlay Thresholds
                rule_top = alt.Chart(pd.DataFrame({'y': [70]})).mark_rule(color='red', strokeDash=[5,5]).encode(y='y')
                rule_bot = alt.Chart(pd.DataFrame({'y': [30]})).mark_rule(color='green', strokeDash=[5,5]).encode(y='y')

                st.altair_chart(price_chart & (rsi_chart + rule_top + rule_bot), use_container_width=True)

                # Trade History Table
                if st.session_state.trades:
                    st.subheader("📜 Trade Log")
                    trade_df = pd.DataFrame(st.session_state.trades)
                    # Show latest trades first
                    st.dataframe(trade_df.iloc[::-1].head(5), use_container_width=True)

        time.sleep(1)

    except Exception as e:
        st.error(f"System Initializing... {e}")
        time.sleep(2)