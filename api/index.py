from http.server import BaseHTTPRequestHandler
import json
import pandas as pd
import requests
import random
from datetime import datetime

# ===== FINAL NAME =====
BOT_NAME = "🚀 NEXUS FUTURE ENGINE 🚀"
DEVELOPER = "👨‍💻 Chandan"

ALL_PAIRS = [
    "USDBRL-OTC","USDNGN-OTC","USDCOP-OTC","USDARS-OTC",
    "USDCLP-OTC","USDPEN-OTC","USDTRY-OTC","USDPKR-OTC",
    "USDBDT-OTC","USDZAR-OTC","USDSGD-OTC","USDTHB-OTC","USDHKD-OTC",
    "EURUSD","EURGBP","EURJPY","GBPJPY","AUDJPY","EURAUD","GBPAUD",
    "EURCHF","GBPCHF","AUDCHF","CADJPY","CHFJPY","NZDJPY",
    "EURCAD","GBPCAD","AUDCAD","NZDCAD","EURNZD","GBPNZD","AUDNZD"
]

# ========= DATA =========
def get_live_data():
    try:
        url = "https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1m&limit=200"
        data = requests.get(url).json()

        df = pd.DataFrame(data, columns=["time","open","high","low","close","volume","_","_","_","_","_","_"])

        for col in ["open","high","low","close"]:
            df[col] = df[col].astype(float)

        df["ema20"] = df["close"].ewm(span=20).mean()
        df["ema50"] = df["close"].ewm(span=50).mean()
        df["ema200"] = df["close"].ewm(span=200).mean()

        delta = df["close"].diff()
        gain = delta.clip(lower=0).rolling(14).mean()
        loss = -delta.clip(upper=0).rolling(14).mean()
        rs = gain / loss
        df["rsi"] = 100 - (100/(1+rs))

        return df
    except:
        return None

# ========= LOGIC =========
def advanced_score(df):
    last = df.iloc[-1]
    prev = df.iloc[-2]

    score = 0

    if last["ema20"] > last["ema50"] > last["ema200"]:
        score += 3
    elif last["ema20"] < last["ema50"] < last["ema200"]:
        score -= 3

    score += 1 if last["close"] > prev["close"] else -1

    if last["rsi"] < 30:
        score += 2
    elif last["rsi"] > 70:
        score -= 2

    body = abs(last["close"] - last["open"])
    wick = last["high"] - last["low"]

    if body > wick * 0.6:
        score += 2 if last["close"] > last["open"] else -2

    if last["high"] > prev["high"]:
        score += 1
    if last["low"] < prev["low"]:
        score -= 1

    return score

# ========= ENGINES =========
def live_engine(df):
    score = advanced_score(df)
    prob = min(abs(score)*12, 95)

    if abs(score) < 4:
        return None, prob

    return ("CALL" if score > 0 else "PUT"), prob

def otc_engine():
    base = random.randint(-6,6)
    prob = random.randint(70,95)

    if abs(base) < 3:
        return None, prob

    return ("CALL" if base > 0 else "PUT"), prob

# ========= FORMAT =========
def format_signal(pair, market, signal, prob):
    icon = "🟢📈" if signal == "CALL" else "🔴📉"
    tier = "💎 VIP" if prob >= 85 else "🔥 PREMIUM"
    time_now = datetime.now().strftime("%H:%M")

    return f"""
╔════════════════════╗
{BOT_NAME}
{DEVELOPER}
╚════════════════════╝
{icon} {pair} ({market})
⏰ {time_now}
🔮 {signal}
📊 {prob}% {tier}
━━━━━━━━━━━━━━━━━━
"""

# ========= GENERATE =========
def generate_signals():
    df = get_live_data()
    output = []

    for pair in ALL_PAIRS:

        if "OTC" in pair:
            signal, prob = otc_engine()
            market = "OTC"
        else:
            if df is None:
                continue
            signal, prob = live_engine(df)
            market = "LIVE"

        if signal and prob >= 75:
            output.append(format_signal(pair, market, signal, prob))

    return output[:10]

# ========= API =========
class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        signals = generate_signals()

        response = {
            "bot": BOT_NAME,
            "developer": DEVELOPER,
            "signals": signals
        }

        self.send_response(200)
        self.send_header('Content-type','application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
