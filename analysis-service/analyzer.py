import json
from kafka import KafkaConsumer
import psycopg2  # Library for PostgreSQL database

# --- Database Setup ---
def get_db_connection():
    return psycopg2.connect(
        host="localhost",
        database="market_db",
        user="admin",
        password="adminpassword"
    )

def init_db():
    """Creates the table if it does not exist."""
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS market_prices (
                id SERIAL PRIMARY KEY,
                symbol VARCHAR(10),
                price DECIMAL,
                timestamp BIGINT
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        print("✅ Database Connected & Table Ready.")
    except Exception as e:
        print(f"❌ Database Init Error: {e}")

# --- Kafka Setup ---
consumer = KafkaConsumer(
    'market-data',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='latest',
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

# --- Main Execution ---
if __name__ == "__main__":
    print("🧠 Analyzer Started... Listening and Recording to DB...")
    init_db()  # Ensure DB is ready

    for message in consumer:
        try:
            data = message.value
            
            # Extract Data
            symbol = data.get('symbol')
            price = float(data.get('price'))
            timestamp = data.get('timestamp')

            # 1. Visual Output (Console)
            print(f"📊 [LIVE] {symbol}: ${price:,.2f} | Saved to DB 💾")

            # 2. Save to Database (Memory)
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO market_prices (symbol, price, timestamp) VALUES (%s, %s, %s)",
                (symbol, price, timestamp)
            )
            conn.commit()
            cur.close()
            conn.close()

        except Exception as e:
            print(f"⚠️ Error processing message: {e}")