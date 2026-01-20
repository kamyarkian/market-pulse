import json
from kafka import KafkaConsumer

print("🧠 Smart Analyzer Started... Listening for market signals...")

# 1. Connect to Kafka
consumer = KafkaConsumer(
    'market-data',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='latest',  # Read only the newest data
    value_deserializer=lambda x: x.decode('utf-8')
)

# 2. Process Data Stream
for message in consumer:
    try:
        # Parse JSON
        event = json.loads(message.value)
        
        symbol = event.get('symbol', 'UNKNOWN')
        price = event.get('price', 0)
        volume = event.get('volume', 0)
        
        # 3. Smart Logic (Sensitivity Adjustment)
        # Only alert if price moves significantly around 95,000
        
        if price > 96000:
            print(f"🚀 SELL SIGNAL | {symbol} reached ${price:,.2f} | High Volume: {volume}")
            
        elif price < 95200:
            print(f"💎 BUY SIGNAL  | {symbol} dropped to ${price:,.2f} | Good Entry!")
            
        else:
            # Normal fluctuation - just log it simply
            print(f"📊 Market Monitoring: {symbol} at ${price:,.2f}")

    except json.JSONDecodeError:
        print(f"⚠️ Raw Data: {message.value}")
        
    except Exception as e:
        print(f"❌ Error: {e}")