import streamlit as st
import pandas as pd
import psycopg2
import time
import altair as alt

# --- 1. Page Config ---
st.set_page_config(page_title="Market Pulse | DEBUG MODE", page_icon="⚡", layout="wide")

st.title("⚡ Market Pulse: Professional Monitor")

# --- DEBUG INFO (To prove what code is running) ---
DB_HOST = "postgres"  # This must match docker-compose service name
st.caption(f"🔌 System Configured to connect to: **{DB_HOST}**")

# --- 2. Database Connection ---
def get_data():
    conn = psycopg2.connect(
        host=DB_HOST,             # <--- FORCE DOCKER NETWORK
        database="market_db",
        user="admin",
        password="adminpassword"
    )
    query = "SELECT * FROM market_prices ORDER BY timestamp DESC LIMIT 150"
    df = pd.read_sql(query, conn)
    conn.close()
    
    df = df.sort_values(by="timestamp")
    df = df[df['price'] > 0]
    df['time'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

placeholder = st.empty()

# --- 3. Main Loop ---
while True:
    try:
        # Create a clean container for errors to prevent stacking
        err_placeholder = st.empty() 
        
        df = get_data()

        with placeholder.container():
            # KPI Metrics
            latest = df.iloc[-1]['price']
            prev = df.iloc[-2]['price'] if len(df) > 1 else latest
            delta = latest - prev
            
            c1, c2 = st.columns([1, 3])
            c1.metric("💰 BTC Price", f"${latest:,.2f}", f"{delta:,.2f}")
            
            # Status Badge
            if latest > 98000: c2.error("🔴 OVERBOUGHT")
            elif latest < 88000: c2.success("🟢 OVERSOLD")
            else: c2.info("⚪ NEUTRAL")

            # Pro Chart
            chart = alt.Chart(df).mark_line(color='#00FF00').encode(
                x=alt.X('time:T', title='Time'),
                y=alt.Y('price:Q', scale=alt.Scale(zero=False), title='Price')
            ).properties(height=400).interactive()
            
            st.altair_chart(chart, use_container_width=True)

    except Exception as e:
        # This shows error ONLY if connection fails
        # If you see "localhost" here, Docker is running old code!
        st.error(f"❌ Connection Failed: {e}")
        time.sleep(2)
        
    time.sleep(1)