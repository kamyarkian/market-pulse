import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# ==========================================
# 1. STRATEGY CONFIGURATION (v3.0 - The Balanced Warrior)
# ==========================================
TICKER = "BTC-CAD"
INTERVAL = "1h"
INITIAL_CAPITAL = 10000

# Strategy Parameters
RSI_PERIOD = 14
RSI_BUY_THRESHOLD = 35.0
RSI_SELL_THRESHOLD = 65.0

STOP_LOSS_PCT = 0.025      # 2.5% Risk
TAKE_PROFIT_PCT = 0.05     # 5.0% Reward

MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9

# ==========================================
# 2. THE CORE ENGINE (Function)
# ==========================================
def run_simulation(period_name, start_date=None, period_tag=None):
    print(f"\n⏳ LOADING DATA: {period_name}...")
    
    try:
        # Fetch Data
        if start_date:
            df = yf.download(TICKER, start=start_date, interval=INTERVAL, progress=False)
        else:
            df = yf.download(TICKER, period=period_tag, interval=INTERVAL, progress=False)
            
        # Clean Data
        if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)
        if 'Close' not in df.columns and 'Adj Close' in df.columns: df = df.rename(columns={"Adj Close": "Close"})
        df = df.rename(columns={"Close": "price"})
        df = df.dropna()
        df['price'] = pd.to_numeric(df['price'])
        
        if df.empty: return None

        # Calculate Indicators
        delta = df['price'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(RSI_PERIOD).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(RSI_PERIOD).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        ema12 = df['price'].ewm(span=MACD_FAST, adjust=False).mean()
        ema26 = df['price'].ewm(span=MACD_SLOW, adjust=False).mean()
        df['macd'] = ema12 - ema26
        df['macd_signal'] = df['macd'].ewm(span=MACD_SIGNAL, adjust=False).mean()
        df = df.dropna()

        # Simulation Loop
        balance = INITIAL_CAPITAL
        position = None
        trades = []
        
        for index, row in df.iterrows():
            price = row['price']
            rsi = row['rsi']
            macd = row['macd']
            signal = row['macd_signal']
            timestamp = index

            # Flags
            is_oversold = rsi < RSI_BUY_THRESHOLD
            is_bullish = macd > signal
            is_overbought = rsi > RSI_SELL_THRESHOLD
            is_bearish = macd < signal

            if position:
                entry = position['entry_price']
                amount = position['amount']
                pct = (price - entry) / entry
                
                reason = None
                if pct <= -STOP_LOSS_PCT: reason = "STOP LOSS 🛑"
                elif pct >= TAKE_PROFIT_PCT: reason = "TAKE PROFIT 💰"
                elif (is_overbought or is_bearish) and pct > 0.005: reason = "SMART EXIT 🧠"
                
                if reason:
                    pnl = (price - entry) * amount
                    balance += (price * amount)
                    trades.append({'Type': 'SELL', 'PnL': pnl})
                    position = None
            else:
                if is_oversold and is_bullish:
                    trade_size = balance * 0.95
                    amount = trade_size / price
                    balance -= trade_size
                    position = {'entry_price': price, 'amount': amount}
        
        # Close final position
        if position:
            balance += position['amount'] * df.iloc[-1]['price']
            
        # Stats
        profit = balance - INITIAL_CAPITAL
        roi = (profit / INITIAL_CAPITAL) * 100
        wins = len([t for t in trades if t['PnL'] > 0])
        total = len(trades)
        win_rate = (wins / total * 100) if total > 0 else 0
        
        return {
            "Period": period_name,
            "Final Balance": balance,
            "Profit": profit,
            "ROI": roi,
            "Trades": total,
            "Win Rate": win_rate
        }

    except Exception as e:
        print(f"Error in {period_name}: {e}")
        return None

# ==========================================
# 3. MULTI-STAGE STRESS TEST
# ==========================================
scenarios = [
    {"name": "6 MONTHS", "tag": "6mo", "start": None},
    {"name": "9 MONTHS", "tag": None,  "start": (datetime.now() - timedelta(days=270)).strftime('%Y-%m-%d')},
    {"name": "12 MONTHS", "tag": "1y",  "start": None}
]

results = []
print("🐺 YAMIN STRESS TEST INITIATED...")
print("Testing Strategy: v3.0 (Smart Exit + 2.5% Risk)")

for s in scenarios:
    res = run_simulation(s['name'], s['start'], s['tag'])
    if res: results.append(res)

# ==========================================
# 4. FINAL COMMANDER REPORT
# ==========================================
print("\n" + "="*80)
print(f"{'PERIOD':<15} | {'PROFIT (CAD)':<15} | {'ROI (%)':<10} | {'TRADES':<8} | {'WIN RATE':<10}")
print("="*80)

for r in results:
    icon = "✅" if r['Profit'] > 0 else "❌"
    print(f"{icon} {r['Period']:<12} | ${r['Profit']:<14,.2f} | {r['ROI']:<9.2f}% | {r['Trades']:<8} | {r['Win Rate']:.1f}%")

print("="*80)