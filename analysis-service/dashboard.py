import streamlit as st
import pandas as pd
import json
from kafka import KafkaConsumer
import time

# 1. Page Config
st.set_page_config(page_title="Market Pulse 🚀", layout="wide")
st.title("⚡ Real-Time Market Pulse")

# 2. Setup placeholders for live updates
col1, col2 = st.columns(2)
with col1:
    price_metric = st.empty()
with col2:
    signal_metric = st.empty()

st.subheader("Live Price Chart (BTC-USD)")
chart_holder = st.empty()

# 3. Connect to Kafka
consumer = KafkaConsumer(
    'market-data',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='latest',
    value_deserializer=lambda x: x.decode('utf-8')
)

# 4. Data Buffer for the Chart
data = []

# 5. Continuous Loop
try:
    for message in consumer:
        # Parse Data
        event = json.loads(message.value)
        price = event.get('price', 0)
        symbol = event.get('symbol', 'BTC-USD')
        
        # Add to history (keep last 50 points)
        data.append(price)
        if len(data) > 50:
            data.pop(0)
            
        # Update Metrics
        price_metric.metric(label="Current Price", value=f"${price:,.2f}")
        
        # Logic Signal
        if price > 96000:
            signal_metric.error("🔴 SELL SIGNAL! (Overbought)")
        elif price < 95200:
            signal_metric.success("🟢 BUY SIGNAL! (Oversold)")
        else:
            signal_metric.info("⚪ HOLD (Market Stable)")

        # Update Chart
        chart_data = pd.DataFrame(data, columns=["Price"])
        chart_holder.line_chart(chart_data)
        
        # Small sleep to prevent UI freezing
        time.sleep(0.1)

except Exception as e:
    st.error(f"Error: {e}")