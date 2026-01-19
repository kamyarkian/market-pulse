from kafka import KafkaConsumer
import json

# Connection configuration
consumer = KafkaConsumer(
    'market-data',
    bootstrap_servers=['localhost:9092'],
    auto_offset_reset='earliest',  # Read from the beginning
    enable_auto_commit=True,
    value_deserializer=lambda x: x.decode('utf-8')  # Decode bytes to string
)

print("🧠 Analyzer is listening for SMART market data...")

# Continuous loop to process incoming messages
for message in consumer:
    raw_data = message.value
    
    try:
        # 1. Attempt to parse JSON structure
        event = json.loads(raw_data)
        
        # 2. Extract key fields safely
        symbol = event.get('symbol', 'UNKNOWN')
        price = event.get('price', 0)
        volume = event.get('volume', 0)
        
        # 3. Print structured analysis
        print(f"📊 [PROCESSED] Symbol: {symbol} | Price: ${price} | Volume: {volume}")
        
        # 4. Apply simple business logic
        if price > 50000:
             print("    🚀 ALERT: High Value Asset Detected!")
             
    except json.JSONDecodeError:
        # Fallback: If data is not JSON (like our previous "Hello" messages)
        print(f"📝 [TEXT-ONLY] {raw_data}")